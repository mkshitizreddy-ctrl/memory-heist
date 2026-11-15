"""
tests/test_sidebars.py

The 16:9 window: the game still draws into a 960x640 slice in the middle, the
strips either side are filled with the floor's wall panels, and nothing is drawn
over the game itself.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core import display
from ui import sidebars


@pytest.fixture(autouse=True)
def display_init():
    pygame.init()


def test_the_canvas_is_sixteen_by_nine_and_the_game_keeps_its_size():
    w, h = display.CANVAS_SIZE
    assert abs(w / h - 16 / 9) < 0.01
    window = pygame.Surface(display.CANVAS_SIZE)
    area = display.game_area(window)
    assert area.get_size() == display.GAME_SIZE
    assert area.get_abs_offset() == (display.SIDE_WIDTH, 0)


def test_a_plain_960_window_is_used_whole():
    window = pygame.Surface(display.GAME_SIZE)
    assert display.game_area(window).get_abs_offset() == (0, 0)


@pytest.mark.parametrize("state, level", [("menu", None), ("playing", "level1"), ("playing", "final_vault")])
def test_the_strips_are_filled_and_the_game_is_left_alone(state, level):
    window = pygame.Surface(display.CANVAS_SIZE)
    window.fill((1, 2, 3))
    sidebars.draw_sidebars(window, state, level, 1.0)
    w, h = window.get_size()
    assert window.get_at((10, 300))[:3] != (1, 2, 3)                   # left strip painted
    assert window.get_at((w - 10, 300))[:3] != (1, 2, 3)               # right strip painted
    for x in (display.SIDE_WIDTH, w // 2, w - display.SIDE_WIDTH - 1):
        assert window.get_at((x, 300))[:3] == (1, 2, 3)                # the game area untouched


def test_each_floor_has_its_own_strip_colour():
    left = {}
    for level in ("level1", "level3", "final_vault"):
        window = pygame.Surface(display.CANVAS_SIZE)
        sidebars.draw_sidebars(window, "playing", level, 0.0)
        left[level] = window.get_at((display.SIDE_WIDTH - 2, 300))[:3]
    assert len(set(left.values())) == 3


def test_nothing_is_drawn_when_the_window_has_no_strips():
    window = pygame.Surface(display.GAME_SIZE)
    window.fill((1, 2, 3))
    sidebars.draw_sidebars(window, "playing", "level2", 0.0)
    assert window.get_at((10, 300))[:3] == (1, 2, 3)


def test_the_real_game_draws_into_the_middle_of_a_wide_window():
    from core.game import Game
    game = Game()
    try:
        assert game.window.get_size() == display.CANVAS_SIZE
        assert game.screen.get_size() == display.GAME_SIZE
        game.update(1 / 60)
        game.render()
    finally:
        game.music.stop()
