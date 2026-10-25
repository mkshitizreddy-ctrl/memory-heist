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
        "security_penalty_multiplier": 0.5,
        "hints_enabled": True,
    },
    "medium": {
        "label": "MEDIUM",
        "timer_multiplier": 1.0,
        "security_penalty_multiplier": 1.0,
        "hints_enabled": True,
    },
    "hard": {
        "label": "HARD",
        "timer_multiplier": 0.7,
        "security_penalty_multiplier": 1.5,
        "hints_enabled": False,
    },
}

DEFAULT_DIFFICULTY = "medium"


def get_difficulty(name):
    """Return the difficulty config dict, or the default if name is invalid."""
    return DIFFICULTIES.get(name, DIFFICULTIES[DEFAULT_DIFFICULTY])