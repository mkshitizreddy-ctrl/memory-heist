"""Tests for the top-level loop in core/game.py: event routing, pause,
and state changes. Headless (SDL dummy drivers), no window needed."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.game import Game


def key_event(key, unicode=""):
    return pygame.event.Event(pygame.KEYDOWN, key=key, unicode=unicode)


def feed(monkeypatch, *events):
    """Make the next pygame.event.get() return exactly these events."""
    monkeypatch.setattr(pygame.event, "get", lambda: list(events))


@pytest.fixture
def game():
    return Game()


@pytest.fixture
def received(game, monkeypatch):
    """Every event that reaches the active level is appended here."""
    events = []
    monkeypatch.setattr(game.level_manager, "handle_event", events.append)
    return events


# --- sanity: the recorder really sees events -------------------------------

def test_keys_reach_the_level_while_playing(game, received, monkeypatch):
    game.change_state("playing")
    feed(monkeypatch, key_event(pygame.K_a, "a"))
    game.handle_events()
    assert len(received) == 1


def test_escape_pauses_and_is_not_forwarded(game, received, monkeypatch):
    game.change_state("playing")
    feed(monkeypatch, key_event(pygame.K_ESCAPE))
    game.handle_events()
    assert game.paused
    assert received == []


def test_paused_game_does_not_advance_the_timer(game):
    game.change_state("playing")
    game.timer.start(10)
    game.paused = True
    game.update(1.0)
    assert game.timer.get_remaining() == 10


# --- keys that trigger a transition must not leak into the new screen ------

def test_enter_on_menu_does_not_leak_into_level1(game, received, monkeypatch):
    game.story_enabled = False  # with the story on, ENTER opens the intro
    feed(monkeypatch, key_event(pygame.K_RETURN))
    game.handle_events()
    assert game.state == "playing"
    assert received == []


def test_retry_key_on_lose_screen_does_not_leak_into_level1(
    game, received, monkeypatch
):
    game.change_state("lose")
    feed(monkeypatch, key_event(pygame.K_r, "r"))
    game.handle_events()
    assert game.state == "playing"
    assert received == []


def test_escape_that_unpauses_is_not_forwarded(game, received, monkeypatch):
    game.change_state("playing")
    game.paused = True
    feed(monkeypatch, key_event(pygame.K_ESCAPE))
    game.handle_events()
    assert not game.paused
    assert received == []


# --- a finished game must stay finished ------------------------------------

def test_win_is_not_overwritten_by_lose_on_the_same_frame(game):
    game.change_state("playing")
    game.level_manager.start("final_vault")
    game.level_manager.current.complete = True
    game.timer.start(0.01)

    game.update(1.0)

    assert game.state == "win"


# --- real losses must still be losses ---------------------------------------

def test_security_lockdown_still_loses(game):
    game.change_state("playing")
    game.security.increase(1000)

    game.update(0.016)

    assert game.state == "lose"


def test_expired_timer_still_loses(game):
    game.change_state("playing")
    game.timer.start(0.01)

    game.update(1.0)

    assert game.state == "lose"
