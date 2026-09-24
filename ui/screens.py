"""
ui/screens.py
Win screen, lose screen, and any transition/feedback screens.
"""

import pygame


class WinScreen:
    def __init__(self):
        self.title_font = pygame.font.Font(None, 64)
        self.prompt_font = pygame.font.Font(None, 32)

    def render(self, surface, score=0):
        width = surface.get_width()
        title = self.title_font.render("YOU ESCAPED!", True, (100, 230, 140))
        score_text = self.prompt_font.render(f"Final Score: {score}", True, (200, 200, 200))
        prompt = self.prompt_font.render("Press ESC to quit", True, (150, 150, 150))
        surface.blit(title, (width // 2 - title.get_width() // 2, 200))
        surface.blit(score_text, (width // 2 - score_text.get_width() // 2, 280))
        surface.blit(prompt, (width // 2 - prompt.get_width() // 2, 340))


class LoseScreen:
    def __init__(self):
        self.title_font = pygame.font.Font(None, 64)
        self.prompt_font = pygame.font.Font(None, 32)

    def render(self, surface, score=0):
        width = surface.get_width()
        title = self.title_font.render("LOCKDOWN", True, (230, 80, 80))
        subtitle = self.prompt_font.render("MISSION FAILED", True, (200, 120, 120))
        score_text = self.prompt_font.render(f"Score: {score}", True, (180, 180, 180))
        prompt = self.prompt_font.render("Press ESC to quit  |  R to retry", True, (150, 150, 150))
        surface.blit(title, (width // 2 - title.get_width() // 2, 180))
        surface.blit(subtitle, (width // 2 - subtitle.get_width() // 2, 250))
        surface.blit(score_text, (width // 2 - score_text.get_width() // 2, 310))
        surface.blit(prompt, (width // 2 - prompt.get_width() // 2, 380))
