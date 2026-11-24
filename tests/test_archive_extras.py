"""Floor 4 extras: the clock reset, the RUSH slip, the guarded slip, Echo's freeze and the recap."""

import math
import os
import random

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from levels import archive_decor as A
from levels import archive_requests as R
from levels.floor4_archive import (
    FREEZE_FROM_STAGE, FREEZE_SETTINGS, GUARD_PAUSE, GUARD_POSTS, MIN_CARRY_SECONDS, POINTS, RECAP_SECONDS,
    REQUESTS, SLIP_SECONDS, STREAK_FOR_REFILL, RUSH_MIN_SECONDS, RUSH_POINTS, RUSH_SHARE, TIMEOUT_PENALTY, WRONG_PENALTY, WRONG_SECURITY)
from tests.test_floor4_archive import key, make_level, stand_and_press

DIFFS = ("easy", "medium", "hard")


def solve(level, player, count=1):
    for _ in range(count):
        stand_and_press(level, player, level.request["answer"])
        level.update(level.read_hold)                  # exactly the reading hold: the clock has not moved


def wrong_index(level):
    return next(i for i in range(len(level.request["labels"])) if i != level.request["answer"])


def play_all(level, player, miss_stages=()):
    for stage in range(REQUESTS):
        if stage in miss_stages:
            stand_and_press(level, player, wrong_index(level))
            level.update(level.read_hold + 0.1)
        solve(level, player)


# --- the slip clock: carried on, refilled after two clean answers in a row ----------------------------
def test_the_slip_clock_numbers():
    assert SLIP_SECONDS == {"easy": 90, "medium": 50, "hard": 35}
    for difficulty, seconds in SLIP_SECONDS.items():
        assert make_level(difficulty=difficulty)[0].time_limit == seconds


def _first_plain_stage_pair(level):
    """A level whose requests 1 and 2 are not RUSH, so the plain clock rules show up cleanly."""
    return level.rush_stage not in (1, 2)


def _plain_level(difficulty="medium"):
    for seed in range(60):
        level, game, player = make_level(difficulty=difficulty, seed=seed)
        if level.rush_stage == 3:
            return level, game, player
    raise AssertionError("no seed with the RUSH slip last")


@pytest.mark.parametrize("difficulty", DIFFS)
def test_a_single_right_answer_carries_the_clock_on(difficulty):
    level, _, player = _plain_level(difficulty)
    level.update(12.0)
    left = level.time_left
    solve(level, player)
    assert level.streak == 1
    assert level.time_left == pytest.approx(left) and level.time_left < level.time_limit - 11


@pytest.mark.parametrize("difficulty", DIFFS)
def test_two_right_answers_in_a_row_refill_the_clock(difficulty):
    level, _, player = _plain_level(difficulty)
    level.update(12.0)
    solve(level, player)
    level.update(5.0)
    solve(level, player)
    assert level.streak == 0
    assert level.time_left == pytest.approx(level._slip_limit()) and level.stage == 2


def test_the_run_of_clean_answers_starts_over_after_a_refill():
    level, _, player = _plain_level()
    seen = []
    for _ in range(3):
        level.update(6.0)
        solve(level, player)
        seen.append(level.streak)
    assert seen == [1, 0, 1]


def test_a_wrong_answer_breaks_the_run():
    level, _, player = _plain_level()
    level.update(9.0)
    solve(level, player)                                     # streak 1
    stand_and_press(level, player, wrong_index(level))
    level.update(level.read_hold)
    assert level.streak == 0
    left = level.time_left
    solve(level, player)                                     # clean again, but only the first
    assert level.streak == 1 and level.time_left == pytest.approx(min(level._slip_limit(), left))


def test_a_timeout_breaks_the_run_and_gives_a_full_clock():
    level, _, player = _plain_level()
    level.update(9.0)
    solve(level, player)
    assert level.streak == 1
    level.time_left = 0.01
    level.update(0.05)
    assert level.streak == 0 and level.time_left == pytest.approx(level._slip_limit())


def test_a_carried_clock_never_leaves_less_than_the_minimum_to_read_the_next_slip():
    level, _, player = _plain_level()
    level.time_left = 3.0
    solve(level, player)
    assert level.streak == 1
    assert level.time_left == pytest.approx(MIN_CARRY_SECONDS)


def test_a_carried_clock_is_never_longer_than_the_next_slips_limit():
    level, _, player = make_level(seed=2)                    # request 2 is the RUSH slip on this seed
    assert level.rush_stage == 1
    solve(level, player)
    assert level.time_left <= level._slip_limit(1) + 1e-9
    assert level.time_left == pytest.approx(level._slip_limit(1))


def test_the_last_seconds_tick_again_after_a_refill():
    level, _, player = _plain_level()
    played = []
    level.sfx = played.append
    level.time_left = 5.5
    for _ in range(100):                                      # ticks 5 and 4 once each
        level.update(1 / 60)
    solve(level, player)
    level.time_left = 12.0
    solve(level, player)                                      # the second clean answer: refilled
    assert level._last_tick is None
    played.clear()
    level.time_left = 5.5
    for _ in range(100):
        level.update(1 / 60)
    assert played.count("click") == 2


def test_the_message_says_when_the_clock_refilled():
    level, _, player = _plain_level()
    solve(level, player)
    assert "Clock refilled" not in level.message
    solve(level, player)
    assert "Clock refilled" in level.message


def test_the_refill_pips_show_on_the_slip():
    level, _, player = _plain_level()
    seen = []
    real = A.draw_slip
    A.draw_slip = lambda *a, **k: seen.append(k.get("streak"))
    try:
        level.render(pygame.Surface((960, 640)))
        solve(level, player)
        level.render(pygame.Surface((960, 640)))
    finally:
        A.draw_slip = real
    assert seen == [(0, STREAK_FOR_REFILL), (1, STREAK_FOR_REFILL)]


# --- RUSH ----------------------------------------------------------------------------------------
@pytest.mark.parametrize("seed", range(30))
def test_the_rush_and_guarded_slips_are_planned_apart_and_never_the_first_rush(seed):
    level, _, _ = make_level(seed=seed)
    assert level.rush_stage in (1, 2, 3)
    assert level.guard_stage in range(REQUESTS) and level.guard_stage != level.rush_stage


def test_the_plan_is_deterministic_and_does_not_change_the_slips():
    a, _, pa = make_level(seed=11)
    b, _, pb = make_level(seed=11)
    assert (a.rush_stage, a.guard_stage) == (b.rush_stage, b.guard_stage)
    assert a.request["lines"] == R.make_request(0, random.Random(11), ["badge"], "medium")["lines"]
    solve(a, pa, 2)
    solve(b, pb, 2)
    assert a.request["lines"] == b.request["lines"]
    assert len({make_level(seed=s)[0].rush_stage for s in range(30)}) == 3


@pytest.mark.parametrize("difficulty", DIFFS)
def test_the_rush_clock_is_shorter_but_never_below_the_minimum(difficulty):
    level, _, _ = make_level(difficulty=difficulty)
    rush = level._slip_limit(level.rush_stage)
    assert RUSH_MIN_SECONDS <= rush <= level.time_limit
    assert rush < level.time_limit
    other = next(n for n in range(REQUESTS) if n != level.rush_stage)
    assert level._slip_limit(other) == level.time_limit
    assert RUSH_SHARE["easy"] > RUSH_SHARE["medium"] > RUSH_SHARE["hard"]


def test_the_rush_slip_pays_double_and_only_that_one():
    level, game, player = make_level(seed=2)
    paid = []
    for _ in range(REQUESTS):
        rush = level.request["rush"]
        before = game.score.value
        solve(level, player)
        paid.append((rush, game.score.value - before))
    assert [p for r, p in paid if r] == [RUSH_POINTS]
    assert all(p == POINTS for r, p in paid if not r) and sum(r for r, _ in paid) == 1


def test_the_rush_slip_keeps_the_normal_penalties_and_its_short_clock_after_a_miss_or_timeout():
    level, game, player = make_level(seed=2)
    while level.stage != level.rush_stage:
        solve(level, player)
    short = level._slip_limit()
    level.time_left = short                                     # a fresh clock on the RUSH slip
    assert level.request["rush"]
    stand_and_press(level, player, wrong_index(level))
    assert game.score.value % 10 != 99 and game.security.level == WRONG_SECURITY
    before = game.score.value
    level.update(level.read_hold + 0.1)
    level.time_left = 0.01
    level.update(0.05)
    assert game.score.value == before - TIMEOUT_PENALTY
    assert level.request["rush"] and level.time_left == pytest.approx(short) and level.stage == level.rush_stage
    assert WRONG_PENALTY == 10


def test_the_slip_bar_fraction_uses_the_rush_clock():
    level, _, player = make_level(seed=2)
    while level.stage != level.rush_stage:
        solve(level, player)
    level.time_left = level._slip_limit() / 2
    seen = {}
    real = A.draw_slip
    A.draw_slip = lambda *a, **k: seen.setdefault("fraction", a[4])
    try:
        level.render(pygame.Surface((960, 640)))
    finally:
        A.draw_slip = real
    assert seen["fraction"] == pytest.approx(0.5)


# --- the guarded slip ------------------------------------------------------------------------------
def _guard_level(difficulty="medium", seed=2):
    level, game, player = make_level(difficulty=difficulty, seed=seed)
    return level, game, player


def test_the_guard_post_is_the_waypoint_nearest_each_answer():
    reach = {0: [A.box_rect(i).center for i in range(5)], 1: [A.drawer_rect(i).center for i in range(4)],
             2: [A.tray_rect(i).center for i in range(3)], 3: [A.tray_rect(i).center for i in range(3)]}
    for stage, spots in reach.items():
        for spot in spots:
            nearest = min(range(len(A.DRONE_ROUTE)), key=lambda i: math.dist(A.DRONE_ROUTE[i], spot))
            assert nearest == GUARD_POSTS[stage], (stage, spot)


@pytest.mark.parametrize("difficulty", DIFFS)
def test_the_drone_only_guards_during_the_guarded_request(difficulty):
    level, _, player = make_level(difficulty=difficulty, seed=4)
    for stage in range(REQUESTS):
        guarded = stage == level.guard_stage
        assert (level.drone.guard == GUARD_POSTS[stage]) == guarded
        assert level.request["guarded"] == guarded
        solve(level, player)
    assert level.drone.guard is None                      # nothing left to guard once the vault opens


@pytest.mark.parametrize("difficulty", ["easy", "medium"])
def test_a_looping_drone_lingers_longer_at_its_guard_post(difficulty):
    level, _, _ = make_level(difficulty=difficulty, seed=2)
    drone = level.drone
    drone.set_guard(2, GUARD_PAUSE[difficulty])
    drone.x, drone.y = map(float, A.DRONE_ROUTE[2])
    drone.last, drone.target, drone.pause_left = 1, 2, 0.0
    drone.x, drone.y = A.DRONE_ROUTE[2][0] - 0.5, A.DRONE_ROUTE[2][1]
    drone.update(0.1)
    assert drone.last == 2 and drone.pause_left >= GUARD_PAUSE[difficulty] - 1e-6
    plain = make_level(difficulty=difficulty, seed=2)[0].drone
    plain.set_guard(None, 0.0)                                  # an unguarded drone for comparison
    plain.x, plain.y = A.DRONE_ROUTE[2][0] - 0.5, A.DRONE_ROUTE[2][1]
    plain.last, plain.target, plain.pause_left = 1, 2, 0.0
    plain.update(0.1)
    assert plain.pause_left < drone.pause_left


def test_a_roaming_drone_keeps_coming_back_to_its_guard_post():
    counts = {True: 0, False: 0}
    for guarded in (True, False):
        for seed in range(12):
            level, _, _ = make_level(difficulty="hard", seed=seed)
            level.drone.set_guard(4 if guarded else None, 2.2)
            last = level.drone.last
            for _ in range(60 * 40):
                level.drone.update(1 / 60)
                if level.drone.last != last:
                    last = level.drone.last
                    counts[guarded] += last == 4
    assert counts[True] > counts[False] * 1.4


def test_the_scan_flash_shows_the_drones_heading_for_a_moment():
    level, _, _ = make_level()
    level.handle_event(key(pygame.K_q))
    assert level.scan_flash > 0 and level.drone.heading() is not None
    level.update(5.0)
    assert level.scan_flash == 0
    jammed, _, _ = make_level(hints=False)
    jammed.handle_event(key(pygame.K_q))
    assert jammed.scan_flash == 0


# --- Echo's freeze -----------------------------------------------------------------------------------
def test_freeze_is_locked_until_two_requests_are_filed():
    level, _, player = make_level()
    level.handle_event(key(pygame.K_f))
    assert level.freeze_left == 0 and level.freeze_cooldown == 0 and "unlocks" in level.message
    solve(level, player, FREEZE_FROM_STAGE)
    level.handle_event(key(pygame.K_f))
    assert level.freeze_left > 0


@pytest.mark.parametrize("difficulty", DIFFS)
def test_freeze_numbers_follow_the_difficulty(difficulty):
    level, _, player = make_level(difficulty=difficulty)
    solve(level, player, FREEZE_FROM_STAGE)
    level.handle_event(key(pygame.K_f))
    cfg = FREEZE_SETTINGS[difficulty]
    assert level.freeze_left == pytest.approx(cfg["seconds"])
    assert level.freeze_cooldown == pytest.approx(cfg["cooldown"])
    assert FREEZE_SETTINGS["easy"]["cooldown"] < FREEZE_SETTINGS["medium"]["cooldown"] < FREEZE_SETTINGS["hard"]["cooldown"]
    assert FREEZE_SETTINGS["easy"]["seconds"] > FREEZE_SETTINGS["medium"]["seconds"] > FREEZE_SETTINGS["hard"]["seconds"]


def test_a_frozen_drone_does_not_move_or_log_you_then_carries_on():
    level, game, player = make_level(difficulty="medium")
    solve(level, player, FREEZE_FROM_STAGE)
    level.update(level.drone_grace + 0.1)
    level.handle_event(key(pygame.K_f))
    before_score = game.score.value
    position = level.drone.centre
    player.rect.center = level.drone.centre                     # standing right in its light
    frozen = FREEZE_SETTINGS["medium"]["seconds"]
    for _ in range(int((frozen - 0.2) * 60)):
        level.update(1 / 60)
        assert level.drone.centre == position and level.drone_hits == 0
    assert game.score.value == before_score
    for _ in range(60):
        level.update(1 / 60)
    assert level.freeze_left == 0
    level.drone.speed = 105.0
    for _ in range(60):
        level.update(1 / 60)
    assert level.drone.centre != position or level.drone_hits > 0     # it is on the move again


def test_freeze_cools_down_before_it_can_be_used_again():
    level, _, player = make_level(difficulty="medium")
    solve(level, player, FREEZE_FROM_STAGE)
    level.handle_event(key(pygame.K_f))
    level.update(FREEZE_SETTINGS["medium"]["seconds"] + 0.1)
    level.handle_event(key(pygame.K_f))
    assert level.freeze_left == 0 and "recharging" in level.message
    level.update(FREEZE_SETTINGS["medium"]["cooldown"])
    assert level.freeze_cooldown == 0
    level.handle_event(key(pygame.K_f))
    assert level.freeze_left > 0


def test_the_ability_bar_shows_every_state():
    level, _, player = make_level(difficulty="medium")
    states = lambda: {a["name"]: a["state"] for a in level._abilities()}   # noqa: E731
    assert states() == {"LURE": "ready", "FREEZE": "locked"}
    level.handle_event(key(pygame.K_x))
    assert states()["LURE"] == "cooling"
    solve(level, player, FREEZE_FROM_STAGE)
    assert states()["FREEZE"] == "ready"
    level.handle_event(key(pygame.K_f))
    assert states()["FREEZE"] == "active"
    level.update(FREEZE_SETTINGS["medium"]["seconds"] + 0.1)
    assert states()["FREEZE"] == "cooling"
    cool = next(a for a in level._abilities() if a["name"] == "FREEZE")
    assert 0 < cool["left"] <= cool["total"]


# --- the recap -----------------------------------------------------------------------------------------
def test_the_recap_lists_every_request_with_its_mistakes():
    level, _, player = make_level(seed=3)
    play_all(level, player, miss_stages=(1, 3))
    rows = level._recap_rows()
    assert len(rows) == REQUESTS
    assert "clean" in rows[0][0] and "1 miss" in rows[1][0] and "1 miss" in rows[3][0]
    for text, _ in rows:
        assert any(f"[{r['form']}]" in text for r in level.solved)
    notes = level._recap_notes()
    assert len(notes) == 2 and all(" - " in text for text, _ in notes)
    assert any("KEYS" in text for text, _ in notes) and any("LOOPS" in text for text, _ in notes)


def test_the_recap_counts_timeouts_and_flags_the_rush_slip():
    level, _, player = make_level(seed=3)
    level.time_left = 0.01
    level.update(0.05)
    play_all(level, player)
    rows = level._recap_rows()
    assert "1 timed out" in rows[0][0]
    assert sum("RUSH" in text for text, _ in rows) == 1 and "RUSH" in rows[level.rush_stage][0]


def test_a_clean_run_has_nothing_to_review():
    level, _, player = make_level(seed=3)
    play_all(level, player)
    assert level._recap_notes() == [] and all("clean" in t for t, _ in level._recap_rows())


def test_the_recap_panel_opens_when_the_last_request_is_filed_then_closes_and_r_reopens_it():
    level, _, player = make_level(seed=3)
    level.handle_event(key(pygame.K_r))
    assert level.recap_left == 0 and "recap" in level.message          # not yet
    play_all(level, player)
    assert level.recap_left == pytest.approx(RECAP_SECONDS, abs=0.5)
    level.update(RECAP_SECONDS + 0.5)
    assert level.recap_left == 0
    level.handle_event(key(pygame.K_r))
    assert level.recap_left > 0
    level.handle_event(key(pygame.K_r))
    assert level.recap_left == 0


# --- drawing never breaks ------------------------------------------------------------------------------
@pytest.mark.parametrize("difficulty", DIFFS)
def test_every_stage_renders_with_the_new_parts(difficulty):
    level, _, player = make_level(difficulty=difficulty, seed=6)
    surface = pygame.Surface((960, 640))
    for stage in range(REQUESTS):
        level.update(0.5)
        level.handle_event(key(pygame.K_q))
        level.render(surface)
        if stage >= FREEZE_FROM_STAGE:
            level.handle_event(key(pygame.K_f))
            level.update(0.2)
            level.render(surface)
        solve(level, player)
    level.update(0.3)
    level.render(surface)                                              # the recap panel is up
    level.handle_event(key(pygame.K_r))
    level.render(surface)


# --- the real game loop delivers the new keys ------------------------------------------------------------
def test_f_r_x_and_q_reach_floor_4_through_the_real_game_loop():
    from core.game import Game
    from tests.test_practice_mode import press

    game = Game()
    game.running = True
    press(game, pygame.K_RETURN)
    game.story_screen.done = True
    game._leave_story()
    game._end_briefing()
    game.level_manager.start("level4")
    level = game.level_manager.current
    assert type(level).__name__ == "ArchiveFloor" and game.state == "playing"

    def answer():
        level.player.rect.center = A.stand_zone(level.stage, level.request["answer"]).center
        press(game, pygame.K_e)
        level.update(level.read_hold)

    press(game, pygame.K_x)
    assert level.lure_cooldown > 0
    press(game, pygame.K_q)
    assert level.scan_flash > 0
    press(game, pygame.K_f)
    assert level.freeze_left == 0 and "unlocks" in level.message                 # locked at first
    answer()
    answer()
    press(game, pygame.K_f)
    assert level.freeze_left > 0
    answer()
    answer()
    assert level.stage == REQUESTS and level.recap_left > 0
    level.update(RECAP_SECONDS + 1)
    press(game, pygame.K_r)                                                      # R is also the "new run" key
    assert level.recap_left > 0 and game.state == "playing"                      # on the lose / win screens
