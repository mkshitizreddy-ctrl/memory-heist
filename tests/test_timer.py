
from systems.timer import Timer


def test_timer_initial_state():
    timer = Timer()

    assert timer.get_remaining() == 0
    assert timer.expired() is False


def test_start_sets_remaining_time_and_activates_timer():
    timer = Timer()

    timer.start(10)

    assert timer.get_remaining() == 10
    assert timer.active is True
    assert timer.expired() is False


def test_update_reduces_remaining_time():
    timer = Timer(10)
    timer.start(10)

    timer.update(3)

    assert timer.get_remaining() == 7


def test_timer_does_not_go_below_zero():
    timer = Timer()
    timer.start(2)

    timer.update(5)

    assert timer.get_remaining() == 0


def test_timer_expires_when_countdown_reaches_zero():
    timer = Timer()
    timer.start(3)

    timer.update(3)

    assert timer.expired() is True


def test_inactive_timer_does_not_count_down():
    timer = Timer(10)

    timer.update(4)

    assert timer.get_remaining() == 10
    assert timer.expired() is False
