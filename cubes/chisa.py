from __future__ import annotations

from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, RollContext


class _LowestRollBonus(Effect):
    """If Chisa's roll is ≤ all other cubes' base rolls this round, +2 pads."""

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.ROLL_POST)

    def can_trigger(self, ctx: RollContext) -> bool:
        return ctx.active_cube is self.owner

    def apply(self, ctx: RollContext) -> None:
        others = [v for k, v in ctx.game.round_rolls.items() if k != self.owner.name]
        if not others or ctx.roll <= min(others):
            ctx.roll += 2


class Chisa(CubeBase):
    """If this turn's roll is the lowest among all Cubes, advance 2 extra pads."""

    CUBE_TYPE: ClassVar[str] = "Chisa"

    def _setup_effects(self) -> None:
        self._register(_LowestRollBonus(self))
