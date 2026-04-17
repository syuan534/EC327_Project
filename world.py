"""
World grid — version0 skeleton (no implementation).
"""

from __future__ import annotations

from typing import Iterable, List, Set

Cell = tuple[int, int]


class Grid:
    """2D arena grid; methods to be implemented in later versions."""

    def __init__(self, size: int = 28) -> None:
        """Create a grid of `size` x `size` cells."""
        self.size = size

    def wrap(self, cell: Cell) -> Cell:
        """Wrap coordinates for torus topology."""
        pass

    def neighbors4(self, cell: Cell) -> List[Cell]:
        """Return the four orthogonal neighbors of `cell`."""
        pass

    def is_valid(self, cell: Cell) -> bool:
        """Return True if `cell` is inside the arena."""
        pass

    def occupied(self, cells: Iterable[Cell]) -> Set[Cell]:
        """Placeholder: normalize or copy an occupied cell iterable."""
        pass
