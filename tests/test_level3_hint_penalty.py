"""
tests/test_level3_hint_penalty.py

Level 3 hint penalty:
    Easy / Medium -> 10 points
    Hard          -> 15 points
The hint still displays as before, and a correct answer never earns
less than the existing 10-point minimum.
"""

import os
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.difficulty import get_difficulty
from levels.level3_loops import Level3LaserLoop
from systems.scoring import ScoreTracker

# difficulty -> (question points in puzzles.json, expected hint penalty)
EXPECTED = {
    "easy": (40, 10),
    "medium": (50, 10),
    "hard": (60, 15),
}

NUMBER_KEYS = {
    1: pygame.K_1,
    2: pygame.K_2,
    3: pygame.K_3,
    4: pygame.K_4,
}


def key_event(key):
    return pygame.event.Event(pygame.KEYDOWN, key=key)


def make_level(difficulty_key):
    pygame.font.init()

    game = SimpleNamespace(
        difficulty=get_difficulty(difficulty_key),
        score=ScoreTracker(),
        security=SimpleNamespace(increase=lambda amount: None),
    )

    level = Level3LaserLoop(game=game)
    level.room_map.current_name = "level3_room1"
    level.current_question_number = 0
    level.load_current_question()

    return level


def answer_correctly(level):
    level.handle_event(
        key_event(NUMBER_KEYS[level.correct_option_index + 1])
    )


def answer_wrongly(level):
    wrong_index = next(
        index
        for index in range(len(level.options))
        if index != level.correct_option_index
    )
    level.handle_event(key_event(NUMBER_KEYS[wrong_index + 1]))


@pytest.mark.parametrize("key", list(EXPECTED))
def test_correct_answer_without_hint_earns_full_points(key):
    points, _ = EXPECTED[key]
    level = make_level(key)

    assert level.question_points == points

    answer_correctly(level)

    assert level.game.score.get_score() == points


@pytest.mark.parametrize("key", list(EXPECTED))
def test_hint_penalty_matches_difficulty(key):
    points, penalty = EXPECTED[key]
    level = make_level(key)

    assert level.hint_penalty() == penalty

    level.handle_event(key_event(pygame.K_h))
    answer_correctly(level)

    assert level.game.score.get_score() == points - penalty


@pytest.mark.parametrize("key", list(EXPECTED))
def test_hint_still_displays_and_message_shows_penalty(key):
    _, penalty = EXPECTED[key]
    level = make_level(key)

    level.handle_event(key_event(pygame.K_h))

    assert level.show_hint is True
    assert level.hint_used is True
    assert level.current_hint
    assert f"reduced by {penalty}." in level.feedback


@pytest.mark.parametrize("key", list(EXPECTED))
def test_pressing_hint_twice_does_not_stack_the_penalty(key):
    points, penalty = EXPECTED[key]
    level = make_level(key)

    level.handle_event(key_event(pygame.K_h))
    level.handle_event(key_event(pygame.K_h))
    answer_correctly(level)

    assert level.game.score.get_score() == points - penalty


@pytest.mark.parametrize(
    "key, question_points",
    [
        ("easy", 12),
        ("medium", 10),
        ("hard", 20),
        ("hard", 10),
    ],
)
def test_minimum_score_for_correct_answer_is_unchanged(
    key, question_points
):
    level = make_level(key)
    level.question_points = question_points

    level.handle_event(key_event(pygame.K_h))
    answer_correctly(level)

    assert level.game.score.get_score() == 10


@pytest.mark.parametrize("key", list(EXPECTED))
def test_wrong_answer_penalty_is_unchanged(key):
    level = make_level(key)
    level.game.score.add(100)

    answer_wrongly(level)

    assert level.game.score.get_score() == 90


@pytest.mark.parametrize("key", list(EXPECTED))
def test_penalty_through_real_game_selection(key):
    """Menu -> ENTER -> Level 3, using the real Game object."""
    from core.game import Game

    game = Game()
    game.menu.selected_difficulty = key
    pygame.event.post(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN)
    )
    game.handle_events()

    level = game.level_manager.levels["level3"]
    points, penalty = EXPECTED[key]

    game.score.reset()
    level.room_map.current_name = "level3_room1"
    level.current_question_number = 0
    level.load_current_question()

    level.handle_event(key_event(pygame.K_h))
    answer_correctly(level)

    assert level.question_points == points
    assert game.score.get_score() == points - penalty