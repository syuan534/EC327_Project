"""
Player snake — version0 skeleton (no implementation).
"""

from __future__ import annotations

from typing import Tuple

from world import Cell


class Snake:
    """Snake entity; logic added in later milestones."""

    def __init__(self, grid: object) -> None:
        """Attach snake to a grid instance."""
        pass

    def move(self) -> None:
        """Advance the snake one step in the current direction."""
        pass

    def grow(self, amount: int) -> None:
        """Schedule growth by `amount` segments."""
        pass

    def check_self_collision(self) -> bool:
        """Return True if the snake currently intersects itself."""
        pass

    @property
    def head(self) -> Cell:
        """Grid cell of the snake head."""
        pass
