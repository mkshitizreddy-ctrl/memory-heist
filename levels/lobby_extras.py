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
CHIP_SPOTS = [(4, 5), (25, 9), (10, 13), (23, 10), (14, 9), (6, 16), (21, 14)]

VENDING_POINTS = 5
BELL_LINES = ("Ding! Sign in, please.", "One moment, visitor.", "Please stop ringing that.")
VENDING_LINE = "A cold coffee drops out. +5"
VENDING_EMPTY = "Sold out."

# Filing cabinets hold the intake manifests; E reads one (the chute rules).
MANIFEST_OFF = "Manifest sealed on this difficulty."
MANIFEST_TITLE = "Manifest {n}: "
# The water cooler is where the staff talk.
COOLER_LINES = ("Cold water. Nobody mentions the cameras.",
                "Someone taped a note: 'Blink less.'",
                "The cooler hums. So do the walls.")
# The sofa is the visitor waiting area: the sign taped above it is the joke.
SOFA_LINES = ("Visitors waiting: 212. Estimated wait: unknown.",
              "The cushion is still warm. Nobody is here.",
              "Sign-in sheet: every name is crossed out.")
# The guard and the receptionist trade a line when he passes her desk.
BANTER_GAP = 22.0
BANTER_RANGE = 70
BANTER = (("Quiet shift.", "Quiet is on file."),
          ("Anyone in?", "Only the courier."),
          ("Coffee later?", "Sold out. Again."))

# The reception phone: it rings now and then and the receptionist takes the call.
PHONE_FIRST_AT = 12.0
PHONE_EVERY = 31.0
RING_TIME = 2.2
CALL_LINES = ("NovaCorp reception.", "Yes. No. Please hold.", "He is not in. Nobody is.",
              "All calls are recorded.")


class Phone:
    """Rings every so often; at the end of the ring the receptionist picks up.

    update(dt) returns "ring" when the ringing starts and again halfway through
    (play the sound), "answer" when the call is taken (speak line()), else None.
    """

    def __init__(self):
        self.clock = PHONE_FIRST_AT
        self.ringing = 0.0
        self.calls = 0

    @property
    def is_ringing(self):
        return self.ringing > 0.0

    def line(self):
        return CALL_LINES[(self.calls - 1) % len(CALL_LINES)]

    def update(self, dt):
        if self.ringing > 0.0:
            before = self.ringing
            self.ringing = max(0.0, self.ringing - dt)
            if self.ringing == 0.0:
                self.calls += 1
                return "answer"
            if before > RING_TIME / 2 >= self.ringing:
                return "ring"
            return None
        self.clock -= dt
        if self.clock <= 0.0:
            self.clock = PHONE_EVERY
            self.ringing = RING_TIME
            return "ring"
        return None


def draw_phone(surf, desk, ringing, t):
    """The desk phone: a handset on a base; it shakes and shows ring arcs while ringing."""
    x, y = desk.x + 100, desk.y - 4
    shake = int(math.sin(t * 40) * 1.5) if ringing else 0
    pygame.draw.rect(surf, theme.INK, (x - 9, y - 5, 18, 7), border_radius=2)
    pygame.draw.rect(surf, theme.SLATE, (x - 9, y - 5, 18, 7), 1, border_radius=2)
    pygame.draw.rect(surf, (30, 32, 40), (x - 8 + shake, y - 10, 16, 5), border_radius=2)       # handset
    pygame.draw.rect(surf, theme.MIST, (x - 8 + shake, y - 10, 16, 5), 1, border_radius=2)
    if ringing:
        for r, a in ((6, 200), (10, 140)):
            arc = pygame.Rect(0, 0, r * 2, r * 2)
            arc.center = (x, y - 12)
            pygame.draw.arc(surf, theme.mix(theme.GOLD, theme.INK, 1 - a / 255), arc, 0.5, 2.6, 2)


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
    """A lost visitor badge: a clipped card on a lanyard with a teal stripe, a photo and text lines."""
    bob = int(math.sin(t * 3 + chip.phase) * 2)
    sway = int(round(math.sin(t * 2 + chip.phase) * 1.5))
    c = chip.rect.move(0, bob).center
    glow = 0.5 + 0.5 * math.sin(t * 5 + chip.phase)
    halo = pygame.Surface((40, 40), pygame.SRCALPHA)
    pygame.draw.circle(halo, (*theme.TEAL, int(40 + 50 * glow)), (20, 20), 18)
    surf.blit(halo, (c[0] - 20, c[1] - 20))
    card = pygame.Rect(0, 0, 14, 18)
    card.center = (c[0] + sway, c[1] + 1)
    pygame.draw.rect(surf, theme.INK, card.inflate(2, 2), border_radius=2)
    pygame.draw.rect(surf, theme.PAPER, card, border_radius=2)
    pygame.draw.rect(surf, theme.mix(theme.TEAL, theme.PAPER, glow * 0.3), (card.x, card.y, card.w, 5), border_top_left_radius=2, border_top_right_radius=2)
    pygame.draw.rect(surf, theme.SLATE, (card.x + 2, card.y + 7, 5, 5))                        # photo
    for ly in (card.y + 8, card.y + 11, card.y + 14):
        pygame.draw.line(surf, theme.MIST, (card.x + 8, ly), (card.right - 2, ly), 1)
    pygame.draw.rect(surf, theme.INK, (card.centerx - 2, card.y - 4, 4, 4))                     # clip
    pygame.draw.line(surf, theme.CORAL, (card.centerx, card.y - 4), (card.centerx + 3, card.y - 9), 1)  # lanyard
