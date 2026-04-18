from __future__ import annotations

from typing import Tuple

from world import Cell


class Snake:
    def __init__(self, grid: object) -> None:
        """Attach snake to a grid instance."""
        self.hp: int = C.PLAYER_MAX_HP
        self.invincible_s: float = 0.0
        pass

    def reset(self) -> None:
        self.hp = C.PLAYER_MAX_HP #healh point system
        self.invincible_s = 0.0 #check invincibility time

    def update_timers(self, dt_s: float) -> None:
        if self.invincible_s > 0:
            self.invincible_s = max(0.0, self.invincible_s - dt_s)

    def is_invincible(self) -> bool:
        return self.invincible_s > 0

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
