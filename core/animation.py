"""
core/animation.py
Owner: Member 1 - Core Game System

Shared animation kit so every floor moves the same way:

  * SpriteSheet / Animation  - frame-based sprite animation
  * SquashStretch            - springy scale pulse (jump, land, pick-up, hit)
  * hit_flash                - white flash on a sprite copy
  * Shake                    - trauma-based screenshake for the WORLD layer only
                               (never the HUD or dialogue)
"""

import math
import random

import pygame


class SpriteSheet:
    """Cuts a strip/grid image into equal frames, left-to-right, top-to-bottom."""

    def __init__(self, image, frame_w, frame_h):
        if frame_w <= 0 or frame_h <= 0:
            raise ValueError("frame size must be positive")
        cols = image.get_width() // frame_w
        rows = image.get_height() // frame_h
        if cols < 1 or rows < 1:
            raise ValueError("image smaller than one frame")
        self.frames = []
        for r in range(rows):
            for c in range(cols):
                rect = pygame.Rect(c * frame_w, r * frame_h, frame_w, frame_h)
                self.frames.append(image.subsurface(rect).copy())

    def __len__(self):
        return len(self.frames)

    def __getitem__(self, i):
        return self.frames[i]

    def slice(self, start, count):
        return self.frames[start:start + count]


class Animation:
    """Plays a list of frames at `fps`. loop=False holds the last frame."""

    def __init__(self, frames, fps=8.0, loop=True):
        if not frames:
            raise ValueError("animation needs at least one frame")
        if fps <= 0:
            raise ValueError("fps must be positive")
        self.frames = list(frames)
        self.fps = fps
        self.loop = loop
        self.time = 0.0

    def reset(self):
        self.time = 0.0

    def update(self, dt):
        self.time += max(0.0, dt)

    @property
    def index(self):
        i = int(self.time * self.fps)
        n = len(self.frames)
        return i % n if self.loop else min(i, n - 1)

    @property
    def done(self):
        return (not self.loop) and int(self.time * self.fps) >= len(self.frames) - 1

    @property
    def frame(self):
        return self.frames[self.index]


class SquashStretch:
    """Damped spring around scale 1.0. Area is kept roughly constant.

    trigger(0.3)  -> stretch tall (jump / pop); trigger(-0.3) -> squash flat (land).
    """

    def __init__(self, stiffness=300.0, damping=14.0):
        self.stiffness = stiffness
        self.damping = damping
        self.x = 0.0       # displacement from rest
        self.v = 0.0

    def trigger(self, amount):
        self.v += amount * 12.0

    def update(self, dt):
        dt = min(max(0.0, dt), 1 / 30)   # keep the spring stable on lag spikes
        self.v += (-self.stiffness * self.x - self.damping * self.v) * dt
        self.x += self.v * dt

    @property
    def at_rest(self):
        return abs(self.x) < 1e-3 and abs(self.v) < 1e-2

    @property
    def scale(self):
        """(sx, sy): taller means narrower."""
        sy = max(0.2, 1.0 + self.x)
        return 1.0 / sy, sy


def scaled(surface, sx, sy, anchor="midbottom"):
    """Scale a sprite; returns (new_surface, offset) so the anchor stays put."""
    w = max(1, int(round(surface.get_width() * sx)))
    h = max(1, int(round(surface.get_height() * sy)))
    img = pygame.transform.scale(surface, (w, h))
    base = surface.get_rect()
    new = img.get_rect()
    setattr(new, anchor, getattr(base, anchor))
    return img, (new.x - base.x, new.y - base.y)


def hit_flash(surface, amount=1.0, colour=(255, 255, 255)):
    """Copy of `surface` pushed toward `colour` by amount 0..1; alpha untouched."""
    amount = max(0.0, min(1.0, amount))
    out = surface.copy()
    if amount <= 0:
        return out
    add = pygame.Surface(out.get_size(), pygame.SRCALPHA)
    add.fill(tuple(int(c * amount) for c in colour) + (0,))
    out.blit(add, (0, 0), special_flags=pygame.BLEND_RGB_ADD)
    return out


class Shake:
    """Trauma shake: offset magnitude scales with trauma squared, decaying fast.

    Apply `offset()` to the world layer only.
    """

    def __init__(self, max_offset=10, decay=1.8, seed=1):
        self.max_offset = max_offset
        self.decay = decay
        self.trauma = 0.0
        self._rng = random.Random(seed)

    def add(self, amount):
        self.trauma = max(0.0, min(1.0, self.trauma + amount))

    def update(self, dt):
        self.trauma = max(0.0, self.trauma - self.decay * max(0.0, dt))

    def offset(self):
        if self.trauma <= 0:
            return (0, 0)
        mag = self.max_offset * self.trauma ** 2
        ang = self._rng.uniform(0, 2 * math.pi)
        return (int(round(math.cos(ang) * mag)), int(round(math.sin(ang) * mag)))
