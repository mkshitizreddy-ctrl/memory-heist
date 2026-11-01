"""The win and lose screens must advertise the keys that actually work."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from ui.screens import LoseScreen, WinScreen


class RecordingFont:
    """Wraps a font and remembers every string it was asked to render."""

    def __init__(self, font):
        self._font = font
        self.texts = []

    def render(self, text, *args, **kwargs):
        self.texts.append(text)
        return self._font.render(text, *args, **kwargs)


class NoScores:
    """A leaderboard stand-in so the tests never touch saves/."""

    def top(self, count):
        return []

    def add(self, name, score, difficulty, coop):
        return None


@pytest.fixture
def surface():
    pygame.init()
    return pygame.Surface((960, 640))


def recorded_prompts(screen, surface):
    screen.prompt_font = RecordingFont(screen.prompt_font)
    screen.render(surface)
    return screen.prompt_font.texts


def test_lose_screen_offers_retry_menu_and_quit(surface):
    texts = recorded_prompts(LoseScreen(), surface)

    hint = " ".join(texts)
    assert "R" in hint and "retry" in hint
    assert "M" in hint and "menu" in hint
    assert "ESC" in hint and "quit" in hint


def test_saved_win_screen_offers_play_again_menu_and_quit(surface):
    screen = WinScreen(leaderboard=NoScores())
    screen.entering = False

    hint = " ".join(recorded_prompts(screen, surface))

    assert "R" in hint and "play again" in hint
    assert "M" in hint and "menu" in hint
    assert "ESC" in hint and "quit" in hint


def test_win_screen_does_not_advertise_r_and_m_while_a_name_is_typed(surface):
    screen = WinScreen(leaderboard=NoScores())  # starts in name entry

    hint = " ".join(recorded_prompts(screen, surface))

    assert "menu" not in hint
    assert "play again" not in hint
