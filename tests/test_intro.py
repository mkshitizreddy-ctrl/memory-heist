"""The intro scene sits between the menu and Level 1 and never costs time."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.difficulty import get_difficulty, run_time_seconds
from core.game import Game
from core.story import STORY


class RecordingFont:
    def __init__(self, font):
        self._font = font
        self.texts = []

    def render(self, text, *args, **kwargs):
        self.texts.append(text)
        return self._font.render(text, *args, **kwargs)


def press(game, key, char=""):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=char))
    game.handle_events()


@pytest.fixture
def game():
    return Game()


@pytest.fixture
def at_intro(game):
    press(game, pygame.K_RETURN)  # start from the menu
    return game


def test_enter_on_the_menu_opens_the_intro_instead_of_starting_the_run(at_intro):
    assert at_intro.state == "intro"
    assert at_intro.timer.active is False


def test_the_intro_shows_the_intro_beat(at_intro):
    assert at_intro.story_screen.title == STORY["intro"]["title"]


def test_the_intro_knows_about_coop(game):
    game.menu.coop = True

    press(game, pygame.K_RETURN)

    assert game.story_screen.coop is True


def test_the_clock_does_not_run_during_the_intro(at_intro):
    at_intro.update(5.0)

    assert at_intro.timer.active is False
    assert at_intro.state == "intro"


def test_first_key_finishes_typing_and_second_starts_the_run(at_intro):
    press(at_intro, pygame.K_SPACE, " ")
    assert at_intro.state == "intro"

    press(at_intro, pygame.K_SPACE, " ")

    assert at_intro.state == "playing"


def test_the_run_timer_starts_full_when_the_intro_ends(at_intro):
    press(at_intro, pygame.K_SPACE, " ")
    press(at_intro, pygame.K_SPACE, " ")

    assert at_intro.timer.active is True
    assert at_intro.timer.get_remaining() == run_time_seconds(get_difficulty("medium"))


def test_escape_skips_the_intro_instead_of_quitting(at_intro):
    press(at_intro, pygame.K_ESCAPE)

    assert at_intro.running is True
    assert at_intro.state == "playing"


def test_the_key_that_ends_the_intro_does_not_reach_level_one(at_intro, monkeypatch):
    seen = []
    press(at_intro, pygame.K_SPACE, " ")
    monkeypatch.setattr(at_intro.level_manager, "handle_event", seen.append)
    press(at_intro, pygame.K_SPACE, " ")

    assert at_intro.state == "playing"
    assert seen == []


def test_story_can_be_switched_off(game):
    game.story_enabled = False

    press(game, pygame.K_RETURN)

    assert game.state == "playing"


def test_retry_after_a_loss_does_not_replay_the_intro(at_intro):
    press(at_intro, pygame.K_ESCAPE)
    at_intro.change_state("lose")

    press(at_intro, pygame.K_r, "r")

    assert at_intro.state == "playing"


def test_the_intro_is_drawn_by_the_game(at_intro):
    screen = at_intro.story_screen
    screen.title_font = RecordingFont(screen.title_font)

    at_intro.render()

    assert STORY["intro"]["title"] in screen.title_font.texts
