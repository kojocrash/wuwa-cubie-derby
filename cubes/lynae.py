from __future__ import annotations

import random
from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, RollContext


class _LynaeRollModifier(Effect):
    """
    Three mutually exclusive outcomes after rolling:
      20% → stay still (roll = 0)
      60% → advance doubled (roll *= 2)
      20% → normal roll (unchanged)
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.ROLL_POST)

    def can_trigger(self, ctx: RollContext) -> bool:
        return ctx.cube is self.owner

    def apply(self, ctx: RollContext) -> None:
        r = random.random()
        if r < 0.20:
            ctx.roll = 0
        elif r < 0.80:
            ctx.roll *= 2
        # else: 20% — keep as-is


class Lynae(CubeBase):
    """60% chance to double the roll; 20% chance to stay still; 20% normal."""

    CUBE_TYPE: ClassVar[str] = "Lynae"

    def _setup_effects(self) -> None:
        self._register(_LynaeRollModifier(self))
