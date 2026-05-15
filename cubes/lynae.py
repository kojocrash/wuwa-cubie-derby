from __future__ import annotations

import random
from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, RollContext, PreMoveContext


class _LynaeRollCheck(Effect):
    """During the batch roll phase, tag Lynae with her outcome for this round."""

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.ROLL_POST)

    def can_trigger(self, ctx: RollContext) -> bool:
        return self.owner in ctx.rolls

    def apply(self, ctx: RollContext) -> None:
        r = random.random()
        if r < 0.20:
            self.owner.add_tag("lynae.still")
        elif r < 0.80:
            self.owner.add_tag("lynae.double")
        # else: 20% — no tag, normal roll


class _LynaeRollApply(Effect):
    """At the start of Lynae's turn, consume the outcome tag to adjust move count."""

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.PRE_MOVE, priority=10)

    def can_trigger(self, ctx: PreMoveContext) -> bool:
        return ctx.active_cube is self.owner and (
            self.owner.has_tag("lynae.still", exact=True)
            or self.owner.has_tag("lynae.double", exact=True)
        )

    def apply(self, ctx: PreMoveContext) -> None:
        if self.owner.has_tag("lynae.still", exact=True):
            self.owner.remove_tags("lynae.still", exact=True)
            ctx.move_count = 0
        elif self.owner.has_tag("lynae.double", exact=True):
            self.owner.remove_tags("lynae.double", exact=True)
            ctx.move_count *= 2


class Lynae(CubeBase):
    """60% chance to double the roll; 20% chance to stay still; 20% normal."""

    CUBE_TYPE: ClassVar[str] = "Lynae"

    def _setup_effects(self) -> None:
        self._register(_LynaeRollCheck(self))
        self._register(_LynaeRollApply(self))
