"""Finishing the Final Vault opens the ending card, then the win screen."""

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
    press(game, pygame.K_SPACE, " ")
    press(game, pygame.K_SPACE, " ")


def finish_level(game):
    game.level_manager.current.complete = True
    game.update(0.016)


def play_to_the_final_vault(game):
    """Finish levels 1-5, closing each briefing, until the Final Vault runs."""
    for _ in LEVEL_ORDER[:-1]:
        finish_level(game)
        close_card(game)
    assert game.level_manager.current_name == "final_vault"
    assert game.state == "playing"


@pytest.fixture
def game():
    g = Game()
    press(g, pygame.K_RETURN)
    press(g, pygame.K_ESCAPE)  # skip the intro: straight into Level 1
    assert g.state == "playing"
    return g


@pytest.fixture
def at_ending(game):
    play_to_the_final_vault(game)
    finish_level(game)
    return game


def test_finishing_the_final_vault_opens_the_ending_card(at_ending):
    assert at_ending.state == "outro"
    assert at_ending.story_screen.title == STORY["outro"]["title"]


def test_the_route_map_shows_every_level_done(at_ending):
    total = len(LEVEL_ORDER)

    assert at_ending.story_screen.progress == (total, total)


def test_the_clock_and_the_final_score_are_frozen_on_the_ending(game):
    play_to_the_final_vault(game)
    game.score.add(100)
    game.timer.remaining = 200.4
    finish_level(game)
    score = game.win_screen.score
    remaining = game.timer.get_remaining()

    game.update(10.0)

    assert game.timer.get_remaining() == remaining
    assert game.win_screen.score == score == 300  # (100 + 200) x 1.0 on Medium


def test_two_keys_leave_the_ending_for_the_win_screen_without_typing(at_ending):
    close_card(at_ending)

    assert at_ending.state == "win"
    assert at_ending.win_screen.entering is True
    assert at_ending.win_screen.name == ""


def test_escape_skips_the_ending_instead_of_quitting(at_ending):
    press(at_ending, pygame.K_ESCAPE)

    assert at_ending.running is True
    assert at_ending.state == "win"


def test_the_name_can_still_be_typed_after_the_ending(at_ending):
    close_card(at_ending)

    press(at_ending, pygame.K_a, "a")

    assert at_ending.win_screen.name == "a"


def test_no_ending_card_when_the_story_is_switched_off(game):
    play_to_the_final_vault(game)
    game.story_enabled = False

    finish_level(game)

    assert game.state == "win"


def test_losing_never_opens_the_ending(game):
    game.timer.remaining = 0.01

    game.update(1.0)

    assert game.state == "lose"


def test_the_ending_is_drawn_with_the_full_route_map(at_ending):
    screen = at_ending.story_screen
    screen.title_font = RecordingFont(screen.title_font)
    screen.map_font = RecordingFont(screen.map_font)

    at_ending.render()

    assert STORY["outro"]["title"] in screen.title_font.texts
    assert screen.map_font.texts == ["1", "2", "3", "4", "5", "F"]


def test_the_ending_wins_over_a_timer_that_runs_out_on_the_same_frame(game):
    play_to_the_final_vault(game)
    game.level_manager.current.complete = True
    game.timer.remaining = 0.01

    game.update(1.0)

    assert game.state == "outro"
