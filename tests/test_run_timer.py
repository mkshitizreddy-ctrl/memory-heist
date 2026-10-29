"""The run has one global countdown, scaled by difficulty; running out loses."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

from core.difficulty import get_difficulty
from core.game import Game

DT = 0.05


@pytest.fixture
def game():
    return Game()


def start_run(game, difficulty="medium"):
    game.difficulty = get_difficulty(difficulty)
    game._start_new_run()


@pytest.mark.parametrize(
    "name, seconds",
    [("easy", 1350), ("medium", 900), ("hard", 630)],
)
def test_run_timer_starts_at_the_difficulty_length(game, name, seconds):
    start_run(game, name)

    assert game.timer.active
    assert game.timer.get_remaining() == seconds


def test_timer_counts_down_while_playing(game):
    start_run(game)

    game.update(DT)

    assert game.timer.get_remaining() == pytest.approx(900 - DT)


def test_timer_is_frozen_while_paused(game):
    start_run(game)
    game.paused = True

    game.update(DT)

    assert game.timer.active
    assert game.timer.get_remaining() == 900


def test_running_out_of_time_loses_the_run(game):
    start_run(game)
    game.timer.remaining = 0.01

    game.update(DT)

    assert game.state == "lose"


def test_restart_after_losing_gets_the_full_time_again(game):
    start_run(game)
    game.timer.remaining = 1

    game._start_new_run()

    assert game.timer.active
    assert game.timer.get_remaining() == 900
