"""Floor 3: each room runs the loop on its LOOP LOGIC board, and the door asks about it. Headless."""

import os
import random
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from levels import laser_requests as LR
from levels.patrol_requests import _fmt
import test_level3_room3_core as C

pygame.init()
DIFFS = ("easy", "medium", "hard")


@pytest.fixture(autouse=True)
def generated_questions(monkeypatch):
    """The generated questions are behind a switch (the fixed bank is the default); these tests use them."""
    monkeypatch.setenv("MEMORY_HEIST_GENERATED_LEVEL3", "1")
    monkeypatch.delenv("MEMORY_HEIST_OLD_LEVEL3", raising=False)


def every_request(room, difficulty, seeds=200):
    return [LR.make_request(room, difficulty, random.Random(seed)) for seed in range(seeds)]


# ---- the generator ----------------------------------------------------------------------

@pytest.mark.parametrize("room", (1, 2, 3))
@pytest.mark.parametrize("difficulty", DIFFS)
def test_every_request_has_one_right_answer_among_four(room, difficulty):
    for req in every_request(room, difficulty):
        assert len(req["options"]) == 4 and len(set(req["options"])) == 4
        assert req["answer"] in req["options"]
        assert req["question"] and req["hint"] and req["explanation"]
        assert req["points"] == LR.POINTS[difficulty]


@pytest.mark.parametrize("room", (1, 3))
@pytest.mark.parametrize("difficulty", DIFFS)
def test_answer_comes_from_running_the_board_code(room, difficulty):
    for req in every_request(room, difficulty):
        fired, _ = LR.run(req["code"])
        assert fired == req["fires"]
        expected = _fmt(sorted(fired)) if room == 1 else str(len(fired))
        assert req["answer"] == expected, req["code"]


@pytest.mark.parametrize("difficulty", DIFFS)
def test_room1_lights_at_least_one_real_pad_and_room3_vents_after_one_or_two_pulses(difficulty):
    for req in every_request(1, difficulty):
        assert req["fires"] and all(0 <= pad < LR.PADS for pad in req["fires"])
    for req in every_request(3, difficulty):
        assert 1 <= len(req["fires"]) <= 2          # a pulse cycle is ~9 s; the room clock is ~20 s


@pytest.mark.parametrize("room", (1, 2, 3))
def test_board_code_fits_the_header(room):
    pygame.font.init()
    level, _ = C.make3()
    for difficulty in DIFFS:
        for req in every_request(room, difficulty, 60):
            assert len(req["code"]) <= LR.MAX_LINES
            level.room_requests[level.current_room_number()] = req
            board = level._loop_board()
            assert board["panel"].right <= 900 and board["panel"].height == 44
            assert board["lane"].width >= 420           # the objective still fits on two lines
            objective = level.ROOM_OBJECTIVES[room].replace(". ", "  ·  ")
            lines = level._wrap_text(level._font(20), objective, board["lane"].width - 12, 2)
            assert not lines[-1].endswith("..."), (room, lines)


# ---- the rooms do what the board says ----------------------------------------------------

def at_room(room, difficulty="medium"):
    level, game = C.make3(difficulty)
    level.current_checkpoint = room
    level.room = level.room_map.current
    level.barrier_walls = level.room.walls
    level.current_question_number = room - 1
    level.setup_room_hazards()
    level.load_current_question()
    return level, game


def test_door_questions_are_the_rooms_board_requests():
    level, _ = C.make3()
    for room in (1, 2, 3):
        assert level.selected_questions[room - 1] is level.room_requests[room]


def test_room1_only_lit_pads_shield():
    level, _ = at_room(1)
    level.lit_pads = {0, 2}
    for index, pad in enumerate(level.safe_zones):
        player = pygame.Rect(0, 0, 32, 32)
        player.center = pad.center
        assert level.player_in_safe_pocket(player) is (index in (0, 2))


def test_room1_lit_pads_follow_the_board():
    for seed in range(20):
        random.seed(seed)
        level, _ = at_room(1)
        assert level.lit_pads == set(level.room_requests[1]["fires"])


def test_room2_cameras_follow_the_board():
    level, _ = at_room(2)
    assert level.camera_bank.active == set(level.room_requests[2]["fires"])


@pytest.mark.parametrize("pulses", (1, 2))
def test_room3_core_vents_after_the_boards_pulses(pulses):
    level, game = at_room(3)
    level.core_vent_after = pulses
    C.go_near_core(level, game)
    for pulse in range(pulses):
        C.to_state(level, "pulse")
        if pulse < pulses - 1:
            C.to_state(level, "recovery")
            assert level.core_state == "recovery"
    C.to_state(level, "offline")
    assert level.core_timer > 0 and level.core_pulse_count == 0


def test_the_old_question_bank_is_the_default(monkeypatch):
    monkeypatch.delenv("MEMORY_HEIST_GENERATED_LEVEL3", raising=False)
    monkeypatch.delenv("MEMORY_HEIST_OLD_LEVEL3", raising=False)
    level, _ = C.make3()
    assert level.room_requests == {}
    assert all(q["id"].startswith("level3_loop_") for q in level.selected_questions)
    assert level.lit_pads is None and level.core_vent_after is None       # the plain rooms
    assert level._loop_board()["code"] == level.code_lines                # the original board code


def test_the_generated_questions_are_one_switch_away(monkeypatch):
    monkeypatch.setenv("MEMORY_HEIST_GENERATED_LEVEL3", "1")
    monkeypatch.delenv("MEMORY_HEIST_OLD_LEVEL3", raising=False)
    level, _ = C.make3()
    assert set(level.room_requests) == {1, 2, 3}
    assert level.core_vent_after is not None                              # room 3 follows its board
    assert level._loop_board()["code"] == level.room_requests[3]["code"]


def test_the_old_switch_still_wins_over_the_generated_one(monkeypatch):
    monkeypatch.setenv("MEMORY_HEIST_GENERATED_LEVEL3", "1")
    monkeypatch.setenv("MEMORY_HEIST_OLD_LEVEL3", "1")
    level, _ = C.make3()
    assert level.room_requests == {}
