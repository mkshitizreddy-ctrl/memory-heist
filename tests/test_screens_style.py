"""Restyled menu, win and lose screens share one backdrop and layout rules."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from ui import backdrop, theme
from ui.kit import draw_chip
from ui.menu import MainMenu
from ui.screens import LoseScreen, WinScreen

SIZE = (960, 640)


class Board:
    def __init__(self, entries=()):
        self.entries = list(entries)

    def top(self, n):
        return self.entries[:n]

    def add(self, *a):
        return 1


ROWS = [{"name": "abcdefghijkl", "score": 99999, "difficulty": "Medium", "coop": True}] * 5


@pytest.fixture(autouse=True)
def init():
    pygame.init()


@pytest.fixture
def surf():
    return pygame.Surface(SIZE)


def snap(s):
    return pygame.image.tostring(s, "RGB")


# --- backdrop ------------------------------------------------------------
def test_motes_are_deterministic_in_bounds_and_drift():
    a = backdrop.mote_positions(10, backdrop.MOTE_COUNT, SIZE)
    assert a == backdrop.mote_positions(10, backdrop.MOTE_COUNT, SIZE)
    assert len(a) == backdrop.MOTE_COUNT
    for x, y, r, t in a:
        assert 0 <= x < SIZE[0] and 0 <= y < SIZE[1] and r >= 1 and 0 <= t <= 1
    b = backdrop.mote_positions(200, backdrop.MOTE_COUNT, SIZE)
    assert a != b
    assert len({(round(x), round(y)) for x, y, *_ in a}) > backdrop.MOTE_COUNT // 2


def test_gradient_and_vignette_are_cached_and_tinted():
    assert backdrop.gradient(SIZE, theme.TEAL) is backdrop.gradient(SIZE, theme.TEAL)
    assert backdrop.vignette(SIZE) is backdrop.vignette(SIZE)
    teal = backdrop.gradient(SIZE, theme.TEAL).get_at((480, 600))[:3]
    coral = backdrop.gradient(SIZE, theme.CORAL).get_at((480, 600))[:3]
    assert teal != coral and teal[1] > teal[0] and coral[0] > coral[1]


def test_vignette_darkens_corners_more_than_centre():
    v = backdrop.vignette(SIZE)
    assert v.get_at((2, 2)).a > v.get_at((480, 320)).a + 40


def test_backdrop_animates(surf):
    backdrop.draw_backdrop(surf, 0)
    a = snap(surf)
    backdrop.draw_backdrop(surf, 90)
    assert snap(surf) != a


# --- chip helper ---------------------------------------------------------
def test_filled_chip_is_solid_and_outlined_chip_is_not(surf):
    font = pygame.font.Font(None, 22)
    surf.fill((0, 0, 0))
    rect = pygame.Rect(100, 100, 170, 34)
    draw_chip(surf, rect, "x", font, border=theme.CORAL, filled=True)
    assert surf.get_at((112, 117))[:3] == theme.CORAL
    surf.fill((0, 0, 0))
    draw_chip(surf, rect, "x", font, border=theme.CORAL, filled=False)
    assert surf.get_at((112, 117))[:3] != theme.CORAL


# --- menu ----------------------------------------------------------------
def test_menu_layout_fits_and_nothing_overlaps():
    lay = MainMenu().layout()
    blocks = [lay["panel"], *lay["chips"], lay["coop"], lay["start"]]
    screen = pygame.Rect(0, 0, *SIZE)
    for b in blocks:
        assert screen.contains(b)
    for i, a in enumerate(blocks):
        for b in blocks[i + 1:]:
            assert not a.colliderect(b)
    for h in lay["heroes"]:
        assert screen.contains(h) and not h.colliderect(lay["panel"])


def test_menu_keys_still_work():
    m = MainMenu()
    for key, name in ((pygame.K_1, "easy"), (pygame.K_3, "hard"), (pygame.K_2, "medium")):
        m.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))
        assert m.selected_difficulty == name
    m.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_c))
    assert m.coop
    m.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(1, 1)))


def test_selected_difficulty_chip_is_the_solid_one(surf):
    m = MainMenu()
    tint = {"easy": theme.TEAL, "medium": theme.GOLD, "hard": theme.CORAL}
    for idx, name in enumerate(("easy", "medium", "hard")):
        m.selected_difficulty = name
        m.render(surf)
        for i, chip in enumerate(m.layout()["chips"]):
            solid = surf.get_at((chip.x + 14, chip.centery))[:3] == tint[("easy", "medium", "hard")[i]]
            assert solid == (i == idx)


def test_echo_is_dim_until_co_op_is_on(surf):
    m = MainMenu()
    echo = m.layout()["heroes"][1]
    m.render(surf)
    off = pygame.image.tostring(surf.subsurface(echo), "RGB")
    m.coop = True
    m.render(surf)
    on = pygame.image.tostring(surf.subsurface(echo), "RGB")
    bright = lambda b: sum(b)
    assert bright(on) > bright(off) * 1.3


def test_co_op_chip_fills_when_on(surf):
    m = MainMenu()
    chip = m.layout()["coop"]
    m.render(surf)
    off = surf.get_at((chip.x + 14, chip.centery))[:3]
    m.coop = True
    m.render(surf)
    assert surf.get_at((chip.x + 14, chip.centery))[:3] == theme.GOLD != off


# --- win screen ----------------------------------------------------------
def test_win_layout_blocks_fit_and_do_not_overlap():
    lay = WinScreen(leaderboard=Board()).layout()
    screen = pygame.Rect(0, 0, *SIZE)
    assert screen.contains(lay["score"]) and screen.contains(lay["table"])
    assert not lay["score"].colliderect(lay["table"])
    assert lay["table"].bottom <= SIZE[1] - 70           # room for the key prompt


def test_win_rows_stay_inside_the_table_with_the_longest_name(surf):
    w = WinScreen(leaderboard=Board(ROWS))
    w.skip_entry()
    table = w.layout()["table"]
    w.render(surf, 99999)
    last_row_bottom = table.y + 48 + 5 * 38
    assert last_row_bottom <= table.bottom
    # nothing painted past the table's right edge inside its band
    assert surf.get_at((table.right - 2, table.y + 120))[:3] != theme.PAPER


def test_own_leaderboard_row_is_highlighted(surf):
    w = WinScreen(leaderboard=Board(ROWS))
    w.skip_entry()
    table = w.layout()["table"]
    w.rank = 2
    w.render(surf, 5)
    y = table.y + 48 + 38 + 12
    mine = surf.get_at((table.x + 20, y))[:3]
    w.rank = None
    w.render(surf, 5)
    assert surf.get_at((table.x + 20, y))[:3] != mine


def test_win_name_cursor_blinks_and_typing_shows(surf):
    w = WinScreen(leaderboard=Board())
    w.begin(100, "Medium", False)
    w.name = "AB"
    w.tick = 0
    w.render(surf, 100)
    a = snap(surf)
    w.tick = 30
    w.render(surf, 100)
    assert snap(surf) != a


def test_win_screen_shows_echo_bright_only_for_co_op(surf):
    w = WinScreen(leaderboard=Board())
    w.skip_entry()
    rect = pygame.Rect(SIZE[0] // 2 + 380 - 96, 22, 96, 96)
    w.begin(1, "Medium", False); w.skip_entry(); w.render(surf, 1)
    solo = sum(pygame.image.tostring(surf.subsurface(rect), "RGB"))
    w.begin(1, "Medium", True); w.skip_entry(); w.render(surf, 1)
    duo = sum(pygame.image.tostring(surf.subsurface(rect), "RGB"))
    assert duo > solo * 1.3


# --- lose screen ---------------------------------------------------------
def test_lose_layout_fits_and_does_not_overlap():
    lay = LoseScreen().layout()
    screen = pygame.Rect(0, 0, *SIZE)
    for r in lay.values():
        assert screen.contains(r)
    assert not lay["score"].colliderect(lay["tip"])
    assert lay["eye"].bottom < 200                       # above the LOCKDOWN title


def test_lose_screen_is_red_tinted_and_pulses(surf):
    l = LoseScreen()
    l.render(surf, 5)
    r, g, b = surf.get_at((20, 600))[:3]
    assert r > g and r > b
    eye = l.layout()["eye"].inflate(60, 60)
    l.tick = 0; l.render(surf, 5)
    a = pygame.image.tostring(surf.subsurface(eye), "RGB")
    l.tick = 44; l.render(surf, 5)
    assert pygame.image.tostring(surf.subsurface(eye), "RGB") != a


def test_screens_render_a_huge_score_without_error(surf):
    LoseScreen().render(surf, 10 ** 9)
    w = WinScreen(leaderboard=Board())
    w.skip_entry()
    w.render(surf, 10 ** 9)


def test_filled_chip_text_is_dark_for_contrast(surf):
    font = pygame.font.Font(None, 22)
    surf.fill((0, 0, 0))
    rect = pygame.Rect(100, 100, 170, 34)
    draw_chip(surf, rect, "MMMM", font, fg=theme.CORAL, border=theme.CORAL, filled=True)
    inner = surf.subsurface(rect.inflate(-60, -10))
    colours = {tuple(inner.get_at((x, y)))[:3] for x in range(inner.get_width())
               for y in range(inner.get_height())}
    assert theme.CORAL in colours and theme.INK in colours
    assert theme.PAPER not in colours


def test_lose_screen_draws_the_alert_eye(surf):
    from core.hero_portrait import make_portrait
    l = LoseScreen()
    l.tick = 0
    l.render(surf, 1)
    eye = l.layout()["eye"]
    drawn = pygame.image.tostring(surf.subsurface(eye), "RGB")
    alert = make_portrait("warden", eye.width, l.tick, alert=True)
    calm = make_portrait("warden", eye.width, l.tick, alert=False)
    assert pygame.image.tostring(alert, "RGBA") != pygame.image.tostring(calm, "RGBA")
    # the centre of the drawn eye matches the alert art, not the calm art
    cx, cy = eye.width // 2, eye.height // 2
    assert surf.get_at((eye.centerx, eye.centery))[:3] == alert.get_at((cx, cy))[:3] or \
        surf.get_at((eye.centerx, eye.centery))[:3] != calm.get_at((cx, cy))[:3]


def test_motes_rise_over_time():
    a = backdrop.mote_positions(0, 12, SIZE)
    b = backdrop.mote_positions(40, 12, SIZE)
    risen = sum(1 for (_, y0, *_), (_, y1, *_) in zip(a, b) if y1 != y0)
    assert risen == 12
