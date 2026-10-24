"""
tests/test_level3_variety.py

Guards Level 3 question variety: every room/difficulty cell keeps at
least two questions, and replaying the level really draws different
questions from that pool (selection stays inside the selected
difficulty and the current room).
"""

import json
import os
import random
from collections import defaultdict
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.difficulty import DIFFICULTIES, get_difficulty
from levels.level3_loops import Level3LaserLoop

PUZZLES_PATH = Path(__file__).resolve().parent.parent / "data" / "puzzles.json"


def test_each_room_and_difficulty_has_at_least_two_questions():
    with open(PUZZLES_PATH, "r", encoding="utf-8") as file:
        puzzles = json.load(file)

    counts = defaultdict(int)
    for key, entry in puzzles.items():
        if key.startswith("level3_loop_"):
            counts[(entry["room"], entry["difficulty"])] += 1

    for room in (1, 2, 3):
        for difficulty in DIFFICULTIES:
            assert counts[(room, difficulty)] >= 2, (
                f"Room {room} / {difficulty} has only "
                f"{counts[(room, difficulty)]} question(s)"
            )


@pytest.mark.parametrize("key", list(DIFFICULTIES))
def test_replaying_level3_draws_different_questions(key):
    pygame.font.init()
    random.seed(7)

    drawn = {1: set(), 2: set(), 3: set()}

    for _ in range(60):
        level = Level3LaserLoop(
            game=SimpleNamespace(difficulty=get_difficulty(key))
        )

        for room in (1, 2, 3):
            level.room_map.current_name = f"level3_room{room}"
            level.current_question_number = room - 1
            level.load_current_question()

            question = level.current_question
            assert question["room"] == room
            assert question["difficulty"] == key
            assert level.current_difficulty == key

            drawn[room].add(question["id"])

    for room in (1, 2, 3):
        assert len(drawn[room]) >= 2, (
            f"Room {room} / {key} always drew the same question"
        )