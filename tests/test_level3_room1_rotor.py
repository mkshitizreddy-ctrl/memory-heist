"""
tests/test_level3_room1_rotor.py

Room 1 final correction: the single rotating laser must be long enough to
sweep all three safe spaces, must hurt players inside them (the safe spaces
only protect against the tracking laser), keeps its warning -> active ->
cooldown cycle, and every other room is untouched.
"""

import math
import os
import random
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.difficulty import get_difficulty
from levels.level3_loops import Level3LaserLoop
from systems.scoring import ScoreTracker

PLAYER = 32
FRAME = 1 / 60


def make_level(difficulty="medium", coop=False):
    pygame.font.init()
    random.seed(5)

    events = []
    game = SimpleNamespace(
        difficulty=get_difficulty(difficulty),
        player=SimpleNamespace(rect=pygame.Rect(80, 280, PLAYER, PLAYER)),
        player2=SimpleNamespace(rect=pygame.Rect(118, 280, PLAYER, PLAYER)),
        coop=coop,
        security=SimpleNamespace(increase=lambda amount: events.append(amount), level=0),
        score=ScoreTracker(),
    )

    level = Level3LaserLoop(game=game)
    level.room_requests.pop(1, None)     # pad geometry: every pad lit (board choice: test_level3_board_loops.py)
    level.setup_room_hazards()
    return level, game, events


def rotor(level):
    return level.lasers[0]


def nearest_point(level, rect):
    laser = rotor(level)

    return (
        min(max(laser["cx"], rect.left), rect.right),
        min(max(laser["cy"], rect.top), rect.bottom),
    )


def aim_at_nearest_point(level, rect):
    laser = rotor(level)
    x, y = nearest_point(level, rect)

    return math.degrees(math.atan2(y - laser["cy"], x - laser["cx"])) % 360.0


def legal_placements(zone):
    """Corner, edge-centre and centre placements of a 32 px player inside a zone."""

    xs = (zone.left, zone.centerx - PLAYER // 2, zone.right - PLAYER)
    ys = (zone.top, zone.centery - PLAYER // 2, zone.bottom - PLAYER)

    return [pygame.Rect(x, y, PLAYER, PLAYER) for x in xs for y in ys]


def phase_windows(level, horizon=14.0, step=0.01):
    windows = []

    for tick in range(int(horizon / step)):
        level.laser_clock = tick * step
        phase = level.laser_phase(0)

        if windows and windows[-1][0] == phase:
            windows[-1][2] = level.laser_clock + step
        else:
            windows.append([phase, level.laser_clock, level.laser_clock + step])

    return windows


def clock_in(level, phase, occurrence=0):
    found = [w for w in phase_windows(level) if w[0] == phase]
    start, end = found[occurrence][1], found[occurrence][2]

    return (start + end) / 2


def hit_with(level, events, game, rect, angle, phase="active", player="player"):
    """Aim the rotor, set the clock to a phase, and run the real collision check."""

    rotor(level)["angle"] = angle % 360.0
    level.laser_clock = clock_in(level, phase, 1 if phase == "off" else 0)
    level.laser_penalty_cooldown = 0.0
    events.clear()
    getattr(game, player).rect.topleft = rect.topleft
    level.check_laser_collision(FRAME)

    return bool(events)


# ------------------------------------------------------------------ reach

def test_the_room_1_rotor_is_one_straight_beam_through_its_pivot():
    level, _, _ = make_level()
    laser = rotor(level)

    assert len([l for l in level.lasers if l.get("axis") == "r"]) == 1
    assert laser["beam_offsets"] == (0.0,)

    corners = level._scanner_corners({**laser, "angle": 37.0})
    cx = sum(x for x, _ in corners) / 4
    cy = sum(y for _, y in corners) / 4

    assert (cx, cy) == pytest.approx((laser["cx"], laser["cy"]), abs=1e-6)
    assert math.dist(corners[0], corners[1]) == pytest.approx(2 * laser["half"], abs=1e-6)
    assert math.dist(corners[1], corners[2]) == pytest.approx(laser["beam_width"], abs=1e-6)


def test_the_beam_is_long_enough_for_the_farthest_legal_spot_in_every_safe_space():
    level, _, _ = make_level()
    laser = rotor(level)
    pivot = (laser["cx"], laser["cy"])
    margin = 8

    for zone in level.safe_zones:
        placements = [
            pygame.Rect(x, y, PLAYER, PLAYER)
            for x in range(zone.left, zone.right - PLAYER + 1)
            for y in range(zone.top, zone.bottom - PLAYER + 1)
        ]
        needed = max(
            math.dist(pivot, nearest_point(level, rect)) for rect in placements
        )

        assert laser["half"] >= needed + margin, (tuple(zone), needed)


@pytest.mark.parametrize("zone_index", (0, 1, 2))
def test_some_beam_angle_hits_every_legal_placement_in_each_safe_space(zone_index):
    level, _, _ = make_level()
    zone = level.safe_zones[zone_index]

    for x in range(zone.left, zone.right - PLAYER + 1, 6):
        for y in range(zone.top, zone.bottom - PLAYER + 1, 6):
            rect = pygame.Rect(x, y, PLAYER, PLAYER)

            assert level.player_in_safe_pocket(rect)
            assert any(
                level._scanner_hits_rect({**rotor(level), "angle": float(a)}, rect)
                for a in range(360)
            ), (zone_index, x, y)


def test_the_beam_stays_inside_the_room_horizontally():
    level, _, _ = make_level()
    laser = rotor(level)
    bounds = level.room_map.current.bounds

    assert bounds.left < laser["cx"] - laser["half"]
    assert laser["cx"] + laser["half"] < bounds.right


# ------------------------------------------------- damage in the safe spaces

@pytest.mark.parametrize("zone_index", (0, 1, 2))
def test_the_rotor_hurts_a_player_inside_every_safe_space(zone_index):
    level, game, events = make_level()

    for rect in legal_placements(level.safe_zones[zone_index]):
        assert level.player_in_safe_pocket(rect)
        assert hit_with(level, events, game, rect, aim_at_nearest_point(level, rect)), rect


@pytest.mark.parametrize("zone_index", (0, 1, 2))
def test_a_player_outside_the_beam_takes_no_rotor_damage(zone_index):
    level, game, events = make_level()

    for rect in legal_placements(level.safe_zones[zone_index]):
        assert not hit_with(level, events, game, rect, aim_at_nearest_point(level, rect) + 90.0), rect


@pytest.mark.parametrize("phase", ("off", "warning"))
@pytest.mark.parametrize("zone_index", (0, 1, 2))
def test_no_rotor_damage_during_warning_or_cooldown(zone_index, phase):
    level, game, events = make_level()

    for rect in legal_placements(level.safe_zones[zone_index]):
        assert not hit_with(level, events, game, rect, aim_at_nearest_point(level, rect), phase=phase), (phase, rect)


def test_one_continuous_collision_costs_one_penalty_and_the_beam_then_re_arms():
    level, game, events = make_level()
    rect = legal_placements(level.safe_zones[1])[4]
    rotor(level)["angle"] = aim_at_nearest_point(level, rect)
    level.laser_clock = clock_in(level, "active")
    level.laser_penalty_cooldown = 0.0
    game.player.rect.topleft = rect.topleft

    for _ in range(60):                       # a full second of overlap
        level.check_laser_collision(FRAME)

    assert len(events) == 1
    assert level.laser_phase(0) == "off"       # the existing re-arm after a hit


# -------------------------------------------------------------- timing

@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_rotor_cycle_is_warning_then_active_then_cooldown_with_a_short_fair_warning(difficulty):
    level, _, _ = make_level(difficulty)
    laser = rotor(level)
    windows = phase_windows(level)
    phases = [w[0] for w in windows]

    assert phases[:4] == ["off", "warning", "active", "off"]
    assert 0.8 <= laser["warning_duration"] <= 1.1
    assert windows[1][2] - windows[1][1] == pytest.approx(laser["warning_duration"], abs=0.03)
    assert windows[2][2] - windows[2][1] == pytest.approx(laser["active_duration"], abs=0.03)
    assert windows[3][2] - windows[3][1] == pytest.approx(laser["cooldown_duration"], abs=0.03)
    assert laser["cooldown_duration"] >= 5.0                 # time to reposition


def test_medium_values_and_rotation_speeds_are_as_designed():
    medium, _, _ = make_level("medium")

    assert rotor(medium)["warning_duration"] == pytest.approx(0.90)
    assert rotor(medium)["speed"] == pytest.approx(32.0)
    assert rotor(make_level("easy")[0])["speed"] < 32.0 < rotor(make_level("hard")[0])["speed"]


# ----------------------------------------------- tracking laser + co-op

def tracking_beam(level, zone, inside):
    """A tracking beam crossing a safe space, plus a player inside / just outside it."""

    template = level.emitters[0]
    vertical_down = zone.top > 300
    emitter = dict(template, state="active", target=None, angle=90.0 if vertical_down else -90.0,
                   origin=(zone.centerx, 300), beam_length=400.0, beam_width=10)
    level.emitters = [emitter]

    if vertical_down:
        y = zone.centery - PLAYER // 2 if inside else zone.bottom - PLAYER + 1
    else:
        y = zone.centery - PLAYER // 2 if inside else zone.top - 1
    rect = pygame.Rect(zone.centerx - PLAYER // 2, y, PLAYER, PLAYER)

    assert level.player_in_safe_pocket(rect) is inside

    return rect


@pytest.mark.parametrize("zone_index", (0, 1, 2))
def test_every_safe_space_still_protects_against_the_tracking_laser_only(zone_index):
    level, game, events = make_level()
    zone = level.safe_zones[zone_index]

    protected = tracking_beam(level, zone, inside=True)
    game.player.rect.topleft = protected.topleft
    level.laser_clock = 0.0                       # rotor off: only the tracking beam is live
    level.laser_penalty_cooldown = 0.0
    level.check_laser_collision(FRAME)

    assert events == []                           # inside the space: protected

    exposed = tracking_beam(level, zone, inside=False)
    game.player.rect.topleft = exposed.topleft
    level.laser_penalty_cooldown = 0.0
    level.check_laser_collision(FRAME)

    assert events                                 # one pixel outside: hit


@pytest.mark.parametrize("zone_index", (0, 1, 2))
def test_co_op_a_protected_partner_does_not_protect_the_other_player(zone_index):
    level, game, events = make_level(coop=True)
    zone = level.safe_zones[zone_index]
    inside = tracking_beam(level, zone, inside=True)
    outside = pygame.Rect(inside.x, inside.y, PLAYER, PLAYER)
    outside_rect = tracking_beam(level, zone, inside=False)

    game.player.rect.topleft = inside.topleft               # player 1: protected
    game.player2.rect.topleft = outside_rect.topleft        # player 2: exposed on the beam
    level.laser_clock = 0.0
    level.laser_penalty_cooldown = 0.0
    level.check_laser_collision(FRAME)

    assert events                                           # player 2 is hit

    events.clear()
    game.player2.rect.topleft = inside.topleft              # both inside: nobody is hit
    game.player.rect.topleft = inside.topleft
    level.laser_penalty_cooldown = 0.0
    level.check_laser_collision(FRAME)

    assert events == []


@pytest.mark.parametrize("hit_player", ("player", "player2"))
def test_co_op_the_rotor_checks_each_player_independently(hit_player):
    level, game, events = make_level(coop=True)
    other = "player2" if hit_player == "player" else "player"
    in_a = legal_placements(level.safe_zones[0])[6]
    in_c = legal_placements(level.safe_zones[2])[0]

    rotor(level)["angle"] = aim_at_nearest_point(level, in_a)
    level.laser_clock = clock_in(level, "active")
    level.laser_penalty_cooldown = 0.0
    getattr(game, hit_player).rect.topleft = in_a.topleft         # on the beam, inside SAFE A
    getattr(game, other).rect.topleft = in_c.topleft              # off the beam, inside SAFE C
    level.check_laser_collision(FRAME)

    assert len(events) == 1


def test_the_tracking_laser_locks_its_aim_and_does_not_chase_while_firing():
    level, game, events = make_level()
    emitter = level.emitters[0]
    game.player.rect.topleft = (450, 300)                     # inside the trigger, not in a safe space
    previous = None
    locked = None
    firings = 0
    tracked_angles = set()

    for _ in range(60 * 24):
        game.player.rect.x = 430
        level.update(FRAME)
        state = emitter["state"]

        if state in ("tracking", "warning"):
            tracked_angles.add(round(emitter["angle"], 3))     # it does follow the player here

        if state == "active":
            if previous != "active":
                locked = emitter["angle"]
                firings += 1

            assert emitter["angle"] == pytest.approx(locked, abs=1e-6)
            assert emitter["angle"] == pytest.approx(emitter["locked_angle"], abs=1e-6)
            game.player.rect.y = 200 if game.player.rect.y > 250 else 330   # dodge while it fires

        previous = state

    assert firings >= 2                                        # several complete firing cycles
    assert len(tracked_angles) > 1                             # the aim moved before locking


def test_tracking_laser_timings_are_unchanged():
    emitter = make_level()[0].emitters[0]

    assert (emitter["open_time"], emitter["track_time"], emitter["warn_time"], emitter["lock_time"],
            emitter["active_time"], emitter["retract_time"], emitter["cooldown_time"]) == (
        0.28, 0.36, 1.65, 0.18, 0.72, 0.24, 2.4)
    assert emitter["turn_rate"] == 62.0 and emitter["beam_width"] == 10


# ------------------------------------------------- drawing matches collision

def red_pixel(surface, x, y):
    r, g, b = tuple(surface.get_at((x, y)))[:3]

    return r > 200 and g < 90 and b < 90


def test_the_drawn_beam_matches_the_collision_beam_and_ends_at_the_room_walls():
    level, _, _ = make_level()
    laser = rotor(level)
    laser["angle"] = 165.0
    level.laser_clock = clock_in(level, "active")
    surface = pygame.Surface((960, 640))
    level.render(surface)
    bounds = level.room_map.current.bounds
    on_beam = across = 0

    for t in range(-int(laser["half"]) + 30, int(laser["half"]) - 30, 12):    # stop short of the end caps
        x = laser["cx"] + math.cos(math.radians(165.0)) * t
        y = laser["cy"] + math.sin(math.radians(165.0)) * t

        if abs(t) < 24 or not bounds.inflate(-20, -20).collidepoint(x, y) or x > 820:   # hub / gate frame
            continue

        on_beam += 1
        assert red_pixel(surface, round(x), round(y)), (t, x, y)

        px = x + math.cos(math.radians(255.0)) * 20
        py = y + math.sin(math.radians(255.0)) * 20

        if bounds.inflate(-20, -20).collidepoint(px, py):
            across += 1
            assert not red_pixel(surface, round(px), round(py))

    assert on_beam > 20 and across > 20

    laser["angle"] = 90.0                                          # straight up: must not leave the room
    level.render(surface)

    for y in range(bounds.top - 24, bounds.top - 2):
        for x in range(laser["cx"] - 12, laser["cx"] + 12):
            assert not red_pixel(surface, x, y)


# ------------------------------------------------------------ scope guard

ROOM_2_MEDIUM = [{'axis': 'x', 'direction': 1, 'max_x': 640, 'min_x': 245, 'speed': 165.0, 'x': 270, 'y': 225}, {'axis': 'y', 'bottom': 375, 'direction': 1, 'length': 95, 'phase_offset': 0.5, 'speed': 42.0, 'top': 220, 'x': 675, 'y': 245.0}]
ROOM_3_MEDIUM = [{'x': 255, 'y': 415, 'direction': 1, 'speed': 175.0, 'axis': 'x', 'max_x': 540, 'min_x': 235}, {'axis': 'y', 'x': 760, 'y': 240.0, 'length': 80, 'top': 235, 'bottom': 335, 'direction': -1, 'speed': 52.0, 'phase_offset': 2.0}, {'axis': 'r', 'cx': 520, 'cy': 285, 'half': 64, 'angle': 35.0, 'direction': -1, 'speed': 38.0, 'beam_offsets': [0.0, 90.0], 'beam_width': 16, 'danger_radius': 62, 'phase_offset': 2.5}]


def plain(value):
    if isinstance(value, dict):
        return {k: plain(v) for k, v in value.items()}

    if isinstance(value, (list, tuple)):
        return [plain(v) for v in value]

    return value


@pytest.mark.parametrize("room", (2, 3))
def test_room2_uses_new_lanes_while_room3_laser_definitions_stay_unchanged(room):
    level, _, _ = make_level()
    level.room_map.current_name = f"level3_room{room}"
    level.setup_room_hazards()

    if room == 2:
        assert [laser["axis"] for laser in level.lasers] == ["x", "y"]
        assert level.lasers[0]["width"] == 165
        assert level.lasers[0]["min_x"] == 230
        assert level.lasers[0]["max_x"] == 330
        assert level.lasers[1]["x"] == 638
        assert [laser["active_duration"] for laser in level.lasers] == [1.25, 1.25]
    else:
        assert plain(level.lasers) == ROOM_3_MEDIUM
        assert all("layout_radius" not in laser for laser in level.lasers)


def test_room_1_safe_spaces_and_the_gate_are_where_they_were():
    level, _, _ = make_level()

    assert [tuple(z) for z in level.safe_zones] == [(80, 386, 140, 54), (265, 162, 132, 52), (650, 384, 136, 52)]
    assert level.room_map.current_name == "level3_room1"
    assert tuple(level.room_map.current.bounds) == (40, 150, 880, 300)
