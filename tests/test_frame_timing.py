"""Tests for the frame-time cap in core/game.py."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

from core.game import Game


class FakeClock:
    """Stands in for pygame's Clock: tick() returns a fixed frame time in ms."""

    def __init__(self, milliseconds):
        self.milliseconds = milliseconds

    def tick(self, fps):
        return self.milliseconds


@pytest.fixture
def game():
    return Game()


def test_normal_frame_time_is_unchanged(game):
    game.clock = FakeClock(16)
    assert game._frame_dt() == pytest.approx(0.016)


def test_stalled_frame_is_capped(game):
    game.clock = FakeClock(3000)  # e.g. the window was dragged for 3 s
    assert game._frame_dt() == pytest.approx(0.05)


def test_capped_step_cannot_skip_a_wall(game):
    # A player moves at most speed * dt pixels per frame. With the cap that is
    # 200 * 0.05 = 10 px, well below the 32 px player width.
    game.clock = FakeClock(10_000)
    assert game.player.speed * game._frame_dt() < game.player.rect.width
