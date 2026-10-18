"""Shared helpers for Level 1 and Level 2 (JSON loading, drawing, clicks)."""
import json
import os

import pygame

PUZZLE_FILE = os.path.join(os.path.dirname(__file__), "..", "data", "puzzles.json")

BG = (12, 16, 28)
PANEL = (24, 32, 52)
GREEN = (60, 220, 120)
RED = (230, 80, 80)
YELLOW = (240, 200, 70)
WHITE = (235, 240, 250)
GREY = (120, 130, 150)
BLUE = (70, 120, 220)


def load_level_data(key, default):
    """Return puzzles.json[key], or `default` if the file/key is missing."""
    try:
        with open(PUZZLE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict) and key in data:
            return data[key]
    except (OSError, ValueError):
        pass
    return default


def draw_text(surface, font, text, pos, color=WHITE):
    """Draw one line of text at pos (top-left)."""
    surface.blit(font.render(str(text), True, color), pos)


def draw_button(surface, font, rect, text, hover=False, color=BLUE, disabled=False):
    """Draw a rectangular button with centered text."""
    if disabled:
        fill = (40, 44, 56)
    else:
        fill = tuple(min(255, c + 40) for c in color) if hover else color
    pygame.draw.rect(surface, fill, rect, border_radius=8)
    pygame.draw.rect(surface, WHITE, rect, 2, border_radius=8)
    label = font.render(str(text), True, GREY if disabled else WHITE)
    surface.blit(label, label.get_rect(center=rect.center))


class ClickTracker:
    """Detects a single left-click per press (no repeat while held)."""

    def __init__(self):
        """Start with the mouse button considered released."""
        self._was_down = False

    def clicked(self):
        """Return True only on the frame the left button goes down."""
        down = pygame.mouse.get_pressed()[0]
        result = down and not self._was_down
        self._was_down = down
        return result

def draw_cyber_background(surface, tick=0):
    """Fill with a dark background plus a subtle animated scanline grid."""
    surface.fill(BG)
    w, h = surface.get_size()
    line_color = (24, 40, 60)
    offset = (tick // 3) % 40
    for y in range(-40 + offset, h, 40):
        pygame.draw.line(surface, line_color, (0, y), (w, y), 1)
    for x in range(0, w, 60):
        pygame.draw.line(surface, line_color, (x, 0), (x, h), 1)


def draw_glow_text(surface, font, text, center, color=GREEN, glow_color=(20, 60, 40)):
    """Draw text with a soft drop-shadow glow behind it for a terminal look."""
    glow = font.render(str(text), True, glow_color)
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2)):
        r = glow.get_rect(center=(center[0] + dx, center[1] + dy))
        surface.blit(glow, r)
    main = font.render(str(text), True, color)
    surface.blit(main, main.get_rect(center=center))