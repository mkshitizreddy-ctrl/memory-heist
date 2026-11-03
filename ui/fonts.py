"""
ui/fonts.py
Owner: Member 1 - Core Game System

One place to get a font. pygame's built-in font is thin and looks fuzzy at
the 16-24 px sizes the HUD uses, so the game ships Lato (assets/fonts) and
everything asks for it here.

    from ui.fonts import ui_font
    self.font = ui_font(26)              # same size number as Font(None, 26)
    self.title = ui_font(64, bold=True)

The size number means what it did for pygame.font.Font(None, size), so
switching a line over does not move the layout. Falls back to the built-in
font if the file is missing, so the game never fails to start over a font.
"""

from pathlib import Path

import pygame

FONT_DIR = Path(__file__).resolve().parent.parent / "assets" / "fonts"
REGULAR = "Lato-Semibold.ttf"
BOLD = "Lato-Bold.ttf"

# Lato needs about 3/4 of the default font's size number to take the same width.
SIZE_FACTOR = 0.76
MIN_PIXELS = 9

_cache = {}


def pixel_size(size):
    """Pixel size to ask Lato for, given a legacy Font(None, size) number."""
    return max(MIN_PIXELS, round(size * SIZE_FACTOR))


def ui_font(size, bold=False):
    """A cached font; the same (size, bold) always returns the same object."""
    key = (size, bool(bold))
    font = _cache.get(key)
    if font is None:
        font = _load(size, bool(bold))
        _cache[key] = font
    return font


def _load(size, bold):
    path = FONT_DIR / (BOLD if bold else REGULAR)
    try:
        return pygame.font.Font(str(path), pixel_size(size))
    except (OSError, pygame.error):
        return pygame.font.Font(None, size)


def clear_cache():
    """Forget every font.

    Runs automatically on pygame.quit(): a Font made before a quit is dead
    afterwards, and using one crashes the interpreter instead of raising.
    """
    _cache.clear()


pygame.register_quit(clear_cache)
