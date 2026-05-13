from __future__ import annotations

import random
from collections import defaultdict
from typing import TYPE_CHECKING

from .effect_system import (
    Effect, Step,
    EffectContext,
    TurnOrderContext, RollContext, PreMoveContext,
    StepPreContext, StepPostContext, FinishCheckContext,
    PadEffectContext, TurnEndContext, RoundEndContext,
)
from .track import TRACK_SIZE, PadType, get_pad_type

if TYPE_CHECKING:
    from .cube_base import CubeBase


class Game:
    """
    Manages all race state and runs the race to completion.

    Typical usage
    -------------
    game = Game()
    game.setup([(Chisa(), None), (Lynae(), None), ...])
    ranking = game.run_game()
    """

    def __init__(self) -> None:
        # Import here to avoid a circular import at module load time
        from cubes.abbowser import AbbowserCube
        self.cubes: list[CubeBase] = []
        self.pads: dict[int, CubeBase] = {}  # pad → bottom cube of stack (absent if empty)
        self.round_number: int = 0
        self.round_rolls: dict[str, int] = {}
        self.race_finished: bool = False
        self._first_half: bool = False
        self._abbowser: AbbowserCube = AbbowserCube()

    # ------------------------------------------------------------------
    # Linked-list stack helpers (private)
    # ------------------------------------------------------------------

    def _get_top(self, pad: int) -> CubeBase | None:
        cur = self.pads.get(pad)
        while cur is not None and cur.above is not None:
            cur = cur.above
        return cur

    def _append_to_top(self, cube: CubeBase, pad: int) -> None:
        top = self._get_top(pad)
        if top is None:
            self.pads[pad] = cube
            cube.below = None
        else:
            top.above = cube
            cube.below = top
        cube.above = None

    def _detach_single(self, cube: CubeBase) -> None:
        """Remove only cube from its stack, stitching its neighbours together."""
        pad = cube.position
        if cube.below is not None:
            cube.below.above = cube.above
        else:
            if cube.above is not None:
                self.pads[pad] = cube.above
            else:
                self.pads.pop(pad, None)
        if cube.above is not None:
            cube.above.below = cube.below
        cube.above = None
        cube.below = None

    def _set_stack(self, pad: int, ordered: list[CubeBase]) -> None:
        """Install ordered (bottom→top) as the full stack at pad."""
        if not ordered:
            self.pads.pop(pad, None)
            return
        self.pads[pad] = ordered[0]
        for i, c in enumerate(ordered):
            c.below = ordered[i - 1] if i > 0 else None
            c.above = ordered[i + 1] if i < len(ordered) - 1 else None

    # ------------------------------------------------------------------
    # Public stack helpers
    # ------------------------------------------------------------------

    def get_stack(self, pad: int) -> list[CubeBase]:
        """Return all cubes at pad, bottom→top."""
        result, cur = [], self.pads.get(pad)
        while cur is not None:
            result.append(cur)
            cur = cur.above
        return result

    def move_unit(self, cube: CubeBase, new_pad: int) -> None:
        """Move cube + its above-stack to new_pad, landing on top of whatever is there."""
        unit = cube.get_moving_unit()
        old_pad = cube.position
        # Detach unit from old pad
        if cube.below is not None:
            cube.below.above = None
            cube.below = None
        else:
            self.pads.pop(old_pad, None)
        # Append unit on top of new pad
        top = self._get_top(new_pad)
        if top is None:
            self.pads[new_pad] = unit[0]
        else:
            top.above = unit[0]
            unit[0].below = top
        for c in unit:
            c.position = new_pad

    def teleport_to_bottom(self, cube: CubeBase) -> None:
        """Reposition cube to the bottom of its current pad's stack."""
        pad = cube.position
        if self.pads.get(pad) is cube:
            return  # already at bottom
        self._detach_single(cube)
        old_bottom = self.pads.get(pad)
        cube.above = old_bottom
        cube.below = None
        if old_bottom is not None:
            old_bottom.below = cube
        self.pads[pad] = cube

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def setup(
        self,
        participants: list[tuple[CubeBase, int | None]],
    ) -> None:
        """
        Place cubes for a race.

        participants: [(cube, pad), ...] where pad=None means first-half (all start at pad 1).
        If ALL pads are None → first-half mode: initial stack order is deferred until the
        round-1 turn order is known so each cube's first move is independent.
        If ANY pad is an int → second-half mode: cubes are placed at their specified pads.
        Abbowser is not included in participants; Game manages it internally.
        """
        self.cubes = [cube for cube, _ in participants]
        is_second_half = any(pad is not None for _, pad in participants)

        if not is_second_half:
            for cube in self.cubes:
                cube.position = 1
                cube.laps_needed = 1
            self._first_half = True
        else:
            by_pad: dict[int, list[CubeBase]] = defaultdict(list)
            for cube, pad in participants:
                actual = (pad % TRACK_SIZE) if pad is not None else 1
                cube.position = actual
                cube.laps_needed = 1
                by_pad[actual].append(cube)
            for pad, group in by_pad.items():
                self._set_stack(pad, group)  # insertion order = bottom → top
            self._first_half = False

    # ------------------------------------------------------------------
    # Ranking helpers
    # ------------------------------------------------------------------

    def active_non_ab_cubes(self) -> list[CubeBase]:
        return [c for c in self.cubes if c.CUBE_TYPE != "Abbowser"]

    def get_adjusted_distance(self, cube: CubeBase) -> int:
        """Pads remaining until cube wins. Lower = closer to winning. AB returns a sentinel."""
        if cube.CUBE_TYPE == "Abbowser":
            return 10_000
        if cube.laps_needed == 0:
            return 0
        base = (TRACK_SIZE - cube.position) % TRACK_SIZE
        if base == 0:
            base = TRACK_SIZE
        return base + (cube.laps_needed - 1) * TRACK_SIZE

    def get_ranking(self) -> list[CubeBase]:
        """Non-AB cubes sorted best → worst."""
        def sort_key(cube: CubeBase):
            dist = self.get_adjusted_distance(cube)
            stack = self.get_stack(cube.position)
            idx = stack.index(cube) if cube in stack else -1
            return (dist, -idx)
        return sorted(self.active_non_ab_cubes(), key=sort_key)

    # ------------------------------------------------------------------
    # Effect gathering
    # ------------------------------------------------------------------

    def all_effects(self, step: Step) -> list[Effect]:
        effects = [e for cube in self.cubes for e in cube.get_effects(step)]
        effects.sort(key=lambda e: -e.priority)
        return effects

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run_game(self) -> list[CubeBase]:
        """Run until someone finishes. Returns ranking best → worst (no AB)."""
        ab = self._abbowser

        while not self.race_finished:
            self.round_number += 1

            # Introduce AB at round 3
            if self.round_number == 3 and ab not in self.cubes:
                ab.position = 0
                ab.laps_needed = 1
                self.cubes.append(ab)
                self._append_to_top(ab, 0)

            # --- Turn order phase ---
            turn_order = list(self.cubes)
            random.shuffle(turn_order)
            ctx = TurnOrderContext(game=self, turn_order=turn_order)
            self._run_step(Step.TURN_ORDER, ctx)
            turn_order = ctx.turn_order

            # For first-half round 1: build the initial stack from turn order
            # (first mover on top so each cube's first move is independent)
            if self._first_half and self.round_number == 1:
                self._set_stack(1, list(reversed(turn_order)))
                self._first_half = False

            # --- Roll phase: pre-roll all dice before any turns execute ---
            self.round_rolls = {cube.name: cube.base_roll() for cube in turn_order}

            # --- Turn phase ---
            for cube in turn_order:
                if self.race_finished:
                    break
                self._execute_turn(cube)

            if self.race_finished:
                break

            # --- Round-end phase ---
            ctx = RoundEndContext(game=self)
            self._run_step(Step.ROUND_END, ctx)

        return self.get_ranking()

    # ------------------------------------------------------------------
    # Turn execution
    # ------------------------------------------------------------------

    def _execute_turn(self, cube: CubeBase) -> None:
        # ROLL_POST: effects can modify the pre-rolled value
        ctx = RollContext(game=self, active_cube=cube, roll=self.round_rolls[cube.name])
        self._run_step(Step.ROLL_POST, ctx)
        total_pads = ctx.roll

        # PRE_MOVE: effects can adjust how many pads will be moved
        ctx = PreMoveContext(game=self, active_cube=cube, roll=total_pads, total_pads=total_pads)
        self._run_step(Step.PRE_MOVE, ctx)
        total_pads = ctx.total_pads

        direction = -1 if cube.CUBE_TYPE == "Abbowser" else 1
        pads_remaining = total_pads
        moved = False

        # --- Movement loop ---
        while pads_remaining > 0:
            # STEP_PRE
            ctx = StepPreContext(
                game=self, active_cube=cube,
                pads_remaining=pads_remaining, direction=direction,
            )
            self._run_step(Step.STEP_PRE, ctx)
            pads_remaining = ctx.pads_remaining
            direction = ctx.direction
            if ctx.cancelled:
                break

            next_pad = (cube.position + direction) % TRACK_SIZE
            self.move_unit(cube, next_pad)
            moved = True
            pads_remaining -= 1

            # STEP_POST
            ctx = StepPostContext(
                game=self, active_cube=cube,
                pads_remaining=pads_remaining, direction=direction,
            )
            self._run_step(Step.STEP_POST, ctx)
            pads_remaining = ctx.pads_remaining

            # Finish check: only for forward crossing of pad 0
            if direction == 1 and cube.position == 0:
                if self._check_and_resolve_finish(cube, direction):
                    break

            if self.race_finished:
                break

        # --- Pad effect (landing pad trigger) ---
        if moved and not self.race_finished:
            self._apply_pad_effect(cube)

        # --- Turn-end effects ---
        ctx = TurnEndContext(game=self, active_cube=cube)
        self._run_step(Step.TURN_END, ctx)

    # ------------------------------------------------------------------
    # Pad effects
    # ------------------------------------------------------------------

    def _apply_pad_effect(self, cube: CubeBase) -> None:
        pad_type = get_pad_type(cube.position)

        if pad_type == PadType.THRUSTER:
            new_pad = (cube.position + 1) % TRACK_SIZE
            self.move_unit(cube, new_pad)
            if new_pad == 0:
                self._check_and_resolve_finish(cube, direction=1)

        elif pad_type == PadType.BLOCKER:
            new_pad = (cube.position - 1) % TRACK_SIZE
            self.move_unit(cube, new_pad)

        elif pad_type == PadType.SPATIAL_RIFT:
            stack = self.get_stack(cube.position)
            random.shuffle(stack)
            self._set_stack(cube.position, stack)

        ctx = PadEffectContext(game=self, active_cube=cube)
        self._run_step(Step.PAD_EFFECT, ctx)

    # ------------------------------------------------------------------
    # Finish-line resolution
    # ------------------------------------------------------------------

    def _check_and_resolve_finish(self, cube: CubeBase, direction: int) -> bool:
        """
        Called when direction==1 and cube is at pad 0.
        Fires FINISH_CHECK effects (which may suppress the crossing).
        If not suppressed, decrements laps_needed for the moving unit.
        Returns True if the race is now finished.
        """
        ctx = FinishCheckContext(game=self, active_cube=cube, direction=direction)
        self._run_step(Step.FINISH_CHECK, ctx)

        if ctx.finish_suppressed:
            return False

        unit = cube.get_moving_unit()
        for c in unit:
            if c.CUBE_TYPE != "Abbowser":
                c.laps_needed -= 1

        if any(c.laps_needed <= 0 for c in unit if c.CUBE_TYPE != "Abbowser"):
            self.race_finished = True
            return True

        return False

    # ------------------------------------------------------------------
    # Internal dispatcher
    # ------------------------------------------------------------------

    def _run_step(self, step: Step, ctx: EffectContext) -> None:
        for eff in self.all_effects(step):
            if eff.matches(ctx):
                eff.apply(ctx)
