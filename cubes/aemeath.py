from __future__ import annotations

from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Step, TurnEndContext
from engine.track import TRACK_SIZE

_MIDPOINT_PAD = TRACK_SIZE // 2
_TAG = "aemeath.midpoint"


def _circular_distance(a: int, b: int) -> int:
    diff = abs(a - b)
    return min(diff, TRACK_SIZE - diff)


class _MidpointTeleport(Effect):
    """
    At the end of the turn Aemeath first crosses the midpoint (TRACK_SIZE // 2),
    she teleports on top of the closest non-Abbowser cube that is ahead of her.
    If no cube is ahead the teleport is held over and retried each subsequent
    TURN_END until one is available.  Triggers once per match.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Step.TURN_END)

    def matches(self, ctx: TurnEndContext) -> bool:
        return (
            ctx.active_cube is self.owner
            and self.owner.position >= _MIDPOINT_PAD
            and not self.owner.has_tag(_TAG, exact=True)
        )

    def apply(self, ctx: TurnEndContext) -> None:
        aemeath = self.owner
        game = ctx.game
        aemeath_dist = game.get_adjusted_distance(aemeath)

        candidates = [
            c for c in game.cubes
            if not c.is_abbowser
            and c is not aemeath
            and game.get_adjusted_distance(c) < aemeath_dist
        ]
        if not candidates:
            return  # no one ahead — hold the teleport for a later turn

        candidates.sort(
            key=lambda c: (
                _circular_distance(c.position, aemeath.position),
                game.get_adjusted_distance(c),
            )
        )
        aemeath.add_tag(_TAG, timestamp=game.round_number)
        aemeath.attach_above(candidates[0], game)


class Aemeath(CubeBase):
    """
    Teleports on top of the closest non-Abbowser cube ahead of her the first time
    she crosses the midpoint (TRACK_SIZE // 2).  If no cube is ahead, the teleport
    is held until one is.  Triggers once per match at TURN_END.
    """

    CUBE_TYPE: ClassVar[str] = "Aemeath"

    def _setup_effects(self) -> None:
        self._register(_MidpointTeleport(self))
