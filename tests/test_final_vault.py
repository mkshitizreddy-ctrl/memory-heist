"""Tests for levels/final_vault.py."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from levels.final_vault import FinalVault

ANSWER_KEYS = {1: pygame.K_1, 2: pygame.K_2, 3: pygame.K_3}
CORRECT_SEQUENCE = [1, 2, 3, 1, 3, 2]


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


def answer(vault, number):
    vault.handle_event(key(ANSWER_KEYS[number]))


def type_digits(vault, digits):
    for ch in digits:
        vault.handle_event(key(pygame.K_0, ch))


def submit(vault):
    vault.handle_event(key(pygame.K_RETURN))


@pytest.fixture
def game():
    return FakeGame()


@pytest.fixture
def vault(game):
    return FinalVault(game=game)


def test_starts_at_stage_one(vault):
    assert vault.stage == 1
    assert not vault.is_complete()


def test_every_stage_has_content(vault):
    for stage in range(1, vault.total_stages + 1):
        vault.stage = stage
        assert vault._get_objective()
        assert vault._get_code_lines()
        assert len(vault._get_options()) == 3


def test_full_playthrough_unlocks(vault, game):
    for number in CORRECT_SEQUENCE:
        answer(vault, number)
    assert vault.is_complete()
    assert "MASTER VAULT UNLOCKED" in vault.feedback
    # 6 x 50 per stage + 150 final bonus
    assert game.score.total == 6 * 50 + 150


def test_wrong_answer_stays_and_penalizes(vault, game):
    answer(vault, 2)
    assert vault.stage == 1
    assert "INCORRECT" in vault.feedback
    assert game.security.total == 20
    assert game.score.total == -10


def test_correct_answer_advances_and_clears_terminal(vault):
    type_digits(vault, "12")
    answer(vault, 1)
    assert vault.stage == 2
    assert vault.command == ""
    assert vault.command_result == ""


def type_text(vault, text):
    for ch in text:
        vault.handle_event(key(getattr(pygame, f"K_{ch}"), ch))


@pytest.mark.parametrize("stage", [1, 2, 3, 4, 5])
def test_terminal_inactive_on_answer_only_stages(vault, stage):
    vault.stage = stage
    type_digits(vault, "5")
    assert vault.command == ""
    submit(vault)
    assert "answer panel" in vault.feedback


def test_text_not_accepted_before_terminal_stage(vault):
    vault.stage = 4
    type_text(vault, "ab")
    assert vault.command == ""


def test_stage6_valid_integer_is_accepted(vault, game):
    vault.stage = 6
    type_digits(vault, "5")
    submit(vault)
    assert "clearance level verified" in vault.command_result
    assert not vault.is_complete()
    assert game.security.total == 0


def test_stage6_wrong_integer_raises_security(vault, game):
    vault.stage = 6
    type_digits(vault, "9")
    submit(vault)
    assert vault.command_result == "Integer received: 9"
    assert game.security.total == 5


def test_stage6_invalid_text_triggers_exception_path(vault, game):
    vault.stage = 6
    type_text(vault, "ab")
    submit(vault)
    assert "ValueError caught" in vault.command_result
    assert "EXCEPTION HANDLED" in vault.feedback
    assert game.security.total == 5
    assert vault.command == ""


def test_stage6_empty_input_is_rejected_without_penalty(vault, game):
    vault.stage = 6
    submit(vault)
    assert "Enter a value" in vault.feedback
    assert game.security.total == 0


def test_terminal_input_limits(vault):
    vault.stage = 6
    type_digits(vault, "123456")
    assert len(vault.command) == 4
    vault.handle_event(key(pygame.K_BACKSPACE))
    assert len(vault.command) == 3


def test_events_ignored_after_complete(vault, game):
    for number in CORRECT_SEQUENCE:
        answer(vault, number)
    before = game.score.total
    answer(vault, 1)
    assert game.score.total == before


def test_non_keydown_ignored(vault):
    vault.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_1))
    assert vault.selected_option is None


def test_works_without_game():
    vault = FinalVault()
    for number in CORRECT_SEQUENCE:
        answer(vault, number)
    assert vault.is_complete()


def test_render_every_stage_does_not_crash(vault):
    pygame.init()
    surface = pygame.Surface((960, 640))
    for stage in range(1, vault.total_stages + 1):
        vault.stage = stage
        vault.render(surface)