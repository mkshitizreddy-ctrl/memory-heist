"""F11 toggles fullscreen from any screen without side effects."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.game import Game


@pytest.fixture
def toggles(monkeypatch):
    """Replace the real toggle with a counter so no window really changes."""
    calls = []
    monkeypatch.setattr(pygame.display, "toggle_fullscreen", lambda: calls.append(1) or 1)
    return calls


@pytest.fixture
def game(toggles):
    g = Game()
    g._start_new_run()
    return g


def press(game, key, char=""):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=char))
    game.handle_events()


@pytest.mark.parametrize("state", ["menu", "playing", "win", "lose"])
def test_f11_toggles_fullscreen_in_every_state(game, toggles, state):
    game.change_state(state)

    press(game, pygame.K_F11)

    assert toggles == [1]


def test_f11_does_not_pause_or_reach_the_level(game, monkeypatch):
    seen = []
    monkeypatch.setattr(game.level_manager, "handle_event", seen.append)
    game.change_state("playing")

    press(game, pygame.K_F11)

    assert game.paused is False
    assert seen == []


def test_f11_is_not_typed_into_the_leaderboard_name(game):
    game.change_state("win")

    press(game, pygame.K_F11, "")

    assert game.win_screen.name == "" and game.win_screen.entering is True


def test_a_failing_toggle_does_not_crash_the_game(game, monkeypatch):
    def fail():
        raise pygame.error("not supported here")

    monkeypatch.setattr(pygame.display, "toggle_fullscreen", fail)

    press(game, pygame.K_F11)

    assert game.running is True


def test_window_asks_for_a_scaled_display(monkeypatch):
    real = pygame.display.set_mode
    flags_seen = []

    def spy(size, flags=0, *args, **kwargs):
        flags_seen.append(flags)
        return real(size, flags, *args, **kwargs)

    monkeypatch.setattr(pygame.display, "set_mode", spy)

    Game()

    assert flags_seen[0] & pygame.SCALED


def test_window_falls_back_when_scaling_is_unavailable(monkeypatch):
    real = pygame.display.set_mode

    def no_scaling(size, flags=0, *args, **kwargs):
        if flags & pygame.SCALED:
            raise pygame.error("failed to create renderer")
        return real(size, flags, *args, **kwargs)

    monkeypatch.setattr(pygame.display, "set_mode", no_scaling)

    game = Game()

    assert game.screen.get_size() == (960, 640)
