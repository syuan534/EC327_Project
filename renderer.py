"""Draw arena, snake, menu / game over (no sidebar, no score)."""

from __future__ import annotations

import pygame

import constants as C
from snake import Snake


class Renderer:
    def __init__(self) -> None:
        pygame.font.init()
        self._title = pygame.font.Font(None, 52)
        self._hint = pygame.font.Font(None, 26)

    def draw_menu(self, screen: pygame.Surface) -> None:
        screen.fill(C.COLOR_BG)
        t = self._title.render("Snake", True, (240, 240, 250))
        h = self._hint.render("Press ENTER to start", True, (180, 180, 200))
        cx, cy = C.WINDOW_WIDTH // 2, C.WINDOW_HEIGHT // 2
        screen.blit(t, (cx - t.get_width() // 2, cy - 50))
        screen.blit(h, (cx - h.get_width() // 2, cy + 10))

    def draw(self, screen: pygame.Surface, state: str, snake: Snake, game_over: bool) -> None:
        screen.fill(C.COLOR_BG)
        self._draw_arena(screen, snake)
        if game_over or state == C.STATE_GAME_OVER:
            ov = pygame.Surface((C.WINDOW_WIDTH, C.WINDOW_HEIGHT), pygame.SRCALPHA)
            ov.fill((0, 0, 0, 140))
            screen.blit(ov, (0, 0))
            go = self._title.render("GAME OVER", True, (255, 90, 90))
            r = self._hint.render("Press R to restart, Q to quit", True, (220, 220, 230))
            cx, cy = C.WINDOW_WIDTH // 2, C.WINDOW_HEIGHT // 2
            screen.blit(go, (cx - go.get_width() // 2, cy - 20))
            screen.blit(r, (cx - r.get_width() // 2, cy + 30))

    def _draw_arena(self, screen: pygame.Surface, snake: Snake) -> None:
        pad = 2
        ax = pad
        ay = pad
        aw = C.ARENA_WIDTH - 2 * pad
        ah = C.ARENA_HEIGHT - 2 * pad
        pygame.draw.rect(screen, (10, 10, 22), (ax, ay, aw, ah))
        for x in range(C.GRID_SIZE + 1):
            px = ax + x * C.CELL_SIZE
            pygame.draw.line(screen, C.COLOR_GRID, (px, ay), (px, ay + ah), 1)
        for y in range(C.GRID_SIZE + 1):
            py = ay + y * C.CELL_SIZE
            pygame.draw.line(screen, C.COLOR_GRID, (ax, py), (ax + aw, py), 1)
        pygame.draw.rect(screen, C.COLOR_BORDER, (ax, ay, aw, ah), 2)

        inset = 1
        for i, cell in enumerate(snake.body):
            cx, cy = cell
            r = pygame.Rect(ax + cx * C.CELL_SIZE + inset, ay + cy * C.CELL_SIZE + inset, C.CELL_SIZE - 2 * inset, C.CELL_SIZE - 2 * inset)
            col = C.COLOR_SNAKE_HEAD if i == 0 else C.COLOR_SNAKE_BODY
            pygame.draw.rect(screen, col, r, border_radius=3)
