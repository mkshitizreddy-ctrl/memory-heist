"""
ui/hud.py
Heads-up display: level, score, security meter, timer.
"""

import math

import pygame

from core.hero_portrait import make_portrait

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


# The timer turns red when this many seconds (or fewer) are left.
WARNING_SECONDS = 60


def format_time(seconds):
    """Return seconds as M:SS, rounded up.

    Rounding up means a fresh run reads 15:00 and 0:00 only appears at the
    moment the time is really up.
    """
    whole = max(0, math.ceil(seconds))
    return f"{whole // 60}:{whole % 60:02d}"


class HUD:
    def __init__(self):
        self.font = pygame.font.Font(None, 26)
        self.small = pygame.font.Font(None, 20)

    def badge_rects(self, width, coop=False):
        """Where the hero badges go: just left of the timer, Ghost first."""
        count = 2 if coop else 1
        right = width - TIMER_SPACE - BADGE_TIMER_MARGIN
        left = right - count * BADGE_SIZE - (count - 1) * BADGE_GAP
        return [
            pygame.Rect(left + i * (BADGE_SIZE + BADGE_GAP), 0, BADGE_SIZE, BADGE_SIZE)
            for i in range(count)
        ]

    def render(self, surface, level_name, score=0, security_level=0,
               security_max=100, timer_remaining=None, coop=False, tick=0):
        width = surface.get_width()

        # Semi-transparent top bar
        bar = pygame.Surface((width, 48), pygame.SRCALPHA)
        bar.fill((10, 12, 22, 210))
        surface.blit(bar, (0, 0))

        # Level label
        label = LEVEL_LABELS.get(level_name, level_name)
        text = self.font.render(label, True, (200, 210, 230))
        surface.blit(text, (16, 14))

        # Score
        score_text = self.font.render(f"Score  {score}", True, (160, 210, 255))
        surface.blit(score_text, (200, 14))

        # Security meter
        bar_x, bar_y, bar_w, bar_h = 360, 18, 160, 14
        pygame.draw.rect(surface, (40, 45, 60), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        fill = int(bar_w * (security_level / max(1, security_max)))
        if security_level < 50:
            color = (70, 200, 110)
        elif security_level < 80:
            color = (220, 180, 50)
        else:
            color = (220, 70, 70)
        pygame.draw.rect(surface, color, (bar_x, bar_y, fill, bar_h), border_radius=4)

        sec_label = self.small.render(f"{security_level}/{security_max}", True, (180, 185, 200))
        surface.blit(sec_label, (bar_x + bar_w + 10, bar_y - 1))

        # Heroes: Ghost, plus Echo in co-op (both blink and pulse with tick).
        names = ["ghost", "echo"] if coop else ["ghost"]
        for name, rect in zip(names, self.badge_rects(width, coop)):
            surface.blit(make_portrait(name, BADGE_SIZE, tick + (15 if name == "echo" else 0)), rect)

        # Timer (right side)
        if timer_remaining is not None:
            remaining = max(0, timer_remaining)
            warning = remaining <= WARNING_SECONDS
            timer_color = (255, 100, 100) if warning else (220, 220, 100)
            timer_text = self.font.render(
                f"Time  {format_time(remaining)}", True, timer_color
            )
            surface.blit(timer_text, (width - 130, 14))
