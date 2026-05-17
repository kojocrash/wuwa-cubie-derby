from __future__ import annotations

import random
from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, TurnEndContext


class _TeleportToTop(Effect):
    """
    Checks if the moved cubes stacked above Jinhsi. If so, rolls a 40%
    chance to teleport her to the top of the stack.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.TURN_END, priority=4)

    def can_trigger(self, ctx: TurnEndContext) -> bool:
        return (
            ctx.active_cube is not self.owner
            and self.owner.above is not None
            and ctx.active_cube.position == self.owner.position
            and ctx.active_cube in self.owner.stack_above()
        )

    def apply(self, ctx: TurnEndContext) -> None:
        if random.random() < 0.40:
            ctx.game.teleport_to_top(self.owner)


class Jinhsi(CubeBase):
    """
    40% chance to float to the top of her stack at the end of any turn where a
    cube that shares her pad finishes moving and she has cubes above her.
    """

    CUBE_TYPE: ClassVar[str] = "Jinhsi"

    def _setup_effects(self) -> None:
        self._register(_TeleportToTop(self))
