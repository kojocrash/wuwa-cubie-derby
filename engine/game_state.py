from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from .track import TRACK_SIZE

if TYPE_CHECKING:
    from .cube_base import CubeBase
    from .effect_system import Step


class GameState:
    """All mutable race state: positions, stacks, round counters."""

    def __init__(self) -> None:
        self.cubes: list[CubeBase] = []
        # pads[pad] = list ordered bottom → top
        self.pads: dict[int, list[CubeBase]] = defaultdict(list)
        self.round_number: int = 0
        # Base dice for the current round before ROLL_POST effects
        self.round_rolls: dict[str, int] = {}
        self.race_finished: bool = False

    # ------------------------------------------------------------------
    # Stack helpers
    # ------------------------------------------------------------------

    def get_moving_unit(self, cube: CubeBase) -> list[CubeBase]:
        """Returns [cube, …everything above it] — the group that moves together."""
        stack = self.pads[cube.position]
        try:
            idx = stack.index(cube)
            return stack[idx:]
        except ValueError:
            return [cube]

    def move_unit(self, cube: CubeBase, new_pad: int) -> None:
        """Move cube and its stack-above to new_pad, landing on top of whatever is there."""
        unit = self.get_moving_unit(cube)
        old_pad = cube.position

        for c in unit:
            self.pads[old_pad].remove(c)

        self.pads[new_pad].extend(unit)

        for c in unit:
            c.position = new_pad

    def teleport_to_bottom(self, cube: CubeBase) -> None:
        """Move cube to index 0 of its current pad's stack (position within stack only)."""
        stack = self.pads[cube.position]
        if stack and stack[0] is not cube:
            stack.remove(cube)
            stack.insert(0, cube)

    # ------------------------------------------------------------------
    # Ranking
    # ------------------------------------------------------------------

    def get_adjusted_distance(self, cube: CubeBase) -> int:
        """
        Pads remaining until cube wins, accounting for AB-induced extra laps.
        Lower = closer to winning.  AB returns a sentinel so it never ranks well.
        """
        if cube.IS_ABBOWSER:
            return 10_000
        if cube.laps_needed == 0:
            return 0  # just crossed the finish line
        base = (TRACK_SIZE - cube.position) % TRACK_SIZE
        # At pad 0 with laps still pending: needs a full lap before next finish crossing
        if base == 0:
            base = TRACK_SIZE
        return base + (cube.laps_needed - 1) * TRACK_SIZE

    def get_ranking(self) -> list[CubeBase]:
        """
        Non-AB cubes sorted best → worst.
        Primary: adjusted distance ascending.
        Tiebreak: higher in stack (larger index) wins (negate for ascending sort).
        """
        non_ab = [c for c in self.cubes if not c.IS_ABBOWSER]

        def sort_key(cube: CubeBase):
            dist = self.get_adjusted_distance(cube)
            try:
                stack_idx = self.pads[cube.position].index(cube)
            except ValueError:
                stack_idx = -1
            return (dist, -stack_idx)

        return sorted(non_ab, key=sort_key)

    # ------------------------------------------------------------------
    # Effect gathering
    # ------------------------------------------------------------------

    def all_effects(self, step: Step) -> list:
        effects = []
        for cube in self.cubes:
            effects.extend(cube.get_effects(step))
        effects.sort(key=lambda e: -e.priority)
        return effects

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def active_non_ab_cubes(self) -> list[CubeBase]:
        return [c for c in self.cubes if not c.IS_ABBOWSER]
