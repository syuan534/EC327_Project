from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Set

import constants as C
from world import Cell, Grid

@dataclass
class TimedItem:
    pos: Cell
    remaining_s: float


class ItemManager:
    def __init__(self, grid: Grid) -> None:
        self.grid = grid
        self.normal_food: List[Cell] = []
        self.golden_foods: List[TimedItem] = []
        self._t: float = 0.0
        self._retry_accum_s: float = 0.0
        self._golden_spawn_accum_s: float = 0.0

    def reset(self, occupied: Set[Cell]) -> None:
        self.normal_food = []
        self.golden_foods = []
        self._t = 0.0
        self._retry_accum_s = 0.0
        self._golden_spawn_accum_s = 0.0
        while len(self.normal_food) < C.NORMAL_FOOD_COUNT:
            occ = occupied | set(self.normal_food) | {g.pos for g in self.golden_foods}
            p = self.grid.random_empty_cell(occ)
            if p is None:
                break
            self.normal_food.append(p)

    def update(self, dt_s: float, occupied: Set[Cell], snake_head: Cell, player_hp: int, score: int) -> None:
        _ = (snake_head, player_hp, score)
        self._t += dt_s
        self._retry_accum_s += dt_s
        while self._retry_accum_s >= C.FOOD_RESPAWN_TRY_INTERVAL_S and len(self.normal_food) < C.NORMAL_FOOD_COUNT:
            self._retry_accum_s -= C.FOOD_RESPAWN_TRY_INTERVAL_S
            occ = occupied | set(self.normal_food) | {g.pos for g in self.golden_foods}
            p = self.grid.random_empty_cell(occ)
            if p is None:
                break
            self.normal_food.append(p)

        for g in self.golden_foods:
            g.remaining_s -= dt_s
        self.golden_foods = [g for g in self.golden_foods if g.remaining_s > 0]

        self._golden_spawn_accum_s += dt_s
        while self._golden_spawn_accum_s >= C.GOLDEN_FOOD_SPAWN_INTERVAL_S:
            self._golden_spawn_accum_s -= C.GOLDEN_FOOD_SPAWN_INTERVAL_S
            if len(self.golden_foods) < C.GOLDEN_FOOD_MAX and random.random() < C.GOLDEN_FOOD_SPAWN_CHANCE_PER_CHECK:
                occ = occupied | set(self.normal_food) | {g.pos for g in self.golden_foods}
                p = self.grid.random_empty_cell(occ)
                if p is not None:
                    self.golden_foods.append(TimedItem(pos=p, remaining_s=C.GOLDEN_FOOD_DURATION_S))

    def occupied_cells(self) -> Set[Cell]:
        occ: Set[Cell] = set(self.normal_food)
        for g in self.golden_foods:
            occ.add(g.pos)
        return occ

    def golden_alpha(self) -> int:
        lo, hi = C.GOLDEN_FOOD_PULSE_ALPHA_MIN, C.GOLDEN_FOOD_PULSE_ALPHA_MAX
        amp = (hi - lo) * 0.5
        mid = lo + amp
        v = mid + amp * math.sin(self._t * (math.tau * C.GOLDEN_FOOD_PULSE_SPEED * 0.25))
        return int(max(lo, min(hi, v)))
    
    def try_collect_at_head(self, head: Cell) -> Dict[str, int]:
        effects: Dict[str, int] = {}
        if head in self.normal_food:
            self.normal_food = [p for p in self.normal_food if p != head]
            effects["score"] = C.SCORE_FOOD_NORMAL
            effects["grow"] = C.GROW_FOOD_NORMAL
        for g in self.golden_foods:
            if g.pos == head:
                self.golden_foods = [x for x in self.golden_foods if x.pos != head]
                effects["score"] = effects.get("score", 0) + C.SCORE_FOOD_GOLDEN
                effects["grow"] = effects.get("grow", 0) + C.GROW_FOOD_GOLDEN
                effects["golden"] = 1
                break
        return effects