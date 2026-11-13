"""
tests/test_final_core.py

The finale, WARDEN's Core: every lock's right plate is proved by running its
Python, the rules keep the old Final Vault's numbers, every plate, the core and
the exit can be walked to, the searchlight costs score only, and a run through
the real game ends in the win state.
"""

import math
import os
import random
from collections import deque
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from levels import core_decor as C
from levels import core_requests as R
from levels.final_core import (
    BEAM_GRACE, BEAM_PENALTY, COMPLETION_BONUS, STAGE_POINTS, WRONG_PENALTY, WRONG_SECURITY, CoreVault)

pygame.init()


class Score:
    def __init__(self):
        self.value = 0

    def add(self, n):
        self.value += n

    def penalize(self, n):
        self.value -= n


class Security:
    def __init__(self):
        self.level = 0

    def increase(self, n):
        self.level += n


def make_core(hints=True, seed=1):
    game = SimpleNamespace(score=Score(), security=Security(), hints=SimpleNamespace(enabled=hints),
                           coop=False, player2=None)
    player = SimpleNamespace(rect=pygame.Rect(0, 0, 24, 28), moving=False)
    player.rect.topleft = C.SPAWNS[0]
    core = CoreVault(player=player, game=game, seed=seed)
    core.beam_grace = 999                          # rules tests: keep the searchlight out of the way
    return core, game, player


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


def press_plate(core, player, k, j=None):
    j = core.locks[k]["answer"] if j is None else j
    player.rect.center = C.plate_rect(k, j).center
    core.handle_event(key(pygame.K_e))


def solve_all(core, player):
    for k in range(R.LOCKS):
        press_plate(core, player, k)


# --- every lock is real Python ------------------------------------------------------------
def truth(lock):
    if lock["kind"] == "type":
        return eval(lock["code"]).__name__
    if lock["kind"] == "raise":
        with pytest.raises(Exception) as caught:
            exec(lock["code"], {})
        return type(caught.value).__name__
    scope = {"_print": lambda *a: None}
    exec(lock["code"], scope)
    value = scope["result"]
    return repr(value) if isinstance(value, str) else str(value)


@pytest.mark.parametrize("lock", range(6))
def test_each_locks_right_plate_is_what_python_gives(lock):
    rng = random.Random(lock)
    for _ in range(80):
        r = R.make_lock(lock, rng)
        assert r["labels"][r["answer"]] == truth(r)
        assert len(set(r["labels"])) == 3 and r["topic"] == R.TOPICS[lock]


def test_lock_code_fits_the_terminal():
    rng = random.Random(2)
    for _ in range(200):
        for k in range(6):
            r = R.make_lock(k, rng)
            assert len(r["lines"]) <= 5 and all(len(line) <= 42 for line in r["lines"])


# --- the rules ------------------------------------------------------------------------------
def test_locks_open_in_any_order_for_fifty_each():
    core, game, player = make_core()
    for k in (3, 0, 5, 1, 4, 2):
        press_plate(core, player, k)
    assert len(core.solved) == 6 and game.score.value == 6 * STAGE_POINTS and game.security.level == 0


def test_a_solved_lock_pays_once():
    core, game, player = make_core()
    press_plate(core, player, 2)
    press_plate(core, player, 2)
    assert game.score.value == STAGE_POINTS


def test_a_wrong_plate_is_ruled_out_and_costs_the_old_penalties():
    core, game, player = make_core()
    wrong = (core.locks[0]["answer"] + 1) % 3
    press_plate(core, player, 0, wrong)
    assert wrong in core.out[0] and 0 not in core.solved
    assert game.security.level == WRONG_SECURITY and game.score.value == -WRONG_PENALTY
    press_plate(core, player, 0, wrong)
    assert game.security.level == WRONG_SECURITY


def test_the_iris_opens_after_six_and_the_chip_pays_the_bonus_then_the_lift_opens():
    core, game, player = make_core()
    solve_all(core, player)
    player.rect.center = (C.CORE.centerx, C.CORE.bottom + 20)
    core.handle_event(key(pygame.K_e))
    assert not core.chip_taken                                  # the iris is still opening
    core.update(2.0)
    core.handle_event(key(pygame.K_e))
    assert core.chip_taken and game.score.value == 6 * STAGE_POINTS + COMPLETION_BONUS
    player.rect.center = C.EXIT_ZONE.center
    core.update(0.1)
    assert not core.is_complete()
    for _ in range(90):
        core.update(1 / 60)
    assert core.is_complete()


def test_hints_for_the_nearest_lock_and_off_when_hints_are():
    core, _, player = make_core()
    player.rect.center = C.plate_rect(4, 1).center
    core.handle_event(key(pygame.K_h))
    assert core.locks[4]["hint"] in core.message
    quiet, _, qp = make_core(hints=False)
    qp.rect.center = C.plate_rect(4, 1).center
    quiet.handle_event(key(pygame.K_h))
    assert "off" in quiet.message


def test_the_searchlight_costs_score_only_after_its_grace_and_speeds_up():
    core, game, player = make_core()
    core.beam_grace = BEAM_GRACE
    point = C.plate_rect(1, 1).center
    player.rect.center = point
    core.beam_angle = math.atan2(point[1] - C.CENTRE[1], point[0] - C.CENTRE[0])
    core._update_beam(0.0)
    assert core.beam_hits == 0                                   # grace
    core.beam_grace = 0.0
    core.beam_angle = math.atan2(point[1] - C.CENTRE[1], point[0] - C.CENTRE[0])
    core._update_beam(0.0)
    assert core.beam_hits == 1 and game.score.value == -BEAM_PENALTY and game.security.level == 0
    a0 = core.beam_angle
    core._update_beam(1.0)
    slow = (core.beam_angle - a0) % math.tau
    press_plate(core, player, 0)
    press_plate(core, player, 1)
    a1 = core.beam_angle
    core._update_beam(1.0)
    assert (core.beam_angle - a1) % math.tau > slow


def test_the_searchlight_stops_once_the_chip_is_taken():
    core, game, player = make_core()
    solve_all(core, player)
    core.update(2.0)
    player.rect.center = (C.CORE.centerx, C.CORE.bottom + 20)
    core.handle_event(key(pygame.K_e))
    a = core.beam_angle
    core.update(1.0)
    assert core.beam_angle == a


def test_render_draws_every_moment_and_changes_no_state():
    core, game, player = make_core()
    surface = pygame.Surface((960, 640))
    core.render(surface)
    press_plate(core, player, 0, (core.locks[0]["answer"] + 1) % 3)
    core.render(surface)
    solve_all(core, player)
    before = (len(core.solved), game.score.value, core.beam_angle, core.iris)
    core.render(surface)
    assert (len(core.solved), game.score.value, core.beam_angle, core.iris) == before
    core.update(2.0)
    core.render(surface)


# --- the room ------------------------------------------------------------------------------------
def reachable(core, start, goal):
    size = 16

    def free(c):
        r = pygame.Rect(0, 0, 24, 28)
        r.center = (c[0] * size + 8, c[1] * size + 8)
        return not core.room_map.blocked(r)

    s, g = (start[0] // size, start[1] // size), (goal[0] // size, goal[1] // size)
    seen, queue = {s}, deque([s])
    while queue:
        c = queue.popleft()
        if c == g:
            return True
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            n = (c[0] + dx, c[1] + dy)
            if n not in seen and 0 <= n[0] < 60 and 0 <= n[1] < 40 and free(n):
                seen.add(n)
                queue.append(n)
    return False


def test_every_plate_the_core_and_the_exit_can_be_walked_to():
    core, _, _ = make_core()
    start = pygame.Rect(C.SPAWNS[0], (24, 28)).center
    for k in range(6):
        for j in range(3):
            centre = C.plate_rect(k, j).center
            box = pygame.Rect(0, 0, 24, 28)
            box.center = centre
            assert not core.room_map.blocked(box), (k, j)
            assert reachable(core, start, centre), (k, j)
    assert reachable(core, start, (C.CORE.centerx, C.CORE.bottom + 20))
    core.door_block.size = (0, 0)
    assert reachable(core, start, C.EXIT_ZONE.center)


def test_the_room_is_round():
    rows = C.layout_rows()
    widths = [row.count(".") for row in rows[4:19]]
    top, middle = widths[0], widths[len(widths) // 2]
    assert middle > top * 2


def test_a_run_through_the_real_game_ends_in_the_win_state():
    from core.game import Game

    game = Game()
    try:
        game.story_enabled = False
        game.level_manager.start("final_vault")
        game._last_level_name = "level5"
        game.state = "playing"
        game.update(1 / 60)
        core = game.level_manager.current
        assert isinstance(core, CoreVault)
        core.beam_grace = 999
        for k in range(6):
            game.player.rect.center = C.plate_rect(k, core.locks[k]["answer"]).center
            core.handle_event(key(pygame.K_e))
        for _ in range(120):
            game.update(1 / 60)
        game.player.rect.center = (C.CORE.centerx, C.CORE.bottom + 20)
        core.handle_event(key(pygame.K_e))
        for _ in range(90):
            game.update(1 / 60)
        game.player.rect.center = C.EXIT_ZONE.center
        for _ in range(10):
            game.update(1 / 60)
        assert core.is_complete() and game.state in ("win", "outro")
    finally:
        game.music.stop()
