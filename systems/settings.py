"""Player settings: music, effects and voice volumes and a mute switch.

Saved as JSON next to the leaderboard (saves/settings.json).  A missing or
damaged file simply gives the defaults, and a failed save never crashes the
game.  Set MEMORY_HEIST_SETTINGS to point somewhere else (the tests do).
"""

import json
import math
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_PATH = os.path.join(ROOT, "saves", "settings.json")
ENV_VAR = "MEMORY_HEIST_SETTINGS"

STEP = 0.1
DEFAULT_MUSIC = 1.0
DEFAULT_SFX = 1.0
DEFAULT_VOICE = 1.0


def settings_path():
    return os.environ.get(ENV_VAR) or DEFAULT_PATH


def clamp(value, default=1.0):
    """A volume between 0 and 1, rounded to 2 places; junk gives `default`."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return default
    if math.isnan(value):
        return default
    return round(max(0.0, min(1.0, float(value))), 2)


def step(value, delta):
    """Move a volume by a whole step, staying inside 0..1."""
    return clamp(round(value + delta, 2))


class Settings:
    def __init__(self, music=DEFAULT_MUSIC, sfx=DEFAULT_SFX, muted=False, path=None,
                 voice=DEFAULT_VOICE):
        self.music = clamp(music, DEFAULT_MUSIC)
        self.sfx = clamp(sfx, DEFAULT_SFX)
        self.voice = clamp(voice, DEFAULT_VOICE)
        self.muted = bool(muted)
        self.path = path or settings_path()

    # --- changing -----------------------------------------------------------
    def set_music(self, value):
        self.music = clamp(value, self.music)

    def set_sfx(self, value):
        self.sfx = clamp(value, self.sfx)

    def set_voice(self, value):
        self.voice = clamp(value, self.voice)

    def toggle_muted(self):
        self.muted = not self.muted

    # --- saving -------------------------------------------------------------
    def to_dict(self):
        return {"music": self.music, "sfx": self.sfx, "voice": self.voice, "muted": self.muted}

    @classmethod
    def load(cls, path=None):
        path = path or settings_path()
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                raise ValueError("settings must be an object")
        except (OSError, ValueError):
            return cls(path=path)
        muted = data.get("muted", False)
        return cls(
            music=data.get("music", DEFAULT_MUSIC),
            sfx=data.get("sfx", DEFAULT_SFX),
            voice=data.get("voice", DEFAULT_VOICE),
            muted=muted if isinstance(muted, bool) else False,
            path=path,
        )

    def save(self):
        """Write the file; returns False (instead of raising) if that fails."""
        try:
            os.makedirs(os.path.dirname(self.path) or ".", exist_ok=True)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(self.to_dict(), f, indent=2)
            return True
        except OSError:
            return False
