"""The HUD carries Ghost (and Echo in co-op), so every level shows the heroes."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.game import Game
from core.hero_portrait import BLINK_PERIOD
from ui.hud import HUD

WIDTH = 960


@pytest.fixture(autouse=True)
def display():
    pygame.init()
    pygame.display.set_mode((WIDTH, 640))


def bar_surface():
    s = pygame.Surface((WIDTH, 48))
    s.fill((0, 0, 0))
    return s


def lit(surface, rect):
    """Pixels inside rect that differ from the plain bar colour."""
    background = surface.get_at((595, 2))[:3]   # empty bar, left of the badges
    return sum(
        1
        for x in range(rect.left, rect.right)
        for y in range(rect.top, rect.bottom)
        if surface.get_at((x, y))[:3] != background
    )


def region(surface, rect):
    return pygame.image.tostring(surface.subsurface(rect), "RGBA")


def draw(hud, **kwargs):
    s = bar_surface()
    hud.render(s, "level1", score=120, security_level=40, timer_remaining=600, **kwargs)
    return s


def test_one_badge_for_a_solo_run_and_two_for_co_op():
    hud = HUD()

    assert len(hud.badge_rects(WIDTH, coop=False)) == 1
    assert len(hud.badge_rects(WIDTH, coop=True)) == 2


def test_ghost_is_on_the_left_and_echo_on_the_right():
    ghost, echo = HUD().badge_rects(WIDTH, coop=True)

    assert ghost.right <= echo.left


def test_the_solo_badge_sits_where_ghost_sits_in_co_op():
    solo = HUD().badge_rects(WIDTH, coop=False)[0]
    ghost, echo = HUD().badge_rects(WIDTH, coop=True)

    assert solo == echo or solo == ghost


@pytest.mark.parametrize("width", [960, 1280])
@pytest.mark.parametrize("coop", [False, True])
def test_badges_fit_inside_the_bar_and_clear_every_other_hud_item(width, coop):
    hud = HUD()
    taken = [
        pygame.Rect(16, 0, 150, 48),       # level label
        pygame.Rect(200, 0, 150, 48),      # score
        pygame.Rect(360, 0, 225, 48),      # security meter and its number
        pygame.Rect(width - 130, 0, 130, 48),  # timer
    ]
    for rect in hud.badge_rects(width, coop):
        assert 0 <= rect.top and rect.bottom <= 48
        assert rect.right <= width
        assert all(not rect.colliderect(t) for t in taken)


def test_the_badge_is_actually_drawn():
    hud = HUD()
    rect = hud.badge_rects(WIDTH, coop=False)[0]

    assert lit(draw(hud), rect) > 200


def test_co_op_draws_a_second_hero():
    hud = HUD()
    solo = lit(draw(hud, coop=False), pygame.Rect(600, 0, 200, 48))
    duo = lit(draw(hud, coop=True), pygame.Rect(600, 0, 200, 48))

    assert duo > solo


def test_the_badge_blinks():
    hud = HUD()
    rect = hud.badge_rects(WIDTH, coop=False)[0]

    assert region(draw(hud, tick=0), rect) != region(draw(hud, tick=BLINK_PERIOD - 1), rect)


def test_old_calls_without_the_new_arguments_still_work():
    hud = HUD()
    s = bar_surface()
    hud.render(s, "level1", score=5, security_level=10, timer_remaining=30)


def test_the_game_tells_the_hud_about_co_op(monkeypatch):
    game = Game()
    seen = {}
    original = game.hud.render

    def spy(surface, *args, **kwargs):
        seen.update(kwargs)
        return original(surface, *args, **kwargs)

    monkeypatch.setattr(game.hud, "render", spy)
    game.story_enabled = False
    game.coop = True
    game.change_state("playing")
    game.render()

    assert seen.get("coop") is True
    assert "tick" in seen
