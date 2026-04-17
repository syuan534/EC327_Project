"""
Snake+ | EC327 — version0: pygame window + loading banner only.
"""

from __future__ import annotations

import sys

import pygame

import constants as C


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Snake+ | EC327")
    screen = pygame.display.set_mode((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    font = pygame.font.Font(None, 36)
    msg = font.render("Snake+ | EC327 | Loading...", True, C.COLOR_TEXT)
    running = True

    while running:
        clock.tick(60)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_q:
                running = False

        screen.fill(C.COLOR_BG)
        cx = C.WINDOW_WIDTH // 2 - msg.get_width() // 2
        cy = C.WINDOW_HEIGHT // 2 - msg.get_height() // 2
        screen.blit(msg, (cx, cy))
        pygame.display.flip()

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
