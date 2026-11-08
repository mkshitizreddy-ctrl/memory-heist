"""
levels/lobby_extras.py

Floor 1 extras, on top of the crate sorting: the WARDEN camera sweeps the
lobby (stay out of its beam), three visitor chips are hidden on the floor,
and the reception bell and vending machine answer to E.

None of it touches the crate rules or the security meter, so the floor still
scores like the old Level 1: a spotting costs a little score, never security.
"""

import math

import pygame

from ui import theme

BEAM_LENGTH = 360
BEAM_HALF_ANGLE = 0.17          # radians either side of the beam's centre line
BEAM_SWING = 0.75               # how far the beam swings from straight down
BEAM_PERIOD = 7.0               # seconds for one full left-right-left sweep
SPOT_TIME = 0.45                # seconds in the beam before the WARDEN notices
SPOT_COOLDOWN = 3.0             # seconds before it can notice anyone again
SPOT_PENALTY = 5                # score lost when spotted
MAX_SPOTS = 4                   # after this many the camera stops penalising

CHIP_SIZE = 18
CHIP_POINTS = 10
CHIP_BONUS = 30                 # for finding all of them
CHIPS_HIDDEN = 3
# Tile spots (col, row) a chip may be hidden on: open floor, clear of props.
CHIP_SPOTS = [(4, 5), (27, 7), (10, 13), (23, 10), (14, 9), (6, 16), (21, 14)]

VENDING_POINTS = 5
BELL_LINES = ("Ding! Sign in, please.", "One moment, visitor.", "Please stop ringing that.")
VENDING_LINE = "A cold coffee drops out. +5"
VENDING_EMPTY = "Sold out."


class SweepBeam:
    """A narrow wedge of light swinging from the camera over the lobby floor."""

    def __init__(self, origin, length=BEAM_LENGTH, half_angle=BEAM_HALF_ANGLE,
                 swing=BEAM_SWING, period=BEAM_PERIOD):
        self.origin = origin
        self.length = length
        self.half_angle = half_angle
        self.swing = swing
        self.period = period

    def angle(self, t):
        """Direction of the centre line at time t (pi/2 is straight down the screen)."""
        return math.pi / 2 + self.swing * math.sin(2 * math.pi * t / self.period)

    def contains(self, point, t):
        dx, dy = point[0] - self.origin[0], point[1] - self.origin[1]
        dist = math.hypot(dx, dy)
        if dist > self.length:
            return False
        off = (math.atan2(dy, dx) - self.angle(t) + math.pi) % (2 * math.pi) - math.pi
        return abs(off) <= self.half_angle

    def polygon(self, t):
        a = self.angle(t)
        ox, oy = self.origin
        return [(ox, oy)] + [
            (ox + math.cos(a + s) * self.length, oy + math.sin(a + s) * self.length)
            for s in (-self.half_angle, self.half_angle)]


class Watch:
    """Counts how long each player stands in the beam and rules when they are spotted."""

    def __init__(self, beam):
        self.beam = beam
        self.exposure = {}
        self.cooldown = 0.0
        self.spots = 0

    def update(self, dt, t, points):
        """Advance by dt; `points` maps a player key to a position. Returns the
        key of whoever was just spotted, or None."""
        self.cooldown = max(0.0, self.cooldown - dt)
        spotted = None
        for key, point in points.items():
            if self.cooldown > 0.0 or not self.beam.contains(point, t):
                self.exposure[key] = 0.0        # after a spotting everyone starts fresh
                continue
            self.exposure[key] = self.exposure.get(key, 0.0) + dt
            if (spotted is None and self.exposure[key] >= SPOT_TIME
                    and self.spots < MAX_SPOTS):
                spotted = key
                self.exposure[key] = 0.0
                self.cooldown = SPOT_COOLDOWN
                self.spots += 1
        return spotted

    def danger(self):
        """0 (nobody in the beam) to just under 1 (about to be spotted)."""
        return min(1.0, max(self.exposure.values(), default=0.0) / SPOT_TIME)


class Chip:
    def __init__(self, tile):
        col, row = tile
        self.rect = pygame.Rect(0, 0, CHIP_SIZE, CHIP_SIZE)
        self.rect.center = (col * 32 + 16, row * 32 + 16)
        self.taken = False
        self.phase = col * 0.7 + row * 0.3


def draw_beam(overlay, beam, t, danger):
    """The beam as a translucent wedge: teal while calm, coral as the WARDEN closes in."""
    overlay.fill((0, 0, 0, 0))
    colour = theme.mix(theme.TEAL, theme.CORAL, danger)
    pygame.draw.polygon(overlay, (*colour, int(38 + 70 * danger)), beam.polygon(t))
    return overlay


def draw_chip(surf, chip, t):
    bob = int(math.sin(t * 3 + chip.phase) * 2)
    c = chip.rect.move(0, bob).center
    glow = 0.5 + 0.5 * math.sin(t * 5 + chip.phase)
    pygame.draw.circle(surf, theme.mix(theme.NAVY, theme.TEAL, 0.4 + 0.3 * glow), c, 15)
    body = pygame.Rect(0, 0, 14, 14)
    body.center = c
    pygame.draw.rect(surf, theme.INK, body.inflate(2, 2), border_radius=3)
    pygame.draw.rect(surf, theme.mix(theme.TEAL, theme.PAPER, glow * 0.6), body, border_radius=3)
    for dx in (-4, 0, 4):
        pygame.draw.line(surf, theme.INK, (c[0] + dx, c[1] - 3), (c[0] + dx, c[1] + 3), 1)
