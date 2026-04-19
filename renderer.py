from __future__ import annotations

import pygame

import constants as C
from snake import Snake


class Renderer:
    def __init__(self) -> None:
        pygame.font.init()
        self._title = pygame.font.Font(None, 52)
        self._hint = pygame.font.Font(None, 26)
        self._score = pygame.font.Font(None, 34)

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
        game_over: bool,
    ) -> None:
        screen.fill(C.COLOR_BG)
        self._draw_arena(screen, snake)
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

    def _draw_arena(self, screen: pygame.Surface, snake: Snake, items: ItemManager, enemies: EnemyManager) -> None:
        _ = enemies
        surf = pygame.Surface((C.ARENA_WIDTH, C.ARENA_HEIGHT))
        surf.fill((10, 10, 22))
        for x in range(C.GRID_SIZE + 1):
            pygame.draw.line(surf, C.COLOR_GRID, (x * C.CELL_SIZE, 0), (x * C.CELL_SIZE, C.ARENA_HEIGHT), 1)
        for y in range(C.GRID_SIZE + 1):
            pygame.draw.line(surf, C.COLOR_GRID, (0, y * C.CELL_SIZE), (C.ARENA_WIDTH, y * C.CELL_SIZE), 1)
        pygame.draw.rect(surf, C.COLOR_BORDER, (0, 0, C.ARENA_WIDTH, C.ARENA_HEIGHT), 2)

        inset = 1
        for i, cell in enumerate(snake.body):
            cx, cy = cell
            r = pygame.Rect(cx * C.CELL_SIZE + inset, cy * C.CELL_SIZE + inset, C.CELL_SIZE - 2 * inset, C.CELL_SIZE - 2 * inset)
            pygame.draw.rect(surf, self._snake_color(snake, i), r, border_radius=3)

        for fc in items.normal_food:
            px = fc[0] * C.CELL_SIZE + C.CELL_SIZE // 2
            py = fc[1] * C.CELL_SIZE + C.CELL_SIZE // 2
            pygame.draw.circle(surf, C.COLOR_FOOD, (px, py), C.FOOD_RADIUS)

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