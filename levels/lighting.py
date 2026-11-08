"""
levels/lighting.py

2D lighting for every floor: a dim ambient light map, soft coloured light
pools, a cheap bloom on the brightest pixels, and blob shadows under things
that stand on the floor.

How a frame is lit
------------------
1. `LightLayer.lightmap` starts as the ambient colour (a dim blue-grey).
2. Each `Light` adds a cached radial glow to it (additive).
3. The world is multiplied by the light map: lit areas keep their colour,
   unlit areas fall into shadow. This is what makes lamps, the camera beam
   and the vending machine read as real light sources.
4. A soft additive tint per light gives each pool its colour.
5. Bloom: the brightest pixels are blurred at quarter resolution and added
   back, so lamps and LEDs glow.

The player is drawn after the level by the game, so it stays unlit and
reads clearly as the focus of the screen.
"""

from dataclasses import dataclass

import numpy as np
import pygame

AMBIENT = (140, 148, 172)       # light-map base: ~57% brightness, cool tint
TINT_STRENGTH = 0.35            # how much of a light's colour is added on top
BLOOM_THRESHOLD = 170           # brightness (0-255) above which pixels bloom
BLOOM_STRENGTH = 0.55
BLOOM_SCALE = 4                 # bloom is computed at 1/BLOOM_SCALE size


@dataclass(frozen=True)
class Light:
    """A circular light: centre (x, y), radius in px, RGB colour, intensity 0-1+."""
    centre: tuple
    radius: int
    colour: tuple = (255, 244, 220)
    intensity: float = 1.0


_GLOW_CACHE = {}


def glow(radius):
    """A square float mask [2r, 2r] with smooth falloff, 1.0 at the centre, 0.0 at the edge."""
    cached = _GLOW_CACHE.get(radius)
    if cached is None:
        ys, xs = np.mgrid[-radius:radius, -radius:radius].astype(np.float32) + 0.5
        d = np.sqrt(xs ** 2 + ys ** 2) / radius
        cached = np.clip(1.0 - d, 0.0, 1.0) ** 2                      # Shape: [2r, 2r]
        _GLOW_CACHE[radius] = cached
    return cached


def _glow_surface(radius, colour, intensity):
    """The glow mask as an RGB surface (colour * mask * intensity), for additive blits."""
    mask = glow(radius) * intensity                                    # Shape: [2r, 2r]
    rgb = np.clip(mask[..., None] * np.array(colour, dtype=np.float32), 0, 255)
    surf = pygame.Surface((radius * 2, radius * 2))
    pygame.surfarray.blit_array(surf, rgb.astype(np.uint8).swapaxes(0, 1))
    return surf


class LightLayer:
    """Applies lighting to a finished world surface."""

    def __init__(self, ambient=AMBIENT, bloom=True):
        self.ambient = ambient
        self.bloom = bloom
        self._surfaces = {}
        self._lightmap = None

    def _surface(self, radius, colour, intensity):
        key = (radius, tuple(colour), round(intensity, 2))
        surf = self._surfaces.get(key)
        if surf is None:
            if len(self._surfaces) > 160:                              # dynamic radii: cap the cache
                self._surfaces.clear()
            surf = self._surfaces[key] = _glow_surface(radius, colour, intensity)
        return surf

    def lightmap(self, size, lights):
        """Ambient plus every light, as an RGB surface the size of the world."""
        if self._lightmap is None or self._lightmap.get_size() != size:
            self._lightmap = pygame.Surface(size)
        lm = self._lightmap
        lm.fill(self.ambient)
        for light in lights:
            # white-ish contribution brightens; clamp so one light never exceeds full
            s = self._surface(light.radius, (255, 255, 255), light.intensity * 1.0)
            lm.blit(s, (light.centre[0] - light.radius, light.centre[1] - light.radius),
                    special_flags=pygame.BLEND_RGB_ADD)
        return lm

    def apply(self, world, lights):
        lights = list(lights)
        lm = self.lightmap(world.get_size(), lights)
        world.blit(lm, (0, 0), special_flags=pygame.BLEND_RGB_MULT)
        for light in lights:
            tint = self._surface(light.radius, light.colour, light.intensity * TINT_STRENGTH * 0.5)
            world.blit(tint, (light.centre[0] - light.radius, light.centre[1] - light.radius),
                       special_flags=pygame.BLEND_RGB_ADD)
        if self.bloom:
            self._bloom(world)
        return world

    @staticmethod
    def _bloom(world):
        w, h = world.get_size()
        small = pygame.transform.smoothscale(world, (max(1, w // BLOOM_SCALE), max(1, h // BLOOM_SCALE)))
        arr = pygame.surfarray.array3d(small).astype(np.float32)       # Shape: [w/4, h/4, 3]
        lum = arr @ np.array([0.299, 0.587, 0.114], dtype=np.float32)  # Shape: [w/4, h/4]
        arr *= (lum > BLOOM_THRESHOLD)[..., None]
        bright = pygame.Surface(small.get_size())
        pygame.surfarray.blit_array(bright, arr.astype(np.uint8))
        for divisor in (8, 16):                                        # two blur radii: tight core + wide halo
            soft = pygame.transform.smoothscale(bright, (max(1, w // divisor), max(1, h // divisor)))
            soft = pygame.transform.smoothscale(soft, (w, h))
            soft.fill((int(255 * BLOOM_STRENGTH),) * 3, special_flags=pygame.BLEND_RGB_MULT)
            world.blit(soft, (0, 0), special_flags=pygame.BLEND_RGB_ADD)


_SHADOWS = {}


def blob_shadow(surface, rect, alpha=80, squash=0.38):
    """A soft elliptical shadow on the floor under `rect` (feet of a thing)."""
    rect = pygame.Rect(rect)
    w = max(6, rect.w + 6)
    h = max(4, int(w * squash))
    key = (w, h, alpha)
    shadow = _SHADOWS.get(key)
    if shadow is None:
        shadow = pygame.Surface((w, h), pygame.SRCALPHA)
        for i in range(4):                                              # stacked ellipses = soft edge
            inset = i * max(1, w // 14)
            a = int(alpha * (i + 1) / 4)
            pygame.draw.ellipse(shadow, (0, 0, 0, a // 2 + 4),
                                (inset, inset // 2, w - 2 * inset, max(2, h - inset)))
        _SHADOWS[key] = shadow
    surface.blit(shadow, (rect.centerx - w // 2, rect.bottom - h // 2 - 1))
