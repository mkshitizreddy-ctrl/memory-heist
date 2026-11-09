"""
levels/snake_decor.py
Owner: Member 1 - Core Game System

Geometry and art for Floor 2, the maintenance grid, rebuilt as a utility tunnel
that snakes back and forth.  Power runs through three relay corridors:

      wall     [ relay 1 ]      [ relay 2 ]      [ relay 3 ]        <- the questions
      corr. 1  spawn ==========================>= gate 1 |v
      corr. 2          gate 2 =<===========================  v
      corr. 3  v-------------------------------------------> exit shutter

Each corridor holds the breaker plates (answers) for its relay.  Power gate 1
ends corridor 1, a shaft drops to corridor 2, gate 2 ends it at the far west,
a shaft drops to corridor 3 and the exit shutter is its east end.  Nothing here
changes the rules; level2_grid.py owns those.

Floors 5 and the Final Vault still use levels/grid_decor.py (the straight hall);
this module reuses its shared pieces (screens, plates, gates, helpers).
"""

import math
import random

import pygame

from core.tilemap import TILE
from levels.grid_decor import (                                    # shared pieces, re-exported for the level
    _draw_rack, _glow, _hazard, draw_gate, draw_pad, draw_screen, draw_shutter, fit_font, fit_prompt,
    led_state, pulse_points, rack_led_positions, timer_fraction)
from levels.lobby_decor import Motes
from ui import theme
from ui.fonts import code_font, ui_font          # noqa: F401  (code_font re-exported for tests)
from ui.kit import draw_panel


COLS, ROWS = 30, 20
WALL_ROWS = 6                      # rows 0..5 are wall: the relay screens hang there
LAST_ROW = 17                      # last row of floor
SCREEN_COLS = ((2, 9), (11, 18), (20, 27))  # first and last column of each relay screen
TOPICS = ("ARITHMETIC", "COMPARISON", "LOGIC")

# The utility tunnel is a snake of three corridors, one per relay:
#   corridor 1 runs east to power gate 1, a shaft drops to
#   corridor 2 which runs west to power gate 2, a shaft drops to
#   corridor 3 which runs east to the exit shutter.
BANDS = ((6, 9), (11, 13), (15, 17))        # first and last floor row of each corridor
SEPARATORS = (10, 14)                       # the wall rows between corridors
SHAFTS = ((26, 27), (2, 3))                 # the columns where each separator is open
LANE_ROW = (8, 12, 16)                      # the lit centre row of each corridor
FLOW = (1, -1, 1)                           # which way the power flows: east, west, east
PAD_CENTRE_X = (12 * TILE, 15 * TILE, 16 * TILE)

SCREEN_Y, SCREEN_H, SCREEN_INSET = 100, 84, 8
PAD_W, PAD_H, PAD_GAP = 58, 52, 6
PAD_YS = tuple(first * TILE + (last - first + 1) * TILE // 2 - PAD_H // 2 for first, last in BANDS)
GATE_RECTS = (pygame.Rect(24 * TILE, BANDS[0][0] * TILE, TILE, 4 * TILE),
              pygame.Rect(5 * TILE, BANDS[1][0] * TILE, TILE, 3 * TILE),
              pygame.Rect(28 * TILE, BANDS[2][0] * TILE, 2 * TILE, 3 * TILE))
SPAWNS = ((3 * TILE, LANE_ROW[0] * TILE), (4 * TILE + 8, LANE_ROW[0] * TILE))
MOTE_AREA = pygame.Rect(2 * TILE, 6 * TILE, 26 * TILE, 12 * TILE)
LEDS_PER_RACK = 6
PULSE_SECONDS = 4.0                # a power pulse crosses a corridor in this long


# --- geometry ---------------------------------------------------------------
def screen_rect(gate):
    left = SCREEN_COLS[gate][0] * TILE
    return pygame.Rect(left + SCREEN_INSET, SCREEN_Y, (SCREEN_COLS[gate][1] - SCREEN_COLS[gate][0] + 1) * TILE
                       - 2 * SCREEN_INSET, SCREEN_H)


def rack_rects():
    """Breaker cabinets on the north wall of corridor 1."""
    return [pygame.Rect(col * TILE, BANDS[0][0] * TILE, TILE, 2 * TILE) for col in (6, 19)]


def desk_rects():
    """The engineer's workbench, against the north wall of corridor 1."""
    return [pygame.Rect(11 * TILE, BANDS[0][0] * TILE, 2 * TILE, TILE)]


def transformer_rects():
    """Two transformer blocks on the south wall of corridor 3."""
    return [pygame.Rect(col * TILE, BANDS[2][1] * TILE, 2 * TILE, TILE) for col in (6, 22)]


def pad_rects(gate, count):
    """`count` breaker plates in a row, centred in corridor `gate`."""
    total = count * PAD_W + (count - 1) * PAD_GAP
    x = PAD_CENTRE_X[gate] - total // 2
    return [pygame.Rect(x + i * (PAD_W + PAD_GAP), PAD_YS[gate], PAD_W, PAD_H) for i in range(count)]


def layout_rows(cols=COLS, rows=ROWS):
    """Walls round the edge and between the three corridors, a shaft joining each pair."""
    out = []
    for y in range(rows):
        if y < WALL_ROWS or y > LAST_ROW:
            out.append("#" * cols)
            continue
        row = ["#", "#"] + ["."] * (cols - 4) + ["#", "#"]
        if y in SEPARATORS:
            row = ["#"] * cols
            lo, hi = SHAFTS[SEPARATORS.index(y)]
            for x in range(lo, hi + 1):
                row[x] = ","
        elif y in LANE_ROW:
            for x in range(2, cols - 2):
                row[x] = ","
        if BANDS[2][0] <= y <= BANDS[2][1]:                      # the exit gap
            row[cols - 2] = row[cols - 1] = "."
        out.append("".join(row))
    return out


# --- live floor panels: the operators in action ----------------------------------
# A panel is live when its expression is true for the tick counter n, and a live
# panel zaps whoever stands on it (score only, never security).  Reading the
# operator tells you when it is safe to cross.
PANEL_STEP = 1.2                     # seconds per tick of the counter n
PANEL_EXPRS = (("n % 3 == 0", lambda n: n % 3 == 0),     # corridor 1: live one tick in three
               ("n % 2 == 1", lambda n: n % 2 == 1),     # corridor 2: live every other tick
               ("n % 3 != 0", lambda n: n % 3 != 0))     # corridor 3: live two ticks in three
PANEL_COLS = (20, 21, 8)             # first column of each corridor's panel (3 tiles wide)


def panel_rects():
    """One live panel across each corridor, full height so it has to be timed."""
    return [pygame.Rect(col * TILE, first * TILE, 3 * TILE, (last - first + 1) * TILE)
            for col, (first, last) in zip(PANEL_COLS, BANDS)]


def tick(t):
    """The counter n the panels read: one step every PANEL_STEP seconds."""
    return int(max(0.0, t) / PANEL_STEP)


def panel_live(corridor, n):
    return PANEL_EXPRS[corridor][1](n)


def panel_at(rect):
    """Index of the panel whose floor `rect` stands on (by its centre), or None."""
    for i, panel in enumerate(panel_rects()):
        if panel.collidepoint(rect.center):
            return i
    return None


def draw_floor_panel(surface, rect, expr, live, t):
    """A floor panel: dark with its expression when safe, crackling coral-white when live."""
    base = theme.mix(theme.INK, theme.SLATE, 0.35)
    pygame.draw.rect(surface, base, rect)
    for x in range(rect.left, rect.right, 12):                     # grating bars
        pygame.draw.line(surface, theme.mix(base, theme.INK, 0.5), (x, rect.top), (x, rect.bottom), 1)
    edge = theme.CORAL if live else theme.mix(theme.GOLD, theme.INK, 0.45)
    pygame.draw.rect(surface, edge, rect, 2)
    if live:
        pulse = 0.5 + 0.5 * math.sin(t * 18)
        pygame.draw.rect(surface, theme.mix(theme.CORAL, theme.PAPER, 0.3 + 0.4 * pulse), rect.inflate(-8, -8), 2)
        rng = random.Random(int(t * 14))                           # arcs that jump between frames
        for _ in range(4):
            x = rng.randint(rect.left + 6, rect.right - 6)
            pts = [(x, rect.top + 4)]
            for k in range(1, 5):
                pts.append((x + rng.randint(-9, 9), rect.top + 4 + k * (rect.h - 8) // 4))
            pygame.draw.lines(surface, theme.PAPER, False, pts, 2)
    label = ui_font(15, bold=True).render(expr, True, theme.PAPER if live else theme.GOLD)
    plate = label.get_rect(center=(rect.centerx, rect.top + 14)).inflate(8, 4)
    pygame.draw.rect(surface, theme.INK, plate, border_radius=3)
    surface.blit(label, label.get_rect(center=plate.center))


def draw_tick_plates(surface, n):
    """The counter n on each separator wall, so a player can read the panels."""
    for sep, col in zip(SEPARATORS, (8, 22)):
        plate = pygame.Rect(col * TILE, sep * TILE + 5, 4 * TILE, 22)
        pygame.draw.rect(surface, theme.INK, plate, border_radius=3)
        pygame.draw.rect(surface, theme.GOLD, plate, 1, border_radius=3)
        text = ui_font(15, bold=True).render(f"COUNTER  n = {n}", True, theme.GOLD)
        surface.blit(text, text.get_rect(center=plate.center))


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
    for sep, col in zip(SEPARATORS, (14, 20)):                   # a valve wheel set in each separator wall
        c = (col * TILE + TILE // 2, sep * TILE + TILE // 2)
        pygame.draw.circle(bg, theme.INK, c, 9)
        pygame.draw.circle(bg, theme.CORAL, c, 7, 2)
        pygame.draw.line(bg, theme.CORAL, (c[0] - 6, c[1]), (c[0] + 6, c[1]), 2)
        pygame.draw.line(bg, theme.CORAL, (c[0], c[1] - 6), (c[0], c[1] + 6), 2)
    for rack in rack_rects():
        _draw_rack(bg, rack, metal)
        pygame.draw.line(bg, theme.mix(theme.INK, accent, 0.25),         # cable down to the lane
                         (rack.centerx, rack.bottom), (rack.centerx, LANE_ROW[0] * TILE + 4), 3)
    for desk in desk_rects():
        draw_panel(bg, desk, fill=theme.mix(theme.NAVY, accent, 0.2), border=metal, radius=4, shadow=False)
        for i in range(4):
            pygame.draw.rect(bg, theme.mix(accent, theme.PAPER, 0.3 * (i % 2)),
                             (desk.x + 8 + i * 12, desk.y + 10, 7, 5), border_radius=1)
    for block in transformer_rects():
        _draw_transformer(bg, block, metal)
    for row in LANE_ROW:                                         # the lit lane of each corridor
        lane = pygame.Rect(2 * TILE, row * TILE, 26 * TILE, TILE)
        for x in range(lane.left + 8, lane.right, 28):           # dashed centre line
            pygame.draw.line(bg, theme.mix(theme.GOLD, theme.INK, 0.35), (x, lane.centery), (x + 12, lane.centery), 2)
        for y in (lane.top, lane.bottom - 2):
            pygame.draw.line(bg, theme.mix(accent, theme.INK, 0.35), (lane.left, y), (lane.right, y), 2)
    for sep, (lo, hi) in zip(SEPARATORS, SHAFTS):                # arrows down each shaft
        cx = (lo + hi + 1) * TILE // 2
        pygame.draw.polygon(bg, theme.mix(theme.GOLD, theme.INK, 0.4),
                            [(cx - 8, sep * TILE + 9), (cx + 8, sep * TILE + 9), (cx, sep * TILE + 23)])
    for first, last in SCREEN_COLS:                              # soft pools of light under the screens
        glow = _glow(150, theme.mix(theme.INK, accent, 0.28))
        bg.blit(glow, ((first + last + 1) * TILE // 2 - 150, SCREEN_Y + SCREEN_H // 2 - 40),
                special_flags=pygame.BLEND_RGB_ADD)
    for rect in GATE_RECTS[:2]:                                  # hazard stripes under the gates
        _hazard(bg, rect)
    _exit_sign(bg, accent)
    for gate, (_, last) in enumerate(BANDS):                     # relay stencils on the floor
        label = ui_font(16, bold=True).render(f"RELAY BAY {gate + 1} - {TOPICS[gate]}", True,
                                              theme.mix(theme.INK, accent, 0.55))
        bg.blit(label, label.get_rect(center=(PAD_CENTRE_X[gate], (last + 1) * TILE - 10)))


def _draw_transformer(bg, rect, metal):
    pygame.draw.rect(bg, (0, 0, 0), rect.move(2, 3), border_radius=3)
    pygame.draw.rect(bg, theme.mix(metal, theme.INK, 0.5), rect, border_radius=3)
    pygame.draw.rect(bg, metal, rect, 2, border_radius=3)
    for x in range(rect.x + 8, rect.right - 6, 8):               # cooling fins
        pygame.draw.line(bg, theme.mix(metal, theme.INK, 0.65), (x, rect.y + 5), (x, rect.bottom - 6), 2)


def _exit_sign(bg, accent):
    sign = pygame.Rect(28 * TILE + 4, SEPARATORS[1] * TILE + 3, 56, 26)
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
    y = LANE_ROW[2] * TILE + TILE // 2
    for k in range(4):
        x = 23 * TILE + k * 36
        glow = ((time * 2.5 - k * 0.4) % 1.6) / 1.6
        colour = theme.mix(theme.INK, theme.TEAL, 0.25 + 0.75 * max(0.0, 1.0 - abs(glow - 0.3) * 2.2))
        pygame.draw.lines(surface, colour, False, [(x, y - 10), (x + 10, y), (x, y + 10)], 3)


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
        for row, flow in zip(LANE_ROW, FLOW):                    # power flows along each corridor, east / west / east
            start, end = (3 * TILE, 26 * TILE) if flow > 0 else (26 * TILE, 3 * TILE)
            for x, _ in pulse_points(self.time, (start, 0), (end, 0)):
                pygame.draw.rect(world, theme.mix(accent, theme.PAPER, 0.5), (int(x) - 5, row * TILE + 4, 10, 2))
        for m in self.motes.motes:
            twinkle = 0.5 + 0.5 * math.sin(self.time * 1.5 + m["phase"])
            world.set_at((int(m["x"]), int(m["y"])), theme.mix(theme.INK, theme.MIST, 0.25 + 0.5 * twinkle))


