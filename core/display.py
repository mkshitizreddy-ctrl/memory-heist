"""
core/display.py
Owner: Member 1 - Core Game System

Window setup helpers that must run before pygame opens its window.
"""

import os
import sys

import pygame

HEADLESS_DRIVERS = ('dummy', 'offscreen')
WINDOWED_ENV = 'MEMORY_HEIST_WINDOWED'   # set to 1 to force a window (development, screenshots)


def configure_scaling():
    """Ask SDL to smooth the picture when it is scaled up to the screen.

    The game draws at 960x640. Full-screen on a laptop or monitor is rarely a
    whole multiple of that, and without smoothing the pixels come out in
    uneven widths and shimmer as things move. Must run before the window opens.
    """
    os.environ.setdefault("SDL_RENDER_SCALE_QUALITY", "1")


def window_flags(fullscreen, driver=None):
    """pygame flags for the game window.

    SCALED keeps the drawing surface at 960x640 and maps mouse positions back.
    FULLSCREEN is added when wanted, except for headless drivers (tests) and
    when MEMORY_HEIST_WINDOWED is set.
    """
    flags = pygame.SCALED
    if fullscreen and driver not in HEADLESS_DRIVERS and not os.environ.get(WINDOWED_ENV):
        flags |= pygame.FULLSCREEN
    return flags


def is_fullscreen():
    """True when the open window is full-screen."""
    surface = pygame.display.get_surface()
    return bool(surface is not None and surface.get_flags() & pygame.FULLSCREEN)


def enable_dpi_awareness():
    """Stop Windows from stretching the window when display scaling is on.

    With 125% or 150% scaling, a program that does not say it understands
    scaling gets its picture enlarged by Windows, which makes all text
    blurry. Declaring DPI awareness turns that off. Does nothing on other
    systems, and never raises: returns True only if Windows accepted it.
    """
    if sys.platform != "win32":
        return False
    try:
        import ctypes

        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)  # Windows 8.1+
        except (AttributeError, OSError):
            ctypes.windll.user32.SetProcessDPIAware()  # older Windows
        return True
    except Exception:
        return False
