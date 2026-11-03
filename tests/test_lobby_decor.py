"""Lobby decoration: baked props, ambient motion, and a promise not to disturb play."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import math
import random

import pygame
import pytest

from levels import lobby_decor as D
from levels.floor1_lobby import FloorOneLobby
from tests.test_floor1_lobby import make_level
from ui import theme

SENTINEL = (1, 2, 3)
DESK = pygame.Rect(12 * D.TILE, 15 * D.TILE, 6 * D.TILE, D.TILE)
VENDING = pygame.Rect(26 * D.TILE, 12 * D.TILE, D.TILE, 2 * D.TILE)
TEXT_BAND = pygame.Rect(64, 44, 496, 52)          # title and message line
HINT_BAND = pygame.Rect(740, 44, 160, 26)
BIN_ROW = pygame.Rect(8 * D.TILE, 4 * D.TILE, 14 * D.TILE, D.TILE)


@pytest.fixture(autouse=True)
def display_init():
    pygame.init()
    pygame.display.set_mode((960, 640))


def painted(surface, rect):
    """True if anything inside `rect` differs from the sentinel fill."""
    return any(surface.get_at((x, y))[:3] != SENTINEL
               for x in range(rect.left, rect.right) for y in range(rect.top, rect.bottom))


def baked():
    bg = pygame.Surface((960, 640))
    bg.fill(SENTINEL)
    D.draw_static(bg, theme.floor_palette("level1")["accent"], DESK)
    return bg


# --- pure helpers -----------------------------------------------------------
def test_clock_hands_turn_at_the_right_speeds():
    assert D.clock_angles(0) == (0.0, 0.0, 0.0)
    sec, minute, hour = D.clock_angles(15)
    assert sec == pytest.approx(math.pi / 2) and minute < 0.03 and hour < 0.003
    assert D.clock_angles(60)[0] == pytest.approx(0.0)
    assert D.clock_angles(60)[1] == pytest.approx(math.tau / 60)
    assert D.clock_angles(3600)[1] == pytest.approx(0.0)
    assert D.clock_angles(3600)[2] == pytest.approx(math.tau / 12)
    assert D.clock_angles(43200)[2] == pytest.approx(0.0)


def test_each_light_stutters_in_its_turn_and_is_steady_otherwise():
    period = D.FLICKER_PERIOD
    for i in range(len(D.LIGHT_COLS)):
        t = i * period + 0.05
        assert D.flicker(t, i) < 1.0
        others = [D.flicker(t, j) for j in range(len(D.LIGHT_COLS)) if j != i]
        assert others == [1.0] * (len(D.LIGHT_COLS) - 1)
        assert D.flicker(i * period + D.FLICKER_SECONDS + 0.2, i) == 1.0
    values = [D.flicker(t / 20, i) for t in range(2000) for i in range(len(D.LIGHT_COLS))]
    assert 0.35 <= min(values) < 0.6 and max(values) == 1.0
    assert sum(values) / len(values) > 0.95                      # a stutter, not a strobe


def test_the_beam_sweeps_symmetrically_around_straight_down():
    assert D.scan_angle(0) == pytest.approx(math.pi / 2)
    quarter = D.SWEEP_SECONDS / 4
    assert D.scan_angle(quarter) == pytest.approx(math.pi / 2 + D.SWEEP)
    assert D.scan_angle(3 * quarter) == pytest.approx(math.pi / 2 - D.SWEEP)
    assert D.scan_angle(1.3 + D.SWEEP_SECONDS) == pytest.approx(D.scan_angle(1.3))
    assert all(abs(D.scan_angle(t / 10) - math.pi / 2) <= D.SWEEP + 1e-9 for t in range(200))


def test_cone_is_a_fan_from_the_origin():
    pts = D.cone_points((100, 50), math.pi / 2, length=80, spread=0.3, arc=4)
    assert pts[0] == (100, 50) and len(pts) == 6
    assert all(math.dist(p, (100, 50)) == pytest.approx(80) for p in pts[1:])
    a0 = math.atan2(pts[1][1] - 50, pts[1][0] - 100)
    a1 = math.atan2(pts[-1][1] - 50, pts[-1][0] - 100)
    assert abs(a0 - a1) == pytest.approx(0.6)
    assert (pts[1][0] + pts[-1][0]) / 2 == pytest.approx(100)    # centred on the angle


def test_the_beam_is_stronger_on_alert():
    assert D.scan_alpha(True) > D.scan_alpha(False) > 0


# --- dust motes -------------------------------------------------------------
def test_motes_stay_inside_their_area_however_long_they_drift():
    motes = D.Motes(random.Random(1), D.MOTE_AREA)
    assert len(motes.motes) == D.MOTE_COUNT
    for _ in range(600):
        motes.update(0.5)
        assert all(D.MOTE_AREA.left <= m["x"] < D.MOTE_AREA.right
                   and D.MOTE_AREA.top <= m["y"] < D.MOTE_AREA.bottom for m in motes.motes)


def test_motes_drift_only_when_time_passes_and_are_deterministic():
    a, b = D.Motes(random.Random(5), D.MOTE_AREA), D.Motes(random.Random(5), D.MOTE_AREA)
    assert a.motes == b.motes
    before = [dict(m) for m in a.motes]
    a.update(0.0)
    a.update(-3.0)
    assert a.motes == before
    a.update(1.0)
    assert sum(1 for m, n in zip(a.motes, before) if (m["x"], m["y"]) != (n["x"], n["y"])) == D.MOTE_COUNT
    assert D.Motes(random.Random(6), D.MOTE_AREA).motes != b.motes


def test_motes_wrap_to_the_far_side():
    motes = D.Motes(random.Random(0), D.MOTE_AREA, count=1)
    motes.motes[0].update(x=D.MOTE_AREA.right - 0.5, y=D.MOTE_AREA.centery, vx=10.0, vy=0.0)
    motes.update(1.0)
    assert D.MOTE_AREA.left <= motes.motes[0]["x"] < D.MOTE_AREA.left + 10


# --- baked decoration -------------------------------------------------------
@pytest.mark.parametrize("name,rect", [
    ("rug", D.RUG.inflate(-40, -40)), ("notice board", D.BOARD), ("poster", D.POSTER),
    ("extinguisher", D.EXTINGUISHER), ("exit stripes", D.STRIPES[0]),
    ("elevator stripes", D.STRIPES[1]), ("indicator", D.INDICATOR),
    ("clock", pygame.Rect(D.CLOCK_CENTRE[0] - 12, D.CLOCK_CENTRE[1] - 12, 24, 24)),
    ("desk clutter", pygame.Rect(DESK.x, DESK.y - 28, DESK.w, 26))])
def test_each_decoration_is_actually_drawn(name, rect):
    assert painted(baked(), rect), name


@pytest.mark.parametrize("name,rect", [
    ("title and message", TEXT_BAND), ("hint text", HINT_BAND), ("bins", BIN_ROW),
    ("camera mount", pygame.Rect(20 * D.TILE, 2 * D.TILE + 4, 22, 12))])
def test_decoration_never_covers_text_bins_or_the_camera(name, rect):
    assert not painted(baked(), rect), name


def test_decoration_stays_off_the_crate_spots_that_are_not_on_the_rug():
    from levels.floor1_lobby import CRATE_SPOTS
    bg = baked()
    for col, row in CRATE_SPOTS:
        spot = pygame.Rect(col * D.TILE, row * D.TILE, D.TILE, D.TILE)
        if not D.RUG.colliderect(spot):
            assert not painted(bg, spot), (col, row)


def test_the_monitor_sits_on_the_desks_right_end():
    m = D.monitor_rect(DESK)
    assert m.right < DESK.right and m.bottom <= DESK.y and m.w > 0 and m.h > 0


# --- ambience ---------------------------------------------------------------
def blank():
    s = pygame.Surface((960, 640))
    s.fill(SENTINEL)
    return s


def frame(time, alert=False, fill=None):
    amb = D.Ambience(seed=2)
    amb.update(time)
    s = blank()
    if fill:
        s.fill(fill)
    amb.draw(s, DESK, VENDING, alert)
    return s


def region_differs(a, b, rect):
    return any(a.get_at((x, y)) != b.get_at((x, y))
               for x in range(rect.left, rect.right) for y in range(rect.top, rect.bottom))


def test_time_only_moves_forward():
    amb = D.Ambience()
    amb.update(0.5)
    amb.update(-4.0)
    assert amb.time == pytest.approx(0.5)


@pytest.mark.parametrize("name,rect,t0,t1", [
    ("clock hands", pygame.Rect(D.CLOCK_CENTRE[0] - 14, D.CLOCK_CENTRE[1] - 14, 28, 28), 0.0, 15.0),
    ("monitor", D.monitor_rect(DESK), 0.0, 1.3),
    ("elevator arrow", D.INDICATOR, 0.0, 0.5),
    ("vending slot", pygame.Rect(VENDING.x + 5, VENDING.y + 6, 22, 36), 0.0, 0.7)])
def test_things_animate(name, rect, t0, t1):
    assert region_differs(frame(t0), frame(t1), rect), name


def test_dust_is_drawn_and_drifts():
    amb = D.Ambience(seed=2)
    s = blank()
    amb._draw_motes(s)
    marks = sum(1 for x in range(D.MOTE_AREA.left, D.MOTE_AREA.right)
                for y in range(D.MOTE_AREA.top, D.MOTE_AREA.bottom) if s.get_at((x, y))[:3] != SENTINEL)
    assert D.MOTE_COUNT <= marks <= 2 * D.MOTE_COUNT
    assert region_differs(frame(0.0), frame(5.0), D.MOTE_AREA)


def test_every_frame_draws_the_dust(monkeypatch):
    amb = D.Ambience()
    drawn = []
    monkeypatch.setattr(D.Ambience, "_draw_motes", lambda self, world: drawn.append(world))
    amb.draw(blank(), DESK, VENDING)
    assert len(drawn) == 1


def test_the_clock_has_a_dark_rim():
    x, y = D.CLOCK_CENTRE
    assert baked().get_at((x + D.CLOCK_RADIUS + 2, y))[:3] == tuple(theme.INK[:3])


def test_the_beam_lights_the_floor_below_the_camera_and_nowhere_sideways():
    s = frame(0.0, fill=(0, 0, 0))
    below = (D.CAMERA_ORIGIN[0], D.CAMERA_ORIGIN[1] + 90)
    beside = (D.CAMERA_ORIGIN[0] + 140, D.CAMERA_ORIGIN[1] + 8)
    assert s.get_at(below)[:3] != (0, 0, 0)
    assert s.get_at(beside)[:3] == (0, 0, 0)


def test_the_beam_is_brighter_and_redder_on_alert():
    calm, alarmed = frame(0.0, fill=(0, 0, 0)), frame(0.0, True, fill=(0, 0, 0))
    p = (D.CAMERA_ORIGIN[0], D.CAMERA_ORIGIN[1] + 90)
    c, a = calm.get_at(p), alarmed.get_at(p)
    assert sum(a[:3]) > sum(c[:3])
    assert c[0] < c[1] and a[0] > a[1]                # teal when calm, coral on alert


def test_a_stuttering_light_dims_and_a_steady_one_does_not():
    light0 = (D.LIGHT_COLS[0] * D.TILE, 2 * D.TILE + 27)
    light1 = (D.LIGHT_COLS[1] * D.TILE, 2 * D.TILE + 27)
    amb = D.Ambience()
    amb.update(0.05)
    s = blank()
    s.fill((255, 255, 255))
    amb.draw(s, DESK, VENDING)
    assert sum(s.get_at(light0)[:3]) < 3 * 255
    assert s.get_at(light1)[:3] == (255, 255, 255)


# --- inside the real level --------------------------------------------------
def test_decoration_adds_nothing_to_collide_with():
    level, _, _ = make_level()
    assert len(level.props) == 11                     # 4 bins, desk, 4 plants, sofa, vending
    assert level.room_map.blocked(pygame.Rect(D.RUG.centerx, D.RUG.centery, 8, 8)) is False
    for stripe in D.STRIPES:                          # floor decals are walked on, not around
        assert level.room_map.blocked(stripe) is False


def test_the_level_animates_but_leaves_its_own_randomness_alone():
    level, _, _ = make_level(seed=4)
    state = level.rng.getstate()
    homes = [c.rect.topleft for c in level.crates]
    surface = pygame.Surface((960, 640))
    level.render(surface)
    level.update(1 / 60)
    first = surface.copy()
    for _ in range(300):
        level.update(1 / 60)
    level.render(surface)
    assert level.ambience.time > 4.9
    assert level.rng.getstate() == state
    assert [c.rect.topleft for c in level.crates] == homes
    assert region_differs(first, surface, pygame.Rect(0, 0, 960, 640))


def test_the_background_with_its_decoration_is_built_only_once():
    level, _, _ = make_level()
    surface = pygame.Surface((960, 640))
    level.render(surface)
    built = level._background
    level.update(1.0)
    level.render(surface)
    assert level._background is built


def test_the_camera_alert_matches_the_security_meter():
    level, game, _ = make_level()
    assert level._alerted() is False
    game.security.level = game.security.max_level * 0.5
    assert level._alerted() is True
    game.security.level = game.security.max_level * 0.5 - 1
    assert level._alerted() is False
    assert FloorOneLobby(game=None)._alerted() is False


def test_the_decorated_lobby_still_renders_under_alert():
    level, game, _ = make_level()
    game.security.level = game.security.max_level
    surface = pygame.Surface((960, 640))
    level.render(surface)
    assert surface.get_at((0, 0)) is not None


def test_the_level_bakes_the_decoration_once_with_its_own_desk(monkeypatch):
    calls = []
    monkeypatch.setattr(D, "draw_static", lambda bg, accent, desk: calls.append((accent, desk)))
    level, _, _ = make_level()
    surface = pygame.Surface((960, 640))
    level.render(surface)
    level.render(surface)
    assert calls == [(theme.floor_palette("level1")["accent"], level.desk)]


def test_the_level_tells_the_ambience_its_desk_vending_machine_and_alert(monkeypatch):
    level, game, _ = make_level()
    seen = []
    monkeypatch.setattr(level.ambience, "draw", lambda world, desk, vending, alert=False:
                        seen.append((desk, vending, alert)))
    surface = pygame.Surface((960, 640))
    level.render(surface)
    game.security.level = game.security.max_level
    level.render(surface)
    assert seen == [(level.desk, level.vending, False), (level.desk, level.vending, True)]
