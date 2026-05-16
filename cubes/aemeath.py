from __future__ import annotations

from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, TurnEndContext
from engine.track import TRACK_SIZE

_MIDPOINT_PAD = TRACK_SIZE // 2
_TAG = "aemeath.midpoint"


class _MidpointTeleport(Effect):
    """
    Checks if Aemeath has passed the midpoint and a non-Abbowser cube
    exists ahead by pad position. If so, teleports her to the top of
    the nearest stack ahead. Triggers at most once per match.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.TURN_END)

    def can_trigger(self, ctx: TurnEndContext) -> bool:
        aemeath_pos = ctx.game.get_adjusted_position(self.owner)

        return (
            ctx.active_cube is self.owner
            and aemeath_pos > _MIDPOINT_PAD
            and not self.owner.has_tag(_TAG)
            and any(
                ctx.game.get_adjusted_position(c) > aemeath_pos
                for c in ctx.game.cubes 
                if not c.is_abbowser and c is not self.owner
            )
        )

    def apply(self, ctx: TurnEndContext) -> None:
        game = ctx.game
        aemeath = self.owner
        aemeath_pos = game.get_adjusted_position(aemeath)

        candidates = [
            c for c in game.cubes
            if not c.is_abbowser and c is not aemeath
            and game.get_adjusted_position(c) > aemeath_pos
        ]

        if not candidates:
            return  # no one ahead — hold the teleport for a later turn (update: can_trigger should make this impossible now)

        target = min(candidates, key=game.get_adjusted_position)

        aemeath.add_tag(_TAG)
        aemeath.attach_above(target, game)


class Aemeath(CubeBase):
    """
    After passing the midpoint, if a non-Abbowser cube exists ahead (pad
    position, not ranking), teleports to the top of the nearest stack ahead.
    Can only trigger once per match.
    """

    CUBE_TYPE: ClassVar[str] = "Aemeath"

    def _setup_effects(self) -> None:
        self._register(_MidpointTeleport(self))
