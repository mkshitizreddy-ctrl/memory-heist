import pygame
import pytest

from levels.level1 import Level1
@pytest.fixture(autouse=True)
def initialize_pygame_font():
    pygame.font.init()
    yield
    pygame.font.quit()

class FakeHints:
    def __init__(self, enabled=True):
        self.enabled = enabled


class FakeScore:
    def __init__(self):
        self.penalty = 0

    def penalize(self, points):
        self.penalty += points

    def add(self, points):
        pass


class FakeSecurity:
    def __init__(self):
        self.increase_amount = 0

    def increase(self, amount):
        self.increase_amount += amount


class FakeGame:
    def __init__(self, hints_enabled=True):
        self.hints = FakeHints(enabled=hints_enabled)
        self.score = FakeScore()
        self.security = FakeSecurity()


@pytest.fixture
def question():
    return {
        "prompt": "What is the data type of agent_id?",
        "options": ["int", "str", "bool"],
        "answer": "str",
        "hint": "It is text inside quotes.",
    }


def test_wrong_answer_shows_hint_when_hints_enabled(question):
    game = FakeGame(hints_enabled=True)
    level = Level1(game=game)

    level._check_answer(question, "int")

    assert level.message == "Wrong. Hint: It is text inside quotes."
    assert game.security.increase_amount == 20
    assert game.score.penalty == 10


def test_wrong_answer_hides_hint_when_hints_disabled(question):
    game = FakeGame(hints_enabled=False)
    level = Level1(game=game)

    level._check_answer(question, "int")

    assert level.message == "Wrong. Hints are off on this difficulty."
    assert question["hint"] not in level.message
    assert game.security.increase_amount == 20
    assert game.score.penalty == 10


def test_wrong_answer_without_game_shows_question_hint(question):
    level = Level1(game=None)

    level._check_answer(question, "int")

    assert level.message == "Wrong. Hint: It is text inside quotes."