from __future__ import annotations

import random
from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, RollContext, PreMoveContext, RoundEndContext

_NO_MOVEMENT_TAG = "lynae.still"
_DOUBLE_MOVEMENT_TAG = "lynae.double"

class _LynaeRollCheck(Effect):
    """During the batch roll phase, tag Lynae with her outcome for this round."""

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.ROLL_POST)

    def can_trigger(self, ctx: RollContext) -> bool:
        return self.owner in ctx.rolls

    def apply(self, ctx: RollContext) -> None:
        r = random.random()
        if r < 0.20:
            self.owner.add_tag(_NO_MOVEMENT_TAG)
        elif r < 0.80:
            self.owner.add_tag(_DOUBLE_MOVEMENT_TAG)
        # else: 20% — no tag, normal roll


class _LynaeRollApply(Effect):
    """At the start of Lynae's turn, consume the outcome tag to adjust move count."""

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.PRE_MOVE, priority=10)

    def can_trigger(self, ctx: PreMoveContext) -> bool:
        return ctx.active_cube is self.owner and (
            self.owner.has_tag(_NO_MOVEMENT_TAG)
            or self.owner.has_tag(_DOUBLE_MOVEMENT_TAG)
        )

    def apply(self, ctx: PreMoveContext) -> None:
        if self.owner.has_tag(_NO_MOVEMENT_TAG):
            self.owner.remove_tags(_NO_MOVEMENT_TAG)
            ctx.move_count = 0
        elif self.owner.has_tag(_DOUBLE_MOVEMENT_TAG):
            self.owner.remove_tags(_DOUBLE_MOVEMENT_TAG)
            ctx.move_count *= 2

class _LynaeRollEffectCleanup(Effect):
    """As a safety net, removes lingering effect tags"""

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.ROUND_END)

    def can_trigger(self, ctx: RoundEndContext) -> bool:
        return self.owner.has_tag("lynae", exact=False)

    def apply(self, ctx: RoundEndContext) -> None:
        self.owner.remove_tags("lynae", exact=False)

class Lynae(CubeBase):
    """60% chance to double the roll; 20% chance to stay still; 20% normal."""

    CUBE_TYPE: ClassVar[str] = "Lynae"

    def _setup_effects(self) -> None:
        self._register(_LynaeRollCheck(self))
        self._register(_LynaeRollApply(self))
        self._register(_LynaeRollEffectCleanup(self))
