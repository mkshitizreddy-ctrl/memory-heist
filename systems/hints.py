"""
systems/hints.py
Owner: Member 5

Hint lookup keyed by puzzle id, loaded from data/puzzles.json.
Using a hint should call ScoreTracker.penalize() from scoring.py.
"""

import json


class HintSystem:
    def __init__(self, puzzles_path="data/puzzles.json"):
        with open(puzzles_path, "r") as f:
            self.puzzles = json.load(f)

    def get_hint(self, puzzle_id):
        puzzle = self.puzzles.get(puzzle_id, {})
        return puzzle.get("hint", "No hint available.")
