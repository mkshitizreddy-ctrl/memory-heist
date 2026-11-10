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
BOARD_LINES = ("while True:", "    if laser_detected:", "        break")


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
    for x in range(24, width - 70, 28):
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


_DRESSING = {1: _lockers, 2: _monitors, 3: _checkpoint}


def build_room(room, size):
    """The baked room: floor, wall and the room's own furniture."""
    width, height = size
    surface = pygame.Surface(size)
    _floor(surface, width, height)
    _patrol_line(surface, width)
    _wall(surface, width)
    _DRESSING[room](surface)
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
    """The objective, as a notice pinned to the wall."""
    _frame(surface, NOTICE, (214, 206, 170), (120, 110, 80))
    pygame.draw.circle(surface, theme.CORAL, (NOTICE.centerx, NOTICE.y + 5), 3)                # the pin
    font = ui_font(14, bold=True)
    for i, line in enumerate(text_lines):
        img = font.render(line, True, (40, 36, 28))
        surface.blit(img, (NOTICE.x + 8, NOTICE.y + 12 + i * 15))


def draw_board(surface, laser_live, gate_open, t):
    """The same loop as code.  The 'if' line lights while a beam is live;
    'break' lights once the gate is open, as the patrol stops."""
    panel = pygame.Surface(BOARD.size, pygame.SRCALPHA)
    pygame.draw.rect(panel, (*theme.INK, 225), panel.get_rect(), border_radius=6)
    pygame.draw.rect(panel, (*ACCENT, 255), panel.get_rect(), 2, border_radius=6)
    surface.blit(panel, BOARD.topleft)
    head = ui_font(14, bold=True).render("PATROL  LOOP", True, ACCENT)
    surface.blit(head, (BOARD.x + 10, BOARD.y + 4))
    font = code_font(15)
    for i, line in enumerate(BOARD_LINES):
        if i == 0:
            colour = theme.SKY
        elif i == 1:
            colour = theme.CORAL if laser_live else DIM_CODE
        else:
            colour = theme.TEAL if gate_open else DIM_CODE
        surface.blit(font.render(line, True, colour), (BOARD.x + 10, BOARD.y + 21 + i * 15))
    dot = theme.CORAL if laser_live else theme.SLATE
    pygame.draw.circle(surface, dot, (BOARD.right - 14, BOARD.y + 12), 4)
