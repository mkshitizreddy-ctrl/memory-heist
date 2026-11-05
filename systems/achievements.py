"""
systems/achievements.py

Lifetime stats and badges, kept in saves/stats.json (override the path with the
MEMORY_HEIST_STATS environment variable; the tests do). A badge is earned by
how a run was won; the win screen shows the ones earned this time and marks the
ones that are new. A missing or damaged file means a fresh start, never a crash.
"""

import json
import os

ENV_VAR = "MEMORY_HEIST_STATS"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(ROOT, "saves", "stats.json")

VETERAN_WINS = 3
SPEED_FRACTION = 0.5        # time left, as a share of the run clock, for Speed Runner

# (id, name, how to earn it), in the order the stats screen shows them.
BADGES = (
    ("escape", "First Escape", "Win a run"),
    ("flawless", "Flawless", "Win without a single mistake"),
    ("speed", "Speed Runner", "Win with half the clock left"),
    ("duo", "Dynamic Duo", "Win in co-op"),
    ("nerves", "Nerves of Steel", "Win on Hard"),
    ("veteran", "Veteran", f"Win {VETERAN_WINS} runs"),
)
BADGE_IDS = tuple(b[0] for b in BADGES)
BADGE_NAMES = {b[0]: b[1] for b in BADGES}


def earned_badges(result, wins):
    """Badge ids a won run qualifies for.

    result: mistakes, time_left, run_seconds, difficulty, coop, continued.
    wins:   total wins including this one.
    A continued run never counts as flawless or fast, since part of it was not
    watched (its mistakes and clock were not carried over in full).
    """
    earned = ["escape"]
    if result["mistakes"] <= 0 and not result["continued"]:
        earned.append("flawless")
    run_seconds = result["run_seconds"]
    if (not result["continued"] and run_seconds > 0
            and result["time_left"] >= SPEED_FRACTION * run_seconds):
        earned.append("speed")
    if result["coop"]:
        earned.append("duo")
    if result["difficulty"] == "hard":
        earned.append("nerves")
    if wins >= VETERAN_WINS:
        earned.append("veteran")
    return [b for b in BADGE_IDS if b in earned]


def _path(path):
    return path or os.environ.get(ENV_VAR) or DEFAULT_PATH


def _count(value):
    return value if isinstance(value, int) and not isinstance(value, bool) and value >= 0 else 0


class Stats:
    def __init__(self, path=None):
        self.path = _path(path)
        self.wins = self.losses = self.best_score = 0
        self.best_time_left = 0
        self.badges = []
        self._load()

    def _load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError):
            return
        if not isinstance(data, dict):
            return
        self.wins = _count(data.get("wins"))
        self.losses = _count(data.get("losses"))
        self.best_score = _count(data.get("best_score"))
        self.best_time_left = _count(data.get("best_time_left"))
        saved = data.get("badges")
        if isinstance(saved, list):
            self.badges = [b for b in BADGE_IDS if b in saved]

    def _save(self):
        data = {"wins": self.wins, "losses": self.losses, "best_score": self.best_score,
                "best_time_left": self.best_time_left, "badges": self.badges}
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except OSError:
            pass            # best-effort: the game carries on without saving

    def record_win(self, score, result):
        """Count a win; returns (badges earned this run, the ones that are new)."""
        self.wins += 1
        self.best_score = max(self.best_score, int(score))
        self.best_time_left = max(self.best_time_left, int(result["time_left"]))
        earned = earned_badges(result, self.wins)
        new = [b for b in earned if b not in self.badges]
        self.badges = [b for b in BADGE_IDS if b in self.badges or b in earned]
        self._save()
        return earned, new

    def record_loss(self):
        self.losses += 1
        self._save()
