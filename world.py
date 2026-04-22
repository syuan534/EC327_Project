"""Grid — bounded arena."""
from __future__ import annotations

import random
from typing import Iterator, List, Optional, Set

Cell = tuple[int, int]


class Grid:
    def __init__(self, size: int) -> None:
        self.size = size

    def in_bounds(self, cell: Cell) -> bool:
        x, y = cell
        return 0 <= x < self.size and 0 <= y < self.size

    def neighbors4(self, cell: Cell) -> List[Cell]:
        x, y = cell
        cand = [(x, y - 1), (x, y + 1), (x - 1, y), (x + 1, y)]
        return [c for c in cand if self.in_bounds(c)]

    def iter_all(self) -> Iterator[Cell]:
        for y in range(self.size):
            for x in range(self.size):
                yield (x, y)

    def random_empty_cell(self, occupied: Set[Cell]) -> Optional[Cell]:
        total = self.size * self.size
        if len(occupied) >= total:
            return None
        for _ in range(self.size * 8):
            c = (random.randrange(self.size), random.randrange(self.size))
            if c not in occupied:
                return c
        pool = [c for c in self.iter_all() if c not in occupied]
        return random.choice(pool) if pool else None
