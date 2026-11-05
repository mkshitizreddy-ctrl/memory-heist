"""Shared animated backdrop for the menu, win and lose screens.

A soft vertical gradient in the screen's tint colour, two slow searchlight
beams sweeping the sky, a NovaCorp skyline along the bottom with windows that
switch on and off, drifting motes of light, and a dark vignette.  The gradient,
skyline, beams and vignette are built once per size and tint; each frame only
blits them, draws the lit windows and the motes.
"""

import math

import pygame

from ui import theme

MOTE_COUNT = 46
BEAM_SWING = 26                  # degrees either side of straight up
BEAM_STEP = 2                    # beam frames are cached every 2 degrees
BEAM_SIZE = (150, 520)
BEAM_SOURCES = (0.16, 0.84)      # as a share of the screen width
BEAM_ALPHA = 20
_gradients = {}
_vignettes = {}
_skylines = {}
_beams = {}


def tower_layout(width, seed=11):
    """Deterministic (x, width, height) towers across `width`, with a tall NovaCorp spire mid-screen."""
    towers = []
    x = 0
    i = 0
    while x < width:
        w = 26 + (i * 37 + seed) % 31
        h = 38 + (i * 53 + seed * 3) % 70
        towers.append((x, w, h))
        x += w + (i + seed) % 4
        i += 1
    spire = min(range(len(towers)), key=lambda k: abs(towers[k][0] + towers[k][1] // 2 - width // 2))
    x, w, _ = towers[spire]
    towers[spire] = (x, w, 168)
    return towers


def window_slots(towers):
    """Every possible window as (x, y_from_bottom, phase), on a grid inside each tower."""
    slots = []
    for t, (x, w, h) in enumerate(towers):
        for cx in range(x + 6, x + w - 6, 8):
            for cy in range(14, h - 8, 12):
                slots.append((cx, cy, ((cx * 31 + cy * 17 + t * 7) % 628) / 100))
    return slots


def window_level(tick, phase):
    """0 for a dark window, up to 1 for a lit one; lights come and go slowly."""
    wave = math.sin(tick * 0.012 + phase * 3.1)
    return 0.0 if wave < 0.35 else min(1.0, (wave - 0.35) / 0.3)


def skyline(size, tint):
    """Cached (silhouette surface, window slots) for the bottom of the screen."""
    key = (size, tint)
    cached = _skylines.get(key)
    if cached is None:
        w, h = size
        towers = tower_layout(w)
        surf = pygame.Surface(size, pygame.SRCALPHA)
        colour = theme.mix(theme.mix(theme.NAVY, tint, 0.28), (0, 0, 0), 0.4)     # the sky's own tint, darker
        for x, tw, th in towers:
            pygame.draw.rect(surf, colour, (x, h - th, tw, th))
        x, tw, th = max(towers, key=lambda t: t[2])
        pygame.draw.rect(surf, colour, (x + tw // 2 - 1, h - th - 22, 3, 22))     # antenna
        slots = [(sx, h - sy, phase) for sx, sy, phase in window_slots(towers)]
        cached = _skylines[key] = (surf, slots)
    return cached


def beam_angle(tick, phase=0.0):
    """Whole-degree beam tilt, a slow sweep, snapped to the cached steps."""
    raw = BEAM_SWING * math.sin(tick * 0.011 + phase)
    return int(round(raw / BEAM_STEP)) * BEAM_STEP


def beam_centre(source, height, angle):
    """Where the middle of a beam sits so its foot stays on `source`, whatever its tilt."""
    rad = math.radians(angle)
    sx, sy = source
    return (sx - (height / 2) * math.sin(rad), sy - (height / 2) * math.cos(rad))


def beam(angle, tint):
    """Cached, rotated searchlight cone: narrow at its foot (bottom), wide and faint above."""
    key = (angle, tint)
    surf = _beams.get(key)
    if surf is None:
        w, h = BEAM_SIZE
        cone = pygame.Surface(BEAM_SIZE, pygame.SRCALPHA)
        colour = theme.mix(tint, theme.PAPER, 0.55)
        pygame.draw.polygon(cone, (*colour, BEAM_ALPHA),
                            [(w // 2 - 5, h), (w // 2 + 5, h), (w, 0), (0, 0)])
        pygame.draw.polygon(cone, (*colour, BEAM_ALPHA),
                            [(w // 2 - 3, h), (w // 2 + 3, h), (w * 3 // 4, 0), (w // 4, 0)])
        surf = _beams[key] = pygame.transform.rotate(cone, angle)
    return surf


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


def draw_scenery(surface, tick, tint):
    """Searchlights behind, then the skyline with its lit windows."""
    width, height = surface.get_size()
    for n, share in enumerate(BEAM_SOURCES):
        angle = beam_angle(tick, phase=n * 2.4)
        image = beam(angle, tint)
        centre = beam_centre((int(width * share), height - 70), BEAM_SIZE[1], angle)
        surface.blit(image, image.get_rect(center=(round(centre[0]), round(centre[1]))))
    silhouette, slots = skyline(surface.get_size(), tint)
    surface.blit(silhouette, (0, 0))
    lit = theme.mix(theme.GOLD, tint, 0.25)
    dark = theme.mix(theme.INK, tint, 0.12)
    for x, y, phase in slots:
        level = window_level(tick, phase)
        if level > 0:
            pygame.draw.rect(surface, theme.mix(dark, lit, 0.55 * level), (x, y, 3, 4))


def draw_backdrop(surface, tick, tint=theme.SKY, count=MOTE_COUNT, scenery=True):
    size = surface.get_size()
    surface.blit(gradient(size, tint), (0, 0))
    if scenery:
        draw_scenery(surface, tick, tint)
    glow = theme.mix(tint, theme.PAPER, 0.4)
    for x, y, radius, twinkle in mote_positions(tick, count, size):
        pygame.draw.circle(surface, theme.mix(theme.NAVY, glow, 0.25 + 0.6 * twinkle),
                           (int(x), int(y)), radius)
    surface.blit(vignette(size), (0, 0))
