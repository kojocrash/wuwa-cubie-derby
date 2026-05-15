from __future__ import annotations

from typing import ClassVar

from engine.cube_base import CubeBase
from engine.effect_system import Effect, Phase, PadEffectContext
from engine.track import PadType

class _LuukPadEffect(Effect):
    """
    Amplifies the pad effect when Luuk lands on a Thruster or Blocker.
    
    Thruster: advances 3 *extra* pads. 
    
    Blocker: retreats 1 *extra* pad.
    """
    def __init__(self, owner: CubeBase) -> None:
        super().__init__(owner, Phase.PAD_EFFECT)

    def can_trigger(self, ctx: PadEffectContext) -> bool:
        return ctx.active_cube is self.owner and ctx.pad_type in [PadType.THRUSTER, PadType.BLOCKER]

    def apply(self, ctx: PadEffectContext) -> None:
        if ctx.pad_type == PadType.THRUSTER:
            ctx.push_pads += 3
        elif ctx.pad_type == PadType.BLOCKER:
            ctx.push_pads += 1

class Luuk(CubeBase):
    """
    When Luuk himself lands on a Thruster or Blocker pad, he overrides
    the standard pad effect — advancing 3 *extra* pads on a Thruster
    and retreating 1 *extra* pad on a Blocker.
    """

    CUBE_TYPE: ClassVar[str] = "Luuk"

    def _setup_effects(self) -> None:
        self._register(_LuukPadEffect(self))
