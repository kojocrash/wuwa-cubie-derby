from __future__ import annotations

import random
from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, TurnEndContext, PreMoveContext

_TAG = "cartethyia.bonus_triggered"

class _CartethyiaTriggerEffect(Effect):
    """
    Checks if Cartethyia is in last place after her movement ends.
    On success, marks her to roll for bonus movement each remaining turn.
    Triggers at most once per match.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.TURN_END)

    def can_trigger(self, ctx: TurnEndContext) -> bool:
        return (
            ctx.active_cube is self.owner
            and not self.owner.has_tag(_TAG)
            and ctx.game.get_ranking()[-1] is self.owner
        )

    def apply(self, ctx: TurnEndContext) -> None:
        self.owner.add_tag(_TAG)

class _CartethyiaBonusMovementEffect(Effect):
    """
    Each remaining turn after the trigger, rolls a 60% chance to advance
    Cartethyia 2 extra pads.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.PRE_MOVE, priority=10)

    def can_trigger(self, ctx: PreMoveContext) -> bool:
        return (
            ctx.active_cube is self.owner
            and self.owner.has_tag(_TAG)
        )

    def apply(self, ctx: PreMoveContext) -> None:
        if random.random() < 0.60:
            ctx.move_count += 2

class Cartethyia(CubeBase):
    """
    When Cartethyia finishes last after her own movement, each remaining turn there is
    a 60% chance she gains 2 extra pads of movement. Can only trigger once per match.
    """

    CUBE_TYPE: ClassVar[str] = "Cartethyia"

    def _setup_effects(self) -> None:
        self._register(_CartethyiaTriggerEffect(self))
        self._register(_CartethyiaBonusMovementEffect(self))
