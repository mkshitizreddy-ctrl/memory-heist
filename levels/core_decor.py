"""
levels/core_decor.py
Owner: Member 1 - Core Game System (the Final Vault rebuilt as WARDEN's Core)

Geometry and art for the last floor: WARDEN's core, a round chamber with the
Master Memory chip sealed in an iris at its centre.  Six lock pylons ring the
core, one for every floor of the run; three answer plates sit in front of each.
WARDEN's eye watches from the iris and sweeps a searchlight round the room.

      [ WARDEN's terminal ]                         [ core status ]
                     .  -  ~  plates  ~  -  .
      lift ====  (  pylon      EYE      pylon  )  ==== exit lift
                     '  -  ~  plates  ~  -  '

The round floor is unlike any other floor's layout.  final_core.py owns the rules.
"""

import math

import pygame

from core.tilemap import TILE
from levels import novacorp_style
from ui import theme
from ui.fonts import code_font, ui_font

COLS, ROWS = 30, 20
CENTRE_TILE = (15, 11)
CENTRE = (CENTRE_TILE[0] * TILE + TILE // 2, CENTRE_TILE[1] * TILE + TILE // 2)
FLOOR_RADIUS = 7.3                    # tiles
CORRIDOR_ROWS = (10, 11, 12)
PYLON_RADIUS = 132
PLATE_RADIUS = 198
PLATE_SPREAD = 17                     # degrees between a lock's plates
BEAM_HALF = 13                        # degrees: half the searchlight's width
BEAM_NEAR, BEAM_FAR = 56, 236         # the beam starts outside the iris and reaches the wall

CORE = pygame.Rect(0, 0, 84, 84)
CORE.center = CENTRE
DOOR = pygame.Rect(28 * TILE, CORRIDOR_ROWS[0] * TILE, 2 * TILE, 3 * TILE)
EXIT_ZONE = pygame.Rect(28 * TILE + 8, DOOR.y, 2 * TILE, DOOR.h)
LIFT = pygame.Rect(0, CORRIDOR_ROWS[0] * TILE, 2 * TILE, 3 * TILE)
SPAWNS = ((3 * TILE, 10 * TILE + 8), (3 * TILE, 11 * TILE + 24))
TERMINAL = pygame.Rect(36, 100, 216, 196)          # WARDEN's terminal on the wall: the lock you are near
STATUS = pygame.Rect(712, 100, 212, 196)           # the core's status: six lamps and WARDEN's integrity
MOTE_AREA = pygame.Rect(CENTRE[0] - 230, CENTRE[1] - 230, 460, 460)

CORE_RED = (190, 40, 44)
STEEL = (54, 46, 54)
CODE_INK = (230, 200, 190)


# --- geometry ---------------------------------------------------------------------------
def layout_rows():
    out = []
    cx, cy = CENTRE_TILE
    for y in range(ROWS):
        row = []
        for x in range(COLS):
            inside = math.hypot(x - cx, y - cy) <= FLOOR_RADIUS and y >= 3
            corridor = y in CORRIDOR_ROWS and 2 <= x <= COLS - 1
            row.append("." if inside or corridor else "#")
        out.append("".join(row))
    return out


def lock_angle(k):
    return math.radians(-90 + 60 * k)


def pylon_rect(k):
    a = lock_angle(k)
    r = pygame.Rect(0, 0, 28, 34)
    r.center = (CENTRE[0] + int(PYLON_RADIUS * math.cos(a)), CENTRE[1] + int(PYLON_RADIUS * math.sin(a)))
    return r


def plate_rect(k, j):
    a = lock_angle(k) + math.radians((j - 1) * PLATE_SPREAD)
    r = pygame.Rect(0, 0, 50, 30)
    r.center = (CENTRE[0] + int(PLATE_RADIUS * math.cos(a)), CENTRE[1] + int(PLATE_RADIUS * math.sin(a)))
    return r


def prop_rects():
    return [CORE] + [pylon_rect(k) for k in range(6)]


def in_beam(beam_angle, point):
    """True if `point` is lit by the searchlight pointing at `beam_angle` (radians)."""
    dx, dy = point[0] - CENTRE[0], point[1] - CENTRE[1]
    dist = math.hypot(dx, dy)
    if not BEAM_NEAR <= dist <= BEAM_FAR:
        return False
    diff = (math.atan2(dy, dx) - beam_angle + math.pi) % math.tau - math.pi
    return abs(math.degrees(diff)) <= BEAM_HALF


# --- static room ---------------------------------------------------------------------------
def draw_static(bg, tilemap, seed=6):
    pal = theme.floor_palette("final_vault")
    novacorp_style.draw_walls(bg, tilemap, pal["floor"])
    cx, cy = CENTRE
    for r, tone in ((226, (40, 22, 26)), (210, (58, 30, 34)), (150, (46, 24, 28)), (120, (62, 32, 36))):
        pygame.draw.circle(bg, tone, CENTRE, r, 3)
    for k in range(24):                                          # radial seams in the floor
        a = math.tau * k / 24
        p0 = (cx + math.cos(a) * 64, cy + math.sin(a) * 64)
        p1 = (cx + math.cos(a) * 222, cy + math.sin(a) * 222)
        pygame.draw.line(bg, (44, 22, 26), p0, p1, 1)
    for k in range(6):                                           # a lit groove from each pylon to the core
        a = lock_angle(k)
        p0 = (cx + math.cos(a) * 46, cy + math.sin(a) * 46)
        p1 = (cx + math.cos(a) * (PYLON_RADIUS - 18), cy + math.sin(a) * (PYLON_RADIUS - 18))
        pygame.draw.line(bg, (80, 30, 34), p0, p1, 4)
    novacorp_style.stains(bg, MOTE_AREA, seed=seed, count=8)
    for rect, title in ((TERMINAL, "WARDEN // LOCK TERMINAL"), (STATUS, "CORE STATUS")):
        pygame.draw.rect(bg, (12, 8, 10), rect, border_radius=4)
        pygame.draw.rect(bg, (120, 40, 44), rect, 2, border_radius=4)
        bg.blit(ui_font(12, bold=True).render(title, True, (200, 90, 90)), (rect.x + 8, rect.y + 6))
    for lift, label in ((LIFT, "LIFT"), (DOOR, "")):
        pygame.draw.rect(bg, (80, 70, 76), lift)
        pygame.draw.line(bg, (30, 26, 30), (lift.centerx, lift.y + 4), (lift.centerx, lift.bottom - 4), 2)
        pygame.draw.rect(bg, (30, 26, 30), lift, 2)
    sign = pygame.Rect(DOOR.x - 12, DOOR.y - 30, DOOR.w + 12, 22)
    pygame.draw.rect(bg, (20, 40, 36), sign, border_radius=3)
    pygame.draw.rect(bg, theme.TEAL, sign, 1, border_radius=3)
    out = ui_font(12, bold=True).render("EXTRACTION", True, theme.TEAL)
    bg.blit(out, out.get_rect(center=sign.center))
    for x0 in (64, 768):                                         # server banks in the lower corners
        for i in range(4):
            bank = pygame.Rect(x0 + i * 34, 14 * TILE + 16, 28, 4 * TILE - 8)
            pygame.draw.rect(bg, (30, 26, 32), bank)
            pygame.draw.rect(bg, (70, 56, 64), bank, 1)
    novacorp_style.grade(bg, seed=seed, tint=(1.04, 0.94, 0.94))


# --- live parts -----------------------------------------------------------------------------
def draw_beam(surface, angle, alert, t):
    """WARDEN's searchlight: a pale wedge from the iris to the wall, red when it has caught someone."""
    cx, cy = CENTRE
    half = math.radians(BEAM_HALF)
    points = [(cx + math.cos(angle) * BEAM_NEAR, cy + math.sin(angle) * BEAM_NEAR)]
    for s in range(9):
        a = angle - half + 2 * half * s / 8
        points.append((cx + math.cos(a) * BEAM_FAR, cy + math.sin(a) * BEAM_FAR))
    layer = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    colour = (255, 70, 60, 70) if alert else (255, 220, 200, 44)
    pygame.draw.polygon(layer, colour, points)
    edge = (255, 120, 100, 150) if alert else (255, 230, 210, 90)
    pygame.draw.lines(layer, edge, False, [points[1], points[0], points[-1]], 2)
    surface.blit(layer, (0, 0))


def draw_core(surface, solved, iris, chip_taken, t):
    """The iris and WARDEN's eye.  The eye cracks with each lock; the iris opens on the chip."""
    cx, cy = CENTRE
    k = solved / 6
    ring = theme.mix(CORE_RED, theme.TEAL, k)
    pygame.draw.circle(surface, (16, 10, 12), CENTRE, 44)
    pygame.draw.circle(surface, ring, CENTRE, 44, 3)
    for i in range(6):                                           # six lock lamps round the rim
        a = lock_angle(i)
        lamp = theme.TEAL if i < solved else (90, 30, 34)
        pygame.draw.circle(surface, lamp, (cx + int(math.cos(a) * 38), cy + int(math.sin(a) * 38)), 3)
    if iris < 1.0:                                               # the eye, behind closing shutters
        look = (cx + int(6 * math.sin(t * 0.9)), cy + int(4 * math.cos(t * 0.7)))
        pygame.draw.ellipse(surface, (60, 12, 16), (look[0] - 24, look[1] - 13, 48, 26))
        pygame.draw.ellipse(surface, theme.mix(theme.CORAL, ring, k), (look[0] - 24, look[1] - 13, 48, 26), 2)
        pygame.draw.circle(surface, theme.mix(theme.CORAL, (255, 255, 255), 0.2), look, 9)
        pygame.draw.circle(surface, (20, 4, 6), look, 4)
        for c in range(solved):                                  # cracks spread with every lock
            a = 0.6 + c * 1.05
            p = [(look[0] + math.cos(a) * 6, look[1] + math.sin(a) * 6),
                 (look[0] + math.cos(a + 0.3) * 16, look[1] + math.sin(a + 0.3) * 14),
                 (look[0] + math.cos(a - 0.2) * 26, look[1] + math.sin(a - 0.2) * 20)]
            pygame.draw.lines(surface, (240, 220, 210), False, p, 1)
        if iris > 0:
            for i in range(8):                                   # shutters sliding back
                a = math.tau * i / 8 + iris * 1.2
                r0, r1 = 40 * iris, 42
                pygame.draw.line(surface, ring, (cx + math.cos(a) * r0, cy + math.sin(a) * r0),
                                 (cx + math.cos(a) * r1, cy + math.sin(a) * r1), 4)
    if iris >= 1.0 and not chip_taken:                           # the Master Memory chip
        bob = int(3 * math.sin(t * 3))
        chip = pygame.Rect(0, 0, 26, 20)
        chip.center = (cx, cy + bob)
        pygame.draw.rect(surface, (40, 120, 110), chip, border_radius=3)
        pygame.draw.rect(surface, theme.TEAL, chip, 2, border_radius=3)
        for i in range(4):
            pygame.draw.line(surface, theme.GOLD, (chip.x + 5 + i * 5, chip.bottom), (chip.x + 5 + i * 5, chip.bottom + 4))
        pygame.draw.rect(surface, theme.GOLD, chip.inflate(-14, -10))


def draw_pylon(surface, k, state, t):
    """state: 'idle', 'near', 'solved'."""
    r = pylon_rect(k)
    pygame.draw.ellipse(surface, (0, 0, 0), (r.x - 2, r.bottom - 6, r.w + 4, 10))
    body = (64, 52, 60) if state != "solved" else (40, 70, 66)
    pygame.draw.rect(surface, body, r, border_radius=4)
    pygame.draw.rect(surface, theme.mix(body, theme.PAPER, 0.35), (r.x, r.y, r.w, 6), border_radius=4)
    lamp = {"idle": theme.CORAL, "near": theme.GOLD, "solved": theme.TEAL}[state]
    pulse = 0.6 + 0.4 * math.sin(t * 4 + k) if state == "near" else 1.0
    pygame.draw.rect(surface, theme.mix((20, 10, 12), lamp, pulse), r.inflate(-10, -16).move(0, 3), border_radius=2)
    num = ui_font(12, bold=True).render(str(k + 1), True, (230, 220, 220))
    surface.blit(num, num.get_rect(center=(r.centerx, r.y + 12)))


def draw_plates(surface, k, labels, out, wrong, standing, solved_index, t):
    font = code_font(13)
    for j in range(3):
        r = plate_rect(k, j)
        if solved_index is not None:
            tone = theme.TEAL if j == solved_index else (40, 36, 40)
        elif j in wrong:
            tone = theme.CORAL
        elif j in out:
            tone = (90, 50, 54)
        else:
            tone = theme.GOLD if j == standing else (150, 120, 120)
        pygame.draw.rect(surface, (20, 14, 16), r, border_radius=5)
        pygame.draw.rect(surface, tone, r, 2, border_radius=5)
        if j < len(labels) and (solved_index is None or j == solved_index):
            ink = (170, 100, 100) if j in out else CODE_INK
            img = font.render(labels[j], True, ink)
            if img.get_width() > r.w - 6:
                img = pygame.transform.smoothscale(img, (r.w - 6, img.get_height()))
            surface.blit(img, img.get_rect(center=r.center))
        if j in out and solved_index is None:
            pygame.draw.line(surface, theme.CORAL, (r.x + 4, r.y + 4), (r.right - 5, r.bottom - 5), 2)


def draw_terminal(surface, lock, solved, t):
    """WARDEN's terminal shows the lock you are nearest: its floor, its code, which plate to stand on."""
    r = TERMINAL
    inner = r.inflate(-16, -34).move(0, 9)
    if lock is None:
        lines = ["Walk up to a lock pylon.", "", "Six locks. Six floors.", "Open them in any order."]
        font = ui_font(15)
        for i, line in enumerate(lines):
            surface.blit(font.render(line, True, (190, 150, 150)), (inner.x, inner.y + i * 20))
        return
    head = ui_font(13, bold=True)
    tone = theme.TEAL if solved else theme.GOLD
    surface.blit(head.render(f"LOCK {lock['lock'] + 1}  {lock['topic']}", True, tone), (inner.x, inner.y))
    surface.blit(ui_font(12).render(lock["floor"], True, (150, 120, 120)), (inner.x, inner.y + 16))
    font = code_font(13)
    for i, line in enumerate(lock["lines"][:5]):
        img = font.render(line, True, CODE_INK)
        if img.get_width() > inner.w:
            img = pygame.transform.smoothscale(img, (inner.w, img.get_height()))
        surface.blit(img, (inner.x, inner.y + 38 + i * 16))
    tail = "OPEN" if solved else "Stand on the right plate, press E."
    surface.blit(ui_font(13, bold=True).render(tail, True, tone), (inner.x, inner.bottom - 16))


def draw_status(surface, solved, integrity, chip_taken, t):
    r = STATUS.inflate(-16, -34).move(0, 9)
    font = ui_font(13, bold=True)
    for k in range(6):
        lamp = theme.TEAL if k in solved else (90, 30, 34)
        pygame.draw.circle(surface, lamp, (r.x + 12 + k * 31, r.y + 14), 9)
        surface.blit(ui_font(11, bold=True).render(str(k + 1), True, (230, 220, 220)), (r.x + 9 + k * 31, r.y + 7))
    surface.blit(font.render("WARDEN INTEGRITY", True, (200, 140, 140)), (r.x, r.y + 38))
    bar = pygame.Rect(r.x, r.y + 58, r.w, 10)
    pygame.draw.rect(surface, (30, 16, 18), bar)
    flick = 1.0 if integrity > 0.3 or int(t * 6) % 2 else 0.4
    pygame.draw.rect(surface, theme.mix((60, 20, 20), theme.CORAL, flick), (bar.x, bar.y, int(bar.w * integrity), bar.h))
    msg = "CHIP EXTRACTED" if chip_taken else ("IRIS OPEN" if len(solved) == 6 else "MASTER MEMORY SEALED")
    surface.blit(font.render(msg, True, theme.TEAL if len(solved) == 6 else (200, 140, 140)), (r.x, r.y + 82))
