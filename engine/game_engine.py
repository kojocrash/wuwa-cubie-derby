from __future__ import annotations

import random
from typing import TYPE_CHECKING

from .effect_system import EffectContext, Step
from .game_state import GameState
from .track import TRACK_SIZE, PadType, get_pad_type

if TYPE_CHECKING:
    from .cube_base import CubeBase


class GameEngine:
    """
    Runs one race to completion and returns the final ranking.

    Typical usage
    -------------
    engine = GameEngine()
    engine.setup_first_half(cube_list, abbowser=ab_cube)
    ranking = engine.run_game()
    """

    def __init__(self) -> None:
        self.state = GameState()
        self._first_half: bool = False
        self._abbowser: CubeBase | None = None

    # ------------------------------------------------------------------
    # Setup helpers
    # ------------------------------------------------------------------

    def setup_first_half(
        self,
        cubes: list[CubeBase],
        abbowser: CubeBase | None = None,
    ) -> None:
        """
        First-half race: all regular cubes start at pad 1.
        Initial stack order is deferred until round-1 turn order is known so
        that each cube's first move is independent (first-mover on top).
        """
        state = self.state
        regular = [c for c in cubes if not c.IS_ABBOWSER]
        state.cubes = regular[:]
        for cube in regular:
            cube.position = 1
            cube.laps_needed = 1
        # Stack will be built once the round-1 turn order is determined
        self._first_half = True
        self._abbowser = abbowser

    def setup_custom(
        self,
        cubes: list[CubeBase],
        positions: dict[str, int],
        stacks: list[list[str]] | None = None,
        abbowser: CubeBase | None = None,
    ) -> None:
        """
        Second-half / arbitrary starting positions.
        *positions*: {cube_name: pad}
        *stacks*: list of [bottom_name, …, top_name] groups at each position.
                  If None each cube is placed alone at its position.
        """
        state = self.state
        regular = [c for c in cubes if not c.IS_ABBOWSER]
        by_name = {c.name: c for c in regular}

        state.cubes = regular[:]
        for cube in regular:
            cube.position = positions.get(cube.name, 1)
            cube.laps_needed = 1

        if stacks:
            for stack_group in stacks:
                if not stack_group:
                    continue
                for name in stack_group:  # bottom → top
                    cube = by_name[name]
                    state.pads[cube.position].append(cube)
        else:
            for cube in regular:
                state.pads[cube.position].append(cube)

        self._first_half = False
        self._abbowser = abbowser

    # ------------------------------------------------------------------
    # Main loop
    # ------------------------------------------------------------------

    def run_game(self) -> list[CubeBase]:
        """Run until someone finishes. Returns ranking best → worst (no AB)."""
        state = self.state
        ab = self._abbowser

        while not state.race_finished:
            state.round_number += 1

            # Introduce AB at round 3
            if ab is not None and state.round_number == 3 and ab not in state.cubes:
                ab.position = 0
                ab.laps_needed = 1
                state.cubes.append(ab)
                state.pads[0].append(ab)

            # --- Turn order phase ---
            turn_order = list(state.cubes)
            random.shuffle(turn_order)
            ctx = EffectContext(state, Step.TURN_ORDER, None)
            ctx.data["turn_order"] = turn_order
            for eff in state.all_effects(Step.TURN_ORDER):
                if eff.condition(ctx):
                    eff.apply(ctx)
            turn_order = ctx.data["turn_order"]

            # For first-half round 1: arrange the initial stack to match turn order
            if self._first_half and state.round_number == 1:
                state.pads[1].clear()
                for cube in reversed(turn_order):
                    state.pads[1].append(cube)
                self._first_half = False

            # --- Roll phase: pre-roll all dice before any turns execute ---
            state.round_rolls = {cube.name: cube.base_roll() for cube in turn_order}

            # --- Turn phase ---
            for cube in turn_order:
                if state.race_finished:
                    break
                self._execute_turn(cube)

            if state.race_finished:
                break

            # --- Round-end phase ---
            ctx = EffectContext(state, Step.ROUND_END, None)
            for eff in state.all_effects(Step.ROUND_END):
                if eff.condition(ctx):
                    eff.apply(ctx)

        return state.get_ranking()

    # ------------------------------------------------------------------
    # Turn execution
    # ------------------------------------------------------------------

    def _execute_turn(self, cube: CubeBase) -> None:
        state = self.state

        # ROLL_POST: effects can modify the pre-rolled value
        roll = state.round_rolls[cube.name]
        ctx = EffectContext(state, Step.ROLL_POST, cube, roll=roll)
        self._run(Step.ROLL_POST, ctx)
        total_pads = ctx.roll

        # PRE_MOVE: effects can adjust how many pads will be moved
        ctx = EffectContext(
            state, Step.PRE_MOVE, cube,
            roll=total_pads, total_pads=total_pads, pads_remaining=total_pads,
        )
        self._run(Step.PRE_MOVE, ctx)
        total_pads = ctx.total_pads

        direction = -1 if cube.IS_ABBOWSER else 1
        pads_remaining = total_pads
        moved = False

        # --- Movement loop ---
        while pads_remaining > 0:
            # STEP_PRE
            ctx = EffectContext(
                state, Step.STEP_PRE, cube,
                pads_remaining=pads_remaining, direction=direction,
            )
            self._run(Step.STEP_PRE, ctx)
            pads_remaining = ctx.pads_remaining
            direction = ctx.direction
            if ctx.cancelled:
                break

            next_pad = (cube.position + direction) % TRACK_SIZE
            state.move_unit(cube, next_pad)
            moved = True
            pads_remaining -= 1

            # STEP_POST: AB pickup, Aemeath teleport, etc.
            ctx = EffectContext(
                state, Step.STEP_POST, cube,
                pads_remaining=pads_remaining, direction=direction,
            )
            self._run(Step.STEP_POST, ctx)
            pads_remaining = ctx.pads_remaining  # effects may cancel remaining steps

            # Finish check: only for forward crossing of pad 0
            if direction == 1 and cube.position == 0:
                if self._check_and_resolve_finish(cube, direction):
                    break

            if state.race_finished:
                break

        # --- Pad effect (landing pad trigger) ---
        if moved and not state.race_finished:
            self._apply_pad_effect(cube)

        # --- Turn-end effects ---
        ctx = EffectContext(state, Step.TURN_END, cube)
        self._run(Step.TURN_END, ctx)

    # ------------------------------------------------------------------
    # Pad effects
    # ------------------------------------------------------------------

    def _apply_pad_effect(self, cube: CubeBase) -> None:
        state = self.state
        pad_type = get_pad_type(cube.position)

        if pad_type == PadType.THRUSTER:
            new_pad = (cube.position + 1) % TRACK_SIZE
            state.move_unit(cube, new_pad)
            # Thruster is always a forward push; check finish if it reaches pad 0
            if new_pad == 0:
                self._check_and_resolve_finish(cube, direction=1)

        elif pad_type == PadType.BLOCKER:
            new_pad = (cube.position - 1) % TRACK_SIZE
            state.move_unit(cube, new_pad)

        elif pad_type == PadType.SPATIAL_RIFT:
            stack = state.pads[cube.position]
            random.shuffle(stack)

        # PAD_EFFECT window for cube effects
        ctx = EffectContext(state, Step.PAD_EFFECT, cube)
        self._run(Step.PAD_EFFECT, ctx)

    # ------------------------------------------------------------------
    # Finish-line resolution
    # ------------------------------------------------------------------

    def _check_and_resolve_finish(self, cube: CubeBase, direction: int) -> bool:
        """
        Called when direction==1 and cube is at pad 0.
        Fires FINISH_CHECK effects (which may suppress).
        If not suppressed, decrements laps_needed for the moving unit.
        Returns True if the race is now finished.
        """
        state = self.state
        ctx = EffectContext(
            state, Step.FINISH_CHECK, cube,
            finish_triggered=True, direction=direction,
        )
        self._run(Step.FINISH_CHECK, ctx)

        if ctx.finish_suppressed:
            return False

        unit = state.get_moving_unit(cube)
        for c in unit:
            if not c.IS_ABBOWSER:
                c.laps_needed -= 1

        if any(c.laps_needed <= 0 for c in unit if not c.IS_ABBOWSER):
            state.race_finished = True
            return True

        return False

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------

    def _run(self, step: Step, ctx: EffectContext) -> None:
        for eff in self.state.all_effects(step):
            if eff.condition(ctx):
                eff.apply(ctx)
