"""
levels/patrol_lanes.py
Owner: Member 5 (UI)

Floor 3, Rooms 1 and 3 - the lane loop.  The wall board shows

    for lane in range(4):
        zap(lane)

and the floor does exactly that: electric lanes fire one after another, then
the loop ends and the room rests before it starts again.  Room 1 has four
columns you cross left to right; Room 3 has three rows you cross bottom to
top while the patrol robot (the outer `while`) walks above them.

This module holds the timing, the danger rectangles and the drawing; Level 3
only asks it which rectangles are live and tells it when a hit re-arms the loop.
"""

import math
import random

import pygame

from ui import theme

# Room 1: four columns across the corridor, from the wall's foot to the question panel.
COLUMN_COUNT = 4
COLUMN_WIDTH = 56
COLUMN_XS = (250, 400, 550, 700)
TOP, BOTTOM = 168, 462

# Room 3: three tripwire rows between the side walls, below the exit door's opening.
ROW_YS = (308, 368, 428)
ROW_THICKNESS = 18
ROW_LEFT, ROW_RIGHT = 64, 846

GRACE = 2.0                                 # nothing fires for this long after entering or a hit
WARN = 0.8
REST = 1.5

# Seconds between one lane firing and the next, and how long each stays live.
STEP = {"easy": 1.5, "medium": 1.2, "hard": 1.0}
LIVE_STEPS = {"easy": 1.3, "medium": 1.6, "hard": 2.0}   # how many steps a lane stays live: neighbours overlap

RED = (255, 45, 45)
CORE = (255, 190, 190)
AMBER = (255, 190, 60)


def layout_rects(layout):
    if layout == "rows":
        return [pygame.Rect(ROW_LEFT, y, ROW_RIGHT - ROW_LEFT, ROW_THICKNESS) for y in ROW_YS]
    return [pygame.Rect(x, TOP, COLUMN_WIDTH, BOTTOM - TOP) for x in COLUMN_XS]


class LaneLoop:
    """Timing and drawing of a lane loop."""

    def __init__(self, difficulty="medium", layout="columns"):
        self.layout = layout
        self.rects = layout_rects(layout)
        self.count = len(self.rects)
        self.step = STEP.get(difficulty, STEP["medium"])
        self.live = self.step * LIVE_STEPS.get(difficulty, LIVE_STEPS["medium"])
        self.cycle = self.count * self.step + self.live - self.step + REST
        self.clock = 0.0
        self._glow = {}

    # ---- timing ---------------------------------------------------------

    def update(self, dt):
        self.clock += max(0.0, dt)

    def rearm(self):
        """After a hit: the loop starts over with a fresh safe window."""
        self.clock = 0.0

    def phase(self, lane):
        """'off' (safe), 'warning' (safe, about to fire) or 'active'."""
        if self.clock < GRACE - WARN:
            return "off"
        if self.clock < GRACE:
            return "warning" if lane == 0 else "off"

        position = (self.clock - GRACE) % self.cycle
        start = lane * self.step

        if start <= position < start + self.live:
            return "active"
        if start - WARN <= position < start:
            return "warning"
        if lane == 0 and position >= self.cycle - WARN:
            return "warning"
        return "off"

    def phases(self):
        return [self.phase(lane) for lane in range(self.count)]

    def current_lane(self):
        """The lane the loop is on (the one that fired last), or None while resting."""
        if self.clock < GRACE:
            return None
        position = (self.clock - GRACE) % self.cycle
        if position >= (self.count - 1) * self.step + self.live:
            return None
        return min(self.count - 1, int(position // self.step))

    def resting(self):
        return self.clock >= GRACE and self.current_lane() is None

    def rect(self, lane):
        return self.rects[lane]

    def active_rects(self):
        return [self.rect(lane) for lane in range(self.count) if self.phase(lane) == "active"]

    def light_rects(self, origin):
        """(rect, phase) pieces for the room lighting, in room-local coordinates."""
        pieces = []
        for lane in range(self.count):
            phase = self.phase(lane)
            if phase == "off":
                continue
            rect = self.rect(lane).move(-origin[0], -origin[1])
            if rect.width > rect.height:
                for x in range(rect.left, rect.right, 130):
                    pieces.append((pygame.Rect(x, rect.y, min(130, rect.right - x), rect.height), phase))
            else:
                for y in range(rect.top, rect.bottom, 110):
                    pieces.append((pygame.Rect(rect.x, y, rect.width, min(110, rect.bottom - y)), phase))
        return pieces

    # ---- drawing --------------------------------------------------------

    def _glow_for(self, size):
        if size not in self._glow:
            glow = pygame.Surface((size[0] + 24, size[1] + 24), pygame.SRCALPHA)
            for pad, alpha in ((12, 16), (8, 30), (4, 52)):
                pygame.draw.rect(glow, (255, 50, 50, alpha), glow.get_rect().inflate(-(12 - pad) * 2, -(12 - pad) * 2),
                                 border_radius=12)
            self._glow[size] = glow
        return self._glow[size]

    def draw(self, surface, t):
        pulse = 0.5 + 0.5 * math.sin(t * 7.0)

        for lane in range(self.count):
            phase = self.phase(lane)
            rect = self.rect(lane)
            horizontal = rect.width > rect.height

            # the lane painted on the floor: dark plate with hazard edge strips
            plate = pygame.Surface(rect.size, pygame.SRCALPHA)
            plate.fill((10, 12, 22, 120))
            surface.blit(plate, rect.topleft)
            self._edge_strips(surface, rect, horizontal)

            inner = rect.inflate(0, -8) if horizontal else rect.inflate(-8, 0)

            if phase == "active":
                glow = self._glow_for(rect.size)
                glow.set_alpha(int(170 + 70 * pulse))
                surface.blit(glow, (rect.x - 12, rect.y - 12))
                pygame.draw.rect(surface, RED, inner)
                if horizontal:
                    pygame.draw.line(surface, CORE, (rect.left, rect.centery), (rect.right - 1, rect.centery), 2)
                else:
                    pygame.draw.line(surface, CORE, (rect.centerx, rect.top), (rect.centerx, rect.bottom - 1), 2)
                self._arcs(surface, rect, t, horizontal)
            elif phase == "warning":
                lit = int(t * 8) % 2 == 0
                pygame.draw.rect(surface, (110, 62, 30) if lit else (62, 32, 30), inner)
                dash = AMBER if lit else (150, 100, 45)
                if horizontal:
                    for x in range(rect.left, rect.right, 14):       # dashed: readable without colour
                        pygame.draw.rect(surface, dash, (x, inner.y, min(7, rect.right - x), inner.height))
                else:
                    for y in range(rect.top, rect.bottom, 14):
                        pygame.draw.rect(surface, dash, (inner.x, y, inner.width, min(7, rect.bottom - y)))

            self._caps(surface, rect, phase, horizontal)

    @staticmethod
    def _edge_strips(surface, rect, horizontal):
        if horizontal:
            for x in range(rect.left, rect.right, 16):
                shade = (150, 120, 40) if (x // 16) % 2 == 0 else (30, 28, 24)
                w = min(16, rect.right - x)
                pygame.draw.rect(surface, shade, (x, rect.top, w, 3))
                pygame.draw.rect(surface, shade, (x, rect.bottom - 3, w, 3))
        else:
            for y in range(rect.top, rect.bottom, 16):
                shade = (150, 120, 40) if (y // 16) % 2 == 0 else (30, 28, 24)
                h = min(16, rect.bottom - y)
                pygame.draw.rect(surface, shade, (rect.x, y, 4, h))
                pygame.draw.rect(surface, shade, (rect.right - 4, y, 4, h))

    @staticmethod
    def _arcs(surface, rect, t, horizontal):
        """Crackling lightning inside a live lane, redrawn a few times a second."""
        rng = random.Random(int(t * 18) * 31 + rect.x + rect.y)
        for _ in range(2):
            if horizontal:
                y = rect.centery + rng.randint(-3, 3)
                points = [(rect.left, y)]
                for x in range(rect.left + 14, rect.right, 14):
                    y = max(rect.y + 5, min(rect.bottom - 5, y + rng.randint(-5, 5)))
                    points.append((x, y))
            else:
                x = rect.centerx + rng.randint(-8, 8)
                points = [(x, rect.top)]
                for y in range(rect.top + 14, rect.bottom, 14):
                    x = max(rect.x + 8, min(rect.right - 8, x + rng.randint(-9, 9)))
                    points.append((x, y))
            pygame.draw.lines(surface, (255, 245, 245), False, points, 2)

    @staticmethod
    def _caps(surface, rect, phase, horizontal):
        lens = {"active": (255, 60, 60), "warning": AMBER, "off": (95, 95, 110)}[phase]
        if horizontal:
            caps = [pygame.Rect(rect.left - 12, rect.y - 4, 12, rect.height + 8),
                    pygame.Rect(rect.right, rect.y - 4, 12, rect.height + 8)]
        else:
            caps = [pygame.Rect(rect.x - 6, rect.top - 12, rect.width + 12, 12),
                    pygame.Rect(rect.x - 6, rect.bottom, rect.width + 12, 12)]
        for cap in caps:
            pygame.draw.rect(surface, (38, 34, 62), cap, border_radius=4)
            pygame.draw.rect(surface, theme.mix(lens, (38, 34, 62), 0.3), cap, 2, border_radius=4)
            pygame.draw.circle(surface, lens, cap.center, 3)
