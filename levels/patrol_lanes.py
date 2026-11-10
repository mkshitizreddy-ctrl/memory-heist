"""
levels/patrol_lanes.py
Owner: Member 5 (UI)

Floor 3, Room 1 - the lane loop.  The wall board shows

    for lane in range(4):
        zap(lane)
    rest()

and the floor does exactly that: four electric lanes fire one after another,
then the loop ends and the corridor rests before it starts again.  This module
holds the timing, the danger rectangles and the drawing; Level 3 only asks it
which rectangles are live and tells it when a hit re-arms the loop.
"""

import math
import random

import pygame

from ui import theme

LANE_COUNT = 4
LANE_WIDTH = 56
LANE_XS = (250, 400, 550, 700)             # screen x of each lane's left edge
TOP, BOTTOM = 168, 462                      # caps sit between the wall's foot and the question panel
GRACE = 2.0                                 # nothing fires for this long after entering or a hit
WARN = 0.8
REST = 1.5

# Seconds between one lane firing and the next, and how long each stays live.
STEP = {"easy": 1.5, "medium": 1.2, "hard": 1.0}
LIVE_STEPS = {"easy": 1.3, "medium": 1.6, "hard": 2.0}   # how many steps a lane stays live: neighbours overlap

RED = (255, 45, 45)
CORE = (255, 190, 190)
AMBER = (255, 190, 60)


class LaneLoop:
    """Timing and drawing of the four-lane loop."""

    def __init__(self, difficulty="medium"):
        self.step = STEP.get(difficulty, STEP["medium"])
        self.live = self.step * LIVE_STEPS.get(difficulty, LIVE_STEPS["medium"])
        self.cycle = LANE_COUNT * self.step + self.live - self.step + REST
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
        return [self.phase(lane) for lane in range(LANE_COUNT)]

    def current_lane(self):
        """The lane the loop is on (the one that fired last), or None while resting."""
        if self.clock < GRACE:
            return None
        position = (self.clock - GRACE) % self.cycle
        lane = min(LANE_COUNT - 1, int(position // self.step))
        if position >= (LANE_COUNT - 1) * self.step + self.live:
            return None
        return lane

    def resting(self):
        return self.clock >= GRACE and self.current_lane() is None

    def rect(self, lane):
        return pygame.Rect(LANE_XS[lane], TOP, LANE_WIDTH, BOTTOM - TOP)

    def active_rects(self):
        return [self.rect(lane) for lane in range(LANE_COUNT) if self.phase(lane) == "active"]

    def light_rects(self, origin):
        """(rect, phase) pieces for the room lighting, in room-local coordinates."""
        pieces = []
        for lane in range(LANE_COUNT):
            phase = self.phase(lane)
            if phase == "off":
                continue
            rect = self.rect(lane).move(-origin[0], -origin[1])
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

        for lane in range(LANE_COUNT):
            phase = self.phase(lane)
            rect = self.rect(lane)

            # the lane painted on the floor: dark plate with hazard edge strips
            plate = pygame.Surface(rect.size, pygame.SRCALPHA)
            plate.fill((10, 12, 22, 120))
            surface.blit(plate, rect.topleft)
            for y in range(rect.top, rect.bottom, 16):
                shade = (150, 120, 40) if (y // 16) % 2 == 0 else (30, 28, 24)
                pygame.draw.rect(surface, shade, (rect.x, y, 4, min(16, rect.bottom - y)))
                pygame.draw.rect(surface, shade, (rect.right - 4, y, 4, min(16, rect.bottom - y)))

            if phase == "active":
                glow = self._glow_for(rect.size)
                glow.set_alpha(int(170 + 70 * pulse))
                surface.blit(glow, (rect.x - 12, rect.y - 12))
                inner = rect.inflate(-8, 0)
                pygame.draw.rect(surface, RED, inner)
                pygame.draw.line(surface, CORE, (rect.centerx, rect.top), (rect.centerx, rect.bottom - 1), 2)
                self._arcs(surface, rect, t)
            elif phase == "warning":
                lit = int(t * 8) % 2 == 0
                inner = rect.inflate(-8, 0)
                pygame.draw.rect(surface, (110, 62, 30) if lit else (62, 32, 30), inner)
                for y in range(rect.top, rect.bottom, 14):       # dashed: readable without colour
                    pygame.draw.rect(surface, AMBER if lit else (150, 100, 45),
                                     (rect.x + 4, y, rect.width - 8, min(7, rect.bottom - y)))

            self._caps(surface, rect, lane, phase)

    def _arcs(self, surface, rect, t):
        """Crackling lightning inside a live lane, redrawn a few times a second."""
        rng = random.Random(int(t * 18) * 31 + rect.x)
        for _ in range(2):
            x = rect.centerx + rng.randint(-8, 8)
            points = [(x, rect.top)]
            for y in range(rect.top + 14, rect.bottom, 14):
                x = max(rect.x + 8, min(rect.right - 8, x + rng.randint(-9, 9)))
                points.append((x, y))
            pygame.draw.lines(surface, (255, 245, 245), False, points, 2)

    def _caps(self, surface, rect, lane, phase):
        lens = {"active": (255, 60, 60), "warning": AMBER, "off": (95, 95, 110)}[phase]
        for y in (rect.top - 12, rect.bottom):
            cap = pygame.Rect(rect.x - 6, y, rect.width + 12, 12)
            pygame.draw.rect(surface, (38, 34, 62), cap, border_radius=4)
            pygame.draw.rect(surface, theme.mix(lens, (38, 34, 62), 0.3), cap, 2, border_radius=4)
            pygame.draw.circle(surface, lens, cap.center, 3)
