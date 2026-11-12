"""
levels/server_decor.py
Owner: Member 1 - Core Game System (Floor 5 rebuilt on the shared kit)

Geometry and art for Floor 5, WARDEN's Server Hall: a cold machine room where
every machine is a function with its def stencilled on the casing.

      wall  [ WARDEN's eye ]   [   JOB TICKET   ]   [ reactor gauges ]
      row 6 [ ROUTER  def ]    [ PRESS   def ]      [ REACTOR  def ]
            sysadmin's beat ------------------------------------------>
            [patch panel]  rack  ==conveyor==  rack  [except breakers]
            [  4 ports  ]  rack  [  4 bays  ]  rack  [   2 x 2      ]
      spawn  ~vent~        ~vent~      ~vent~        [WARDEN console]   exit

Jobs, in order: patch the router's cable to the port whose value lands in the
asked parameter (arguments), route the press's conveyor to the bay its return
value goes to (return values), pull the except breaker that catches the
reactor's error before it overheats (exceptions); then type an access level at
WARDEN's console (a real try/except).  floor5_server.py owns the rules.
"""

import math
import random

import pygame

from core.tilemap import TILE
from levels import novacorp_style
from ui import theme
from ui.fonts import code_font, ui_font

COLS, ROWS = 30, 20
WALL_ROWS = 6
LAST_ROW = 17
EXIT_ROWS = (14, 15, 16)
CABLE_ROWS = (9,)                     # the sysadmin's beat, a cable tray runs under it

MACHINES = (pygame.Rect(2 * TILE, 6 * TILE, 6 * TILE, 3 * TILE),        # ROUTER  (arguments)
            pygame.Rect(12 * TILE, 6 * TILE, 6 * TILE, 3 * TILE),       # PRESS   (return values)
            pygame.Rect(22 * TILE, 6 * TILE, 6 * TILE, 3 * TILE))       # REACTOR (exceptions)
MACHINE_NAMES = ("ROUTER", "PRESS", "REACTOR")
PANEL = pygame.Rect(2 * TILE, 11 * TILE, 6 * TILE, TILE)                # four ports
BAYS = pygame.Rect(12 * TILE, 12 * TILE, 6 * TILE, TILE)                # four output bays
BOARD = pygame.Rect(22 * TILE, 11 * TILE, 6 * TILE, 2 * TILE)           # four breakers, 2 x 2
RACKS = (pygame.Rect(10 * TILE, 11 * TILE, TILE, 4 * TILE),          # two-tile walkways: cols 8-9, 20-21 and the top aisle
         pygame.Rect(19 * TILE, 11 * TILE, TILE, 4 * TILE))
CONSOLE = pygame.Rect(23 * TILE, 16 * TILE, 3 * TILE, 2 * TILE)
DOOR = pygame.Rect(28 * TILE, EXIT_ROWS[0] * TILE, 2 * TILE, len(EXIT_ROWS) * TILE)
EXIT_ZONE = pygame.Rect(28 * TILE + 8, DOOR.y, 2 * TILE, DOOR.h)
SPAWNS = ((2 * TILE + 8, 15 * TILE), (3 * TILE + 16, 15 * TILE))
LIFT = pygame.Rect(0, 15 * TILE, 2 * TILE, 3 * TILE)

TICKET = pygame.Rect(9 * TILE, 90, 12 * TILE, 100)
EYE_SCREEN = pygame.Rect(2 * TILE, 92, 6 * TILE, 92)
GAUGES = pygame.Rect(22 * TILE, 92, 6 * TILE, 92)
VENTS = tuple((col * TILE + TILE // 2, 16 * TILE) for col in (6, 14, 17))
VENT_PERIOD, VENT_WARN, VENT_BLOW = 5.5, 1.0, 1.5
SYSADMIN_ROUTE = [(3 * TILE, 9 * TILE + 2), (14 * TILE, 9 * TILE + 2), (25 * TILE, 9 * TILE + 2)]
MOTE_AREA = pygame.Rect(2 * TILE, 6 * TILE, 26 * TILE, 12 * TILE)

STEEL = (58, 66, 80)
STEEL_LIT = (120, 132, 150)
COLD = (120, 200, 230)                # the hall's cold service light
CODE_INK = (170, 230, 210)


# --- geometry ----------------------------------------------------------------------
def layout_rows():
    out = []
    for y in range(ROWS):
        if y < WALL_ROWS or y > LAST_ROW:
            out.append("#" * COLS)
            continue
        row = ["#", "#"] + ["," if y in CABLE_ROWS else "."] * (COLS - 4) + ["#", "#"]
        if y in EXIT_ROWS:
            row[COLS - 2] = row[COLS - 1] = "."
        out.append("".join(row))
    return out


def prop_rects():
    return [*MACHINES, PANEL, BAYS, BOARD, *RACKS, CONSOLE]


def port_rect(i):
    return pygame.Rect(PANEL.x + i * 48 + 6, PANEL.y + 5, 36, PANEL.h - 10)


def bay_rect(i):
    return pygame.Rect(BAYS.x + i * 48 + 4, BAYS.y + 3, 40, BAYS.h - 6)


def breaker_rect(i):
    row, col = divmod(i, 2)
    return pygame.Rect(BOARD.x + col * 96 + 6, BOARD.y + row * TILE + 3, 84, TILE - 6)


def targets(stage):
    return [(port_rect, bay_rect, breaker_rect)[stage](i) for i in range(4)]


def stand_zone(stage, i):
    """Where you stand to act on target i."""
    if stage == 0:
        return pygame.Rect(PANEL.x + i * 48, PANEL.y - TILE - 8, 48, TILE + 8)
    if stage == 1:
        return pygame.Rect(BAYS.x + i * 48, BAYS.y - TILE - 8, 48, TILE + 8)
    row, col = divmod(i, 2)
    if row == 0:
        return pygame.Rect(BOARD.x + col * 96, BOARD.y - TILE - 8, 96, TILE + 8)
    return pygame.Rect(BOARD.x + col * 96, BOARD.bottom, 96, TILE + 8)


def vent_state(i, t):
    """'rest', 'warn' or 'blow' for vent i at time t (each vent runs offset from the others)."""
    phase = (t + i * 1.9) % VENT_PERIOD
    rest = VENT_PERIOD - VENT_WARN - VENT_BLOW
    if phase < rest:
        return "rest"
    return "warn" if phase < rest + VENT_WARN else "blow"


def plume_rect(i):
    """The scalding column of steam: the whole height of the bottom corridor, 40 px wide."""
    x, _ = VENTS[i]
    return pygame.Rect(x - 20, 15 * TILE, 40, 3 * TILE)


# --- static room ---------------------------------------------------------------------
def _shadow(surface, rect, depth=14, alpha=110):
    shade = pygame.Surface((rect.w + 6, depth), pygame.SRCALPHA)
    for i in range(depth):
        pygame.draw.line(shade, (0, 0, 0, int(alpha * (1 - i / depth))), (0, i), (rect.w + 6, i))
    surface.blit(shade, (rect.x - 3, rect.bottom))


def _box(surface, rect, body=STEEL, cap=8):
    """A steel cabinet seen from above and in front: lit top, dark edges, a shadow on the floor."""
    _shadow(surface, rect)
    pygame.draw.rect(surface, body, rect)
    pygame.draw.rect(surface, theme.mix(body, theme.PAPER, 0.35), (rect.x, rect.y, rect.w, cap))
    pygame.draw.line(surface, theme.mix(body, (0, 0, 0), 0.5), (rect.x, rect.y + cap), (rect.right - 1, rect.y + cap), 2)
    pygame.draw.rect(surface, theme.mix(body, (0, 0, 0), 0.55), rect, 2)


def _rack(surface, rect):
    _box(surface, rect, (40, 44, 54), cap=6)
    for y in range(rect.y + 12, rect.bottom - 8, 10):            # server blades
        pygame.draw.rect(surface, (26, 28, 36), (rect.x + 5, y, rect.w - 10, 7))
        pygame.draw.line(surface, (70, 76, 90), (rect.x + 5, y), (rect.right - 6, y))


def _floor(surface):
    """A raised floor: perforated cooling tiles in the aisles, a cable tray under the beat."""
    for x in range(2 * TILE, 28 * TILE, TILE):
        for y in (10 * TILE, 13 * TILE):
            if any(r.collidepoint(x + 4, y + 4) for r in prop_rects()):
                continue
            for dx in range(6, TILE - 4, 6):
                for dy in range(6, TILE - 4, 6):
                    surface.set_at((x + dx, y + dy), (20, 24, 32))
    tray = pygame.Rect(2 * TILE, 9 * TILE + TILE // 2 - 3, 26 * TILE, 6)
    pygame.draw.rect(surface, (34, 38, 46), tray)
    for x in range(tray.x, tray.right, 10):
        pygame.draw.line(surface, (60, 66, 76), (x, tray.y), (x + 4, tray.bottom - 1))


def _wall(surface):
    pygame.draw.rect(surface, (12, 14, 20), EYE_SCREEN, border_radius=4)
    pygame.draw.rect(surface, STEEL_LIT, EYE_SCREEN, 2, border_radius=4)
    pygame.draw.rect(surface, (12, 14, 20), GAUGES, border_radius=4)
    pygame.draw.rect(surface, STEEL_LIT, GAUGES, 2, border_radius=4)
    sign = pygame.Rect(DOOR.x - 8, 12 * TILE + 8, DOOR.w + 8, 24)
    pygame.draw.rect(surface, (40, 20, 20), sign, border_radius=3)
    pygame.draw.rect(surface, theme.CORAL, sign, 2, border_radius=3)
    label = ui_font(12, bold=True).render("TO THE VAULT", True, theme.mix(theme.CORAL, theme.PAPER, 0.4))
    surface.blit(label, label.get_rect(center=sign.center))
    pygame.draw.rect(surface, (80, 86, 96), LIFT)
    pygame.draw.line(surface, (30, 32, 40), (LIFT.centerx, LIFT.y + 4), (LIFT.centerx, LIFT.bottom - 4), 2)
    pygame.draw.rect(surface, (30, 32, 40), LIFT, 2)


def _vents(surface):
    for x, y in VENTS:
        grate = pygame.Rect(x - 16, y - 10, 32, 20)
        pygame.draw.rect(surface, (30, 30, 34), grate, border_radius=3)
        for gx in range(grate.x + 4, grate.right - 2, 5):
            pygame.draw.line(surface, (70, 64, 56), (gx, grate.y + 3), (gx, grate.bottom - 4))
        pygame.draw.rect(surface, (110, 90, 50), grate, 1, border_radius=3)


def draw_static(bg, tilemap, seed=5):
    rng = random.Random(seed)
    pal = theme.floor_palette("level5")
    novacorp_style.draw_walls(bg, tilemap, pal["floor"])
    _floor(bg)
    novacorp_style.stains(bg, MOTE_AREA, seed=seed, count=10)
    novacorp_style.stencil(bg, "EFFICIENCY IS LOYALTY", (14 * TILE, 15 * TILE + 20), ui_font(18, bold=True), alpha=55)
    for rect in RACKS:
        _rack(bg, rect)
    for rect in MACHINES:
        _box(bg, rect, (50, 58, 72), cap=10)
    _box(bg, PANEL, (44, 50, 62), cap=5)
    _box(bg, BAYS, (44, 50, 62), cap=5)
    _box(bg, BOARD, (54, 50, 46), cap=6)
    _box(bg, CONSOLE, (36, 40, 52), cap=6)
    _vents(bg)
    _wall(bg)
    novacorp_style.grade(bg, seed=seed, tint=(0.92, 0.98, 1.02))
    del rng


# --- live parts -------------------------------------------------------------------------
def draw_machine(surface, i, lines, active, done, heat, t):
    """A machine's face: its name plate, its def in green phosphor, a status lamp."""
    r = MACHINES[i]
    face = pygame.Rect(r.x + 8, r.y + 16, r.w - 16, r.h - 26)
    pygame.draw.rect(surface, (10, 14, 18), face, border_radius=3)
    lamp = theme.TEAL if done else (theme.GOLD if active else (60, 66, 80))
    pygame.draw.rect(surface, lamp, face, 1, border_radius=3)
    plate = ui_font(12, bold=True).render(MACHINE_NAMES[i], True, lamp)
    surface.blit(plate, (face.x + 6, face.y + 3))
    font = code_font(12)
    for k, line in enumerate(lines[:4]):
        img = font.render(line, True, CODE_INK if active or done else (90, 110, 104))
        if img.get_width() > face.w - 10:
            img = pygame.transform.smoothscale(img, (face.w - 10, img.get_height()))
        surface.blit(img, (face.x + 6, face.y + 18 + k * 13))
    blink = (int(t * 2 + i) % 2 == 0) or done
    pygame.draw.circle(surface, lamp if blink else (40, 44, 52), (face.right - 8, face.y + 8), 3)
    if i == 2 and heat > 0:                                      # the reactor's heat bar
        bar = pygame.Rect(face.x + 6, face.bottom - 8, face.w - 12, 4)
        pygame.draw.rect(surface, (40, 30, 30), bar)
        hot = theme.mix(theme.GOLD, theme.CORAL, min(1.0, heat))
        pygame.draw.rect(surface, hot, (bar.x, bar.y, int(bar.w * min(1.0, heat)), bar.h))


def _label(surface, rect, text, ink, font):
    img = font.render(text, True, ink)
    if img.get_width() > rect.w - 4:
        img = pygame.transform.smoothscale(img, (rect.w - 4, img.get_height()))
    surface.blit(img, img.get_rect(center=rect.center))


def draw_ports(surface, labels, out, highlight, plugged, t):
    font = code_font(13)
    for i, rect in enumerate(targets(0)):
        lit = i == highlight and i not in out
        pygame.draw.rect(surface, (16, 18, 24), rect, border_radius=3)
        pygame.draw.rect(surface, COLD if lit else (80, 90, 104), rect, 1, border_radius=3)
        pygame.draw.circle(surface, (6, 8, 10), (rect.centerx, rect.y + 5), 3)        # the socket
        if i < len(labels):
            _label(surface, rect.move(0, 4), labels[i], (90, 60, 60) if i in out else CODE_INK, font)
        if i in out:
            pygame.draw.line(surface, theme.CORAL, rect.topleft, rect.bottomright, 2)
    if plugged is not None:                                      # the cable from the router's jack
        start = (MACHINES[0].centerx, MACHINES[0].bottom - 4)
        end = targets(0)[plugged].midtop
        mid = ((start[0] + end[0]) // 2, max(start[1], end[1]) + 26)
        points = [((1 - s) ** 2 * start[0] + 2 * (1 - s) * s * mid[0] + s * s * end[0],
                   (1 - s) ** 2 * start[1] + 2 * (1 - s) * s * mid[1] + s * s * end[1]) for s in [k / 16 for k in range(17)]]
        pygame.draw.lines(surface, (20, 20, 24), False, points, 5)
        pygame.draw.lines(surface, theme.GOLD, False, points, 2)


def draw_conveyor(surface, routed, t, running):
    """The belt from the press down to the bays; once routed, a diverter points at the chosen bay."""
    belt = pygame.Rect(MACHINES[1].centerx - 14, MACHINES[1].bottom, 28, BAYS.y - MACHINES[1].bottom)
    pygame.draw.rect(surface, (24, 26, 30), belt)
    pygame.draw.rect(surface, (70, 76, 86), belt, 1)
    shift = int((t * 40) % 12) if running else 0
    for y in range(belt.y - 12 + shift, belt.bottom, 12):
        if y >= belt.y:
            pygame.draw.lines(surface, (90, 96, 106), False, [(belt.x + 6, y), (belt.centerx, y + 5), (belt.right - 6, y)], 2)
    if routed is not None:
        target = targets(1)[routed].midtop
        pygame.draw.line(surface, theme.GOLD, (belt.centerx, belt.bottom - 2), target, 3)


def draw_bays(surface, labels, out, highlight, routed, t):
    font = code_font(13)
    for i, rect in enumerate(targets(1)):
        lit = i == highlight and i not in out
        tone = theme.TEAL if routed == i else (COLD if lit else (80, 90, 104))
        pygame.draw.rect(surface, (16, 18, 24), rect, border_radius=3)
        pygame.draw.rect(surface, tone, rect, 1 if routed != i else 2, border_radius=3)
        if i < len(labels):
            _label(surface, rect, labels[i], (90, 60, 60) if i in out else CODE_INK, font)
        if i in out:
            pygame.draw.line(surface, theme.CORAL, rect.topleft, rect.bottomright, 2)


def draw_breakers(surface, labels, out, highlight, pulled, t):
    small = ui_font(11, bold=True)
    font = code_font(13)
    for i, rect in enumerate(targets(2)):
        lit = i == highlight and i not in out
        pygame.draw.rect(surface, (30, 28, 26), rect, border_radius=3)
        tone = theme.TEAL if pulled == i else (theme.GOLD if lit else (110, 96, 70))
        pygame.draw.rect(surface, tone, rect, 1 if pulled != i else 2, border_radius=3)
        lever = pygame.Rect(rect.right - 14, rect.y + (12 if pulled == i else 3), 8, 10)    # the lever, down once pulled
        pygame.draw.rect(surface, theme.CORAL if pulled != i else theme.TEAL, lever, border_radius=2)
        if i < len(labels):
            word = small.render("except", True, (150, 140, 120))
            surface.blit(word, (rect.x + 5, rect.y + 2))
            _label(surface, pygame.Rect(rect.x + 2, rect.y + 11, rect.w - 18, 14), labels[i],
                   (90, 60, 60) if i in out else (230, 214, 170), font)
        if i in out:
            pygame.draw.line(surface, theme.CORAL, rect.topleft, rect.bottomright, 2)


def draw_racks_live(surface, t):
    for k, rect in enumerate(RACKS):
        for j, y in enumerate(range(rect.y + 13, rect.bottom - 8, 10)):
            for n in range(3):
                on = math.sin(t * (2.0 + n) + j * 1.7 + k * 3 + n) > 0.2
                colour = (80, 230, 160) if (j + n) % 4 else (255, 180, 60)
                surface.set_at((rect.x + 8 + n * 4, y + 3), colour if on else (30, 34, 40))
                surface.set_at((rect.x + 9 + n * 4, y + 3), colour if on else (30, 34, 40))


def draw_eye_screen(surface, t, alarm):
    """WARDEN watches the hall: a red eye that tracks, over a log scrolling past."""
    r = EYE_SCREEN.inflate(-8, -8)
    font = code_font(11)
    logs = ("CITIZEN 0471  LOGGED", "FLOOR 4  RECORDS SEALED", "COURIER  UNVERIFIED",
            "REACTOR  NOMINAL", "LIFT  B  IN USE", "CITIZEN 1180  LOGGED")
    previous = surface.get_clip()
    surface.set_clip(r)
    scroll = int(t * 10) % (len(logs) * 12)
    for k in range(len(logs) * 2):
        y = r.y + k * 12 - scroll
        surface.blit(font.render(logs[k % len(logs)], True, (70, 40, 44)), (r.x + 4, y))
    surface.set_clip(previous)
    centre = (r.centerx + int(10 * math.sin(t * 0.7)), r.centery)
    red = theme.CORAL if not alarm else (255, 60, 50)
    pygame.draw.ellipse(surface, (40, 10, 12), (centre[0] - 26, centre[1] - 13, 52, 26))
    pygame.draw.ellipse(surface, red, (centre[0] - 26, centre[1] - 13, 52, 26), 2)
    pygame.draw.circle(surface, red, centre, 8 if not alarm else 10)
    pygame.draw.circle(surface, (20, 4, 6), centre, 3)


def draw_gauges(surface, heat, uptime, t):
    r = GAUGES.inflate(-10, -10)
    font = ui_font(12, bold=True)
    surface.blit(font.render("REACTOR HEAT", True, (150, 160, 176)), (r.x + 4, r.y + 2))
    bar = pygame.Rect(r.x + 4, r.y + 20, r.w - 8, 10)
    pygame.draw.rect(surface, (30, 30, 36), bar)
    hot = theme.mix(theme.TEAL, theme.CORAL, min(1.0, heat))
    pygame.draw.rect(surface, hot, (bar.x, bar.y, int(bar.w * min(1.0, heat)), bar.h))
    surface.blit(font.render("JOBS DONE", True, (150, 160, 176)), (r.x + 4, r.y + 40))
    for k in range(4):
        lamp = theme.TEAL if k < uptime else (40, 46, 56)
        pygame.draw.circle(surface, lamp, (r.x + 12 + k * 22, r.y + 66), 7)


def draw_ticket(surface, request, step, total, done, t):
    r = TICKET
    pygame.draw.rect(surface, (0, 0, 0), r.move(3, 3))
    pygame.draw.rect(surface, (12, 16, 22), r, border_radius=4)
    pygame.draw.rect(surface, COLD, r, 2, border_radius=4)
    head = ui_font(13, bold=True)
    if done:
        msg = head.render(done, True, theme.TEAL)
        surface.blit(msg, msg.get_rect(center=(r.centerx, r.y + 40)))
        return
    title = head.render(f"JOB {step}/{total} - {request['topic']}  ({['ROUTER', 'PRESS', 'REACTOR'][request['stage']]})",
                        True, theme.GOLD)
    surface.blit(title, (r.x + 10, r.y + 7))
    font = code_font(13)
    for k, line in enumerate(request["lines"][:5]):
        img = font.render(line, True, CODE_INK)
        if img.get_width() > r.w - 20:
            img = pygame.transform.smoothscale(img, (r.w - 20, img.get_height()))
        surface.blit(img, (r.x + 10, r.y + 25 + k * 14))


def draw_vents(surface, t):
    for i, (x, y) in enumerate(VENTS):
        state = vent_state(i, t)
        if state == "warn":
            glow = pygame.Surface((40, 24), pygame.SRCALPHA)
            pulse = 0.5 + 0.5 * math.sin(t * 18)
            pygame.draw.ellipse(glow, (255, 150, 60, int(60 + 80 * pulse)), glow.get_rect())
            surface.blit(glow, (x - 20, y - 12))
        elif state == "blow":
            plume = plume_rect(i)
            layer = pygame.Surface(plume.size, pygame.SRCALPHA)
            for k in range(9):
                yy = plume.h - ((t * 120 + k * 13) % plume.h)
                rad = 8 + int(10 * (1 - yy / plume.h))
                pygame.draw.circle(layer, (220, 226, 232, 90), (plume.w // 2 + int(6 * math.sin(k + t * 3)), int(yy)), rad)
            surface.blit(layer, plume.topleft)


CONSOLE_WINDOW = pygame.Rect(190, 214, 580, 330)


def draw_console_window(surface, code_lines, command, result, feedback, good, hint, hint_cost, t):
    """WARDEN's console while a player types: the real code, the entry, what it raised."""
    from ui.kit import draw_panel, wrap_text
    box = CONSOLE_WINDOW
    draw_panel(surface, box, fill=(10, 12, 18), border=theme.CORAL, radius=8)
    surface.blit(ui_font(22, bold=True).render("WARDEN CONSOLE - unlock_vault.py", True, theme.CORAL), (box.x + 16, box.y + 10))
    mono = code_font(15)
    for k, line in enumerate(code_lines):
        surface.blit(mono.render(line, True, CODE_INK), (box.x + 18, box.y + 40 + k * 16))
    y = box.y + 40 + len(code_lines) * 16 + 8
    entry = pygame.Rect(box.x + 14, y, box.w - 28, 30)
    pygame.draw.rect(surface, (4, 6, 10), entry, border_radius=6)
    pygame.draw.rect(surface, theme.MIST, entry, 2, border_radius=6)
    cursor = "_" if int(t * 2) % 2 == 0 else " "
    surface.blit(code_font(17).render(f"entry = {command}{cursor}", True, theme.PAPER), (entry.x + 10, entry.y + 6))
    y = entry.bottom + 6
    if result:
        surface.blit(code_font(15).render(str(result)[:58], True, theme.SKY), (box.x + 16, y))
        y += 20
    small = ui_font(18)
    lines = [(line, theme.TEAL if good else theme.CORAL) for line in wrap_text(feedback, small, box.w - 32)] if feedback else []
    lines += [(line, theme.GOLD) for line in wrap_text(hint, small, box.w - 32)] if hint else []
    for text, ink in lines[:3]:
        surface.blit(small.render(text, True, ink), (box.x + 16, y))
        y += small.get_linesize()
    help_text = f"ENTER: run    TAB: hint (-{hint_cost} pts)    Arrow keys: step away"
    tip = ui_font(16).render(help_text, True, theme.MIST)
    surface.blit(tip, (box.x + 16, box.bottom - 24))
