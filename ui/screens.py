"""
ui/screens.py
Win screen, lose screen.
"""

import pygame

from levels.common import draw_cyber_background, draw_glow_text, GREEN, RED


class WinScreen:
    def __init__(self):
        self.title_font = pygame.font.Font(None, 68)
        self.subtitle_font = pygame.font.Font(None, 32)
        self.prompt_font = pygame.font.Font(None, 28)
        self.tick = 0

    def render(self, surface, score=0):
        self.tick += 1
        width = surface.get_width()
        height = surface.get_height()

        draw_cyber_background(surface, self.tick)

        draw_glow_text(surface, self.title_font, "YOU ESCAPED!",
                        (width // 2, 190), color=GREEN)

        subtitle = self.subtitle_font.render(
            "Master Memory acquired. Mission complete.",
            True, (180, 200, 190)
        )
        surface.blit(subtitle, (width // 2 - subtitle.get_width() // 2, 260))

        score_text = self.subtitle_font.render(f"Final Score: {score}", True, (200, 220, 255))
        surface.blit(score_text, (width // 2 - score_text.get_width() // 2, 320))

        pulse = 140 + int(60 * abs((self.tick % 60) - 30) / 30)
        prompt = self.prompt_font.render("Press ESC to quit", True, (pulse, pulse, pulse + 10))
        surface.blit(prompt, (width // 2 - prompt.get_width() // 2, height - 80))


class LoseScreen:
    def __init__(self):
        self.title_font = pygame.font.Font(None, 68)
        self.subtitle_font = pygame.font.Font(None, 32)
        self.prompt_font = pygame.font.Font(None, 28)
        self.tick = 0

    def render(self, surface, score=0):
        self.tick += 1
        width = surface.get_width()
        height = surface.get_height()

        draw_cyber_background(surface, self.tick)

        draw_glow_text(surface, self.title_font, "LOCKDOWN",
                        (width // 2, 180), color=RED, glow_color=(60, 15, 15))

        subtitle = self.subtitle_font.render("MISSION FAILED", True, (200, 130, 130))
        surface.blit(subtitle, (width // 2 - subtitle.get_width() // 2, 250))

        score_text = self.subtitle_font.render(f"Score: {score}", True, (180, 180, 190))
        surface.blit(score_text, (width // 2 - score_text.get_width() // 2, 310))

        pulse = 140 + int(60 * abs((self.tick % 60) - 30) / 30)
        prompt = self.prompt_font.render(
            "Press R to retry   |   ESC to quit",
            True, (pulse, 155, 165)
        )
        surface.blit(prompt, (width // 2 - prompt.get_width() // 2, height - 80))