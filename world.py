"""
world.py

Grid / world helpers:
- Wraparound coordinates (no wall death)
- Occupied cell tracking helpers
- Random empty cell selection
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Iterable, Iterator, List, Optional, Sequence, Set, Tuple

import constants as C

Cell = Tuple[int, int]


@dataclass(frozen=True)
class Grid:
    """
    A 2D grid of size GRID_SIZE x GRID_SIZE.

    Snake+ supports two movement styles:
    - Player snake: walls exist (no wrap).
    - Chaser snake: wraparound movement (wrap).
    """

    size: int = C.GRID_SIZE

    def wrap(self, cell: Cell) -> Cell:
        """Wrap any (x, y) into [0, size) with torus topology."""
        x, y = cell
        return (x % self.size, y % self.size)

    def in_bounds(self, cell: Cell) -> bool:
        """True if cell is inside the arena bounds."""
        x, y = cell
        return 0 <= x < self.size and 0 <= y < self.size

    def neighbors4(self, cell: Cell, wrap: bool = True) -> List[Cell]:
        """
        4-connected neighbors (up, down, left, right).
        If wrap=True: neighbors wrap at edges.
        If wrap=False: out-of-bounds neighbors are excluded.
        """
        x, y = cell
        candidates = [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
        if wrap:
            return [self.wrap(c) for c in candidates]
        return [c for c in candidates if self.in_bounds(c)]

    def iter_all(self) -> Iterator[Cell]:
        """Yield all cells in row-major order."""
        for y in range(self.size):
            for x in range(self.size):
                yield (x, y)

    def random_empty_cell(self, occupied: Set[Cell]) -> Optional[Cell]:
        """
        Return a random empty cell not in occupied.
        Returns None if the grid is full.
        """
        total = self.size * self.size
        if len(occupied) >= total:
            return None

        # Fast path: try random sampling first.
        attempts = min(total, self.size * 8)
        for _ in range(attempts):
            c = (random.randrange(self.size), random.randrange(self.size))
            if c not in occupied:
                return c

        # Fallback: build candidate list.
        candidates = [c for c in self.iter_all() if c not in occupied]
        return random.choice(candidates) if candidates else None


def occupied_union(*groups: Iterable[Cell]) -> Set[Cell]:
    """Build a single occupied-set from multiple iterables."""
    occ: Set[Cell] = set()
    for g in groups:
        occ.update(g)
    return occ


def manhattan(a: Cell, b: Cell, size: int = C.GRID_SIZE) -> int:
    """
    Manhattan distance (non-wrapped).
    Used for radius checks where walls matter (magnet radius, damage queries, etc.).
    """
    ax, ay = a
    bx, by = b
    return abs(ax - bx) + abs(ay - by)


def manhattan_wrap(a: Cell, b: Cell, size: int = C.GRID_SIZE) -> int:
    """
    Wrapped Manhattan distance on a torus grid.
    Used for chaser snake heuristics and wraparound logic.
    """
    ax, ay = a
    bx, by = b
    dx = abs(ax - bx)
    dy = abs(ay - by)
    dx = min(dx, size - dx)
    dy = min(dy, size - dy)
    return dx + dy

