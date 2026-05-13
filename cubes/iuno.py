from __future__ import annotations

from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, TurnEndContext
from engine.track import TRACK_SIZE

_MIDPOINT_PAD = TRACK_SIZE // 2
_TAG = "iuno.gather"


class _GatherAtMidpoint(Effect):
    """
    At TURN_END, the first time Iuno is at or past the midpoint with at least one
    non-Abbowser cube ahead, all non-Abbowser cubes are teleported to Iuno's pad
    and restacked by ranking: last place at the bottom, first place at the top.
    Abbowser (if present at that pad) stays below everyone.

    If no cube is ahead when Iuno crosses, the effect is held and retried each
    subsequent TURN_END until a valid target exists.  Triggers once per match.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.TURN_END)

    def can_trigger(self, ctx: TurnEndContext) -> bool:
        iuno = self.owner
        if ctx.active_cube is not iuno:
            return False
        if iuno.position < _MIDPOINT_PAD:
            return False
        if iuno.has_tag(_TAG, exact=True):
            return False
        return any(
            c.position > iuno.position
            for c in ctx.game.cubes
            if not c.is_abbowser and c is not iuno
        )

    def apply(self, ctx: TurnEndContext) -> None:
        iuno = self.owner
        game = ctx.game
        target_pad = iuno.position

        # Rank worst→best so the worst-ranked cube ends up at the bottom of the
        # new stack and the best-ranked cube ends up at the top.
        # Abbowser is excluded from get_ranking() and is left untouched; if he
        # happens to be at target_pad he stays at the very bottom.
        cubes_ordered = list(reversed(game.get_ranking()))

        for cube in cubes_ordered:
            game._detach_single(cube)

        for cube in cubes_ordered:
            game._append_to_top(cube, target_pad)
            cube.position = target_pad

        iuno.add_tag(_TAG)


class Iuno(CubeBase):
    """
    Once per match: when Iuno first reaches or passes the midpoint with at least
    one cube ahead, all non-Abbowser cubes are pulled to her pad and restacked by
    ranking (last place → bottom, first place → top).  Held if no one is ahead.
    """

    CUBE_TYPE: ClassVar[str] = "Iuno"

    def _setup_effects(self) -> None:
        self._register(_GatherAtMidpoint(self))
