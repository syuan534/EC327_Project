from __future__ import annotations

from collections import deque
from typing import Deque, Iterable

import constants as C
from world import Cell, Grid

DIR_UP = (0, -1)
DIR_DOWN = (0, 1)
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)


class Snake:
    def __init__(self, grid: Grid) -> None:
        self.grid = grid
        self.body: Deque[Cell] = deque()
        self.direction: Cell = DIR_RIGHT
        self._pending_growth: int = 0

    def reset(self) -> None:
        self.body.clear()
        hx, hy = C.SNAKE_START_X, C.SNAKE_START_Y
        for i in range(C.SNAKE_START_LENGTH):
            self.body.append((hx - i, hy))
        self.direction = DIR_RIGHT
        self._pending_growth = 0

    @property
    def head(self) -> Cell:
        return self.body[0]

    def occupies(self) -> Iterable[Cell]:
        return list(self.body)

    def set_direction(self, new_dir: Cell) -> None:
        dx, dy = new_dir
        ox, oy = self.direction
        if (dx, dy) == (-ox, -oy):
            return
        self.direction = (dx, dy)

    def next_head(self) -> Cell:
        hx, hy = self.head
        dx, dy = self.direction
        return (hx + dx, hy + dy)

    def would_hit_wall(self) -> bool:
        return not self.grid.in_bounds(self.next_head())

    def would_self_bite(self) -> bool:
        nxt = self.next_head()
        if len(self.body) <= 1:
            return False
        if self._pending_growth > 0:
            return nxt in list(self.body)[1:]
        return nxt in list(self.body)[1:-1]

    def move_to(self, new_head: Cell) -> None:
        self.body.appendleft(new_head)
        if self._pending_growth > 0:
            self._pending_growth -= 1
        else:
            self.body.pop()
