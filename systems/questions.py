"""Question pool loader and randomizer. Shared by every level's gates."""
import json
import os
import random

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data", "questions")


class QuestionBank:
    """Loads a level's question pool and hands out random, non-repeating questions."""

    def __init__(self, level_key, difficulty="medium"):
        """Load data/questions/<level_key>.json and set the active difficulty."""
        self.level_key = level_key
        self.difficulty = difficulty
        self.all_questions = self._load(level_key)
        self._used_ids = set()

    def _load(self, level_key):
        """Read the question list for this level, or return a tiny fallback set."""
        path = os.path.join(DATA_DIR, f"{level_key}.json")
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return [{
                "id": f"{level_key}_fallback",
                "question": "Fallback question - questions file not found.",
                "options": ["A", "B"], "answer": "A",
                "difficulty": "easy", "hint": "Pick A.", "points": 50,
            }]

    def set_difficulty(self, difficulty):
        """Change the active difficulty filter."""
        self.difficulty = difficulty

    def _pool(self):
        """Return unused questions matching the active difficulty, or any unused question."""
        matching = [q for q in self.all_questions
                    if q["difficulty"] == self.difficulty and q["id"] not in self._used_ids]
        if matching:
            return matching
        return [q for q in self.all_questions if q["id"] not in self._used_ids]

    def next_question(self):
        """Return a random not-yet-used question, resetting the used list once exhausted."""
        pool = self._pool()
        if not pool:
            self._used_ids.clear()
            pool = self._pool()
        question = random.choice(pool)
        self._used_ids.add(question["id"])
        return question

    def reset(self):
        """Clear used-question tracking, e.g. when the player restarts the level."""
        self._used_ids.clear()
