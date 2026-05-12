from __future__ import annotations

from engine.cube_base import CubeBase


_CYCLE = (3, 2, 1)


class Mornye(CubeBase):
    """Dice rolls 3, 2, 1 in repeating succession."""

    def __init__(self, name: str) -> None:
        self._turn_count: int = 0
        super().__init__(name)

    def base_roll(self) -> int:
        roll = _CYCLE[self._turn_count % 3]
        self._turn_count += 1
        return roll
