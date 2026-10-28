import pygame

from levels.level4_memory import Level4MemoryVault


class FakeScore:
    def __init__(self):
        self.added = 0
        self.penalized = 0

    def add(self, points):
        self.added += points

    def penalize(self, points):
        self.penalized += points


class FakeSecurity:
    def __init__(self):
        self.increased = 0

    def increase(self, amount):
        self.increased += amount


class FakeGame:
    def __init__(self):
        self.score = FakeScore()
        self.security = FakeSecurity()


def test_correct_answer_resets_hacking_state_and_awards_points_once():
    game = FakeGame()

    # IMPORTANT:
    # game=game passes FakeGame as the game parameter,
    # not as the player parameter.
    level = Level4MemoryVault(game=game)

    level.active_gate = 0
    level.hacking_active = True

    correct_answer = level.gates[0]["answer"]

    # First correct answer
    level.answer_gate(correct_answer)

    # Gate should unlock
    assert level.gates[0]["unlocked"] is True

    # Hacking prompt should close
    assert level.hacking_active is False

    # No gate should remain active
    assert level.active_gate is None

    # Correct answer gives exactly 40 points
    assert game.score.added == 40

    # Try answering again
    # active_gate is None, so nothing should happen
    level.answer_gate(correct_answer)

    # Score must NOT increase again
    assert game.score.added == 40


def test_incorrect_answer_resets_hacking_state():
    game = FakeGame()

    # Pass FakeGame as the game parameter
    level = Level4MemoryVault(game=game)

    level.active_gate = 0
    level.hacking_active = True

    correct_answer = level.gates[0]["answer"]

    # Pick an answer that is definitely different
    wrong_answer = (correct_answer + 1) % 4

    level.answer_gate(wrong_answer)

    # Gate should remain locked
    assert level.gates[0]["unlocked"] is False

    # Hacking prompt should close
    assert level.hacking_active is False

    # No gate should remain active
    assert level.active_gate is None

    # Incorrect answer gives exactly 10 penalty
    assert game.score.penalized == 10

    # Security should increase by 15
    assert game.security.increased == 15