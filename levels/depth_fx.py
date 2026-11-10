"""
levels/depth_fx.py
Owner: Member 5 (UI)

Small, stateless effects that give the flat pixel rooms some depth and life.  Every
function draws from the clock `t` alone (no particle lists to keep), so a level only
has to call it each frame, and none of them touches gameplay.

    light_bars   slanted bars of light drifting across the floor, like a lamp through blinds
    steam        a periodic hiss of steam rising from a vent
    sparks       a loose cable throwing a few sparks every so often
    motes        dust turning slowly in the light
"""

import math

import pygame


def _hash(n):
    """A cheap repeatable 0..1 value from an integer: stable 'randomness' with no RNG state."""
    x = math.sin(n * 12.9898 + 78.233) * 43758.5453
    return x - math.floor(x)


def light_bars(surface, region, t, colour=(255, 236, 190), alpha=16, width=30, gap=64, speed=6.0):
    """Soft slanted bars of light across `region`; added to the picture, so dark floors stay dark."""
    region = pygame.Rect(region)
    layer = pygame.Surface(region.size, pygame.SRCALPHA)
    slant = region.height * 0.55
    offset = (t * speed) % (width + gap)
    x = -slant - offset
    while x < region.width + slant:
        points = [(x, 0), (x + width, 0), (x + width - slant, region.height), (x - slant, region.height)]
        pygame.draw.polygon(layer, (*colour, alpha), points)
        x += width + gap
    previous = surface.get_clip()
    surface.set_clip(region)
    surface.blit(layer, region.topleft)
    surface.set_clip(previous)


def steam(surface, origin, t, period=7.0, seed=0.0, puffs=7, rise=48, burst=2.4):
    """A vent that hisses for `burst` seconds every `period`: grey puffs rise, swell and fade."""
    phase = (t + seed * period) % period
    if phase > burst + 1.6:
        return
    size = 64
    layer = pygame.Surface((size, size * 2), pygame.SRCALPHA)
    ox, oy = origin
    drawn = False
    for k in range(puffs):
        age = phase - k * (burst / puffs)
        if age < 0 or age > 1.6:
            continue
        u = age / 1.6
        x = size // 2 + math.sin(k * 2.3 + seed * 7) * 7 * u + u * 5
        y = size * 2 - 6 - rise * u
        radius = 3 + 9 * u
        fade = (1 - u) * min(1.0, age * 5)
        pygame.draw.circle(layer, (200, 206, 214, int(78 * fade)), (int(x), int(y)), int(radius))
        drawn = True
    if drawn:
        surface.blit(layer, (ox - size // 2, oy - size * 2 + 6))


def sparks(surface, origin, t, period=8.0, seed=0.0, count=7):
    """A short shower of sparks arcing down from `origin` once per period."""
    phase = (t + seed * period) % period
    if phase > 0.7:
        return
    ox, oy = origin
    for k in range(count):
        angle = math.pi * (0.15 + 0.7 * _hash(k + seed * 31))
        speed = 40 + 60 * _hash(k * 3 + seed * 17)
        x = ox + math.cos(angle) * speed * phase * (1 if k % 2 else -1)
        y = oy + math.sin(angle) * speed * phase * 0.4 + 180 * phase * phase
        life = 1 - phase / 0.7
        colour = (255, int(190 + 50 * life), int(90 + 80 * life))
        pygame.draw.rect(surface, colour, (int(x), int(y), 2, 2))


def motes(surface, region, t, count=26, colour=(210, 214, 200), seed=0.0):
    """Dust turning slowly in the room: a few pixels that drift and twinkle."""
    region = pygame.Rect(region)
    for i in range(count):
        a, b, c = _hash(i + seed), _hash(i * 7 + seed + 3), _hash(i * 13 + seed + 5)
        x = region.x + (a * region.width + t * (3 + 5 * c) * (1 if b > 0.5 else -1)) % region.width
        y = region.y + (b * region.height + math.sin(t * 0.6 + i) * 10 + t * 2 * c) % region.height
        twinkle = 0.35 + 0.65 * (0.5 + 0.5 * math.sin(t * 1.4 + i * 1.7))
        tone = tuple(int(v * twinkle) for v in colour)
        surface.set_at((int(x), int(y)), tone) if region.collidepoint(x, y) else None
