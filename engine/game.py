from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import TYPE_CHECKING

from .effect_system import (
    Effect, Phase,
    EffectContext,
    TurnOrderContext, RollContext, PreMoveContext,
    MovePreContext, MovePostContext, FinishCheckContext,
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

    Pass verbose=True to print a detailed turn-by-turn trace.
    """

    def __init__(self, verbose: bool = False) -> None:
        from cubes.abbowser import AbbowserCube
        self.verbose = verbose
        ab = AbbowserCube()
        ab.laps_needed = math.inf
        self._abbowser = ab
        self.cubes: list[CubeBase] = []
        self.pads: dict[int, CubeBase] = {}  # pad → bottom cube of stack (absent if empty)
        self.round_number: int = 0
        self.round_rolls: dict[CubeBase, int] = {}
        self.race_finished: bool = False
        self._first_half: bool = False

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

    def teleport_to_top(self, cube: CubeBase) -> None:
        """Reposition cube to the top of its current pad's stack."""
        if cube.above is None:
            return  # already at top
        self._detach_single(cube)
        self._append_to_top(cube, cube.position)

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def setup(
        self,
        participants: list[tuple[CubeBase, int | None]],
    ) -> None:
        """
        Place cubes for a race.

        participants: [(cube, pad), ...] where pad=None means pad 0 in second-half.
        If ALL pads are None → first-half mode: all regular cubes start at pad 1,
          and the initial stack order is deferred until the round-1 turn order is known.
        If ANY pad is supplied → second-half mode: pad=None defaults to pad 0.

        Abbowser is not included in participants; Game places him at pad 0 below
        any other cubes that start there.
        """
        # Reset AB and plant him at pad 0 (bottom of any eventual stack there)
        ab = self._abbowser
        ab.position = 0
        ab.laps_needed = math.inf
        ab.above = None
        ab.below = None
        self.pads = {0: ab}
        self.cubes = [ab]

        regular = [cube for cube, _ in participants]
        self.cubes.extend(regular)

        is_second_half = any(pad is not None for _, pad in participants)

        if not is_second_half:
            # First-half: all regular cubes at pad 1, stack order set after turn order
            for cube in regular:
                cube.position = 1
                cube.laps_needed = 1
                self._append_to_top(cube, 1)
            self._first_half = True
        else:
            # Second-half: place cubes at their specified pads; None → pad 0
            for cube, pad in participants:
                actual = (pad % TRACK_SIZE) if pad is not None else 0
                cube.position = actual
                is_starting_behind = (pad is not None and pad < 0) or actual > TRACK_SIZE // 4  # quarter-track threshold is arbitrary
                cube.laps_needed = 2 if is_starting_behind else 1
                self._append_to_top(cube, actual)
            self._first_half = False

    # ------------------------------------------------------------------
    # Ranking helpers
    # ------------------------------------------------------------------

    def active_non_ab_cubes(self) -> list[CubeBase]:
        return [c for c in self.cubes if not c.is_abbowser]

    def get_adjusted_distance(self, cube: CubeBase) -> int:
        """Pads remaining until cube wins. Lower = closer to winning. AB returns a sentinel."""
        if cube.is_abbowser:
            return 10_000
        if cube.laps_needed == 0:
            return 0
        base = (TRACK_SIZE - cube.position) % TRACK_SIZE
        if base == 0:
            base = TRACK_SIZE
        return base + (cube.laps_needed - 1) * TRACK_SIZE

    def get_adjusted_position(self, cube: CubeBase) -> int:
        """Pads effectively traveled. Higher = closer to winning. Complement of adjusted_distance."""
        return TRACK_SIZE - self.get_adjusted_distance(cube)

    def get_ranking(self) -> list[CubeBase]:
        """Non-Abbowser cubes sorted best → worst."""
        def sort_key(cube: CubeBase):
            dist = self.get_adjusted_distance(cube)
            stack = self.get_stack(cube.position)
            idx = stack.index(cube) if cube in stack else -1
            return (dist, -idx)
        return sorted(self.active_non_ab_cubes(), key=sort_key)

    # ------------------------------------------------------------------
    # Effect gathering
    # ------------------------------------------------------------------

    def all_effects(self, phase: Phase) -> list[Effect]:
        effects = [e for cube in self.cubes for e in cube.get_effects(phase)]
        effects.sort(key=lambda e: -e.priority)
        return effects

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run_game(self) -> list[CubeBase]:
        """Run until someone finishes. Returns ranking best → worst (no Abbowser)."""
        if not self.race_finished and not self._first_half and self.round_number == 0:
            # Seems like ROUND_END effects can trigger at the very beginning of non-1st-half races (Changli on 2026 Preliminary C 2nd-half NA server)
            #   might need more research but this is closest hypothesis
            ctx = RoundEndContext(game=self)
            self._trigger_phase_effects(Phase.ROUND_END, ctx)

        while not self.race_finished:
            self.round_number += 1

            if self.verbose:
                print(f"\n{'═' * 52}")
                print(f"  ROUND {self.round_number}")
                print(f"{'═' * 52}")

            # --- Turn order phase ---
            turn_order = list(self.cubes)
            random.shuffle(turn_order)
            ctx = TurnOrderContext(game=self, turn_order=turn_order)
            self._trigger_phase_effects(Phase.TURN_ORDER, ctx)
            turn_order = ctx.turn_order

            if self.verbose:
                print(f"Turn order: {' → '.join(c.name for c in turn_order)}")

            # For first-half round 1: rebuild pad-1 stack from turn order
            # (first mover on top so each cube's first move is independent)
            if self._first_half and self.round_number == 1:
                self._set_stack(1, list(reversed(turn_order)))
                self._first_half = False

            # Print initial board after any round-1 stack setup so what's shown is accurate
            if self.verbose and self.round_number == 1:
                self._vprint_board("INITIAL BOARD")

            # --- Roll phase: pre-roll all dice, then fire ROLL_POST for each cube ---
            base_rolls: dict[CubeBase, int] = {cube: cube.base_roll() for cube in turn_order}
            # Populate round_rolls with base values so ROLL_POST effects (e.g. Chisa)
            # can read other cubes' raw rolls during the batch phase.
            self.round_rolls = dict(base_rolls)

            modified_rolls: dict[CubeBase, int] = {}
            for cube in turn_order:
                ctx = RollContext(game=self, cube=cube, roll=base_rolls[cube])
                self._trigger_phase_effects(Phase.ROLL_POST, ctx)
                modified_rolls[cube] = ctx.roll

            if self.verbose:
                parts = []
                for cube in turn_order:
                    base = base_rolls[cube]
                    mod = modified_rolls[cube]
                    parts.append(
                        f"{cube.name}={base}" if base == mod
                        else f"{cube.name}={base}→{mod}"
                    )
                print(f"Rolls:      {'  '.join(parts)}")

            self.round_rolls = modified_rolls

            # --- Turn phase ---
            for cube in turn_order:
                if self.race_finished:
                    break
                self._execute_turn(cube)

            if self.race_finished:
                break

            # --- Round-end phase ---
            ctx = RoundEndContext(game=self)
            self._trigger_phase_effects(Phase.ROUND_END, ctx)

            if self.verbose:
                self._vprint_board(f"after round {self.round_number}")

        if self.verbose:
            self._vprint_board("FINAL")

        return self.get_ranking()

    # ------------------------------------------------------------------
    # Turn execution
    # ------------------------------------------------------------------

    def _move_one_pad(
        self,
        cube: CubeBase,
        stride: int,
        pads_remaining: int,
        is_pad_push: bool = False,
    ) -> tuple[int, bool]:
        """
        Consume one move, advance cube one pad, fire MOVE_POST, check the finish line.

        pads_remaining: moves still to go including this one; decremented internally
        before MOVE_POST so effects see the remaining count after this move.
        Returns (updated_pads_remaining, should_stop).
        """
        pads_remaining -= 1
        old_pos = cube.position
        next_pad = (cube.position + stride) % TRACK_SIZE
        self.move_unit(cube, next_pad)

        if self.verbose:
            unit = cube.get_moving_unit()
            carrying = (
                f"  [+ {', '.join(c.name for c in unit[1:])}]" if len(unit) > 1 else ""
            )
            print(f"    pad {old_pos} → pad {next_pad}{carrying}")

        ctx = MovePostContext(
            game=self, active_cube=cube,
            pads_remaining=pads_remaining, stride=stride,
            is_pad_push=is_pad_push,
        )
        self._trigger_phase_effects(Phase.MOVE_POST, ctx)
        pads_remaining = ctx.pads_remaining

        if stride > 0 and cube.position == 0:
            if self.verbose:
                print(f"    *** {cube.name} crosses the finish line!")
            if self._check_and_resolve_finish(cube, stride=stride):
                return pads_remaining, True

        if self.race_finished:
            return pads_remaining, True

        return pads_remaining, False

    def _run_movement(
        self,
        cube: CubeBase,
        stride: int,
        move_count: int,
        is_pad_push: bool = False,
    ) -> bool:
        """
        Move cube one pad at a time for up to move_count moves.

        For regular movement (not is_pad_push) fires MOVE_PRE before each move,
        which can cancel, adjust the remaining count, or change the stride.
        MOVE_POST effects that modify pads_remaining mid-push are respected.
        Returns True if at least one move was made.
        """
        pads_remaining = move_count
        moved = False
        while pads_remaining > 0:
            if not is_pad_push:
                ctx = MovePreContext(
                    game=self, active_cube=cube,
                    pads_remaining=pads_remaining, stride=stride,
                )
                self._trigger_phase_effects(Phase.MOVE_PRE, ctx)
                pads_remaining = ctx.pads_remaining
                stride = ctx.stride
                if ctx.cancelled:
                    if self.verbose:
                        print(f"    (movement cancelled)")
                    return moved
            moved = True
            pads_remaining, stop = self._move_one_pad(cube, stride, pads_remaining, is_pad_push)
            if stop:
                return moved
        return moved

    def _execute_turn(self, cube: CubeBase) -> None:
        roll = self.round_rolls[cube]

        # PRE_MOVE: effects can adjust how many moves will be made
        ctx = PreMoveContext(game=self, active_cube=cube, roll=roll, move_count=roll)
        self._trigger_phase_effects(Phase.PRE_MOVE, ctx)
        move_count = ctx.move_count

        if self.verbose:
            roll_str = str(roll) if move_count == roll else f"{roll}→{move_count}"
            print(f"\n  [{cube.name}]  pad {cube.position}  roll={roll_str}  ({move_count} moves)")

        stride = -1 if cube.is_abbowser else 1
        self._run_movement(cube, stride, move_count)

        # --- Pad effect (landing pad trigger) ---
        if not self.race_finished:
            self._apply_pad_effect(cube)

        if self.verbose:
            unit = cube.get_moving_unit()
            carrying = (
                f"  [carrying: {', '.join(c.name for c in unit[1:])}]" if len(unit) > 1 else ""
            )
            print(f"    ends at pad {cube.position}{carrying}")

        # --- Turn-end effects ---
        ctx = TurnEndContext(game=self, active_cube=cube)
        self._trigger_phase_effects(Phase.TURN_END, ctx)

    # ------------------------------------------------------------------
    # Pad effects
    # ------------------------------------------------------------------

    def _apply_pad_effect(self, cube: CubeBase) -> None:
        pad_type = get_pad_type(cube.position)

        if pad_type == PadType.NORMAL:
            return

        # Build context with the proposed outcome; fire PAD_EFFECT so effects
        # can modify push distance, stack order, etc. before anything executes.
        if pad_type == PadType.SPATIAL_RIFT:
            proposed = self.get_stack(cube.position)
            random.shuffle(proposed)
            ctx = PadEffectContext(
                game=self, active_cube=cube, pad_type=pad_type, new_order=proposed,
            )
        else:
            ctx = PadEffectContext(
                game=self, active_cube=cube, pad_type=pad_type, push_pads=1,
            )

        self._trigger_phase_effects(Phase.PAD_EFFECT, ctx)

        # Execute using the (possibly modified) context values
        if pad_type == PadType.THRUSTER:
            if self.verbose:
                print(f"    [THRUSTER at pad {cube.position}] pushing {ctx.push_pads} pad(s) forward")
            self._run_movement(cube, 1, ctx.push_pads, is_pad_push=True)
            if not self.race_finished:
                self._apply_pad_effect(cube)

        elif pad_type == PadType.BLOCKER:
            if self.verbose:
                print(f"    [BLOCKER at pad {cube.position}] pushing {ctx.push_pads} pad(s) backward")
            self._run_movement(cube, -1, ctx.push_pads, is_pad_push=True)
            if not self.race_finished:
                self._apply_pad_effect(cube)

        elif pad_type == PadType.SPATIAL_RIFT:
            if self.verbose:
                print(f"    [SPATIAL RIFT at pad {cube.position}] shuffling stack")
            self._set_stack(cube.position, ctx.new_order)
            if self.verbose:
                order_str = ", ".join(c.name for c in self.get_stack(cube.position))
                print(f"    new order (bottom→top): {order_str}")

    # ------------------------------------------------------------------
    # Finish-line resolution
    # ------------------------------------------------------------------

    def _check_and_resolve_finish(self, cube: CubeBase, stride: int) -> bool:
        """
        Called when stride > 0 and cube landed on pad 0.
        Fires FINISH_CHECK effects (which may suppress the crossing).
        Decrements laps_needed for every non-Abbowser cube in the moving unit.
        Returns True if the race is now finished.
        """
        ctx = FinishCheckContext(game=self, active_cube=cube, stride=stride)
        self._trigger_phase_effects(Phase.FINISH_CHECK, ctx)

        if ctx.finish_suppressed:
            return False

        unit = cube.get_moving_unit()
        for c in unit:
            if not c.is_abbowser:
                c.laps_needed -= 1

        if any(c.laps_needed <= 0 for c in unit if not c.is_abbowser):
            self.race_finished = True
            return True

        return False

    # ------------------------------------------------------------------
    # Internal dispatcher
    # ------------------------------------------------------------------

    def _trigger_phase_effects(self, phase: Phase, ctx: EffectContext) -> None:
        for eff in self.all_effects(phase):
            if eff.can_trigger(ctx):
                eff.apply(ctx)

    # ------------------------------------------------------------------
    # Debug helpers
    # ------------------------------------------------------------------

    def _vprint_board(self, label: str) -> None:
        print(f"\n  Board [{label}]:")
        if not self.pads:
            print("    (empty)")
            return
        for pad in sorted(self.pads.keys()):
            stack = self.get_stack(pad)
            names = ", ".join(c.name for c in stack)
            print(f"    pad {pad:2d}: {names}  (bottom → top)")
