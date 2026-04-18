from __future__ import annotations


class Renderer:
    """Pygame drawing facade; logic added in later versions."""

    def __init__(self) -> None:
        pass

    #a draw function for 
    def draw(
        self,
        screen: pygame.Surface,
        state: str,
        score: int,
        high_score: int,
        hp: int,
        snake: Snake,
    )-> None:
        screen.fill(C.COLOR_BG)
        self._draw_sidebar(screen, score, high_score, snake.length(), hp)

    #sidebar to display player/snake status
    def _draw_sidebar(self, screen: pygame.Surface, score: int, high_score: int, length: int, hp: int) -> None:

    def _draw_arena(self, surface: object) -> None:
        pass

    def _draw_snake(self, surface: object, snake: object) -> None:
        pass

    def _draw_hud(self, surface: object, score: int, high_score: int, length: int) -> None:
        pass

    def _draw_menu(self, surface: object) -> None:
        pass
