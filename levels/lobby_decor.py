"""
levels/lobby_decor.py
Owner: Member 1 - Core Game System

The small things that make the Floor 1 lobby feel lived in.  Nothing here
touches gameplay: no prop is added to the room map, so nobody ever bumps into
a decoration, and nothing is drawn over the title, the message line or the
hint text.

    draw_static(bg, accent, desk)     baked once into the background: a rug,
                                      hazard stripes, a notice board, a poster,
                                      a fire extinguisher, desk clutter
    Ambience(seed).update(dt)         and .draw(world, alert) every frame:
                                      wall clock, flickering lights, drifting
                                      dust, the receptionist's monitor, a
                                      blinking vending machine, the elevator
                                      indicator and the camera's sweeping beam

The pure helpers (clock_angles, flicker, scan_angle, cone_points, Motes) hold
the maths so it can be tested without a window.
"""

import math
import random

import pygame

from core.tilemap import TILE
from ui import theme
from ui.fonts import code_font

# --- where things go (the wall band keeps y 48..96 clear for text) -----------
RUG = pygame.Rect(9 * TILE, 8 * TILE + 8, 12 * TILE, 6 * TILE - 16)
CLOCK_CENTRE = (580, 70)
CLOCK_RADIUS = 15
BOARD = pygame.Rect(8, 7 * TILE + 4, 48, 72)               # left wall, below the elevator
POSTER = pygame.Rect(904, 4 * TILE + 12, 48, 64)           # right wall, above the exit
EXTINGUISHER = pygame.Rect(912, 13 * TILE + 8, 20, 46)     # right wall, below the exit
INDICATOR = pygame.Rect(12, 74, 40, 18)                    # above the elevator doors
STRIPES = (pygame.Rect(27 * TILE, 9 * TILE, TILE, 3 * TILE),     # in front of the exit
           pygame.Rect(2 * TILE, 3 * TILE, TILE, 3 * TILE))      # in front of the elevator
LIGHT_COLS = tuple(range(4, 28, 4))                        # the wall lights
MOTE_AREA = pygame.Rect(2 * TILE, 3 * TILE, 26 * TILE, 15 * TILE)
MOTE_COUNT = 18
CAMERA_ORIGIN = (20 * TILE + 16, 2 * TILE + 10)
CONE_LENGTH = 150
CONE_SPREAD = 0.28            # half-angle of the beam, radians
SWEEP = 0.5                   # how far the beam swings either side of straight down
SWEEP_SECONDS = 7.0
CONE_ALPHA = 24
CONE_ALPHA_ALERT = 52
FLICKER_PERIOD = 9.0          # one light stutters about this often
FLICKER_SECONDS = 0.35


# --- pure helpers ------------------------------------------------------------
def clock_angles(t):
    """(second, minute, hour) hand angles in radians, 0 = twelve, clockwise."""
    turn = 2 * math.pi
    return ((t % 60.0) / 60.0 * turn,
            (t % 3600.0) / 3600.0 * turn,
            (t % 43200.0) / 43200.0 * turn)


def flicker(t, index):
    """Brightness 0.35..1.0 of wall light `index`.  Mostly steady; every
    FLICKER_PERIOD seconds one light (taking turns) stutters for a moment."""
    slot, into = divmod(t, FLICKER_PERIOD)
    if int(slot) % len(LIGHT_COLS) != index or into > FLICKER_SECONDS:
        return 1.0
    return 0.35 + 0.65 * abs(math.sin(into / FLICKER_SECONDS * math.pi * 4))


def scan_angle(t):
    """Beam direction: straight down (pi/2) swinging +/- SWEEP."""
    return math.pi / 2 + SWEEP * math.sin(t / SWEEP_SECONDS * 2 * math.pi)


def cone_points(origin, angle, length=CONE_LENGTH, spread=CONE_SPREAD, arc=4):
    """Polygon of a beam: the apex, then points along a rounded far edge."""
    points = [tuple(origin)]
    for i in range(arc + 1):
        a = angle - spread + 2 * spread * i / arc
        points.append((origin[0] + math.cos(a) * length, origin[1] + math.sin(a) * length))
    return points


def scan_alpha(alert):
    return CONE_ALPHA_ALERT if alert else CONE_ALPHA


class Motes:
    """Specks of dust drifting in the light.  They wrap around the area."""

    def __init__(self, rng, area, count=MOTE_COUNT):
        self.area = pygame.Rect(area)
        self.motes = [{"x": rng.uniform(self.area.left, self.area.right),
                       "y": rng.uniform(self.area.top, self.area.bottom),
                       "vx": rng.uniform(-4, 4), "vy": rng.uniform(-7, -2),
                       "phase": rng.uniform(0, math.tau)} for _ in range(count)]

    def update(self, dt):
        dt = max(0.0, dt)
        a = self.area
        for m in self.motes:
            m["x"] = a.left + (m["x"] + m["vx"] * dt - a.left) % a.w
            m["y"] = a.top + (m["y"] + m["vy"] * dt - a.top) % a.h


# --- baked decoration --------------------------------------------------------
def _alpha_fill(surface, rect, colour, alpha):
    layer = pygame.Surface(rect.size, pygame.SRCALPHA)
    layer.fill((*colour, alpha))
    surface.blit(layer, rect.topleft)


def _draw_rug(bg, accent):
    base = theme.mix(theme.NAVY, accent, 0.20)
    edge = theme.mix(accent, theme.NAVY, 0.72)
    line = theme.mix(base, accent, 0.20)
    pygame.draw.rect(bg, theme.mix(base, theme.INK, 0.5), RUG.move(3, 4), border_radius=10)
    pygame.draw.rect(bg, edge, RUG, border_radius=10)
    inner = RUG.inflate(-16, -16)
    pygame.draw.rect(bg, base, inner, border_radius=6)
    pygame.draw.rect(bg, line, inner.inflate(-12, -12), 1, border_radius=4)
    cx, cy = inner.center
    for k in range(-5, 6):                                   # a lattice of diamonds
        x = cx + k * 48
        if inner.left + 18 < x < inner.right - 18:
            pygame.draw.polygon(bg, line, [(x, cy - 28), (x + 24, cy), (x, cy + 28), (x - 24, cy)], 1)
    for y in range(RUG.top + 8, RUG.bottom - 6, 10):         # fringe on the short ends
        pygame.draw.line(bg, edge, (RUG.left - 5, y), (RUG.left, y), 1)
        pygame.draw.line(bg, edge, (RUG.right, y), (RUG.right + 5, y), 1)


def _draw_stripes(bg):
    for rect in STRIPES:
        layer = pygame.Surface(rect.size, pygame.SRCALPHA)
        for x in range(-rect.h, rect.w + rect.h, 12):
            pygame.draw.line(layer, (*theme.GOLD, 120), (x, rect.h), (x + rect.h, 0), 6)
        bg.blit(layer, rect.topleft)
        pygame.draw.rect(bg, theme.mix(theme.GOLD, theme.INK, 0.4), rect, 1)


def _draw_notice_board(bg):
    pygame.draw.rect(bg, theme.mix((150, 110, 70), theme.INK, 0.35), BOARD, border_radius=3)
    cork = BOARD.inflate(-6, -6)
    pygame.draw.rect(bg, (176, 132, 86), cork, border_radius=2)
    for dx, dy, w, h, tint in ((4, 5, 16, 20, theme.PAPER), (24, 8, 15, 14, theme.GOLD),
                               (6, 33, 14, 18, theme.SKY), (23, 30, 16, 22, theme.PAPER)):
        sheet = pygame.Rect(cork.x + dx, cork.y + dy, w, h)
        pygame.draw.rect(bg, tint, sheet)
        for line in range(sheet.y + 4, sheet.bottom - 2, 4):
            pygame.draw.line(bg, theme.mix(tint, theme.INK, 0.45), (sheet.x + 2, line), (sheet.right - 3, line))
        pygame.draw.circle(bg, theme.CORAL, (sheet.centerx, sheet.y + 1), 2)


def _draw_poster(bg, accent):
    pygame.draw.rect(bg, theme.INK, POSTER.inflate(4, 4))
    pygame.draw.rect(bg, theme.mix(theme.NAVY, accent, 0.35), POSTER)
    cx, top = POSTER.centerx, POSTER.y + 10
    shield = [(cx - 12, top), (cx + 12, top), (cx + 12, top + 18), (cx, top + 32), (cx - 12, top + 18)]
    pygame.draw.polygon(bg, theme.mix(accent, theme.PAPER, 0.3), shield)
    pygame.draw.polygon(bg, theme.PAPER, shield, 2)
    pygame.draw.line(bg, theme.PAPER, (cx - 5, top + 14), (cx - 1, top + 19), 2)
    pygame.draw.line(bg, theme.PAPER, (cx - 1, top + 19), (cx + 6, top + 9), 2)
    for i, w in enumerate((30, 22)):
        pygame.draw.line(bg, theme.MIST, (cx - w // 2, POSTER.bottom - 14 + i * 5),
                         (cx + w // 2, POSTER.bottom - 14 + i * 5), 2)


def _draw_extinguisher(bg):
    r = EXTINGUISHER
    pygame.draw.rect(bg, theme.INK, r.inflate(6, 6), border_radius=6)
    body = pygame.Rect(r.x, r.y + 8, r.w, r.h - 8)
    pygame.draw.rect(bg, theme.CORAL, body, border_radius=7)
    pygame.draw.rect(bg, theme.mix(theme.CORAL, theme.PAPER, 0.35), (body.x + 3, body.y + 4, 4, body.h - 12), border_radius=2)
    pygame.draw.rect(bg, theme.MIST, (r.x + 5, r.y + 2, 10, 8), border_radius=2)
    pygame.draw.line(bg, theme.MIST, (r.x + 15, r.y + 5), (r.x + 22, r.y + 9), 2)
    pygame.draw.rect(bg, theme.PAPER, (r.x + 4, body.y + 16, r.w - 8, 8))


def _draw_desk_clutter(bg, desk):
    top = desk.y
    # lamp (left end)
    lx = desk.x + 16
    pygame.draw.ellipse(bg, theme.INK, (lx - 8, top - 4, 16, 6))
    pygame.draw.line(bg, theme.MIST, (lx, top - 2), (lx + 6, top - 16), 2)
    pygame.draw.polygon(bg, theme.GOLD, [(lx + 1, top - 20), (lx + 15, top - 18), (lx + 11, top - 11)])
    # bell
    bx = desk.x + 58
    pygame.draw.ellipse(bg, theme.GOLD, (bx - 6, top - 10, 12, 10))
    pygame.draw.rect(bg, theme.mix(theme.GOLD, theme.INK, 0.4), (bx - 8, top - 2, 16, 3), border_radius=1)
    pygame.draw.circle(bg, theme.PAPER, (bx, top - 11), 2)
    # papers
    px = desk.x + 128
    for i, tint in enumerate((theme.MIST, theme.PAPER)):
        pygame.draw.rect(bg, tint, (px + i * 2, top - 7 - i * 2, 18, 8))
        pygame.draw.rect(bg, theme.mix(tint, theme.INK, 0.4), (px + i * 2, top - 7 - i * 2, 18, 8), 1)
    # monitor (the screen itself is animated by Ambience)
    mon = monitor_rect(desk)
    pygame.draw.rect(bg, theme.INK, mon.inflate(4, 4), border_radius=3)
    pygame.draw.rect(bg, theme.SLATE, (mon.centerx - 8, mon.bottom + 2, 16, 3))
    pygame.draw.rect(bg, theme.MIST, (mon.centerx - 4, mon.bottom, 8, 3))


def monitor_rect(desk):
    """The monitor's screen, on the desk's right end."""
    return pygame.Rect(desk.right - 52, desk.y - 28, 30, 20)


def draw_static(bg, accent, desk):
    _draw_rug(bg, accent)
    _draw_stripes(bg)
    _draw_notice_board(bg)
    _draw_poster(bg, accent)
    _draw_extinguisher(bg)
    _draw_desk_clutter(bg, desk)
    pygame.draw.rect(bg, theme.INK, INDICATOR, border_radius=3)
    pygame.draw.rect(bg, theme.SLATE, INDICATOR, 1, border_radius=3)
    pygame.draw.circle(bg, theme.INK, CLOCK_CENTRE, CLOCK_RADIUS + 3)
    pygame.draw.circle(bg, theme.mix(theme.PAPER, theme.NAVY, 0.15), CLOCK_CENTRE, CLOCK_RADIUS)
    for hour in range(12):
        a = hour / 12 * math.tau
        inner = CLOCK_RADIUS - (4 if hour % 3 == 0 else 2)
        pygame.draw.line(bg, theme.INK,
                         (CLOCK_CENTRE[0] + math.sin(a) * inner, CLOCK_CENTRE[1] - math.cos(a) * inner),
                         (CLOCK_CENTRE[0] + math.sin(a) * (CLOCK_RADIUS - 1),
                          CLOCK_CENTRE[1] - math.cos(a) * (CLOCK_RADIUS - 1)), 1)


# --- animation ---------------------------------------------------------------
class Ambience:
    def __init__(self, seed=0):
        self.time = 0.0
        self.motes = Motes(random.Random(seed), MOTE_AREA)
        self._font = None

    def update(self, dt):
        dt = max(0.0, dt)
        self.time += dt
        self.motes.update(dt)

    def draw(self, world, desk, vending, alert=False):
        self._draw_beam(world, alert)
        self._draw_lights(world)
        self._draw_clock(world)
        self._draw_monitor(world, desk)
        self._draw_vending(world, vending)
        self._draw_indicator(world)
        self._draw_motes(world)

    def _draw_beam(self, world, alert):
        size = CONE_LENGTH * 2 + 4
        layer = pygame.Surface((size, size), pygame.SRCALPHA)
        centre = (size // 2, size // 2)
        colour = theme.CORAL if alert else theme.TEAL
        pygame.draw.polygon(layer, (*colour, scan_alpha(alert)),
                            cone_points(centre, scan_angle(self.time)))
        world.blit(layer, (CAMERA_ORIGIN[0] - centre[0], CAMERA_ORIGIN[1] - centre[1]))

    def _draw_lights(self, world):
        for i, col in enumerate(LIGHT_COLS):
            dim = 1.0 - flicker(self.time, i)
            if dim > 0:
                x = col * TILE
                _alpha_fill(world, pygame.Rect(x - 14, 2 * TILE + 24, 28, 6), theme.INK, int(210 * dim))

    def _draw_clock(self, world):
        sec, minute, hour = clock_angles(self.time)
        cx, cy = CLOCK_CENTRE
        for angle, length, colour, width in ((hour, 7, theme.INK, 2), (minute, 11, theme.INK, 1),
                                             (sec, 13, theme.CORAL, 1)):
            pygame.draw.line(world, colour, (cx, cy),
                             (cx + math.sin(angle) * length, cy - math.cos(angle) * length), width)
        pygame.draw.circle(world, theme.INK, (cx, cy), 2)

    def _draw_monitor(self, world, desk):
        screen = monitor_rect(desk)
        glow = 0.5 + 0.5 * math.sin(self.time * 3.0)
        pygame.draw.rect(world, theme.mix(theme.INK, theme.TEAL, 0.25 + 0.1 * glow), screen)
        for i in range(4):                                   # lines of "text" scrolling up
            y = screen.y + 2 + (i * 5 - int(self.time * 6)) % 20
            width = 8 + (i * 7) % 14
            pygame.draw.line(world, theme.mix(theme.TEAL, theme.PAPER, 0.3),
                             (screen.x + 3, y), (screen.x + 3 + width, y))

    def _draw_vending(self, world, vending):
        window = pygame.Rect(vending.x + 5, vending.y + 6, vending.w - 10, vending.h - 28)
        slot = int(self.time * 1.5) % 6
        row, col = divmod(slot, 2)
        _alpha_fill(world, pygame.Rect(window.x + 3 + col * 11, window.y + 4 + row * 11, 8, 7),
                    theme.PAPER, 150)

    def _draw_indicator(self, world):
        if self._font is None:
            self._font = code_font(15)
        digit = self._font.render("1", True, theme.TEAL)
        world.blit(digit, digit.get_rect(center=(INDICATOR.x + 12, INDICATOR.centery)))
        if int(self.time * 2) % 2 == 0:                      # the "up" arrow blinks
            x, y = INDICATOR.x + 29, INDICATOR.centery
            pygame.draw.polygon(world, theme.GOLD, [(x - 5, y + 4), (x + 5, y + 4), (x, y - 5)])

    def _draw_motes(self, world):
        for m in self.motes.motes:
            twinkle = 0.5 + 0.5 * math.sin(self.time * 1.5 + m["phase"])
            colour = theme.mix(theme.INK, theme.MIST, 0.25 + 0.5 * twinkle)
            world.set_at((int(m["x"]), int(m["y"])), colour)
            if twinkle > 0.8:
                world.set_at((int(m["x"]) + 1, int(m["y"])), colour)
