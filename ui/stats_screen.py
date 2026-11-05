"""The badges and stats page, opened from the menu with B.

Four lifetime numbers across the top, then one cell per badge: a gold star
and bright text once earned, a dim outline until then (the way to earn it
stays visible, so the page doubles as a goal list).
"""

import math

import pygame

from core.floor_stats import format_duration
from systems.achievements import BADGES
from ui import theme
from ui.backdrop import draw_backdrop
from ui.fonts import ui_font
from ui.kit import blit_centered, draw_chip, draw_panel

PANEL_SIZE = (780, 500)
CELL_SIZE = (360, 64)
STAR_RADIUS = 20


def star_points(centre, radius, inner=0.45):
    """The ten corners of a five-pointed star, point up."""
    cx, cy = centre
    points = []
    for i in range(10):
        angle = -math.pi / 2 + i * math.pi / 5
        r = radius if i % 2 == 0 else radius * inner
        points.append((cx + math.cos(angle) * r, cy + math.sin(angle) * r))
    return points


def stat_values(stats):
    """The four headline numbers as (caption, text) pairs."""
    best_time = format_duration(stats.best_time_left) if stats.best_time_left else "--:--"
    return [("WINS", str(stats.wins)), ("LOSSES", str(stats.losses)),
            ("BEST SCORE", str(stats.best_score)), ("BEST TIME LEFT", best_time)]


class StatsScreen:
    def __init__(self):
        self.title_font = ui_font(52, bold=True)
        self.caption_font = ui_font(20)
        self.value_font = ui_font(36)
        self.name_font = ui_font(26)
        self.desc_font = ui_font(20)
        self.chip_font = ui_font(24)

    def layout(self, width=960):
        panel = pygame.Rect((0, 0), PANEL_SIZE)
        panel.midtop = (width // 2, 100)
        slot_w = (panel.width - 40) // 4
        slots = [pygame.Rect(panel.x + 20 + i * slot_w, panel.y + 24, slot_w, 76) for i in range(4)]
        cells = []
        for i in range(len(BADGES)):
            cell = pygame.Rect((0, 0), CELL_SIZE)
            cell.topleft = (panel.x + 20 + (i % 2) * (CELL_SIZE[0] + 20),
                            panel.y + 130 + (i // 2) * (CELL_SIZE[1] + 14))
            cells.append(cell)
        back = pygame.Rect(0, 0, 220, 38)
        back.midbottom = (panel.centerx, panel.bottom - 16)
        return {"panel": panel, "slots": slots, "cells": cells, "back": back}

    def render(self, surface, stats, tick=0):
        width = surface.get_width()
        lay = self.layout(width)
        draw_backdrop(surface, tick, theme.GOLD)
        blit_centered(surface, self.title_font.render("BADGES & STATS", True, theme.GOLD),
                      (width // 2, 56))
        panel = draw_panel(surface, lay["panel"], fill=theme.mix(theme.INK, theme.NAVY, 0.6),
                           border=theme.GOLD)
        for slot, (caption, text) in zip(lay["slots"], stat_values(stats)):
            blit_centered(surface, self.caption_font.render(caption, True, theme.MIST),
                          (slot.centerx, slot.y + 14))
            blit_centered(surface, self.value_font.render(text, True, theme.SKY),
                          (slot.centerx, slot.y + 48))
        pygame.draw.line(surface, theme.SLATE, (panel.x + 24, panel.y + 112),
                         (panel.right - 24, panel.y + 112), 2)

        for cell, (badge_id, name, how) in zip(lay["cells"], BADGES):
            have = badge_id in stats.badges
            pygame.draw.rect(surface, theme.mix(theme.INK, theme.GOLD, 0.16 if have else 0.0),
                             cell, border_radius=12)
            pygame.draw.rect(surface, theme.GOLD if have else theme.SLATE, cell, width=2,
                             border_radius=12)
            centre = (cell.x + 38, cell.centery)
            points = star_points(centre, STAR_RADIUS)
            if have:
                pygame.draw.polygon(surface, theme.GOLD, points)
            else:
                pygame.draw.polygon(surface, theme.SLATE, points, width=2)
            surface.blit(self.name_font.render(name, True, theme.PAPER if have else theme.MIST),
                         (cell.x + 74, cell.y + 8))
            surface.blit(self.desc_font.render(how, True, theme.MIST),
                         (cell.x + 74, cell.y + 38))
        draw_chip(surface, lay["back"], "ESC: back", self.chip_font, fg=theme.TEAL, border=theme.TEAL)
