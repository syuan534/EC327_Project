"""Arena + snake + food circles + sidebar labels."""

from __future__ import annotations

import pygame

import constants as C
from enemies import EnemyManager
from items import ItemManager
from snake import Snake


class Renderer:
    def __init__(self) -> None:
        pygame.font.init()
        self._title = pygame.font.Font(None, 48)
        self._label = pygame.font.Font(None, 22)
        self._score = pygame.font.Font(None, 36)

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
        snake: Snake,
        items: ItemManager,
        enemies: EnemyManager,
        game_over: bool,
    ) -> None:
        screen.fill(C.COLOR_BG)
        self._draw_arena_layer(screen, snake, items, enemies)
        self._draw_sidebar(screen, score, high_score, snake.length())
        if game_over or state == C.STATE_GAME_OVER:
            ov = pygame.Surface((C.WINDOW_WIDTH, C.WINDOW_HEIGHT), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 130))
            screen.blit(ov, (0, 0))
            go = self._title.render("GAME OVER", True, (255, 80, 80))
            r = self._label.render("Press R to restart, Q to quit", True, C.COLOR_TEXT)
            cx, cy = C.WINDOW_WIDTH // 2, C.WINDOW_HEIGHT // 2
            screen.blit(go, (cx - go.get_width() // 2, cy - 20))
            screen.blit(r, (cx - r.get_width() // 2, cy + 28))

    def _cell_center(self, cell: tuple[int, int], pad: int) -> tuple[int, int]:
        cx, cy = cell
        ax, ay = pad, pad
        x = ax + cx * C.CELL_SIZE + C.CELL_SIZE // 2
        y = ay + cy * C.CELL_SIZE + C.CELL_SIZE // 2
        return (x, y)

    def _draw_arena_layer(self, screen: pygame.Surface, snake: Snake, items: ItemManager, enemies: EnemyManager) -> None:
        _ = enemies
        pad = 2
        ax, ay = pad, pad
        aw, ah = C.ARENA_WIDTH - 2 * pad, C.ARENA_HEIGHT - 2 * pad
        surf = pygame.Surface((C.ARENA_WIDTH, C.ARENA_HEIGHT))
        surf.fill((10, 10, 22))
        for x in range(C.GRID_SIZE + 1):
            px = x * C.CELL_SIZE
            pygame.draw.line(surf, C.COLOR_GRID, (px, 0), (px, C.ARENA_HEIGHT), 1)
        for y in range(C.GRID_SIZE + 1):
            py = y * C.CELL_SIZE
            pygame.draw.line(surf, C.COLOR_GRID, (0, py), (C.ARENA_WIDTH, py), 1)
        pygame.draw.rect(surf, C.COLOR_BORDER, (0, 0, C.ARENA_WIDTH, C.ARENA_HEIGHT), 2)

        inset = 1
        for i, cell in enumerate(snake.body):
            cx, cy = cell
            r = pygame.Rect(cx * C.CELL_SIZE + inset, cy * C.CELL_SIZE + inset, C.CELL_SIZE - 2 * inset, C.CELL_SIZE - 2 * inset)
            col = C.COLOR_SNAKE_HEAD if i == 0 else C.COLOR_SNAKE_BODY
            pygame.draw.rect(surf, col, r, border_radius=3)

        for fc in items.normal_food:
            pygame.draw.circle(surf, C.COLOR_FOOD, self._cell_center(fc, 0), C.FOOD_RADIUS)

        screen.blit(surf, (ax, ay))

    def _draw_sidebar(self, screen: pygame.Surface, score: int, high_score: int, length: int) -> None:
        panel = pygame.Rect(C.ARENA_WIDTH, 0, C.SIDEBAR_WIDTH, C.WINDOW_HEIGHT)
        pygame.draw.rect(screen, C.COLOR_SIDEBAR_BG, panel)
        x = C.ARENA_WIDTH + C.HUD_PADDING
        y = C.HUD_PADDING

        def line(text: str, big: bool = False) -> None:
            nonlocal y
            font = self._score if big else self._label
            surf = font.render(text, True, C.COLOR_TEXT)
            screen.blit(surf, (x, y))
            y += surf.get_height() + C.HUD_LINE_GAP

        line("Score", False)
        line(str(score), True)
        line("High Score", False)
        line(str(high_score), True)
        line("Snake Length", False)
        line(str(length), True)
