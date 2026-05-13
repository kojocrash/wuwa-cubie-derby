from __future__ import annotations

from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Step, StepPostContext
from engine.track import TRACK_SIZE

_MIDPOINT_PAD = 16
_TAG = "aemeath.midpoint"


def _circular_distance(a: int, b: int) -> int:
    diff = abs(a - b)
    return min(diff, TRACK_SIZE - diff)


class _MidpointTeleport(Effect):
    """
    When Aemeath first steps onto pad 16 (the midpoint), she teleports on top
    of the closest non-AB cube (skipping AB if it would be closest).
    Triggers only once per match.  Cancels any remaining movement this turn.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Step.STEP_POST)

    def matches(self, ctx: StepPostContext) -> bool:
        return (
            ctx.active_cube is self.owner
            and self.owner.position == _MIDPOINT_PAD
            and not self.owner.has_tag(_TAG, exact=True)
        )

    def apply(self, ctx: StepPostContext) -> None:
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
        ctx.pads_remaining = 0


class Aemeath(CubeBase):
    """
    When reaching pad 16 (midpoint), teleports on top of the closest non-AB cube.
    Triggers once per match.
    """

    CUBE_TYPE: ClassVar[str] = "Aemeath"

    def _setup_effects(self) -> None:
        self._register(_MidpointTeleport(self))
