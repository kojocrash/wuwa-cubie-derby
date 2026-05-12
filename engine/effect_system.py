from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .game_state import GameState
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


@dataclass
class EffectContext:
    game: GameState
    step: Step
    active_cube: CubeBase | None = None  # None for round-level steps (TURN_ORDER, ROUND_END)
    subject_cube: CubeBase | None = None

    # Mutable fields — effects read and write these
    roll: int = 0
    total_pads: int = 0
    pads_remaining: int = 0
    direction: int = 1           # +1 forward, -1 backward
    finish_triggered: bool = False
    finish_suppressed: bool = False
    cancelled: bool = False
    data: dict = field(default_factory=dict)   # step-specific extras


class Effect:
    step: Step
    priority: int = 0  # higher priority fires first among same-step effects

    def __init__(self, owner: CubeBase, step: Step, priority: int = 0) -> None:
        self.owner = owner
        self.step = step
        self.priority = priority

    def condition(self, ctx: EffectContext) -> bool:
        return True

    def apply(self, ctx: EffectContext) -> None:
        pass
