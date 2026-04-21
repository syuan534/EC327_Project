from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque, Iterable, Optional

import constants as C
from world import Cell, Grid

DIR_UP = (0, -1)
DIR_DOWN = (0, 1)
DIR_LEFT = (-1, 0)
DIR_RIGHT = (1, 0)

@dataclass
class FlashState:
    remaining_s: float
    color: tuple[int, int, int]

class Snake:
    def __init__(self, grid: Grid) -> None:
        self.grid = grid
        self.body: Deque[Cell] = deque()
        self.direction: Cell = DIR_RIGHT
        self._pending_growth: int = 0
        self.hp: int = C.PLAYER_MAX_HP
        self.invincible_s: float = 0.0
        self.flash: Optional[FlashState] = None


    def reset(self) -> None:
        self.body.clear()
        hx, hy = C.SNAKE_START_X, C.SNAKE_START_Y
        for i in range(C.SNAKE_START_LENGTH):
            self.body.append((hx - i, hy))
        self.direction = DIR_RIGHT
        self._pending_growth = 0
        self.hp = C.PLAYER_MAX_HP
        self.invincible_s = 0.0
        self.flash = None

    @property
    def head(self) -> Cell:
        return self.body[0]

    def occupies(self) -> Iterable[Cell]:
        return list(self.body)

    def length(self) -> int:
        return len(self.body)

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

    def grow(self, n: int) -> None:
        self._pending_growth += max(0, int(n))

    def update_timers(self, dt_s: float) -> None:
        if self.invincible_s > 0:
            self.invincible_s = max(0.0, self.invincible_s - dt_s)
        if self.flash:
            self.flash.remaining_s -= dt_s
            if self.flash.remaining_s <= 0:
                self.flash = None

    def is_invincible(self) -> bool:
        return self.invincible_s > 0
    
    def flash_color(self) -> Optional[tuple[int, int, int]]:
        return self.flash.color if self.flash else None
    
    def take_hit(self) -> str:
        if self.is_invincible():
            return "ignored"
        self.hp = max(0, self.hp - 1)
        self.invincible_s = C.INVINCIBILITY_DURATION_S
        self.flash = FlashState(remaining_s=C.INVINCIBILITY_DURATION_S, color=C.COLOR_SNAKE_DAMAGE)
        return "damaged"