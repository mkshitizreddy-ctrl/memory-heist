"""
ui/menu.py
Owner: Member 5

Main menu and tutorial screens.
"""

import pygame


class MainMenu:
    def __init__(self):
        self.title_font = pygame.font.Font(None, 64)
        self.prompt_font = pygame.font.Font(None, 32)

    def render(self, surface):
        width = surface.get_width()
        title = self.title_font.render("MEMORY HEIST", True, (220, 220, 220))
        prompt = self.prompt_font.render("Press ENTER to start", True, (150, 150, 150))
        surface.blit(title, (width // 2 - title.get_width() // 2, 220))
        surface.blit(prompt, (width // 2 - prompt.get_width() // 2, 320))

    def handle_click(self, pos):
        pass