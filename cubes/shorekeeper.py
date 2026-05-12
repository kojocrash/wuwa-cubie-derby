from __future__ import annotations

import random

from engine.cube_base import CubeBase


class Shorekeeper(CubeBase):
    """Dice only rolls 2 or 3."""

    def base_roll(self) -> int:
        return random.randint(2, 3)
