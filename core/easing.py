"""
core/easing.py
Owner: Member 1 - Core Game System

Easing curves for the shared animation kit. Every function maps t in [0, 1]
to a progress value (0 at the start, 1 at the end) and clamps t first, so
callers can pass raw elapsed/duration ratios.
"""

import math


def clamp01(t):
    return max(0.0, min(1.0, t))


def linear(t):
    return clamp01(t)


def ease_in_quad(t):
    t = clamp01(t)
    return t * t


def ease_out_quad(t):
    t = clamp01(t)
    return 1.0 - (1.0 - t) ** 2


def ease_in_out_quad(t):
    t = clamp01(t)
    if t < 0.5:
        return 2.0 * t * t
    return 1.0 - ((-2.0 * t + 2.0) ** 2) / 2.0


def ease_out_cubic(t):
    t = clamp01(t)
    return 1.0 - (1.0 - t) ** 3


def ease_out_back(t, overshoot=1.70158):
    """Overshoots 1.0 then settles; good for pop-in UI."""
    t = clamp01(t)
    c3 = overshoot + 1.0
    return 1.0 + c3 * (t - 1.0) ** 3 + overshoot * (t - 1.0) ** 2


def ease_out_elastic(t):
    t = clamp01(t)
    if t in (0.0, 1.0):
        return t
    return 2.0 ** (-10.0 * t) * math.sin((t * 10.0 - 0.75) * (2.0 * math.pi / 3.0)) + 1.0


def lerp(a, b, t):
    return a + (b - a) * t


class Tween:
    """Time-driven value from `start` to `end` over `duration` seconds."""

    def __init__(self, start, end, duration, ease=ease_out_cubic):
        if duration <= 0:
            raise ValueError("duration must be positive")
        self.start = start
        self.end = end
        self.duration = duration
        self.ease = ease
        self.elapsed = 0.0

    def update(self, dt):
        self.elapsed = min(self.duration, self.elapsed + max(0.0, dt))
        return self.value

    @property
    def value(self):
        return lerp(self.start, self.end, self.ease(self.elapsed / self.duration))

    @property
    def done(self):
        return self.elapsed >= self.duration
