"""Tests for player movement in core/player.py."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from collections import defaultdict

import pygame
import pytest

from core.player import Player


@pytest.fixture(autouse=True)
def display():
    pygame.init()
    pygame.display.set_mode((64, 64))


def held(*keys):
    """Stand-in for pygame.key.get_pressed() with only these keys down."""
    pressed = defaultdict(bool)
    for key in keys:
        pressed[key] = True
    return pressed


def run_for_one_second(player, keys, fps, blocked=None):
    for _ in range(fps):
        player.handle_input(keys, 1.0 / fps, blocked=blocked)


@pytest.mark.parametrize("fps", [30, 60, 144])
def test_speed_does_not_depend_on_frame_rate(fps):
    player = Player(0, 0)

    run_for_one_second(player, held(pygame.K_d), fps)

    assert abs(player.rect.x - 200) <= 1


def test_moving_left_covers_the_same_distance_as_moving_right():
    player = Player(500, 0)

    run_for_one_second(player, held(pygame.K_a), 60)

    assert abs((500 - player.rect.x) - 200) <= 1


def test_diagonal_speed_is_normalised():
    player = Player(0, 0)

    run_for_one_second(player, held(pygame.K_d, pygame.K_s), 60)

    assert abs(player.rect.x - 141.4) <= 1.5
    assert abs(player.rect.y - 141.4) <= 1.5


def test_standing_still_does_not_move():
    player = Player(40, 40)

    run_for_one_second(player, held(), 60)

    assert player.rect.topleft == (40, 40)


def test_blocked_move_is_reverted_and_does_not_creep():
    player = Player(0, 0)

    def wall_at_50(rect):
        return rect.x >= 50

    run_for_one_second(player, held(pygame.K_d), 60, blocked=wall_at_50)
    stopped_at = player.rect.x
    run_for_one_second(player, held(pygame.K_d), 60, blocked=wall_at_50)

    assert stopped_at < 50
    assert player.rect.x == stopped_at
