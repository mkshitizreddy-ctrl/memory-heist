"""The HUD shows the run timer as M:SS and warns in the last minute."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

import ui.hud as hud

NORMAL = (220, 220, 100)
WARNING = (255, 100, 100)


class RecordingFont:
    """Wraps a font and remembers every (text, colour) it was asked to draw."""

    def __init__(self, font):
        self._font = font
        self.calls = []

    def render(self, text, antialias, color, *args, **kwargs):
        self.calls.append((text, color))
        return self._font.render(text, antialias, color, *args, **kwargs)


@pytest.fixture
def surface():
    pygame.init()
    return pygame.Surface((960, 640))


def drawn_timer(surface, remaining):
    """Render the HUD and return the (text, colour) of its Time label."""
    bar = hud.HUD()
    bar.font = RecordingFont(bar.font)
    bar.render(surface, "level1", timer_remaining=remaining)
    labels = [c for c in bar.font.calls if c[0].startswith("Time")]
    return labels[0] if labels else None


@pytest.mark.parametrize(
    "seconds, expected",
    [
        (0, "0:00"),
        (0.2, "0:01"),
        (59, "0:59"),
        (60, "1:00"),
        (629.4, "10:30"),
        (899.95, "15:00"),
        (1349, "22:29"),
        (-3, "0:00"),
    ],
)
def test_format_time_is_minutes_and_seconds_rounded_up(seconds, expected):
    assert hud.format_time(seconds) == expected


def test_hud_draws_the_timer_as_minutes_and_seconds(surface):
    text, _ = drawn_timer(surface, 900)

    assert text == "Time  15:00"


def test_hud_draws_no_timer_before_the_run_starts(surface):
    assert drawn_timer(surface, None) is None


def test_timer_is_normal_colour_above_one_minute(surface):
    _, color = drawn_timer(surface, 61)

    assert color == NORMAL


def test_timer_turns_red_in_the_last_minute(surface):
    _, color = drawn_timer(surface, 60)

    assert color == WARNING
