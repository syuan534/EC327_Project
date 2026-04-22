from __future__ import annotations

import json
import os
import sys
from typing import Set

import pygame

import constants as C
from enemies import EnemyManager
from items import ItemManager
from renderer import Renderer
from snake import DIR_DOWN, DIR_LEFT, DIR_RIGHT, DIR_UP, Snake
from world import Grid

def load_high_score() -> int:
    path = os.path.join(os.path.dirname(__file__), C.HIGHSCORE_FILE)
    try:
        with open(path, "r", encoding="utf-8") as f:
            return max(0, int(json.load(f).get(C.HIGHSCORE_KEY, 0)))
    except (OSError, ValueError, json.JSONDecodeError, TypeError):
        return 0


def save_high_score(v: int) -> None:
    path = os.path.join(os.path.dirname(__file__), C.HIGHSCORE_FILE)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({C.HIGHSCORE_KEY: int(v)}, f)
    except OSError:
        pass


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Snake+ v2b")
    screen = pygame.display.set_mode((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    grid = Grid(C.GRID_SIZE)
    snake = Snake(grid)
    items = ItemManager(grid)
    enemies = EnemyManager(grid)
    renderer = Renderer()

    high_score = load_high_score()
    state = C.STATE_MENU
    score = 0

    def reset() -> None:
        nonlocal score
        score = 0
        snake.reset()
        enemies.reset()
        occ: Set[tuple[int, int]] = set(snake.occupies())
        items.reset(occ)
        renderer.particles = []

    reset()
    running = True

    while running:
        dt = clock.tick(C.BASE_FPS) / 1000.0
        renderer.update_fx(dt)
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_q:
                    running = False
                if state == C.STATE_MENU and ev.key == pygame.K_RETURN:
                    reset()
                    state = C.STATE_PLAYING
                elif state == C.STATE_PLAYING:
                    if ev.key == pygame.K_UP:
                        snake.set_direction(DIR_UP)
                    elif ev.key == pygame.K_DOWN:
                        snake.set_direction(DIR_DOWN)
                    elif ev.key == pygame.K_LEFT:
                        snake.set_direction(DIR_LEFT)
                    elif ev.key == pygame.K_RIGHT:
                        snake.set_direction(DIR_RIGHT)
                elif state == C.STATE_GAME_OVER and ev.key == pygame.K_r:
                    reset()
                    state = C.STATE_PLAYING

        if state == C.STATE_MENU:
            renderer.draw_menu(screen, high_score)
        elif state == C.STATE_PLAYING:
            snake.update_timers(dt)
            occ_snake = set(snake.occupies())
            occ_items = items.occupied_cells()
            occ_en = enemies.occupied_cells()
            spawn_occ = occ_snake | occ_items | occ_en
            items.update(dt, spawn_occ, snake.head, snake.hp, score)
            enemies.update(dt, score, spawn_occ)

            attempted = snake.next_head()
            if snake.would_self_bite():
                snake.hp = 0
                state = C.STATE_GAME_OVER
                if score > high_score:
                    high_score = score
                    save_high_score(high_score)
            elif snake.would_hit_wall() or attempted in enemies.blocker_cells():
                snake.take_hit()
                if snake.hp <= 0:
                    state = C.STATE_GAME_OVER
                    if score > high_score:
                        high_score = score
                        save_high_score(high_score)
            else:
                snake.move_to(attempted)
                fx = items.try_collect_at_head(snake.head)
                if fx:
                    score += int(fx.get("score", 0))
                    snake.grow(int(fx.get("grow", 0)))
                    if fx.get("golden"):
                        renderer.spawn_eat_particles(snake.head, C.COLOR_FOOD_GOLDEN)
                    else:
                        renderer.spawn_eat_particles(snake.head, C.COLOR_FOOD)

            renderer.draw(screen, state, score, high_score, snake.hp, snake, items, enemies, game_over=False)
        else:
            renderer.draw(screen, state, score, high_score, snake.hp, snake, items, enemies, game_over=True)

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
