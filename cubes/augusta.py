from __future__ import annotations

from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, PreMoveContext, TurnOrderContext

_TAG = "augusta.go_last"


class _GoLastNextRound(Effect):
    """If Augusta was flagged last round, move her to the end of this round's turn order."""

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.TURN_ORDER, priority=10)

    def can_trigger(self, ctx: TurnOrderContext) -> bool:
        return self.owner.has_tag(_TAG, exact=True) and self.owner in ctx.turn_order

    def apply(self, ctx: TurnOrderContext) -> None:
        ctx.turn_order.remove(self.owner)
        ctx.turn_order.append(self.owner)
        self.owner.remove_tags(_TAG, exact=True)


class _SkipTurn(Effect):
    """If Augusta is at the top of a stack, she skips her turn and goes last next round."""

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.PRE_MOVE)

    def can_trigger(self, ctx: PreMoveContext) -> bool:
        return (
            ctx.active_cube is self.owner
            and self.owner.above is None
            and self.owner.below is not None
        )

    def apply(self, ctx: PreMoveContext) -> None:
        ctx.move_count = 0
        self.owner.add_tag(_TAG)


class Augusta(CubeBase):
    """
    When at the top of a stack at the start of her turn, skips her turn and
    goes last the following round.
    """

    CUBE_TYPE: ClassVar[str] = "Augusta"

    def _setup_effects(self) -> None:
        self._register(_GoLastNextRound(self))
        self._register(_SkipTurn(self))
