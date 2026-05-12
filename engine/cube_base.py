from __future__ import annotations

import random
from typing import TYPE_CHECKING

from .tag_system import TagMixin
from .effect_system import Effect, Step

if TYPE_CHECKING:
    pass


class CubeBase(TagMixin):
    """
    Base class for all race participants.

    Subclasses override:
      - _setup_effects()  to register Effect instances via self._register()
      - base_roll()       to customise the raw dice (default: 1–3)

    Class attributes:
      IS_ABBOWSER  — set True only on AbbowserCube; gates AB-specific logic
    """

    IS_ABBOWSER: bool = False

    def __init__(self, name: str) -> None:
        self.__init_tags__()
        self.name = name
        self.position: int = 0
        # laps_needed tracks how many forward finish-line crossings are required.
        # Starts at 1.  Incremented when AB carries this cube backward through pad 0.
        self.laps_needed: int = 1
        self.effects: list[Effect] = []
        self._setup_effects()

    # ------------------------------------------------------------------
    # Subclass API
    # ------------------------------------------------------------------

    def _setup_effects(self) -> None:
        """Register effects here in subclasses."""

    def base_roll(self) -> int:
        """Raw dice roll before any effect modifications.  Default: 1–3."""
        return random.randint(1, 3)

    # ------------------------------------------------------------------
    # Effect helpers
    # ------------------------------------------------------------------

    def _register(self, effect: Effect) -> None:
        self.effects.append(effect)

    def get_effects(self, step: Step) -> list[Effect]:
        return sorted(
            [e for e in self.effects if e.step == step],
            key=lambda e: -e.priority,
        )

    # ------------------------------------------------------------------
    # Misc
    # ------------------------------------------------------------------

    def __repr__(self) -> str:
        return f"{self.name}@{self.position}"
