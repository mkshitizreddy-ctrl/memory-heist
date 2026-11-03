"""
core/display.py
Owner: Member 1 - Core Game System

Window setup helpers that must run before pygame opens its window.
"""

import sys


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
