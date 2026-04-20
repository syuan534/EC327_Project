"""Stub enemy manager — no enemies in version1_patrick_b."""

from __future__ import annotations

from typing import Set

from world import Cell, Grid


class EnemyManager:
    def __init__(self, grid: Grid) -> None:
        _ = grid

    def reset(self) -> None:
        pass

    def occupied_cells(self) -> Set[Cell]:
        return set()

    def update(self, *args: object, **kwargs: object) -> None:
        pass

    def blocker_cells(self) -> Set[Cell]:
        return set()
