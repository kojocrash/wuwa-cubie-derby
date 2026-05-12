from __future__ import annotations

import random

from engine.cube_base import CubeBase
from engine.effect_system import Effect, EffectContext, Step


class _DoubleAdvance(Effect):
    """28% chance to double the rolled number (one move of 2×roll pads)."""

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Step.ROLL_POST)

    def condition(self, ctx: EffectContext) -> bool:
        return ctx.active_cube is self.owner

    def apply(self, ctx: EffectContext) -> None:
        if random.random() < 0.28:
            ctx.roll *= 2


class Carlotta(CubeBase):
    """28% chance to advance twice the rolled number."""

    def _setup_effects(self) -> None:
        self._register(_DoubleAdvance(self))
