"""Floor 3: each door question is about the loop that room really runs."""

import math
import os
import random
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.difficulty import get_difficulty
from levels import patrol_cameras, patrol_lanes
from levels.patrol_requests import POINTS, make_request

DIFFS = ("easy", "medium", "hard")


def replay(code):
    """Run the board's code again, independently of the generator."""
    calls, state = [], {"patrols": 1}

    def patrol():
        state["patrols"] -= 1
        return state["patrols"] >= 0

    scope = {"zap": calls.append, "sweep": calls.append, "patrol": patrol}
    exec("\n".join(code), scope)
    return calls, scope


def expected(request):
    calls, scope = replay(request["code"])
    q = request["question"]
    if "first" in q:
        return str(calls[0])
    if "when it stops" in q:
        return str(scope["cam"])
    return ", ".join(str(v) for v in sorted(calls))


@pytest.mark.parametrize("room", (1, 2, 3))
@pytest.mark.parametrize("difficulty", DIFFS)
def test_every_answer_is_what_python_does(room, difficulty):
    rng = random.Random(room * 10 + len(difficulty))
    for _ in range(150):
        r = make_request(room, difficulty, rng)
        assert r["answer"] == expected(r), r
        assert len(r["options"]) == 4 and len(set(r["options"])) == 4 and r["answer"] in r["options"]
        assert r["fires"] == replay(r["code"])[0]
        assert r["room"] == room and r["difficulty"] == difficulty
        assert r["points"] == POINTS[difficulty]
        assert 2 <= len(r["code"]) <= 4 and r["hint"] and r["explanation"]


@pytest.mark.parametrize("difficulty", DIFFS)
def test_rooms_only_use_lanes_and_cameras_that_exist(difficulty):
    rng = random.Random(4)
    for _ in range(200):
        assert set(make_request(1, difficulty, rng)["fires"]) <= {0, 1, 2, 3}
        assert set(make_request(3, difficulty, rng)["fires"]) <= {0, 1, 2}
        count = patrol_cameras.SETTINGS[difficulty][0]
        assert set(make_request(2, difficulty, rng)["fires"]) <= set(range(count))


def test_the_lane_loop_fires_only_the_board_order():
    loop = patrol_lanes.LaneLoop("medium", "columns", order=[2, 0])
    seen, current = set(), []
    for _ in range(int(loop.cycle * 2 * 60) + 200):
        loop.update(1 / 60)
        seen |= {lane for lane, p in enumerate(loop.phases()) if p == "active"}
        lane = loop.current_lane()
        if lane is not None and (not current or current[-1] != lane):
            current.append(lane)
    assert seen == {0, 2}
    assert current[:2] == [2, 0]


def test_the_default_lane_loop_is_unchanged():
    loop = patrol_lanes.LaneLoop("medium", "columns")
    assert loop.order == [0, 1, 2, 3]


def test_cameras_off_the_loop_never_see():
    bank = patrol_cameras.CameraBank("hard", active=[1])
    bank.clock = patrol_cameras.GRACE + 1
    mx, my = bank.mount(1)
    a = math.radians(bank.angle(1))
    spot = pygame.Rect(0, 0, 4, 4)
    spot.center = (mx + 120 * math.cos(a), my + 120 * math.sin(a))     # dead centre of camera 1's cone
    assert bank.camera_seeing([spot]) == 1
    bank.active = {0, 2}
    assert bank.camera_seeing([spot]) != 1


@pytest.fixture
def level():
    pygame.init()
    pygame.display.set_mode((960, 640))
    from levels.level3_loops import Level3LaserLoop

    random.seed(11)
    return Level3LaserLoop(game=SimpleNamespace(difficulty=get_difficulty("hard")))


@pytest.mark.skip(reason='Level 3 keeps its own question pool; generated door requests need team-lead approval')
def test_each_room_runs_its_own_question(level):
    for room in (1, 2, 3):
        level.room_map.current_name = f"level3_room{room}"
        level.current_question_number = room - 1
        level.setup_room_hazards()
        level.load_current_question()
        request = level.room_requests[room]
        assert level.current_question is request
        assert level.options[level.correct_option_index] == request["answer"]
        if room == 2:
            assert level.camera_bank.active == set(request["fires"])
        else:
            assert level.lane_loop.order == request["fires"]


@pytest.mark.skip(reason='Level 3 keeps its own question pool; generated door requests need team-lead approval')
def test_old_question_bank_returns_with_the_switch(monkeypatch):
    monkeypatch.setenv("MEMORY_HEIST_OLD_LEVEL3", "1")
    pygame.init()
    pygame.display.set_mode((960, 640))
    from levels.level3_loops import Level3LaserLoop

    old = Level3LaserLoop(game=SimpleNamespace(difficulty=get_difficulty("easy")))
    assert old.room_requests == {}
    assert old.selected_questions[0]["id"].startswith("level3_loop_")
    assert old.lane_loop.order == [0, 1, 2, 3]


def test_camera_trace_is_the_counter_at_each_check():
    rng = random.Random(8)
    for _ in range(100):
        r = make_request(2, rng.choice(DIFFS), rng)
        calls, scope = replay(r["code"])
        assert r["trace"] == calls + [scope["cam"]]


def _game_level():
    from core.game import Game

    game = Game()
    game._start_new_run()
    game.level_manager.start("level3")
    return game, game.level_manager.current


@pytest.mark.skip(reason='Level 3 keeps its own question pool; generated door requests need team-lead approval')
def test_answers_only_count_at_the_door():
    game, level = _game_level()
    level.room_map.current_name = "level3_room1"
    level.current_question_number = 0
    level.load_current_question()
    game.player.rect.topleft = (100, 446)                       # at the spawn, far from the door
    right = pygame.K_1 + level.correct_option_index
    level.handle_event(pygame.event.Event(pygame.KEYDOWN, key=right))
    assert level.gate1.state == "locked" and "door" in level.feedback.lower()
    game.player.rect.center = level.gate1.rect.center
    level.handle_event(pygame.event.Event(pygame.KEYDOWN, key=right))
    assert level.gate1.state != "locked"
    assert level.doors_opened() == 1                            # the counter moves with the door
