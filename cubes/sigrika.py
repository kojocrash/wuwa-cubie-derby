from __future__ import annotations

from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, RollContext, PreMoveContext, RoundEndContext

MARK_COUNT = 2

_TAG = "sigrika.cripple"

class _SigrikaMarkEffect(Effect):
    """
    Marks up to 2 cubes ranked immediately ahead of Sigrika after each dice roll.
    The first dice roll of the match is exempt from this effect. (first-half races only)
    """
    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.ROLL_POST)

    def can_trigger(self, ctx: RollContext) -> bool:
        return (
            not ctx.game._first_half
            or  ctx.game.round_number > 1
        )

    def apply(self, ctx: RollContext) -> None:
        rankings = ctx.game.get_ranking()
        sigrika_idx = rankings.index(self.owner)

        for i in range(MARK_COUNT):
            cube_idx = sigrika_idx - 1 - i
            if cube_idx < 0: break

            target_cube = rankings[cube_idx]
            target_cube.add_tag(_TAG)

class _SigrikaCrippleEffect(Effect):
    """
    Reduces the marked cube's movement by 1 pad for the current round.
    Movement cannot be reduced to 0 or below.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.PRE_MOVE, priority=-1)

    def can_trigger(self, ctx: PreMoveContext) -> bool:
        return ctx.active_cube.has_tag(_TAG)

    def apply(self, ctx: PreMoveContext) -> None:
        ctx.active_cube.remove_tags(_TAG)
        
        if ctx.move_count > 1:
            ctx.move_count -= 1

class _SigrikaEffectCleanup(Effect):
    """As a safety net, removes lingering effect tags"""

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.ROUND_END)

    def can_trigger(self, ctx: RoundEndContext) -> bool:
        return any(c.has_tag(_TAG) for c in ctx.game.cubes)

    def apply(self, ctx: RoundEndContext) -> None:
        for cube in ctx.game.cubes:
            cube.remove_tags(_TAG)


class Sigrika(CubeBase):
    """Up to 2 Cubes ranked directly above Sigrika at the start of the round will advance 1 fewer pad this turn. This effect does not freeze Cubes in place or make them go backwards."""

    CUBE_TYPE: ClassVar[str] = "Sigrika"

    def _setup_effects(self) -> None:
        self._register(_SigrikaMarkEffect(self))
        self._register(_SigrikaCrippleEffect(self))
        self._register(_SigrikaEffectCleanup(self))
