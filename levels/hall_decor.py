"""
levels/hall_decor.py
Owner: Member 4 - Apporov Sahu's Level 5, rebuilt on the shared kit

Geometry and art for Floor 5, the server hall.  The footprint is Floor 2's (three
chambers in a row, a lit lane through them, three gates) so the two floors feel
like one building, but the furniture and the rules of the room are Level 5's:

      wall    [ screen 1 ]   [ screen 2 ]   [ screen 3 ]      <- the questions
      code    [ def unlock_vault ........ ][ try / except .. ]  <- the program, lines lit
      lane    spawn  ==gate 1==========gate 2============ exit door
      floor   [ 2 x 2 pads ]  [ 2 x 2 pads ]  [ 2 x 2 pads ]   <- the answers
      south   racks                          racks + control terminal

Stand on a pad and press the action key to answer.  When the last question is
answered, the control terminal in the south-east corner wakes up.  Nothing here
changes the rules; level5_hall.py owns those, and level5_control.py owns the
scoring they were built from.

Pure helpers (pad_rects, code_size, fit_label, ...) hold the maths so it can be
tested without a window.
"""

import math

import pygame

from core.tilemap import TILE
from levels import grid_decor as G
from levels.level5_questions import CODE_LINES, GATES
from ui import theme
from ui.fonts import code_font, ui_font
from ui.kit import draw_panel, wrap_text

# The footprint is Floor 2's.
COLS, ROWS = G.COLS, G.ROWS
CHAMBERS, PARTITIONS, LANE_ROWS = G.CHAMBERS, G.PARTITIONS, G.LANE_ROWS
GATE_RECTS, SPAWNS = G.GATE_RECTS, G.SPAWNS
layout_rows, screen_rect = G.layout_rows, G.screen_rect

RACK_ROW = 16                                    # racks stand against the south wall
CODE_Y, CODE_H, CODE_W = 200, 116, 408
CODE_BLOCKS = (pygame.Rect(2 * TILE, CODE_Y, CODE_W, CODE_H),
               pygame.Rect(28 * TILE - CODE_W, CODE_Y, CODE_W, CODE_H))
BLOCK_LINES = ((0, 1, 2, 3), (5, 6, 7, 8, 9))     # which CODE_LINES each block shows
BLOCK_TITLES = ("unlock_vault.py", "recovery.py")
CODE_LINE_H = 18

PAD_W, PAD_H, PAD_GAP, ROW_GAP = 118, 40, 8, 6
PAD_TOP = 13 * TILE + 6

CONSOLE = pygame.Rect(G.CHAMBERS[2][0] * TILE + 4 * TILE - 48, RACK_ROW * TILE, 96, 2 * TILE)
READOUT = pygame.Rect(2 * TILE, 18 * TILE + 8, 26 * TILE, 46)
TERMINAL_WINDOW = pygame.Rect(220, 322, 520, 240)
SCREEN_PROMPT_TOP = 24


# --- geometry ---------------------------------------------------------------
def pad_rects(gate, count):
    """`count` pads in a two-wide grid, centred in chamber `gate`."""
    first, last = CHAMBERS[gate]
    centre = first * TILE + (last - first + 1) * TILE // 2
    left = centre - (2 * PAD_W + PAD_GAP) // 2
    return [pygame.Rect(left + (i % 2) * (PAD_W + PAD_GAP), PAD_TOP + (i // 2) * (PAD_H + ROW_GAP),
                        PAD_W, PAD_H) for i in range(count)]


def rack_rects():
    """Two racks per chamber, one against each partition."""
    return [pygame.Rect(col * TILE, RACK_ROW * TILE, TILE, 2 * TILE)
            for first, last in CHAMBERS for col in (first, last)]


def solid_props():
    """Everything in the room a player cannot walk through."""
    return rack_rects() + list(CODE_BLOCKS) + [CONSOLE]


# --- pure helpers -----------------------------------------------------------
def code_size():
    """The biggest code font (<= 16) whose longest program line fits a code block."""
    longest = max(CODE_LINES, key=len)
    room = CODE_W - 16 - 26
    for size in (16, 15, 14, 13, 12):
        if code_font(size).size(longest)[0] <= room:
            return size
    return 12


def fit_prompt(prompt, width, height):
    """(font, lines): the biggest prompt font whose wrapped text fits width x height."""
    font, lines = None, []
    for size in (18, 17, 16, 15, 14):
        font = code_font(size)
        lines = wrap_text(prompt, font, width)
        if len(lines) * font.get_linesize() <= height:
            return font, lines
    return font, lines


def fit_label(label, width, height):
    """(font, lines) for an answer on a pad: at most two lines, as big as will fit."""
    font, lines = None, []
    for size in (17, 16, 15, 14, 13, 12):
        font = code_font(size)
        lines = wrap_text(label, font, width)
        if len(lines) <= 2 and len(lines) * font.get_linesize() <= height:
            return font, lines
    return font, lines


def readout_lines(entries, font, width, limit=2):
    """Wrap (text, colour) entries to `width`, at most `limit` lines in all."""
    out = []
    for text, colour in entries:
        if not text:
            continue
        for line in wrap_text(text, font, width):
            out.append((line, colour))
    return out[:limit]


# --- baked decoration -------------------------------------------------------
def draw_static(bg, accent):
    metal = theme.mix(theme.SLATE, accent, 0.18)
    for gate in range(3):                                        # screen bezels, one colour per gate
        r = screen_rect(gate)
        pygame.draw.rect(bg, theme.INK, r.inflate(10, 10), border_radius=6)
        pygame.draw.rect(bg, theme.mix(metal, GATES[gate]["color"], 0.45), r.inflate(10, 10), 2, border_radius=6)
    pipe_y = G.SCREEN_Y + G.SCREEN_H + 2
    pygame.draw.rect(bg, theme.mix(metal, theme.INK, 0.45), (2 * TILE, pipe_y + 1, 26 * TILE, 5), border_radius=2)
    pygame.draw.rect(bg, theme.mix(metal, theme.PAPER, 0.25), (2 * TILE, pipe_y, 26 * TILE, 2))
    for x in range(2 * TILE + 24, 28 * TILE, 96):
        pygame.draw.rect(bg, theme.INK, (x, pipe_y - 1, 6, 8))
    for rack in rack_rects():
        G._draw_rack(bg, rack, metal)
    lane = pygame.Rect(2 * TILE, LANE_ROWS[0] * TILE, 26 * TILE, 3 * TILE)
    for x in range(lane.left + 8, lane.right, 28):               # dashed centre line
        pygame.draw.line(bg, theme.mix(theme.GOLD, theme.INK, 0.35), (x, lane.centery), (x + 12, lane.centery), 2)
    for y in (lane.top, lane.bottom - 2):
        pygame.draw.line(bg, theme.mix(accent, theme.INK, 0.35), (lane.left, y), (lane.right, y), 2)
    for first, last in CHAMBERS:                                 # soft pools of light
        glow = G._glow(150, theme.mix(theme.INK, accent, 0.28))
        bg.blit(glow, ((first + last + 1) * TILE // 2 - 150, G.SCREEN_Y + G.SCREEN_H // 2 - 40),
                special_flags=pygame.BLEND_RGB_ADD)
    for rect in GATE_RECTS[:2]:
        G._hazard(bg, rect)
    G._exit_sign(bg, accent)
    draw_panel(bg, CONSOLE, fill=theme.mix(theme.NAVY, accent, 0.2), border=metal, radius=5, shadow=False)
    for i in range(6):                                           # keys on the console
        pygame.draw.rect(bg, theme.mix(theme.SLATE, theme.INK, 0.3), (CONSOLE.x + 10 + i * 14, CONSOLE.bottom - 18, 10, 6),
                         border_radius=1)
    draw_panel(bg, READOUT, fill=theme.INK, border=theme.mix(metal, theme.INK, 0.3), radius=5, shadow=False)
    tag = ui_font(14, bold=True).render("READOUT", True, theme.mix(theme.INK, accent, 0.6))
    bg.blit(tag, (READOUT.right - tag.get_width() - 8, READOUT.y + 4))


# --- per-frame drawing ------------------------------------------------------
class Ambience(G.Ambience):
    """Rack lights, data pulses along the lane and drifting motes."""

    def draw(self, world, accent):
        for i, rack in enumerate(rack_rects()):
            for j, pos in enumerate(G.rack_led_positions(rack)):
                state = G.led_state(self.time, i, j)
                colour = (theme.TEAL, theme.GOLD)[state - 1] if state else theme.mix(theme.INK, theme.SLATE, 0.5)
                pygame.draw.rect(world, colour, (pos[0], pos[1], 4, 4))
        lane_top, lane_bottom = LANE_ROWS[0] * TILE + 1, (LANE_ROWS[-1] + 1) * TILE - 3
        for start, end, y in (((2 * TILE, 0), (28 * TILE, 0), lane_top),
                              ((28 * TILE, 0), (2 * TILE, 0), lane_bottom)):
            for x, _ in G.pulse_points(self.time, start, end):
                pygame.draw.rect(world, theme.mix(accent, theme.PAPER, 0.5), (int(x) - 5, y, 10, 2))
        for m in self.motes.motes:
            twinkle = 0.5 + 0.5 * math.sin(self.time * 1.5 + m["phase"])
            world.set_at((int(m["x"]), int(m["y"])), theme.mix(theme.INK, theme.MIST, 0.25 + 0.5 * twinkle))


def draw_screen(surface, rect, gate, state, prompt="", index=0, count=1, answer="", time=0.0):
    """One wall screen.  state: "standby" (a gate ahead), "active", or "accepted"."""
    colour = GATES[gate]["color"]
    border = {"standby": theme.SLATE, "active": colour, "accepted": theme.TEAL}[state]
    pygame.draw.rect(surface, theme.mix(theme.INK, border, 0.12), rect, border_radius=4)
    pygame.draw.rect(surface, border, rect, 1, border_radius=4)
    head = ui_font(15, bold=True).render(f"{GATES[gate]['label']}  {GATES[gate]['name']}", True, border)
    surface.blit(head, (rect.x + 8, rect.y + 5))
    if state == "standby":
        text = code_font(17).render("STANDBY", True, theme.SLATE)
        surface.blit(text, text.get_rect(center=(rect.centerx, rect.centery + 6)))
        return
    if state == "accepted":
        ok = ui_font(22, bold=True).render("ACCEPTED", True, theme.TEAL)
        surface.blit(ok, ok.get_rect(center=(rect.centerx, rect.centery - 2)))
        result = code_font(16).render(f"answer: {answer}", True, theme.PAPER)
        surface.blit(result, result.get_rect(center=(rect.centerx, rect.centery + 22)))
        return
    counter = code_font(14).render(f"Q {index + 1}/{count}", True, colour)
    surface.blit(counter, (rect.right - counter.get_width() - 8, rect.y + 6))
    font, lines = fit_prompt(prompt, rect.w - 16, rect.h - SCREEN_PROMPT_TOP - 4)
    y = rect.y + SCREEN_PROMPT_TOP
    for line in lines:
        surface.blit(font.render(line, True, theme.PAPER), (rect.x + 8, y))
        y += font.get_linesize()


def draw_pad(surface, rect, label, state, colour, time=0.0):
    """An answer pad.  state: "idle", "stand" (a player is on it), "right", "wrong", "out"."""
    fill = {"idle": theme.mix(theme.NAVY, colour, 0.25), "stand": theme.mix(theme.NAVY, colour, 0.5),
            "right": theme.mix(theme.NAVY, theme.TEAL, 0.6), "wrong": theme.mix(theme.NAVY, theme.CORAL, 0.6),
            "out": theme.mix(theme.INK, theme.SLATE, 0.3)}[state]
    edge = {"idle": colour, "stand": theme.PAPER, "right": theme.TEAL, "wrong": theme.CORAL,
            "out": theme.SLATE}[state]
    pygame.draw.rect(surface, (0, 0, 0), rect.move(2, 3), border_radius=8)
    pygame.draw.rect(surface, fill, rect, border_radius=8)
    pygame.draw.rect(surface, edge, rect, 2, border_radius=8)
    if state == "stand":
        glow = 0.5 + 0.5 * math.sin(time * 8)
        pygame.draw.rect(surface, theme.mix(edge, theme.INK, 0.4 + 0.3 * glow), rect.inflate(8, 8), 2, border_radius=10)
    font, lines = fit_label(label, rect.w - 12, rect.h - 6)
    ink = theme.MIST if state == "out" else theme.PAPER
    height = font.get_linesize()
    y = rect.centery - height * len(lines) // 2
    for line in lines:
        image = font.render(line, True, ink)
        box = image.get_rect(center=(rect.centerx, y + height // 2))
        surface.blit(image, box)
        if state == "out":
            pygame.draw.line(surface, theme.CORAL, (box.left, box.centery), (box.right, box.centery), 2)
        y += height


def draw_code_blocks(surface, lit, time=0.0):
    """The program on the wall, in two blocks.  `lit` holds the CODE_LINES indexes to highlight."""
    font = code_font(code_size())
    for block, lines, title in zip(CODE_BLOCKS, BLOCK_LINES, BLOCK_TITLES):
        draw_panel(surface, block, fill=theme.mix(theme.INK, theme.NAVY, 0.4), border=theme.SLATE,
                   radius=5, shadow=False)
        head = ui_font(14, bold=True).render(title, True, theme.MIST)
        surface.blit(head, (block.x + 10, block.y + 5))
        for row, index in enumerate(lines):
            y = block.y + 24 + row * CODE_LINE_H
            on = index in lit
            if on:
                bar = pygame.Rect(block.x + 6, y - 1, block.w - 12, CODE_LINE_H)
                pygame.draw.rect(surface, theme.mix(theme.NAVY, theme.SKY, 0.35), bar, border_radius=3)
                pygame.draw.rect(surface, theme.SKY, (bar.x, bar.y, 3, bar.h))
            number = font.render(f"{index + 1:>2}", True, theme.mix(theme.SLATE, theme.MIST, 0.4))
            surface.blit(number, (block.x + 12, y))
            ink = theme.PAPER if on else theme.mix(theme.MIST, theme.SKY, 0.4)
            surface.blit(font.render(CODE_LINES[index], True, ink), (block.x + 38, y))


def draw_console(surface, state, time):
    """The control terminal.  state: "locked", "ready", "active" or "done"."""
    box = pygame.Rect(CONSOLE.x + 8, CONSOLE.y + 6, CONSOLE.w - 16, 30)
    colour = {"locked": theme.SLATE, "ready": GATES[2]["color"], "active": theme.PAPER, "done": theme.TEAL}[state]
    glow = 0.5 + 0.5 * math.sin(time * 5) if state == "ready" else 1.0
    pygame.draw.rect(surface, theme.mix(theme.INK, colour, 0.12 + 0.25 * glow), box, border_radius=3)
    pygame.draw.rect(surface, colour, box, 1, border_radius=3)
    word = {"locked": "LOCKED", "ready": "READY", "active": "ONLINE", "done": "OPEN"}[state]
    text = code_font(15).render(word, True, colour)
    surface.blit(text, text.get_rect(center=box.center))
    if state == "ready":
        bob = int(3 * math.sin(time * 4))
        tag = pygame.Rect(0, 0, 24, 22)
        tag.midbottom = (CONSOLE.centerx, CONSOLE.y - 6 + bob)
        pygame.draw.rect(surface, theme.INK, tag, border_radius=5)
        pygame.draw.rect(surface, colour, tag, 2, border_radius=5)
        key = ui_font(18, bold=True).render("E", True, colour)
        surface.blit(key, key.get_rect(center=tag.center))


READOUT_FONT_SIZE = 16


def draw_readout(surface, lines, font):
    y = READOUT.y + 6
    for text, colour in lines:
        surface.blit(font.render(text, True, colour), (READOUT.x + 12, y))
        y += font.get_linesize()


def draw_terminal(surface, command, result, feedback, good, hint, hint_cost, time):
    """The pop-up terminal window while a player is typing at the console."""
    box = TERMINAL_WINDOW
    colour = GATES[2]["color"]
    draw_panel(surface, box, fill=theme.mix(theme.INK, theme.NAVY, 0.3), border=colour, radius=8)
    title = ui_font(24, bold=True).render("GATE 3 - CONTROL TERMINAL", True, colour)
    surface.blit(title, (box.x + 16, box.y + 10))
    small = ui_font(20)
    y = box.y + 40
    for line in wrap_text("Type an access level for the vault door, then press ENTER.", small, box.w - 32):
        surface.blit(small.render(line, True, theme.PAPER), (box.x + 16, y))
        y += small.get_linesize()
    entry = pygame.Rect(box.x + 14, box.y + 66, box.w - 28, 34)
    pygame.draw.rect(surface, theme.INK, entry, border_radius=6)
    pygame.draw.rect(surface, theme.MIST, entry, 2, border_radius=6)
    cursor = "_" if int(time * 2) % 2 == 0 else " "
    mono = code_font(18)
    surface.blit(mono.render(f"entry = {command}{cursor}", True, theme.PAPER), (entry.x + 12, entry.y + 7))
    if result:
        surface.blit(mono.render(result[:52], True, theme.SKY), (box.x + 16, box.y + 108))
    y = box.y + 134
    lines = [(line, theme.TEAL if good else theme.CORAL) for line in wrap_text(feedback, small, box.w - 32)]
    lines += [(line, theme.GOLD) for line in wrap_text(hint, small, box.w - 32)] if hint else []
    for text, ink in lines[:3]:
        surface.blit(small.render(text, True, ink), (box.x + 16, y))
        y += small.get_linesize()
    help_text = f"ENTER: run    TAB: hint (-{hint_cost} pts)    Arrow keys: step away"
    surface.blit(ui_font(18).render(help_text, True, theme.MIST), (box.x + 16, box.bottom - 26))
