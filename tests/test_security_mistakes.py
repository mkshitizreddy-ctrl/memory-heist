"""A mistake is counted only when security actually goes up."""

from core.game import DifficultySecurityMeter


def meter(multiplier):
    m = DifficultySecurityMeter()
    m.penalty_multiplier = multiplier
    return m


def test_a_real_penalty_counts_one_mistake_and_scales():
    m = meter(1.5)
    m.increase(20)
    assert m.mistakes == 1 and m.level == 30


def test_a_zero_penalty_is_not_a_mistake():
    m = meter(0.0)
    m.increase(20)
    assert m.mistakes == 0 and m.level == 0
    m = meter(1.0)
    m.increase(0)
    assert m.mistakes == 0 and m.level == 0


def test_a_penalty_that_rounds_to_zero_is_not_a_mistake():
    m = meter(0.5)
    m.increase(1)                     # round(0.5) == 0
    assert m.mistakes == 0 and m.level == 0


def test_reset_clears_mistakes():
    m = meter(1.0)
    m.increase(20)
    m.reset()
    assert m.mistakes == 0 and m.level == 0
