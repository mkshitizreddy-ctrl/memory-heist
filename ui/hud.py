"""
ui/hud.py
Owner: Member 5

Heads-up display: score, lives, timer, security meter.
Reads from systems/scoring.py, systems/security.py, systems/timer.py
- does not own game state itself.
"""

import pygame

LEVEL_LABELS = {
    "level1": "Level 1 of 5",
    "level2": "Level 2 of 5",
    "level3": "Level 3 of 5",
    "level4": "Level 4 of 5",
    "level5": "Level 5 of 5",
}


class HUD:
    def __init__(self):
        self.font = pygame.font.Font(None, 28)

    def render(self, surface, level_name):
        label = LEVEL_LABELS.get(level_name, "")
        text = self.font.render(label, True, (200, 200, 200))
        surface.blit(text, (16, 12))