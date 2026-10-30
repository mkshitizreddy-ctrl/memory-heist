"""ESC on the win screen must not throw away a score that is still being named."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.game import Game


class SpyLeaderboard:
    """Records saves so the tests never touch saves/leaderboard.json."""

    def __init__(self):
        self.added = []

    def top(self, count):
        return []

    def add(self, name, score, difficulty, coop):
        self.added.append((name, score))
        return None


class RecordingFont:
    def __init__(self, font):
        self._font = font
        self.texts = []

    def render(self, text, *args, **kwargs):
        self.texts.append(text)
        return self._font.render(text, *args, **kwargs)


@pytest.fixture
def game():
    g = Game()
    g._start_new_run()
    g.win_screen.leaderboard = SpyLeaderboard()
    return g


def press(game, key, char=""):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=char))
    game.handle_events()


def test_esc_while_typing_a_name_keeps_the_game_open_and_skips_saving(game):
    game.change_state("win")  # the screen is waiting for a name

    press(game, pygame.K_ESCAPE, "\x1b")

    assert game.running is True
    assert game.state == "win"
    assert game.win_screen.entering is False
    assert game.win_screen.leaderboard.added == []


def test_esc_after_the_name_is_saved_still_quits(game):
    game.change_state("win")
    game.win_screen.entering = False

    press(game, pygame.K_ESCAPE, "\x1b")

    assert game.running is False


def test_name_entry_prompt_mentions_how_to_skip(game):
    game.change_state("win")
    game.win_screen.prompt_font = RecordingFont(game.win_screen.prompt_font)

    game.win_screen.render(pygame.Surface((960, 640)))

    text = " ".join(game.win_screen.prompt_font.texts)
    assert "ENTER" in text and "save" in text
    assert "ESC" in text and "skip" in text
