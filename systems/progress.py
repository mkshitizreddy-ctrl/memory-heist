"""
systems/progress.py

The saved run: where the player got to, so the menu can offer "Continue".

Stored as JSON in saves/progress.json (the path can be overridden with the
MEMORY_HEIST_PROGRESS environment variable, which the tests use). A floor is
saved the moment the player clears the one before it. A missing, damaged or
hand-edited file means "no saved run", never a crash.
"""

import json
import os

from core.difficulty import DIFFICULTIES
from core.level_manager import LEVEL_ORDER

ENV_VAR = "MEMORY_HEIST_PROGRESS"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(ROOT, "saves", "progress.json")


def _path(path):
    return path or os.environ.get(ENV_VAR) or DEFAULT_PATH


def _is_int(value):
    return isinstance(value, int) and not isinstance(value, bool)


def _is_number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _valid(data):
    return (
        isinstance(data, dict)
        and data.get("level") in LEVEL_ORDER
        and data.get("level") != LEVEL_ORDER[0]       # floor 1 is just a new game
        and _is_int(data.get("score")) and data["score"] >= 0
        and _is_number(data.get("remaining")) and data["remaining"] > 0
        and data.get("difficulty") in DIFFICULTIES
        and isinstance(data.get("coop"), bool)
    )


def save_progress(level, score, remaining, difficulty, coop, path=None):
    """Write the run so far. Best-effort: a read-only disk just means no Continue."""
    data = {
        "level": level,
        "score": score,
        "remaining": round(remaining, 1) if _is_number(remaining) else remaining,
        "difficulty": difficulty,
        "coop": coop,
    }
    if not _valid(data):
        return False
    target = _path(path)
    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except OSError:
        return False
    return True


def load_progress(path=None):
    """The saved run as a dict, or None when there is none worth continuing."""
    try:
        with open(_path(path), "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, ValueError):
        return None
    return data if _valid(data) else None


def clear_progress(path=None):
    """Forget the saved run (after a win, so Continue never replays a finished game)."""
    try:
        os.remove(_path(path))
    except OSError:
        pass


def describe(data):
    """The menu's one-line summary: 'Floor 3 - 450 pts'."""
    floor = LEVEL_ORDER.index(data["level"]) + 1
    name = "Final Vault" if data["level"] == LEVEL_ORDER[-1] else f"Floor {floor}"
    return f"{name} - {data['score']} pts"
