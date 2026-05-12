from __future__ import annotations

import random

from engine.cube_base import CubeBase
from engine.effect_system import Effect, EffectContext, Step


def _is_past_ab(cube: CubeBase, ab: CubeBase) -> bool:
    """
    True if *cube* is 'past' AB in the forward race direction.
    AB moves backward from pad 0; cubes with higher pad numbers have more
    forward progress and are considered past AB.
    Pad 0 is the finish line — a cube there is always 'past' any non-zero AB pos.
    """
    if ab.position == 0:
        return False
    if cube.position == 0:
        return True
    return cube.position > ab.position


class _TeleportToBottom(Effect):
    """
    After every step AB takes, he sinks to the bottom of whatever stack he's in.
    This handles both landing on an existing stack and passing through one.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Step.STEP_POST, priority=10)

    def condition(self, ctx: EffectContext) -> bool:
        return ctx.active_cube is self.owner

    def apply(self, ctx: EffectContext) -> None:
        ctx.game.teleport_to_bottom(self.owner)


class _BackwardFinishCross(Effect):
    """
    When AB steps backward onto pad 0, all non-AB cubes he's carrying get
    their laps_needed incremented (they've been set back past the finish line).
    Fires after _TeleportToBottom so AB is already at the bottom of the stack.
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Step.STEP_POST, priority=9)

    def condition(self, ctx: EffectContext) -> bool:
        return (
            ctx.active_cube is self.owner
            and ctx.direction == -1
            and self.owner.position == 0
        )

    def apply(self, ctx: EffectContext) -> None:
        for cube in ctx.game.pads[0]:
            if not cube.IS_ABBOWSER:
                cube.laps_needed += 1


class _SeparationTeleport(Effect):
    """
    At round end: if AB is alone AND all other cubes are past him in the race
    direction, teleport AB back to the finish line (pad 0).
    """

    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Step.ROUND_END)

    def condition(self, ctx: EffectContext) -> bool:
        ab = self.owner
        game = ctx.game

        if ab not in game.cubes:
            return False
        if ab.position == 0:
            return False  # already at finish

        # AB must not be in a stack with others
        if len(game.pads[ab.position]) > 1:
            return False

        # All regular cubes must be past AB
        return all(_is_past_ab(c, ab) for c in game.active_non_ab_cubes())

    def apply(self, ctx: EffectContext) -> None:
        ab = self.owner
        game = ctx.game
        game.pads[ab.position].remove(ab)
        game.pads[0].insert(0, ab)
        ab.position = 0


class AbbowserCube(CubeBase):
    """
    The chaos wildcard.  Moves backward (from finish toward start), rolls 1–6,
    always sinks to the bottom of any stack it joins, and teleports back to the
    finish line whenever separated from all other cubes at round end.
    """

    IS_ABBOWSER: bool = True

    def base_roll(self) -> int:
        return random.randint(1, 6)

    def _setup_effects(self) -> None:
        self._register(_TeleportToBottom(self))
        self._register(_BackwardFinishCross(self))
        self._register(_SeparationTeleport(self))
