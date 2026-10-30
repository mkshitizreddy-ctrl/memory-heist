"""Win and lose screens: M returns to the menu, R on win starts a new run."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.game import Game


@pytest.fixture
def game():
    g = Game()
    g._start_new_run()
    return g


def press(game, key, char=""):
    """Deliver one key press to the game exactly as the event loop would."""
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=char))
    game.handle_events()


def lose(game):
    game.change_state("lose")


def win_with_name_saved(game):
    game.change_state("win")
    game.win_screen.entering = False  # the name has been entered and saved


def test_m_on_the_lose_screen_returns_to_the_menu(game):
    lose(game)

    press(game, pygame.K_m, "m")

    assert game.state == "menu"


def test_m_on_the_win_screen_returns_to_the_menu_once_the_name_is_saved(game):
    win_with_name_saved(game)

    press(game, pygame.K_m, "m")

    assert game.state == "menu"


def test_r_on_the_win_screen_starts_a_new_run_once_the_name_is_saved(game):
    game.score.add(40)
    win_with_name_saved(game)

    press(game, pygame.K_r, "r")

    assert game.state == "playing"
    assert game.score.get_score() == 0
    assert game.timer.active


def test_m_while_typing_a_name_is_just_a_letter(game):
    game.change_state("win")  # the screen is waiting for a name

    press(game, pygame.K_m, "m")

    assert game.state == "win"
    assert game.win_screen.name == "m"


def test_r_while_typing_a_name_is_just_a_letter(game):
    game.change_state("win")

    press(game, pygame.K_r, "r")

    assert game.state == "win"
    assert game.win_screen.name == "r"


def test_the_menu_key_does_not_reach_the_menu(game, monkeypatch):
    seen = []
    monkeypatch.setattr(game.menu, "handle_event", seen.append)
    lose(game)

    press(game, pygame.K_m, "m")

    assert game.state == "menu"
    assert seen == []


def test_menu_then_enter_starts_a_fresh_run(game):
    game.timer.remaining = 5
    lose(game)

    press(game, pygame.K_m, "m")
    press(game, pygame.K_RETURN)

    assert game.state == "playing"
    assert game.timer.active
    assert game.timer.get_remaining() == 900
