from __future__ import annotations

from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, MovePostContext, PreMoveContext

_TAG = "hiyuki.movement_bonus"

class _HiyukiEncounterObserver(Effect):
    """
    Monitors for Hiyuki encountering Abbowser on the track. When it occurs,
    flags her as having triggered the encounter.
    """
    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.MOVE_POST)

    def can_trigger(self, ctx: MovePostContext) -> bool:
        return (
            ctx.active_cube is self.owner
            and not self.owner.has_tag(_TAG)
            and ctx.game.get_adjusted_position(self.owner) > 0
            and self.owner.position == ctx.game._abbowser.position
        )

    def apply(self, ctx: MovePostContext) -> None:
        self.owner.add_tag(_TAG)

class _HiyukiBonusMovementEffect(Effect):
    """
    Once the encounter flag is set, adds 1 extra pad to every
    subsequent move Hiyuki makes.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.PRE_MOVE, priority=10)

    def can_trigger(self, ctx: PreMoveContext) -> bool:
        return (
            ctx.active_cube is self.owner
            and self.owner.has_tag(_TAG)
        )

    def apply(self, ctx: PreMoveContext) -> None:
        ctx.move_count += 1

class Hiyuki(CubeBase):
    """After encountering Abbowser, Hiyuki gains a permanent +1 pad bonus for the rest of the game."""

    CUBE_TYPE: ClassVar[str] = "Hiyuki"

    def _setup_effects(self) -> None:
        self._register(_HiyukiEncounterObserver(self))
        self._register(_HiyukiBonusMovementEffect(self))
