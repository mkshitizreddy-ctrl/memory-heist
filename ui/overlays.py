"""Pause overlay: dimmed game, a stats panel and the way back in.

Everything that costs time (dim layer, fonts) is built once in __init__, so a
paused frame only blits and renders a few short strings.
"""

import pygame

from ui import theme
from ui.hud import LEVEL_LABELS, format_time
from ui.kit import blit_centered, draw_chip, draw_panel

PANEL_SIZE = (440, 270)


class PauseOverlay:
    def __init__(self, size):
        self.size = size
        self.dim = pygame.Surface(size, pygame.SRCALPHA)
        self.dim.fill((4, 6, 14, 170))
        self.title_font = pygame.font.Font(None, 64)
        self.label_font = pygame.font.Font(None, 20)
        self.value_font = pygame.font.Font(None, 34)
        self.chip_font = pygame.font.Font(None, 26)
        self.panel = pygame.Rect((0, 0), PANEL_SIZE)
        self.panel.center = (size[0] // 2, size[1] // 2)

    def stat_slots(self):
        """Three equal columns inside the panel: Score, Security, Time."""
        slot_w = (self.panel.width - 40) // 3
        return [pygame.Rect(self.panel.x + 20 + i * slot_w, self.panel.y + 100, slot_w, 70)
                for i in range(3)]

    def resume_chip(self):
        chip = pygame.Rect(0, 0, 300, 44)
        chip.midbottom = (self.panel.centerx, self.panel.bottom - 24)
        return chip

    def draw(self, surface, level_name="", score=0, security=0, security_max=100,
             remaining=None, tick=0):
        surface.blit(self.dim, (0, 0))
        accent = theme.floor_palette(level_name)["accent"]
        panel = draw_panel(surface, self.panel,
                           fill=theme.mix(theme.INK, theme.NAVY, 0.7), border=accent)
        blit_centered(surface, self.title_font.render("PAUSED", True, theme.PAPER),
                      (panel.centerx, panel.y + 40))
        blit_centered(surface, self.label_font.render(
            LEVEL_LABELS.get(level_name, level_name).upper(), True, accent),
            (panel.centerx, panel.y + 76))

        stats = [("SCORE", str(score), theme.SKY),
                 ("SECURITY", f"{security}/{security_max}",
                  theme.CORAL if security >= 0.8 * max(1, security_max) else theme.TEAL),
                 ("TIME", format_time(remaining) if remaining is not None else "--:--",
                  theme.GOLD)]
        for slot, (caption, value, colour) in zip(self.stat_slots(), stats):
            blit_centered(surface, self.label_font.render(caption, True, theme.MIST),
                          (slot.centerx, slot.y + 10))
            blit_centered(surface, self.value_font.render(value, True, colour),
                          (slot.centerx, slot.y + 42))

        pulse = 0.5 + 0.5 * abs((tick % 60) - 30) / 30
        draw_chip(surface, self.resume_chip(), "ESC: resume", self.chip_font,
                  fg=theme.mix(theme.TEAL, theme.PAPER, 0.5 * pulse), border=theme.TEAL)
