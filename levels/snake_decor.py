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
    _draw_rack, _glow, _hazard, draw_gate, draw_pad, draw_screen as _shared_screen, draw_shutter, fit_font, fit_prompt,
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


FUSE_BOX = pygame.Rect(4 * TILE + 8, SEPARATORS[0] * TILE + 3, 44, 26)      # spare fuses, wall of corridor 1/2
POSTER = pygame.Rect(12 * TILE, SEPARATORS[1] * TILE + 3, 52, 26)           # the safety poster, wall of corridor 2/3
STEAM_VENTS = tuple((col * TILE + TILE // 2, sep * TILE + TILE // 2) for sep, col in zip(SEPARATORS, (14, 20)))


def rack_rects():
    """Breaker cabinets on the north wall of corridor 1."""
    return [pygame.Rect(col * TILE, BANDS[0][0] * TILE, TILE, 2 * TILE) for col in (6, 17)]


def desk_rects():
    """The engineer's workbench, against the north wall of corridor 1."""
    return [pygame.Rect(11 * TILE, BANDS[0][0] * TILE, 2 * TILE, TILE)]


def transformer_rects():
    """Two transformer blocks on the south wall of corridor 3."""
    return [pygame.Rect(col * TILE, BANDS[2][1] * TILE, 2 * TILE, TILE) for col in (4, 22)]


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
# Each corridor has a crossing of floor panels, one per row, and every panel shows
# an expression.  A panel is live when its expression is True and zaps whoever steps
# on it (score only, never security).  Read the expressions, then walk the row whose
# expression is False.  There is no timing: the answer never changes.
PANEL_COLS = (20, 20, 7)             # first column of each corridor's crossing (4 tiles wide)
PANEL_TILES_WIDE = 4
TRUE_EXPRS = (                       # [corridor] -> expressions that are True (live)
    ("3 + 4 == 7", "2 ** 3 == 8", "9 // 2 == 4", "10 % 4 == 2", "6 * 2 == 12", "9 - 4 == 5"),
    ("5 > 3", "4 <= 4", "2 != 3", "7 >= 7", "1 < 9", "6 == 6"),
    ("True and True", "True or False", "not False", "False or True", "not (1 > 2)", "not (3 > 5)"),
)
FALSE_EXPRS = (                      # [corridor] -> expressions that are False (safe)
    ("2 + 2 == 5", "7 // 2 == 4", "9 % 4 == 2", "2 ** 3 == 6", "5 * 2 == 12", "8 - 3 == 4"),
    ("3 > 5", "4 == 5", "6 != 6", "2 >= 8", "9 < 1", "5 <= 4"),
    ("True and False", "not True", "False or False", "False and True", "not (2 > 1)", "True and not True"),
)


def evaluate(expr):
    """The real Python truth of a panel's expression (constants only)."""
    return bool(eval(expr, {"__builtins__": {}}, {}))            # noqa: S307 - literals from this file only


def panel_tiles(rng):
    """The panels of every corridor: [{"corridor","row","rect","expr","live"}...].

    Every corridor keeps at least one safe row (and at least one live row), and the
    safe rows move around with the seed so the crossing is not memorised.
    """
    tiles = []
    for corridor, (first, last) in enumerate(BANDS):
        rows = list(range(first, last + 1))
        safe_count = rng.choice((1, 2)) if len(rows) > 3 else 1
        safe_rows = set(rng.sample(rows, safe_count))
        live_pool = rng.sample(TRUE_EXPRS[corridor], len(rows))
        safe_pool = rng.sample(FALSE_EXPRS[corridor], len(rows))
        for k, row in enumerate(rows):
            live = row not in safe_rows
            expr = live_pool[k] if live else safe_pool[k]
            tiles.append({"corridor": corridor, "row": row, "expr": expr, "live": live,
                          "rect": pygame.Rect(PANEL_COLS[corridor] * TILE, row * TILE,
                                              PANEL_TILES_WIDE * TILE, TILE)})
    return tiles


def panel_under(tiles, rect):
    """The panel whose floor `rect` stands on (by its centre), or None."""
    for tile in tiles:
        if tile["rect"].collidepoint(rect.center):
            return tile
    return None


def draw_floor_panel(surface, tile, state, t):
    """One floor panel.  state: "unknown" (not tried), "safe" (stepped on, nothing), "live" (it zapped)."""
    rect = tile["rect"]
    base = theme.mix(theme.INK, theme.SLATE, 0.35)
    pygame.draw.rect(surface, base, rect)
    for x in range(rect.left + 8, rect.right, 16):                 # grating slots
        pygame.draw.line(surface, theme.mix(base, theme.INK, 0.5), (x, rect.top + 3), (x, rect.bottom - 4), 1)
    edge = {"unknown": theme.mix(theme.GOLD, theme.INK, 0.45), "safe": theme.TEAL, "live": theme.CORAL}[state]
    pygame.draw.rect(surface, edge, rect, 2)
    if state == "live":
        pulse = 0.5 + 0.5 * math.sin(t * 18)
        pygame.draw.rect(surface, theme.mix(theme.CORAL, theme.PAPER, 0.3 + 0.4 * pulse), rect.inflate(-6, -6), 2)
        rng = random.Random(int(t * 14) + rect.y)
        for _ in range(3):                                          # arcs that jump between frames
            x = rng.randint(rect.left + 8, rect.right - 8)
            pygame.draw.lines(surface, theme.PAPER, False,
                              [(x, rect.top + 3), (x + rng.randint(-8, 8), rect.centery), (x + rng.randint(-8, 8), rect.bottom - 3)], 2)
    colour = {"unknown": theme.GOLD, "safe": theme.TEAL, "live": theme.PAPER}[state]
    label = code_font(14).render(tile["expr"], True, colour)
    surface.blit(label, label.get_rect(center=rect.center))


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
    draw_rivets(bg, accent)
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
    draw_poster(bg, POSTER)
    draw_fuse_box(bg, FUSE_BOX)
    draw_panel_signs(bg)
    draw_wall_pipes(bg, metal)
    draw_toolbox(bg, TOOLBOX)
    for gate, (_, last) in enumerate(BANDS):                     # relay stencils on the floor
        label = ui_font(16, bold=True).render(f"RELAY BAY {gate + 1} - {TOPICS[gate]}", True,
                                              theme.mix(theme.INK, accent, 0.9))
        spot = label.get_rect(center=(PAD_CENTRE_X[gate], (last + 1) * TILE - 10))
        plate = pygame.Surface((spot.w + 14, spot.h + 2), pygame.SRCALPHA)
        pygame.draw.rect(plate, (*theme.INK, 170), plate.get_rect(), border_radius=3)
        bg.blit(plate, (spot.x - 7, spot.y - 1))                 # dark plate so the stencil reads
        bg.blit(label, spot)


PANEL_SIGNS = (pygame.Rect(PANEL_COLS[0] * TILE + 8, SEPARATORS[0] * TILE + 5, 112, 22),       # under crossing 1
               pygame.Rect(PANEL_COLS[1] * TILE + 36, SEPARATORS[1] * TILE + 5, 92, 22),      # under crossing 2 (clear of the valve)
               pygame.Rect(PANEL_COLS[2] * TILE + 8, (LAST_ROW + 1) * TILE + 5, 112, 22))     # under crossing 3


def draw_panel_signs(surface):
    """A small wall plate under each crossing that says how to read the panels."""
    for rect in PANEL_SIGNS:
        pygame.draw.rect(surface, theme.INK, rect, border_radius=3)
        pygame.draw.rect(surface, theme.CORAL, rect, 1, border_radius=3)
        text = ui_font(14, bold=True).render("TRUE = LIVE", True, theme.CORAL)
        surface.blit(text, text.get_rect(center=rect.center))


TOOLBOX = pygame.Rect(7 * TILE + 4, BANDS[0][0] * TILE + 11, 26, 16)         # the engineer's toolbox, by his cabinet


def draw_toolbox(surface, rect):
    """A red steel toolbox with a handle, a latch and a spanner sticking out."""
    pygame.draw.rect(surface, (0, 0, 0), rect.move(2, 2), border_radius=2)
    pygame.draw.rect(surface, (176, 52, 44), rect, border_radius=2)
    pygame.draw.rect(surface, (96, 26, 24), rect, 1, border_radius=2)
    pygame.draw.line(surface, (212, 214, 220), (rect.x + 5, rect.y - 3), (rect.right - 5, rect.y - 3), 2)      # handle
    pygame.draw.line(surface, (212, 214, 220), (rect.x + 5, rect.y - 3), (rect.x + 5, rect.y), 2)
    pygame.draw.line(surface, (212, 214, 220), (rect.right - 5, rect.y - 3), (rect.right - 5, rect.y), 2)
    pygame.draw.rect(surface, theme.GOLD, (rect.centerx - 2, rect.y + 5, 4, 5))                             # latch
    pygame.draw.line(surface, (150, 156, 168), (rect.right - 3, rect.y + 2), (rect.right + 5, rect.y - 4), 3)   # spanner


def draw_wall_pipes(bg, metal):
    """Pipe runs along the top and bottom of each separator wall, with brackets, a gauge and a conduit."""
    for sep in SEPARATORS:
        lo, hi = SHAFTS[SEPARATORS.index(sep)]
        top, bottom = sep * TILE + 1, sep * TILE + TILE - 5
        for x0, x1 in ((2 * TILE, lo * TILE), ((hi + 1) * TILE, 28 * TILE)):          # nothing across the open shaft
            pygame.draw.rect(bg, theme.mix(metal, theme.INK, 0.5), (x0, top + 1, x1 - x0, 4), border_radius=2)
            pygame.draw.rect(bg, theme.mix(metal, theme.PAPER, 0.3), (x0, top, x1 - x0, 2))
            pygame.draw.rect(bg, theme.mix(theme.INK, theme.SLATE, 0.4), (x0, bottom, x1 - x0, 3))      # a flat conduit
            for x in range(x0 + 20, x1 - 8, 64):
                pygame.draw.rect(bg, theme.INK, (x, top - 1, 5, 7))                       # brackets
                pygame.draw.rect(bg, theme.mix(theme.GOLD, theme.INK, 0.5), (x, bottom, 3, 3))   # cable ties
    for sep, col in zip(SEPARATORS, (10, 24)):                                           # a pressure gauge on each wall
        c = (col * TILE + TILE // 2, sep * TILE + TILE // 2)
        pygame.draw.circle(bg, theme.INK, c, 10)
        pygame.draw.circle(bg, theme.mix(theme.PAPER, theme.INK, 0.15), c, 8)
        pygame.draw.arc(bg, theme.TEAL, pygame.Rect(c[0] - 6, c[1] - 6, 12, 12), 0.4, 2.0, 2)
        pygame.draw.arc(bg, theme.CORAL, pygame.Rect(c[0] - 6, c[1] - 6, 12, 12), 2.0, 2.7, 2)
        pygame.draw.line(bg, theme.INK, c, (c[0] + 4, c[1] - 4), 2)


def draw_rivets(bg, accent):
    """Tread-plate rivets in the corner of every floor tile, so the corridors read as steel decking."""
    dot = theme.mix(theme.mix(theme.SLATE, accent, 0.18), theme.PAPER, 0.18)
    for first, last in BANDS:
        for row in range(first, last + 1):
            for col in range(2, 28):
                for dx, dy in ((4, 4), (TILE - 6, 4), (4, TILE - 6), (TILE - 6, TILE - 6)):
                    bg.fill(dot, (col * TILE + dx, row * TILE + dy, 2, 2))


def draw_fuse_box(surface, rect, taken=False):
    """A wall fuse box: grey door, red cross, a row of spare fuses (empty once the fuse is taken)."""
    pygame.draw.rect(surface, theme.INK, rect.inflate(4, 4), border_radius=3)
    pygame.draw.rect(surface, theme.mix(theme.SLATE, theme.MIST, 0.25), rect, border_radius=3)
    pygame.draw.rect(surface, theme.mix(theme.SLATE, theme.INK, 0.5), rect, 1, border_radius=3)
    cross = (rect.x + 9, rect.centery)
    pygame.draw.line(surface, theme.CORAL, (cross[0] - 4, cross[1]), (cross[0] + 4, cross[1]), 3)
    pygame.draw.line(surface, theme.CORAL, (cross[0], cross[1] - 4), (cross[0], cross[1] + 4), 3)
    for i in range(3):
        slot = pygame.Rect(rect.x + 18 + i * 8, rect.y + 6, 5, 14)
        pygame.draw.rect(surface, theme.INK, slot)
        if not (taken and i == 2):
            pygame.draw.rect(surface, theme.GOLD, slot.inflate(-2, -6))


def draw_poster(surface, rect):
    """A yellow safety poster with a warning triangle and text lines."""
    pygame.draw.rect(surface, theme.mix(theme.GOLD, theme.INK, 0.2), rect)
    pygame.draw.rect(surface, theme.INK, rect, 1)
    tri = [(rect.x + 12, rect.y + 5), (rect.x + 20, rect.bottom - 5), (rect.x + 4, rect.bottom - 5)]
    pygame.draw.polygon(surface, theme.INK, tri)
    pygame.draw.line(surface, theme.GOLD, (rect.x + 12, rect.y + 11), (rect.x + 12, rect.y + 16), 2)
    for k in range(3):
        pygame.draw.line(surface, theme.INK, (rect.x + 26, rect.y + 7 + k * 6), (rect.right - 5 - (k % 2) * 8, rect.y + 7 + k * 6), 2)


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
        self.steam = []                                          # puffs rising from the pipe valves
        self._rng = random.Random(seed + 99)
        self._steam_wait = 1.5

    def update(self, dt):
        dt = max(0.0, dt)
        self.time += dt
        self.motes.update(dt)
        self._steam_wait -= dt
        if self._steam_wait <= 0:                                # a valve hisses every few seconds
            self._steam_wait = self._rng.uniform(2.5, 5.0)
            vx, vy = self._rng.choice(STEAM_VENTS)
            for _ in range(6):
                self.steam.append({"x": vx + self._rng.uniform(-4, 4), "y": vy + self._rng.uniform(-3, 3),
                                   "vx": self._rng.uniform(-10, 10), "vy": self._rng.uniform(-34, -18),
                                   "life": 1.4, "r": self._rng.uniform(4, 7)})
        for puff in self.steam:
            puff["x"] += puff["vx"] * dt
            puff["y"] += puff["vy"] * dt
            puff["r"] += 5.0 * dt
            puff["life"] -= dt
        self.steam = [p for p in self.steam if p["life"] > 0]

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
        for puff in self.steam:                                  # soft grey-white clouds that fade as they rise
            alpha = int(90 * min(1.0, puff["life"] / 1.4))
            r = int(puff["r"])
            cloud = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
            pygame.draw.circle(cloud, (225, 225, 230, alpha), (r, r), r)
            world.blit(cloud, (int(puff["x"]) - r, int(puff["y"]) - r))
        for m in self.motes.motes:
            twinkle = 0.5 + 0.5 * math.sin(self.time * 1.5 + m["phase"])
            world.set_at((int(m["x"]), int(m["y"])), theme.mix(theme.INK, theme.MIST, 0.25 + 0.5 * twinkle))




def draw_screen(surface, rect, gate, state, accent, prompt="", answer="", fraction=1.0,
                seconds=0, time=0.0):
    """Floor 2 wall screen: the shared screen, but a waiting relay says what it waits for."""
    _shared_screen(surface, rect, gate, state, accent, prompt, answer, fraction, seconds, time)
    if state != "standby":
        return
    cover = pygame.Rect(rect.x + 4, rect.y + 24, rect.w - 8, rect.h - 28)
    pygame.draw.rect(surface, theme.mix(theme.INK, theme.SLATE, 0.10), cover)   # wipe the bare "STANDBY"
    for y in range(cover.y + 2, cover.bottom, 4):                               # dead-screen scanlines
        pygame.draw.line(surface, theme.mix(theme.INK, theme.SLATE, 0.22), (cover.x, y), (cover.right, y))
    line = f"WAITING FOR RELAY {gate}" if gate > 0 else "STANDBY"
    text = code_font(15).render(line, True, theme.SLATE)
    surface.blit(text, text.get_rect(center=(cover.centerx, cover.centery - 4)))
    if int(time * 1.6) % 2 == 0:                                                # blinking cursor
        pygame.draw.rect(surface, theme.SLATE, (cover.centerx + text.get_width() // 2 + 4,
                                               cover.centery - 10, 8, 12))
