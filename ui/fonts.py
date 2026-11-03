"""
ui/fonts.py
Owner: Member 1 - Core Game System

One place to get a font. pygame's built-in font is thin and looks fuzzy at
the 16-24 px sizes the HUD uses, so the game ships Chakra Petch (assets/fonts), an angular techno face that
fits the NovaCorp setting, and
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
REGULAR = "ChakraPetch-SemiBold.ttf"
BOLD = "ChakraPetch-Bold.ttf"
MONO = "ShareTechMono-Regular.ttf"

# Chakra Petch needs about 0.71 of the default font's size number to take
# the same width.
SIZE_FACTOR = 0.71
MIN_PIXELS = 9
# Share Tech Mono is narrower per size number; this keeps tags the same height.
MONO_FACTOR = 0.8

_cache = {}


def pixel_size(size):
    """Pixel size to ask the font for, given a legacy Font(None, size) number."""
    return max(MIN_PIXELS, round(size * SIZE_FACTOR))


def ui_font(size, bold=False):
    """A cached font; the same (size, bold) always returns the same object."""
    key = (size, bool(bold))
    font = _cache.get(key)
    if font is None:
        font = _load(size, bool(bold))
        _cache[key] = font
    return font


def code_font(size):
    """Monospace font for Python values and type names (0.5, "agent", int).

    Chakra Petch squeezes a decimal point until 0.5 reads as "O5", which is
    the wrong thing to teach, so anything that shows code uses this instead.
    """
    key = (size, "mono")
    font = _cache.get(key)
    if font is None:
        try:
            font = pygame.font.Font(str(FONT_DIR / MONO), max(MIN_PIXELS, round(size * MONO_FACTOR)))
        except (OSError, pygame.error):
            font = pygame.font.Font(None, size)
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
