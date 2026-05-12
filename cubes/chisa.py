from __future__ import annotations

from engine.cube_base import CubeBase
from engine.effect_system import Effect, EffectContext, Step


class _LowestRollBonus(Effect):
    """If Chisa's roll is ≤ all other cubes' base rolls this round, +2 pads."""

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Step.ROLL_POST)

    def condition(self, ctx: EffectContext) -> bool:
        return ctx.active_cube is self.owner

    def apply(self, ctx: EffectContext) -> None:
        others = [v for k, v in ctx.game.round_rolls.items() if k != self.owner.name]
        if not others or ctx.roll <= min(others):
            ctx.roll += 2


class Chisa(CubeBase):
    """If this turn's roll is the lowest among all Cubes, advance 2 extra pads."""

    def _setup_effects(self) -> None:
        self._register(_LowestRollBonus(self))
