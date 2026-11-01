"""
ui/cutscene_fx.py
Owner: Member 1 - Core Game System

Screen effects for the story cards: faint falling data streams, CRT
scanlines with a slow sweep, and a short glitch. Every effect is a plain
function or small class with no hidden randomness (same seed or tick gives
the same picture), so it is easy to test.
"""

import random

import pygame

STREAM_CHARS = "01<>{}[]()=+*#/\\"
CELL = 22                      # pixel height of one character
STREAM_ALPHAS = (70, 48, 30, 14)  # head -> tail; kept faint so text stays readable
STREAM_COLOR = (0, 255, 140)

FLICKER_SECONDS = 0.5          # how long a new card glitches for
GLITCH_PERIOD = 240            # ticks between short glitches on WARDEN cards
GLITCH_LENGTH = 8

_scanline_overlays = {}


class DataStreams:
    """Columns of characters that fall behind the card."""

    def __init__(self, width, height, seed=7):
        self.width = width
        self.height = height
        self.clock = 0.0
        self._font = pygame.font.Font(None, 22)
        self._glyphs = {}
        rng = random.Random(seed)
        self.columns = []
        for i in range(max(1, width // CELL)):
            self.columns.append({
                "x": i * CELL + CELL // 2,
                "speed": rng.uniform(40, 110),
                "length": rng.randint(6, 14),
                "head": rng.uniform(-height, height),
            })

    def heads(self):
        return [c["head"] for c in self.columns]

    def update(self, dt):
        self.clock += dt
        for c in self.columns:
            c["head"] += c["speed"] * dt
            if c["head"] - c["length"] * CELL > self.height:
                c["head"] -= self.height + c["length"] * CELL  # wrap, no randomness

    def _glyph(self, char, level):
        key = (char, level)
        if key not in self._glyphs:
            image = self._font.render(char, True, STREAM_COLOR)
            image.set_alpha(STREAM_ALPHAS[level])
            self._glyphs[key] = image
        return self._glyphs[key]

    def draw(self, surface):
        for index, c in enumerate(self.columns):
            for k in range(c["length"]):
                y = c["head"] - k * CELL
                if y < -CELL or y > self.height:
                    continue
                level = min(len(STREAM_ALPHAS) - 1, int(len(STREAM_ALPHAS) * k / c["length"]))
                char = STREAM_CHARS[(index * 7 + int(y // CELL) * 13 + int(self.clock * 2)) % len(STREAM_CHARS)]
                glyph = self._glyph(char, level)
                surface.blit(glyph, (c["x"] - glyph.get_width() // 2, int(y)))


def draw_scanlines(surface, tick):
    """Darken every third row and sweep a faint light band down the screen."""
    size = surface.get_size()
    overlay = _scanline_overlays.get(size)
    if overlay is None:
        overlay = pygame.Surface(size, pygame.SRCALPHA)
        for y in range(0, size[1], 3):
            pygame.draw.line(overlay, (0, 0, 0, 38), (0, y), (size[0], y))
        _scanline_overlays[size] = overlay
    surface.blit(overlay, (0, 0))

    band_height = 36
    band = pygame.Surface((size[0], band_height), pygame.SRCALPHA)
    band.fill((140, 200, 255, 14))
    y = (tick * 3) % (size[1] + band_height) - band_height
    surface.blit(band, (0, y))


def draw_glitch(surface, tick, intensity):
    """Shift a few horizontal slices sideways; intensity 0..1, 0 does nothing."""
    if intensity <= 0:
        return
    intensity = min(1.0, intensity)
    rng = random.Random(tick)
    width, height = surface.get_size()
    source = surface.copy()
    for _ in range(1 + int(6 * intensity)):
        slice_height = rng.randint(6, 30)
        y = rng.randint(0, max(0, height - slice_height))
        shift = int(rng.randint(-40, 40) * intensity) or 3
        surface.blit(source, (shift, y), pygame.Rect(0, y, width, slice_height))


def open_flicker(age):
    """1.0 when a card has just opened, fading to 0 after FLICKER_SECONDS."""
    return max(0.0, min(1.0, 1.0 - age / FLICKER_SECONDS))


def periodic_glitch(tick):
    """A short glitch every GLITCH_PERIOD ticks (never on the very first tick)."""
    return 0.5 if tick % GLITCH_PERIOD >= GLITCH_PERIOD - GLITCH_LENGTH else 0.0
