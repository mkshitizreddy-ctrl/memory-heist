"""
core/difficulty.py
Owner: Member 1 - Core Game System

Difficulty presets. Each preset affects timer length, hint availability,
and security penalty scaling. Actual wiring into gameplay happens in
game.py separately.
"""

DIFFICULTIES = {
    "easy": {
        "label": "EASY",
        "timer_multiplier": 1.5,
        "question_time_multiplier": 2.0,     # each floor's question clock: room to read and think
        "score_multiplier": 0.8,
        "security_penalty_multiplier": 0.5,
        "hints_enabled": True,
    },
    "medium": {
        "label": "MEDIUM",
        "timer_multiplier": 1.0,
        "question_time_multiplier": 1.3,
        "score_multiplier": 1.0,
        "security_penalty_multiplier": 1.0,
        "hints_enabled": True,
    },
    "hard": {
        "label": "HARD",
        "timer_multiplier": 0.7,
        "question_time_multiplier": 0.7,
        "score_multiplier": 1.25,
        "security_penalty_multiplier": 1.5,
        "hints_enabled": False,
    },
}

DEFAULT_DIFFICULTY = "medium"

# Length of the whole-run countdown on MEDIUM, in seconds. EASY and HARD
# scale it with the preset's timer_multiplier.
BASE_RUN_SECONDS = 900


def get_difficulty(name):
    """Return the difficulty config dict, or the default if name is invalid."""
    return DIFFICULTIES.get(name, DIFFICULTIES[DEFAULT_DIFFICULTY])


# Security cools a little in the lift between floors, so one bad floor does not doom the run.
FLOOR_COOLDOWN = 25


def question_time_multiplier(difficulty):
    """Scale for a floor's question clock; `difficulty` is a name or a config dict."""
    config = difficulty if isinstance(difficulty, dict) else get_difficulty(difficulty)
    return config.get("question_time_multiplier", config.get("timer_multiplier", 1.0))


def run_time_seconds(difficulty):
    """Seconds on the whole-run countdown for a difficulty config dict."""
    return round(BASE_RUN_SECONDS * difficulty["timer_multiplier"])
