"""
snake.py

Snake+ Snake entity:
- Player movement with walls (no wrap)
- Growth
- Self-bite detection
- Health + invincibility frames (damage flash)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Deque, Iterable, Optional

from collections import deque

import constants as C
from world import Cell, Grid


DIR_UP: Cell = (0, -1)
DIR_DOWN: Cell = (0, 1)
DIR_LEFT: Cell = (-1, 0)
DIR_RIGHT: Cell = (1, 0)


@dataclass
class FlashState:
    """
    Visual feedback for recent damage/absorb.
    """

    remaining_s: float
    color: tuple[int, int, int]


class Snake:
    """
    Grid snake represented by an ordered body list (head at index 0).

    The snake does not die to walls; positions are wrapped by Grid.
    """

    def __init__(self, grid: Grid) -> None:
        self.grid = grid
        self.body: Deque[Cell] = deque()
        self.direction: Cell = DIR_RIGHT
        self._pending_growth: int = 0
        self.hp: int = C.PLAYER_MAX_HP
        self.invincible_s: float = 0.0
        self.flash: Optional[FlashState] = None
        self.shield_active: bool = False

    def reset(self) -> None:
        """Reset to the starting snake state."""
        self.body.clear()
        hx = C.SNAKE_START_POS_X
        hy = C.SNAKE_START_POS_Y
        for i in range(C.SNAKE_START_LENGTH):
            self.body.append((hx - i, hy))
        self.direction = DIR_RIGHT
        self._pending_growth = 0
        self.hp = C.PLAYER_MAX_HP
        self.invincible_s = 0.0
        self.flash = None
        self.shield_active = False

    @property
    def head(self) -> Cell:
        """Current head cell."""
        return self.body[0]

    def occupies(self) -> Iterable[Cell]:
        """All occupied cells by the snake."""
        return self.body

    def length(self) -> int:
        """Current length."""
        return len(self.body)

    def set_direction(self, new_dir: Cell) -> None:
        """
        Update movement direction.
        180-degree reversals are ignored to prevent instant self-bite.
        """
        dx, dy = new_dir
        odx, ody = self.direction
        if (dx, dy) == (-odx, -ody):
            return
        self.direction = (dx, dy)

    def next_head_unwrapped(self) -> Cell:
        """Compute next head position without wrapping."""
        hx, hy = self.head
        dx, dy = self.direction
        return (hx + dx, hy + dy)

    def would_hit_wall(self) -> bool:
        """True if the next move would go out of bounds."""
        return not self.grid.in_bounds(self.next_head_unwrapped())

    def grow(self, amount: int) -> None:
        """Schedule growth by amount cells over future moves."""
        self._pending_growth += max(0, int(amount))

    def update_timers(self, dt_s: float) -> None:
        """Advance invincibility and flash timers."""
        if self.invincible_s > 0:
            self.invincible_s = max(0.0, self.invincible_s - dt_s)
        if self.flash:
            self.flash.remaining_s -= dt_s
            if self.flash.remaining_s <= 0:
                self.flash = None

    def is_invincible(self) -> bool:
        """Whether the snake is currently in invincibility frames."""
        return self.invincible_s > 0

    def flash_color(self) -> Optional[tuple[int, int, int]]:
        """Current flash color if active (damage red or shield white)."""
        return self.flash.color if self.flash else None

    def apply_shield(self) -> None:
        """Activate shield (absorbs one damage instance)."""
        self.shield_active = True

    def heal(self, amount: int) -> None:
        """Heal HP up to PLAYER_MAX_HP."""
        self.hp = min(C.PLAYER_MAX_HP, self.hp + max(0, int(amount)))

    def take_hit(self) -> str:
        """
        Apply a damage instance.

        Returns:
        - 'ignored' if invincible
        - 'absorbed' if shield consumed
        - 'damaged' if HP decreased
        """
        if self.is_invincible():
            return "ignored"
        if self.shield_active:
            self.shield_active = False
            self.invincible_s = C.INVINCIBILITY_DURATION_S
            self.flash = FlashState(remaining_s=C.INVINCIBILITY_DURATION_S, color=C.COLOR_SHIELD_FLASH)
            return "absorbed"

        self.hp = max(0, self.hp - 1)
        self.invincible_s = C.INVINCIBILITY_DURATION_S
        self.flash = FlashState(remaining_s=C.INVINCIBILITY_DURATION_S, color=C.COLOR_SNAKE_DAMAGE)
        return "damaged"

    def move_to(self, new_head: Cell) -> None:
        """
        Advance one step:
        - push new head
        - pop tail unless pending growth
        """
        self.body.appendleft(new_head)
        if self._pending_growth > 0:
            self._pending_growth -= 1
        else:
            self.body.pop()

    def teleport_head(self, new_head: Cell) -> None:
        """
        Teleport the snake head to new_head without changing direction.

        This is used by portals: after a normal move places the head on the
        entry portal, we replace that head cell with the exit portal cell.
        """
        if not self.body:
            return
        self.body.popleft()
        self.body.appendleft(new_head)

    def would_self_bite(self) -> bool:
        """
        Check if the next move would bite the body.

        When not growing on this move, the tail cell is about to vacate,
        so stepping into the current tail is allowed.
        """
        nxt = self.next_head_unwrapped()
        if len(self.body) <= 1:
            return False
        if self._pending_growth > 0:
            return nxt in list(self.body)[1:]
        # Not growing: exclude tail from collision set.
        return nxt in list(self.body)[1:-1]

