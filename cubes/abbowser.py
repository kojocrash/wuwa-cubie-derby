from __future__ import annotations

import random
from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import (
    Effect, Phase,
    TurnOrderContext, MovePostContext, RoundEndContext, PadEffectContext,
)
from engine.track import PadType


def _is_past_ab(cube: CubeBase, ab: CubeBase) -> bool:
    """
    True if *cube* is 'past' Abbowser in the forward race direction.
    Abbowser moves backward from pad 0; cubes with higher pad numbers have more
    forward progress and are considered past Abbowser.
    Pad 0 is the finish line — a cube there is always 'past' any non-zero Abbowser pos.
    """
    if ab.position == 0:
        return False
    if cube.position == 0:
        return True
    return cube.position > ab.position


class _SpatialRiftSink(Effect):
    """In any spatial rift Abbowser lands in, force him to the bottom of the proposed order."""

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.PAD_EFFECT, priority=-10)

    def can_trigger(self, ctx: PadEffectContext) -> bool:
        return ctx.pad_type == PadType.SPATIAL_RIFT and self.owner in ctx.new_order

    def apply(self, ctx: PadEffectContext) -> None:
        ctx.new_order.remove(self.owner)
        ctx.new_order.insert(0, self.owner)


class _SitOut(Effect):
    """Abbowser doesn't take turns in rounds 1 and 2."""

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.TURN_ORDER)

    def can_trigger(self, ctx: TurnOrderContext) -> bool:
        return ctx.game.round_number < 3

    def apply(self, ctx: TurnOrderContext) -> None:
        ctx.turn_order = [c for c in ctx.turn_order if c is not self.owner]


class _TeleportToBottom(Effect):
    """
    After every step Abbowser takes, he sinks to the bottom of whatever stack he's in.
    This handles both landing on an existing stack and passing through one.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.MOVE_POST, priority=10)

    def can_trigger(self, ctx: MovePostContext) -> bool:
        return ctx.active_cube is self.owner

    def apply(self, ctx: MovePostContext) -> None:
        ctx.game.teleport_to_bottom(self.owner)


class _BackwardFinishCross(Effect):
    """
    When Abbowser steps backward onto pad 0, all non-Abbowser cubes he's carrying get
    their laps_needed incremented (they've been set back past the finish line).
    Fires after _TeleportToBottom so Abbowser is already at the bottom of the stack.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.MOVE_POST, priority=9)

    def can_trigger(self, ctx: MovePostContext) -> bool:
        return (
            ctx.active_cube is self.owner
            and ctx.stride < 0
            and self.owner.position == 0
        )

    def apply(self, ctx: MovePostContext) -> None:
        for cube in ctx.game.get_stack(0):
            if not cube.is_abbowser:
                cube.laps_needed += 1


class _SeparationTeleport(Effect):
    """
    At round end: if Abbowser is alone AND all other cubes are past him in the race
    direction, teleport Abbowser back to the finish line (pad 0).
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.ROUND_END)

    def can_trigger(self, ctx: RoundEndContext) -> bool:
        ab = self.owner
        game = ctx.game

        if ab.position == 0:
            return False

        if len(game.get_stack(ab.position)) > 1:
            return False

        return all(_is_past_ab(c, ab) for c in game.active_non_ab_cubes())

    def apply(self, ctx: RoundEndContext) -> None:
        ab = self.owner
        game = ctx.game
        game._detach_single(ab)
        ab.position = 0
        game._append_to_top(ab, 0)
        game.teleport_to_bottom(ab)


class AbbowserCube(CubeBase):
    """
    The chaos wildcard.  Moves backward (from finish toward start), rolls 1–6,
    always sinks to the bottom of any stack it joins, and teleports back to the
    finish line whenever separated from all other cubes at round end.
    Sits out rounds 1 and 2 entirely.
    """

    CUBE_TYPE: ClassVar[str] = "Abbowser"

    def base_roll(self) -> int:
        return random.randint(1, 6)

    def _setup_effects(self) -> None:
        self._register(_SpatialRiftSink(self))
        self._register(_SitOut(self))
        self._register(_TeleportToBottom(self))
        self._register(_BackwardFinishCross(self))
        self._register(_SeparationTeleport(self))
