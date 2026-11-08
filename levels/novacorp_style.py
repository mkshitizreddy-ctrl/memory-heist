"""
levels/novacorp_style.py

The NovaCorp look: a worn, watched, bureaucratic building. Every floor draws
its walls and furniture through these helpers, so the whole game shares one
mood: washed-out colour, dark corners and grain, stained floors, floor
stencils, propaganda posters, filing cabinets and a PA speaker that makes
announcements.

Nothing here knows about a particular level; each function takes the surface
(or rect) to draw on.
"""

import math
import random

import numpy as np
import pygame

from ui import theme

# --- the grade -----------------------------------------------------------
DESATURATE = 0.35               # how far colour is pulled toward grey
TINT = (1.0, 0.97, 0.86)        # a faint nicotine-yellow cast
VIGNETTE = 0.45                 # how dark the corners get
GRAIN = 5                       # +/- brightness of the film grain


def grade(surface, seed=1, desaturate=DESATURATE, tint=TINT, vignette=VIGNETTE, grain=GRAIN):
    """Wash out `surface` in place: less colour, a yellow cast, dark corners, grain."""
    arr = pygame.surfarray.array3d(surface).astype(np.float32)          # [W, H, 3]
    w, h = arr.shape[:2]
    lum = arr @ np.array([0.299, 0.587, 0.114], dtype=np.float32)       # [W, H]
    arr = arr * (1 - desaturate) + lum[..., None] * desaturate
    arr *= np.array(tint, dtype=np.float32)
    xs = np.linspace(-1, 1, w, dtype=np.float32)[:, None]
    ys = np.linspace(-1, 1, h, dtype=np.float32)[None, :]
    arr *= (1 - vignette * np.clip((xs ** 2 + ys ** 2) / 2, 0, 1))[..., None]
    if grain:
        rng = np.random.default_rng(seed)
        arr += rng.integers(-grain, grain + 1, size=(w, h, 1)).astype(np.float32)
    pygame.surfarray.blit_array(surface, np.clip(arr, 0, 255).astype(np.uint8))
    return surface


# --- grime and markings --------------------------------------------------
def stains(surface, area, seed=1, count=14):
    """Dark smudges, scuffs and a crack or two, only inside `area`."""
    area = pygame.Rect(area)
    rng = random.Random(seed)
    layer = pygame.Surface(area.size, pygame.SRCALPHA)
    for _ in range(count):
        w, h = rng.randint(14, 54), rng.randint(8, 26)
        x, y = rng.randint(0, area.w - w), rng.randint(0, area.h - h)
        pygame.draw.ellipse(layer, (10, 8, 6, rng.randint(14, 34)), (x, y, w, h))
    for _ in range(count // 2):                                        # scuff lines
        x, y = rng.randint(0, area.w - 30), rng.randint(0, area.h - 6)
        pygame.draw.line(layer, (0, 0, 0, 40), (x, y), (x + rng.randint(10, 28), y + rng.randint(-3, 3)), 1)
    x, y = rng.randint(20, area.w - 60), rng.randint(10, area.h - 40)  # one crack
    points = [(x, y)]
    for _ in range(4):
        x += rng.randint(6, 14)
        y += rng.randint(-8, 10)
        points.append((min(area.w - 1, x), max(0, min(area.h - 1, y))))
    pygame.draw.lines(layer, (0, 0, 0, 90), False, points, 1)
    surface.blit(layer, area.topleft)


def stencil(surface, text, centre, font, colour=(214, 176, 60), alpha=120, angle=0):
    """Paint `text` on the floor, faded as if walked on."""
    img = font.render(text, True, colour)
    if angle:
        img = pygame.transform.rotate(img, angle)
    img = img.convert_alpha() if pygame.display.get_surface() else img
    img.set_alpha(alpha)
    surface.blit(img, img.get_rect(center=centre))
    return img.get_rect(center=centre)


def dashed_line(surface, start, end, colour=(214, 176, 60), alpha=110, dash=14, gap=10, width=3):
    """A painted floor line made of dashes."""
    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    length = math.dist(start, end)
    if length == 0:
        return
    dx, dy = (end[0] - start[0]) / length, (end[1] - start[1]) / length
    pos = 0.0
    while pos < length:
        stop = min(length, pos + dash)
        pygame.draw.line(layer, (*colour, alpha),
                         (start[0] + dx * pos, start[1] + dy * pos),
                         (start[0] + dx * stop, start[1] + dy * stop), width)
        pos += dash + gap
    surface.blit(layer, (0, 0))


# --- furniture and wall art ----------------------------------------------
def draw_cabinet(surface, rect, accent=(120, 130, 120)):
    """A grey steel filing cabinet seen from the front: three drawers with handles."""
    r = pygame.Rect(rect)
    body = (92, 98, 94)
    pygame.draw.rect(surface, (0, 0, 0), r.move(2, 3), border_radius=3)
    pygame.draw.rect(surface, body, r, border_radius=3)
    drawer_h = r.h // 3
    for i in range(3):
        d = pygame.Rect(r.x + 3, r.y + 3 + i * drawer_h, r.w - 6, drawer_h - 4)
        pygame.draw.rect(surface, theme.mix(body, (200, 205, 195), 0.12), d, border_radius=2)
        pygame.draw.rect(surface, theme.mix(body, (0, 0, 0), 0.45), d, 1, border_radius=2)
        pygame.draw.rect(surface, theme.mix(accent, (0, 0, 0), 0.3), (d.centerx - 5, d.centery - 1, 10, 3))
        label = pygame.Rect(d.x + 3, d.y + 2, 10, 5)
        pygame.draw.rect(surface, (210, 200, 160), label)
    pygame.draw.rect(surface, theme.mix(body, (0, 0, 0), 0.5), r, 2, border_radius=3)


def draw_cooler(surface, rect):
    """A water cooler: grey base, blue bottle, a little tap."""
    r = pygame.Rect(rect)
    pygame.draw.rect(surface, (0, 0, 0), r.move(2, 3), border_radius=4)
    base = pygame.Rect(r.x + 2, r.y + r.h // 2, r.w - 4, r.h // 2)
    pygame.draw.rect(surface, (120, 126, 122), base, border_radius=3)
    bottle = pygame.Rect(r.x + 5, r.y + 2, r.w - 10, r.h // 2 - 2)
    pygame.draw.rect(surface, (110, 150, 190), bottle, border_radius=7)
    pygame.draw.rect(surface, (200, 225, 245), (bottle.x + 3, bottle.y + 4, 4, bottle.h - 10), border_radius=2)
    pygame.draw.circle(surface, (170, 60, 50), (r.x + 9, base.y + 8), 3)
    pygame.draw.circle(surface, (60, 110, 190), (r.right - 9, base.y + 8), 3)
    pygame.draw.rect(surface, (60, 64, 62), base, 2, border_radius=3)


def draw_poster(surface, rect, lines, font, accent=(168, 52, 44)):
    """A propaganda poster: a dark card, a watching eye and a bold slogan."""
    r = pygame.Rect(rect)
    pygame.draw.rect(surface, (0, 0, 0), r.move(2, 2))
    pygame.draw.rect(surface, theme.mix((52, 50, 40), accent, 0.35), r)
    pygame.draw.rect(surface, (214, 200, 150), r, 2)
    eye = (r.centerx, r.y + r.h // 3)
    pygame.draw.ellipse(surface, (226, 214, 170), (eye[0] - 14, eye[1] - 8, 28, 16))
    pygame.draw.circle(surface, accent, eye, 6)
    pygame.draw.circle(surface, (16, 14, 10), eye, 3)
    y = r.y + r.h // 2 + 6
    for line in lines:
        img = font.render(line, True, (232, 220, 176))
        surface.blit(img, img.get_rect(midtop=(r.centerx, y)))
        y += img.get_height() + 1


def draw_speaker(surface, centre, t, active):
    """A ceiling PA speaker: a grille, and a red light that blinks while it speaks."""
    x, y = centre
    pygame.draw.rect(surface, (40, 42, 40), (x - 14, y - 8, 28, 16), border_radius=4)
    for dx in (-8, -3, 2, 7):
        pygame.draw.line(surface, (90, 94, 90), (x + dx, y - 5), (x + dx, y + 5), 1)
    on = active and int(t * 6) % 2 == 0
    pygame.draw.circle(surface, (230, 60, 50) if on else (80, 40, 36), (x + 18, y), 3)


# --- the PA system -------------------------------------------------------
class PA:
    """Reads a short announcement every so often and shows it as a caption."""

    FIRST_AT = 8.0
    EVERY = 28.0
    SHOW = 4.5

    def __init__(self, lines):
        self.lines = tuple(lines)
        self.time = 0.0
        self._next = self.FIRST_AT
        self._count = 0
        self.caption = ""
        self._since = None

    def update(self, dt):
        """Advance by dt. Returns the announcement the moment it starts, else None."""
        self.time += dt
        if self._since is not None:
            self._since += dt
            if self._since >= self.SHOW:
                self._since = None
                self.caption = ""
        if self.time >= self._next:
            self._next += self.EVERY
            self.caption = self.lines[self._count % len(self.lines)]
            self._count += 1
            self._since = 0.0
            return self.caption
        return None

    @property
    def active(self):
        return self._since is not None

    def alpha(self):
        """0..255: fades in, holds, fades out."""
        if self._since is None:
            return 0
        fade = 0.4
        k = min(self._since / fade, (self.SHOW - self._since) / fade, 1.0)
        return int(255 * max(0.0, k))
