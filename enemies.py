from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Set
import constants as C
from world import Cell, Grid

@dataclass
class Blocker:
    pos: Cell

class EnemyManager:
    def __init__(self, grid: Grid) -> None:
        self.grid = grid
        self.blockers: List[Blocker] = []
        self._t_blocker: float = 0.0

    def reset(self) -> None:
        self.blockers = []
        self._t_blocker = 0.0

    def occupied_cells(self) -> Set[Cell]:
        return {b.pos for b in self.blockers}
    
    def update(self, dt_s: float, score: int, occupied_for_spawn: Set[Cell]) -> None:
        if score < C.SCORE_BLOCKER_START:
            return
        self._t_blocker += dt_s
        if self._t_blocker >= C.BLOCKER_SPAWN_INTERVAL_S:
            self._t_blocker -= C.BLOCKER_SPAWN_INTERVAL_S
            if len(self.blockers) < C.BLOCKER_MAX_COUNT:
                occ = occupied_for_spawn | self.occupied_cells()
                p = self.grid.random_empty_cell(occ)
                if p is not None:
                    self.blockers.append(Blocker(pos=p))

    def blocker_cells(self) -> Set[Cell]:
        return {b.pos for b in self.blockers}
    

