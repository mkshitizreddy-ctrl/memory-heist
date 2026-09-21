"""
ui/screens.py
Owner: Member 5

Win screen, lose screen, and any transition/feedback screens.
"""

import pygame


class WinScreen:
    def __init__(self):
        self.title_font = pygame.font.Font(None, 64)
        self.prompt_font = pygame.font.Font(None, 32)

    def render(self, surface):
        width = surface.get_width()
        title = self.title_font.render("YOU ESCAPED!", True, (100, 230, 140))
        prompt = self.prompt_font.render("Press ESC to quit", True, (150, 150, 150))
        surface.blit(title, (width // 2 - title.get_width() // 2, 220))
        surface.blit(prompt, (width // 2 - prompt.get_width() // 2, 320))


class LoseScreen:
    def render(self, surface):
        pass