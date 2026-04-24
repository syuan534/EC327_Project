"""
main.py

Snake+ entry point:
- Pygame init and game loop
- Game state machine (MENU, PLAYING, PAUSED, GAME_OVER)
- Event handling (movement, pause, restart, quit)
- Difficulty scaling: +1 FPS every 30s up to max 20 FPS
- High score load/save (highscore.json)
"""

from __future__ import annotations

import json
import os
from typing import Set

import pygame

import constants as C
from enemies import EnemyManager
from items import ItemManager
from renderer import Renderer
from snake import DIR_DOWN, DIR_LEFT, DIR_RIGHT, DIR_UP, Snake
from world import Grid, occupied_union


def load_high_score() -> int:
    """Load high score from highscore.json; return 0 if missing/invalid."""
    path = os.path.join(os.path.dirname(__file__), C.HIGHSCORE_FILE)
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        v = int(data.get(C.HIGHSCORE_KEY, 0))
        return max(0, v)
    except (OSError, ValueError, json.JSONDecodeError, TypeError):
        return 0


def save_high_score(value: int) -> None:
    """Save high score to highscore.json."""
    path = os.path.join(os.path.dirname(__file__), C.HIGHSCORE_FILE)
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump({C.HIGHSCORE_KEY: int(value)}, f)
    except OSError:
        pass


def main() -> None:
    """Boot the game and run the main loop."""
    pygame.init()
    pygame.display.set_caption("Snake+")
    screen = pygame.display.set_mode((C.WINDOW_WIDTH, C.WINDOW_HEIGHT))
    clock = pygame.time.Clock()

    grid = Grid()
    snake = Snake(grid)
    items = ItemManager(grid)
    enemies = EnemyManager(grid)
    renderer = Renderer()

    high_score = load_high_score()

    # Game session state
    state = C.STATE_MENU
    score = 0
    elapsed_play_s = 0.0
    difficulty_level = 0
    target_fps = C.BASE_FPS
    survival_bonus_accum_s = 0.0
    score_flash_s = 0.0

    def reset_session() -> None:
        nonlocal score, elapsed_play_s, difficulty_level, target_fps, survival_bonus_accum_s, score_flash_s
        score = 0
        elapsed_play_s = 0.0
        difficulty_level = 0
        target_fps = C.BASE_FPS
        survival_bonus_accum_s = 0.0
        score_flash_s = 0.0
        snake.reset()
        enemies.reset()
        occ = occupied_union(snake.occupies(), enemies.occupied_cells())
        items.reset(occ)
        renderer.particles = []
        renderer.shake_remaining_s = 0.0

    running = True
    reset_session()

    while running:
        dt_s = clock.tick(target_fps) / 1000.0
        renderer.update_fx(dt_s)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    running = False

                if state == C.STATE_MENU:
                    if event.key == pygame.K_RETURN:
                        reset_session()
                        state = C.STATE_PLAYING

                elif state == C.STATE_PLAYING:
                    if event.key == pygame.K_p:
                        state = C.STATE_PAUSED
                    elif event.key == pygame.K_UP:
                        snake.set_direction(DIR_UP)
                    elif event.key == pygame.K_DOWN:
                        snake.set_direction(DIR_DOWN)
                    elif event.key == pygame.K_LEFT:
                        snake.set_direction(DIR_LEFT)
                    elif event.key == pygame.K_RIGHT:
                        snake.set_direction(DIR_RIGHT)

                elif state == C.STATE_PAUSED:
                    if event.key == pygame.K_p:
                        state = C.STATE_PLAYING

                elif state == C.STATE_GAME_OVER:
                    if event.key == pygame.K_r:
                        reset_session()
                        state = C.STATE_PLAYING
                    elif event.key == pygame.K_q:
                        running = False

        if state == C.STATE_MENU:
            renderer.draw_menu(screen, high_score)
            pygame.display.flip()
            continue

        if state == C.STATE_PAUSED:
            chaser_phase, chaser_time, chaser_ind = enemies.chaser_hud()
            renderer.draw(
                screen=screen,
                state=state,
                score=score,
                high_score=high_score,
                difficulty_level=difficulty_level,
                hp=snake.hp,
                score_flash_s=score_flash_s,
                chaser_hud_phase=chaser_phase,
                chaser_hud_time_s=chaser_time,
                chaser_hud_indicator=chaser_ind,
                snake=snake,
                items=items,
                enemies=enemies,
                paused_overlay=True,
                game_over_overlay=False,
            )
            pygame.display.flip()
            continue

        if state == C.STATE_PLAYING:
            elapsed_play_s += dt_s
            new_level = int(elapsed_play_s // C.DIFFICULTY_INCREASE_INTERVAL_S)
            if new_level != difficulty_level:
                difficulty_level = new_level
            target_fps = min(C.MAX_FPS, C.BASE_FPS + difficulty_level * C.FPS_INCREASE_PER_LEVEL)

            # Update snake timers (invincibility + flashes)
            snake.update_timers(dt_s)
            if score_flash_s > 0:
                score_flash_s = max(0.0, score_flash_s - dt_s)

            # Survival bonus
            survival_bonus_accum_s += dt_s
            while survival_bonus_accum_s >= C.SURVIVAL_BONUS_INTERVAL_S:
                survival_bonus_accum_s -= C.SURVIVAL_BONUS_INTERVAL_S
                score += C.SCORE_SURVIVAL_BONUS
                score_flash_s = C.SCORE_FLASH_DURATION_S

            # Compute occupied sets for spawning and pathing
            occ_enemies = enemies.occupied_cells()
            occ_items = items.occupied_cells()
            occ_snake = set(snake.occupies())

            occupied_for_spawn: Set[tuple[int, int]] = set()
            occupied_for_spawn |= occ_snake
            occupied_for_spawn |= occ_enemies
            occupied_for_spawn |= occ_items

            # Update items (spawns / timers)
            items.update(dt_s, occupied_for_spawn, snake.head, snake.hp, score)

            # Snake movement and collisions (walls ON, no wrap)
            attempted = snake.next_head_unwrapped()

            def apply_damage() -> None:
                nonlocal state
                result = snake.take_hit()
                _ = result
                if snake.hp <= 0:
                    renderer.trigger_shake()
                    state = C.STATE_GAME_OVER

            moved = False
            if snake.would_hit_wall():
                # Border hit: lose 1 HP, do not move.
                apply_damage()
            elif attempted in enemies.blocker_cells():
                # Obstacle hit: lose 1 HP, do not move.
                apply_damage()
            elif snake.would_self_bite():
                state = C.STATE_GAME_OVER
                renderer.trigger_shake()
            else:
                snake.move_to(attempted)
                moved = True

            if state == C.STATE_PLAYING and moved:
                # Portal teleport (after move: head sits on portal cell)
                tp = items.try_portal_teleport(snake.head)
                if tp:
                    exit_cell, _entered = tp
                    snake.teleport_head(exit_cell)

                # Collect items at head, apply effects
                effects = items.try_collect_at_head(snake.head)
                if effects and state == C.STATE_PLAYING:
                    gained = 0
                    grow = effects.get("grow", 0)

                    if "score" in effects:
                        base = int(effects["score"])
                        if items.multiplier_active():
                            base *= C.SCORE_MULTIPLIER_VALUE
                        gained += base
                        if effects.get("golden"):
                            renderer.spawn_eat_particles(snake.head, C.COLOR_FOOD_GOLDEN)
                        else:
                            renderer.spawn_eat_particles(snake.head, C.COLOR_FOOD_NORMAL)
                    if "cherry" in effects:
                        gained += C.SCORE_BONUS_CHERRY
                        renderer.spawn_eat_particles(snake.head, C.COLOR_ITEM_CHERRY)
                    if "heal" in effects:
                        snake.heal(int(effects["heal"]))
                    if "shield" in effects:
                        snake.apply_shield()

                    if grow:
                        snake.grow(int(grow))

                    if gained:
                        score += gained
                        score_flash_s = C.SCORE_FLASH_DURATION_S

            # Enemy update after snake step (chaser moves toward latest head)
            blocked_for_chaser: Set[tuple[int, int]] = set(snake.occupies())
            blocked_for_chaser |= enemies.blocker_cells()
            enemies.update(
                dt_s=dt_s,
                score=score,
                snake_head=snake.head,
                occupied_for_spawn=occupied_for_spawn,
                blocked_for_chaser=blocked_for_chaser,
            )

            # Chaser overlap: damage (unless invincible), then chaser retreats in-place during hunt.
            if state == C.STATE_PLAYING and enemies.player_touched_chaser(snake.head):
                if not snake.is_invincible():
                    apply_damage()
                enemies.retreat_chaser_from_player(snake.head, occupied_for_spawn)

        if state == C.STATE_GAME_OVER:
            if score > high_score:
                high_score = score
            save_high_score(high_score)

            chaser_phase, chaser_time, chaser_ind = enemies.chaser_hud()
            renderer.draw(
                screen=screen,
                state=state,
                score=score,
                high_score=high_score,
                difficulty_level=difficulty_level,
                hp=snake.hp,
                score_flash_s=score_flash_s,
                chaser_hud_phase=chaser_phase,
                chaser_hud_time_s=chaser_time,
                chaser_hud_indicator=chaser_ind,
                snake=snake,
                items=items,
                enemies=enemies,
                paused_overlay=False,
                game_over_overlay=True,
            )
            renderer.draw_game_over_details(screen, score, high_score)
            pygame.display.flip()
            continue

        # Normal draw for PLAYING
        chaser_phase, chaser_time, chaser_ind = enemies.chaser_hud()
        renderer.draw(
            screen=screen,
            state=state,
            score=score,
            high_score=high_score,
            difficulty_level=difficulty_level,
            hp=snake.hp,
            score_flash_s=score_flash_s,
            chaser_hud_phase=chaser_phase,
            chaser_hud_time_s=chaser_time,
            chaser_hud_indicator=chaser_ind,
            snake=snake,
            items=items,
            enemies=enemies,
            paused_overlay=False,
            game_over_overlay=False,
        )
        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()

