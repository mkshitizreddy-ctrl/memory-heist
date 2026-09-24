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
        self.font = pygame.font.Font(None, 28)
        self.small = pygame.font.Font(None, 22)

    def render(self, surface, level_name, score=0, security_level=0, security_max=100, timer_remaining=None):
        # Level label
        label = LEVEL_LABELS.get(level_name, level_name)
        text = self.font.render(label, True, (200, 200, 200))
        surface.blit(text, (16, 12))

        # Score
        score_text = self.font.render(f"Score: {score}", True, (180, 220, 255))
        surface.blit(score_text, (16, 42))

        # Security meter (simple bar)
        bar_x, bar_y, bar_w, bar_h = 16, 72, 180, 14
        pygame.draw.rect(surface, (40, 40, 50), (bar_x, bar_y, bar_w, bar_h), border_radius=4)
        fill = int(bar_w * (security_level / max(1, security_max)))
        color = (80, 200, 100) if security_level < 50 else (220, 180, 40) if security_level < 80 else (220, 60, 60)
        pygame.draw.rect(surface, color, (bar_x, bar_y, fill, bar_h), border_radius=4)
        sec_label = self.small.render(f"Security {security_level}/{security_max}", True, (180, 180, 180))
        surface.blit(sec_label, (bar_x + bar_w + 10, bar_y - 2))

        # Timer (only when active)
        if timer_remaining is not None:
            t = max(0, int(timer_remaining))
            timer_color = (255, 100, 100) if t <= 10 else (220, 220, 100)
            timer_text = self.font.render(f"Time: {t}s", True, timer_color)
            surface.blit(timer_text, (surface.get_width() - 140, 12))
