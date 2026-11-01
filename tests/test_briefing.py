"""A story card opens before every level; the run clock stays frozen on it."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.game import Game
from core.level_manager import LEVEL_ORDER
from core.story import STORY


class RecordingFont:
    def __init__(self, font):
        self._font = font
        self.texts = []

    def render(self, text, *args, **kwargs):
        self.texts.append(text)
        return self._font.render(text, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._font, name)


def press(game, key, char=""):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=char))
    game.handle_events()


def close_card(game):
    """Two key presses: show all the text, then leave the card."""
    press(game, pygame.K_SPACE, " ")
    press(game, pygame.K_SPACE, " ")


@pytest.fixture
def game():
    return Game()


@pytest.fixture
def at_level1_briefing(game):
    press(game, pygame.K_RETURN)  # menu -> intro
    close_card(game)  # intro -> level 1 briefing
    return game


@pytest.fixture
def playing(game):
    press(game, pygame.K_RETURN)
    press(game, pygame.K_ESCAPE)  # skip the whole story
    assert game.state == "playing"
    return game


def finish_level(game):
    game.level_manager.current.complete = True
    game.update(0.016)


# ---- after the intro ------------------------------------------------------

def test_the_intro_leads_to_the_level_1_briefing(at_level1_briefing):
    game = at_level1_briefing

    assert game.state == "briefing"
    assert game.story_screen.title == STORY["level1"]["title"]
    assert game.story_screen.progress == (0, len(LEVEL_ORDER))


def test_the_clock_is_frozen_on_the_level_1_briefing(at_level1_briefing):
    game = at_level1_briefing
    before = game.timer.get_remaining()

    game.update(5.0)

    assert game.state == "briefing"
    assert game.timer.get_remaining() == before


def test_two_keys_close_the_briefing_and_none_reach_the_level(at_level1_briefing, monkeypatch):
    game = at_level1_briefing
    seen = []
    monkeypatch.setattr(game.level_manager, "handle_event", seen.append)

    close_card(game)

    assert game.state == "playing"
    assert seen == []


def test_escape_closes_the_briefing_instead_of_quitting(at_level1_briefing):
    press(at_level1_briefing, pygame.K_ESCAPE)

    assert at_level1_briefing.running is True
    assert at_level1_briefing.state == "playing"


def test_closing_a_briefing_starts_the_level_with_a_fade(at_level1_briefing):
    close_card(at_level1_briefing)

    assert at_level1_briefing._fade_timer > 0


# ---- between levels -------------------------------------------------------

def test_finishing_a_level_opens_the_next_levels_briefing(playing):
    finish_level(playing)

    assert playing.state == "briefing"
    assert playing.level_manager.current_name == "level2"
    assert playing.story_screen.title == STORY["level2"]["title"]
    assert playing.story_screen.progress == (1, len(LEVEL_ORDER))


def test_the_clock_is_frozen_on_a_level_briefing(playing):
    finish_level(playing)
    before = playing.timer.get_remaining()

    playing.update(4.0)

    assert playing.timer.get_remaining() == before


def test_every_level_gets_its_own_briefing_and_the_last_one_wins(playing):
    for index, name in enumerate(LEVEL_ORDER[1:], start=1):
        finish_level(playing)
        assert playing.state == "briefing"
        assert playing.story_screen.title == STORY[name]["title"]
        assert playing.story_screen.progress == (index, len(LEVEL_ORDER))
        close_card(playing)
        assert playing.state == "playing"

    finish_level(playing)  # the Final Vault

    assert playing.state == "win"


def test_retry_after_a_loss_goes_straight_back_into_the_run(playing):
    playing.change_state("lose")

    press(playing, pygame.K_r, "r")

    assert playing.state == "playing"


def test_no_briefings_when_the_story_is_switched_off(game):
    game.story_enabled = False
    press(game, pygame.K_RETURN)

    finish_level(game)

    assert game.state == "playing"
    assert game.level_manager.current_name == "level2"


# ---- drawing --------------------------------------------------------------

def test_the_briefing_is_drawn_with_the_route_map(at_level1_briefing):
    game = at_level1_briefing
    game.story_screen.map_font = RecordingFont(game.story_screen.map_font)

    game.render()

    assert game.story_screen.map_font.texts == ["1", "2", "3", "4", "5", "F"]
