"""
enemies.py — version3_steven_a

Blockers + chaser snake (BFS, no wrap). On player touch: chaser repositions
at least CHASER_RETREAT_MIN_MANHATTAN cells from player (hunt continues).
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass
from typing import Deque, Dict, List, Optional, Set, Tuple

import constants as C
from world import Cell, Grid, manhattan


@dataclass
class Blocker:
    pos: Cell


def bfs_next_step_nowrap(grid: Grid, start: Cell, goal: Cell, blocked: Set[Cell]) -> Optional[Cell]:
    if start == goal:
        return start

    q: Deque[Cell] = deque([start])
    came: Dict[Cell, Optional[Cell]] = {start: None}

    while q:
        cur = q.popleft()
        if cur == goal:
            break
        for nb in grid.neighbors4(cur, wrap=False):
            if nb in blocked and nb != goal:
                continue
            if nb not in came:
                came[nb] = cur
                q.append(nb)

    if goal not in came:
        return None

    cur = goal
    prev = came[cur]
    while prev is not None and prev != start:
        cur = prev
        prev = came[cur]
    return cur if prev == start else None


@dataclass
class ChaserSnake:
    body: Deque[Cell]

    @property
    def head(self) -> Cell:
        return self.body[0]


class EnemyManager:
    def __init__(self, grid: Grid) -> None:
        self.grid = grid
        self.blockers: List[Blocker] = []
        self._t_blocker: float = 0.0
        self._tick: int = 0
        self.chaser: Optional[ChaserSnake] = None
        self.chaser_phase: str = "idle"
        self.chaser_phase_remaining_s: float = 0.0

    def reset(self) -> None:
        self.blockers = []
        self._t_blocker = 0.0
        self._tick = 0
        self.chaser = None
        self.chaser_phase = "idle"
        self.chaser_phase_remaining_s = 0.0

    def occupied_cells(self) -> Set[Cell]:
        occ: Set[Cell] = {b.pos for b in self.blockers}
        if self.chaser:
            occ.update(self.chaser.body)
        return occ

    def blocker_cells(self) -> Set[Cell]:
        return {b.pos for b in self.blockers}

    def update(
        self,
        dt_s: float,
        score: int,
        snake_head: Cell,
        occupied_for_spawn: Set[Cell],
        blocked_for_chaser: Set[Cell],
    ) -> None:
        self._tick += 1
        self._update_blockers(dt_s, score, occupied_for_spawn)
        base_occ = set(occupied_for_spawn) | self.blocker_cells()
        self._update_chaser_cycle(dt_s, score, snake_head, base_occ, blocked_for_chaser)

    def _update_blockers(self, dt_s: float, score: int, occupied_for_spawn: Set[Cell]) -> None:
        if score < C.SCORE_BLOCKER_START:
            return
        self._t_blocker += dt_s
        if self._t_blocker >= C.BLOCKER_SPAWN_INTERVAL_S:
            self._t_blocker -= C.BLOCKER_SPAWN_INTERVAL_S
            if len(self.blockers) < C.BLOCKER_MAX_COUNT:
                self._spawn_blocker(occupied_for_spawn | self.occupied_cells())

    def _spawn_blocker(self, occupied: Set[Cell]) -> bool:
        pos = self.grid.random_empty_cell(occupied)
        if pos is None:
            return False
        self.blockers.append(Blocker(pos=pos))
        return True

    def _update_chaser_cycle(
        self,
        dt_s: float,
        score: int,
        snake_head: Cell,
        occupied: Set[Cell],
        blocked_for_chaser: Set[Cell],
    ) -> None:
        if score < C.SCORE_CHASER_SNAKE_APPEAR:
            self.chaser = None
            self.chaser_phase = "idle"
            self.chaser_phase_remaining_s = 0.0
            return

        if self.chaser_phase == "idle":
            self.chaser_phase = "cooldown"
            self.chaser_phase_remaining_s = 0.0

        if self.chaser_phase == "cooldown":
            if self.chaser_phase_remaining_s > 0:
                self.chaser_phase_remaining_s -= dt_s
            if self.chaser_phase_remaining_s <= 0:
                if self._spawn_chaser_at_edge(snake_head, occupied):
                    self.chaser_phase = "hunt"
                    self.chaser_phase_remaining_s = C.CHASER_HUNT_DURATION_S
                else:
                    self.chaser_phase_remaining_s = 0.05
            return

        if self.chaser_phase == "hunt":
            self.chaser_phase_remaining_s -= dt_s
            self._move_chaser(snake_head, blocked_for_chaser)
            if self.chaser_phase_remaining_s <= 0:
                self.chaser = None
                self.chaser_phase = "cooldown"
                self.chaser_phase_remaining_s = C.CHASER_COOLDOWN_S

    def _edge_cells(self) -> List[Cell]:
        n = self.grid.size
        cells: List[Cell] = []
        for x in range(n):
            cells.append((x, 0))
            cells.append((x, n - 1))
        for y in range(1, n - 1):
            cells.append((0, y))
            cells.append((n - 1, y))
        return cells

    def _build_chaser_body(self, head: Cell, occupied: Set[Cell], seg_count: int) -> Optional[Deque[Cell]]:
        hx, hy = head
        dx_candidates = (1, -1) if hx <= self.grid.size // 2 else (-1, 1)
        for dx in dx_candidates:
            segs: List[Cell] = []
            ok = True
            for i in range(seg_count):
                x = hx + dx * i
                y = hy
                if not self.grid.in_bounds((x, y)) or (x, y) in occupied:
                    ok = False
                    break
                segs.append((x, y))
            if ok:
                return deque(segs)
        return None

    def _spawn_chaser_at_edge(self, player_head: Cell, occupied: Set[Cell]) -> bool:
        candidates = [c for c in self._edge_cells() if c not in occupied and manhattan(c, player_head) >= C.CHASER_MIN_SPAWN_DISTANCE]
        random.shuffle(candidates)
        for head in candidates:
            body = self._build_chaser_body(head, occupied, C.CHASER_FIXED_LENGTH)
            if body:
                self.chaser = ChaserSnake(body=body)
                return True
        return False

    def retreat_chaser_from_player(self, player_head: Cell, occupied_for_spawn: Set[Cell]) -> None:
        """After a hit, move chaser so all segments are >= retreat distance from player (still hunting)."""
        if not self.chaser or self.chaser_phase != "hunt":
            return
        occ = set(occupied_for_spawn) | self.blocker_cells()
        for c in list(self.chaser.body):
            occ.discard(c)

        edge_pool = [c for c in self._edge_cells() if c not in occ and manhattan(c, player_head) >= C.CHASER_RETREAT_MIN_MANHATTAN]
        random.shuffle(edge_pool)
        for head in edge_pool[:60]:
            body = self._build_chaser_body(head, occ, C.CHASER_FIXED_LENGTH)
            if body:
                self.chaser = ChaserSnake(body=body)
                return

        for _ in range(250):
            h = self.grid.random_empty_cell(occ)
            if h is None:
                break
            if manhattan(h, player_head) < C.CHASER_RETREAT_MIN_MANHATTAN:
                continue
            body = self._build_chaser_body(h, occ, C.CHASER_FIXED_LENGTH)
            if body:
                self.chaser = ChaserSnake(body=body)
                return

    def _move_chaser(self, player_head: Cell, blocked_for_chaser: Set[Cell]) -> None:
        if not self.chaser:
            return
        ch = self.chaser
        if self._tick % C.CHASER_SNAKE_MOVE_EVERY_TICKS != 0:
            return

        blocked = set(blocked_for_chaser) | self.blocker_cells() | set(ch.body)
        step = bfs_next_step_nowrap(self.grid, ch.head, player_head, blocked)
        if step is None:
            nbs = [nb for nb in self.grid.neighbors4(ch.head, wrap=False) if nb not in blocked]
            if not nbs:
                return
            step = random.choice(nbs)

        ch.body.appendleft(step)
        ch.body.pop()

    def player_touched_chaser(self, player_head: Cell) -> bool:
        if not self.chaser:
            return False
        return player_head in self.chaser.body

    def chaser_hud(self) -> Tuple[str, float, str]:
        if self.chaser_phase == "hunt":
            return ("hunt", max(0.0, self.chaser_phase_remaining_s), "")
        if self.chaser_phase == "cooldown":
            return ("cooldown", max(0.0, self.chaser_phase_remaining_s), "")
        return ("idle", 0.0, "")
