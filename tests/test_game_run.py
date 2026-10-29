"""Game.run() must return when the loop ends, not exit the interpreter."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.game import Game


@pytest.fixture
def game():
    g = Game()
    g.running = True
    return g


def stop_after_one_frame(game, monkeypatch):
    frames = []

    def handle_events():
        frames.append(1)
        game.running = False

    monkeypatch.setattr(game, "handle_events", handle_events)
    return frames


def test_run_returns_when_running_is_cleared(game, monkeypatch):
    frames = stop_after_one_frame(game, monkeypatch)

    # A SystemExit raised by run() would propagate and fail this test.
    assert game.run() is None
    assert len(frames) == 1


def test_run_leaves_pygame_initialised(game, monkeypatch):
    stop_after_one_frame(game, monkeypatch)

    game.run()

    assert pygame.get_init()
