"""version1_patrick_a — core snake movement and rendering."""

from __future__ import annotations

import sys

import pygame

import constants as C
from renderer import Renderer
from snake import DIR_DOWN, DIR_LEFT, DIR_RIGHT, DIR_UP, Snake
from world import Grid


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Snake+ v1a")
    screen = pygame.display.set_mode((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    grid = Grid(C.GRID_SIZE)
    snake = Snake(grid)
    renderer = Renderer()

    state = C.STATE_MENU

    def reset() -> None:
        snake.reset()

    reset()
    running = True

    while running:
        clock.tick(C.BASE_FPS)
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
            renderer.draw_menu(screen)
        elif state == C.STATE_PLAYING:
            if snake.would_hit_wall() or snake.would_self_bite():
                state = C.STATE_GAME_OVER
            else:
                snake.move_to(snake.next_head())
            renderer.draw(screen, state, snake, game_over=False)
        else:
            renderer.draw(screen, state, snake, game_over=True)

        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
