"""
tests/test_floor4_archive.py

Floor 4, the Records Archive: every request's right answer is checked by running
the Python on the slip, the rules (right, wrong, out of time, drone, finish) match
Floor 4's numbers, the room is walkable to every target and the exit, and the
game builds this floor unless the old Level 4 is asked for.
"""

import os
import random
from collections import deque
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from levels import archive_decor as A
from levels import archive_requests as R
from levels.floor4_archive import (
    DRONE_GRACE, DRONE_PENALTY, FINISH_BONUS, POINTS, TIMEOUT_PENALTY, TIMEOUT_SECURITY,
    WRONG_PENALTY, WRONG_SECURITY, ArchiveFloor)

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


def make_level(hints=True, difficulty="medium", seed=1):
    game = SimpleNamespace(score=Score(), security=Security(), hints=SimpleNamespace(enabled=hints),
                           difficulty=difficulty, coop=False, player2=None)
    player = SimpleNamespace(rect=pygame.Rect(0, 0, 24, 28), moving=False)
    player.rect.center = A.SPAWNS[0]
    level = ArchiveFloor(player=player, game=game, seed=seed)
    game.player = player
    return level, game, player


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


def stand_and_press(level, player, index):
    player.rect.center = A.stand_zone(level.stage, index).center
    level.handle_event(key(pygame.K_e))


# --- the slips are real Python ---------------------------------------------------------
@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_shelf_answer_is_what_python_returns(difficulty):
    rng = random.Random(5)
    for _ in range(60):
        r = R.shelf_request(rng, difficulty)
        shelf = r["names"]
        expr = r["lines"][-1][len("pull("):-1]
        assert eval(expr, {"shelf": shelf, "len": len}) == "ghost"
        assert shelf[r["answer"]] == "ghost"
        assert r["labels"][r["answer"]] == f"[{r['answer']}]"


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_catalogue_answer_is_the_key_python_looks_up(difficulty):
    rng = random.Random(7)
    for _ in range(80):
        r = R.catalogue_request(rng, difficulty)
        codes = r["codes"]
        last = r["lines"][-1]
        if last.startswith("# which key holds"):
            wanted = last.split("'")[1]
            key_used = next(k for k, v in codes.items() if v == wanted)
        else:
            looked = []
            scope = {"codes": codes, "open": looked.append}
            for line in r["lines"][2:]:
                exec(line, scope)
            value = looked[0]
            key_used = next(k for k, v in codes.items() if v == value)
        assert r["labels"][r["answer"]] == repr(key_used)
        assert r["take"] == codes[key_used]
        assert len(set(r["labels"])) == 4


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_vault_answer_is_the_item_python_feeds(difficulty):
    rng = random.Random(9)
    for _ in range(60):
        items = ["badge", "dossier", rng.choice(R.CODE_VALUES)]
        r = R.vault_request(rng, items, difficulty)
        fed = []
        scope = {"vault": SimpleNamespace(feed=fed.append)}
        for line in r["lines"]:
            exec(line, scope)
        assert fed and fed[0] == items[r["answer"]]


def test_slip_lines_fit_the_slip():
    rng = random.Random(3)
    for _ in range(200):
        for stage in range(3):
            r = R.make_request(stage, rng, ["badge", "dossier", "B-7"], "medium")
            assert len(r["lines"]) <= 4 and all(len(line) <= 44 for line in r["lines"])


# --- the rules -------------------------------------------------------------------------
def test_right_answers_file_three_requests_and_fill_the_satchel():
    level, game, player = make_level()
    assert level.satchel == ["badge"] and level.gates_passed == 0
    stand_and_press(level, player, level.request["answer"])
    assert level.stage == 1 and level.satchel == ["badge", "dossier"] and game.score.value == POINTS
    card = level.request["take"]
    stand_and_press(level, player, level.request["answer"])
    assert level.stage == 2 and level.satchel[-1] == card
    stand_and_press(level, player, level.request["answer"])
    assert level.stage == 3 and level.gates_passed == 3
    assert game.score.value == 3 * POINTS and game.security.level == 0


def test_a_wrong_answer_raises_security_and_keeps_the_same_request():
    level, game, player = make_level()
    request = level.request
    wrong = (request["answer"] + 1) % 5
    stand_and_press(level, player, wrong)
    assert level.stage == 0 and level.request is request
    assert game.security.level == WRONG_SECURITY and game.score.value == -WRONG_PENALTY
    assert (0, wrong) in level.wrong


def test_running_out_of_time_brings_a_new_slip():
    level, game, player = make_level()
    level.time_left = 0.01
    level.update(0.05)
    assert game.security.level == TIMEOUT_SECURITY and game.score.value == -TIMEOUT_PENALTY
    assert level.time_left == level.time_limit and level.stage == 0


def test_acting_on_another_stage_does_nothing():
    level, game, player = make_level()
    player.rect.center = A.stand_zone(1, 0).center
    level.handle_event(key(pygame.K_e))
    assert level.stage == 0 and game.security.level == 0 and "slip" in level.message


def test_the_drone_logs_you_for_score_only_and_not_during_its_grace():
    level, game, player = make_level()
    player.rect.center = level.drone.centre
    level.drone.speed = 0
    level.update(0.1)
    assert level.drone_hits == 0
    level.update(DRONE_GRACE)
    player.rect.center = level.drone.centre
    level.update(0.02)
    assert level.drone_hits == 1 and game.score.value == -DRONE_PENALTY and game.security.level == 0
    level.update(0.5)
    assert level.drone_hits == 1                                 # cooldown: once, not every frame


def test_the_lure_pulls_the_drone_away_and_it_logs_nobody_meanwhile():
    level, game, player = make_level()
    level.update(DRONE_GRACE + 0.1)
    level.handle_event(key(pygame.K_x))
    assert level.drone.lure is not None
    player.rect.center = level.drone.centre
    level.update(0.05)
    assert level.drone_hits == 0
    level.handle_event(key(pygame.K_x))
    assert "recharging" in level.message
    level.update(5.0)
    assert level.drone.lure is None


def test_scan_gives_the_hint_and_is_jammed_when_hints_are_off():
    level, _, _ = make_level()
    level.handle_event(key(pygame.K_q))
    assert level.request["hint"] in level.message
    quiet, _, _ = make_level(hints=False)
    quiet.handle_event(key(pygame.K_q))
    assert "jammed" in quiet.message


def test_the_vault_door_opens_after_the_last_request_and_the_bonus_is_paid_once():
    level, game, player = make_level()
    for _ in range(3):
        stand_and_press(level, player, level.request["answer"])
    player.rect.center = A.EXIT_ZONE.center
    level.update(0.1)
    assert not level.is_complete()                              # the reader is still scanning
    for _ in range(90):
        level.update(1 / 60)
    assert level.is_complete()
    assert game.score.value == 3 * POINTS + FINISH_BONUS
    level.update(1.0)
    assert game.score.value == 3 * POINTS + FINISH_BONUS


def test_second_player_answers_with_right_shift():
    level, game, player = make_level()
    p2 = SimpleNamespace(rect=pygame.Rect(0, 0, 24, 28), moving=False)
    game.coop, game.player2 = True, p2
    p2.rect.center = A.stand_zone(0, level.request["answer"]).center
    level.handle_event(key(pygame.K_RSHIFT))
    assert level.stage == 1


# --- the room ---------------------------------------------------------------------------
def reachable(level, start, goal):
    S = 16

    def free(c):
        r = pygame.Rect(0, 0, 24, 28)
        r.center = (c[0] * S + 8, c[1] * S + 8)
        return not level.room_map.blocked(r)

    s, g = (start[0] // S, start[1] // S), (goal[0] // S, goal[1] // S)
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


def test_every_target_and_the_exit_can_be_walked_to_from_the_spawn():
    level, _, _ = make_level()
    for stage, count in ((0, 5), (1, 4), (2, 3)):
        for i in range(count):
            assert reachable(level, A.SPAWNS[0], A.stand_zone(stage, i).center), (stage, i)
    level.door_block.size = (0, 0)
    assert reachable(level, A.SPAWNS[0], A.EXIT_ZONE.center)


def test_spawns_are_clear_and_the_exit_is_shut_at_first():
    level, _, _ = make_level()
    for x, y in A.SPAWNS:
        assert not level.room_map.blocked(pygame.Rect(x, y, 24, 28))
    assert level.room_map.blocked(A.DOOR.inflate(-8, -8))


def test_render_draws_every_stage_and_changes_no_state():
    level, game, player = make_level()
    surface = pygame.Surface((960, 640))
    for _ in range(4):
        before = (level.stage, level.time_left, level.drone.x, game.score.value, list(level.satchel))
        level.render(surface)
        assert (level.stage, level.time_left, level.drone.x, game.score.value, list(level.satchel)) == before
        if level.stage < 3:
            stand_and_press(level, player, level.request["answer"])


def test_the_game_builds_the_archive_unless_the_old_level_is_asked_for(monkeypatch):
    from core.game import Game
    from levels.level4_memory import Level4MemoryVault

    game = Game()
    assert isinstance(game.level_manager.levels["level4"], ArchiveFloor)
    monkeypatch.setenv("MEMORY_HEIST_OLD_LEVEL4", "1")
    game._register_levels()
    assert isinstance(game.level_manager.levels["level4"], Level4MemoryVault)


def test_the_lure_keeps_the_drone_in_its_aisle_not_over_the_stacks():
    level, _, _ = make_level()
    level.handle_event(key(pygame.K_x))
    for _ in range(120):
        level.update(1 / 60)
        r = pygame.Rect(0, 0, 16, 12)
        r.center = level.drone.centre
        assert not any(r.colliderect(s) for s in A.STACKS)
    assert abs(level.drone.y - A.DRONE_Y) < 2


def test_a_new_slip_drops_out_of_the_tube():
    level, _, player = make_level()
    level.update(1.0)
    assert level.slip_drop == 1.0
    stand_and_press(level, player, level.request["answer"])
    assert level.slip_drop == 0.0
    level.update(0.2)
    assert 0.0 < level.slip_drop < 1.0


def test_the_last_seconds_tick_once_each():
    level, _, _ = make_level()
    played = []
    level.sfx = played.append
    level.time_left = 5.5
    for _ in range(100):                                  # 5.5 s down to about 3.8 s
        level.update(1 / 60)
    assert played.count("click") == 2                     # 5 and 4, once each
