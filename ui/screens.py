"""
ui/screens.py
Win screen, lose screen.
"""

import pygame


class WinScreen:
    def __init__(self):
        self.title_font = pygame.font.Font(None, 68)
        self.subtitle_font = pygame.font.Font(None, 32)
        self.prompt_font = pygame.font.Font(None, 28)

    def render(self, surface, score=0):
        width = surface.get_width()
        height = surface.get_height()

        title = self.title_font.render("YOU ESCAPED!", True, (90, 230, 140))
        surface.blit(title, (width // 2 - title.get_width() // 2, 180))

        subtitle = self.subtitle_font.render(
            "Master Memory acquired. Mission complete.",
            True, (180, 200, 190)
        )
        surface.blit(subtitle, (width // 2 - subtitle.get_width() // 2, 260))

        score_text = self.subtitle_font.render(f"Final Score: {score}", True, (200, 220, 255))
        surface.blit(score_text, (width // 2 - score_text.get_width() // 2, 320))

        prompt = self.prompt_font.render("Press ESC to quit", True, (140, 150, 160))
        surface.blit(prompt, (width // 2 - prompt.get_width() // 2, height - 80))


class LoseScreen:
    def __init__(self):
        self.title_font = pygame.font.Font(None, 68)
        self.subtitle_font = pygame.font.Font(None, 32)
        self.prompt_font = pygame.font.Font(None, 28)

    def render(self, surface, score=0):
        width = surface.get_width()
        height = surface.get_height()

        title = self.title_font.render("LOCKDOWN", True, (230, 80, 80))
        surface.blit(title, (width // 2 - title.get_width() // 2, 170))

        subtitle = self.subtitle_font.render("MISSION FAILED", True, (200, 130, 130))
        surface.blit(subtitle, (width // 2 - subtitle.get_width() // 2, 250))

        score_text = self.subtitle_font.render(f"Score: {score}", True, (180, 180, 190))
        surface.blit(score_text, (width // 2 - score_text.get_width() // 2, 310))

        prompt = self.prompt_font.render(
            "Press R to retry   |   ESC to quit",
            True, (150, 155, 165)
        )
        surface.blit(prompt, (width // 2 - prompt.get_width() // 2, height - 80))
