"""The restyled HUD: floor colour, count-up score, cell meter, timer pill."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

import ui.hud as hud
from ui import theme

W = 960


@pytest.fixture(autouse=True)
def init():
    pygame.init()


def draw(h, level="level1", **kw):
    s = pygame.Surface((W, 48))
    s.fill((0, 0, 0))
    kw.setdefault("score", 0)
    h.render(s, level, **kw)
    return s


# --- pure helpers --------------------------------------------------------
@pytest.mark.parametrize("level, colour", [
    (0, theme.TEAL), (49, theme.TEAL), (50, theme.GOLD), (79, theme.GOLD),
    (80, theme.CORAL), (100, theme.CORAL)])
def test_security_colour_bands(level, colour):
    assert hud.security_colour(level) == colour


@pytest.mark.parametrize("level, maximum, expected", [
    (0, 100, 0), (1, 100, 1), (5, 100, 1), (6, 100, 2), (50, 100, 10),
    (100, 100, 20), (150, 100, 20), (-5, 100, 0), (3, 0, 20)])
def test_lit_segments(level, maximum, expected):
    assert hud.lit_segments(level, maximum) == expected


def test_count_up_moves_toward_target_and_snaps():
    assert hud.count_up(0, 100) == pytest.approx(25)
    assert hud.count_up(100, 0) == pytest.approx(75)
    assert hud.count_up(99.5, 100) == 100
    shown = 0.0
    for _ in range(60):
        shown = hud.count_up(shown, 250)
    assert shown == 250


# --- behaviour -----------------------------------------------------------
def test_first_frame_shows_the_real_score_not_zero():
    h = hud.HUD()
    assert h._score_value(1200) == 1200


def test_score_counts_up_gradually_then_settles():
    h = hud.HUD()
    h._score_value(0)
    seen = [h._score_value(100) for _ in range(40)]
    assert 0 < seen[0] < 100
    assert seen == sorted(seen)
    assert seen[-1] == 100


def test_score_gain_triggers_a_glow_that_fades():
    h = hud.HUD()
    h._score_value(0)
    h._score_value(50)
    assert h._flash > 0
    for _ in range(40):
        h._score_value(50)
    assert h._flash == 0


def test_losing_points_does_not_glow():
    h = hud.HUD()
    h._score_value(100)
    h._score_value(60)
    assert h._flash == 0


def test_bar_line_uses_the_floors_accent_colour():
    a = draw(hud.HUD(), "level1")
    b = draw(hud.HUD(), "level2")
    assert a.get_at((600, 47))[:3] != b.get_at((600, 47))[:3]


def test_floor_name_is_shown_in_the_floors_accent_colour():
    seen = []

    class Rec:
        def __init__(self, f): self.f = f
        def render(self, text, aa, colour, *a, **k):
            seen.append((text, colour))
            return self.f.render(text, aa, colour, *a, **k)

    h = hud.HUD()
    h.tiny = Rec(h.tiny)
    draw(h, "level3")
    assert ("LASER CORRIDOR", theme.floor_palette("level3")["accent"]) in seen


def lit_cells(surface, colour):
    n = 0
    for i in range(hud.SEGMENTS):
        x = int(360 + i * (160 / hud.SEGMENTS)) + 2
        if surface.get_at((x, 29))[:3] == colour:
            n += 1
    return n


def test_meter_lights_cells_in_proportion_and_colour():
    s = draw(hud.HUD(), security_level=30, security_max=100)
    assert lit_cells(s, theme.TEAL) == 6
    s = draw(hud.HUD(), security_level=60, security_max=100)
    assert lit_cells(s, theme.GOLD) == 12


def test_meter_pulses_only_in_danger():
    calm = {draw(hud.HUD(), security_level=30, tick=t).get_at((365, 29))[:3] for t in range(0, 40, 5)}
    danger = {draw(hud.HUD(), security_level=95, tick=t).get_at((365, 29))[:3] for t in range(0, 40, 5)}
    assert len(calm) == 1
    assert len(danger) > 2


def test_timer_pill_edge_flashes_only_in_the_last_minute():
    def edges(remaining):
        return {draw(hud.HUD(), timer_remaining=remaining, tick=t).get_at((W - 133, 24))[:3]
                for t in range(0, 40, 4)}
    assert len(edges(600)) == 1
    assert len(edges(30)) > 2


def test_timer_pill_is_clear_of_the_hero_badges():
    h = hud.HUD()
    pill = pygame.Rect(W - 134, 8, 126, 32)
    for rect in h.badge_rects(W, coop=True):
        assert not rect.colliderect(pill)


def test_unknown_level_still_renders():
    draw(hud.HUD(), "mystery_floor", timer_remaining=10)
