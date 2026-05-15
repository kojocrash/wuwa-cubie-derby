from __future__ import annotations

from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, TurnEndContext
from engine.track import TRACK_SIZE

_MIDPOINT_PAD = TRACK_SIZE // 2
_TAG = "aemeath.midpoint"


class _MidpointTeleport(Effect):
    """
    At the end of the turn Aemeath first crosses the midpoint (TRACK_SIZE // 2),
    she teleports to the top of the stack on the closest pad strictly ahead of her
    (higher pad number).  If no cube occupies a pad ahead, the teleport is held
    over and retried each subsequent TURN_END until one is available.
    Triggers once per match.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.TURN_END)

    def can_trigger(self, ctx: TurnEndContext) -> bool:
        return (
            ctx.active_cube is self.owner
            and ctx.game.get_adjusted_position(self.owner) > _MIDPOINT_PAD
            and not self.owner.has_tag(_TAG)
        )

    def apply(self, ctx: TurnEndContext) -> None:
        aemeath = self.owner
        game = ctx.game
        aemeath_adj = game.get_adjusted_position(aemeath)

        candidates = [
            c for c in game.cubes
            if not c.is_abbowser and c is not aemeath
            and game.get_adjusted_position(c) > aemeath_adj
        ]
        if not candidates:
            return  # no one ahead — hold the teleport for a later turn

        closest_adj = min(game.get_adjusted_position(c) for c in candidates)
        target = next(c for c in candidates if game.get_adjusted_position(c) == closest_adj)

        aemeath.add_tag(_TAG)
        aemeath.attach_above(target, game)


class Aemeath(CubeBase):
    """
    Teleports to the top of the closest stack ahead of her the first time she crosses
    the midpoint (TRACK_SIZE // 2).  If no cube is ahead, the teleport is held until
    one is.  Triggers once per match at TURN_END.
    """

    CUBE_TYPE: ClassVar[str] = "Aemeath"

    def _setup_effects(self) -> None:
        self._register(_MidpointTeleport(self))
