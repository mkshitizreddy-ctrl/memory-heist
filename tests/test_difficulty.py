
from core.difficulty import (
    DEFAULT_DIFFICULTY,
    DIFFICULTIES,
    get_difficulty,
)


def test_default_difficulty_is_medium():
    assert DEFAULT_DIFFICULTY == "medium"


def test_easy_difficulty_settings():
    difficulty = get_difficulty("easy")

    assert difficulty["label"] == "EASY"
    assert difficulty["timer_multiplier"] == 1.5
    assert difficulty["security_penalty_multiplier"] == 0.5
    assert difficulty["hints_enabled"] is True


def test_medium_difficulty_settings():
    difficulty = get_difficulty("medium")

    assert difficulty["label"] == "MEDIUM"
    assert difficulty["timer_multiplier"] == 1.0
    assert difficulty["security_penalty_multiplier"] == 1.0
    assert difficulty["hints_enabled"] is True


def test_hard_difficulty_settings():
    difficulty = get_difficulty("hard")

    assert difficulty["label"] == "HARD"
    assert difficulty["timer_multiplier"] == 0.7
    assert difficulty["security_penalty_multiplier"] == 1.5
    assert difficulty["hints_enabled"] is False


def test_invalid_difficulty_falls_back_to_medium():
    assert get_difficulty("invalid") == DIFFICULTIES["medium"]


def test_each_difficulty_has_required_settings():
    required_keys = {
        "label",
        "timer_multiplier",
        "security_penalty_multiplier",
        "hints_enabled",
    }

    for difficulty in DIFFICULTIES.values():
        assert required_keys.issubset(difficulty.keys())
