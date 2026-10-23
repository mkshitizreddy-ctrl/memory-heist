
from systems.scoring import ScoreTracker


def test_initial_score_is_zero():
    tracker = ScoreTracker()

    assert tracker.get_score() == 0


def test_add_points():
    tracker = ScoreTracker()

    tracker.add(100)

    assert tracker.get_score() == 100


def test_penalize_points():
    tracker = ScoreTracker()
    tracker.add(100)

    tracker.penalize(30)

    assert tracker.get_score() == 70


def test_penalty_cannot_make_score_negative():
    tracker = ScoreTracker()
    tracker.add(10)

    tracker.penalize(25)

    assert tracker.get_score() == 0


def test_reset_clears_score():
    tracker = ScoreTracker()
    tracker.add(100)

    tracker.reset()

    assert tracker.get_score() == 0
