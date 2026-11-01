"""Shared animated backdrop for the menu, win and lose screens.

A soft vertical gradient in the screen's tint colour, slowly drifting motes
of light, and a dark vignette.  The gradient and vignette are built once per
size and tint; only the motes are drawn each frame.
"""

import math

import pygame

from ui import theme

MOTE_COUNT = 46
_gradients = {}
_vignettes = {}


def gradient(size, tint):
    """Cached top-to-bottom gradient from near-black to a tinted navy."""
    key = (size, tint)
    surf = _gradients.get(key)
    if surf is None:
        w, h = size
        surf = pygame.Surface(size)
        top = theme.mix(theme.INK, tint, 0.08)
        bottom = theme.mix(theme.NAVY, tint, 0.28)
        for y in range(h):
            pygame.draw.line(surf, theme.mix(top, bottom, y / max(1, h - 1)), (0, y), (w, y))
        _gradients[key] = surf
    return surf


def vignette(size):
    """Cached dark edges (alpha), built small and smooth-scaled up."""
    surf = _vignettes.get(size)
    if surf is None:
        sw, sh = 32, 20
        small = pygame.Surface((sw, sh), pygame.SRCALPHA)
        for y in range(sh):
            for x in range(sw):
                dx = (x + 0.5) / sw * 2 - 1
                dy = (y + 0.5) / sh * 2 - 1
                d = min(1.0, math.hypot(dx, dy) / 1.25)
                small.set_at((x, y), (0, 0, 0, int(150 * d ** 2.5)))
        surf = pygame.transform.smoothscale(small, size)
        _vignettes[size] = surf
    return surf


def mote_positions(tick, count, size):
    """Deterministic drifting motes as (x, y, radius, twinkle 0..1)."""
    w, h = size
    out = []
    for i in range(count):
        # simple integer hash so the layout is stable but looks scattered
        a = (i * 7919 + 13) % 1009 / 1009
        b = (i * 104729 + 29) % 1013 / 1013
        c = (i * 15485863 + 7) % 1019 / 1019
        speed = 0.15 + 0.35 * c
        x = (a * w + math.sin(tick * 0.012 * (0.5 + c) + i) * 14) % w
        y = (b * h - tick * speed) % h
        radius = 1 + (i % 3 == 0)
        twinkle = 0.5 + 0.5 * math.sin(tick * 0.05 + i * 1.7)
        out.append((x, y, radius, twinkle))
    return out


def draw_backdrop(surface, tick, tint=theme.SKY, count=MOTE_COUNT):
    size = surface.get_size()
    surface.blit(gradient(size, tint), (0, 0))
    glow = theme.mix(tint, theme.PAPER, 0.4)
    for x, y, radius, twinkle in mote_positions(tick, count, size):
        pygame.draw.circle(surface, theme.mix(theme.NAVY, glow, 0.25 + 0.6 * twinkle),
                           (int(x), int(y)), radius)
    surface.blit(vignette(size), (0, 0))
