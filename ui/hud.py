"""
ui/hud.py
Heads-up display: level, score, security meter, timer.
"""

import math

import pygame

from core.hero_portrait import make_portrait
from ui import theme

LEVEL_LABELS = {
    "level1": "Level 1 of 5",
    "level2": "Level 2 of 5",
    "level3": "Level 3 of 5",
    "level4": "Level 4 of 5",
    "level5": "Level 5 of 5",
    "final_vault": "Final Vault",
}


# Ghost (and Echo in co-op) ride in the bar, so every level shows the heroes.
BADGE_SIZE = 48      # exactly the size of the portrait art: no uneven pixels
BADGE_GAP = 6
BADGE_TIMER_MARGIN = 10   # clear space kept before the timer text
TIMER_SPACE = 130         # width reserved for the timer at the right edge


SEGMENTS = 20             # the security meter is drawn as this many cells
SECURITY_CALM = 50        # below this the meter is green
SECURITY_DANGER = 80      # from here it is red and pulses


# The timer turns red when this many seconds (or fewer) are left.
WARNING_SECONDS = 60


def format_time(seconds):
    """Return seconds as M:SS, rounded up.

    Rounding up means a fresh run reads 15:00 and 0:00 only appears at the
    moment the time is really up.
    """
    whole = max(0, math.ceil(seconds))
    return f"{whole // 60}:{whole % 60:02d}"


def security_colour(level):
    """Green while calm, amber when worrying, red in danger."""
    if level < SECURITY_CALM:
        return theme.TEAL
    if level < SECURITY_DANGER:
        return theme.GOLD
    return theme.CORAL


def lit_segments(level, maximum, count=SEGMENTS):
    """How many meter cells are lit: any non-zero security lights at least one."""
    if level <= 0:
        return 0
    fraction = min(1.0, level / max(1, maximum))
    return max(1, min(count, math.ceil(fraction * count)))


def count_up(shown, target, rate=0.25):
    """Move the displayed score toward the real one, snapping when close."""
    if abs(target - shown) < 1:
        return float(target)
    return shown + (target - shown) * rate


class HUD:
    def __init__(self):
        self.font = pygame.font.Font(None, 26)
        self.small = pygame.font.Font(None, 20)
        self.tiny = pygame.font.Font(None, 16)
        self.big = pygame.font.Font(None, 28)
        self._shown_score = None      # score currently displayed (counts up)
        self._flash = 0               # frames left of the "points gained" glow
        self._last_score = None

    def badge_rects(self, width, coop=False):
        """Where the hero badges go: just left of the timer, Ghost first."""
        count = 2 if coop else 1
        right = width - TIMER_SPACE - BADGE_TIMER_MARGIN
        left = right - count * BADGE_SIZE - (count - 1) * BADGE_GAP
        return [
            pygame.Rect(left + i * (BADGE_SIZE + BADGE_GAP), 0, BADGE_SIZE, BADGE_SIZE)
            for i in range(count)
        ]

    def _score_value(self, score):
        if self._shown_score is None:
            self._shown_score = float(score)
        if self._last_score is not None and score > self._last_score:
            self._flash = 24
        self._last_score = score
        self._shown_score = count_up(self._shown_score, score)
        self._flash = max(0, self._flash - 1)
        return int(round(self._shown_score))

    def _caption(self, surface, text, x, y, colour=theme.MIST):
        surface.blit(self.tiny.render(text, True, colour), (x, y))

    def render(self, surface, level_name, score=0, security_level=0,
               security_max=100, timer_remaining=None, coop=False, tick=0):
        width = surface.get_width()
        palette = theme.floor_palette(level_name)
        accent = palette["accent"]

        # Dark top bar with a thin line in the floor's own colour
        bar = pygame.Surface((width, 48), pygame.SRCALPHA)
        bar.fill((10, 12, 22, 225))
        surface.blit(bar, (0, 0))
        pygame.draw.rect(surface, theme.mix(accent, theme.INK, 0.35), (0, 46, width, 2))

        # Level label with the floor name in the floor's accent colour
        label = LEVEL_LABELS.get(level_name, level_name)
        pygame.draw.rect(surface, accent, (10, 9, 3, 30), border_radius=1)
        surface.blit(self.small.render(label, True, theme.PAPER), (20, 8))
        surface.blit(self.tiny.render(palette["name"].upper(), True, accent), (20, 28))

        # Score (counts up, glows gold when points arrive)
        shown = self._score_value(score)
        self._caption(surface, "SCORE", 200, 6)
        glow = self._flash / 24
        colour = theme.mix(theme.SKY, theme.GOLD, glow)
        surface.blit(self.big.render(f"{shown}", True, colour), (200, 20))

        # Security meter: cells that light up, pulsing when in danger
        bar_x, bar_y, bar_w, bar_h = 360, 22, 160, 14
        self._caption(surface, "SECURITY", bar_x, 6)
        lit = lit_segments(security_level, security_max)
        base = security_colour(security_level)
        if security_level >= SECURITY_DANGER:
            base = theme.mix(base, theme.PAPER, 0.25 * (0.5 + 0.5 * math.sin(tick * 0.35)))
        cell_w = bar_w / SEGMENTS
        for i in range(SEGMENTS):
            cell = pygame.Rect(int(bar_x + i * cell_w), bar_y, max(2, int(cell_w) - 2), bar_h)
            if i < lit:
                pygame.draw.rect(surface, base, cell, border_radius=2)
            else:
                pygame.draw.rect(surface, theme.mix(theme.NAVY, theme.INK, 0.3), cell, border_radius=2)
        sec_label = self.small.render(f"{security_level}/{security_max}", True, theme.MIST)
        surface.blit(sec_label, (bar_x + bar_w + 10, bar_y - 1))

        # Heroes: Ghost, plus Echo in co-op (both blink and pulse with tick).
        names = ["ghost", "echo"] if coop else ["ghost"]
        for name, rect in zip(names, self.badge_rects(width, coop)):
            surface.blit(make_portrait(name, BADGE_SIZE, tick + (15 if name == "echo" else 0)), rect)

        # Timer (right side) on a pill that flashes when time is nearly up
        if timer_remaining is not None:
            remaining = max(0, timer_remaining)
            warning = remaining <= WARNING_SECONDS
            timer_color = (255, 100, 100) if warning else (220, 220, 100)
            pill = pygame.Rect(width - 134, 8, 126, 32)
            edge = theme.SLATE
            if warning:
                edge = theme.mix(theme.SLATE, theme.CORAL, 0.5 + 0.5 * math.sin(tick * 0.3))
            pygame.draw.rect(surface, theme.mix(theme.INK, theme.NAVY, 0.5), pill, border_radius=8)
            pygame.draw.rect(surface, edge, pill, 2, border_radius=8)
            timer_text = self.font.render(
                f"Time  {format_time(remaining)}", True, timer_color
            )
            surface.blit(timer_text, timer_text.get_rect(center=pill.center))
