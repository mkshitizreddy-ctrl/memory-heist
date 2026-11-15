"""
ui/sidebars.py
Owner: Member 1 - Core Game System

The game is drawn at 960x640 (3:2). On a 16:9 screen that leaves two empty strips,
which SDL used to fill with black. The window is now 16:9 (1136x640, see
core/display.py) and these strips are part of the building instead: dark NovaCorp
wall panels in the current floor's colour, the floor's name running down the left
one, a watching eye and a column of status lights down the right one.

Static parts are baked once per floor; only the lights and the eye move.
"""

import math

import pygame

from core.display import GAME_SIZE, SIDE_WIDTH
from ui import theme
from ui.fonts import ui_font

_cache = {}


def _floor_key(state, level_name):
    return level_name if state == "playing" and level_name else "menu"


def _panel(height, accent, name, left):
    """One baked strip: wall panels, seams, rivets, a lit edge toward the game, a stencilled name."""
    surf = pygame.Surface((SIDE_WIDTH, height))
    base = theme.mix(theme.INK, accent, 0.08)
    surf.fill(base)
    seam = theme.mix(base, (0, 0, 0), 0.45)
    for y in range(0, height, 80):                                    # wall panels
        pygame.draw.line(surf, seam, (0, y), (SIDE_WIDTH, y), 2)
        for x in (10, SIDE_WIDTH - 12):
            pygame.draw.circle(surf, theme.mix(base, theme.PAPER, 0.18), (x, y + 10), 2)
    edge_x = SIDE_WIDTH - 3 if left else 0                            # the lit trim beside the game
    pygame.draw.rect(surf, theme.mix(accent, theme.INK, 0.45), (edge_x, 0, 3, height))
    shade = pygame.Surface((24, height), pygame.SRCALPHA)
    for i in range(24):
        pygame.draw.line(shade, (0, 0, 0, 120 - i * 5), (i, 0), (i, height))
    surf.blit(pygame.transform.flip(shade, left, False), (SIDE_WIDTH - 24, 0) if left else (0, 0))   # shadow away from the game
    if left and name:                                                 # the floor's name, stencilled down the wall
        label = ui_font(20, bold=True).render(name.upper(), True, theme.mix(accent, theme.INK, 0.35))
        label = pygame.transform.rotate(label, 90)
        label.set_alpha(150)
        surf.blit(label, label.get_rect(center=(SIDE_WIDTH // 2, height // 2)))
    return surf


def _baked(key, height):
    if (key, height) not in _cache:
        pal = theme.floor_palette(key if key != "menu" else "level1")
        accent = pal["accent"] if key != "menu" else theme.CORAL
        name = pal.get("name", "") if key != "menu" else "NovaCorp"
        _cache[(key, height)] = (_panel(height, accent, name, True), _panel(height, accent, "", False), accent)
    return _cache[(key, height)]


def draw_sidebars(window, state, level_name, t):
    """Fill the strips either side of the game. Does nothing if the window has no strips."""
    width, height = window.get_size()
    if width <= GAME_SIZE[0]:                                         # no strips: never paint over the game
        return
    left, right, accent = _baked(_floor_key(state, level_name), height)
    window.blit(left, (0, 0))
    x0 = width - SIDE_WIDTH
    window.blit(right, (x0, 0))
    eye = (x0 + SIDE_WIDTH // 2, 70)                                  # WARDEN's eye watches from the right wall
    look = int(5 * math.sin(t * 0.6))
    pygame.draw.ellipse(window, (30, 10, 14), (eye[0] - 20, eye[1] - 10, 40, 20))
    pygame.draw.ellipse(window, theme.mix(theme.CORAL, theme.INK, 0.3), (eye[0] - 20, eye[1] - 10, 40, 20), 2)
    pygame.draw.circle(window, theme.CORAL, (eye[0] + look, eye[1]), 5)
    for i in range(12):                                               # a column of status lights
        y = 130 + i * 38
        on = math.sin(t * (0.8 + 0.13 * i) + i * 1.7) > 0.35
        colour = theme.mix(accent, theme.PAPER, 0.2) if on else theme.mix(theme.INK, accent, 0.18)
        pygame.draw.rect(window, colour, (x0 + SIDE_WIDTH // 2 - 9, y, 18, 5), border_radius=2)
