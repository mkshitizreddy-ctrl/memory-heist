"""
ui/menu.py
Owner: Member 5

Main menu and tutorial screen.
"""

import pygame

from levels.common import draw_cyber_background, draw_glow_text, GREEN
from core.difficulty import DIFFICULTIES

CONTROLS = [
    ("Level 1 & 2", "Mouse - click answers / tiles"),
    ("Level 3, 5 & Final Vault", "1-4 keys - select an answer"),
    ("Level 4", "WASD to move, E to collect / interact"),
    ("Any time", "ESC to pause or quit, R to retry after a loss"),
]

DIFFICULTY_ORDER = ["easy", "medium", "hard"]


class MainMenu:
    def __init__(self):
        self.title_font = pygame.font.Font(None, 64)
        self.subtitle_font = pygame.font.Font(None, 26)
        self.heading_font = pygame.font.Font(None, 24)
        self.control_font = pygame.font.Font(None, 22)
        self.prompt_font = pygame.font.Font(None, 32)
        self.tick = 0
        self.selected_difficulty = "medium"

    def handle_event(self, event):
        """Let the player switch difficulty with 1/2/3 while at the menu."""
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_1:
            self.selected_difficulty = "easy"
        elif event.key == pygame.K_2:
            self.selected_difficulty = "medium"
        elif event.key == pygame.K_3:
            self.selected_difficulty = "hard"

    def render(self, surface):
        self.tick += 1
        width = surface.get_width()

        draw_cyber_background(surface, self.tick)

        draw_glow_text(surface, self.title_font, "MEMORY HEIST",
                        (width // 2, 90), color=GREEN)

        subtitle = self.subtitle_font.render(
            "Escape the vault by solving 5 Python puzzles, then the Final Vault.",
            True, (170, 180, 200)
        )
        surface.blit(subtitle, (width // 2 - subtitle.get_width() // 2, 140))

        heading = self.heading_font.render("HOW TO PLAY", True, (140, 200, 255))
        surface.blit(heading, (width // 2 - heading.get_width() // 2, 200))

        y = 240
        for label, action in CONTROLS:
            line = self.control_font.render(f"{label}:  {action}", True, (200, 205, 215))
            surface.blit(line, (width // 2 - line.get_width() // 2, y))
            y += 34

        # Difficulty selector
        y += 20
        diff_heading = self.heading_font.render("DIFFICULTY (press 1/2/3)", True, (140, 200, 255))
        surface.blit(diff_heading, (width // 2 - diff_heading.get_width() // 2, y))
        y += 32

        diff_line_parts = []
        for key_num, name in zip(("1", "2", "3"), DIFFICULTY_ORDER):
            label = DIFFICULTIES[name]["label"]
            marker = "> " if name == self.selected_difficulty else "  "
            diff_line_parts.append(f"{marker}[{key_num}] {label}")
        diff_line = "   ".join(diff_line_parts)
        diff_text = self.control_font.render(diff_line, True, (100, 230, 140))
        surface.blit(diff_text, (width // 2 - diff_text.get_width() // 2, y))

        pulse = 150 + int(70 * abs((self.tick % 60) - 30) / 30)
        prompt = self.prompt_font.render("Press ENTER to start", True, (pulse, 220, pulse))
        surface.blit(prompt, (width // 2 - prompt.get_width() // 2, y + 50))

    def handle_click(self, pos):
        pass