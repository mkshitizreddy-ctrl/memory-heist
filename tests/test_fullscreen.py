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


# --- start full-screen, and remember the choice -----------------------------------
from core import display
from systems.settings import Settings


def test_window_flags_are_scaled_and_add_fullscreen_only_when_wanted(monkeypatch):
    monkeypatch.delenv(display.WINDOWED_ENV, raising=False)
    assert display.window_flags(True, "windows") == pygame.SCALED | pygame.FULLSCREEN
    assert display.window_flags(False, "windows") == pygame.SCALED
    assert not display.window_flags(True, "dummy") & pygame.FULLSCREEN       # tests never go full-screen
    assert not display.window_flags(True, "offscreen") & pygame.FULLSCREEN


def test_the_windowed_switch_beats_the_fullscreen_setting(monkeypatch):
    monkeypatch.setenv(display.WINDOWED_ENV, "1")
    assert not display.window_flags(True, "windows") & pygame.FULLSCREEN


def test_scaling_is_smoothed_unless_the_user_already_chose(monkeypatch):
    monkeypatch.delenv("SDL_RENDER_SCALE_QUALITY", raising=False)
    display.configure_scaling()
    assert os.environ["SDL_RENDER_SCALE_QUALITY"] == "1"
    monkeypatch.setenv("SDL_RENDER_SCALE_QUALITY", "0")
    display.configure_scaling()
    assert os.environ["SDL_RENDER_SCALE_QUALITY"] == "0"


def test_the_game_asks_for_a_fullscreen_window_by_default(monkeypatch):
    monkeypatch.delenv(display.WINDOWED_ENV, raising=False)
    seen = []
    monkeypatch.setattr(pygame.display, "get_driver", lambda: "windows")
    monkeypatch.setattr(pygame.display, "set_mode", lambda size, flags=0: seen.append((size, flags)) or pygame.Surface(size))
    Game._create_window()
    assert seen[0] == ((960, 640), pygame.SCALED | pygame.FULLSCREEN)


def test_a_saved_windowed_choice_is_respected(monkeypatch, tmp_path):
    monkeypatch.delenv(display.WINDOWED_ENV, raising=False)
    Settings(fullscreen=False).save()
    seen = []
    monkeypatch.setattr(pygame.display, "get_driver", lambda: "windows")
    monkeypatch.setattr(pygame.display, "set_mode", lambda size, flags=0: seen.append(flags) or pygame.Surface(size))
    Game._create_window()
    assert seen[0] == pygame.SCALED


def test_the_window_falls_back_when_fullscreen_is_not_available(monkeypatch):
    monkeypatch.delenv(display.WINDOWED_ENV, raising=False)
    attempts = []

    def picky(size, flags=0):
        attempts.append(flags)
        if flags & pygame.FULLSCREEN:
            raise pygame.error("no fullscreen here")
        return pygame.Surface(size)

    monkeypatch.setattr(pygame.display, "get_driver", lambda: "windows")
    monkeypatch.setattr(pygame.display, "set_mode", picky)
    Game._create_window(True)
    assert attempts == [pygame.SCALED | pygame.FULLSCREEN, pygame.SCALED]


def test_f11_remembers_what_the_window_became(game, monkeypatch):
    monkeypatch.setattr(display, "is_fullscreen", lambda: False)
    press(game, pygame.K_F11)
    assert game.settings.fullscreen is False
    assert Settings.load().fullscreen is False
    monkeypatch.setattr(display, "is_fullscreen", lambda: True)
    press(game, pygame.K_F11)
    assert Settings.load().fullscreen is True


def test_a_failed_toggle_does_not_change_the_saved_choice(monkeypatch):
    def fail():
        raise pygame.error("nope")

    monkeypatch.setattr(pygame.display, "toggle_fullscreen", fail)
    g = Game()
    g.settings.fullscreen = True
    g._toggle_fullscreen()
    assert g.settings.fullscreen is True


def test_settings_default_to_fullscreen_and_ignore_nonsense():
    assert Settings().fullscreen is True
    assert Settings(fullscreen="yes").fullscreen is True
    assert Settings(fullscreen=False).to_dict()["fullscreen"] is False
