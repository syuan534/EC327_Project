"""
Enemies — version0 skeleton (no implementation).
"""

from __future__ import annotations

from typing import Set

from world import Cell


class EnemyManager:
    """Blockers and chaser; logic added in later versions."""

    def __init__(self, grid: object) -> None:
        pass

    def update(self, dt_s: float, score: int, snake_head: Cell, occupied_for_spawn: Set[Cell], blocked_for_chaser: Set[Cell]) -> None:
        pass

    def spawn_chaser(self) -> None:
        pass

    def draw(self, surface: object) -> None:
        pass
