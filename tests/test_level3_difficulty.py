"""
tests/test_level3_difficulty.py

Regression tests: Level 3 must show and use the difficulty the player
selected in the menu in every room, regardless of the difficulty field
of whichever question was drawn for that room.
"""

import os
import random
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.difficulty import DIFFICULTIES, get_difficulty
from levels.level3_loops import Level3LaserLoop


@pytest.fixture(autouse=True)
def _pygame_fonts():
    pygame.font.init()


def make_level(difficulty_key):
    """Build Level 3 with the same game.difficulty object Game provides."""
    game = SimpleNamespace(difficulty=get_difficulty(difficulty_key))
    return Level3LaserLoop(game=game)


def enter_room(level, room_number):
    """Move to a room the way the room-transition code does."""
    level.room_map.current_name = f"level3_room{room_number}"
    level.current_question_number = room_number - 1
    level.load_current_question()


@pytest.mark.parametrize("key", list(DIFFICULTIES))
def test_resolves_selected_difficulty_from_game_preset(key):
    level = make_level(key)

    assert level.get_selected_difficulty() == key
    assert level.current_difficulty == key


@pytest.mark.parametrize("key", list(DIFFICULTIES))
def test_difficulty_stays_selected_in_every_room(key):
    # Many seeds so every possible question draw (including fallback
    # draws whose own difficulty differs from the selection) is covered.
    for seed in range(40):
        random.seed(seed)
        level = make_level(key)

        for room_number in (1, 2, 3):
            enter_room(level, room_number)
            assert level.current_difficulty == key


def test_question_difficulty_does_not_overwrite_global_difficulty():
    level = make_level("hard")

    # Force a question whose own difficulty differs from the selection.
    level.selected_questions[0] = dict(
        level.selected_questions[0], difficulty="easy"
    )
    enter_room(level, 1)

    assert level.current_question["difficulty"] == "easy"
    assert level.current_difficulty == "hard"


@pytest.mark.parametrize(
    "difficulty, expected",
    [
        ("hard", "hard"),
        ("EASY", "easy"),
        ({"name": "hard"}, "hard"),
        ({"level": "easy"}, "easy"),
        ({"label": "unknown preset"}, "medium"),
        (None, "medium"),
        ("nonsense", "medium"),
        (123, "medium"),
    ],
)
def test_get_selected_difficulty_accepts_supported_shapes(
    difficulty, expected
):
    level = make_level("medium")
    level.game = SimpleNamespace(difficulty=difficulty)

    assert level.get_selected_difficulty() == expected