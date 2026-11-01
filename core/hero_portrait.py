"""
core/hero_portrait.py
Owner: Member 1 - Core Game System

Large animated portraits for the story cards: Ghost, Echo and WARDEN.
Each one is drawn on a 48x48 pixel grid (shading, highlights, details), then
scaled up without smoothing so it keeps the pixel-art look at any card size.
The small in-game sprite (entities/sprites.py) is not used or changed here.

Animation, all driven by `tick`:
  * a glow that pulses (visor, goggle lenses, chip slot, WARDEN's iris)
  * the thieves blink every BLINK_PERIOD ticks for BLINK_LENGTH ticks
  * the thieves breathe (shoulders rise one pixel); Echo's ponytail sways
  * WARDEN's pupil looks side to side and its ring of marks turns
"""

import math

import pygame

CHARACTERS = ("ghost", "echo", "warden")

# Glow colour per character.
GLOW = {
    "ghost": (0, 230, 255),
    "echo": (255, 190, 60),
    "warden": (255, 50, 50),
}

GRID = 48  # drawing resolution; the result is scaled to the requested size

BLINK_PERIOD = 120  # ticks between the start of two blinks
BLINK_LENGTH = 6    # ticks the eyes stay shut


def is_blinking(tick):
    """True during the last BLINK_LENGTH ticks of every BLINK_PERIOD."""
    return tick % BLINK_PERIOD >= BLINK_PERIOD - BLINK_LENGTH


def _breath(tick):
    """0 or 1: how many grid pixels the shoulders are raised."""
    return 1 if math.sin(tick * 0.07) > 0.3 else 0


def _pulse(tick):
    return 0.5 + 0.5 * math.sin(tick * 0.2)


def _shift(points, dy):
    return [(x, y - dy) for x, y in points]


def _draw_ghost(g, tick, blink):
    dy = _breath(tick)
    # Cloak: body, shaded right side, bright top edge, collar and straps.
    body = _shift([(4, 47), (8, 32), (18, 27), (30, 27), (40, 32), (44, 47)], dy)
    pygame.draw.polygon(g, (24, 34, 62), body)
    pygame.draw.polygon(g, (16, 24, 46), _shift([(30, 27), (40, 32), (44, 47), (32, 47)], dy))
    pygame.draw.lines(g, (70, 96, 150), False, _shift([(8, 32), (18, 27), (30, 27), (40, 32)], dy), 1)
    pygame.draw.polygon(g, (10, 14, 28), _shift([(18, 27), (24, 35), (30, 27)], dy))
    pygame.draw.line(g, (44, 58, 92), (14, 33 - dy), (20, 47), 1)
    pygame.draw.line(g, (44, 58, 92), (34, 33 - dy), (28, 47), 1)
    pygame.draw.rect(g, (52, 64, 98), (22, 36 - dy, 4, 4))  # chip-slot frame
    pygame.draw.rect(g, (8, 12, 24), (23, 37 - dy, 2, 2))

    # Hood: dark shell with a lit rim on the left, then the shadowed face.
    pygame.draw.ellipse(g, (20, 28, 52), (12, 3, 24, 28))
    pygame.draw.arc(g, (58, 82, 128), (12, 3, 24, 28), math.radians(100), math.radians(200), 2)
    pygame.draw.ellipse(g, (6, 10, 22), (16, 8, 16, 18))
    pygame.draw.rect(g, (14, 20, 36), (19, 19, 10, 4))      # mask
    pygame.draw.line(g, (30, 40, 64), (20, 21), (28, 21), 1)

    # Visor: bevelled frame; closed it shrinks to a dim line.
    pygame.draw.rect(g, (40, 60, 84), (16, 12, 16, 5))
    if blink:
        pygame.draw.rect(g, (16, 50, 66), (17, 14, 14, 1))
    else:
        pygame.draw.rect(g, GLOW["ghost"], (17, 13, 14, 3))
        pygame.draw.rect(g, (190, 250, 255), (18, 13, 4, 1))  # specular glint


def _draw_echo(g, tick, blink):
    dy = _breath(tick)
    sway = round(2 * math.sin(tick * 0.06))

    # Ponytail behind everything, swaying.
    tail = [(34, 11), (41 + sway, 19), (42 + sway, 32), (38 + sway, 38), (36, 24)]
    pygame.draw.polygon(g, (150, 70, 20), tail)
    pygame.draw.lines(g, (214, 124, 44), False, [(37, 14), (41 + sway, 22), (41 + sway, 31)], 1)

    # Jacket: orange with a shaded side, dark collar and zipper.
    body = _shift([(6, 47), (9, 33), (18, 28), (30, 28), (39, 33), (42, 47)], dy)
    pygame.draw.polygon(g, (214, 120, 40), body)
    pygame.draw.polygon(g, (168, 82, 24), _shift([(30, 28), (39, 33), (42, 47), (31, 47)], dy))
    pygame.draw.lines(g, (255, 176, 90), False, _shift([(9, 33), (18, 28), (30, 28)], dy), 1)
    pygame.draw.polygon(g, (60, 40, 32), _shift([(18, 28), (24, 34), (30, 28)], dy))
    pygame.draw.line(g, (96, 60, 36), (24, 34 - dy), (24, 47), 1)
    pygame.draw.rect(g, (96, 70, 40), (27, 38 - dy, 4, 4))  # chip-slot frame
    pygame.draw.rect(g, (40, 24, 12), (28, 39 - dy, 2, 2))

    # Hair, face, neck.
    pygame.draw.ellipse(g, (150, 70, 20), (11, 4, 26, 27))
    pygame.draw.rect(g, (226, 172, 132), (21, 25, 6, 5))      # neck
    pygame.draw.ellipse(g, (240, 190, 150), (16, 10, 16, 17))
    pygame.draw.ellipse(g, (214, 160, 122), (26, 12, 6, 14))  # shaded cheek
    pygame.draw.polygon(g, (150, 70, 20), [(15, 9), (33, 9), (31, 13), (24, 11), (17, 14)])  # fringe
    pygame.draw.polygon(g, (214, 124, 44), [(18, 9), (26, 8), (22, 11)])

    # Goggles pushed up on the forehead.
    pygame.draw.rect(g, (60, 50, 70), (13, 8, 22, 3))
    for cx in (19, 29):
        pygame.draw.circle(g, (96, 86, 110), (cx, 9), 4)
        pygame.draw.circle(g, GLOW["echo"], (cx, 9), 3)

    # Eyes and mouth.
    if blink:
        pygame.draw.line(g, (60, 30, 40), (19, 17), (21, 17), 1)
        pygame.draw.line(g, (60, 30, 40), (27, 17), (29, 17), 1)
    else:
        pygame.draw.rect(g, (255, 255, 255), (18, 16, 4, 3))
        pygame.draw.rect(g, (255, 255, 255), (26, 16, 4, 3))
        pygame.draw.rect(g, (30, 20, 50), (20, 16, 2, 3))
        pygame.draw.rect(g, (30, 20, 50), (28, 16, 2, 3))
    pygame.draw.rect(g, (190, 100, 100), (22, 22, 4, 1))


def _draw_warden(g, tick, alert=False):
    cx = cy = GRID // 2
    # Hexagonal housing with two antennae.
    hexagon = [
        (cx + 22 * math.cos(math.radians(a)), cy + 22 * math.sin(math.radians(a)))
        for a in range(30, 390, 60)
    ]
    pygame.draw.rect(g, (90, 16, 26), (11, 0, 2, 6))
    pygame.draw.rect(g, (90, 16, 26), (35, 0, 2, 6))
    pygame.draw.polygon(g, (34, 12, 20), hexagon)
    pygame.draw.polygon(g, (120, 24, 34), hexagon, 2)
    inner = [
        (cx + 19 * math.cos(math.radians(a)), cy + 19 * math.sin(math.radians(a)))
        for a in range(30, 390, 60)
    ]
    pygame.draw.polygon(g, (52, 16, 26), inner)
    pygame.draw.lines(g, (176, 56, 64), False, hexagon[3:6], 1)  # lit upper-left bevel
    for x, y in hexagon:  # rivets at the corners
        pygame.draw.rect(g, (200, 90, 90), (round(x) - 1, round(y) - 1, 2, 2))

    # Ring of marks that slowly turns.
    spin = tick * (0.12 if alert else 0.03)
    for i in range(12):
        angle = spin + i * math.pi / 6
        x = round(cx + 17 * math.cos(angle))
        y = round(cy + 17 * math.sin(angle))
        pygame.draw.rect(g, (230, 60, 60) if i % 3 == 0 else (130, 30, 40), (x - 1, y - 1, 2, 2))

    # Eye: iris layers, a pupil that looks around, and a glint.
    look = round(6 * math.sin(tick * 0.18)) if alert else round(5 * math.sin(tick * 0.03))
    pygame.draw.circle(g, (60, 8, 16), (cx, cy), 13)
    pygame.draw.circle(g, (150, 12, 22), (cx, cy), 11)
    pygame.draw.circle(g, (214, 32, 40), (cx, cy), 8)
    pygame.draw.circle(g, (255, 76, 64), (cx, cy), 5)
    pygame.draw.circle(g, (6, 0, 4), (cx + look, cy), 4)
    pygame.draw.arc(g, (255, 140, 120), (cx - 11, cy - 11, 22, 22), math.radians(110), math.radians(170), 2)
    for k in range(-6, 7, 3):  # faint scan lines across the iris
        pygame.draw.line(g, (170, 20, 30), (cx - 6, cy + k), (cx - 4, cy + k), 1)
    pygame.draw.rect(g, (255, 210, 200), (cx + look - 2, cy - 2, 1, 1))


def make_portrait(name, size, tick=0, alert=False):
    """Return a size x size SRCALPHA portrait of `name`; tick drives the animation.

    alert only affects WARDEN: faster eye and ring, quicker glow (it is "speaking").
    """
    if name not in CHARACTERS:
        raise ValueError(f"Unknown character: {name!r}")

    grid = pygame.Surface((GRID, GRID), pygame.SRCALPHA)
    blink = is_blinking(tick)
    if name == "ghost":
        _draw_ghost(grid, tick, blink)
    elif name == "echo":
        _draw_echo(grid, tick, blink)
    else:
        _draw_warden(grid, tick, alert)
    figure = pygame.transform.scale(grid, (size, size))  # nearest neighbour

    unit = size / GRID
    color = GLOW[name]
    pulse = _pulse(tick * 2.5 if alert and name == "warden" else tick)

    # Soft halo behind the figure, drawn under it so the edges stay crisp.
    halo = pygame.Surface((size, size), pygame.SRCALPHA)
    height = 0.5 if name == "warden" else 0.28
    center = (int(size * 0.5), int(size * height))
    pygame.draw.circle(halo, (*color, int(25 + 45 * pulse)), center, int(size * 0.22))
    pygame.draw.circle(halo, (*color, int(15 + 30 * pulse)), center, int(size * 0.3))

    # Pulsing light on top of the sprite.
    glow = pygame.Surface((size, size), pygame.SRCALPHA)
    if name == "ghost":
        if not blink:
            visor = pygame.Rect(int(17 * unit), int(13 * unit), int(14 * unit), max(1, int(3 * unit)))
            pygame.draw.rect(glow, (*color, int(60 + 120 * pulse)), visor)
        chip = (int(23 * unit), int((37 - _breath(tick)) * unit))
        pygame.draw.rect(glow, (*color, int(60 + 150 * (1 - pulse))), (*chip, max(1, int(2 * unit)), max(1, int(2 * unit))))
    elif name == "echo":
        for lens_x in (19, 29):
            pygame.draw.circle(glow, (*color, int(40 + 110 * pulse)),
                               (int(lens_x * unit), int(9 * unit)), max(1, int(3 * unit)))
        chip = (int(28 * unit), int((39 - _breath(tick)) * unit))
        pygame.draw.rect(glow, (*color, int(60 + 150 * (1 - pulse))), (*chip, max(1, int(2 * unit)), max(1, int(2 * unit))))
    else:
        iris = (int(24 * unit), int(24 * unit))
        pygame.draw.circle(glow, (*color, int(30 + 90 * pulse)), iris, max(1, int(8 * unit)))

    result = pygame.Surface((size, size), pygame.SRCALPHA)
    result.blit(halo, (0, 0))
    result.blit(figure, (0, 0))
    result.blit(glow, (0, 0))
    return result
