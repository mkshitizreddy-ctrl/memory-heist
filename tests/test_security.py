
from systems.security import SecurityMeter


def test_security_starts_at_zero():
    security = SecurityMeter()

    assert security.level == 0
    assert security.is_lockdown() is False


def test_increase_security_by_default_amount():
    security = SecurityMeter()

    security.increase()

    assert security.level == 20


def test_increase_security_by_custom_amount():
    security = SecurityMeter()

    security.increase(35)

    assert security.level == 35


def test_security_level_does_not_exceed_maximum():
    security = SecurityMeter(max_level=50)

    security.increase(40)
    security.increase(30)

    assert security.level == 50


def test_lockdown_activates_at_maximum():
    security = SecurityMeter(max_level=50)

    security.increase(50)

    assert security.is_lockdown() is True


def test_reset_clears_security_level():
    security = SecurityMeter()
    security.increase(60)

    security.reset()

    assert security.level == 0
    assert security.is_lockdown() is False
