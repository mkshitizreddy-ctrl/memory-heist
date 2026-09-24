"""
ui/hud.py
Heads-up display: level, score, security meter, timer.
"""

import pygame

LEVEL_LABELS = {
    "level1": "Level 1 of 5",
    "level2": "Level 2 of 5",
    "level3": "Level 3 of 5",
    "level4": "Level 4 of 5",
    "level5": "Level 5 of 5",
    "final_vault": "Final Vault",
}


class HUD:
    def __init__(self):
        self.font = pygame.font.Font(None, 26)
        self.small = pygame.font.Font(None, 20)

    def render(self, surface, level_name, score=0, security_level=0,
               security_max=100, timer_remaining=None):
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

        # Timer (right side)
        if timer_remaining is not None:
            t = max(0, int(timer_remaining))
            timer_color = (255, 100, 100) if t <= 10 else (220, 220, 100)
            timer_text = self.font.render(f"Time  {t}s", True, timer_color)
            surface.blit(timer_text, (width - 130, 14))
