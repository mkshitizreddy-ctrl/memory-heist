"""
levels/grid_decor.py
Owner: Member 1 - Core Game System

Geometry and art for Floor 2, the maintenance grid.  The room is three
chambers in a row, joined by a service lane:

      wall    [ screen 1 ]   [ screen 2 ]   [ screen 3 ]      <- the questions
      floor   racks, desk    racks, desk    racks, desk
      lane    spawn  ==gate 1==========gate 2============ exit door (gate 3)
      floor   [ answer pads ][ answer pads ][ answer pads ]

Each chamber's wall screen shows its gate's question; the answers are pads on
the floor.  Stand on one and press the action key.  Nothing here changes the
rules; level2_grid.py owns those.

Pure helpers (pad_rects, led_state, pulse_points, ...) hold the maths so it can
be tested without a window.
"""

import math
import random

import pygame

from core.tilemap import TILE
from levels.lobby_decor import Motes
from ui import theme
from ui.fonts import code_font, ui_font
from ui.kit import draw_panel, wrap_text

COLS, ROWS = 30, 20
WALL_ROWS = 6                      # rows 0..5 are wall: the screens hang there
LAST_ROW = 17                      # last row of floor
CHAMBERS = ((2, 9), (11, 18), (20, 27))     # first and last column of each chamber
PARTITIONS = (10, 19)              # the wall columns between chambers
LANE_ROWS = (10, 11, 12)           # the lane that runs through every gate
TOPICS = ("ARITHMETIC", "COMPARISON", "LOGIC")

SCREEN_Y, SCREEN_H, SCREEN_INSET = 100, 84, 8
PAD_W, PAD_H, PAD_GAP = 58, 52, 6
PAD_Y = 14 * TILE
GATE_RECTS = (pygame.Rect(PARTITIONS[0] * TILE, LANE_ROWS[0] * TILE, TILE, 3 * TILE),
              pygame.Rect(PARTITIONS[1] * TILE, LANE_ROWS[0] * TILE, TILE, 3 * TILE),
              pygame.Rect(28 * TILE, LANE_ROWS[0] * TILE, 2 * TILE, 3 * TILE))
SPAWNS = ((3 * TILE, 11 * TILE), (4 * TILE + 8, 11 * TILE))
MOTE_AREA = pygame.Rect(2 * TILE, 6 * TILE, 26 * TILE, 12 * TILE)
LEDS_PER_RACK = 6
PULSE_SECONDS = 4.0                # a data pulse crosses the lane in this long


# --- geometry ---------------------------------------------------------------
def screen_rect(gate):
    left = CHAMBERS[gate][0] * TILE
    return pygame.Rect(left + SCREEN_INSET, SCREEN_Y, (CHAMBERS[gate][1] - CHAMBERS[gate][0] + 1) * TILE
                       - 2 * SCREEN_INSET, SCREEN_H)


def rack_rects():
    out = []
    for first, _ in CHAMBERS:
        for dx in (1, 6):
            out.append(pygame.Rect((first + dx) * TILE, WALL_ROWS * TILE, TILE, 2 * TILE))
    return out


def desk_rects():
    return [pygame.Rect((first + 3) * TILE, 7 * TILE, 2 * TILE, TILE) for first, _ in CHAMBERS]


def pad_rects(gate, count):
    """`count` pads in a row, centred in chamber `gate`."""
    first, last = CHAMBERS[gate]
    total = count * PAD_W + (count - 1) * PAD_GAP
    x = (first * TILE + (last - first + 1) * TILE // 2) - total // 2
    return [pygame.Rect(x + i * (PAD_W + PAD_GAP), PAD_Y, PAD_W, PAD_H) for i in range(count)]


def layout_rows(cols=COLS, rows=ROWS):
    """Walls round the edge and between chambers, a lit lane through the middle."""
    out = []
    for y in range(rows):
        if y < WALL_ROWS or y > LAST_ROW:
            out.append("#" * cols)
            continue
        row = ["#", "#"] + ["."] * (cols - 4) + ["#", "#"]
        for col in PARTITIONS:
            row[col] = "#"
        if y in LANE_ROWS:
            for x in range(2, cols - 2):
                row[x] = ","
            for col in PARTITIONS:
                row[col] = ","
            row[cols - 2] = row[cols - 1] = "."
        out.append("".join(row))
    return out


# --- pure helpers -----------------------------------------------------------
def led_state(t, rack, led):
    """0 dark, 1 green, 2 amber: a rack's indicator lights, each on its own beat."""
    v = math.sin(t * (1.3 + 0.37 * ((rack + led) % 4)) + rack * 7 + led * 13)
    if v > 0.55:
        return 1
    if v < -0.85:
        return 2
    return 0


def pulse_points(t, start, end, count=3, seconds=PULSE_SECONDS):
    """Where `count` evenly spaced data pulses are on the line start -> end at time t."""
    out = []
    for k in range(count):
        u = (t / seconds + k / count) % 1.0
        out.append((start[0] + (end[0] - start[0]) * u, start[1] + (end[1] - start[1]) * u))
    return out


def timer_fraction(time_left, time_limit):
    if time_limit <= 0:
        return 0.0
    return max(0.0, min(1.0, time_left / time_limit))


def fit_font(text, max_width, sizes=(22, 20, 18, 16, 14)):
    """The biggest code font in `sizes` whose rendering of `text` fits `max_width`."""
    font = None
    for size in sizes:
        font = code_font(size)
        if font.size(text)[0] <= max_width:
            return font
    return font


def fit_prompt(prompt, width, sizes=(20, 19, 18), lines=2, smallest=17, smallest_lines=3):
    """(font, wrapped lines) for a screen prompt: the biggest font that fits `lines`
    lines, else the smallest font cut to `smallest_lines` lines."""
    for size in sizes:
        font = code_font(size)
        wrapped = wrap_text(prompt, font, width)
        if len(wrapped) <= lines:
            return font, wrapped
    font = code_font(smallest)
    return font, wrap_text(prompt, font, width)[:smallest_lines]


# --- baked decoration -------------------------------------------------------
def draw_static(bg, accent):
    metal = theme.mix(theme.SLATE, accent, 0.18)
    for gate in range(3):                                        # screen bezels
        r = screen_rect(gate)
        pygame.draw.rect(bg, theme.INK, r.inflate(10, 10), border_radius=6)
        pygame.draw.rect(bg, metal, r.inflate(10, 10), 2, border_radius=6)
    pipe_y = SCREEN_Y + SCREEN_H + 2                             # a pipe under the screens
    pygame.draw.rect(bg, theme.mix(metal, theme.INK, 0.45), (2 * TILE, pipe_y + 1, 26 * TILE, 5), border_radius=2)
    pygame.draw.rect(bg, theme.mix(metal, theme.PAPER, 0.25), (2 * TILE, pipe_y, 26 * TILE, 2))
    for x in range(2 * TILE + 24, 28 * TILE, 96):
        pygame.draw.rect(bg, theme.INK, (x, pipe_y - 1, 6, 8))
    for col in PARTITIONS:                                       # a valve wheel on each partition
        c = (col * TILE + TILE // 2, pipe_y + 3)
        pygame.draw.circle(bg, theme.INK, c, 9)
        pygame.draw.circle(bg, theme.CORAL, c, 7, 2)
        pygame.draw.line(bg, theme.CORAL, (c[0] - 6, c[1]), (c[0] + 6, c[1]), 2)
        pygame.draw.line(bg, theme.CORAL, (c[0], c[1] - 6), (c[0], c[1] + 6), 2)
    for rack in rack_rects():
        _draw_rack(bg, rack, metal)
        pygame.draw.line(bg, theme.mix(theme.INK, accent, 0.25),         # cable down to the lane
                         (rack.centerx, rack.bottom), (rack.centerx, LANE_ROWS[0] * TILE - 4), 3)
    for desk in desk_rects():
        draw_panel(bg, desk, fill=theme.mix(theme.NAVY, accent, 0.2), border=metal, radius=4, shadow=False)
        for i in range(4):
            pygame.draw.rect(bg, theme.mix(accent, theme.PAPER, 0.3 * (i % 2)),
                             (desk.x + 8 + i * 14, desk.y + 10, 8, 5), border_radius=1)
    lane = pygame.Rect(2 * TILE, LANE_ROWS[0] * TILE, 26 * TILE, 3 * TILE)
    for x in range(lane.left + 8, lane.right, 28):               # dashed centre line
        pygame.draw.line(bg, theme.mix(theme.GOLD, theme.INK, 0.35), (x, lane.centery), (x + 12, lane.centery), 2)
    for y in (lane.top, lane.bottom - 2):
        pygame.draw.line(bg, theme.mix(accent, theme.INK, 0.35), (lane.left, y), (lane.right, y), 2)
    for first, last in CHAMBERS:                                 # soft pools of light
        glow = _glow(150, theme.mix(theme.INK, accent, 0.28))
        bg.blit(glow, ((first + last + 1) * TILE // 2 - 150, SCREEN_Y + SCREEN_H // 2 - 40),
                special_flags=pygame.BLEND_RGB_ADD)
    for rect in GATE_RECTS[:2]:                                  # hazard stripes under the gates
        _hazard(bg, rect)
    _exit_sign(bg, accent)
    for gate, (first, last) in enumerate(CHAMBERS):              # bay stencils on the floor
        label = ui_font(16, bold=True).render(f"RELAY BAY {gate + 1} - {TOPICS[gate]}", True,
                                              theme.mix(theme.INK, accent, 0.55))
        bg.blit(label, label.get_rect(center=((first + last + 1) * TILE // 2, 17 * TILE - 14)))


def _hazard(bg, rect):
    """Diagonal warning stripes on the floor cell a gate stands in."""
    bg.fill(theme.mix(theme.INK, theme.GOLD, 0.1), rect)
    clip = bg.get_clip()
    bg.set_clip(rect)
    for x in range(rect.left - rect.h, rect.right, 14):
        pygame.draw.line(bg, theme.mix(theme.GOLD, theme.INK, 0.45), (x, rect.bottom), (x + rect.h, rect.top), 5)
    bg.set_clip(clip)


def _exit_sign(bg, accent):
    sign = pygame.Rect(28 * TILE + 4, 8 * TILE, 56, 26)
    pygame.draw.rect(bg, theme.INK, sign, border_radius=4)
    pygame.draw.rect(bg, theme.TEAL, sign, 2, border_radius=4)
    text = ui_font(16, bold=True).render("EXIT", True, theme.TEAL)
    bg.blit(text, text.get_rect(center=(sign.centerx - 6, sign.centery)))
    tip = [(sign.right - 14, sign.centery - 5), (sign.right - 14, sign.centery + 5), (sign.right - 7, sign.centery)]
    pygame.draw.polygon(bg, theme.TEAL, tip)


def draw_chevrons(surface, openness, time):
    """Arrows along the lane that run toward the exit once its door is opening."""
    if openness < 0.5:
        return
    y = LANE_ROWS[1] * TILE + TILE // 2
    for k in range(4):
        x = 23 * TILE + k * 36
        glow = ((time * 2.5 - k * 0.4) % 1.6) / 1.6
        colour = theme.mix(theme.INK, theme.TEAL, 0.25 + 0.75 * max(0.0, 1.0 - abs(glow - 0.3) * 2.2))
        pygame.draw.lines(surface, colour, False, [(x, y - 10), (x + 10, y), (x, y + 10)], 3)


def _glow(radius, colour):
    surf = pygame.Surface((radius * 2, radius * 2))
    for r in range(radius, 0, -3):
        k = (1.0 - r / radius) ** 2
        pygame.draw.circle(surf, tuple(int(c * k) for c in colour), (radius, radius), r)
    return surf


def _draw_rack(bg, rack, metal):
    pygame.draw.rect(bg, (0, 0, 0), rack.move(2, 3), border_radius=3)
    pygame.draw.rect(bg, theme.mix(metal, theme.INK, 0.55), rack, border_radius=3)
    pygame.draw.rect(bg, metal, rack, 2, border_radius=3)
    for i in range(3):                                           # vents
        y = rack.y + 36 + i * 7
        pygame.draw.line(bg, theme.mix(metal, theme.INK, 0.6), (rack.x + 6, y), (rack.right - 7, y), 2)


# --- per-frame drawing ------------------------------------------------------
def rack_led_positions(rack):
    return [(rack.x + 8 + (i % 3) * 8, rack.y + 8 + (i // 3) * 8) for i in range(LEDS_PER_RACK)]


class Ambience:
    def __init__(self, seed=0):
        self.time = 0.0
        self.motes = Motes(random.Random(seed), MOTE_AREA, count=14)

    def update(self, dt):
        dt = max(0.0, dt)
        self.time += dt
        self.motes.update(dt)

    def draw(self, world, accent):
        for i, rack in enumerate(rack_rects()):
            for j, pos in enumerate(rack_led_positions(rack)):
                state = led_state(self.time, i, j)
                colour = (theme.TEAL, theme.GOLD)[state - 1] if state else theme.mix(theme.INK, theme.SLATE, 0.5)
                pygame.draw.rect(world, colour, (pos[0], pos[1], 4, 4))
        lane_top, lane_bottom = LANE_ROWS[0] * TILE + 1, (LANE_ROWS[-1] + 1) * TILE - 3
        for start, end, y in (((2 * TILE, 0), (28 * TILE, 0), lane_top),
                              ((28 * TILE, 0), (2 * TILE, 0), lane_bottom)):
            for x, _ in pulse_points(self.time, start, end):
                pygame.draw.rect(world, theme.mix(accent, theme.PAPER, 0.5), (int(x) - 5, y, 10, 2))
        for m in self.motes.motes:
            twinkle = 0.5 + 0.5 * math.sin(self.time * 1.5 + m["phase"])
            world.set_at((int(m["x"]), int(m["y"])), theme.mix(theme.INK, theme.MIST, 0.25 + 0.5 * twinkle))


def draw_gate(surface, rect, openness, time):
    """An energy barrier between two posts; it retracts into them as it opens."""
    openness = max(0.0, min(1.0, openness))
    for y in (rect.top, rect.bottom - 10):
        pygame.draw.rect(surface, theme.SLATE, (rect.x + 4, y, rect.w - 8, 10), border_radius=3)
        pygame.draw.rect(surface, theme.MIST, (rect.x + 4, y, rect.w - 8, 10), 1, border_radius=3)
    reach = int((rect.h / 2 - 10) * (1.0 - openness))
    if reach <= 0:
        return
    shimmer = 0.5 + 0.5 * math.sin(time * 9)
    bars = max(2, rect.w // 8)
    for i in range(bars):
        x = rect.x + rect.w // 2 + int((i - (bars - 1) / 2) * 7)
        colour = theme.mix(theme.CORAL, theme.PAPER, 0.25 + 0.5 * ((shimmer + i * 0.37) % 1.0))
        pygame.draw.line(surface, colour, (x, rect.top + 10), (x, rect.top + 10 + reach), 2)
        pygame.draw.line(surface, colour, (x, rect.bottom - 10 - reach), (x, rect.bottom - 10), 2)


def draw_shutter(surface, rect, openness, lamp_colour):
    """The exit: two plates slide apart, a lamp beside them."""
    openness = max(0.0, min(1.0, openness))
    pygame.draw.rect(surface, theme.INK, rect)
    slide = int((rect.h // 2) * openness)
    for half in (pygame.Rect(rect.x, rect.y - slide, rect.w, rect.h // 2),
                 pygame.Rect(rect.x, rect.centery + slide, rect.w, rect.h // 2)):
        pygame.draw.rect(surface, theme.SLATE, half)
        pygame.draw.rect(surface, theme.MIST, half, 2)
    pygame.draw.circle(surface, lamp_colour, (rect.x - 10, rect.centery), 6)


def draw_screen(surface, rect, gate, state, accent, prompt="", answer="", fraction=1.0,
                seconds=0, time=0.0):
    """One wall screen.  state: "standby" (a gate ahead), "active", or "accepted"."""
    border = {"standby": theme.SLATE, "active": accent, "accepted": theme.TEAL}[state]
    pygame.draw.rect(surface, theme.mix(theme.INK, border, 0.12), rect, border_radius=4)
    pygame.draw.rect(surface, border, rect, 1, border_radius=4)
    head = ui_font(15, bold=True).render(f"RELAY {gate + 1}  {TOPICS[gate]}", True, border)
    surface.blit(head, (rect.x + 8, rect.y + 5))
    body = code_font(17)
    if state == "standby":
        text = body.render("STANDBY", True, theme.SLATE)
        surface.blit(text, text.get_rect(center=(rect.centerx, rect.centery + 6)))
        return
    if state == "accepted":
        ok = ui_font(22, bold=True).render("ACCEPTED", True, theme.TEAL)
        surface.blit(ok, ok.get_rect(center=(rect.centerx, rect.centery - 2)))
        result = body.render(f"answer: {answer}", True, theme.PAPER)
        surface.blit(result, result.get_rect(center=(rect.centerx, rect.centery + 22)))
        return
    y = rect.y + 24
    font, lines = fit_prompt(prompt, rect.w - 16)
    for line in lines:
        surface.blit(font.render(line, True, theme.PAPER), (rect.x + 8, y))
        y += font.get_linesize()
    bar = pygame.Rect(rect.x + 8, rect.bottom - 12, rect.w - 16, 5)
    pygame.draw.rect(surface, theme.mix(theme.INK, theme.SLATE, 0.5), bar, border_radius=2)
    low = fraction < 0.25
    colour = theme.mix(theme.CORAL, theme.PAPER, 0.5 + 0.5 * math.sin(time * 10)) if low else accent
    pygame.draw.rect(surface, colour, (bar.x, bar.y, int(bar.w * fraction), bar.h), border_radius=2)
    clock = code_font(14).render(f"{seconds}s", True, colour)
    surface.blit(clock, (rect.right - clock.get_width() - 8, rect.y + 6))


def draw_pad(surface, rect, label, state, accent, time=0.0):
    """An answer pad.  state: "idle", "stand" (a player is on it), "right", "wrong"."""
    fill = {"idle": theme.mix(theme.NAVY, accent, 0.25), "stand": theme.mix(theme.NAVY, accent, 0.5),
            "right": theme.mix(theme.NAVY, theme.TEAL, 0.6), "wrong": theme.mix(theme.NAVY, theme.CORAL, 0.6)}[state]
    edge = {"idle": accent, "stand": theme.PAPER, "right": theme.TEAL, "wrong": theme.CORAL}[state]
    pygame.draw.rect(surface, (0, 0, 0), rect.move(2, 3), border_radius=8)
    pygame.draw.rect(surface, fill, rect, border_radius=8)
    pygame.draw.rect(surface, edge, rect, 2, border_radius=8)
    if state == "stand":
        glow = 0.5 + 0.5 * math.sin(time * 8)
        pygame.draw.rect(surface, theme.mix(edge, theme.INK, 0.4 + 0.3 * glow), rect.inflate(8, 8), 2, border_radius=10)
    for sx in (rect.x + 8, rect.right - 11):                     # breaker plate: two screws and a lever slot
        pygame.draw.circle(surface, theme.mix(edge, theme.INK, 0.5), (sx, rect.y + 7), 2)
    pygame.draw.rect(surface, theme.mix(edge, theme.INK, 0.6), (rect.centerx - 7, rect.y + 5, 14, 4), border_radius=2)
    font = fit_font(label, rect.w - 8)
    text = font.render(label, True, theme.PAPER)
    surface.blit(text, text.get_rect(center=rect.center))
