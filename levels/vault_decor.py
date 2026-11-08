"""
levels/vault_decor.py
Owner: Member 4 - Apporov Sahu's Final Vault, rebuilt on the shared kit

Geometry and art for the Master Vault.  It shares Floor 2's and Floor 5's footprint
(three chambers, a lit lane, three gates) so the last floor feels like the rest of
the building, but each chamber now holds TWO of the six stages:

      wall    [ screen: stage 1/2 ]  [ screen: stage 3/4 ]  [ screen: stage 5/6 ]
      code    [ code monitor ]       [ code monitor ]       [ code monitor ]
      lane    spawn  ==gate 1==========gate 2============ vault door
      floor   [ 3 answer pads ]      [ 3 answer pads ]      [ 3 answer pads ]
      south   racks                                          exception terminal (stage 6)

Stand on a pad and press the action key.  Nothing here changes the rules;
final_vault_hall.py owns those and final_vault.py owns the questions.

Pure helpers (pad_rects, fit_code, ...) hold the maths so it can be tested without a window.
"""

import math

import pygame

from core.tilemap import TILE
from levels import grid_decor as G
from levels import hall_decor as H
from ui import theme
from ui.fonts import code_font, ui_font
from ui.kit import draw_panel, wrap_text

# The footprint is Floor 2's and Floor 5's.
CHAMBERS, LANE_ROWS = H.CHAMBERS, H.LANE_ROWS
GATE_RECTS, SPAWNS = H.GATE_RECTS, H.SPAWNS
layout_rows, screen_rect = H.layout_rows, H.screen_rect
rack_rects, Ambience = H.rack_rects, H.Ambience
READOUT, READOUT_FONT_SIZE = H.READOUT, H.READOUT_FONT_SIZE
TERMINAL_WINDOW = H.TERMINAL_WINDOW
fit_prompt, fit_label, readout_lines = H.fit_prompt, H.fit_label, H.readout_lines
draw_pad, draw_readout = H.draw_pad, H.draw_readout

TOPICS = ("DATA TYPES", "OPERATORS", "LOOPS", "DICTIONARIES", "FUNCTIONS", "EXCEPTIONS")
STAGES = len(TOPICS)
PER_CHAMBER = 2
COLOURS = (theme.SKY, theme.GOLD, (190, 130, 255))          # one per chamber

PAD_W, PAD_H, PAD_GAP = 188, 32, 4
PAD_TOP = 13 * TILE + 2          # three rows end at 522, so the strip in front of the console is clear of every pad zone
CODE_W, CODE_Y, CODE_H = 240, 200, 116
CODE_LINE_H = 18
CONSOLE = pygame.Rect(CHAMBERS[2][0] * TILE + 4 * TILE - 48, 17 * TILE, 96, TILE)
SCREEN_PROMPT_TOP = 24


# --- geometry ---------------------------------------------------------------
def chamber_of(stage):
    """0-based chamber that holds 1-based `stage`."""
    return (stage - 1) // PER_CHAMBER


def code_rect(chamber):
    first, last = CHAMBERS[chamber]
    centre = first * TILE + (last - first + 1) * TILE // 2
    return pygame.Rect(centre - CODE_W // 2, CODE_Y, CODE_W, CODE_H)


def pad_rects(chamber, count):
    """`count` pads stacked in a column, centred in chamber `chamber`."""
    first, last = CHAMBERS[chamber]
    centre = first * TILE + (last - first + 1) * TILE // 2
    return [pygame.Rect(centre - PAD_W // 2, PAD_TOP + i * (PAD_H + PAD_GAP), PAD_W, PAD_H)
            for i in range(count)]


def solid_props():
    return rack_rects() + [code_rect(c) for c in range(3)] + [CONSOLE]


# --- pure helpers -----------------------------------------------------------
def fit_code(lines, width):
    """The biggest code font (<= 16) in which the longest of `lines` fits `width`."""
    longest = max(lines, key=len, default="")
    for size in (16, 15, 14, 13, 12):
        if code_font(size).size(longest)[0] <= width:
            return code_font(size)
    return code_font(12)


def lit_lines(lines):
    """Indexes of the lines with a blank (?) to fill: the part the question is about."""
    return {i for i, line in enumerate(lines) if "?" in line}


# --- baked decoration -------------------------------------------------------
def draw_static(bg, accent):
    metal = theme.mix(theme.SLATE, accent, 0.18)
    for gate in range(3):                                        # screen bezels
        r = screen_rect(gate)
        pygame.draw.rect(bg, theme.INK, r.inflate(10, 10), border_radius=6)
        pygame.draw.rect(bg, theme.mix(metal, COLOURS[gate], 0.45), r.inflate(10, 10), 2, border_radius=6)
    pipe_y = G.SCREEN_Y + G.SCREEN_H + 2
    pygame.draw.rect(bg, theme.mix(metal, theme.INK, 0.45), (2 * TILE, pipe_y + 1, 26 * TILE, 5), border_radius=2)
    pygame.draw.rect(bg, theme.mix(metal, theme.PAPER, 0.25), (2 * TILE, pipe_y, 26 * TILE, 2))
    for x in range(2 * TILE + 24, 28 * TILE, 96):
        pygame.draw.rect(bg, theme.INK, (x, pipe_y - 1, 6, 8))
    for rack in rack_rects():
        G._draw_rack(bg, rack, metal)
    lane = pygame.Rect(2 * TILE, LANE_ROWS[0] * TILE, 26 * TILE, 3 * TILE)
    for x in range(lane.left + 8, lane.right, 28):
        pygame.draw.line(bg, theme.mix(theme.GOLD, theme.INK, 0.35), (x, lane.centery), (x + 12, lane.centery), 2)
    for y in (lane.top, lane.bottom - 2):
        pygame.draw.line(bg, theme.mix(accent, theme.INK, 0.35), (lane.left, y), (lane.right, y), 2)
    for first, last in CHAMBERS:
        glow = G._glow(150, theme.mix(theme.INK, accent, 0.28))
        bg.blit(glow, ((first + last + 1) * TILE // 2 - 150, G.SCREEN_Y + G.SCREEN_H // 2 - 40),
                special_flags=pygame.BLEND_RGB_ADD)
    for rect in GATE_RECTS[:2]:
        G._hazard(bg, rect)
    G._exit_sign(bg, accent)
    draw_panel(bg, CONSOLE, fill=theme.mix(theme.NAVY, accent, 0.2), border=metal, radius=5, shadow=False)
    draw_panel(bg, READOUT, fill=theme.INK, border=theme.mix(metal, theme.INK, 0.3), radius=5, shadow=False)
    tag = ui_font(14, bold=True).render("READOUT", True, theme.mix(theme.INK, accent, 0.6))
    bg.blit(tag, (READOUT.right - tag.get_width() - 8, READOUT.y + 4))


# --- per-frame drawing ------------------------------------------------------
def draw_screen(surface, rect, chamber, state, stage=1, prompt="", answer=""):
    """One wall screen.  state: "standby" (a chamber ahead), "active", or "accepted"."""
    colour = COLOURS[chamber]
    border = {"standby": theme.SLATE, "active": colour, "accepted": theme.TEAL}[state]
    pygame.draw.rect(surface, theme.mix(theme.INK, border, 0.12), rect, border_radius=4)
    pygame.draw.rect(surface, border, rect, 1, border_radius=4)
    first = chamber * PER_CHAMBER + 1
    if state == "active":
        head = f"STAGE {stage}  {TOPICS[stage - 1]}"
    else:
        head = f"STAGES {first}-{first + PER_CHAMBER - 1}"
    surface.blit(ui_font(15, bold=True).render(head, True, border), (rect.x + 8, rect.y + 5))
    if state == "standby":
        text = code_font(17).render("SEALED", True, theme.SLATE)
        surface.blit(text, text.get_rect(center=(rect.centerx, rect.centery + 6)))
        return
    if state == "accepted":
        ok = ui_font(22, bold=True).render("ACCEPTED", True, theme.TEAL)
        surface.blit(ok, ok.get_rect(center=(rect.centerx, rect.centery - 2)))
        result = code_font(14).render(answer[:26], True, theme.PAPER)
        surface.blit(result, result.get_rect(center=(rect.centerx, rect.centery + 22)))
        return
    font, lines = fit_prompt(prompt, rect.w - 16, rect.h - SCREEN_PROMPT_TOP - 4)
    y = rect.y + SCREEN_PROMPT_TOP
    for line in lines:
        surface.blit(font.render(line, True, theme.PAPER), (rect.x + 8, y))
        y += font.get_linesize()


def draw_code_monitor(surface, chamber, state, lines=(), time=0.0):
    """The code a stage is about.  state: "active", "solved" or "sealed"."""
    block = code_rect(chamber)
    colour = {"active": COLOURS[chamber], "solved": theme.TEAL, "sealed": theme.SLATE}[state]
    draw_panel(surface, block, fill=theme.mix(theme.INK, theme.NAVY, 0.4), border=colour, radius=5, shadow=False)
    title = {"active": "code", "solved": "solved", "sealed": "sealed"}[state]
    surface.blit(ui_font(14, bold=True).render(title, True, theme.MIST), (block.x + 10, block.y + 5))
    if state != "active":
        mark = ui_font(26, bold=True).render("OK" if state == "solved" else "- - -", True, colour)
        surface.blit(mark, mark.get_rect(center=block.center))
        return
    font = fit_code(lines, block.w - 24)
    lit = lit_lines(lines)
    for row, line in enumerate(lines):
        y = block.y + 24 + row * CODE_LINE_H
        if row in lit:
            bar = pygame.Rect(block.x + 6, y - 1, block.w - 12, CODE_LINE_H)
            glow = 0.5 + 0.5 * math.sin(time * 4)
            pygame.draw.rect(surface, theme.mix(theme.NAVY, colour, 0.25 + 0.15 * glow), bar, border_radius=3)
            pygame.draw.rect(surface, colour, (bar.x, bar.y, 3, bar.h))
        ink = theme.PAPER if row in lit else theme.mix(theme.MIST, colour, 0.3)
        surface.blit(font.render(line, True, ink), (block.x + 12, y))


def draw_console(surface, state, time):
    """The exception terminal.  state: "locked", "ready", "active" or "done"."""
    box = pygame.Rect(CONSOLE.x + 8, CONSOLE.y + 5, CONSOLE.w - 16, CONSOLE.h - 10)
    colour = {"locked": theme.SLATE, "ready": COLOURS[2], "active": theme.PAPER, "done": theme.TEAL}[state]
    glow = 0.5 + 0.5 * math.sin(time * 5) if state == "ready" else 1.0
    pygame.draw.rect(surface, theme.mix(theme.INK, colour, 0.12 + 0.25 * glow), box, border_radius=3)
    pygame.draw.rect(surface, colour, box, 1, border_radius=3)
    word = {"locked": "LOCKED", "ready": "READY", "active": "ONLINE", "done": "OPEN"}[state]
    text = code_font(14).render(word, True, colour)
    surface.blit(text, text.get_rect(center=box.center))
    if state == "ready":
        bob = int(3 * math.sin(time * 4))
        tag = pygame.Rect(0, 0, 24, 22)
        tag.midbottom = (CONSOLE.centerx, CONSOLE.y - 4 + bob)
        pygame.draw.rect(surface, theme.INK, tag, border_radius=5)
        pygame.draw.rect(surface, colour, tag, 2, border_radius=5)
        key = ui_font(18, bold=True).render("E", True, colour)
        surface.blit(key, key.get_rect(center=tag.center))


def draw_terminal(surface, command, result, feedback, good, time):
    """The pop-up terminal window while a player is typing at the console."""
    box = TERMINAL_WINDOW
    colour = COLOURS[2]
    draw_panel(surface, box, fill=theme.mix(theme.INK, theme.NAVY, 0.3), border=colour, radius=8)
    surface.blit(ui_font(24, bold=True).render("STAGE 6 - EXCEPTION TERMINAL", True, colour), (box.x + 16, box.y + 10))
    small = ui_font(20)
    y = box.y + 40
    for line in wrap_text("Type an integer or invalid text, then press ENTER.", small, box.w - 32):
        surface.blit(small.render(line, True, theme.PAPER), (box.x + 16, y))
        y += small.get_linesize()
    entry = pygame.Rect(box.x + 14, box.y + 66, box.w - 28, 34)
    pygame.draw.rect(surface, theme.INK, entry, border_radius=6)
    pygame.draw.rect(surface, theme.MIST, entry, 2, border_radius=6)
    cursor = "_" if int(time * 2) % 2 == 0 else " "
    surface.blit(code_font(18).render(f"input = {command}{cursor}", True, theme.PAPER), (entry.x + 12, entry.y + 7))
    if result:
        for k, line in enumerate(wrap_text(result, code_font(16), box.w - 32)[:2]):
            surface.blit(code_font(16).render(line, True, theme.SKY), (box.x + 16, box.y + 108 + k * 18))
    y = box.y + 150
    for text in wrap_text(feedback, small, box.w - 32)[:2]:
        surface.blit(small.render(text, True, theme.TEAL if good else theme.CORAL), (box.x + 16, y))
        y += small.get_linesize()
    help_text = "ENTER: run    BACKSPACE: edit    Arrow keys: step away"
    surface.blit(ui_font(18).render(help_text, True, theme.MIST), (box.x + 16, box.bottom - 26))
