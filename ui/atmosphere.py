"""
ui/atmosphere.py
Owner: Member 1 - Core Game System

"NovaCorp Lockdown": one colour grade over every screen so the six levels,
the menu and the story cards look like one place.

  * depth  0..1  how far into the building the player is. A cold navy at
                 the entrance, warmer light deeper in.
  * alert  0..1  how close WARDEN is. A red glow pulses in from the screen
                 edges; it follows the security meter, so mistakes show.

Built from cached overlays (one multiply layer that carries the tint and the
vignette, and a red edge glow), so it costs only a few milliseconds a frame.
Levels never know it exists.
"""

import math

import pygame

from core.level_manager import LEVEL_ORDER

VIGNETTE = 0.38        # darkest the corners get
GLOW = 0.80            # strongest the red edge glow gets
DEPTH_ALERT = 0.25     # alert the deepest level carries with no mistakes
_EDGE_START = 0.55     # distance from the centre where the edge effects begin
_EDGE_SPAN = 0.86
_CALM_STATES = ("menu", "intro", "outro", "win")


def _clamp(value, low=0.0, high=1.0):
    return max(low, min(high, value))


def mood_for(state, level_name, security_level, security_max):
    """Return (depth, alert) for a screen.

    Menu, intro, the ending and the win screen are calm: the building is
    quiet again. Losing is full lockdown at the depth reached.
    """
    if state in _CALM_STATES or state not in ("playing", "briefing", "lose"):
        return 0.0, 0.0

    if level_name in LEVEL_ORDER and len(LEVEL_ORDER) > 1:
        depth = LEVEL_ORDER.index(level_name) / (len(LEVEL_ORDER) - 1)
    else:
        depth = 0.0

    if state == "lose":
        return depth, 1.0

    ratio = security_level / security_max if security_max > 0 else 0.0
    return depth, _clamp(max(DEPTH_ALERT * depth, ratio))


class Atmosphere:
    def __init__(self, size):
        self._build(size)

    def _build(self, size):
        self.size = size
        self._shades = {}
        # Compute the edge falloff on a small grid, then stretch it smoothly.
        grid_w, grid_h = 48, 32
        vignette = pygame.Surface((grid_w, grid_h))
        glow = pygame.Surface((grid_w, grid_h), pygame.SRCALPHA)
        for y in range(grid_h):
            for x in range(grid_w):
                dx = (x + 0.5 - grid_w / 2) / (grid_w / 2)
                dy = (y + 0.5 - grid_h / 2) / (grid_h / 2)
                edge = _clamp((math.hypot(dx, dy) - _EDGE_START) / _EDGE_SPAN)
                shade = int(255 * (1 - VIGNETTE * edge))
                vignette.set_at((x, y), (shade, shade, shade))
                glow.set_at((x, y), (255, 30, 40, int(255 * GLOW * edge ** 1.2)))
        self._vignette = pygame.transform.smoothscale(vignette, size).convert()
        self._glow = pygame.transform.smoothscale(glow, size)

    def _shade(self, depth):
        """Tint and vignette in one multiply layer, cached per tenth of depth."""
        step = round(depth * 10)
        if step not in self._shades:
            d = step / 10
            tint = (
                int(255 * (0.90 + 0.10 * d)),
                int(255 * (0.97 - 0.10 * d)),
                int(255 * (1.00 - 0.16 * d)),
            )
            layer = self._vignette.copy()
            layer.fill(tint, special_flags=pygame.BLEND_RGB_MULT)
            self._shades[step] = layer
        return self._shades[step]

    def apply(self, surface, depth, alert, tick=0):
        """Grade `surface` in place."""
        if surface.get_size() != self.size:
            self._build(surface.get_size())
        depth = _clamp(depth)
        alert = _clamp(alert)

        surface.blit(self._shade(depth), (0, 0), special_flags=pygame.BLEND_RGB_MULT)

        pulse = 0.65 + 0.35 * math.sin(tick * 0.12)
        strength = int(255 * alert * pulse)
        if strength > 0:
            self._glow.set_alpha(strength)
            surface.blit(self._glow, (0, 0))
