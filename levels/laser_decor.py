"""
levels/laser_decor.py
Owner: Member 3 - Yashovardhan (Floor 3), restyled by Member 5 (UI)

Floor 3's three laser rooms in the NovaCorp look.  Pure drawing, baked once per
room: worn concrete tiles, a back and front wall, the floor paint each room
needs and a washed-out grade, so the floor matches Floors 1, 2, 4 and 5.
Nothing here changes a rule; the lasers, pads, robot, core and gates stay in
levels/level3_loops.py, which hands in the positions it uses.

    Room 1  LASER TRAINING    test range: scorch marks where the rotor has fired for years
    Room 2  LASER NETWORK     the sentry's patrol loop painted on the floor
    Room 3  CORE INFILTRATION reactor deck: grating and the overload limit ring
"""

import math
import random

import pygame

from levels import novacorp_style as style
from ui import theme
from ui.fonts import ui_font

PALETTE = theme.floor_palette("level3")
ACCENT = PALETTE["accent"]
FLOOR = theme.mix(PALETTE["floor"], theme.SLATE, 0.55)    # night-shift concrete with a teal cast
WALL = (24, 32, 42)
SIDE = theme.mix(WALL, theme.SLATE, 0.45)
AMBER = theme.mix(theme.GOLD, FLOOR, 0.3)
RED = (168, 52, 44)
TRIM = theme.mix(ACCENT, theme.SLATE, 0.55)            # the room's one accent, muted for panel borders
OPTION_FILL = theme.mix(theme.INK, theme.NAVY, 0.6)     # answer buttons: the team kit's navy
OPTION_BORDER = theme.mix(TRIM, theme.NAVY, 0.35)

ORIGIN = (40, 30)                                       # the room surface sits at this screen point


def _local(point):
    return (point[0] - ORIGIN[0], point[1] - ORIGIN[1])


def _tiles(surface, area, seed):
    """Worn 40 px concrete tiles: two tones, grout, a few cracked or replaced tiles."""
    rng = random.Random(seed)
    dark = theme.mix(theme.INK, FLOOR, 0.62)
    light = theme.mix(theme.INK, FLOOR, 0.74)
    for ty in range(area.top, area.bottom, 40):
        for tx in range(area.left, area.right, 40):
            colour = light if ((tx - area.left) // 40 + (ty - area.top) // 40) % 2 == 0 else dark
            if rng.random() < 0.06:                                 # a replaced tile that never matched
                colour = theme.mix(colour, theme.PAPER, 0.06)
            pygame.draw.rect(surface, colour, (tx, ty, 40, 40))
    grout = theme.mix(dark, theme.INK, 0.5)
    for x in range(area.left, area.right, 40):
        pygame.draw.line(surface, grout, (x, area.top), (x, area.bottom - 1))
    for y in range(area.top, area.bottom, 40):
        pygame.draw.line(surface, grout, (area.left, y), (area.right - 1, y))
    style.stains(surface, area, seed=seed, count=18)


def _back_wall(surface, rect):
    """The wall behind the header: panels, a skirting board and its shadow on the floor."""
    pygame.draw.rect(surface, WALL, rect)
    for x in range(rect.left, rect.right, 80):
        pygame.draw.line(surface, theme.mix(WALL, theme.INK, 0.5), (x, rect.top), (x, rect.bottom))
    pygame.draw.rect(surface, theme.mix(WALL, theme.SLATE, 0.5), (rect.left, rect.bottom - 8, rect.width, 8))
    pygame.draw.line(surface, theme.mix(ACCENT, WALL, 0.55), (rect.left, rect.bottom), (rect.right, rect.bottom), 2)
    shade = pygame.Surface((rect.width, 14), pygame.SRCALPHA)
    for i in range(14):
        pygame.draw.line(shade, (0, 0, 0, 90 - i * 6), (0, i), (rect.width, i))
    surface.blit(shade, (rect.left, rect.bottom + 1))


def _front_wall(surface, rect):
    pygame.draw.rect(surface, SIDE, rect)
    for x in range(rect.left, rect.right, 80):
        pygame.draw.line(surface, theme.mix(SIDE, theme.INK, 0.55), (x, rect.top), (x, rect.bottom - 1))
    pygame.draw.line(surface, theme.mix(ACCENT, SIDE, 0.4), (rect.left, rect.top), (rect.right - 1, rect.top), 2)


def wall_face(surface, rect):
    """A bulkhead seen from above (screen coordinates): steel panels, rivets, a lit edge."""
    rect = pygame.Rect(rect)
    pygame.draw.rect(surface, SIDE, rect)
    seam = theme.mix(SIDE, theme.INK, 0.55)
    for y in range(rect.top, rect.bottom, 36):
        pygame.draw.line(surface, seam, (rect.left, y), (rect.right - 1, y))
    for y in range(rect.top + 18, rect.bottom, 36):
        pygame.draw.circle(surface, theme.mix(SIDE, theme.PAPER, 0.35), (rect.centerx, y), 2)
    edge = theme.mix(ACCENT, SIDE, 0.35)
    pygame.draw.line(surface, edge, rect.topleft, (rect.left, rect.bottom - 1), 2)
    pygame.draw.line(surface, edge, (rect.right - 1, rect.top), (rect.right - 1, rect.bottom - 1), 2)


def _stencil(surface, text, centre, size=22, alpha=70, colour=None, angle=0):
    style.stencil(surface, text, centre, ui_font(size, bold=True),
                  colour=colour or theme.mix(FLOOR, theme.PAPER, 0.55), alpha=alpha, angle=angle)


# --- the three rooms ----------------------------------------------------------------------

def _range(surface, geo):
    """Room 1: a test range.  Scorch streaks fan out from the rotor hub, which sits on a bolted plate."""
    cx, cy = _local(geo["rotor"])
    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    rng = random.Random(31)
    for _ in range(26):
        angle = rng.uniform(0, math.tau)
        inner, outer = rng.uniform(30, 60), rng.uniform(120, 260)
        start = (cx + math.cos(angle) * inner, cy + math.sin(angle) * inner)
        end = (cx + math.cos(angle) * outer, cy + math.sin(angle) * outer)
        pygame.draw.line(layer, (0, 0, 0, rng.randint(26, 50)), start, end, rng.randint(2, 5))
    surface.blit(layer, (0, 0))
    plate = pygame.Rect(0, 0, 76, 76)
    plate.center = (cx, cy)
    pygame.draw.rect(surface, theme.mix(SIDE, theme.INK, 0.25), plate, border_radius=6)
    pygame.draw.rect(surface, theme.mix(SIDE, theme.PAPER, 0.25), plate, 1, border_radius=6)
    for dx, dy in ((-30, -30), (30, -30), (-30, 30), (30, 30)):
        pygame.draw.circle(surface, theme.mix(SIDE, theme.PAPER, 0.4), (cx + dx, cy + dy), 2)
    _stencil(surface, "LASER TEST RANGE", (cx, 372), 22, alpha=60)
    _stencil(surface, "STAND ON A LIT PAD", (cx, 394), 13, alpha=100, colour=AMBER)


def _gallery(surface, geo):
    """Room 2: the sentry's patrol loop, painted in amber dashes with arrows: it walks it forever."""
    points = [_local(p) for p in geo["waypoints"]]
    if len(points) >= 2:
        offset = (35, 18)                                    # the robot's centre, not its top-left
        loop = [(x + offset[0], y + offset[1]) for x, y in points]
        for start, end in zip(loop, loop[1:] + loop[:1]):
            style.dashed_line(surface, start, end, colour=theme.GOLD, alpha=70, dash=12, gap=10, width=3)
            mx, my = (start[0] + end[0]) / 2, (start[1] + end[1]) / 2
            ang = math.atan2(end[1] - start[1], end[0] - start[0])
            tip = (mx + math.cos(ang) * 7, my + math.sin(ang) * 7)
            left = (mx + math.cos(ang + 2.5) * 7, my + math.sin(ang + 2.5) * 7)
            right = (mx + math.cos(ang - 2.5) * 7, my + math.sin(ang - 2.5) * 7)
            pygame.draw.polygon(surface, AMBER, (tip, left, right))
        _stencil(surface, "while patrol():", (loop[0][0] + 60, loop[0][1] + 52), 14, alpha=90, colour=AMBER)
    _stencil(surface, "CAMERA GALLERY", (430, 372), 22, alpha=60)
    _stencil(surface, "YOU ARE BEING RECORDED", (430, 394), 13, alpha=100, colour=AMBER)


def _reactor(surface, geo):
    """Room 3: a reactor deck.  Grating around the core and the overload limit painted where the ring stops."""
    cx, cy = _local(geo["core"])
    limit = int(geo["ring_max"]) + 8
    deck = pygame.Rect(0, 0, limit * 2 + 24, limit * 2 + 24)
    deck.center = (cx, cy)
    grate = theme.mix(SIDE, theme.INK, 0.35)
    pygame.draw.circle(surface, grate, (cx, cy), limit + 10)
    for x in range(deck.left, deck.right, 8):
        for y in range(deck.top, deck.bottom, 8):
            if math.hypot(x - cx, y - cy) < limit + 8:
                pygame.draw.rect(surface, theme.mix(grate, theme.INK, 0.45), (x, y, 4, 4))
    # the overload limit: red and black hazard dashes around the deck
    for i in range(48):
        a0, a1 = i * math.tau / 48, (i + 0.55) * math.tau / 48
        colour = RED if i % 2 == 0 else theme.INK
        pygame.draw.arc(surface, colour, (cx - limit - 6, cy - limit - 6, (limit + 6) * 2, (limit + 6) * 2),
                        -a1, -a0, 5)
    _stencil(surface, "OVERLOAD LIMIT", (cx - limit - 20, cy), 13, alpha=130,
             colour=theme.mix(RED, theme.PAPER, 0.3), angle=90)
    # coolant pipes along the back wall feed the core
    for y, colour in ((126, (60, 90, 110)), (133, (70, 70, 84))):
        pygame.draw.line(surface, colour, (20, y), (surface.get_width() - 60, y), 5)
        for x in range(60, surface.get_width() - 60, 120):
            pygame.draw.rect(surface, theme.mix(colour, theme.PAPER, 0.2), (x, y - 4, 6, 9))
    _stencil(surface, "REACTOR CORE  -  AUTHORISED STAFF ONLY", (180, 152), 13, alpha=100, colour=AMBER)


_ROOMS = {1: _range, 2: _gallery, 3: _reactor}


def build_room(room, size, geo, play_top=150, play_bottom=450):
    """The baked room (local coordinates, drawn at screen ORIGIN).

    geo: the live positions the dressing follows, in screen coordinates:
    rotor (Room 1), waypoints (Room 2), core and ring_max (Room 3).
    """
    width, height = size
    surface = pygame.Surface(size)
    top, bottom = play_top - ORIGIN[1], play_bottom - ORIGIN[1]
    _tiles(surface, pygame.Rect(0, top, width, bottom - top), seed=room * 7)
    _ROOMS[room](surface, geo)
    _back_wall(surface, pygame.Rect(0, 0, width, top))
    _front_wall(surface, pygame.Rect(0, bottom, width, height - bottom))
    style.grade(surface, seed=room, vignette=0.3, grain=4)
    pygame.draw.rect(surface, theme.mix(WALL, theme.INK, 0.6), (0, 0, width, height), 6)
    pygame.draw.rect(surface, theme.mix(ACCENT, WALL, 0.6), (6, 6, width - 12, height - 12), 1)
    return surface
