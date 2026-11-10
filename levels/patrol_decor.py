"""
levels/patrol_decor.py
Owner: Member 5 (UI)

Floor 3 - the night patrol.  Pure drawing: the three rooms' walls and floors,
the slim header, the patrol-loop board and the small things that move on the
walls.  Nothing here changes a rule of Level 3; the lasers, robot, gates and
questions stay in levels/level3_loops.py.

The story: NovaCorp's night patrol is a loop.  Lasers sweep on a cycle, the
robot walks its route, and the wall board shows the same loop as code.
"""

import math

import pygame

from levels.lighting import Light
from ui import theme
from ui.fonts import code_font, ui_font

ACCENT = theme.floor_palette("level3")["accent"]        # the floor's one accent colour
FLOOR = theme.floor_palette("level3")["floor"]
WALL = (24, 32, 42)
WALL_BOTTOM = 122                                       # room-local y where wall meets floor
ROOM_NAMES = {1: "STAFF CORRIDOR", 2: "CAMERA GALLERY", 3: "CHECKPOINT HALL"}

# Screen-space areas the live parts use (room origin is (40, 30)).
HEADER = pygame.Rect(60, 52, 840, 28)
BOARD = pygame.Rect(560, 82, 262, 70)
NOTICE = pygame.Rect(400, 84, 148, 64)
BANNER_LANE = pygame.Rect(150, 84, 405, 32)

DIM_CODE = theme.mix(theme.SLATE, theme.MIST, 0.45)          # an unlit line is still readable

# --- static room -------------------------------------------------------------

def _floor(surface, width, height):
    dark = theme.mix(theme.INK, FLOOR, 0.45)
    light = theme.mix(theme.INK, FLOOR, 0.6)
    for ty in range(0, height, 40):
        for tx in range(0, width, 40):
            colour = light if (tx // 40 + ty // 40) % 2 == 0 else dark
            pygame.draw.rect(surface, colour, (tx, ty, 40, 40))
    seam = theme.mix(dark, theme.INK, 0.5)
    for x in range(0, width, 40):
        pygame.draw.line(surface, seam, (x, 0), (x, height))
    for y in range(0, height, 40):
        pygame.draw.line(surface, seam, (0, y), (width, y))


def _wall(surface, width):
    pygame.draw.rect(surface, WALL, (0, 0, width, WALL_BOTTOM))
    for x in range(0, width, 80):
        pygame.draw.line(surface, theme.mix(WALL, theme.INK, 0.5), (x, 0), (x, WALL_BOTTOM))
    pygame.draw.rect(surface, theme.mix(WALL, theme.SLATE, 0.5), (0, WALL_BOTTOM - 8, width, 8))   # skirting
    pygame.draw.line(surface, theme.mix(ACCENT, WALL, 0.45), (0, WALL_BOTTOM), (width, WALL_BOTTOM), 2)
    shade = pygame.Surface((width, 14), pygame.SRCALPHA)
    for i in range(14):
        pygame.draw.line(shade, (0, 0, 0, 90 - i * 6), (0, i), (width, i))
    surface.blit(shade, (0, WALL_BOTTOM + 1))                                 # the wall's shadow on the floor


def _patrol_line(surface, width):
    """The robot's route, painted on the floor: amber dashes."""
    amber = theme.mix(theme.GOLD, FLOOR, 0.55)
    for x in range(24, width - 96, 28):
        pygame.draw.rect(surface, amber, (x, 168, 16, 3))


def _frame(surface, rect, fill, border):
    pygame.draw.rect(surface, fill, rect, border_radius=3)
    pygame.draw.rect(surface, border, rect, 1, border_radius=3)


def _lockers(surface):
    """Room 1: the night staff's lockers, a time clock, an extinguisher."""
    metal = theme.mix(theme.NAVY, theme.SLATE, 0.5)
    for i in range(4):
        door = pygame.Rect(20 + i * 44, 52, 38, 62)
        _frame(surface, door, metal, theme.SLATE)
        for slot in range(3):                                   # vents
            pygame.draw.line(surface, theme.INK, (door.x + 8, door.y + 8 + slot * 4),
                             (door.right - 8, door.y + 8 + slot * 4))
        pygame.draw.rect(surface, theme.GOLD, (door.x + 12, door.y + 30, 14, 6))      # name plate
        pygame.draw.circle(surface, theme.SLATE, (door.right - 7, door.y + 40), 2)    # handle
    clock = pygame.Rect(208, 60, 40, 44)
    _frame(surface, clock, theme.NAVY, theme.SLATE)
    pygame.draw.rect(surface, theme.INK, (clock.x + 6, clock.y + 6, 28, 14))
    pygame.draw.rect(surface, theme.SLATE, (clock.x + 8, clock.y + 28, 24, 8))        # card slot
    ext = pygame.Rect(276, 66, 14, 40)
    pygame.draw.rect(surface, theme.CORAL, ext, border_radius=5)
    pygame.draw.rect(surface, theme.INK, (ext.x + 4, ext.y - 6, 6, 6))


def _monitors(surface):
    """Room 2: a bank of CCTV monitors and a ceiling camera."""
    for row in range(2):
        for col in range(4):
            screen = pygame.Rect(20 + col * 62, 52 + row * 34, 54, 28)
            _frame(surface, screen, theme.INK, theme.SLATE)
            pygame.draw.rect(surface, theme.mix(theme.INK, ACCENT, 0.12), screen.inflate(-6, -6))
    pygame.draw.rect(surface, theme.mix(theme.NAVY, theme.SLATE, 0.4), (20, 120 - 8, 246, 4))   # desk edge
    mount = pygame.Rect(297, 26, 6, 24)
    pygame.draw.rect(surface, theme.SLATE, mount)
    pygame.draw.circle(surface, theme.mix(theme.NAVY, theme.SLATE, 0.6), (300, 56), 14)
    pygame.draw.circle(surface, theme.INK, (300, 58), 7)


def _checkpoint(surface):
    """Room 3: WARDEN's plaque over the checkpoint, with a barrier either side."""
    plaque = pygame.Rect(120, 50, 130, 64)
    _frame(surface, plaque, theme.mix(theme.INK, theme.CORAL, 0.18), theme.CORAL)
    pygame.draw.circle(surface, theme.INK, plaque.center, 22)
    pygame.draw.circle(surface, theme.CORAL, plaque.center, 22, 2)
    pygame.draw.circle(surface, theme.CORAL, plaque.center, 9)
    label = ui_font(12, bold=True).render("WARDEN SEES ALL", True, theme.mix(theme.CORAL, theme.PAPER, 0.4))
    surface.blit(label, label.get_rect(midbottom=(plaque.centerx, plaque.bottom - 2)))
    for x in (30, 296):                                         # barrier posts
        pygame.draw.rect(surface, theme.SLATE, (x, 70, 6, 44))
        pygame.draw.rect(surface, theme.GOLD, (x - 4, 66, 14, 6))
    pygame.draw.line(surface, theme.CORAL, (36, 82), (296, 82), 2)


def _stencil(surface, text, centre, size, alpha=70):
    """Paint a number on the floor: it sits under the beams, so it reads while a lane is off."""
    image = ui_font(size, bold=True).render(text, True, theme.mix(FLOOR, theme.PAPER, 0.5))
    image.set_alpha(alpha)
    surface.blit(image, image.get_rect(center=centre))


def _vending(surface):
    """Room 1: the staff vending machine between the time clock and the notice board."""
    body = pygame.Rect(312, 54, 44, 62)
    _frame(surface, body, theme.mix(theme.NAVY, theme.SLATE, 0.3), theme.SLATE)
    window = pygame.Rect(body.x + 5, body.y + 6, 24, 36)
    pygame.draw.rect(surface, theme.INK, window)
    for row in range(3):                                                  # tins on three shelves
        for col in range(3):
            tone = (theme.TEAL, theme.GOLD, theme.CORAL)[(row + col) % 3]
            pygame.draw.rect(surface, theme.mix(tone, theme.INK, 0.3), (window.x + 2 + col * 7, window.y + 3 + row * 11, 5, 8))
    pygame.draw.rect(surface, theme.SLATE, (body.x + 33, body.y + 8, 7, 14))          # coin slot panel
    pygame.draw.rect(surface, theme.INK, (body.x + 5, body.bottom - 14, 34, 8))       # delivery flap


def _floor_staff(surface):
    """Room 1: each lane is a rubber runner on the lino, numbered like the loop's `lane`."""
    for lane, cx in enumerate((210, 360, 510, 660)):
        mat = pygame.Rect(cx - 34, 138, 68, 294)
        pygame.draw.rect(surface, theme.mix(theme.INK, FLOOR, 0.28), mat, border_radius=4)
        for y in range(mat.top + 6, mat.bottom - 4, 12):
            pygame.draw.line(surface, theme.mix(theme.INK, FLOOR, 0.4), (mat.x + 6, y), (mat.right - 7, y))
        pygame.draw.rect(surface, theme.mix(theme.INK, FLOOR, 0.45), mat, 1, border_radius=4)
        _stencil(surface, str(lane), (cx, 285), 34)
    for x, y in ((110, 360), (770, 250)):                                 # floor drains
        pygame.draw.rect(surface, theme.mix(theme.INK, FLOOR, 0.3), (x, y, 28, 20), border_radius=3)
        for gx in range(x + 5, x + 25, 5):
            pygame.draw.line(surface, theme.INK, (gx, y + 4), (gx, y + 16))


def _floor_gallery(surface):
    """Room 2: a raised floor with access hatches, and the cable tray that feeds the ceiling cameras."""
    for hx, hy in ((120, 200), (440, 300), (240, 360), (600, 200)):
        hatch = pygame.Rect(hx, hy, 40, 40)
        pygame.draw.rect(surface, theme.mix(theme.INK, FLOOR, 0.3), hatch)
        pygame.draw.rect(surface, theme.mix(theme.INK, FLOOR, 0.55), hatch, 2)
        pygame.draw.rect(surface, theme.SLATE, (hatch.centerx - 6, hatch.centery - 2, 12, 4), border_radius=2)
    tray = pygame.Rect(270, 124, 480, 8)                                  # from the monitor desk to the cameras
    pygame.draw.rect(surface, theme.mix(theme.INK, theme.GOLD, 0.18), tray)
    for x in range(tray.x, tray.right, 12):
        pygame.draw.line(surface, theme.INK, (x, tray.y), (x + 6, tray.bottom - 1))
    pygame.draw.rect(surface, theme.mix(theme.INK, theme.SLATE, 0.5), tray, 1)
    for cx in (290, 570, 730):                                            # a junction box under each camera
        box = pygame.Rect(cx - 9, 122, 18, 14)
        _frame(surface, box, theme.mix(theme.NAVY, theme.SLATE, 0.5), theme.SLATE)
        pygame.draw.circle(surface, theme.TEAL, (box.centerx, box.centery), 2)


def _floor_checkpoint(surface):
    """Room 3: bare concrete, the checkpoint zone ruled off in yellow, rows numbered like the nested loop."""
    tint = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    tint.fill((60, 66, 78, 40))
    surface.blit(tint, (0, 0))
    zone = pygame.Rect(24, 250, 782, 170)
    amber = theme.mix(theme.GOLD, FLOOR, 0.35)
    for corner, (dx, dy) in (((zone.left, zone.top), (1, 1)), ((zone.right, zone.top), (-1, 1)),
                             ((zone.left, zone.bottom), (1, -1)), ((zone.right, zone.bottom), (-1, -1))):
        pygame.draw.line(surface, amber, corner, (corner[0] + dx * 40, corner[1]), 3)
        pygame.draw.line(surface, amber, corner, (corner[0], corner[1] + dy * 40), 3)
    for row, y in enumerate((278, 338, 398)):
        _stencil(surface, f"row {row}", (70, y - 22), 15, alpha=110)


_DRESSING = {1: _lockers, 2: _monitors, 3: _checkpoint}
_FLOORS = {1: _floor_staff, 2: _floor_gallery, 3: _floor_checkpoint}

# Room-local rectangles of the solid walls (the room surface starts at screen (40, 30)).
# The same walls are handed to the game as collision rectangles (see WALLS_SCREEN).
DOOR_Y = (150, 270)                                       # the exit door's opening: gate y 180-300 on screen
WALL_RECTS_LOCAL = (
    pygame.Rect(0, 0, 880, 122),                          # back wall
    pygame.Rect(0, 122, 24, 326),                         # left wall
    pygame.Rect(806, 122, 28, DOOR_Y[0] - 122),           # right wall above the door
    pygame.Rect(806, DOOR_Y[1], 28, 448 - DOOR_Y[1]),     # right wall below the door
    pygame.Rect(0, 448, 880, 112),                        # front wall, behind the question panel
)
WALLS_SCREEN = tuple(r.move(40, 30) for r in WALL_RECTS_LOCAL)


SIDE = theme.mix(WALL, theme.SLATE, 0.45)                 # side walls: lighter than the back wall so they read


def _brick(surface, rect, vertical):
    """A wall face: panel seams, rivets and a lit edge toward the floor."""
    pygame.draw.rect(surface, SIDE, rect)
    seam = theme.mix(SIDE, theme.INK, 0.55)
    edge = theme.mix(ACCENT, SIDE, 0.35)
    if vertical:
        for y in range(rect.top, rect.bottom, 36):
            pygame.draw.line(surface, seam, (rect.left, y), (rect.right - 1, y))
        for y in range(rect.top + 18, rect.bottom, 36):
            pygame.draw.circle(surface, theme.mix(SIDE, theme.PAPER, 0.35), (rect.centerx, y), 2)
        pygame.draw.line(surface, edge, (rect.left, rect.top), (rect.left, rect.bottom - 1), 2)
        pygame.draw.line(surface, edge, (rect.right - 1, rect.top), (rect.right - 1, rect.bottom - 1), 2)
    else:
        for x in range(rect.left, rect.right, 80):
            pygame.draw.line(surface, seam, (x, rect.top), (x, rect.bottom - 1))
        pygame.draw.line(surface, edge, (rect.left, rect.top), (rect.right - 1, rect.top), 2)


def _shadow(surface, rect, toward):
    """A soft shadow the wall throws on the floor: toward is +1 (right of it) or -1 (left of it)."""
    shade = pygame.Surface((12, rect.height), pygame.SRCALPHA)
    for i in range(12):
        x = i if toward > 0 else 11 - i
        pygame.draw.line(shade, (0, 0, 0, 90 - i * 7), (x, 0), (x, rect.height))
    surface.blit(shade, (rect.right if toward > 0 else rect.left - 12, rect.top))


def _side_walls(surface, width, height):
    """Left, right and front walls, the door's service corridor and the entry door."""
    left, right_top, right_bottom, front = WALL_RECTS_LOCAL[1], WALL_RECTS_LOCAL[2], WALL_RECTS_LOCAL[3], WALL_RECTS_LOCAL[4]

    # beyond the exit door: a dark service corridor with chevrons pointing on
    corridor = pygame.Rect(834, 122, width - 834, 326)
    pygame.draw.rect(surface, theme.mix(theme.INK, FLOOR, 0.25), corridor)
    for y in range(corridor.top, corridor.bottom, 20):
        pygame.draw.rect(surface, theme.mix(theme.INK, theme.GOLD, 0.12), (corridor.x, y, corridor.width, 10))
    mid = (DOOR_Y[0] + DOOR_Y[1]) // 2
    for x in (840, 858):
        pygame.draw.lines(surface, theme.mix(ACCENT, theme.INK, 0.4), False,
                          [(x, mid - 12), (x + 8, mid), (x, mid + 12)], 3)

    for rect, vertical in ((left, True), (right_top, True), (right_bottom, True), (front, False)):
        _brick(surface, rect, vertical)
    _shadow(surface, left, +1)
    _shadow(surface, right_top.union(right_bottom), -1)
    pygame.draw.line(surface, theme.mix(WALL, theme.INK, 0.5), (right_top.left, right_top.bottom), (right_top.right, right_top.bottom), 2)

    # the way you came in: a shut steel door in the left wall at the spawn row
    door = pygame.Rect(left.x, 390, left.width, 60)
    pygame.draw.rect(surface, theme.mix(theme.NAVY, theme.SLATE, 0.45), door)
    pygame.draw.rect(surface, theme.INK, door, 2)
    for y in (door.y + 12, door.y + 30, door.y + 48):
        pygame.draw.line(surface, theme.mix(theme.NAVY, theme.INK, 0.5), (door.x + 3, y), (door.right - 3, y))
    pygame.draw.circle(surface, theme.mix(ACCENT, theme.INK, 0.2), (door.centerx, door.y - 6), 3)       # "sealed" lamp


def build_room(room, size):
    """The baked room: floor, wall and the room's own furniture."""
    width, height = size
    surface = pygame.Surface(size)
    _floor(surface, width, height)
    _patrol_line(surface, width)
    _FLOORS[room](surface)
    _wall(surface, width)
    _side_walls(surface, width, height)
    _DRESSING[room](surface)
    if room == 1:
        _vending(surface)
    vignette = pygame.Surface(size, pygame.SRCALPHA)
    for i in range(36):
        pygame.draw.rect(vignette, (0, 0, 0, int(150 * (1 - i / 36) ** 2)),
                         (i, i, width - 2 * i, height - 2 * i), 1)
    surface.blit(vignette, (0, 0))
    pygame.draw.rect(surface, theme.mix(WALL, theme.INK, 0.6), (0, 0, width, height), 6)
    pygame.draw.rect(surface, theme.mix(ACCENT, WALL, 0.55), (6, 6, width - 12, height - 12), 1)
    return surface


# --- live parts ---------------------------------------------------------------

def draw_wall_life(surface, room, t, origin=(40, 30)):
    """The small things that move on the wall: LEDs, monitor flicker, WARDEN's eye."""
    ox, oy = origin
    if room == 1:
        lit = (int(t * 0.8) % 2 == 0)
        pygame.draw.circle(surface, theme.TEAL if lit else theme.SLATE, (ox + 228, oy + 96), 3)   # time clock LED
    elif room == 2:
        for row in range(2):
            for col in range(4):
                screen = pygame.Rect(ox + 20 + col * 62, oy + 52 + row * 34, 54, 28).inflate(-6, -6)
                sweep = int((t * 14 + col * 9 + row * 17) % screen.height)
                pygame.draw.line(surface, theme.mix(theme.INK, ACCENT, 0.55),
                                 (screen.x, screen.y + sweep), (screen.right - 1, screen.y + sweep))
        if int(t * 1.2) % 2 == 0:
            pygame.draw.circle(surface, theme.CORAL, (ox + 300, oy + 58), 3)                      # REC
    else:
        pulse = 0.5 + 0.5 * math.sin(t * 2.0)
        pygame.draw.circle(surface, theme.mix(theme.CORAL, theme.PAPER, 0.25 * pulse), (ox + 185, oy + 82), 9)


def draw_header(surface, room, question_no, total, difficulty, points, time_left):
    """One slim line: where you are on the left, the clock on the right."""
    panel = pygame.Surface(HEADER.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (*theme.INK, 215), panel.get_rect(), border_radius=6)
    surface.blit(panel, HEADER.topleft)
    pygame.draw.line(surface, ACCENT, (HEADER.x + 6, HEADER.bottom - 1), (HEADER.right - 6, HEADER.bottom - 1), 2)
    title = ui_font(18, bold=True).render(f"FLOOR 3  NIGHT PATROL  |  ROOM {room}/3 {ROOM_NAMES[room]}",
                                          True, theme.PAPER)
    surface.blit(title, (HEADER.x + 10, HEADER.centery - title.get_height() // 2))
    clock = ui_font(20, bold=True).render(f"{time_left:4.1f}s", True,
                                          theme.CORAL if time_left < 6 else theme.GOLD)
    clock_rect = clock.get_rect(midright=(HEADER.right - 10, HEADER.centery))
    surface.blit(clock, clock_rect)
    info = ui_font(15).render(f"Q {question_no}/{total}  |  {difficulty.upper()}  |  {points} pts", True, theme.MIST)
    surface.blit(info, info.get_rect(midright=(clock_rect.left - 18, HEADER.centery)))


def draw_notice(surface, text_lines):
    """The objective, as a worn state form pinned to the wall: stained paper, a pin, a red stamp."""
    _frame(surface, NOTICE, (198, 190, 156), (110, 100, 72))
    pygame.draw.line(surface, (176, 168, 134), (NOTICE.x + 3, NOTICE.bottom - 4), (NOTICE.right - 4, NOTICE.bottom - 4))   # a fold
    pygame.draw.circle(surface, theme.CORAL, (NOTICE.centerx, NOTICE.y + 5), 3)                # the pin
    font = ui_font(14, bold=True)
    for i, line in enumerate(text_lines):
        img = font.render(line, True, (40, 36, 28))
        surface.blit(img, (NOTICE.x + 8, NOTICE.y + 12 + i * 15))
    stamp = ui_font(11, bold=True).render("FORM 7-C", True, (170, 40, 36))
    ring = pygame.Surface((stamp.get_width() + 8, stamp.get_height() + 4), pygame.SRCALPHA)
    pygame.draw.rect(ring, (170, 40, 36, 190), ring.get_rect(), 1, border_radius=3)
    ring.blit(stamp, (4, 2))
    ring = pygame.transform.rotate(ring, 12)
    ring.set_alpha(170)
    surface.blit(ring, ring.get_rect(bottomright=(NOTICE.right - 3, NOTICE.bottom - 3)))


def draw_camera_board(surface, bank, t):
    """Room 2's board: the camera loop as code.  It stops when the gate opens."""
    panel = pygame.Surface(BOARD.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (*theme.INK, 225), panel.get_rect(), border_radius=6)
    pygame.draw.rect(panel, (*ACCENT, 255), panel.get_rect(), 2, border_radius=6)
    surface.blit(panel, BOARD.topleft)
    head = ui_font(13, bold=True).render("PATROL  LOOP", True, ACCENT)
    surface.blit(head, (BOARD.x + 10, BOARD.y + 4))

    seen = bank.on and bank.seen_by is not None
    font = code_font(17)
    lines = (
        ("while camera.on:", theme.SKY if bank.on else theme.SLATE),
        ("    sweep()", theme.CORAL if seen else (theme.GOLD if bank.on else theme.SLATE)),
        ("camera.on = False", theme.SLATE if bank.on else theme.TEAL),
    )
    for i, (text, colour) in enumerate(lines):
        surface.blit(font.render(text, True, colour), (BOARD.x + 10, BOARD.y + 20 + i * 15))

    chip = ui_font(14, bold=True).render("on = True" if bank.on else "on = False", True,
                                         theme.CORAL if seen else theme.MIST)
    surface.blit(chip, chip.get_rect(bottomright=(BOARD.right - 10, BOARD.bottom - 6)))
    pygame.draw.circle(surface, theme.CORAL if seen else theme.SLATE, (BOARD.right - 14, BOARD.y + 12), 4)


def draw_lane_board(surface, loop, gate_open, t, nested=False):
    """The lane loop as code.  The line being run lights up, the loop's own
    variable shows which lane it is on.  Room 3 nests it in the robot's `while`
    loop, and the open gate runs `break`."""
    panel = pygame.Surface(BOARD.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (*theme.INK, 225), panel.get_rect(), border_radius=6)
    pygame.draw.rect(panel, (*ACCENT, 255), panel.get_rect(), 2, border_radius=6)
    surface.blit(panel, BOARD.topleft)
    head = ui_font(13, bold=True).render("PATROL  LOOP", True, ACCENT)
    surface.blit(head, (BOARD.x + 10, BOARD.y + 4))

    phases = loop.phases()
    live = "active" in phases
    lane = loop.current_lane()
    resting = loop.resting() or gate_open

    font = code_font(17)
    loop_colour = theme.GOLD if "warning" in phases and not live else theme.SKY
    if nested:
        lines = (
            ("while patrol():", theme.TEAL if gate_open else theme.SKY),
            ("  for lane in range(3):", loop_colour),
            ("    zap(lane)", theme.CORAL if live else theme.SLATE),
        )
    else:
        lines = (
            ("for lane in range(4):", loop_colour),
            ("    zap(lane)", theme.CORAL if live else theme.SLATE),
            ("rest()", theme.TEAL if resting else theme.SLATE),
        )
    for i, (text, colour) in enumerate(lines):
        surface.blit(font.render(text, True, colour), (BOARD.x + 10, BOARD.y + 20 + i * 15))

    if nested and gate_open:
        chip, chip_colour = "break", theme.TEAL
    else:
        chip, chip_colour = (f"lane = {lane}" if lane is not None else "lane = -"), (theme.CORAL if live else theme.MIST)
    img = ui_font(14, bold=True).render(chip, True, chip_colour)
    surface.blit(img, img.get_rect(bottomright=(BOARD.right - 10, BOARD.bottom - 6)))
    pygame.draw.circle(surface, theme.CORAL if live else theme.SLATE, (BOARD.right - 14, BOARD.y + 12), 4)


# --- the night guard and the lighting ------------------------------------------

AMBIENT = (150, 160, 166)                               # dim, cool: the wing runs on night lighting
GUARD_ROUTES = {1: [(466, 246), (508, 246)], 2: [(330, 246), (640, 246)], 3: [(330, 246), (640, 246)]}
GUARD_ROUTE = GUARD_ROUTES[2]                  # the clear floor between the robot lane and the curtains
GUARD_IDLE_EVERY = 18.0
GUARD_GREETING = {
    1: "Night shift. Mind the beam.",
    2: "The cameras see you. I only pretend not to.",
    3: "Last checkpoint. Nobody gets this far.",
}
GUARD_IDLE = {
    1: ("Nobody told me the loop had a break.", "Same lap, every night."),
    2: ("Forty screens. Nothing ever happens.", "Count the cycle. Then go."),
    3: ("Three rooms, one loop. I am not paid enough.", "WARDEN never blinks. I do."),
}
GUARD_HIT = "Told you. Count the cycle."
GUARD_ALERT = "The droid saw you. Keep moving."

DROID_ROUTE_Y = 166                                     # its feet sit on the dashed patrol line
DROID_NOTICE = "Courier. Badge logged."
DROID_ALERT = "Unauthorised. Hold position."
DROID_GRACE = 2.5                                         # the droid cannot spot you for this long after a room starts

DROID_IDLE_EVERY = 15.0
DROID_IDLE = ("Patrol 7. Nothing to report.", "Counting lanes. Four. Three. Four.", "Every loop ends. Mine does not.")
DROID_STAND_DOWN = "Patrol ended. Standing down."
EXCHANGE_RANGE = 120                                    # how close the guard and the droid must pass to talk
EXCHANGE_REPLY_AFTER = 1.6                               # the droid answers a beat after the guard, so the bubbles never stack
EXCHANGE = ("Evening, Unit 7.", "Greeting logged.")

_WALL_LAMPS = {
    1: ((150, 96), (255, 236, 200), 150, 0.8),          # over the lockers
    2: ((130, 90), (110, 220, 200), 160, 0.9),          # the monitors' glow
    3: ((185, 82), (255, 107, 94), 150, 0.9),           # WARDEN's plaque
}


def room_lights(room, beams, emitters, robot_centre, robot_alert, gate_centre, gate_open):
    """Every light in a room, in room-local coordinates (the room surface starts at 0, 0).

    beams: [(rect, phase)]; emitters: [(x, y, phase)]; phase is off/warning/active.
    """
    lamp = _WALL_LAMPS[room]
    lights = [Light(lamp[0], lamp[2], lamp[1], lamp[3]),
              Light((440, 290), 300, (210, 222, 235), 0.45)]            # the corridor's own ceiling light
    for rect, phase in beams:
        if phase == "active":
            lights.append(Light(rect.center, 120, (255, 70, 60), 1.1))
        elif phase == "warning":
            lights.append(Light(rect.center, 70, (255, 190, 60), 0.6))
    for x, y, phase in emitters:
        colour = {"active": (255, 70, 60), "warning": (255, 190, 60)}.get(phase, (120, 120, 140))
        lights.append(Light((x, y), 34, colour, 0.7 if phase != "off" else 0.25))
    lights.append(Light(robot_centre, 130, (255, 70, 60) if robot_alert else (120, 220, 255),
                        1.0 if robot_alert else 0.55))
    lights.append(Light(gate_centre, 100, (64, 214, 190) if gate_open else (255, 70, 70), 0.8))
    return lights
