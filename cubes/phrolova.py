from __future__ import annotations

from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, PreMoveContext


class _BottomStackBonus(Effect):
    """When Phrolova is at the bottom of a stack with at least one cube above, +3 moves."""

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.PRE_MOVE)

    def can_trigger(self, ctx: PreMoveContext) -> bool:
        return (
            ctx.active_cube is self.owner
            and self.owner.below is None
            and self.owner.above is not None
        )

    def apply(self, ctx: PreMoveContext) -> None:
        ctx.move_count += 3


class Phrolova(CubeBase):
    """Advances 3 extra pads when at the bottom of a stack at the start of her turn."""

    CUBE_TYPE: ClassVar[str] = "Phrolova"

    def _setup_effects(self) -> None:
        self._register(_BottomStackBonus(self))
