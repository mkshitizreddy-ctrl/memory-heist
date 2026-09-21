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
