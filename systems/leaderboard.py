"""
systems/leaderboard.py
Owner: Member 1 - Core Game System (UI by Member 5)

Local top-scores table stored as JSON in saves/leaderboard.json.
"""

import json
import os
from datetime import date

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(ROOT, "saves", "leaderboard.json")

MAX_ENTRIES = 10
MAX_NAME_LENGTH = 12


class Leaderboard:
    def __init__(self, path=DEFAULT_PATH):
        self.path = path
        self.entries = self._load()

    def _load(self):
        """Read saved entries; a missing or damaged file gives an empty table."""
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return []

        if not isinstance(data, list):
            return []

        entries = []
        for item in data:
            if (
                isinstance(item, dict)
                and isinstance(item.get("name"), str)
                and isinstance(item.get("score"), int)
            ):
                entries.append(item)
        return self._sorted(entries)

    @staticmethod
    def _sorted(entries):
        return sorted(entries, key=lambda e: e["score"], reverse=True)[:MAX_ENTRIES]

    def _save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.entries, f, indent=2)
        except OSError:
            # Saving is best-effort; the game keeps running without it.
            pass

    def add(self, name, score, difficulty="Medium", coop=False):
        """Add a score and return its 1-based rank (None if it did not place)."""
        name = (name or "").strip()[:MAX_NAME_LENGTH] or "PLAYER"
        entry = {
            "name": name,
            "score": int(score),
            "difficulty": difficulty,
            "coop": bool(coop),
            "date": date.today().isoformat(),
        }
        self.entries.append(entry)
        self.entries = self._sorted(self.entries)
        self._save()

        for index, item in enumerate(self.entries):
            if item is entry:
                return index + 1
        return None

    def top(self, count=5):
        return self.entries[:count]
