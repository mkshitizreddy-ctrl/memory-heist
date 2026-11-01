"""
ui/menu.py
Owner: Member 5

Main menu and tutorial screen.
"""

import pygame

from levels.common import draw_glow_text, GREEN
from core.difficulty import DIFFICULTIES
from core.hero_portrait import make_portrait
from ui import theme
from ui.backdrop import draw_backdrop
from ui.kit import blit_centered, draw_chip, draw_panel

CONTROLS = [
    ("Level 1 & 2", "Mouse - click answers / tiles"),
    ("Level 3, 5 & Final Vault", "1-4 keys - select an answer"),
    ("Level 3 & 4", "WASD to move, E to collect / interact"),
    ("Co-op (C)", "Player 2: arrow keys to move, Right Shift to interact"),
    ("Any time", "ESC to pause or quit, R to retry after a loss"),
]

DIFFICULTY_ORDER = ["easy", "medium", "hard"]
DIFFICULTY_TINT = {"easy": theme.TEAL, "medium": theme.GOLD, "hard": theme.CORAL}
PORTRAIT_SIZE = 96
ROW_HEIGHT = 30


class MainMenu:
    def __init__(self):
        self.title_font = pygame.font.Font(None, 64)
        self.subtitle_font = pygame.font.Font(None, 26)
        self.heading_font = pygame.font.Font(None, 24)
        self.control_font = pygame.font.Font(None, 22)
        self.prompt_font = pygame.font.Font(None, 32)
        self.tick = 0
        self.selected_difficulty = "medium"
        self.coop = False

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
        elif event.key == pygame.K_c:
            self.coop = not self.coop

    def layout(self, width=960):
        """Every block's rectangle, so nothing overlaps and tests can check it."""
        cx = width // 2
        panel = pygame.Rect(0, 0, 720, 36 + len(CONTROLS) * ROW_HEIGHT + 14)
        panel.midtop = (cx, 168)
        chips = []
        for i in range(3):
            chip = pygame.Rect(0, 0, 170, 34)
            chip.midtop = (cx + (i - 1) * 190, panel.bottom + 52)
            chips.append(chip)
        coop = pygame.Rect(0, 0, 330, 34)
        coop.midtop = (cx, chips[0].bottom + 14)
        start = pygame.Rect(0, 0, 340, 46)
        start.midtop = (cx, coop.bottom + 22)
        return {"panel": panel, "chips": chips, "coop": coop, "start": start,
                "heroes": [pygame.Rect(cx - 370, 30, PORTRAIT_SIZE, PORTRAIT_SIZE),
                           pygame.Rect(cx + 370 - PORTRAIT_SIZE, 30, PORTRAIT_SIZE, PORTRAIT_SIZE)]}

    def render(self, surface):
        self.tick += 1
        width = surface.get_width()
        lay = self.layout(width)

        draw_backdrop(surface, self.tick, theme.SKY)

        # Ghost always; Echo glows only when co-op is on
        ghost_rect, echo_rect = lay["heroes"]
        surface.blit(make_portrait("ghost", PORTRAIT_SIZE, self.tick), ghost_rect)
        echo = make_portrait("echo", PORTRAIT_SIZE, self.tick + 15)
        if not self.coop:
            echo = echo.copy()
            echo.set_alpha(70)
        surface.blit(echo, echo_rect)

        draw_glow_text(surface, self.title_font, "MEMORY HEIST",
                        (width // 2, 70), color=GREEN)
        subtitle = self.subtitle_font.render(
            "Escape the vault by solving 5 Python puzzles, then the Final Vault.",
            True, theme.MIST
        )
        blit_centered(surface, subtitle, (width // 2, 124))

        # How to play: a panel with a key chip per row
        panel = draw_panel(surface, lay["panel"], fill=theme.mix(theme.INK, theme.NAVY, 0.6),
                           border=theme.SLATE)
        blit_centered(surface, self.heading_font.render("HOW TO PLAY", True, theme.SKY),
                      (panel.centerx, panel.y + 20))
        y = panel.y + 36 + ROW_HEIGHT // 2
        for label, action in CONTROLS:
            tag = self.control_font.render(label, True, theme.GOLD)
            surface.blit(tag, (panel.x + 24, y - tag.get_height() // 2))
            line = self.control_font.render(action, True, theme.PAPER)
            surface.blit(line, (panel.x + 250, y - line.get_height() // 2))
            y += ROW_HEIGHT

        # Difficulty selector: three chips, the chosen one is solid
        blit_centered(surface, self.heading_font.render("DIFFICULTY (press 1/2/3)", True, theme.SKY),
                      (width // 2, lay["chips"][0].y - 16))
        for chip, key_num, name in zip(lay["chips"], ("1", "2", "3"), DIFFICULTY_ORDER):
            label = DIFFICULTIES[name]["label"]
            tint = DIFFICULTY_TINT[name]
            draw_chip(surface, chip, f"[{key_num}] {label}", self.control_font,
                      fg=tint, border=tint, filled=name == self.selected_difficulty)

        mode = "ON (P2: arrow keys)" if self.coop else "OFF"
        draw_chip(surface, lay["coop"], f"CO-OP (press C): {mode}", self.control_font,
                  fg=theme.GOLD, border=theme.GOLD, filled=self.coop)

        # Start prompt: breathes
        pulse = 0.5 + 0.5 * abs((self.tick % 60) - 30) / 30
        start = lay["start"]
        pygame.draw.rect(surface, theme.mix(theme.INK, theme.TEAL, 0.25 + 0.2 * pulse), start,
                         border_radius=start.height // 2)
        pygame.draw.rect(surface, theme.mix(theme.TEAL, theme.PAPER, 0.4 * pulse), start,
                         width=2, border_radius=start.height // 2)
        blit_centered(surface, self.prompt_font.render("Press ENTER to start", True,
                                                       theme.mix(theme.TEAL, theme.PAPER, 0.6)),
                      start.center)

    def handle_click(self, pos):
        pass
