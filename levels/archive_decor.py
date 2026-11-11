"""
levels/archive_decor.py
Owner: Member 1 - Core Game System (Floor 4 rebuilt on the shared kit)

Geometry and art for Floor 4, the Records Archive: the hall where NovaCorp keeps a
file on every citizen, Ghost's stolen memory among them.

      wall   [poster]  [clock]  [ REQUEST SLIP ]  [satchel] [CARD CATALOGUE]
      row 6  [desk]          [ shelf: 5 boxes  ]           [ 4 drawers ]
             archivist's beat ------------------------------------------>
             [ stacks ]           [ stacks ]                   (open)
             security drone's aisle ------------------------------------>  exit:
      spawn  lift      [reading tables]               [ vault counter ]    vault door

Three requests, in order: pull a box from the shelf (a list index), open a drawer
of the catalogue (a dictionary key), feed one satchel item to the vault (a list
operation).  Nothing here changes a rule; floor4_archive.py owns those.
"""

import math
import random

import pygame

from core.tilemap import TILE
from levels import novacorp_style
from ui import theme
from ui.fonts import code_font, ui_font

COLS, ROWS = 30, 20
WALL_ROWS = 6                       # rows 0..5: the back wall carries the request slip
LAST_ROW = 17
EXIT_ROWS = (13, 14, 15)
RUNNER_ROWS = (13, 14)              # a worn runner along the drone's aisle

SHELF = pygame.Rect(9 * TILE, 6 * TILE, 10 * TILE, 2 * TILE)          # five boxes, two tiles each
CATALOGUE = pygame.Rect(21 * TILE, 6 * TILE, 6 * TILE, 2 * TILE)      # four drawers, 48 px each
COUNTER = pygame.Rect(21 * TILE, 16 * TILE, 6 * TILE, 2 * TILE)       # the vault's intake: three trays
DESK = pygame.Rect(3 * TILE, 6 * TILE + 8, 4 * TILE, 2 * TILE - 8)
STACKS = (pygame.Rect(4 * TILE, 11 * TILE, 7 * TILE, 2 * TILE),
          pygame.Rect(13 * TILE, 11 * TILE, 7 * TILE, 2 * TILE))
TABLES = (pygame.Rect(9 * TILE, 16 * TILE + 6, 4 * TILE, TILE - 6),
          pygame.Rect(15 * TILE, 16 * TILE + 6, 4 * TILE, TILE - 6))
DOOR = pygame.Rect(28 * TILE, EXIT_ROWS[0] * TILE, 2 * TILE, len(EXIT_ROWS) * TILE)
EXIT_ZONE = pygame.Rect(28 * TILE + 8, DOOR.y, 2 * TILE, DOOR.h)
SPAWNS = ((3 * TILE, 15 * TILE), (4 * TILE + 8, 15 * TILE))

SLIP = pygame.Rect(9 * TILE, 92, 12 * TILE, 96)                      # the request slip on the wall
SATCHEL_TAG = pygame.Rect(21 * TILE + 4, 96, 6 * TILE - 8, 44)
CATALOGUE_SIGN = pygame.Rect(21 * TILE + 4, 150, 6 * TILE - 8, 30)
POSTER = pygame.Rect(76, 96, 62, 88)
CLOCK_CENTRE = (196, 132)
VAULT_SIGN = pygame.Rect(26 * TILE + 8, 11 * TILE + 6, 3 * TILE + 16, 26)
LIFT = pygame.Rect(0, 14 * TILE, 2 * TILE, 3 * TILE)

DRONE_Y = 13 * TILE + 24
DRONE_X = (3 * TILE, 26 * TILE)
ARCHIVIST_ROUTE = [(3 * TILE, 9 * TILE + 4), (12 * TILE, 9 * TILE + 4), (20 * TILE, 9 * TILE + 4)]
MOTE_AREA = pygame.Rect(2 * TILE, 6 * TILE, 26 * TILE, 12 * TILE)
LAMPS = ((5 * TILE, 7 * TILE), (11 * TILE, 16 * TILE + 10), (17 * TILE, 16 * TILE + 10))   # green banker's lamps
CEILING = tuple((x * TILE, y * TILE) for y in (9, 14) for x in (6, 14, 22))

INK = (34, 30, 26)                  # typewriter ink
PAPER = (222, 212, 180)             # request slips and file cards
BRASS = (186, 150, 70)
WOOD = (92, 64, 42)


# --- geometry -------------------------------------------------------------------
def layout_rows():
    out = []
    for y in range(ROWS):
        if y < WALL_ROWS or y > LAST_ROW:
            out.append("#" * COLS)
            continue
        row = ["#", "#"] + ["," if y in RUNNER_ROWS else "."] * (COLS - 4) + ["#", "#"]
        if y in EXIT_ROWS:
            row[COLS - 2] = row[COLS - 1] = "."
        out.append("".join(row))
    return out


def prop_rects():
    return [SHELF, CATALOGUE, COUNTER, DESK, *STACKS, *TABLES]


def box_rect(i):
    return pygame.Rect(SHELF.x + i * 2 * TILE + 6, SHELF.y + 10, 2 * TILE - 12, 2 * TILE - 22)


def drawer_rect(i):
    return pygame.Rect(CATALOGUE.x + i * 48 + 4, CATALOGUE.y + 14, 40, 2 * TILE - 26)


def tray_rect(i):
    return pygame.Rect(COUNTER.x + i * 2 * TILE + 6, COUNTER.y + 6, 2 * TILE - 12, 26)


def targets(stage, count):
    """The things you act on for a stage: boxes, drawers or trays."""
    rect = (box_rect, drawer_rect, tray_rect)[stage]
    return [rect(i) for i in range(count)]


def stand_zone(stage, i):
    """Where you stand to act on target i: the floor strip just in front of it."""
    if stage == 0:
        return pygame.Rect(SHELF.x + i * 2 * TILE, SHELF.bottom, 2 * TILE, TILE + 8)
    if stage == 1:
        return pygame.Rect(CATALOGUE.x + i * 48, CATALOGUE.bottom, 48, TILE + 8)
    return pygame.Rect(COUNTER.x + i * 2 * TILE, COUNTER.y - TILE - 8, 2 * TILE, TILE + 8)


# --- static room ------------------------------------------------------------------
def _shadow(surface, rect, depth=14, alpha=110):
    shade = pygame.Surface((rect.w + 6, depth), pygame.SRCALPHA)
    for i in range(depth):
        pygame.draw.line(shade, (0, 0, 0, int(alpha * (1 - i / depth))), (0, i), (rect.w + 6, i))
    surface.blit(shade, (rect.x - 3, rect.bottom))


def _shelving(surface, rect, rng, cap=8):
    """A steel shelving run seen from above and in front: a lit top, a face full of file boxes."""
    _shadow(surface, rect)
    steel = (70, 74, 84)
    pygame.draw.rect(surface, steel, rect)
    top = pygame.Rect(rect.x, rect.y, rect.w, cap)
    pygame.draw.rect(surface, theme.mix(steel, theme.PAPER, 0.35), top)
    face = pygame.Rect(rect.x + 3, rect.y + cap + 2, rect.w - 6, rect.h - cap - 6)
    pygame.draw.rect(surface, (28, 28, 34), face)
    for row in range(2):
        y = face.y + 2 + row * (face.h // 2)
        x = face.x + 2
        while x < face.right - 6:
            w = rng.randint(7, 13)
            tone = rng.choice(((132, 110, 74), (110, 96, 70), (150, 140, 112), (96, 84, 70), (120, 60, 50)))
            pygame.draw.rect(surface, tone, (x, y, w - 1, face.h // 2 - 4))
            pygame.draw.line(surface, theme.mix(tone, theme.PAPER, 0.3), (x + 2, y + 3), (x + w - 4, y + 3))
            x += w
        pygame.draw.line(surface, theme.mix(steel, theme.PAPER, 0.2), (face.x, y + face.h // 2 - 2), (face.right, y + face.h // 2 - 2), 2)
    pygame.draw.rect(surface, theme.mix(steel, (0, 0, 0), 0.5), rect, 2)


def _desk(surface):
    _shadow(surface, DESK)
    pygame.draw.rect(surface, WOOD, DESK, border_radius=3)
    pygame.draw.rect(surface, theme.mix(WOOD, theme.PAPER, 0.25), (DESK.x, DESK.y, DESK.w, 7), border_radius=3)
    pygame.draw.rect(surface, theme.mix(WOOD, (0, 0, 0), 0.5), DESK, 2, border_radius=3)
    for k in range(3):                                         # a stack of folders
        pygame.draw.rect(surface, (200, 186, 140), (DESK.x + 50, DESK.y + 14 - k * 3, 30, 14))
        pygame.draw.rect(surface, (150, 130, 90), (DESK.x + 50, DESK.y + 14 - k * 3, 30, 14), 1)
    pygame.draw.rect(surface, (150, 40, 36), (DESK.x + 92, DESK.y + 18, 10, 8))       # the rubber stamp
    pygame.draw.rect(surface, WOOD, (DESK.x + 95, DESK.y + 12, 4, 7))
    lamp = (DESK.x + 2 * TILE - 2, DESK.y + 10)                # a green banker's lamp
    pygame.draw.ellipse(surface, (40, 110, 70), (lamp[0] - 12, lamp[1] - 6, 24, 10))
    pygame.draw.line(surface, BRASS, (lamp[0], lamp[1]), (lamp[0], lamp[1] + 12), 2)


def _tables(surface):
    for table in TABLES:
        _shadow(surface, table, 10, 90)
        pygame.draw.rect(surface, WOOD, table, border_radius=2)
        pygame.draw.rect(surface, theme.mix(WOOD, theme.PAPER, 0.2), (table.x, table.y, table.w, 5))
        for cx in range(table.x + 16, table.right - 8, 2 * TILE):                  # chairs, tucked in
            pygame.draw.rect(surface, (60, 44, 34), (cx, table.bottom + 2, 22, 8), border_radius=2)
        lamp = (table.centerx, table.y + 6)
        pygame.draw.ellipse(surface, (40, 110, 70), (lamp[0] - 10, lamp[1] - 5, 20, 9))
        pygame.draw.rect(surface, (210, 200, 160), (table.x + 12, table.y + 8, 18, 11))   # an open file


def _shelf_frame(surface):
    """The request shelf: a dark oak case with an index plate under each box."""
    _shadow(surface, SHELF)
    pygame.draw.rect(surface, (58, 40, 28), SHELF)
    pygame.draw.rect(surface, theme.mix((58, 40, 28), theme.PAPER, 0.3), (SHELF.x, SHELF.y, SHELF.w, 6))
    pygame.draw.rect(surface, (30, 22, 16), SHELF, 2)
    font = code_font(14)
    for i in range(5):
        cell = pygame.Rect(SHELF.x + i * 2 * TILE, SHELF.y, 2 * TILE, SHELF.h)
        pygame.draw.line(surface, (30, 22, 16), (cell.x, cell.y + 6), (cell.x, cell.bottom), 2)
        plate = pygame.Rect(cell.centerx - 16, cell.bottom - 12, 32, 12)
        pygame.draw.rect(surface, BRASS, plate, border_radius=2)
        label = font.render(f"[{i}]", True, (40, 30, 14))
        surface.blit(label, label.get_rect(center=plate.center))


def _catalogue_frame(surface):
    _shadow(surface, CATALOGUE)
    pygame.draw.rect(surface, (74, 52, 36), CATALOGUE, border_radius=2)
    pygame.draw.rect(surface, theme.mix((74, 52, 36), theme.PAPER, 0.3), (CATALOGUE.x, CATALOGUE.y, CATALOGUE.w, 6))
    pygame.draw.rect(surface, (34, 24, 16), CATALOGUE, 2, border_radius=2)


def _counter_frame(surface):
    pygame.draw.rect(surface, (64, 68, 78), COUNTER)
    pygame.draw.rect(surface, theme.mix((64, 68, 78), theme.PAPER, 0.3), (COUNTER.x, COUNTER.y, COUNTER.w, 5))
    pygame.draw.rect(surface, (24, 26, 32), COUNTER, 2)
    pipe = (COUNTER.right - 6, COUNTER.y + 10)                 # the tube that carries items into the vault
    pygame.draw.line(surface, (120, 126, 140), pipe, (DOOR.x - 4, pipe[1]), 6)
    pygame.draw.line(surface, (120, 126, 140), (DOOR.x - 4, pipe[1]), (DOOR.x - 4, DOOR.bottom + 4), 6)


def _wall_decor(surface):
    font = ui_font(12, bold=True)
    novacorp_style.draw_poster(surface, POSTER, ("NOTHING", "TO HIDE.", "NOTHING", "TO FEAR."), font)
    pygame.draw.circle(surface, (30, 30, 34), CLOCK_CENTRE, 22)              # the wall clock
    pygame.draw.circle(surface, (214, 206, 180), CLOCK_CENTRE, 19)
    pygame.draw.circle(surface, (60, 56, 50), CLOCK_CENTRE, 19, 2)
    for k in range(12):
        a = k * math.tau / 12
        p0 = (CLOCK_CENTRE[0] + math.cos(a) * 15, CLOCK_CENTRE[1] + math.sin(a) * 15)
        p1 = (CLOCK_CENTRE[0] + math.cos(a) * 17, CLOCK_CENTRE[1] + math.sin(a) * 17)
        pygame.draw.line(surface, (60, 56, 50), p0, p1, 2 if k % 3 == 0 else 1)
    tube = (120, 126, 140)                                       # the pneumatic tube from the slip to the desk
    pygame.draw.line(surface, tube, (SLIP.x - 2, SLIP.bottom - 20), (DESK.centerx + 20, SLIP.bottom - 20), 5)
    pygame.draw.line(surface, tube, (DESK.centerx + 20, SLIP.bottom - 20), (DESK.centerx + 20, DESK.y + 4), 5)
    pygame.draw.rect(surface, (40, 34, 30), CATALOGUE_SIGN, border_radius=3)
    pygame.draw.rect(surface, BRASS, CATALOGUE_SIGN, 2, border_radius=3)
    sign = ui_font(14, bold=True).render("CARD CATALOGUE  {key: value}", True, BRASS)
    surface.blit(sign, sign.get_rect(center=CATALOGUE_SIGN.center))
    pygame.draw.rect(surface, (40, 20, 20), VAULT_SIGN, border_radius=3)
    pygame.draw.rect(surface, theme.CORAL, VAULT_SIGN, 2, border_radius=3)
    vault = ui_font(13, bold=True).render("MEMORY VAULT", True, theme.mix(theme.CORAL, theme.PAPER, 0.4))
    surface.blit(vault, vault.get_rect(center=VAULT_SIGN.center))
    lift = LIFT                                                  # the lift Ghost came up in
    pygame.draw.rect(surface, (80, 86, 96), lift)
    pygame.draw.line(surface, (30, 32, 40), (lift.centerx, lift.y + 4), (lift.centerx, lift.bottom - 4), 2)
    pygame.draw.rect(surface, (30, 32, 40), lift, 2)


def draw_static(bg, tilemap, seed=4):
    """Everything that never changes, baked once."""
    rng = random.Random(seed)
    pal = theme.floor_palette("level4")
    novacorp_style.draw_walls(bg, tilemap, pal["floor"])
    novacorp_style.stains(bg, MOTE_AREA, seed=seed, count=16)
    novacorp_style.stencil(bg, "SILENCE IN THE ARCHIVE", (12 * TILE, 15 * TILE + 4), ui_font(18, bold=True), alpha=60)
    for rect in STACKS:
        _shelving(bg, rect, rng)
    _desk(bg)
    _tables(bg)
    _shelf_frame(bg)
    _catalogue_frame(bg)
    _counter_frame(bg)
    _wall_decor(bg)
    novacorp_style.grade(bg, seed=seed)


# --- live parts -------------------------------------------------------------------
def _file_box(surface, rect, lift, lit):
    r = rect.move(0, int(lift))
    body = (150, 128, 88) if not lit else (196, 170, 110)
    pygame.draw.rect(surface, body, r, border_radius=2)
    pygame.draw.rect(surface, theme.mix(body, theme.PAPER, 0.3), (r.x, r.y, r.w, 5), border_radius=2)
    pygame.draw.rect(surface, theme.mix(body, (0, 0, 0), 0.45), r, 1, border_radius=2)
    pygame.draw.rect(surface, PAPER, (r.centerx - 12, r.y + 12, 24, 10))                  # blank label
    pygame.draw.circle(surface, theme.mix(body, (0, 0, 0), 0.5), (r.centerx, r.bottom - 7), 3)   # finger hole


def draw_shelf(surface, pulled, wrong, highlight, t):
    """The five boxes. pulled: {i: 0..1}; wrong: {i: seconds}; highlight: index the player stands at."""
    for i in range(5):
        rect = box_rect(i)
        out = pulled.get(i, 0.0)
        if out >= 1.0:                                          # taken: an empty slot, the plate still shows
            pygame.draw.rect(surface, (22, 16, 12), rect, border_radius=2)
            pygame.draw.rect(surface, (40, 30, 22), rect, 1, border_radius=2)
            continue
        shake = math.sin(t * 60) * 2 if i in wrong else 0
        _file_box(surface, rect.move(int(shake), 0), 6 * out, i == highlight)
        if i in wrong:
            pygame.draw.rect(surface, theme.CORAL, rect.inflate(4, 4), 2, border_radius=3)


def draw_drawers(surface, labels, opened, wrong, highlight, card, t):
    font = code_font(12)
    for i in range(4):
        rect = drawer_rect(i)
        out = 8 * opened.get(i, 0.0)
        r = rect.move(0, int(out))
        body = (120, 88, 58) if i != highlight else (150, 112, 74)
        pygame.draw.rect(surface, body, r, border_radius=2)
        pygame.draw.rect(surface, theme.mix(body, (0, 0, 0), 0.5), r, 1, border_radius=2)
        holder = pygame.Rect(r.x + 3, r.y + 4, r.w - 6, 14)              # the brass label holder
        pygame.draw.rect(surface, BRASS, holder, 1)
        pygame.draw.rect(surface, PAPER, holder.inflate(-2, -2))
        if i < len(labels):
            img = font.render(labels[i], True, INK)
            if img.get_width() > holder.w - 2:
                img = pygame.transform.smoothscale(img, (holder.w - 2, img.get_height()))
            surface.blit(img, img.get_rect(center=holder.center))
        pygame.draw.rect(surface, (60, 44, 30), (r.centerx - 6, r.bottom - 9, 12, 4), border_radius=2)   # pull
        if i in wrong:
            pygame.draw.rect(surface, theme.CORAL, r.inflate(4, 4), 2, border_radius=3)
        if opened.get(i, 0.0) > 0.5 and card:
            note = pygame.Rect(r.x + 4, r.bottom - 2, r.w - 8, 16)
            pygame.draw.rect(surface, PAPER, note)
            val = font.render(card, True, theme.CORAL)
            surface.blit(val, val.get_rect(center=note.center))


def draw_trays(surface, labels, fed, wrong, highlight, t):
    font = code_font(12)
    for i in range(3):
        rect = tray_rect(i)
        tone = (40, 44, 52) if i != highlight else (60, 70, 84)
        pygame.draw.rect(surface, tone, rect, border_radius=3)
        pygame.draw.rect(surface, (120, 126, 140), rect, 1, border_radius=3)
        if i < len(labels) and fed.get(i, 0.0) < 1.0:
            sink = int(8 * fed.get(i, 0.0))
            img = font.render(labels[i], True, PAPER)
            surface.blit(img, img.get_rect(center=(rect.centerx, rect.centery + sink)))
        if i in wrong:
            pygame.draw.rect(surface, theme.CORAL, rect.inflate(4, 4), 2, border_radius=4)


def draw_satchel(surface, items):
    tag = SATCHEL_TAG
    pygame.draw.rect(surface, (52, 40, 30), tag, border_radius=4)
    pygame.draw.rect(surface, BRASS, tag, 2, border_radius=4)
    title = ui_font(12, bold=True).render("GHOST'S SATCHEL (a list)", True, BRASS)
    surface.blit(title, (tag.x + 8, tag.y + 4))
    text = "satchel = [" + ", ".join(repr(i) for i in items) + "]"
    font = code_font(13)
    img = font.render(text, True, PAPER)
    if img.get_width() > tag.w - 14:
        img = pygame.transform.smoothscale(img, (tag.w - 14, img.get_height()))
    surface.blit(img, (tag.x + 8, tag.y + 22))


def draw_slip(surface, request, number, total, fraction, seconds, done, t):
    """The request slip pinned to the wall: cream paper, typed Python, a red stamp, a burning clock."""
    r = SLIP
    pygame.draw.rect(surface, (0, 0, 0), r.move(3, 3))
    pygame.draw.rect(surface, PAPER, r)
    pygame.draw.rect(surface, (150, 136, 100), r, 2)
    pygame.draw.circle(surface, theme.CORAL, (r.centerx, r.y + 5), 4)                    # the pin
    head = ui_font(13, bold=True)
    if done:
        msg = head.render("ALL REQUESTS FILED", True, (40, 110, 70))
        surface.blit(msg, msg.get_rect(center=(r.centerx, r.y + 30)))
        sub = code_font(14).render("vault.open()  # walk through the vault door", True, INK)
        surface.blit(sub, sub.get_rect(center=(r.centerx, r.y + 56)))
        return
    title = head.render(f"ARCHIVE REQUEST {number}/{total} - {request['topic']}", True, (120, 34, 30))
    surface.blit(title, (r.x + 10, r.y + 10))
    font = code_font(14)
    for k, line in enumerate(request["lines"][:4]):
        img = font.render(line, True, INK)
        if img.get_width() > r.w - 20:
            img = pygame.transform.smoothscale(img, (r.w - 20, img.get_height()))
        surface.blit(img, (r.x + 10, r.y + 25 + k * 14))
    bar = pygame.Rect(r.x + 10, r.bottom - 7, r.w - 70, 4)
    pygame.draw.rect(surface, (190, 176, 140), bar)
    colour = (40, 110, 70) if fraction > 0.35 else theme.CORAL
    pygame.draw.rect(surface, colour, (bar.x, bar.y, int(bar.w * max(0.0, fraction)), bar.h))
    secs = head.render(f"{seconds:>2}s", True, colour)
    surface.blit(secs, (bar.right + 8, bar.y - 8))


class Drone:
    """The archive's security drone: drifts along the aisle, sweeps a pale searchlight."""

    def __init__(self, speed=88.0):
        self.x = float(DRONE_X[1])
        self.y = float(DRONE_Y)
        self.direction = -1
        self.speed = speed
        self.lure = None             # (x, y) Echo's drone is pulling it toward, or None

    def update(self, dt):
        if self.lure is not None:
            dx, dy = self.lure[0] - self.x, self.lure[1] - self.y
            dist = math.hypot(dx, dy)
            if dist > 2:
                step = min(dist, self.speed * 1.4 * dt)
                self.x += dx / dist * step
                self.y += dy / dist * step
            return
        if abs(self.y - DRONE_Y) > 1:                     # drift back down to the aisle after a lure
            self.y += max(-self.speed * dt, min(self.speed * dt, DRONE_Y - self.y))
        self.x += self.direction * self.speed * dt
        if self.x >= DRONE_X[1]:
            self.x, self.direction = DRONE_X[1], -1
        elif self.x <= DRONE_X[0]:
            self.x, self.direction = DRONE_X[0], 1

    @property
    def centre(self):
        return (int(self.x), int(self.y))
