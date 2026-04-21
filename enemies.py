from __future__ import annotations

from typing import Set

from world import Cell


class EnemyManager:
    def __init__(self, grid: object) -> None:
        pass

    def reset(self) -> None:
        pass

    def occupied_cells(self) -> Set[Cell]:
        return set()

    def update(self, dt_s: float, score: int, snake_head: Cell, occupied_for_spawn: Set[Cell], blocked_for_chaser: Set[Cell]) -> None:
        pass

    def blocker_cells(self) -> Set[Cell]:
        return set()
