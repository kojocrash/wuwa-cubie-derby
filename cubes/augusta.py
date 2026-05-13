from __future__ import annotations

from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, TurnOrderContext

_TAG = "augusta.go_last"


class _GoLastNextRound(Effect):
    """
    If Augusta was flagged last round (she skipped), move her to the end of this
    round's turn order and consume the flag.  High priority so it fires before
    _SkipTurn, ensuring the flag from a previous round is processed first.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.TURN_ORDER, priority=10)

    def can_trigger(self, ctx: TurnOrderContext) -> bool:
        return self.owner.has_tag(_TAG, exact=True) and self.owner in ctx.turn_order

    def apply(self, ctx: TurnOrderContext) -> None:
        ctx.turn_order.remove(self.owner)
        ctx.turn_order.append(self.owner)
        self.owner.remove_tags(_TAG, exact=True)


class _SkipTurn(Effect):
    """
    If Augusta is at the top of a stack (with at least one cube below) she sits
    out this round and is flagged to move last the following round.  Low priority
    so it fires after _GoLastNextRound has already processed any existing flag.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.TURN_ORDER, priority=-10)

    def can_trigger(self, ctx: TurnOrderContext) -> bool:
        return (
            self.owner in ctx.turn_order
            and self.owner.above is None
            and self.owner.below is not None
        )

    def apply(self, ctx: TurnOrderContext) -> None:
        ctx.turn_order.remove(self.owner)
        self.owner.add_tag(_TAG)


class Augusta(CubeBase):
    """
    When at the top of a stack at the start of a round, sits out that round and
    moves last the following round.
    """

    CUBE_TYPE: ClassVar[str] = "Augusta"

    def _setup_effects(self) -> None:
        self._register(_GoLastNextRound(self))
        self._register(_SkipTurn(self))
