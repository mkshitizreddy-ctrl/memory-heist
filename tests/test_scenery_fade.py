"""Backdrop scenery (skyline, searchlights, windows) and the fade between screens."""

import math
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from ui import backdrop as B
from ui import theme
from ui import transitions as T


@pytest.fixture
def surf():
    pygame.init()
    return pygame.Surface((960, 640))


# --- skyline ----------------------------------------------------------------------
def test_the_towers_cover_the_full_width_and_stay_below_the_text():
    towers = B.tower_layout(960)
    assert towers[0][0] == 0
    last_x, last_w, _ = towers[-1]
    assert last_x + last_w >= 960
    heights = sorted(h for _, _, h in towers)
    assert heights[-2] < 120 and heights[-1] == 168          # one tall spire, the rest low


def test_the_spire_stands_near_the_middle():
    towers = B.tower_layout(960)
    x, w, h = max(towers, key=lambda t: t[2])
    assert abs(x + w // 2 - 480) < 60


def test_the_layout_is_deterministic():
    assert B.tower_layout(960) == B.tower_layout(960)


def test_every_window_sits_inside_its_tower():
    towers = B.tower_layout(960)
    for cx, cy, phase in B.window_slots(towers):
        assert any(x <= cx and cx + 3 <= x + w and cy < h for x, w, h in towers)
        assert 0 <= phase < 6.3


def test_windows_are_dark_part_of_the_time_and_lit_part_of_it():
    levels = [B.window_level(t, 1.0) for t in range(0, 1200, 4)]
    assert min(levels) == 0.0 and max(levels) > 0.9
    assert all(0.0 <= v <= 1.0 for v in levels)
    one = [B.window_level(t, 0.5) for t in range(0, 1200, 4)]
    other = [B.window_level(t, 3.5) for t in range(0, 1200, 4)]
    assert one != other                                      # windows do not all blink together


def test_the_skyline_is_cached_per_size_and_tint():
    a = B.skyline((960, 640), theme.SKY)
    assert a is B.skyline((960, 640), theme.SKY)
    assert a is not B.skyline((960, 640), theme.CORAL)


# --- searchlights -----------------------------------------------------------------
def test_beam_angles_sweep_within_the_swing_and_on_the_cache_steps():
    angles = {B.beam_angle(t) for t in range(0, 2000, 7)}
    assert all(abs(a) <= B.BEAM_SWING and a % B.BEAM_STEP == 0 for a in angles)
    assert min(angles) < 0 < max(angles)


def test_the_two_beams_are_out_of_step():
    assert any(B.beam_angle(t, 0.0) != B.beam_angle(t, 2.4) for t in range(0, 600, 5))


def test_a_beams_foot_stays_on_its_source_whatever_its_tilt():
    h = B.BEAM_SIZE[1]
    for angle in (-24, -10, 0, 10, 24):
        cx, cy = B.beam_centre((300, 570), h, angle)
        rad = math.radians(angle)
        foot = (cx + (h / 2) * math.sin(rad), cy + (h / 2) * math.cos(rad))
        assert foot == pytest.approx((300, 570))
    assert B.beam_centre((300, 570), h, 0) == pytest.approx((300, 570 - h / 2))


def test_beam_frames_are_cached():
    assert B.beam(4, theme.SKY) is B.beam(4, theme.SKY)


# --- drawing -----------------------------------------------------------------------
def test_scenery_changes_the_bottom_of_the_screen_but_not_the_top(surf):
    other = pygame.Surface((960, 640))
    B.draw_backdrop(surf, 40, theme.SKY, scenery=True)
    B.draw_backdrop(other, 40, theme.SKY, scenery=False)
    bottom = pygame.Rect(0, 520, 960, 120)
    assert pygame.image.tostring(surf.subsurface(bottom), "RGB") != pygame.image.tostring(other.subsurface(bottom), "RGB")


def test_the_scenery_animates(surf):
    other = pygame.Surface((960, 640))
    B.draw_backdrop(surf, 0, theme.SKY)
    B.draw_backdrop(other, 600, theme.SKY)
    assert pygame.image.tostring(surf, "RGB") != pygame.image.tostring(other, "RGB")


def test_windows_change_as_time_passes(surf, monkeypatch):
    monkeypatch.setattr(B, "beam_angle", lambda tick, phase=0.0: 0)     # hold the beams still
    other = pygame.Surface((960, 640))
    B.draw_scenery(surf, 0, theme.SKY)
    B.draw_scenery(other, 150, theme.SKY)
    strip = pygame.Rect(0, 560, 960, 80)
    assert pygame.image.tostring(surf.subsurface(strip), "RGB") != pygame.image.tostring(other.subsurface(strip), "RGB")


def test_the_scenery_asks_for_two_different_beam_phases(surf, monkeypatch):
    phases = []
    monkeypatch.setattr(B, "beam_angle", lambda tick, phase=0.0: phases.append(phase) or 0)
    B.draw_scenery(surf, 10, theme.SKY)
    assert len(phases) == len(B.BEAM_SOURCES) and len(set(phases)) == len(phases)


# --- state fade --------------------------------------------------------------------
def test_the_fade_starts_black_and_ends_clear():
    assert T.state_fade_alpha(1.0) == 255
    assert T.state_fade_alpha(0.0) == 0
    assert T.state_fade_alpha(2.0) == 255 and T.state_fade_alpha(-1.0) == 0
    values = [T.state_fade_alpha(p / 20) for p in range(21)]
    assert values == sorted(values)


def test_the_fade_eases_so_it_lingers_on_black_at_first():
    assert T.state_fade_alpha(0.5) == 63


def test_draw_state_fade_darkens_the_surface(surf):
    surf.fill((200, 200, 200))
    T.draw_state_fade(surf, 1.0)
    assert surf.get_at((5, 5))[:3] == (0, 0, 0)
    surf.fill((200, 200, 200))
    T.draw_state_fade(surf, 0.5)
    assert 0 < surf.get_at((5, 5))[0] < 200
    surf.fill((200, 200, 200))
    T.draw_state_fade(surf, 0.0)
    assert surf.get_at((5, 5))[:3] == (200, 200, 200)


def make_game():
    from core.game import Game
    g = Game()
    g.running = True
    return g


def test_changing_to_a_screen_starts_the_fade_and_it_runs_out():
    g = make_game()
    g.change_state("lose")
    assert g._state_fade == 1.0
    g.update(T.STATE_FADE_SECONDS / 2)
    assert 0 < g._state_fade < 1
    g.update(T.STATE_FADE_SECONDS)
    assert g._state_fade == 0.0


def test_levels_use_the_elevator_not_the_fade():
    g = make_game()
    g.change_state("menu")
    g._state_fade = 0.0
    g.change_state("playing")
    assert g._state_fade == 0.0


def test_staying_on_the_same_screen_does_not_restart_the_fade():
    g = make_game()
    g.change_state("lose")
    g.update(1.0)
    g.change_state("lose")
    assert g._state_fade == 0.0


def test_a_fading_screen_is_black_at_first_and_visible_once_settled():
    g = make_game()
    g.change_state("lose")
    g.render()
    centre = (480, 380)                                  # inside the lose screen's score panel
    assert g.screen.get_at(centre)[:3] == (0, 0, 0)
    g.update(1.0)
    g.render()
    assert g.screen.get_at(centre)[:3] != (0, 0, 0)
