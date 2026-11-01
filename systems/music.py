"""
systems/music.py
Owner: Member 1 - Core Game System

Adaptive music, generated in code (no music files are bundled).

  * Every floor has its own key. Three looping stems play together:
      pad    - slow chord, always there
      pulse  - rhythmic bass, grows with depth (deeper floor = more drive)
      alert  - a tense tritone drone, rises with the WARDEN alert meter
  * `mix_for()` is pure: (state, level, alert) -> stem volumes. Easy to test.
  * `MusicPlayer` crossfades stems when the floor changes and glides volumes,
    so the music never jumps. With no sound device it does nothing.

Levels never touch this; Game calls MusicPlayer.update() once a frame.
"""

import math

import pygame

from core.level_manager import LEVEL_ORDER

try:
    import numpy as np
except ImportError:                    # numpy is in requirements.txt
    np = None

SAMPLE_RATE = 44100
LOOP_SECONDS = 4.0
MASTER = 0.5
FADE_PER_SECOND = 0.6                   # volume units per second
STEMS = ("pad", "pulse", "alert")
MUSIC_CHANNELS = 6                      # two floors of three stems mid-crossfade
TOTAL_CHANNELS = 16                     # leaves 10 for sound effects

# Root note per floor (Hz). Each floor sits a step higher and tenser.
FLOOR_ROOTS = {
    "level1": 55.0,        # A1
    "level2": 61.74,       # B1
    "level3": 65.41,       # C2
    "level4": 73.42,       # D2
    "level5": 82.41,       # E2
    "final_vault": 87.31,  # F2
}
MENU_ROOT = 49.0                        # G1: calm, below the building

_CALM_STATES = ("menu", "intro", "outro", "win")


def _clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def key_for(state, level_name):
    """Which key (root) a screen plays in."""
    if state in _CALM_STATES or level_name not in FLOOR_ROOTS:
        return "menu"
    return level_name


def mix_for(state, level_name, alert):
    """Stem volumes (0..1) for a screen. Calm screens are pad only."""
    if state in _CALM_STATES or level_name not in LEVEL_ORDER:
        return {"pad": 0.8, "pulse": 0.0, "alert": 0.0}
    depth = LEVEL_ORDER.index(level_name) / max(1, len(LEVEL_ORDER) - 1)
    alert = _clamp(alert)
    if state == "lose":
        return {"pad": 0.2, "pulse": 0.0, "alert": 1.0}
    return {
        "pad": 0.8,
        "pulse": _clamp(0.25 + 0.65 * depth),
        "alert": _clamp(alert ** 1.5),
    }


def approach(current, target, step):
    """Move current toward target by at most `step`."""
    if current < target:
        return min(target, current + step)
    return max(target, current - step)


def _snap(freq):
    """Nudge a frequency so a whole number of cycles fit the loop (no click)."""
    return max(1, round(freq * LOOP_SECONDS)) / LOOP_SECONDS


def synth_stem(stem, root):
    """One seamless stereo int16 loop for a stem in the key of `root`."""
    if np is None:
        raise RuntimeError("numpy is required for music synthesis")
    n = int(SAMPLE_RATE * LOOP_SECONDS)
    t = np.arange(n) / SAMPLE_RATE
    two_pi = 2 * math.pi

    if stem == "pad":
        wave = sum(a * np.sin(two_pi * _snap(root * m) * t)
                   for m, a in ((1, 0.30), (1.5, 0.20), (2, 0.14), (3, 0.06)))
        wave = wave * (0.85 + 0.15 * np.sin(two_pi * 0.25 * t))
    elif stem == "pulse":
        beat = np.mod(t * 2.0, 1.0)                 # 2 beats a second
        env = np.exp(-beat * 6.0)
        wave = 0.6 * env * np.sin(two_pi * _snap(root) * t)
        wave += 0.25 * env * np.sin(two_pi * _snap(root * 2) * t)
    elif stem == "alert":
        wave = 0.28 * np.sin(two_pi * _snap(root * 1.414) * t)   # tritone
        wave += 0.22 * np.sin(two_pi * _snap(root * 2.0) * t)
        wave *= 0.6 + 0.4 * np.sin(two_pi * 1.0 * t) ** 2         # throb
    else:
        raise ValueError(f"unknown stem {stem!r}")

    mono = np.clip(wave, -1.0, 1.0)
    data = (mono * 32767 * 0.5).astype(np.int16)
    return np.ascontiguousarray(np.column_stack((data, data)))


class _Voice:
    def __init__(self, key, stem, index):
        self.key = key
        self.stem = stem
        self.index = index
        self.channel = pygame.mixer.Channel(index)
        self.volume = 0.0
        self.target = 0.0


class MusicPlayer:
    """Crossfading stem player on top of the pygame mixer."""

    def __init__(self, audio):
        self.audio = audio
        self.key = None
        self.voices = []
        self._sounds = {}
        self.available = bool(
            getattr(audio, "mixer_ready", False) and np is not None
        )
        if self.available:
            self._reserve_channels()

    @staticmethod
    def _reserve_channels():
        """Channels 0..5 belong to the music; effects use the rest."""
        if pygame.mixer.get_num_channels() < TOTAL_CHANNELS:
            pygame.mixer.set_num_channels(TOTAL_CHANNELS)
        pygame.mixer.set_reserved(MUSIC_CHANNELS)

    def _free_channel(self):
        busy = {v.index for v in self.voices}
        for i in range(MUSIC_CHANNELS):
            if i not in busy:
                return i
        return None

    def _sound(self, key, stem):
        cached = self._sounds.get((key, stem))
        if cached is None:
            root = MENU_ROOT if key == "menu" else FLOOR_ROOTS[key]
            cached = pygame.sndarray.make_sound(synth_stem(stem, root))
            self._sounds[(key, stem)] = cached
        return cached

    def _start_key(self, key):
        for voice in self.voices:
            voice.target = 0.0
        for stem in STEMS:
            index = self._free_channel()
            if index is None:                         # all reserved channels busy
                continue
            voice = _Voice(key, stem, index)
            voice.channel.set_volume(0.0)
            voice.channel.play(self._sound(key, stem), loops=-1)
            self.voices.append(voice)
        self.key = key

    def update(self, dt, state, level_name, alert):
        if not self.available:
            return
        key = key_for(state, level_name)
        if key != self.key:
            try:
                self._start_key(key)
            except pygame.error:
                self.available = False
                return
        mix = mix_for(state, level_name, alert)
        step = FADE_PER_SECOND * max(0.0, dt)
        muted = not getattr(self.audio, "enabled", True)
        for voice in list(self.voices):
            if voice.key == self.key:
                voice.target = 0.0 if muted else mix[voice.stem] * MASTER
            voice.volume = approach(voice.volume, voice.target, step)
            voice.channel.set_volume(voice.volume)
            if voice.key != self.key and voice.volume <= 0.0:
                voice.channel.stop()
                self.voices.remove(voice)

    def stop(self):
        for voice in self.voices:
            voice.channel.stop()
        self.voices = []
        self.key = None
