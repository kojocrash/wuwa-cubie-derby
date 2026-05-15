from __future__ import annotations

from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, RollContext, PreMoveContext, RoundEndContext

_TAG = "chisa.low_roll_bonus"

class _LowRollCheck(Effect):
    """During the batch roll phase, tag Chisa if her base roll is ≤ all others'."""

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.ROLL_POST)

    def can_trigger(self, ctx: RollContext) -> bool:
        return self.owner in ctx.rolls

    def apply(self, ctx: RollContext) -> None:
        others = [v for k, v in ctx.rolls.items() if k is not self.owner]
        if not others or ctx.rolls[self.owner] <= min(others):
            self.owner.add_tag(_TAG)


class _LowRollBonus(Effect):
    """At the start of Chisa's turn, consume the low-roll tag to add +2 pads."""

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.PRE_MOVE, priority=10)

    def can_trigger(self, ctx: PreMoveContext) -> bool:
        return (
            ctx.active_cube is self.owner
            and self.owner.has_tag(_TAG)
        )

    def apply(self, ctx: PreMoveContext) -> None:
        self.owner.remove_tags(_TAG)
        ctx.move_count += 2

class _LowRollEffectCleanup(Effect):
    """As a safety net, removes lingering effect tags"""

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.ROUND_END)

    def can_trigger(self, ctx: RoundEndContext) -> bool:
        return self.owner.has_tag("chisa", exact=False)

    def apply(self, ctx: RoundEndContext) -> None:
        self.owner.remove_tags("chisa", exact=False)

class Chisa(CubeBase):
    """If this turn's roll is the lowest among all Cubes, advance 2 extra pads."""

    CUBE_TYPE: ClassVar[str] = "Chisa"

    def _setup_effects(self) -> None:
        self._register(_LowRollCheck(self))
        self._register(_LowRollBonus(self))
        self._register(_LowRollEffectCleanup(self))
