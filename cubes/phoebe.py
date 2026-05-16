from __future__ import annotations

import random
from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, PreMoveContext

class _PhoebeMovementBonusEffect(Effect):
    """
    Rolls a 50% chance to advance Phoebe 1 extra pad.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.PRE_MOVE, priority=10)

    def can_trigger(self, ctx: PreMoveContext) -> bool:
        return ctx.active_cube is self.owner

    def apply(self, ctx: PreMoveContext) -> None:
        if random.random() < 0.5:
            ctx.move_count += 1

class Phoebe(CubeBase):
    """
    50% chance to advance 1 extra pad each turn.
    """

    CUBE_TYPE: ClassVar[str] = "Phoebe"

    def _setup_effects(self) -> None:
        self._register(_PhoebeMovementBonusEffect(self))
