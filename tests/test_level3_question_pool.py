"""
tests/test_level3_question_pool.py

Guards the Level 3 question pool in data/puzzles.json: every room must
have at least one question for every difficulty, so the player's
selected difficulty never needs the "fall back to the whole room pool"
path, and the drawn question always matches the selection.
"""

import json
import os
import random
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.difficulty import DIFFICULTIES, get_difficulty
from levels.level3_loops import Level3LaserLoop

PUZZLES_PATH = Path(__file__).resolve().parent.parent / "data" / "puzzles.json"
POINTS = {"easy": 40, "medium": 50, "hard": 60}


def level3_entries():
    with open(PUZZLES_PATH, "r", encoding="utf-8") as file:
        puzzles = json.load(file)
    return {
        key: entry
        for key, entry in puzzles.items()
        if key.startswith("level3_loop_")
    }


def test_every_room_has_every_difficulty():
    entries = level3_entries().values()

    for room in (1, 2, 3):
        for difficulty in DIFFICULTIES:
            matching = [
                e for e in entries
                if e["room"] == room and e["difficulty"] == difficulty
            ]
            assert matching, f"Room {room} has no {difficulty} question"


def test_level3_entries_follow_conventions():
    for key, entry in level3_entries().items():
        assert entry["id"] == key
        assert entry["room"] in (1, 2, 3)
        assert entry["difficulty"] in DIFFICULTIES
        assert len(entry["options"]) == 4
        assert len(set(entry["options"])) == 4
        assert entry["answer"] in entry["options"]
        assert entry["points"] == POINTS[entry["difficulty"]]


@pytest.mark.parametrize("key", list(DIFFICULTIES))
def test_drawn_questions_match_selected_difficulty(key):
    pygame.font.init()

    for seed in range(25):
        random.seed(seed)
        level = Level3LaserLoop(
            game=SimpleNamespace(difficulty=get_difficulty(key))
        )

        for room in (1, 2, 3):
            level.room_map.current_name = f"level3_room{room}"
            level.current_question_number = room - 1
            level.load_current_question()

            assert level.current_question["room"] == room
            assert level.current_question["difficulty"] == key
            assert level.current_difficulty == key