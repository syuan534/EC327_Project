from __future__ import annotations
import math
import random
from dataclasses import dataclass
from typing import List, Tuple

import pygame

import constants as C
from enemies import EnemyManager
from items import ItemManager
from snake import Snake
from world import Cell


@dataclass
class Particle:
    pos: pygame.math.Vector2
    vel: pygame.math.Vector2
    color: Tuple[int, int, int]
    age_s: float
    life_s: float


class Renderer:
    def __init__(self) -> None:
        pygame.font.init()
        self._title = pygame.font.Font(None, 48)
        self._label = pygame.font.Font(None, 22)
        self._score = pygame.font.Font(None, 34)
        self.particles: List[Particle] = []

    def spawn_eat_particles(self, cell: Cell, color: Tuple[int, int, int]) -> None:
        cx = cell[0] * C.CELL_SIZE + C.CELL_SIZE // 2
        cy = cell[1] * C.CELL_SIZE + C.CELL_SIZE // 2
        origin = pygame.math.Vector2(float(cx), float(cy))
        for _ in range(C.PARTICLES_ON_EAT):
            ang = random.random() * math.tau
            spd = C.PARTICLE_SPEED_PX_PER_S * (0.5 + random.random())
            vel = pygame.math.Vector2(math.cos(ang) * spd, math.sin(ang) * spd)
            self.particles.append(Particle(pos=origin.copy(), vel=vel, color=color, age_s=0.0, life_s=C.PARTICLE_LIFETIME_S))

    def update_fx(self, dt_s: float) -> None:
        keep: List[Particle] = []
        for p in self.particles:
            p.age_s += dt_s
            if p.age_s >= p.life_s:
                continue
            p.pos += p.vel * dt_s
            keep.append(p)
        self.particles = keep

    def draw_menu(self, screen: pygame.Surface, high_score: int) -> None:
        screen.fill(C.COLOR_BG)
        t = self._title.render("Snake", True, C.COLOR_TEXT)
        h = self._label.render("Press ENTER to start", True, C.COLOR_TEXT_MUTED)
        hs = self._label.render(f"High score: {high_score}", True, C.COLOR_TEXT)
        cx, cy = C.WINDOW_WIDTH // 2, C.WINDOW_HEIGHT // 2
        screen.blit(t, (cx - t.get_width() // 2, cy - 60))
        screen.blit(h, (cx - h.get_width() // 2, cy))
        screen.blit(hs, (cx - hs.get_width() // 2, cy + 36))

    def draw(
        self,
        screen: pygame.Surface,
        state: str,
        score: int,
        high_score: int,
        hp: int,
        snake: Snake,
        items: ItemManager,
        enemies: EnemyManager,
        game_over: bool,
    ) -> None:
        screen.fill(C.COLOR_BG)
        self._draw_arena(screen, snake, items, enemies)
        self._draw_sidebar(screen, score, high_score, snake.length(), hp)
        if game_over or state == C.STATE_GAME_OVER:
            ov = pygame.Surface((C.WINDOW_WIDTH, C.WINDOW_HEIGHT), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 130))
            screen.blit(ov, (0, 0))
            go = self._title.render("GAME OVER", True, (255, 80, 80))
            r = self._label.render("Press R to restart, Q to quit", True, C.COLOR_TEXT)
            cx, cy = C.WINDOW_WIDTH // 2, C.WINDOW_HEIGHT // 2
            screen.blit(go, (cx - go.get_width() // 2, cy - 20))
            screen.blit(r, (cx - r.get_width() // 2, cy + 28))

    def _snake_color(self, snake: Snake, segment_index: int) -> tuple[int, int, int]:
        fc = snake.flash_color()
        if fc and snake.is_invincible():
            pulse = (pygame.time.get_ticks() // 120) % 2
            return fc if pulse == 0 else (C.COLOR_SNAKE_BODY if segment_index else C.COLOR_SNAKE_HEAD)
        if fc:
            return fc
        return C.COLOR_SNAKE_HEAD if segment_index == 0 else C.COLOR_SNAKE_BODY

    def _draw_arena(self, screen: pygame.Surface, snake: Snake, items: ItemManager, enemies: EnemyManager) -> None:
        surf = pygame.Surface((C.ARENA_WIDTH, C.ARENA_HEIGHT))
        surf.fill((10, 10, 22))
        for x in range(C.GRID_SIZE + 1):
            pygame.draw.line(surf, C.COLOR_GRID, (x * C.CELL_SIZE, 0), (x * C.CELL_SIZE, C.ARENA_HEIGHT), 1)
        for y in range(C.GRID_SIZE + 1):
            pygame.draw.line(surf, C.COLOR_GRID, (0, y * C.CELL_SIZE), (C.ARENA_WIDTH, y * C.CELL_SIZE), 1)
        pygame.draw.rect(surf, C.COLOR_BORDER, (0, 0, C.ARENA_WIDTH, C.ARENA_HEIGHT), 2)

        for b in enemies.blockers:
            bx, by = b.pos
            r = pygame.Rect(bx * C.CELL_SIZE + 1, by * C.CELL_SIZE + 1, C.CELL_SIZE - 2, C.CELL_SIZE - 2)
            pygame.draw.rect(surf, C.COLOR_ENEMY_BLOCKER, r)

        inset = 1
        for i, cell in enumerate(snake.body):
            cx, cy = cell
            r = pygame.Rect(cx * C.CELL_SIZE + inset, cy * C.CELL_SIZE + inset, C.CELL_SIZE - 2 * inset, C.CELL_SIZE - 2 * inset)
            pygame.draw.rect(surf, self._snake_color(snake, i), r, border_radius=3)

        for fc in items.normal_food:
            px = fc[0] * C.CELL_SIZE + C.CELL_SIZE // 2
            py = fc[1] * C.CELL_SIZE + C.CELL_SIZE // 2
            pygame.draw.circle(surf, C.COLOR_FOOD, (px, py), C.FOOD_RADIUS)

        alpha = items.golden_alpha()
        for g in items.golden_foods:
            px = g.pos[0] * C.CELL_SIZE + C.CELL_SIZE // 2
            py = g.pos[1] * C.CELL_SIZE + C.CELL_SIZE // 2
            gs = pygame.Surface((C.GOLDEN_FOOD_RADIUS * 2 + 4, C.GOLDEN_FOOD_RADIUS * 2 + 4), pygame.SRCALPHA)
            pygame.draw.circle(gs, (*C.COLOR_FOOD_GOLDEN, alpha), (gs.get_width() // 2, gs.get_height() // 2), C.GOLDEN_FOOD_RADIUS)
            surf.blit(gs, (px - gs.get_width() // 2, py - gs.get_height() // 2))

        for p in self.particles:
            t = p.age_s / max(0.001, p.life_s)
            a = int(255 * (1.0 - t))
            pr = pygame.Surface((C.PARTICLE_RADIUS_PX * 2 + 2, C.PARTICLE_RADIUS_PX * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(pr, (*p.color, a), (C.PARTICLE_RADIUS_PX + 1, C.PARTICLE_RADIUS_PX + 1), C.PARTICLE_RADIUS_PX)
            surf.blit(pr, (p.pos.x - C.PARTICLE_RADIUS_PX - 1, p.pos.y - C.PARTICLE_RADIUS_PX - 1))

        screen.blit(surf, (2, 2))

    def _draw_sidebar(self, screen: pygame.Surface, score: int, high_score: int, length: int, hp: int) -> None:
        panel = pygame.Rect(C.ARENA_WIDTH, 0, C.SIDEBAR_WIDTH, C.WINDOW_HEIGHT)
        pygame.draw.rect(screen, C.COLOR_SIDEBAR_BG, panel)
        x = C.ARENA_WIDTH + C.HUD_PADDING
        y = C.HUD_PADDING

        def line(text: str, big: bool = False, color: tuple[int, int, int] = C.COLOR_TEXT) -> None:
            nonlocal y
            font = self._score if big else self._label
            surf = font.render(text, True, color)
            screen.blit(surf, (x, y))
            y += surf.get_height() + C.HUD_LINE_GAP

        line("Score", False)
        line(str(score), True)
        line("High Score", False)
        line(str(high_score), True)
        line("Snake Length", False)
        line(str(length), True)
        line("HP", False)
        for i in range(C.PLAYER_MAX_HP):
            col = C.COLOR_HEART_FULL if i < hp else C.COLOR_HEART_EMPTY
            pygame.draw.circle(screen, col, (x + 10 + i * 22, y + 10), 9)
        y += 26