from __future__ import annotations

from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, RollContext, PreMoveContext, RoundEndContext

_TAG = "denia.movement_bonus"

class _DeniaRollTracker(Effect):
    """
    Checks if Denia's current roll matches her previous roll.
    If so, marks her to receive a movement bonus this turn.
    """
    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.ROLL_POST)
        self.last_roll = None

    def can_trigger(self, ctx: RollContext) -> bool:
        return self.owner in ctx.rolls

    def apply(self, ctx: RollContext) -> None:
        current_roll = ctx.rolls[self.owner]

        if current_roll == self.last_roll:
            self.owner.add_tag(_TAG)

        self.last_roll = current_roll

class _DeniaBonusMovementEffect(Effect):
    """
    Applies 2 extra pads of movement to Denia if she has been
    marked this turn.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.PRE_MOVE, priority=10)

    def can_trigger(self, ctx: PreMoveContext) -> bool:
        return (
            ctx.active_cube is self.owner
            and self.owner.has_tag(_TAG)
        )

    def apply(self, ctx: PreMoveContext) -> None:
        self.owner.remove_tags(_TAG)
        ctx.move_count += 2

class _DeniaEffectCleanup(Effect):
    """As a safety net, removes lingering effect tags"""

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.ROUND_END)

    def can_trigger(self, ctx: RoundEndContext) -> bool:
        return self.owner.has_tag("denia", exact=False)

    def apply(self, ctx: RoundEndContext) -> None:
        self.owner.remove_tags("denia", exact=False)

class Denia(CubeBase):
    """If the number rolled matches Denia's previous roll, she advances 2 extra pads."""

    CUBE_TYPE: ClassVar[str] = "Denia"

    def _setup_effects(self) -> None:
        self._register(_DeniaRollTracker(self))
        self._register(_DeniaBonusMovementEffect(self))
        self._register(_DeniaEffectCleanup(self))
