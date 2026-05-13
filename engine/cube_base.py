from __future__ import annotations

import random
from typing import TYPE_CHECKING, ClassVar

from .tag_system import TagMixin
from .effect_system import Effect, Step

if TYPE_CHECKING:
    from .game import Game


class CubeBase(TagMixin):
    """
    Base class for all race participants.

    Subclasses override:
      - _setup_effects()  to register Effect instances via self._register()
      - base_roll()       to customise the raw dice (default: 1–3)

    Class attributes:
      CUBE_TYPE  — canonical type identifier; used by engine logic (e.g. "Abbowser" checks)
    """

    CUBE_TYPE: ClassVar[str] = ""

    @property
    def is_abbowser(self) -> bool:
        return self.CUBE_TYPE == "Abbowser"

    def __init__(self, name: str | None = None) -> None:
        self.__init_tags__()
        self.name: str = name if name is not None else type(self).CUBE_TYPE
        self.position: int = 0
        # laps_needed tracks how many forward finish-line crossings are required.
        # Starts at 1.  Incremented when AB carries this cube backward through pad 0.
        self.laps_needed: int = 1
        # Linked-list stack pointers
        self.above: CubeBase | None = None
        self.below: CubeBase | None = None
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
    # Stack traversal
    # ------------------------------------------------------------------

    def stack_above(self) -> list[CubeBase]:
        """All cubes above self in the current stack, bottom-to-top."""
        result, cur = [], self.above
        while cur is not None:
            result.append(cur)
            cur = cur.above
        return result

    def get_moving_unit(self) -> list[CubeBase]:
        """self + all cubes above it (the group that moves together)."""
        return [self] + self.stack_above()

    # ------------------------------------------------------------------
    # Movement convenience methods
    # ------------------------------------------------------------------

    def move_to(self, pad: int, game: Game) -> None:
        """Move self + stack-above to pad."""
        game.move_unit(self, pad)

    def attach_above(self, other: CubeBase, game: Game) -> None:
        """Detach only self from its current position and place on top of other's stack."""
        game._detach_single(self)
        game._append_to_top(self, other.position)
        self.position = other.position

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
