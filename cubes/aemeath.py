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
    she teleports on top of the closest non-Abbowser cube.  Triggers once per match.
    Fires at TURN_END so the teleport happens after all movement and pad effects
    for that turn have resolved.  "Crosses" means her final position is at or past
    the midpoint, which handles strides greater than 1 skipping the exact pad.
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

        candidates = [
            c for c in game.cubes
            if not c.is_abbowser and c is not aemeath
        ]
        if not candidates:
            return

        candidates.sort(
            key=lambda c: (
                _circular_distance(c.position, aemeath.position),
                game.get_adjusted_distance(c),
            )
        )
        target = candidates[0]

        aemeath.add_tag(_TAG, timestamp=game.round_number)
        aemeath.attach_above(target, game)


class Aemeath(CubeBase):
    """
    Teleports on top of the closest non-Abbowser cube the first time she crosses
    the midpoint (TRACK_SIZE // 2).  Triggers once per match at TURN_END.
    """

    CUBE_TYPE: ClassVar[str] = "Aemeath"

    def _setup_effects(self) -> None:
        self._register(_MidpointTeleport(self))
