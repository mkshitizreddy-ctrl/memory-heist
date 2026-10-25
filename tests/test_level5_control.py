"""Tests for levels/level5_control.py."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from levels.level5_control import Level5ControlCenter


class FakeScore:
    def __init__(self):
        self.total = 0

    def add(self, amount):
        self.total += amount

    def penalize(self, amount):
        self.total -= amount


class FakeSecurity:
    def __init__(self):
        self.total = 0

    def increase(self, amount=20):
        self.total += amount


class FakeGame:
    def __init__(self):
        self.score = FakeScore()
        self.security = FakeSecurity()


def key(k, unicode=""):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode=unicode)


def type_command(level, text):
    for ch in text:
        level.handle_event(key(getattr(pygame, f"K_{ch}"), ch))
    level.handle_event(key(pygame.K_RETURN))


def solve_concepts(level):
    for k in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
        level.handle_event(key(k))


@pytest.fixture
def game():
    return FakeGame()


@pytest.fixture
def level(game):
    return Level5ControlCenter(game=game)


def test_starts_incomplete(level):
    assert not level.is_complete()
    assert level.current_step == 1
    assert not level.concepts_done


def test_correct_answers_advance_steps_and_score(level, game):
    level.handle_event(key(pygame.K_1))
    assert level.current_step == 2
    assert game.score.total == 40


def test_wrong_answer_penalizes(level, game):
    level.handle_event(key(pygame.K_4))
    assert level.current_step == 1
    assert game.security.total == 20
    assert game.score.total == -10
    assert "INCORRECT" in level.feedback


def test_all_concepts_sets_flag(level):
    solve_concepts(level)
    assert level.concepts_done
    assert not level.is_complete()


def test_full_playthrough_completes(level, game):
    solve_concepts(level)
    type_command(level, "5")
    assert level.is_complete()
    assert level.command_result == "RETURN VALUE: MASTER ACCESS"
    # 4 x 40 correct answers + 50 + 100 completion bonuses
    assert game.score.total == 4 * 40 + 150


def test_low_level_is_access_denied_not_type_error(level, game):
    solve_concepts(level)
    type_command(level, "3")
    assert not level.is_complete()
    assert "Access denied" in level.feedback
    assert "Enter an integer" not in level.command_result
    assert game.security.total == 15


def test_empty_input_hits_integer_error(level, game):
    level.handle_event(key(pygame.K_RETURN))
    assert level.command_result == "ERROR: Enter an integer."
    assert game.security.total == 10


def test_cannot_skip_concept_steps(level):
    type_command(level, "5")
    assert not level.is_complete()
    assert "Finish the concept steps first" in level.feedback


def test_cannot_finish_while_on_last_unanswered_step(level):
    for k in (pygame.K_1, pygame.K_2, pygame.K_3):
        level.handle_event(key(k))
    assert level.current_step == 4
    type_command(level, "5")
    assert not level.is_complete()


def test_command_cleared_after_submit(level):
    type_command(level, "3")
    assert level.command == ""


def test_input_length_and_backspace(level):
    for ch in "5555":
        level.handle_event(key(pygame.K_5, ch))
    assert len(level.command) == 3
    level.handle_event(key(pygame.K_BACKSPACE))
    assert len(level.command) == 2


def test_digits_1_to_4_are_answers_before_concepts_done(level):
    level.handle_event(key(pygame.K_3, "3"))
    assert level.command == ""
    assert level.selected_option == 3


def test_digits_1_to_4_type_into_terminal_after_concepts_done(level):
    solve_concepts(level)
    level.handle_event(key(pygame.K_3, "3"))
    assert level.command == "3"


def test_events_ignored_after_complete(level):
    solve_concepts(level)
    type_command(level, "5")
    score_before = level.game.score.total
    level.handle_event(key(pygame.K_4))
    assert level.game.score.total == score_before


def test_works_without_game():
    lvl = Level5ControlCenter()
    solve_concepts(lvl)
    type_command(lvl, "5")
    assert lvl.is_complete()


def test_render_does_not_crash(level):
    pygame.init()
    surface = pygame.Surface((960, 640))
    level.render(surface)
    solve_concepts(level)
    type_command(level, "5")
    level.render(surface)