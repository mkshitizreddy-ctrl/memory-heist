"""
systems/hints.py
Owner: Member 5

Hint lookup keyed by puzzle id, loaded from data/puzzles.json.
Using a hint should call ScoreTracker.penalize() from scoring.py.

`enabled` is switched by the selected difficulty (off on Hard).
"""

import json
from pathlib import Path

# Resolved relative to the repo, not the current working directory.
DEFAULT_PUZZLES_PATH = Path(__file__).resolve().parent.parent / "data" / "puzzles.json"


class HintSystem:
    def __init__(self, puzzles_path=DEFAULT_PUZZLES_PATH):
        self.enabled = True
        with open(puzzles_path, "r", encoding="utf-8") as f:
            self.puzzles = json.load(f)

    def get_hint(self, puzzle_id):
        puzzle = self.puzzles.get(puzzle_id, {})
        return puzzle.get("hint", "No hint available.")
