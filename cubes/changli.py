from __future__ import annotations

import random
from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, RoundEndContext, TurnOrderContext

_TAG = "changli.go_last"


class _CheckGoLast(Effect):
    """
    At round end, if at least one cube is stacked below Changli, roll 65%.
    On success, flag her to move last next round.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.ROUND_END)

    def can_trigger(self, ctx: RoundEndContext) -> bool:
        return self.owner.below is not None

    def apply(self, ctx: RoundEndContext) -> None:
        if random.random() < 0.65:
            self.owner.add_tag(_TAG)


class _GoLastNextRound(Effect):
    """If flagged from last round, move Changli to the end of this round's turn order."""

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.TURN_ORDER, priority=10)

    def can_trigger(self, ctx: TurnOrderContext) -> bool:
        return self.owner.has_tag(_TAG, exact=True)

    def apply(self, ctx: TurnOrderContext) -> None:
        if self.owner in ctx.turn_order:
            ctx.turn_order.remove(self.owner)
            ctx.turn_order.append(self.owner)
        self.owner.remove_tags(_TAG, exact=True)


class Changli(CubeBase):
    """
    At round end, if cubes are stacked below her, 65% chance to move last next round.
    """

    CUBE_TYPE: ClassVar[str] = "Changli"

    def _setup_effects(self) -> None:
        self._register(_CheckGoLast(self))
        self._register(_GoLastNextRound(self))
