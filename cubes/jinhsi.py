from __future__ import annotations

import random
from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, TurnEndContext


class _FloatToTop(Effect):
    """
    At the end of any cube's turn, if that cube shares Jinhsi's pad and at least
    one cube is above Jinhsi, there is a 40% chance she moves to the top of the
    stack.  Can trigger multiple times per round.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.TURN_END)

    def can_trigger(self, ctx: TurnEndContext) -> bool:
        return (
            ctx.active_cube.position == self.owner.position
            and self.owner.above is not None
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
        self._register(_FloatToTop(self))
