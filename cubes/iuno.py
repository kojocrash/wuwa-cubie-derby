from __future__ import annotations

from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, TurnEndContext
from engine.track import TRACK_SIZE

_MIDPOINT_PAD = TRACK_SIZE // 2
_TAG = "iuno.gather"

class _GatherAtMidpoint(Effect):
    """
    Checks if Iuno has passed the midpoint and non-Abbowser cubes exist
    both ahead and behind her in ranking. If so, teleports all of them
    to her pad, stacking in their pre-teleport ranking order (last place → bottom, first place → top).
    Triggers at most once per match.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.TURN_END, priority=5)

    def can_trigger(self, ctx: TurnEndContext) -> bool:
        iuno = self.owner
        if ctx.active_cube is not iuno:
            return False
        if ctx.game.get_adjusted_position(iuno) <= _MIDPOINT_PAD:
            return False
        if iuno.has_tag(_TAG):
            return False
        ranking = ctx.game.get_ranking()
        iuno_idx = ranking.index(iuno)
        return 0 < iuno_idx < len(ranking) - 1  # someone ahead AND behind

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
    Once per match, after passing the midpoint of the track, if there are
    non-Abbowser cubes ranked both ahead and behind her, all of them are
    teleported to her pad. Their stacking order reflects their rankings
    prior to the teleport (last place → bottom, first place → top).
    """

    CUBE_TYPE: ClassVar[str] = "Iuno"

    def _setup_effects(self) -> None:
        self._register(_GatherAtMidpoint(self))
