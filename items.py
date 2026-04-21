from __future__ import annotations

from typing import Dict, List, Set

import constants as C
from world import Cell, Grid


class ItemManager:
    def __init__(self, grid: Grid) -> None:
        self.grid = grid
        self.normal_food: List[Cell] = []
        self._retry_accum_s: float = 0.0

    def reset(self, occupied: Set[Cell]) -> None:
        self.normal_food = []
        self._retry_accum_s = 0.0
        while len(self.normal_food) < C.NORMAL_FOOD_COUNT:
            occ = occupied | set(self.normal_food)
            p = self.grid.random_empty_cell(occ)
            if p is None:
                break
            self.normal_food.append(p)

    def update(self, dt_s: float, occupied: Set[Cell], snake_head: Cell, player_hp: int, score: int) -> None:
        _ = (snake_head, player_hp, score)
        self._retry_accum_s += dt_s
        while self._retry_accum_s >= C.FOOD_RESPAWN_TRY_INTERVAL_S and len(self.normal_food) < C.NORMAL_FOOD_COUNT:
            self._retry_accum_s -= C.FOOD_RESPAWN_TRY_INTERVAL_S
            occ = occupied | set(self.normal_food)
            p = self.grid.random_empty_cell(occ)
            if p is None:
                break
            self.normal_food.append(p)

    def occupied_cells(self) -> Set[Cell]:
        return set(self.normal_food)

    def try_collect_at_head(self, head: Cell) -> Dict[str, int]:
        if head not in self.normal_food:
            return {}
        self.normal_food = [p for p in self.normal_food if p != head]
        return {"score": C.SCORE_FOOD_NORMAL, "grow": C.GROW_FOOD_NORMAL}