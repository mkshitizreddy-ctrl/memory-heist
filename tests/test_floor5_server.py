"""
tests/test_floor5_server.py

Floor 5, WARDEN's Server Hall: each job's right answer is proved by running real
Python (the call, the return, the error raised), the rules keep Floor 5's numbers,
the room is walkable to every port, bay, breaker, the console and the exit, and a
run through the real game reaches the Final Vault.
"""

import os
import random
from collections import deque
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from levels import server_decor as S
from levels import server_requests as R
from levels.floor5_server import JOBS, VENT_PENALTY, ServerFloor
from levels.level5_control import (
    POINTS_COMPLETION_BONUS, POINTS_PER_QUESTION, POINTS_TERMINAL, WRONG_SCORE_PENALTY, WRONG_SECURITY)

pygame.init()


class Score:
    def __init__(self):
        self.value = 0

    def add(self, n):
        self.value += n

    def penalize(self, n):
        self.value -= n

    def get_score(self):
        return self.value


class Security:
    def __init__(self):
        self.level = 0

    def increase(self, n):
        self.level += n


def make_floor(hints=True, difficulty="medium", seed=1):
    game = SimpleNamespace(score=Score(), security=Security(), hints=SimpleNamespace(enabled=hints),
                           difficulty=difficulty, coop=False, player2=None, settings={})
    player = SimpleNamespace(rect=pygame.Rect(0, 0, 24, 28), moving=False)
    player.rect.topleft = S.SPAWNS[0]
    floor = ServerFloor(player=player, game=game, seed=seed)
    return floor, game, player


def key(k, u=""):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode=u)


def do_job(floor, player, index=None):
    index = floor.request["answer"] if index is None else index
    player.rect.center = S.stand_zone(floor.stage, index).center
    floor.handle_event(key(pygame.K_e))


# --- the tickets are real Python -------------------------------------------------------
@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_argument_answer_is_the_value_python_binds(difficulty):
    rng = random.Random(4)
    for _ in range(80):
        r = R.argument_request(rng, difficulty)
        scope = {}
        exec(r["code"], scope)
        assert r["labels"][r["answer"]] == str(scope["result"])


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_return_answer_is_what_python_returns(difficulty):
    rng = random.Random(6)
    for _ in range(80):
        r = R.return_request(rng, difficulty)
        scope = {"_print": lambda *a: None}
        exec(r["code"], scope)
        assert r["labels"][r["answer"]] == repr(scope["result"])
        assert len(set(r["labels"])) == 4


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_exception_answer_is_the_error_python_raises(difficulty):
    rng = random.Random(8)
    for _ in range(80):
        r = R.exception_request(rng, difficulty)
        with pytest.raises(Exception) as caught:
            exec(r["code"], {})
        assert type(caught.value).__name__ == r["labels"][r["answer"]]


def test_tickets_and_machine_faces_fit():
    rng = random.Random(1)
    for _ in range(200):
        for stage in range(3):
            r = R.make_request(stage, rng)
            assert len(r["lines"]) <= 5 and all(len(line) <= 44 for line in r["lines"])
            assert len(r["machine"]) <= 4 and all(len(line) <= 30 for line in r["machine"])


# --- the rules -------------------------------------------------------------------------
def test_three_right_jobs_unlock_the_console_with_floor_5_points():
    floor, game, player = make_floor()
    for stage in range(JOBS):
        assert floor.stage == stage
        do_job(floor, player)
    assert floor.phase == "terminal" and game.score.value == JOBS * POINTS_PER_QUESTION
    assert game.security.level == 0 and floor.gates_passed == JOBS


def test_a_wrong_choice_is_ruled_out_and_costs_floor_5_penalties():
    floor, game, player = make_floor()
    wrong = (floor.request["answer"] + 1) % 4
    do_job(floor, player, wrong)
    assert wrong in floor.out and floor.stage == 0
    assert game.security.level == WRONG_SECURITY and game.score.value == -WRONG_SCORE_PENALTY
    do_job(floor, player, wrong)                                   # ruled out: no second penalty
    assert game.security.level == WRONG_SECURITY


def test_a_hint_costs_points_on_that_job_and_is_off_on_hard():
    floor, game, player = make_floor()
    floor.handle_event(key(pygame.K_h))
    assert floor.request["hint"] in floor.hint_text
    do_job(floor, player)
    assert game.score.value == POINTS_PER_QUESTION - floor.hint_penalty()
    hard, _, _ = make_floor(hints=False, difficulty="hard")
    hard.handle_event(key(pygame.K_h))
    assert not hard.hint_text


def test_the_reactor_trips_if_left_too_long():
    floor, game, player = make_floor()
    do_job(floor, player)
    do_job(floor, player)
    assert floor.stage == 2
    floor.update(floor.heat_seconds * 0.5)
    assert 0.4 < floor.heat < 0.6 and game.security.level == 0
    floor.update(floor.heat_seconds * 0.6)
    assert game.security.level == WRONG_SECURITY and floor.heat < 0.2 and floor.stage == 2


def test_the_console_runs_the_real_try_except_and_opens_the_vault_door():
    floor, game, player = make_floor()
    for _ in range(JOBS):
        do_job(floor, player)
    player.rect.center = (S.CONSOLE.centerx, S.CONSOLE.y - 20)
    floor.handle_event(key(pygame.K_e))
    assert floor.at_terminal and floor.movement_locked
    floor.handle_event(key(pygame.K_3, "3"))
    floor.handle_event(key(pygame.K_RETURN))
    assert "Caught" in floor.command_result and floor.phase == "terminal"
    floor.handle_event(key(pygame.K_a, "a"))
    floor.handle_event(key(pygame.K_RETURN))
    assert "Caught" in floor.command_result
    before = game.score.value
    floor.handle_event(key(pygame.K_9, "9"))
    floor.handle_event(key(pygame.K_RETURN))
    assert floor.phase == "done" and not floor.at_terminal and not floor.is_complete()
    assert game.score.value == before + POINTS_TERMINAL + POINTS_COMPLETION_BONUS
    player.rect.center = S.EXIT_ZONE.center
    floor.update(0.1)
    assert not floor.is_complete()                                  # the door is still scanning
    for _ in range(90):
        floor.update(1 / 60)
    assert floor.is_complete()


def test_arrow_keys_step_away_from_the_console():
    floor, _, player = make_floor()
    for _ in range(JOBS):
        do_job(floor, player)
    player.rect.center = (S.CONSOLE.centerx, S.CONSOLE.y - 20)
    floor.handle_event(key(pygame.K_e))
    floor.handle_event(key(pygame.K_LEFT))
    assert not floor.at_terminal


def test_a_vent_scalds_for_score_only_and_only_while_it_blows():
    floor, game, player = make_floor()
    player.rect.center = S.plume_rect(0).center
    floor.time = 0.0
    while S.vent_state(0, floor.time) != "warn":
        floor.time += 0.05
    floor.update(0.0)
    assert floor.vent_hits == 0
    while S.vent_state(0, floor.time) != "blow":
        floor.time += 0.05
    floor.update(0.0)
    assert floor.vent_hits == 1 and game.score.value == -VENT_PENALTY and game.security.level == 0


def test_render_draws_every_phase_and_changes_no_state():
    floor, game, player = make_floor()
    surface = pygame.Surface((960, 640))
    for _ in range(JOBS + 1):
        before = (floor.stage, floor.phase, game.score.value, floor.heat)
        floor.render(surface)
        assert (floor.stage, floor.phase, game.score.value, floor.heat) == before
        if floor.phase == "questions":
            do_job(floor, player)
    player.rect.center = (S.CONSOLE.centerx, S.CONSOLE.y - 20)
    floor.handle_event(key(pygame.K_e))
    floor.render(surface)


# --- the room ---------------------------------------------------------------------------
def reachable(floor, start, goal):
    size = 16

    def free(c):
        r = pygame.Rect(0, 0, 24, 28)
        r.center = (c[0] * size + 8, c[1] * size + 8)
        return not floor.room_map.blocked(r)

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


def test_every_port_bay_breaker_the_console_and_the_exit_can_be_reached():
    floor, _, _ = make_floor()
    start = pygame.Rect(S.SPAWNS[0], (24, 28)).center
    for stage in range(3):
        for i in range(4):
            assert reachable(floor, start, S.stand_zone(stage, i).center), (stage, i)
    assert reachable(floor, start, (S.CONSOLE.centerx, S.CONSOLE.y - 18))
    floor.door_block.size = (0, 0)
    assert reachable(floor, start, S.EXIT_ZONE.center)


def test_the_vents_can_be_avoided_by_the_upper_aisle():
    floor, _, _ = make_floor()
    for i in range(len(S.VENTS)):
        floor.room_map.props.append(S.plume_rect(i))
    start = pygame.Rect(S.SPAWNS[0], (24, 28)).center
    assert reachable(floor, start, (S.CONSOLE.centerx, S.CONSOLE.y - 18))


def test_a_run_through_the_real_game_reaches_the_final_vault():
    from core.game import Game

    game = Game()
    try:
        game.story_enabled = False
        game.level_manager.start("level5")
        game._last_level_name = "level4"
        game.state = "playing"
        game.update(1 / 60)
        floor = game.level_manager.current
        assert isinstance(floor, ServerFloor)
        assert game.player.rect.topleft == S.SPAWNS[0]
        for _ in range(JOBS):
            game.player.rect.center = S.stand_zone(floor.stage, floor.request["answer"]).center
            floor.handle_event(key(pygame.K_e))
        game.player.rect.center = (S.CONSOLE.centerx, S.CONSOLE.y - 20)
        floor.handle_event(key(pygame.K_e))
        floor.handle_event(key(pygame.K_7, "7"))
        floor.handle_event(key(pygame.K_RETURN))
        for _ in range(120):
            game.update(1 / 60)
        game.player.rect.center = S.EXIT_ZONE.center
        game.update(1 / 60)
        assert game.level_manager.current_name == "final_vault"
    finally:
        game.music.stop()


def test_the_reactor_warns_once_before_it_trips():
    floor, game, player = make_floor()
    do_job(floor, player)
    do_job(floor, player)
    played = []
    floor.sfx = played.append
    floor.update(floor.heat_seconds * 0.7)
    assert "alarm" not in played
    floor.update(floor.heat_seconds * 0.1)
    assert played.count("alarm") == 1 and "OVERHEATING" in floor.message
    floor.update(floor.heat_seconds * 0.1)
    assert played.count("alarm") == 1 and game.security.level == 0


def test_the_wall_screens_sit_below_the_message_line():
    from levels.room_base import MESSAGE_Y
    for rect in (S.TICKET, S.EYE_SCREEN, S.GAUGES):
        assert rect.y >= MESSAGE_Y + 22 and rect.bottom <= 6 * 32
