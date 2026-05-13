from __future__ import annotations

from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, TurnEndContext
from engine.track import TRACK_SIZE

_MIDPOINT_PAD = TRACK_SIZE // 2
_TAG = "iuno.gather"


class _GatherAtMidpoint(Effect):
    """
    At TURN_END, the first time Iuno is at or past the midpoint with at least one
    non-Abbowser cube ahead (higher pad number), all non-Abbowser cubes are
    teleported to Iuno's pad.  The new stack is ordered by their pre-teleport
    positions: furthest behind at the bottom, furthest ahead at the top.

    If no cube is ahead when Iuno crosses, the effect is held and retried each
    subsequent TURN_END until a valid target exists.  Triggers once per match.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.TURN_END)

    def can_trigger(self, ctx: TurnEndContext) -> bool:
        iuno = self.owner
        if ctx.active_cube is not iuno:
            return False
        if iuno.position < _MIDPOINT_PAD:
            return False
        if iuno.has_tag(_TAG, exact=True):
            return False
        return any(
            c.position > iuno.position
            for c in ctx.game.cubes
            if not c.is_abbowser and c is not iuno
        )

    def apply(self, ctx: TurnEndContext) -> None:
        iuno = self.owner
        game = ctx.game
        target_pad = iuno.position

        # Collect non-Abbowser cubes in bottom-to-top stack order, pad by pad
        # (ascending pad = further behind = will end up lower in the new stack)
        cubes_ordered: list[CubeBase] = []
        for pad in sorted(set(c.position for c in game.cubes if not c.is_abbowser)):
            for cube in game.get_stack(pad):
                if not cube.is_abbowser:
                    cubes_ordered.append(cube)

        # Detach every non-Abbowser cube from its current position
        for cube in cubes_ordered:
            game._detach_single(cube)

        # Rebuild the stack at target_pad in sorted order; Abbowser (if present)
        # remains at the bottom since he was never touched
        for cube in cubes_ordered:
            game._append_to_top(cube, target_pad)
            cube.position = target_pad

        iuno.add_tag(_TAG)


class Iuno(CubeBase):
    """
    Once per match: when Iuno first reaches or passes the midpoint (TRACK_SIZE // 2)
    with at least one cube ahead, all non-Abbowser cubes are pulled to her pad and
    restacked by their pre-teleport positions (behind → bottom, ahead → top).
    Held if no one is ahead; fires at TURN_END.
    """

    CUBE_TYPE: ClassVar[str] = "Iuno"

    def _setup_effects(self) -> None:
        self._register(_GatherAtMidpoint(self))
