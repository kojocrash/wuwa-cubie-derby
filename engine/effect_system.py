from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game import Game
    from .cube_base import CubeBase


class Step(Enum):
    TURN_ORDER   = "turn_order"    # before each round: effects can reorder turn_order list
    ROLL_POST    = "roll_post"     # after base_roll(); effects modify roll value
    PRE_MOVE     = "pre_move"      # before movement loop; effects can modify total_pads
    STEP_PRE     = "step_pre"      # before each individual pad step
    STEP_POST    = "step_post"     # after each individual pad step (stacking/AB pickup)
    FINISH_CHECK = "finish_check"  # on forward crossing of pad 0; effects can suppress
    PAD_EFFECT   = "pad_effect"    # window after landing-pad trigger resolves
    TURN_END     = "turn_end"      # after full turn including pad effects
    ROUND_END    = "round_end"     # after all cubes in a round have moved


# ---------------------------------------------------------------------------
# Context hierarchy
# ---------------------------------------------------------------------------

@dataclass
class EffectContext:
    """Base for all per-step contexts."""
    game: Game
    active_cube: CubeBase | None = None  # None for round-level steps


@dataclass
class TurnOrderContext(EffectContext):
    turn_order: list[CubeBase] = field(default_factory=list)  # mutable


@dataclass
class RollContext(EffectContext):
    roll: int = 0                         # mutable


@dataclass
class PreMoveContext(EffectContext):
    roll: int = 0
    total_pads: int = 0                   # mutable


@dataclass
class StepPreContext(EffectContext):
    pads_remaining: int = 0              # mutable
    stride: int = 1                      # mutable: sign=direction, magnitude=pads per step
    cancelled: bool = False              # mutable


@dataclass
class StepPostContext(EffectContext):
    pads_remaining: int = 0              # mutable
    stride: int = 1                      # sign=direction, magnitude=pads per step


@dataclass
class FinishCheckContext(EffectContext):
    stride: int = 1                      # stride that triggered this crossing
    finish_suppressed: bool = False      # mutable


@dataclass
class PadEffectContext(EffectContext):
    pass


@dataclass
class TurnEndContext(EffectContext):
    pass


@dataclass
class RoundEndContext(EffectContext):
    pass


# ---------------------------------------------------------------------------
# Effect base class
# ---------------------------------------------------------------------------

class Effect:
    def __init__(self, owner: CubeBase, step: Step, priority: int = 0) -> None:
        self.owner = owner
        self.step = step
        self.priority = priority

    def matches(self, ctx: EffectContext) -> bool:
        return True

    def apply(self, ctx: EffectContext) -> None:
        pass
