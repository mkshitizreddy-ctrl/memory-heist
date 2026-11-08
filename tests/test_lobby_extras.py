"""Floor 1 extras: the sweeping camera beam, hidden visitor chips, bell and vending machine."""

import math
import os
import random
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.player import Player
from levels import floor1_lobby as f1
from levels import lobby_extras as X
from levels.floor1_lobby import FloorOneLobby
from systems.scoring import ScoreTracker
from systems.security import SecurityMeter


@pytest.fixture(autouse=True)
def display_init():
    pygame.init()
    pygame.display.set_mode((960, 640))


def make_level(seed=1, coop=False):
    p1 = Player(100, 100)
    p2 = Player(150, 100) if coop else None
    game = SimpleNamespace(score=ScoreTracker(), security=SecurityMeter(),
                           hints=SimpleNamespace(enabled=True), coop=coop, player2=p2,
                           difficulty={"security_penalty_multiplier": 1.0})
    return FloorOneLobby(player=p1, game=game, seed=seed), game, p1


def press_e(level):
    level.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))


def into_beam(level, player, t=0.0, dist=200):
    """Put the player on the beam's centre line at time t and set the level clock."""
    level.time = t
    a = level.beam.angle(t)
    ox, oy = level.beam.origin
    player.rect.center = (int(ox + math.cos(a) * dist), int(oy + math.sin(a) * dist))


def hold_still_in_beam(level, player, seconds, t=0.0, dist=200):
    """Stay on the moving beam's line for `seconds`, in 1/60 s steps."""
    for _ in range(round(seconds * 60)):
        into_beam(level, player, level.time if level.time else t, dist)
        level.update(1 / 60)


# --- the beam ------------------------------------------------------------
def test_beam_points_straight_down_at_the_start_and_swings_both_ways():
    b = X.SweepBeam((100, 100))
    assert b.angle(0) == pytest.approx(math.pi / 2)
    assert b.angle(b.period / 4) == pytest.approx(math.pi / 2 + b.swing)
    assert b.angle(3 * b.period / 4) == pytest.approx(math.pi / 2 - b.swing)
    assert b.angle(b.period) == pytest.approx(math.pi / 2)


def test_beam_contains_points_on_its_line_and_not_outside_range_or_angle():
    b = X.SweepBeam((100, 100))
    assert b.contains((100, 300), 0)                       # straight down, in range
    assert not b.contains((100, 100 + b.length + 5), 0)    # too far
    assert b.contains((100, 100 + b.length - 5), 0)
    assert not b.contains((100, 100), 0)                   # the camera itself
    assert not b.contains((100, 20), 0)                    # behind it
    off = b.half_angle + 0.05
    assert not b.contains((100 + 200 * math.sin(off), 100 + 200 * math.cos(off)), 0)
    inside = b.half_angle - 0.05
    assert b.contains((100 + 200 * math.sin(inside), 100 + 200 * math.cos(inside)), 0)
    assert not b.contains((100 + 200 * math.sin(inside), 100 + 200 * math.cos(inside)),
                          b.period / 4)                    # the beam has swung away


def test_beam_polygon_is_a_wedge_from_the_camera():
    b = X.SweepBeam((100, 100))
    poly = b.polygon(0)
    assert poly[0] == (100, 100) and len(poly) == 3
    for x, y in poly[1:]:
        assert math.hypot(x - 100, y - 100) == pytest.approx(b.length)


# --- spotting ------------------------------------------------------------
def test_watch_spots_after_spot_time_in_the_beam_and_not_before():
    w = X.Watch(X.SweepBeam((100, 100)))
    pt = {"p": (100, 300)}
    assert w.update(X.SPOT_TIME - 0.05, 0, pt) is None
    assert w.update(0.1, 0, pt) == "p"
    assert w.spots == 1


def test_leaving_the_beam_resets_the_exposure():
    w = X.Watch(X.SweepBeam((100, 100)))
    w.update(X.SPOT_TIME - 0.05, 0, {"p": (100, 300)})
    w.update(0.1, 0, {"p": (700, 300)})                    # stepped out
    assert w.exposure["p"] == 0
    assert w.update(X.SPOT_TIME - 0.05, 0, {"p": (100, 300)}) is None


def test_watch_waits_out_the_cooldown_and_stops_after_max_spots():
    w = X.Watch(X.SweepBeam((100, 100)))
    pt, away = {"p": (100, 300)}, {"p": (700, 300)}
    assert w.update(X.SPOT_TIME, 0, pt) == "p"
    assert w.update(X.SPOT_COOLDOWN - 0.5, 0, pt) is None   # still cooling down, however long they stand
    assert w.update(0.4, 0, away) is None                   # leaving resets the exposure
    assert w.update(0.2, 0, pt) is None                     # cooldown over, exposure restarts from zero
    assert w.update(X.SPOT_TIME, 0, pt) == "p"
    for _ in range(10):
        w.update(X.SPOT_COOLDOWN, 0, away)
        w.update(X.SPOT_TIME, 0, pt)
    assert w.spots == X.MAX_SPOTS
    w.update(X.SPOT_COOLDOWN, 0, away)
    assert w.update(X.SPOT_TIME * 3, 0, pt) is None


def test_exposure_does_not_build_up_while_the_camera_cools_down():
    w = X.Watch(X.SweepBeam((100, 100)))
    pt = {"p": (100, 300)}
    assert w.update(X.SPOT_TIME, 0, pt) == "p"
    assert w.update(X.SPOT_COOLDOWN - 0.01, 0, pt) is None
    assert w.exposure["p"] == 0
    assert w.update(0.02, 0, pt) is None                     # cooldown over, but a fresh start
    assert w.update(X.SPOT_TIME - 0.05, 0, pt) is None
    assert w.update(0.1, 0, pt) == "p"


def test_danger_rises_in_the_beam_and_is_zero_outside_or_cooling_down():
    w = X.Watch(X.SweepBeam((100, 100)))
    assert w.danger() == 0
    w.update(X.SPOT_TIME / 2, 0, {"p": (100, 300)})
    assert w.danger() == pytest.approx(0.5)
    w.update(X.SPOT_TIME, 0, {"p": (100, 300)})            # spotted: cooling down
    assert w.danger() == 0


def test_danger_stops_at_one_once_the_camera_has_given_up():
    w = X.Watch(X.SweepBeam((100, 100)))
    w.spots = X.MAX_SPOTS
    w.update(5.0, 0, {"p": (100, 300)})
    assert w.danger() == 1.0


def test_two_players_are_tracked_separately():
    w = X.Watch(X.SweepBeam((100, 100)))
    w.update(0.3, 0, {"a": (100, 300), "b": (700, 300)})
    assert w.exposure["a"] == pytest.approx(0.3) and w.exposure["b"] == 0


def test_being_spotted_costs_score_and_never_security():
    level, game, p = make_level()
    game.score.add(50)
    shakes = []
    level.shake.add = lambda amount: shakes.append(amount)
    hold_still_in_beam(level, p, X.SPOT_TIME + 0.2)
    assert shakes == [0.3]
    assert game.score.get_score() == 50 - X.SPOT_PENALTY
    assert game.security.level == 0 and game.security.max_level == 100
    assert "spotted" in level.message.lower()


def test_walking_across_the_beam_quickly_is_safe():
    level, game, p = make_level()
    game.score.add(50)
    level.time = 0.0
    ox, oy = level.beam.origin
    for i in range(30):                                    # 0.5 s sprint through the wedge
        p.rect.center = (int(ox - 80 + i * 6), int(oy + 200))
        level.update(1 / 60)
    assert game.score.get_score() == 50


def test_no_more_spotting_once_the_floor_is_done():
    level, game, p = make_level()
    game.score.add(50)
    level.complete = True
    hold_still_in_beam(level, p, 1.5)
    assert game.score.get_score() == 50


# --- visitor chips -------------------------------------------------------
def test_every_possible_chip_spot_is_open_floor():
    level, _, _ = make_level()
    for spot in X.CHIP_SPOTS:
        assert not level._spot_blocked(spot), spot
        assert not level.room_map.blocked(pygame.Rect(spot[0] * 32 + 7, spot[1] * 32 + 7, 18, 18))


def test_three_distinct_chips_are_hidden_and_the_layout_follows_the_seed():
    level, _, _ = make_level(seed=5)
    assert len(level.chips) == X.CHIPS_HIDDEN
    assert len({c.rect.center for c in level.chips}) == X.CHIPS_HIDDEN
    again, _, _ = make_level(seed=5)
    assert [c.rect.center for c in again.chips] == [c.rect.center for c in level.chips]
    layouts = {tuple(c.rect.center for c in make_level(seed=s)[0].chips) for s in range(12)}
    assert len(layouts) > 1


def test_chips_do_not_change_where_the_crates_start():
    level, _, _ = make_level(seed=3)
    rng = random.Random(3)
    spots = list(f1.CRATE_SPOTS)
    rng.shuffle(spots)
    values = [c.value for c in level.crates]
    assert values == [v for v in f1.pick_crates("medium", rng)]
    assert [c.home.topleft for c in level.crates] == [(c * 32 + 2, r * 32 + 2) for c, r in spots[:6]]


def test_walking_over_a_chip_takes_it_and_scores():
    level, game, p = make_level()
    chip = level.chips[0]
    p.rect.center = chip.rect.center
    level.update(0.016)
    assert chip.taken and level.chips_found == 1
    assert game.score.get_score() == X.CHIP_POINTS
    assert "1/3" in level.message
    level.update(0.016)
    assert game.score.get_score() == X.CHIP_POINTS         # taken once only


def test_the_last_chip_pays_the_bonus():
    level, game, p = make_level()
    for chip in level.chips:
        p.rect.center = chip.rect.center
        level.update(0.016)
    assert level.chips_found == 3
    assert game.score.get_score() == 3 * X.CHIP_POINTS + X.CHIP_BONUS
    assert "all" in level.message.lower()


def test_either_player_can_take_a_chip_in_coop():
    level, game, p1 = make_level(coop=True)
    p2 = game.player2
    p2.rect.center = level.chips[1].rect.center
    p1.rect.center = (40, 400)
    level.update(0.016)
    assert level.chips[1].taken and not level.chips[0].taken


# --- bell and vending machine -------------------------------------------
def test_e_by_the_desk_rings_the_bell_and_the_receptionist_answers():
    level, _, p = make_level()
    for c in level.crates:
        c.rect.topleft = (40, 120)                         # no crate near the desk
    p.rect.midtop = (level.desk.centerx, level.desk.bottom + 2)
    press_e(level)
    assert level.receptionist.speech and level._bell_rings == 1
    first = level.receptionist.speech
    press_e(level)
    assert level._bell_rings == 2 and level.receptionist.speech != first


def test_vending_machine_pays_once_then_is_sold_out():
    level, game, p = make_level()
    for c in level.crates:
        c.rect.topleft = (40, 120)
    p.rect.midright = (level.vending.left - 2, level.vending.centery)
    press_e(level)
    assert game.score.get_score() == X.VENDING_POINTS and level.vending_used
    assert level.message == X.VENDING_LINE
    press_e(level)
    assert game.score.get_score() == X.VENDING_POINTS
    assert level.message == X.VENDING_EMPTY


def test_a_crate_in_reach_wins_over_the_props():
    level, game, p = make_level()
    crate = level.crates[0]
    crate.rect.midtop = (level.desk.centerx, level.desk.bottom + 6)
    p.rect.midtop = (level.desk.centerx, level.desk.bottom + 2)
    press_e(level)
    assert level.carried.get(id(p)) is crate and level._bell_rings == 0


def test_e_in_an_empty_corner_does_nothing():
    level, game, p = make_level()
    for c in level.crates:
        c.rect.topleft = (300, 400)
    p.rect.center = (60, 130)
    before = level.message
    press_e(level)
    assert not level.carried and level._bell_rings == 0 and not level.vending_used
    assert level.message == before


# --- drawing -------------------------------------------------------------
def test_beam_and_chips_draw_and_the_beam_reddens_with_danger():
    calm = X.draw_beam(pygame.Surface((960, 640), pygame.SRCALPHA), X.SweepBeam((480, 80)), 0, 0)
    hot = X.draw_beam(pygame.Surface((960, 640), pygame.SRCALPHA), X.SweepBeam((480, 80)), 0, 1)
    a, b = calm.get_at((480, 200)), hot.get_at((480, 200))
    assert a.a > 0 and b.a > a.a and b.r > a.r and b.g < a.g
    assert calm.get_at((20, 600)).a == 0
    surf = pygame.Surface((100, 100))
    surf.fill((0, 0, 0))
    X.draw_chip(surf, X.Chip((1, 1)), 0.0)
    assert any(surf.get_at((x, y))[:3] != (0, 0, 0) for x in range(100) for y in range(100))


def test_render_shows_chips_counter_and_survives_a_full_frame_loop():
    level, game, p = make_level()
    surf = pygame.Surface((960, 640))
    level.render(surf)
    level.chips_found = 2
    level.render(surf)
    into_beam(level, p)
    for _ in range(60):
        level.update(1 / 60)
        level.render(surf)
    level.complete = True
    level.render(surf)


def _beam_pixel(level):
    ox, oy = level.beam.origin
    return int(ox), int(oy + 220)


def test_the_beam_disappears_once_the_floor_is_done():
    level, _, _ = make_level()
    level.time = 0.0
    surf, done = pygame.Surface((960, 640)), pygame.Surface((960, 640))
    level.render(surf)
    level.complete = True
    level.render(done)
    assert surf.get_at(_beam_pixel(level)) != done.get_at(_beam_pixel(level))


def test_a_taken_chip_is_no_longer_drawn():
    level, _, _ = make_level()
    chip = level.chips[0]
    before, after = pygame.Surface((960, 640)), pygame.Surface((960, 640))
    level.render(before)
    chip.taken = True
    level.render(after)
    assert before.get_at(chip.rect.center) != after.get_at(chip.rect.center)
