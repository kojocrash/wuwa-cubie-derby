from __future__ import annotations

from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, PreMoveContext


class _LastPlaceBonus(Effect):
    """If Calcharo is in last place when his turn starts, +3 moves."""

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.PRE_MOVE)

    def can_trigger(self, ctx: PreMoveContext) -> bool:
        return (
            ctx.active_cube is self.owner
            and ctx.game.get_ranking()[-1] is self.owner
        )

    def apply(self, ctx: PreMoveContext) -> None:
        ctx.move_count += 3


class Calcharo(CubeBase):
    """Advances 3 extra pads when in last place at the start of his turn."""

    CUBE_TYPE: ClassVar[str] = "Calcharo"

    def _setup_effects(self) -> None:
        self._register(_LastPlaceBonus(self))
