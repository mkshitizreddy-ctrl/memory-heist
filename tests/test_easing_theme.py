import pytest

from core import easing
from core.level_manager import LEVEL_ORDER
from ui import theme

CURVES = [
    easing.linear, easing.ease_in_quad, easing.ease_out_quad,
    easing.ease_in_out_quad, easing.ease_out_cubic,
    easing.ease_out_back, easing.ease_out_elastic,
]


@pytest.mark.parametrize("fn", CURVES)
def test_curve_endpoints(fn):
    assert fn(0.0) == pytest.approx(0.0, abs=1e-9)
    assert fn(1.0) == pytest.approx(1.0, abs=1e-9)


@pytest.mark.parametrize("fn", CURVES)
def test_curve_clamps_input(fn):
    assert fn(-5) == fn(0)
    assert fn(7) == fn(1)


def test_back_overshoots_then_settles():
    assert max(easing.ease_out_back(i / 100) for i in range(101)) > 1.0


def test_in_out_symmetric():
    assert easing.ease_in_out_quad(0.5) == pytest.approx(0.5)
    assert easing.ease_in_out_quad(0.25) + easing.ease_in_out_quad(0.75) == pytest.approx(1.0)


def test_tween_runs_to_end_and_stops():
    tw = easing.Tween(10, 20, 1.0, easing.linear)
    assert tw.value == 10
    assert tw.update(0.5) == pytest.approx(15)
    assert not tw.done
    assert tw.update(5.0) == 20
    assert tw.done


def test_tween_ignores_negative_dt_and_bad_duration():
    tw = easing.Tween(0, 1, 1.0, easing.linear)
    tw.update(-3)
    assert tw.elapsed == 0
    with pytest.raises(ValueError):
        easing.Tween(0, 1, 0)


def test_every_level_has_a_floor_palette():
    for name in LEVEL_ORDER:
        p = theme.FLOORS[name]
        assert p["name"] and len(p["floor"]) == 3 and len(p["accent"]) == 3


def test_floor_accents_are_distinct():
    accents = [theme.FLOORS[n]["accent"] for n in LEVEL_ORDER]
    assert len(set(accents)) == len(accents)


def test_unknown_floor_falls_back():
    assert theme.floor_palette("nope")["name"] == "NovaCorp"


def test_mix_endpoints_and_clamp():
    assert theme.mix((0, 0, 0), (200, 100, 50), 0) == (0, 0, 0)
    assert theme.mix((0, 0, 0), (200, 100, 50), 1) == (200, 100, 50)
    assert theme.mix((0, 0, 0), (200, 100, 50), 9) == (200, 100, 50)
    assert theme.mix((0, 0, 0), (200, 100, 50), 0.5) == (100, 50, 25)


def test_palette_colours_are_valid_rgb():
    cols = [theme.INK, theme.NAVY, theme.SLATE, theme.MIST, theme.PAPER,
            theme.GOLD, theme.TEAL, theme.CORAL, theme.SKY]
    for n in LEVEL_ORDER:
        cols += [theme.FLOORS[n]["floor"], theme.FLOORS[n]["accent"]]
    for c in cols:
        assert len(c) == 3 and all(0 <= v <= 255 for v in c)
