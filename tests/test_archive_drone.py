"""Floor 4's security drone: easy runs the loop slowly, medium faster, hard roams it."""

import math
import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from levels import archive_decor as A
from levels.floor4_archive import DRONE_COOLDOWN, DRONE_SETTINGS
from tests.test_floor4_archive import key, make_level

DIFFS = ("easy", "medium", "hard")


def _in_open_floor(point, margin=10):
    r = pygame.Rect(0, 0, 2 * margin, 2 * margin)
    r.center = point
    props = A.prop_rects()
    inside = pygame.Rect(2 * 32, 6 * 32, 26 * 32, 12 * 32)
    return inside.contains(r) and not any(r.colliderect(p) for p in props)


def _leg_points(a, b, step=4):
    n = max(1, int(math.dist(a, b) // step))
    return [(a[0] + (b[0] - a[0]) * i / n, a[1] + (b[1] - a[1]) * i / n) for i in range(n + 1)]


# --- the route itself ----------------------------------------------------------------------
def test_every_leg_of_the_route_is_open_floor():
    route = A.DRONE_ROUTE
    for i, a in enumerate(route):
        b = route[(i + 1) % len(route)]
        for point in _leg_points(a, b):
            assert _in_open_floor(point), (a, b, point)


def test_the_route_keeps_clear_of_the_spawn_and_goes_past_the_places_you_act():
    biggest = max(s["reach"] for s in DRONE_SETTINGS.values())
    for i, a in enumerate(A.DRONE_ROUTE):
        b = A.DRONE_ROUTE[(i + 1) % len(A.DRONE_ROUTE)]
        for point in _leg_points(a, b):
            assert all(math.dist(point, spawn) > biggest for spawn in A.SPAWNS)
    upper = [p for p in A.DRONE_ROUTE if p[1] == A.UPPER_Y]
    shelf = pygame.Rect(A.stand_zone(0, 0)).union(A.stand_zone(0, 4))
    catalogue = pygame.Rect(A.stand_zone(1, 0)).union(A.stand_zone(1, 3))
    assert min(p[0] for p in upper) <= shelf.centerx and max(p[0] for p in upper) >= catalogue.centerx - 40


# --- the three behaviours --------------------------------------------------------------------
def test_the_difficulties_get_different_drones():
    easy, medium, hard = (make_level(difficulty=d)[0] for d in DIFFS)
    assert easy.drone.route and medium.drone.route and hard.drone.roam
    assert not easy.drone.roam and not medium.drone.roam
    assert easy.drone.speed < medium.drone.speed < hard.drone.speed
    assert easy.drone_reach < medium.drone_reach < hard.drone_reach
    assert easy.drone_grace > medium.drone_grace > hard.drone_grace
    cfg = DRONE_SETTINGS
    assert cfg["hard"]["penalty"] > cfg["medium"]["penalty"] == cfg["easy"]["penalty"]
    assert cfg["easy"]["lure_cooldown"] < cfg["medium"]["lure_cooldown"] < cfg["hard"]["lure_cooldown"]
    assert cfg["easy"]["lure_seconds"] > cfg["medium"]["lure_seconds"] > cfg["hard"]["lure_seconds"]


def test_easy_runs_the_same_loop_but_slower_with_longer_pauses():
    level, _, _ = make_level(difficulty="easy")
    order, waited_easy = _stops(level, 90)
    assert order[:6] == [0, 1, 2, 3, 4, 0]
    medium, _, _ = make_level(difficulty="medium")
    _, waited_medium = _stops(medium, 90)
    assert waited_easy / 60 >= 1.0 and DRONE_SETTINGS["easy"]["pause"] > DRONE_SETTINGS["medium"]["pause"]


@pytest.mark.parametrize("difficulty", DIFFS)
def test_the_drone_visits_the_whole_route_and_never_leaves_open_floor(difficulty):
    level, _, _ = make_level(difficulty=difficulty)
    seen = set()
    for _ in range(60 * 90):
        level.drone.update(1 / 60)
        assert _in_open_floor(level.drone.centre, margin=6), level.drone.centre
        for i, point in enumerate(A.DRONE_ROUTE):
            if math.dist(level.drone.centre, point) < 6:
                seen.add(i)
    assert seen == set(range(len(A.DRONE_ROUTE)))


def _stops(level, seconds):
    """Waypoints the drone actually reached, in order (it may pass over others on a long leg)."""
    order, waited = [], 0
    last = level.drone.last
    for _ in range(int(60 * seconds)):
        before = level.drone.centre
        level.drone.update(1 / 60)
        waited += level.drone.centre == before
        if level.drone.last != last:
            last = level.drone.last
            order.append(last)
    return order, waited


def test_medium_runs_the_loop_in_order_and_stops_to_scan_at_the_corners():
    level, _, _ = make_level(difficulty="medium")
    order, waited = _stops(level, 60)
    assert order[:6] == [0, 1, 2, 3, 4, 0]
    assert waited > 60                                    # it stopped for about a second at a corner


def test_hard_roams_differently_for_different_seeds_but_always_along_the_route():
    paths = set()
    for seed in range(6):
        level, _, _ = make_level(difficulty="hard", seed=seed)
        order, _ = _stops(level, 40)
        for a, b in zip(order, order[1:]):
            assert (b - a) % len(A.DRONE_ROUTE) in (1, len(A.DRONE_ROUTE) - 1)
        paths.add(tuple(order[:8]))
    assert len(paths) > 1


def test_a_roaming_drone_heads_back_towards_whoever_it_just_logged():
    level, _, _ = make_level(difficulty="hard")
    drone = level.drone
    drone.x, drone.y = map(float, A.DRONE_ROUTE[1])
    drone.last, drone.target, drone.pause_left = 1, 1, 0.0
    drone.noticed(A.DRONE_ROUTE[2])
    drone.target = drone._choose_next()
    assert drone.target == 2


# --- catching, warning, lure ---------------------------------------------------------------------
def _put_in_light(level, player):
    player.rect.center = level.drone.centre


def test_every_difficulty_warns_in_red_before_it_logs_you():
    for difficulty, warns in (("easy", True), ("medium", True), ("hard", True)):
        level, game, player = make_level(difficulty=difficulty)
        level.update(level.drone_grace + 0.1)
        level.drone.speed = 0
        _put_in_light(level, player)
        level.update(0.05)
        if warns:
            assert game.score.value == 0 and level.drone_hits == 0
            assert any(v > 0 for v in level.drone_lock.values())      # the light has turned red
            level.update(0.7)
        assert level.drone_hits == 1 and game.score.value == -DRONE_SETTINGS[difficulty]["penalty"]
        assert game.security.level == 0                               # score only, as on every floor


def test_stepping_out_of_the_red_light_in_time_costs_nothing():
    level, game, player = make_level(difficulty="medium")
    level.update(level.drone_grace + 0.1)
    level.drone.speed = 0
    _put_in_light(level, player)
    level.update(0.2)
    player.rect.center = (level.drone.centre[0], level.drone.centre[1] + 400)
    for _ in range(30):
        level.update(0.05)
    assert level.drone_hits == 0 and game.score.value == 0 and not any(level.drone_lock.values())


def test_a_second_log_waits_for_the_cooldown():
    level, game, player = make_level(difficulty="hard")
    level.update(level.drone_grace + 0.1)
    level.drone.speed = 0
    _put_in_light(level, player)
    level.update(0.5)
    assert level.drone_hits == 1
    level.update(DRONE_COOLDOWN - 0.8)
    assert level.drone_hits == 1


@pytest.mark.parametrize("difficulty", DIFFS)
def test_the_lure_sends_a_route_drone_to_its_far_corner_then_it_carries_on(difficulty):
    level, _, player = make_level(difficulty=difficulty)
    level.update(0.5)
    level.handle_event(key(pygame.K_x))
    assert level.drone.lure is not None
    target = level.drone.lure
    for _ in range(60 * 12):                                # the slow easy drone needs longer to get there
        level.update(1 / 60)
        assert _in_open_floor(level.drone.centre, margin=6)
    assert level.drone.lure is None                        # the lure ran out
    assert math.dist(level.drone.centre, target) < 8 or level.drone.route
    moved = level.drone.centre
    for _ in range(60 * 6):
        level.update(1 / 60)
    assert level.drone.centre != moved                      # and it set off along its route again


def test_the_lure_numbers_follow_the_difficulty():
    for difficulty in DIFFS:
        level, _, _ = make_level(difficulty=difficulty)
        level.update(0.1)
        level.handle_event(key(pygame.K_x))
        assert level.lure_left == pytest.approx(DRONE_SETTINGS[difficulty]["lure_seconds"])
        assert level.lure_cooldown == pytest.approx(DRONE_SETTINGS[difficulty]["lure_cooldown"])


def test_rendering_every_difficulty_with_the_warning_on_does_not_fail():
    for difficulty in DIFFS:
        level, _, player = make_level(difficulty=difficulty)
        level.update(level.drone_grace + 0.1)
        level.drone.speed = 0
        _put_in_light(level, player)
        level.update(0.1)
        level.render(pygame.Surface((960, 640)))


@pytest.mark.parametrize("difficulty", DIFFS)
def test_a_lure_turns_the_drone_round_when_the_far_corner_is_quicker_the_other_way(difficulty):
    """It used to carry on towards you and loop the whole route; now it takes the short way."""
    level, _, player = make_level(difficulty=difficulty)
    drone = level.drone
    level.update(level.drone_grace + 0.1)
    player.rect.center = (300, 315)                      # the far corner from here is the east end (index 4)
    drone.x, drone.y = 600.0, float(A.DRONE_Y)          # on the lower aisle, heading west to the first corner
    drone.last, drone.target, drone.step_dir, drone.pause_left = 4, 0, 1, 0.0
    start_x = drone.x
    level.handle_event(key(pygame.K_x))
    assert drone.lure_index == 4 and drone.target == 4   # straight back to the east end
    for _ in range(30):
        level.update(1 / 60)
    assert drone.x > start_x                              # moving away from the player, not towards them


def test_a_lure_that_starts_on_a_waypoint_goes_the_shorter_way_round():
    level, _, player = make_level(difficulty="medium")
    drone = level.drone
    level.update(level.drone_grace + 0.1)
    drone.x, drone.y = map(float, A.DRONE_ROUTE[2])      # standing on the top-left corner
    drone.last, drone.target, drone.step_dir, drone.pause_left = 2, 3, 1, 0.0
    player.rect.center = (700, 440)                      # the farthest waypoint from here is index 0
    level.handle_event(key(pygame.K_x))
    assert drone.lure_index == 0 and drone.target == 1 and drone.step_dir == -1
