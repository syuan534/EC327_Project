"""
renderer.py

All Pygame drawing for Snake+:
- Arena + grid
- Snake (gradient body, HP-loss flash + invincibility)
- Items (food, golden pulse, sci-fi portal rings, heart/star/magnet/shield/cherry)
- Enemies (blockers + chaser snake)
- HUD sidebar
- Particle system (food eaten burst)
- Screen shake (death)
- Overlays for MENU / PAUSED / GAME_OVER
"""

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
    """A small particle for simple burst effects."""

    pos: pygame.Vector2
    vel: pygame.Vector2
    color: Tuple[int, int, int]
    age_s: float
    life_s: float


class Renderer:
    """
    Owns render-time state:
    - fonts
    - particles
    - screen shake timer
    - bomb flash animation
    """

    def __init__(self) -> None:
        pygame.font.init()
        self.font_score = pygame.font.Font(None, C.HUD_SCORE_SIZE)
        self.font_label = pygame.font.Font(None, C.HUD_LABEL_SIZE)
        self.font_small = pygame.font.Font(None, C.HUD_SMALL_SIZE)

        self.particles: List[Particle] = []
        self.shake_remaining_s: float = 0.0
        self._time_s: float = 0.0

    def trigger_shake(self) -> None:
        """Start screen shake."""
        self.shake_remaining_s = C.SHAKE_DURATION_S

    def spawn_eat_particles(self, cell: Cell, color: Tuple[int, int, int]) -> None:
        """Spawn a burst of particles at a grid cell center."""
        cx, cy = self._cell_center_px(cell)
        origin = pygame.Vector2(cx, cy)
        for _ in range(C.PARTICLES_ON_EAT):
            ang = random.random() * math.tau
            spd = C.PARTICLE_SPEED_PX_PER_S * (0.6 + 0.6 * random.random())
            vel = pygame.Vector2(math.cos(ang), math.sin(ang)) * spd
            self.particles.append(
                Particle(pos=origin.copy(), vel=vel, color=color, age_s=0.0, life_s=C.PARTICLE_LIFETIME_S)
            )

    def update_fx(self, dt_s: float) -> None:
        """Advance particle and animation timers."""
        self._time_s += dt_s
        if self.shake_remaining_s > 0:
            self.shake_remaining_s = max(0.0, self.shake_remaining_s - dt_s)

        keep: List[Particle] = []
        for p in self.particles:
            p.age_s += dt_s
            if p.age_s >= p.life_s:
                continue
            p.pos += p.vel * dt_s
            keep.append(p)
        self.particles = keep

    def draw(
        self,
        screen: pygame.Surface,
        state: str,
        score: int,
        high_score: int,
        difficulty_level: int,
        hp: int,
        score_flash_s: float,
        chaser_hud_phase: str,
        chaser_hud_time_s: float,
        chaser_hud_indicator: str,
        snake: Snake,
        items: ItemManager,
        enemies: EnemyManager,
        paused_overlay: bool,
        game_over_overlay: bool,
    ) -> None:
        """
        Draw the entire frame based on current game state.
        """
        # Camera shake offset
        ox, oy = self._shake_offset()

        screen.fill(C.COLOR_BG)

        arena = pygame.Surface((C.ARENA_WIDTH, C.ARENA_HEIGHT))
        arena.fill(C.COLOR_BG)

        self._draw_grid(arena)
        self._draw_border(arena)
        if items.magnet_active():
            self._draw_magnet_radius(arena, snake.head)
        self._draw_items(arena, items)
        self._draw_enemies(arena, enemies)
        self._draw_snake(arena, snake)
        self._draw_particles(arena)

        screen.blit(arena, (ox, oy))

        self._draw_sidebar(
            screen,
            score,
            score_flash_s,
            high_score,
            hp,
            difficulty_level,
            snake,
            items,
            chaser_hud_phase,
            chaser_hud_time_s,
            chaser_hud_indicator,
        )

        if paused_overlay:
            self._draw_center_overlay(screen, "PAUSED")
        if game_over_overlay:
            self._draw_center_overlay(screen, "GAME OVER")

    def draw_menu(self, screen: pygame.Surface, high_score: int) -> None:
        """Title screen."""
        screen.fill(C.COLOR_BG)
        title = pygame.font.Font(None, C.HUD_SCORE_SIZE + C.HUD_LABEL_SIZE).render("Snake+", True, C.COLOR_TEXT)
        subtitle = self.font_label.render("Press ENTER to start", True, C.COLOR_TEXT_MUTED)
        hs = self.font_label.render(f"High score: {high_score}", True, C.COLOR_TEXT)

        cx = C.WINDOW_WIDTH // 2
        cy = C.WINDOW_HEIGHT // 2
        screen.blit(title, (cx - title.get_width() // 2, cy - 80))
        screen.blit(subtitle, (cx - subtitle.get_width() // 2, cy - 20))
        screen.blit(hs, (cx - hs.get_width() // 2, cy + 20))

        self._draw_controls_hint(screen, in_menu=True)

    def draw_game_over_details(self, screen: pygame.Surface, score: int, high_score: int) -> None:
        """Game over detailed overlay (score + rank vs high score)."""
        overlay = pygame.Surface((C.WINDOW_WIDTH, C.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*C.COLOR_OVERLAY, 160))
        screen.blit(overlay, (0, 0))

        cx = C.WINDOW_WIDTH // 2
        cy = C.WINDOW_HEIGHT // 2

        go = pygame.font.Font(None, C.HUD_SCORE_SIZE + C.HUD_LABEL_SIZE).render("GAME OVER", True, C.COLOR_TEXT)
        sc = self.font_score.render(str(score), True, C.COLOR_TEXT)
        tag = "NEW HIGH SCORE!" if score >= high_score and high_score > 0 else "Try again"
        rank = self.font_label.render(tag, True, C.COLOR_TEXT_MUTED)

        hint = self.font_small.render("Press R to restart or Q to quit", True, C.COLOR_TEXT)

        screen.blit(go, (cx - go.get_width() // 2, cy - 110))
        screen.blit(sc, (cx - sc.get_width() // 2, cy - 40))
        screen.blit(rank, (cx - rank.get_width() // 2, cy + 10))
        screen.blit(hint, (cx - hint.get_width() // 2, cy + 60))

    # -------------------------
    # Drawing helpers
    # -------------------------

    def _shake_offset(self) -> Tuple[int, int]:
        if self.shake_remaining_s <= 0:
            return (0, 0)
        # deterministic-ish jitter
        mag = C.SHAKE_DISTANCE_PX * (self.shake_remaining_s / C.SHAKE_DURATION_S)
        return (int(random.uniform(-mag, mag)), int(random.uniform(-mag, mag)))

    def _draw_grid(self, surf: pygame.Surface) -> None:
        for i in range(C.GRID_SIZE + 1):
            x = i * C.CELL_SIZE
            pygame.draw.line(surf, C.COLOR_GRID_LINE, (x, 0), (x, C.ARENA_HEIGHT), C.GRID_LINE_WIDTH)
            pygame.draw.line(surf, C.COLOR_GRID_LINE, (0, x), (C.ARENA_WIDTH, x), C.GRID_LINE_WIDTH)

    def _draw_border(self, surf: pygame.Surface) -> None:
        """Bright border line around the arena (walls visible)."""
        pygame.draw.rect(surf, C.COLOR_BORDER, pygame.Rect(0, 0, C.ARENA_WIDTH, C.ARENA_HEIGHT), C.BORDER_LINE_WIDTH)

    def _draw_magnet_radius(self, surf: pygame.Surface, head: Cell) -> None:
        """Blue glow radius circle around the snake head while magnet is active."""
        cx, cy = self._cell_center_px(head)
        r = C.MAGNET_RADIUS_CELLS * C.CELL_SIZE
        s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*C.COLOR_ITEM_MAGNET, 40), (r + 1, r + 1), r, 0)
        pygame.draw.circle(s, (*C.COLOR_ITEM_MAGNET, 90), (r + 1, r + 1), r, 2)
        surf.blit(s, (cx - r - 1, cy - r - 1))

    def _cell_rect(self, cell: Cell, inset: int = C.CELL_INSET) -> pygame.Rect:
        x, y = cell
        return pygame.Rect(
            x * C.CELL_SIZE + inset,
            y * C.CELL_SIZE + inset,
            C.CELL_SIZE - inset * 2,
            C.CELL_SIZE - inset * 2,
        )

    def _cell_center_px(self, cell: Cell) -> Tuple[int, int]:
        x, y = cell
        return (x * C.CELL_SIZE + C.CELL_SIZE // 2, y * C.CELL_SIZE + C.CELL_SIZE // 2)

    def _lerp(self, a: int, b: int, t: float) -> int:
        return int(a + (b - a) * t)

    def _lerp_color(self, c1: Tuple[int, int, int], c2: Tuple[int, int, int], t: float) -> Tuple[int, int, int]:
        return (self._lerp(c1[0], c2[0], t), self._lerp(c1[1], c2[1], t), self._lerp(c1[2], c2[2], t))

    @staticmethod
    def _clamp255(v: float) -> int:
        return int(max(0, min(255, v)))

    def _lighter_rgb(self, color: Tuple[int, int, int], delta: float, rel: float) -> Tuple[int, int, int]:
        """Lighten an RGB tuple; delta scales with rel (0..1) derived from rect size."""
        d = delta * rel
        return (
            self._clamp255(color[0] + d),
            self._clamp255(color[1] + d),
            self._clamp255(color[2] + d),
        )

    def draw_portal(self, surf: pygame.Surface, rect: pygame.Rect, color: Tuple[int, int, int], pulse_alpha: int) -> None:
        """
        Sci-fi portal ring using pygame primitives (no external assets).
        All geometry is derived from rect.width / rect.height.
        """
        label_h = max(1, rect.height // 4)
        ring_rect = pygame.Rect(rect.x, rect.y, rect.width, rect.height - label_h)

        cx = ring_rect.centerx
        cy = ring_rect.centery
        r = max(1, min(ring_rect.width, ring_rect.height) // 2 - 1)

        span = float(min(ring_rect.width, ring_rect.height))
        rel = max(0.15, min(1.0, span / max(1.0, float(rect.width))))

        thick_outer = max(2, int(rect.width * 0.14 + 0.5))
        thick_inner = max(1, (thick_outer + 1) // 3)
        inset_inner = max(2, int(rect.width * 0.22 + 0.5))
        glow_r = max(1, rect.width // 6)

        inner_color = self._lighter_rgb(color, 60.0, rel)

        outer_a = int(max(0, min(255, pulse_alpha)))
        outer_layer = pygame.Surface((ring_rect.width, ring_rect.height), pygame.SRCALPHA)
        pygame.draw.circle(outer_layer, color, (ring_rect.width // 2, ring_rect.height // 2), r, thick_outer)
        outer_layer.set_alpha(outer_a)
        surf.blit(outer_layer, (ring_rect.x, ring_rect.y))

        pygame.draw.circle(surf, inner_color, (cx, cy), max(1, r - inset_inner), thick_inner)
        pygame.draw.circle(surf, inner_color, (cx, cy), glow_r, 0)

        swoosh_inset = max(1, int(rect.width * 0.16 + 0.5))
        swoosh_rect = pygame.Rect(
            ring_rect.x + swoosh_inset,
            ring_rect.y + swoosh_inset,
            ring_rect.width - swoosh_inset * 2,
            ring_rect.height - swoosh_inset * 2,
        )
        swoosh_w = max(1, (thick_outer + 1) // 2)
        pygame.draw.arc(surf, inner_color, swoosh_rect, math.radians(200), math.radians(340), swoosh_w)
        pygame.draw.arc(surf, inner_color, swoosh_rect, math.radians(20), math.radians(160), swoosh_w)

    def draw_shield(self, surf: pygame.Surface, rect: pygame.Rect) -> None:
        """Classic heater-shield icon scaled to rect."""
        cx = rect.centerx
        cy = rect.centery
        w = max(1, rect.width - 2)
        h = max(1, rect.height - 2)

        points = [
            (cx - w // 2, cy - h // 2),
            (cx + w // 2, cy - h // 2),
            (cx + w // 2, cy),
            (cx, cy + h // 2),
            (cx - w // 2, cy),
        ]

        fill_col = (20, 80, 40)
        line_col = (80, 220, 120)
        line_w = max(1, int(rect.width * 0.10))

        pygame.draw.polygon(surf, fill_col, points)
        pygame.draw.polygon(surf, line_col, points, line_w)

        margin = max(1, int(rect.width * 0.06))
        pygame.draw.line(surf, line_col, (cx, cy - h // 2 + margin), (cx, cy + h // 2 - margin), max(1, line_w // 2))
        pygame.draw.line(
            surf,
            line_col,
            (cx - w // 2 + margin, cy - h // 6),
            (cx + w // 2 - margin, cy - h // 6),
            max(1, line_w // 2),
        )

    def draw_magnet(self, surf: pygame.Surface, rect: pygame.Rect) -> None:
        """U-shaped horseshoe magnet scaled to rect."""
        cx = rect.centerx
        cy = rect.centery
        w = max(1, rect.width - 2)
        h = max(1, rect.height - 2)

        arm_w = max(1, w // 4)
        arm_h = max(1, h // 2 + max(1, h // 16))
        arm_y = cy - h // 4

        left_arm = pygame.Rect(cx - w // 2, arm_y, arm_w, arm_h)
        right_arm = pygame.Rect(cx + w // 2 - arm_w, arm_y, arm_w, arm_h)

        red = (220, 50, 50)
        blue = (50, 100, 220)
        silver = (160, 160, 180)

        pygame.draw.rect(surf, red, left_arm, border_radius=max(0, arm_w // 6))
        pygame.draw.rect(surf, blue, right_arm, border_radius=max(0, arm_w // 6))

        mid_h = max(1, arm_w)
        mid_rect = pygame.Rect(cx - w // 2, cy - h // 2, w, mid_h)
        pygame.draw.rect(surf, silver, mid_rect, border_radius=max(0, mid_h // 3))

        arc_h = max(1, arm_w * 2)
        arc_rect = pygame.Rect(cx - w // 2, cy + h // 4 - mid_h, w, arc_h)
        pygame.draw.arc(surf, red, arc_rect, math.radians(180), math.radians(270), arm_w)
        pygame.draw.arc(surf, blue, arc_rect, math.radians(270), math.radians(360), arm_w)

        cap_h = max(1, int(rect.height * 0.16))
        pygame.draw.rect(surf, (255, 80, 80), pygame.Rect(cx - w // 2, cy + h // 4, arm_w, cap_h), border_radius=max(0, cap_h // 3))
        pygame.draw.rect(surf, (80, 140, 255), pygame.Rect(cx + w // 2 - arm_w, cy + h // 4, arm_w, cap_h), border_radius=max(0, cap_h // 3))

    def _draw_snake(self, surf: pygame.Surface, snake: Snake) -> None:
        body = list(snake.body)
        if not body:
            return

        flash = snake.flash_color()
        blink_on = True
        if snake.is_invincible():
            blink_on = int(self._time_s * 12) % 2 == 0

        n = len(body)
        for i, cell in enumerate(body):
            rect = self._cell_rect(cell)
            if flash and blink_on:
                color = flash
            elif i == 0:
                color = C.COLOR_SNAKE_HEAD
            else:
                t = i / max(1, n - 1)
                color = self._lerp_color(C.COLOR_SNAKE_HEAD, C.COLOR_SNAKE_TAIL, t)
            pygame.draw.rect(surf, color, rect, border_radius=C.SNAKE_CORNER_RADIUS)
            pygame.draw.rect(surf, C.COLOR_SNAKE_OUTLINE, rect, 1, border_radius=C.SNAKE_CORNER_RADIUS)

        # Shield absorb ring flash (short ring, only when flash is white and just triggered)
        if flash == C.COLOR_SHIELD_FLASH and snake.is_invincible():
            # Approximate "just triggered" window.
            if snake.invincible_s > (C.INVINCIBILITY_DURATION_S - C.SHIELD_FLASH_DURATION_S):
                self._draw_shield_ring(surf, snake.head)

    def _draw_items(self, surf: pygame.Surface, items: ItemManager) -> None:
        # Normal food
        for p in items.normal_food:
            cx, cy = self._cell_center_px(p)
            pygame.draw.circle(surf, C.COLOR_FOOD_NORMAL, (cx, cy), C.FOOD_RADIUS)

        # Golden food (pulsing alpha)
        alpha = items.golden_alpha()
        for gf in items.golden_foods:
            s = pygame.Surface((C.CELL_SIZE, C.CELL_SIZE), pygame.SRCALPHA)
            pygame.draw.circle(s, (*C.COLOR_FOOD_GOLDEN, alpha), (C.CELL_SIZE // 2, C.CELL_SIZE // 2), C.GOLDEN_FOOD_RADIUS)
            surf.blit(s, (gf.pos[0] * C.CELL_SIZE, gf.pos[1] * C.CELL_SIZE))

        # Heart item (pulsing scale)
        if items.heart_item:
            self._draw_heart(surf, items.heart_item, items.heart_pulse_scale())

        # Score multiplier star
        if items.multiplier_item:
            self._draw_star(surf, items.multiplier_item)

        # Magnet item
        if items.magnet_item:
            self.draw_magnet(surf, self._cell_rect(items.magnet_item))

        # Shield item
        if items.shield_item:
            self.draw_shield(surf, self._cell_rect(items.shield_item))

        # Cherry item
        if items.cherry:
            self._draw_cherry(surf, items.cherry.pos)

        # Portals (A/B): sci-fi ring icons + small label below
        if items.portals:
            alpha = items.portal_glow_alpha()
            portal_a_color = (160, 80, 255)
            portal_b_color = (80, 160, 255)
            for label, pos, p_color in (
                ("A", items.portals.a, portal_a_color),
                ("B", items.portals.b, portal_b_color),
            ):
                cell_rect = pygame.Rect(pos[0] * C.CELL_SIZE, pos[1] * C.CELL_SIZE, C.CELL_SIZE, C.CELL_SIZE)
                self.draw_portal(surf, cell_rect, p_color, alpha)

                label_px = max(6, (cell_rect.height * 4) // 9)
                font = pygame.font.Font(None, label_px)
                t = font.render(label, True, C.COLOR_TEXT)
                lx = cell_rect.centerx - t.get_width() // 2
                margin = max(1, cell_rect.height // 12)
                ly = cell_rect.bottom - t.get_height() - margin
                surf.blit(t, (lx, ly))

    def _draw_enemies(self, surf: pygame.Surface, enemies: EnemyManager) -> None:
        for b in enemies.blockers:
            rect = self._cell_rect(b.pos)
            pygame.draw.rect(surf, C.COLOR_ENEMY_BLOCKER, rect, border_radius=2)
        if enemies.chaser:
            self._draw_chaser_snake(surf, list(enemies.chaser.body))

    def _draw_particles(self, surf: pygame.Surface) -> None:
        for p in self.particles:
            t = p.age_s / max(0.001, p.life_s)
            alpha = int(255 * (1.0 - t))
            s = pygame.Surface((C.PARTICLE_RADIUS_PX * 2 + 2, C.PARTICLE_RADIUS_PX * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*p.color, alpha), (C.PARTICLE_RADIUS_PX + 1, C.PARTICLE_RADIUS_PX + 1), C.PARTICLE_RADIUS_PX)
            surf.blit(s, (p.pos.x - C.PARTICLE_RADIUS_PX - 1, p.pos.y - C.PARTICLE_RADIUS_PX - 1))

    def _draw_sidebar(
        self,
        screen: pygame.Surface,
        score: int,
        score_flash_s: float,
        high_score: int,
        hp: int,
        difficulty_level: int,
        snake: Snake,
        items: ItemManager,
        chaser_hud_phase: str,
        chaser_hud_time_s: float,
        chaser_hud_indicator: str,
    ) -> None:
        panel = pygame.Rect(C.ARENA_WIDTH, 0, C.SIDEBAR_WIDTH, C.WINDOW_HEIGHT)
        pygame.draw.rect(screen, C.COLOR_SIDEBAR_BG, panel)

        x = C.ARENA_WIDTH + C.HUD_PADDING
        y = C.HUD_PADDING

        score_color = C.COLOR_SCORE_FLASH if score_flash_s > 0 else C.COLOR_TEXT
        s = self.font_score.render(str(score), True, score_color)
        screen.blit(s, (x, y))
        y += s.get_height() + C.HUD_LINE_GAP

        hs = self.font_label.render(f"High: {high_score}", True, C.COLOR_TEXT_MUTED)
        screen.blit(hs, (x, y))
        y += hs.get_height() + C.HUD_LINE_GAP

        # Hearts
        y += 2
        self._draw_hearts(screen, (x, y), hp)
        y += self.font_label.get_height() + C.HUD_LINE_GAP

        # Active powerup + countdown
        if items.multiplier_active():
            self._draw_powerup_bar(screen, x, y, "x2", items.multiplier_remaining_s, C.SCORE_MULTIPLIER_DURATION_S, C.COLOR_ITEM_STAR)
            y += C.POWERUP_BAR_HEIGHT + 20
        elif items.magnet_active():
            self._draw_powerup_bar(screen, x, y, "MAGNET", items.magnet_remaining_s, C.MAGNET_DURATION_S, C.COLOR_ITEM_MAGNET)
            y += C.POWERUP_BAR_HEIGHT + 20
        else:
            label = self.font_label.render("Power: -", True, C.COLOR_TEXT_MUTED)
            screen.blit(label, (x, y))
            y += label.get_height() + C.HUD_LINE_GAP

        # Shield status
        if snake.shield_active:
            sh = self.font_label.render("Shield: ON", True, C.COLOR_ITEM_SHIELD)
            screen.blit(sh, (x, y))
        else:
            sh = self.font_label.render("Shield: -", True, C.COLOR_TEXT_MUTED)
            screen.blit(sh, (x, y))
        y += sh.get_height() + C.HUD_LINE_GAP

        ln = self.font_label.render(f"Length: {snake.length()}", True, C.COLOR_TEXT_MUTED)
        screen.blit(ln, (x, y))
        y += ln.get_height() + C.HUD_LINE_GAP

        # Chaser HUD (hunt vs cooldown)
        if chaser_hud_phase == "hunt":
            warn_color = C.COLOR_CHASER_HUD_ACTIVE if int(self._time_s * 8) % 2 == 0 else (160, 50, 50)
            line = "! CHASER ACTIVE !"
            w = self.font_label.render(line, True, warn_color)
            screen.blit(w, (x, y))
            y += w.get_height() + C.HUD_LINE_GAP
            if chaser_hud_indicator:
                ind = self.font_label.render(chaser_hud_indicator, True, warn_color)
                screen.blit(ind, (x, y))
                y += ind.get_height() + C.HUD_LINE_GAP
        elif chaser_hud_phase == "cooldown":
            secs = int(max(0.0, chaser_hud_time_s) + 0.999)
            w = self.font_label.render(f"Chaser cooldown: {secs}s", True, C.COLOR_CHASER_HUD_COOLDOWN)
            screen.blit(w, (x, y))
            y += w.get_height() + C.HUD_LINE_GAP

        diff = self.font_label.render(f"Difficulty: {difficulty_level}", True, C.COLOR_TEXT_MUTED)
        screen.blit(diff, (x, y))
        y += diff.get_height() + C.HUD_LINE_GAP

        # Controls hint at bottom
        self._draw_controls_hint(screen, in_menu=False)

    def _draw_hearts(self, screen: pygame.Surface, pos: Tuple[int, int], hp: int) -> None:
        """Draw hearts using text; gray out lost hearts."""
        x, y = pos
        full = "❤"
        for i in range(C.PLAYER_MAX_HP):
            color = C.COLOR_ITEM_HEART if i < hp else C.COLOR_HEART_LOST
            t = self.font_label.render(full, True, color)
            screen.blit(t, (x + i * (t.get_width() + 4), y))

    def _draw_powerup_bar(
        self,
        screen: pygame.Surface,
        x: int,
        y: int,
        label: str,
        remaining_s: float,
        total_s: float,
        color: Tuple[int, int, int],
    ) -> None:
        """Draw a labeled countdown bar."""
        t = self.font_label.render(f"Power: {label}", True, color)
        screen.blit(t, (x, y))
        y2 = y + t.get_height() + 4
        frac = max(0.0, min(1.0, remaining_s / max(0.001, total_s)))
        bar_bg = pygame.Rect(x, y2, C.POWERUP_BAR_WIDTH, C.POWERUP_BAR_HEIGHT)
        pygame.draw.rect(screen, (50, 50, 70), bar_bg, border_radius=4)
        bar_fg = pygame.Rect(x, y2, int(C.POWERUP_BAR_WIDTH * frac), C.POWERUP_BAR_HEIGHT)
        pygame.draw.rect(screen, color, bar_fg, border_radius=4)

    def _draw_shield_ring(self, surf: pygame.Surface, head: Cell) -> None:
        """White ring flash from snake head on shield absorb."""
        cx, cy = self._cell_center_px(head)
        r = int(C.SHIELD_FLASH_MAX_RADIUS_PX * 0.55)
        s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (*C.COLOR_SHIELD_FLASH, 160), (r + 1, r + 1), r, 4)
        surf.blit(s, (cx - r - 1, cy - r - 1))

    def _draw_heart(self, surf: pygame.Surface, cell: Cell, scale: float) -> None:
        """Draw a heart shape at cell center with a scale pulse."""
        cx, cy = self._cell_center_px(cell)
        size = max(C.ITEM_MIN_DRAW_PX, int(C.ITEM_MIN_DRAW_PX * scale))
        r = size // 4
        s = pygame.Surface((size + 2, size + 2), pygame.SRCALPHA)
        # Two circles + triangle-ish bottom
        pygame.draw.circle(s, C.COLOR_ITEM_HEART, (size // 2 - r, size // 2 - r), r)
        pygame.draw.circle(s, C.COLOR_ITEM_HEART, (size // 2 + r, size // 2 - r), r)
        pts = [(size // 2 - 2 * r, size // 2 - r), (size // 2 + 2 * r, size // 2 - r), (size // 2, size)]
        pygame.draw.polygon(s, C.COLOR_ITEM_HEART, pts)
        surf.blit(s, (cx - size // 2, cy - size // 2))

    def _draw_star(self, surf: pygame.Surface, cell: Cell) -> None:
        """Draw a 5-point star."""
        cx, cy = self._cell_center_px(cell)
        size = max(C.ITEM_MIN_DRAW_PX, C.ITEM_MIN_DRAW_PX)
        r1 = size // 2
        r2 = max(2, r1 // 2)
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * (math.pi / 5)
            r = r1 if i % 2 == 0 else r2
            pts.append((cx + math.cos(ang) * r, cy + math.sin(ang) * r))
        pygame.draw.polygon(surf, C.COLOR_ITEM_STAR, pts)

    def _draw_letter_badge(self, surf: pygame.Surface, cell: Cell, letter: str, color: Tuple[int, int, int]) -> None:
        """Draw a colored badge with a letter."""
        rect = self._cell_rect(cell, inset=C.CELL_INSET)
        pygame.draw.rect(surf, color, rect, border_radius=4)
        t = self.font_small.render(letter, True, (10, 10, 20))
        cx, cy = self._cell_center_px(cell)
        surf.blit(t, (cx - t.get_width() // 2, cy - t.get_height() // 2))

    def _draw_cherry(self, surf: pygame.Surface, cell: Cell) -> None:
        """Draw a bright cherry (pink circle + small stem)."""
        cx, cy = self._cell_center_px(cell)
        r = max(C.ITEM_MIN_DRAW_PX // 3, C.FOOD_RADIUS)
        pygame.draw.circle(surf, C.COLOR_ITEM_CHERRY, (cx, cy), r)
        pygame.draw.line(surf, (80, 220, 140), (cx, cy - r), (cx + r // 2, cy - r - r // 2), 2)

    def _draw_chaser_snake(self, surf: pygame.Surface, body: List[Cell]) -> None:
        """Draw the enemy chaser snake with eyes on the head."""
        for i, cell in enumerate(body):
            rect = self._cell_rect(cell)
            color = C.COLOR_CHASER_HEAD if i == 0 else C.COLOR_CHASER_BODY
            pygame.draw.rect(surf, color, rect, border_radius=C.SNAKE_CORNER_RADIUS)
        if body:
            head = body[0]
            cx, cy = self._cell_center_px(head)
            eye_dx = max(2, C.CELL_SIZE // 6)
            eye_dy = max(2, C.CELL_SIZE // 6)
            pygame.draw.circle(surf, C.COLOR_CHASER_EYE, (cx - eye_dx, cy - eye_dy), 2)
            pygame.draw.circle(surf, C.COLOR_CHASER_EYE, (cx + eye_dx, cy - eye_dy), 2)

    def _draw_controls_hint(self, screen: pygame.Surface, in_menu: bool) -> None:
        x = C.ARENA_WIDTH + C.HUD_PADDING
        lines = []
        if in_menu:
            lines = ["ENTER: start", "Q: quit"]
        else:
            lines = ["Arrows: move", "P: pause", "R: restart", "Q: quit"]
        # Draw from bottom up
        y = C.WINDOW_HEIGHT - C.HUD_PADDING - (len(lines) * (self.font_small.get_height() + 2))
        for line in lines:
            t = self.font_small.render(line, True, C.COLOR_TEXT_MUTED)
            screen.blit(t, (x, y))
            y += t.get_height() + 2

    def _draw_center_overlay(self, screen: pygame.Surface, text: str) -> None:
        overlay = pygame.Surface((C.WINDOW_WIDTH, C.WINDOW_HEIGHT), pygame.SRCALPHA)
        overlay.fill((*C.COLOR_OVERLAY, 140))
        screen.blit(overlay, (0, 0))
        t = pygame.font.Font(None, C.HUD_SCORE_SIZE + C.HUD_LABEL_SIZE).render(text, True, C.COLOR_TEXT)
        screen.blit(t, (C.WINDOW_WIDTH // 2 - t.get_width() // 2, C.WINDOW_HEIGHT // 2 - t.get_height() // 2))

