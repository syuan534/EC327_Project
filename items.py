"""
items.py

ItemManager:
- Spawns/despawns all item types on empty grid cells
- Handles timers/animations (golden food alpha pulse, portal glow timing)
- Applies item effects (growth/score, heart heal, multiplier, magnet, shield, portals)
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Dict, List, Optional, Set, Tuple

import constants as C
from world import Cell, Grid, manhattan


@dataclass
class TimedItem:
    """A grid item with an optional expiration timer."""

    kind: str
    pos: Cell
    remaining_s: float


@dataclass
class PortalPair:
    """A and B portal endpoints with a shared expiration timer."""

    a: Cell
    b: Cell
    remaining_s: float


class ItemManager:
    """
    Owns all items in the arena and their lifecycle.

    - Normal food: keep NORMAL_FOOD_COUNT on board (immediate try + periodic retries + emergency fill).
    - Golden food: at most GOLDEN_FOOD_MAX; periodic spawn check; expires after duration.
    - Portal pair: spawns as A/B together; expires then respawns elsewhere.
    - Heart: spawns on interval when HP is below max (score-gated).
    - Multiplier: spawns on a fixed interval chance; activates x2 scoring timer.
    - Magnet: spawns on a fixed interval chance; attracts nearby food while active.
    - Shield: spawns on a fixed interval chance; applies a 1-hit shield.
    - Cherry: rare timed bonus that despawns if not eaten.
    """

    def __init__(self, grid: Grid) -> None:
        self.grid = grid

        self.normal_food: List[Cell] = []
        self.golden_foods: List[TimedItem] = []
        self.portals: Optional[PortalPair] = None

        # New items
        self.heart_item: Optional[Cell] = None
        self.multiplier_item: Optional[Cell] = None
        self.magnet_item: Optional[Cell] = None
        self.shield_item: Optional[Cell] = None
        self.cherry: Optional[TimedItem] = None

        # Active powerups (timers)
        self.multiplier_remaining_s: float = 0.0
        self.magnet_remaining_s: float = 0.0

        # Animation state
        self._t: float = 0.0
        self._heart_spawn_accum_s: float = 0.0
        self._mult_spawn_accum_s: float = 0.0
        self._magnet_spawn_accum_s: float = 0.0
        self._shield_spawn_accum_s: float = 0.0
        self._cherry_spawn_accum_s: float = 0.0
        self._portal_spawn_accum_s: float = 0.0

        self._normal_food_retry_accum_s: float = 0.0
        self._normal_food_low_streak_s: float = 0.0
        self._golden_spawn_accum_s: float = 0.0

    def reset(self, occupied: Set[Cell]) -> None:
        """Clear all items and respawn the baseline set."""
        self.normal_food = []
        self.golden_foods = []
        self.portals = None

        self.heart_item = None
        self.multiplier_item = None
        self.magnet_item = None
        self.shield_item = None
        self.cherry = None

        self.multiplier_remaining_s = 0.0
        self.magnet_remaining_s = 0.0

        self._t = 0.0
        self._heart_spawn_accum_s = 0.0
        self._mult_spawn_accum_s = 0.0
        self._magnet_spawn_accum_s = 0.0
        self._shield_spawn_accum_s = 0.0
        self._cherry_spawn_accum_s = 0.0
        self._portal_spawn_accum_s = 0.0

        self._normal_food_retry_accum_s = 0.0
        self._normal_food_low_streak_s = 0.0
        self._golden_spawn_accum_s = 0.0

        # One-shot bootstrap to target count (session start).
        while len(self.normal_food) < C.NORMAL_FOOD_COUNT:
            if not self._try_append_one_normal_food(occupied):
                break

    def update(self, dt_s: float, occupied: Set[Cell], snake_head: Cell, player_hp: int, score: int) -> None:
        """
        Advance timers, spawn chance items, and maintain required counts.

        occupied: cells that cannot host items (snake, enemies, blockers, etc.).
        """
        self._t += dt_s
        self._tick_powerups(dt_s)

        # Maintain normal food count.
        self._ensure_normal_food(dt_s, occupied)

        # Golden food: interval-based spawn check, up to GOLDEN_FOOD_MAX.
        for g in self.golden_foods:
            g.remaining_s -= dt_s
        self.golden_foods = [g for g in self.golden_foods if g.remaining_s > 0]

        self._golden_spawn_accum_s += dt_s
        while self._golden_spawn_accum_s >= C.GOLDEN_FOOD_SPAWN_INTERVAL_S:
            self._golden_spawn_accum_s -= C.GOLDEN_FOOD_SPAWN_INTERVAL_S
            if len(self.golden_foods) < C.GOLDEN_FOOD_MAX and random.random() < C.GOLDEN_FOOD_SPAWN_CHANCE_PER_CHECK:
                self._spawn_golden(occupied | set(self.normal_food))

        # Heart spawn (score-gated + interval checks; never at full HP).
        if self.heart_item is None and score >= C.HEART_MIN_SCORE_FOR_SPAWN and player_hp < C.PLAYER_MAX_HP:
            self._heart_spawn_accum_s += dt_s
            if self._heart_spawn_accum_s >= C.HEART_SPAWN_INTERVAL_S:
                self._heart_spawn_accum_s -= C.HEART_SPAWN_INTERVAL_S
                if random.random() < C.HEART_SPAWN_CHANCE:
                    self._spawn_heart(occupied | self._all_item_cells())

        # Score multiplier spawn.
        if self.multiplier_item is None:
            self._mult_spawn_accum_s += dt_s
            if self._mult_spawn_accum_s >= C.STAR_SPAWN_INTERVAL_S:
                self._mult_spawn_accum_s -= C.STAR_SPAWN_INTERVAL_S
                if random.random() < C.STAR_SPAWN_CHANCE:
                    self._spawn_multiplier(occupied | self._all_item_cells())

        # Magnet spawn.
        if self.magnet_item is None:
            self._magnet_spawn_accum_s += dt_s
            if self._magnet_spawn_accum_s >= C.MAGNET_SPAWN_INTERVAL_S:
                self._magnet_spawn_accum_s -= C.MAGNET_SPAWN_INTERVAL_S
                if random.random() < C.MAGNET_SPAWN_CHANCE_PER_CHECK:
                    self._spawn_magnet(occupied | self._all_item_cells())

        # Shield spawn.
        if self.shield_item is None:
            self._shield_spawn_accum_s += dt_s
            if self._shield_spawn_accum_s >= C.SHIELD_SPAWN_INTERVAL_S:
                self._shield_spawn_accum_s -= C.SHIELD_SPAWN_INTERVAL_S
                if random.random() < C.SHIELD_SPAWN_CHANCE_PER_CHECK:
                    self._spawn_shield(occupied | self._all_item_cells())

        # Cherry spawn + despawn.
        if self.cherry is None:
            self._cherry_spawn_accum_s += dt_s
            if self._cherry_spawn_accum_s >= C.CHERRY_SPAWN_INTERVAL_S:
                self._cherry_spawn_accum_s -= C.CHERRY_SPAWN_INTERVAL_S
                if random.random() < C.CHERRY_SPAWN_CHANCE:
                    self._spawn_cherry(occupied | self._all_item_cells())
        else:
            self.cherry.remaining_s -= dt_s
            if self.cherry.remaining_s <= 0:
                self.cherry = None

        # Portals: timed pair; respawn is throttled by interval + chance.
        if self.portals is None:
            self._portal_spawn_accum_s += dt_s
            if self._portal_spawn_accum_s >= C.PORTAL_RESPAWN_INTERVAL_S:
                self._portal_spawn_accum_s -= C.PORTAL_RESPAWN_INTERVAL_S
                if random.random() < C.PORTAL_RESPAWN_CHANCE:
                    self._ensure_portals(occupied | set(self.normal_food) | self._all_item_cells())
        else:
            self.portals.remaining_s -= dt_s
            if self.portals.remaining_s <= 0:
                self.portals = None

        # Magnet effect: attract food within radius toward the snake head.
        if self.magnet_remaining_s > 0:
            self._apply_magnet(snake_head, occupied)

    def _tick_powerups(self, dt_s: float) -> None:
        """Advance active powerup timers."""
        if self.multiplier_remaining_s > 0:
            self.multiplier_remaining_s = max(0.0, self.multiplier_remaining_s - dt_s)
        if self.magnet_remaining_s > 0:
            self.magnet_remaining_s = max(0.0, self.magnet_remaining_s - dt_s)

    def multiplier_active(self) -> bool:
        """Whether score multiplier is active."""
        return self.multiplier_remaining_s > 0

    def magnet_active(self) -> bool:
        """Whether magnet is active."""
        return self.magnet_remaining_s > 0

    def _all_item_cells(self) -> Set[Cell]:
        """All item-occupied cells excluding normal food (which is tracked separately)."""
        s: Set[Cell] = set()
        for g in self.golden_foods:
            s.add(g.pos)
        if self.heart_item:
            s.add(self.heart_item)
        if self.multiplier_item:
            s.add(self.multiplier_item)
        if self.magnet_item:
            s.add(self.magnet_item)
        if self.shield_item:
            s.add(self.shield_item)
        if self.cherry:
            s.add(self.cherry.pos)
        if self.portals:
            s.add(self.portals.a)
            s.add(self.portals.b)
        return s

    def occupied_cells(self) -> Set[Cell]:
        """All cells currently occupied by items (including portal endpoints)."""
        occ: Set[Cell] = set(self.normal_food)
        for g in self.golden_foods:
            occ.add(g.pos)
        if self.heart_item:
            occ.add(self.heart_item)
        if self.multiplier_item:
            occ.add(self.multiplier_item)
        if self.magnet_item:
            occ.add(self.magnet_item)
        if self.shield_item:
            occ.add(self.shield_item)
        if self.cherry:
            occ.add(self.cherry.pos)
        if self.portals:
            occ.add(self.portals.a)
            occ.add(self.portals.b)
        return occ

    def golden_alpha(self) -> int:
        """Pulsing alpha for golden food (150-255)."""
        lo = C.GOLDEN_FOOD_PULSE_ALPHA_MIN
        hi = C.GOLDEN_FOOD_PULSE_ALPHA_MAX
        amp = (hi - lo) * 0.5
        mid = lo + amp
        v = mid + amp * math.sin(self._t * (math.tau * C.GOLDEN_FOOD_PULSE_SPEED))
        return int(max(lo, min(hi, v)))

    def portal_glow_alpha(self) -> int:
        """Pulsing alpha for portal glow."""
        lo = C.GOLDEN_FOOD_PULSE_ALPHA_MIN
        hi = C.GOLDEN_FOOD_PULSE_ALPHA_MAX
        amp = (hi - lo) * 0.5
        mid = lo + amp
        v = mid + amp * math.sin(self._t * (math.tau * C.PORTAL_GLOW_PULSE_SPEED))
        return int(max(lo, min(hi, v)))

    def _try_append_one_normal_food(self, occupied: Set[Cell]) -> bool:
        """Try to add a single normal food pellet. Returns True if placed."""
        occ = set(occupied) | self.occupied_cells()
        pos = self.grid.random_empty_cell(occ)
        if pos is None:
            return False
        self.normal_food.append(pos)
        return True

    def _ensure_normal_food(self, dt_s: float, occupied: Set[Cell]) -> None:
        """
        Keep NORMAL_FOOD_COUNT pellets when possible:
        - Prune invalid cells.
        - If count stays below 3 for FOOD_FORCE_RESPAWN_THRESHOLD_S, force-fill up to 3.
        - Every FOOD_RESPAWN_TRY_INTERVAL_S while below target, one extra spawn attempt.
        - One immediate spawn attempt per tick when below target (keeps post-eat responsiveness).
        """
        self.normal_food = [p for p in self.normal_food if p not in occupied]

        if len(self.normal_food) < 3:
            self._normal_food_low_streak_s += dt_s
        else:
            self._normal_food_low_streak_s = 0.0

        if self._normal_food_low_streak_s >= C.FOOD_FORCE_RESPAWN_THRESHOLD_S and len(self.normal_food) < 3:
            while len(self.normal_food) < 3:
                if not self._try_append_one_normal_food(occupied):
                    break

        self._normal_food_retry_accum_s += dt_s
        while self._normal_food_retry_accum_s >= C.FOOD_RESPAWN_TRY_INTERVAL_S and len(self.normal_food) < C.NORMAL_FOOD_COUNT:
            self._normal_food_retry_accum_s -= C.FOOD_RESPAWN_TRY_INTERVAL_S
            if not self._try_append_one_normal_food(occupied):
                break

        if len(self.normal_food) < C.NORMAL_FOOD_COUNT:
            self._try_append_one_normal_food(occupied)

        if len(self.normal_food) >= 3:
            self._normal_food_low_streak_s = 0.0

    def _spawn_golden(self, occupied: Set[Cell]) -> None:
        """Spawn one golden food with duration (caller enforces max count)."""
        pos = self.grid.random_empty_cell(occupied | self.occupied_cells())
        if pos is None:
            return
        self.golden_foods.append(TimedItem(kind="golden", pos=pos, remaining_s=C.GOLDEN_FOOD_DURATION_S))

    def _spawn_heart(self, occupied: Set[Cell]) -> None:
        """Spawn a heart pickup."""
        pos = self.grid.random_empty_cell(occupied | self.occupied_cells())
        if pos is None:
            return
        self.heart_item = pos

    def _spawn_multiplier(self, occupied: Set[Cell]) -> None:
        """Spawn a score multiplier pickup."""
        pos = self.grid.random_empty_cell(occupied | self.occupied_cells())
        if pos is None:
            return
        self.multiplier_item = pos

    def _spawn_magnet(self, occupied: Set[Cell]) -> None:
        """Spawn a magnet pickup."""
        pos = self.grid.random_empty_cell(occupied | self.occupied_cells())
        if pos is None:
            return
        self.magnet_item = pos

    def _spawn_shield(self, occupied: Set[Cell]) -> None:
        """Spawn a shield pickup."""
        pos = self.grid.random_empty_cell(occupied | self.occupied_cells())
        if pos is None:
            return
        self.shield_item = pos

    def _spawn_cherry(self, occupied: Set[Cell]) -> None:
        """Spawn a timed bonus cherry."""
        pos = self.grid.random_empty_cell(occupied | self.occupied_cells())
        if pos is None:
            return
        self.cherry = TimedItem(kind="cherry", pos=pos, remaining_s=C.CHERRY_DURATION_S)

    def _ensure_portals(self, occupied: Set[Cell]) -> None:
        """Spawn a portal pair if missing."""
        if self.portals is not None:
            return
        occ = occupied | self.occupied_cells()
        a = self.grid.random_empty_cell(occ)
        if a is None:
            return
        occ.add(a)
        b = self.grid.random_empty_cell(occ)
        if b is None:
            return
        self.portals = PortalPair(a=a, b=b, remaining_s=C.PORTAL_DURATION_S)

    def try_collect_at_head(self, head: Cell) -> Dict[str, int]:
        """
        Attempt to collect an item at the snake head cell.

        Returns an effect dict:
        - {"score": +N, "grow": +K} for foods
        - {"heal": +1} for heart
        - {"mult": 1} for multiplier activation
        - {"magnet": 1} for magnet activation
        - {"shield": 1} for shield activation
        - {"cherry": 1} for bonus cherry
        """
        effects: Dict[str, int] = {}

        # Normal food: can be multiple; remove and respawn handled by update().
        if head in self.normal_food:
            self.normal_food = [p for p in self.normal_food if p != head]
            effects["score"] = effects.get("score", 0) + C.SCORE_FOOD_NORMAL
            effects["grow"] = effects.get("grow", 0) + C.GROW_FOOD_NORMAL

        # Golden food:
        if any(head == g.pos for g in self.golden_foods):
            self.golden_foods = [g for g in self.golden_foods if g.pos != head]
            effects["score"] = effects.get("score", 0) + C.SCORE_FOOD_GOLDEN
            effects["grow"] = effects.get("grow", 0) + C.GROW_FOOD_GOLDEN
            effects["golden"] = 1

        # Heart:
        if self.heart_item and head == self.heart_item:
            self.heart_item = None
            effects["heal"] = 1

        # Multiplier:
        if self.multiplier_item and head == self.multiplier_item:
            self.multiplier_item = None
            self.multiplier_remaining_s = C.SCORE_MULTIPLIER_DURATION_S
            effects["mult"] = 1

        # Magnet:
        if self.magnet_item and head == self.magnet_item:
            self.magnet_item = None
            self.magnet_remaining_s = C.MAGNET_DURATION_S
            effects["magnet"] = 1

        # Shield:
        if self.shield_item and head == self.shield_item:
            self.shield_item = None
            effects["shield"] = 1

        # Cherry:
        if self.cherry and head == self.cherry.pos:
            self.cherry = None
            effects["cherry"] = 1

        return effects

    def try_portal_teleport(self, head: Cell) -> Optional[Tuple[Cell, Cell]]:
        """
        If head enters portal A or B, return (exit_cell, entered_cell).
        Caller is responsible for moving the snake head accordingly while
        keeping direction unchanged.
        """
        if not self.portals:
            return None
        if head == self.portals.a:
            return (self.portals.b, self.portals.a)
        if head == self.portals.b:
            return (self.portals.a, self.portals.b)
        return None

    def heart_pulse_scale(self) -> float:
        """Gentle pulse scale for heart item (1.0 -> 1.15 -> 1.0 every 0.8s)."""
        t = (self._t % C.HEART_PULSE_PERIOD_S) / C.HEART_PULSE_PERIOD_S
        # Triangle wave 0..1..0
        tri = 1.0 - abs(2.0 * t - 1.0)
        return C.HEART_PULSE_SCALE_MIN + (C.HEART_PULSE_SCALE_MAX - C.HEART_PULSE_SCALE_MIN) * tri

    def _apply_magnet(self, snake_head: Cell, occupied: Set[Cell]) -> None:
        """
        Attract nearby food items by moving them 1 step toward the snake head.
        Only affects normal and golden food (not portals or powerups).
        """
        occ_now = set(occupied) | self._all_item_cells()

        new_food: List[Cell] = []
        for p in self.normal_food:
            if manhattan(p, snake_head) <= C.MAGNET_RADIUS_CELLS:
                step = self._step_toward(p, snake_head, occ_now)
                if step is not None:
                    p = step
            new_food.append(p)
        self.normal_food = new_food

        for g in self.golden_foods:
            occ_now = set(occupied) | self._all_item_cells()
            if manhattan(g.pos, snake_head) <= C.MAGNET_RADIUS_CELLS:
                step = self._step_toward(g.pos, snake_head, occ_now)
                if step is not None:
                    g.pos = step

    def _step_toward(self, start: Cell, goal: Cell, occupied: Set[Cell]) -> Optional[Cell]:
        """
        Choose a 1-step move that reduces Manhattan distance to goal, if possible.
        """
        sx, sy = start
        gx, gy = goal

        candidates: List[Cell] = []
        if gx > sx:
            candidates.append((sx + 1, sy))
        elif gx < sx:
            candidates.append((sx - 1, sy))
        if gy > sy:
            candidates.append((sx, sy + 1))
        elif gy < sy:
            candidates.append((sx, sy - 1))

        for c in candidates:
            if self.grid.in_bounds(c) and c not in occupied:
                return c
        return None

