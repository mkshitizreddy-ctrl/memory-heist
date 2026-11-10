"""
levels/badge_door.py
Owner: Member 5 (UI)

One door for every floor.  A locked door has a badge reader beside it; when the
answer is right the reader scans the courier's badge (a bright bar sweeps the
card), turns green, and the two steel leaves slide apart into the wall.

The level owns the logic.  It only has to hand this module one number:

    progress   0.0  locked
               0..SCAN_END   the reader is scanning
               SCAN_END..1   the leaves are sliding
               1.0  open

so the same picture works for a timed tween (Floor 1), a linear counter
(Floor 2) and a Gate's unlock timer (Floor 3).
"""

import math

import pygame

from ui import theme

SCAN_END = 0.42                      # share of the sequence spent scanning the badge
LOCKED = theme.CORAL
SCANNING = theme.GOLD
GRANTED = theme.TEAL
LEAF = (72, 82, 112)                 # steel
LEAF_DARK = (40, 48, 74)
JAMB = (30, 36, 58)
JAMB_CAP = 8                         # px of frame above and below the opening
READER_SIZE = (18, 38)


def _clamp(v):
    return max(0.0, min(1.0, v))


def scan_amount(progress):
    """0..1 over the scan part of the sequence."""
    return _clamp(progress / SCAN_END)


def slide_amount(progress):
    """0 (shut) .. 1 (fully open), eased, over the sliding part."""
    u = _clamp((progress - SCAN_END) / (1.0 - SCAN_END))
    return 1.0 - (1.0 - u) ** 3


def state(progress):
    if progress <= 0.0:
        return "locked"
    if progress < SCAN_END:
        return "scanning"
    if progress < 1.0:
        return "opening"
    return "open"


def lamp_colour(progress):
    s = state(progress)
    if s == "locked":
        return LOCKED
    if s == "scanning":
        return SCANNING
    return GRANTED


def reader_rect(door):
    """The badge reader sits on the approach side (left) of the door."""
    w, h = READER_SIZE
    return pygame.Rect(door.x - w - 6, door.centery - h // 2, w, h)


def _draw_reader(surface, door, progress, time):
    box = reader_rect(door)
    tone = lamp_colour(progress)
    pygame.draw.rect(surface, JAMB, box, border_radius=3)
    pygame.draw.rect(surface, theme.mix(tone, theme.INK, 0.35), box, 2, border_radius=3)
    screen = box.inflate(-6, -8)
    pygame.draw.rect(surface, theme.mix(tone, theme.INK, 0.8), screen)
    s = state(progress)

    if s == "locked":                                  # a closed padlock
        cx, cy = screen.center
        pygame.draw.arc(surface, tone, (cx - 4, cy - 9, 8, 10), 0, math.pi, 2)
        pygame.draw.rect(surface, tone, (cx - 5, cy - 2, 10, 8), border_radius=1)
        if int(time * 1.6) % 2 == 0:
            pygame.draw.circle(surface, tone, (box.centerx, box.top - 4), 2)    # slow blink above
    elif s == "scanning":                              # the badge, with a bright sweep across it
        card = pygame.Rect(0, 0, 10, 14)
        card.center = screen.center
        pygame.draw.rect(surface, theme.PAPER, card, border_radius=1)
        pygame.draw.rect(surface, theme.mix(tone, theme.INK, 0.2), (card.x + 1, card.y + 2, card.w - 2, 3))
        pygame.draw.circle(surface, theme.SLATE, (card.x + 3, card.y + 9), 2)
        y = screen.top + int(scan_amount(progress) * (screen.h - 2))
        pygame.draw.rect(surface, tone, (screen.x, y, screen.w, 2))
        glow = pygame.Surface((screen.w, 6), pygame.SRCALPHA)
        glow.fill((*tone, 70))
        surface.blit(glow, (screen.x, y - 2))
    else:                                              # access granted
        cx, cy = screen.center
        pygame.draw.lines(surface, tone, False, [(cx - 5, cy), (cx - 1, cy + 4), (cx + 6, cy - 5)], 3)


def _leaf(surface, area, tone, upper):
    """One steel leaf: panel lines and hazard stripes on the edge that meets the other leaf."""
    pygame.draw.rect(surface, LEAF, area)
    pygame.draw.rect(surface, theme.mix(LEAF, theme.PAPER, 0.18), area.inflate(-6, -6), 1)
    seam_y = area.bottom - 7 if upper else area.top
    for i in range(area.w // 6 + 1):                    # hazard stripes on the meeting edge
        x = area.x + i * 6
        colour = theme.GOLD if i % 2 == 0 else LEAF_DARK
        pygame.draw.rect(surface, colour, (x, seam_y, min(6, area.right - x), 7))
    mid = area.centery + (-6 if upper else 6)
    pygame.draw.line(surface, LEAF_DARK, (area.x + 3, mid), (area.right - 4, mid))
    pygame.draw.rect(surface, tone, (area.x + 3, area.y + 4 if upper else area.bottom - 7, 3, 3))   # status stud


def _draw_vents(surface, door, progress):
    """While the leaves slide, a little steam hisses out of each pocket and a glow lights the reader."""
    s = state(progress)
    if s == "opening":
        u = (progress - SCAN_END) / (1.0 - SCAN_END)
        layer = pygame.Surface((door.w + 24, 50), pygame.SRCALPHA)
        for sign in (-1, 1):
            base = door.top if sign < 0 else door.bottom
            for k in range(3):
                uu = (u - k * 0.15) / 0.65
                if 0 < uu < 1:
                    pos = (layer.get_width() // 2 + (k - 1) * 7, 25 + sign * int(4 + 16 * uu))
                    pygame.draw.circle(layer, (206, 212, 220, int(80 * (1 - uu))), pos, int(3 + 7 * uu))
            surface.blit(layer, (door.centerx - layer.get_width() // 2, base - 25))
            layer.fill((0, 0, 0, 0))
    if s != "locked":
        reader = reader_rect(door)
        halo = pygame.Surface((reader.w + 24, reader.h + 24), pygame.SRCALPHA)
        tone = lamp_colour(progress)
        pygame.draw.rect(halo, (*tone, 34), halo.get_rect(), border_radius=12)
        surface.blit(halo, (reader.x - 12, reader.y - 12))


def draw_badge_door(surface, door, progress, time):
    """Draw the door in the opening `door` (a vertical strip) for the given progress."""
    progress = _clamp(progress)
    tone = lamp_colour(progress)
    slide = slide_amount(progress)

    frame = door.inflate(6, JAMB_CAP * 2)
    pygame.draw.rect(surface, JAMB, frame)
    pygame.draw.rect(surface, theme.INK, door)                  # the dark gap behind the leaves

    half = door.h // 2
    shift = int(half * slide)
    previous = surface.get_clip()
    surface.set_clip(door)                                       # leaves vanish into the wall pockets
    _leaf(surface, pygame.Rect(door.x, door.y - shift, door.w, half), tone, upper=True)
    _leaf(surface, pygame.Rect(door.x, door.y + half + shift, door.w, door.h - half), tone, upper=False)
    surface.set_clip(previous)

    for y in (door.top - JAMB_CAP, door.bottom):                 # caps over the pockets
        pygame.draw.rect(surface, theme.mix(JAMB, theme.PAPER, 0.12), (frame.x, y, frame.w, JAMB_CAP))
        pygame.draw.rect(surface, theme.INK, (frame.x, y, frame.w, JAMB_CAP), 1)
        for dx in (3, frame.w - 5):
            surface.set_at((frame.x + dx, y + 3), tone)
    pygame.draw.rect(surface, theme.mix(tone, theme.INK, 0.4), frame, 1)

    if progress >= 1.0:                                          # open: a soft light spills out of the corridor
        spill = pygame.Surface(door.size, pygame.SRCALPHA)
        spill.fill((*GRANTED, 26 + int(14 * (0.5 + 0.5 * math.sin(time * 3)))))
        surface.blit(spill, door.topleft)

    _draw_vents(surface, door, progress)
    _draw_reader(surface, door, progress, time)
