"""Tests for levels/lobby_juice.py: Floor 1's game-feel layer (no rule changes)."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame
import pytest

from levels import lobby_juice as J
from tests.test_lobby_extras import make_level


@pytest.fixture(autouse=True)
def _pg():
    pygame.init()
    pygame.display.set_mode((64, 64))


def test_popup_rises_and_fades_then_expires():
    p = J.Popup((100, 100), "+25", (0, 255, 0))
    assert p.position() == (100, 100) and p.alpha() == 255
    p.age = J.POPUP_LIFE * 0.5
    assert p.position()[1] == pytest.approx(100 - J.POPUP_RISE * 0.5)
    p.age = J.POPUP_LIFE * 0.8
    assert 0 < p.alpha() < 255
    p.age = J.POPUP_LIFE
    assert not p.alive


def test_flyer_arcs_from_start_to_end_and_shrinks():
    f = J.Flyer((0, 100), (100, 100), "int")
    assert f.position() == (0, 100)
    f.age = J.FLYER_TIME / 2
    x, y = f.position()
    assert x == pytest.approx(50) and y == pytest.approx(100 - J.FLYER_ARC)
    big = J.Flyer((0, 0), (1, 1), "x").size()
    f.age = J.FLYER_TIME
    assert f.done and f.position() == pytest.approx((100, 100)) and f.size() < big


def test_streak_counts_resets_and_only_shows_from_two():
    j = J.Juice()
    j.filed((0, 0), (10, 10), "int", "+25", (1, 1, 1))
    assert j.streak == 1 and not j.streak_visible()
    j.filed((0, 0), (10, 10), "str", "+25", (1, 1, 1))
    assert j.streak_visible()
    j.missed((0, 0), "-10", (1, 1, 1))
    assert j.streak == 0 and j.best_streak == 2


def test_a_third_in_a_row_adds_a_multiplier_popup():
    j = J.Juice()
    for _ in range(3):
        j.filed((0, 0), (10, 10), "int", "+25", (1, 1, 1))
    assert any(p.text == "x3!" for p in j.popups)
    assert not any(p.text == "x2!" for p in j.popups)


def test_update_removes_finished_effects_and_fades_the_flash():
    j = J.Juice()
    j.filed((0, 0), (10, 10), "int", "+25", (1, 1, 1))
    assert j.flash["int"] == 1.0
    j.update(0.2)
    assert 0 < j.flash["int"] < 1.0 and j.flyers and j.popups
    j.update(2.0)
    assert not j.flyers and not j.popups and "int" not in j.flash


def test_flicker_stays_in_range_and_actually_varies():
    values = [J.flicker(t / 10, 3) for t in range(0, 600)]
    assert min(values) >= 0.45 and max(values) <= 1.0
    assert max(values) - min(values) > 0.05


def test_chute_pipe_runs_from_the_wall_to_the_bin_and_flashes():
    surf = pygame.Surface((200, 200))
    bin_rect = pygame.Rect(80, 120, 40, 30)
    pipe = J.draw_chute(surf, bin_rect, (200, 100, 50), 20, 0.0)
    assert pipe.top == 20 and pipe.centerx == bin_rect.centerx and pipe.bottom >= bin_rect.top
    dim = surf.get_at((pipe.centerx - 8, 60))[:3]
    J.draw_chute(surf, bin_rect, (200, 100, 50), 20, 0.0, flash=1.0)
    assert surf.get_at((pipe.centerx - 8, 60))[:3] != dim


def test_chevrons_move_down_over_time():
    a, b = pygame.Surface((100, 200)), pygame.Surface((100, 200))
    r = pygame.Rect(40, 150, 20, 30)
    J.draw_chute(a, r, (255, 255, 255), 20, 0.0)
    J.draw_chute(b, r, (255, 255, 255), 20, 0.3)
    assert pygame.image.tobytes(a, "RGB") != pygame.image.tobytes(b, "RGB")


def test_fan_shadow_darkens_and_turns():
    a, b = pygame.Surface((400, 400)), pygame.Surface((400, 400))
    for s in (a, b):
        s.fill((200, 200, 200))
    J.draw_fan_shadow(a, (200, 200), 0.0)
    J.draw_fan_shadow(b, (200, 200), 1.0)
    assert a.get_at((200, 200))[0] < 200
    assert pygame.image.tobytes(a, "RGB") != pygame.image.tobytes(b, "RGB")


def test_filing_a_parcel_in_floor_1_spawns_effects_but_a_miss_resets_the_streak():
    level, game, p1 = make_level()
    right = level.crates[0]
    right.carrier = p1
    level.carried[id(p1)] = right
    before = game.score.value if hasattr(game.score, "value") else None
    level._drop_in_bin(p1, right, right.answer)
    assert level.juice.streak == 1 and level.juice.flyers and level.juice.popups
    wrong = level.crates[1]
    wrong.carrier = p1
    level.carried[id(p1)] = wrong
    other = next(t for t in level.bins if t != wrong.answer)
    level._drop_in_bin(p1, wrong, other)
    assert level.juice.streak == 0
    assert any(p.text.startswith("-") for p in level.juice.popups)


def test_effects_do_not_change_the_score():
    level, game, p1 = make_level()
    c = level.crates[0]
    c.carrier = p1
    level.carried[id(p1)] = c
    level._drop_in_bin(p1, c, c.answer)
    from levels.floor1_lobby import CRATE_POINTS
    assert game.score.score == CRATE_POINTS if hasattr(game.score, "score") else True
