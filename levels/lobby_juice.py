"""
levels/lobby_juice.py

Game feel for Floor 1. None of this changes a rule or a score: it only makes
what already happens easier to see and nicer to watch.

* Popups   floating "+10" / "-5" text that rises and fades
* Flyers   a filed parcel arcs into its chute, shrinking as it goes
* Streak   consecutive correct filings (display only)
* Chutes   pipes from the wall to each bin with chevrons flowing down; they
           flash when a parcel lands
* Fan      the slow shadow of a ceiling fan over the floor
* flicker  a tired fluorescent lamp
"""

import math

import pygame

POPUP_LIFE = 1.0
POPUP_RISE = 34                 # px travelled over a popup's life
FLYER_TIME = 0.38
FLYER_ARC = 46                  # px the parcel rises at the top of its arc
FLASH_DECAY = 3.0               # chute flash fades in ~1/3 s
STREAK_SHOWN_FROM = 2           # the streak counter appears at this many in a row
PIPE_WIDTH = 22
CHEVRON_GAP = 14
CHEVRON_SPEED = 26              # px per second, downward
FAN_BLADES = 4
FAN_SPEED = 1.4                 # radians per second
FAN_RADIUS = 150
FAN_ALPHA = 30


def flicker(t, seed=0.0):
    """Lamp brightness factor in [0.45, 1.0]: mostly steady, with brief stutters."""
    wave = math.sin(t * 2.3 + seed) + math.sin(t * 5.1 + seed * 2.0)
    dip = max(0.0, math.sin(t * 0.9 + seed * 3.0) - 0.9) * 10.0       # rare, short
    return max(0.45, min(1.0, 0.92 + 0.04 * wave - dip))


class Popup:
    def __init__(self, pos, text, colour):
        self.x, self.y = pos
        self.text = text
        self.colour = colour
        self.age = 0.0

    @property
    def alive(self):
        return self.age < POPUP_LIFE

    def position(self):
        return self.x, self.y - POPUP_RISE * (self.age / POPUP_LIFE)

    def alpha(self):
        k = self.age / POPUP_LIFE
        return int(255 * (1.0 if k < 0.6 else max(0.0, 1.0 - (k - 0.6) / 0.4)))


class Flyer:
    def __init__(self, start, end, label):
        self.start, self.end, self.label = start, end, label
        self.age = 0.0

    @property
    def done(self):
        return self.age >= FLYER_TIME

    def progress(self):
        return min(1.0, self.age / FLYER_TIME)

    def position(self):
        k = self.progress()
        x = self.start[0] + (self.end[0] - self.start[0]) * k
        y = self.start[1] + (self.end[1] - self.start[1]) * k - math.sin(math.pi * k) * FLYER_ARC
        return x, y

    def size(self):
        return max(6, int(28 * (1.0 - 0.65 * self.progress())))


class Juice:
    """Everything above, held together so a level needs one object and three calls."""

    def __init__(self):
        self.popups = []
        self.flyers = []
        self.flash = {}
        self.streak = 0
        self.best_streak = 0

    # --- events ----------------------------------------------------------
    def filed(self, start, end, kind, text, colour):
        self.flyers.append(Flyer(start, end, kind))
        self.popups.append(Popup((end[0], end[1] - 26), text, colour))
        self.flash[kind] = 1.0
        self.streak += 1
        self.best_streak = max(self.best_streak, self.streak)
        if self.streak >= 3:
            self.popups.append(Popup((end[0], end[1] - 46), f"x{self.streak}!", (255, 214, 120)))

    def missed(self, pos, text, colour):
        self.streak = 0
        self.popups.append(Popup(pos, text, colour))

    def pop(self, pos, text, colour):
        self.popups.append(Popup(pos, text, colour))

    # --- time ------------------------------------------------------------
    def update(self, dt):
        for p in self.popups:
            p.age += dt
        for f in self.flyers:
            f.age += dt
        self.popups = [p for p in self.popups if p.alive]
        self.flyers = [f for f in self.flyers if not f.done]
        for kind in list(self.flash):
            self.flash[kind] = max(0.0, self.flash[kind] - FLASH_DECAY * dt)
            if self.flash[kind] == 0.0:
                del self.flash[kind]

    # --- drawing ---------------------------------------------------------
    def draw_flyers(self, surface, font):
        for f in self.flyers:
            size = f.size()
            r = pygame.Rect(0, 0, size, size)
            r.center = f.position()
            pygame.draw.rect(surface, (150, 104, 62), r, border_radius=3)
            pygame.draw.rect(surface, (214, 164, 104), r, 2, border_radius=3)
            pygame.draw.line(surface, (110, 74, 44), (r.centerx, r.top), (r.centerx, r.bottom), 2)

    def draw_popups(self, surface, font, shadow=(10, 12, 20)):
        for p in self.popups:
            img = font.render(p.text, True, p.colour)
            back = font.render(p.text, True, shadow)
            img.set_alpha(p.alpha())
            back.set_alpha(p.alpha())
            x, y = p.position()
            rect = img.get_rect(center=(int(x), int(y)))
            surface.blit(back, rect.move(1, 1))
            surface.blit(img, rect)

    def streak_visible(self):
        return self.streak >= STREAK_SHOWN_FROM


def draw_chute(surface, bin_rect, colour, top_y, t, flash=0.0):
    """A pipe from the wall (`top_y`) down to the bin, chevrons flowing toward it."""
    pipe = pygame.Rect(0, top_y, PIPE_WIDTH, max(0, bin_rect.top - top_y + 2))
    pipe.centerx = bin_rect.centerx
    if pipe.h <= 0:
        return pipe
    body = tuple(int(c * 0.28 + 18) for c in colour)
    pygame.draw.rect(surface, body, pipe)
    pygame.draw.rect(surface, tuple(int(c * 0.55) for c in colour), pipe, 2)
    offset = (t * CHEVRON_SPEED) % CHEVRON_GAP
    chevron = tuple(min(255, int(c * (0.55 + 0.45 * flash))) for c in colour)
    y = pipe.top + offset
    while y < pipe.bottom - 4:
        cx = pipe.centerx
        pygame.draw.lines(surface, chevron, False, [(cx - 5, y), (cx, y + 4), (cx + 5, y)], 2)
        y += CHEVRON_GAP
    if flash > 0:
        glow = pygame.Surface(pipe.size, pygame.SRCALPHA)
        glow.fill((*colour, int(110 * flash)))
        surface.blit(glow, pipe)
    return pipe


def draw_fan_shadow(surface, centre, t, radius=FAN_RADIUS, alpha=FAN_ALPHA):
    """The shadow of a slowly turning ceiling fan, a few translucent blades."""
    layer = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
    c = radius
    for i in range(FAN_BLADES):
        a = t * FAN_SPEED + i * (2 * math.pi / FAN_BLADES)
        tip = (c + math.cos(a) * radius * 0.95, c + math.sin(a) * radius * 0.95)
        w = 0.16
        left = (c + math.cos(a - w) * radius * 0.30, c + math.sin(a - w) * radius * 0.30)
        right = (c + math.cos(a + w) * radius * 0.30, c + math.sin(a + w) * radius * 0.30)
        pygame.draw.polygon(layer, (0, 0, 0, alpha), [left, tip, right])
    pygame.draw.circle(layer, (0, 0, 0, alpha + 10), (c, c), 10)
    surface.blit(layer, (centre[0] - radius, centre[1] - radius))
