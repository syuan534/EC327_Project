from __future__ import annotations

from typing import Set

from world import Cell


class ItemManager:
    """Owns food and powerups; logic added in later versions."""

    def __init__(self, grid: object) -> None:
        pass

    def update(self, dt_s: float, occupied: Set[Cell], snake_head: Cell, player_hp: int, score: int) -> None:
        pass

    def spawn_food(self, occupied: Set[Cell]) -> None:
        pass

    def collect(self, head: Cell) -> dict:
        _ = head
        return {}

    def draw(self, surface: object) -> None:
        pass
