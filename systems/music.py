"""
systems/music.py
Owner: Member 1 - Core Game System

Adaptive music, composed in code (no music files are bundled).

  * Every floor has its own theme (systems/composer.py): its own mode, tempo,
    chords, bass line and melody. Five looping stems play together:
      pad    - sustained chords, always there
      pulse  - bass and drums, grows with depth (deeper floor = more drive)
      arp    - arpeggiated chord tones
      lead   - the melody; it steps back as the WARDEN closes in
      alert  - a tense tritone drone, rises with the WARDEN alert meter
  * `mix_for()` is pure: (state, level, alert) -> stem volumes. Easy to test.
  * `MusicPlayer` crossfades stems when the floor changes and glides volumes,
    so the music never jumps. It renders the next floor's audio in the
    background so a floor change never stalls. With no sound device it does
    nothing.

Levels never touch this; Game calls MusicPlayer.update() once a frame.
"""

import threading
from functools import lru_cache

import pygame

from core.level_manager import LEVEL_ORDER

try:
    import numpy as np
    from systems import composer
except ImportError:                    # numpy is in requirements.txt
    np = None
    composer = None

SAMPLE_RATE = 44100
MASTER = 0.5
FADE_PER_SECOND = 0.6                   # volume units per second
STEMS = ("pad", "pulse", "arp", "lead", "alert")
MUSIC_CHANNELS = 2 * len(STEMS)         # two floors of stems mid-crossfade
TOTAL_CHANNELS = MUSIC_CHANNELS + 10    # leaves 10 for sound effects

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
    """Stem volumes (0..1) for a screen.

    Calm screens get pad, a soft arpeggio and the melody. In play the bass
    and drums grow with depth, and the melody gives way to the alert drone as
    the WARDEN closes in.
    """
    if state in _CALM_STATES or level_name not in LEVEL_ORDER:
        return {"pad": 0.8, "pulse": 0.0, "arp": 0.35, "lead": 0.45, "alert": 0.0}
    depth = LEVEL_ORDER.index(level_name) / max(1, len(LEVEL_ORDER) - 1)
    alert = _clamp(alert)
    if state == "lose":
        return {"pad": 0.2, "pulse": 0.0, "arp": 0.0, "lead": 0.0, "alert": 1.0}
    return {
        "pad": 0.8,
        "pulse": _clamp(0.25 + 0.65 * depth),
        "arp": _clamp((0.4 + 0.3 * depth) * (1.0 - 0.5 * alert)),
        "lead": _clamp(0.6 * (1.0 - alert)),
        "alert": _clamp(alert ** 1.5),
    }


def approach(current, target, step):
    """Move current toward target by at most `step`."""
    if current < target:
        return min(target, current + step)
    return max(target, current - step)


def root_for(key):
    """The tonic (Hz) a screen plays in."""
    if key == "menu":
        return MENU_ROOT
    if key not in FLOOR_ROOTS:
        raise ValueError(f"unknown theme {key!r}")
    return FLOOR_ROOTS[key]


RENDER_CACHE_SIZE = 16                  # about three screens of stems, roughly 30 MB


@lru_cache(maxsize=RENDER_CACHE_SIZE)
def _render(stem, key):
    data = composer.render_stem(stem, key, root_for(key))
    data.setflags(write=False)           # shared between callers: nobody may edit it
    return data


def synth_stem(stem, key):
    """One seamless stereo int16 loop of a stem for a screen ("menu" or a level name).

    Rendering is deterministic, so the most recent loops are remembered: a
    second player (or a floor you return to) costs nothing.
    """
    if composer is None:
        raise RuntimeError("numpy is required for music synthesis")
    return _render(stem, key)


def next_key(key):
    """The floor that follows `key`, whose audio is worth preparing early."""
    if key == "menu":
        return LEVEL_ORDER[0]
    if key in LEVEL_ORDER and LEVEL_ORDER.index(key) + 1 < len(LEVEL_ORDER):
        return LEVEL_ORDER[LEVEL_ORDER.index(key) + 1]
    return None


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
        self._arrays = {}                 # (key, stem) -> audio rendered ahead of time
        self._prefetching = set()
        self._threads = []
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
            data = self._arrays.pop((key, stem), None)
            if data is None:
                data = synth_stem(stem, key)
            cached = pygame.sndarray.make_sound(data)
            self._sounds[(key, stem)] = cached
        return cached

    def prefetch(self, key):
        """Render a screen's stems in a background thread, ready for its turn.

        Only numpy runs off the main thread; the mixer is touched on the main
        thread alone.
        """
        if key is None or key in self._prefetching:
            return
        if all((key, stem) in self._sounds for stem in STEMS):
            return
        self._prefetching.add(key)
        thread = threading.Thread(target=self._render_ahead, args=(key,), daemon=True)
        self._threads.append(thread)
        thread.start()

    def _render_ahead(self, key):
        for stem in STEMS:
            if (key, stem) not in self._arrays:
                self._arrays[(key, stem)] = synth_stem(stem, key)

    def wait_for_prefetch(self):
        """Block until background rendering finishes (used by tests)."""
        for thread in self._threads:
            thread.join()

    def _forget_old(self, keep):
        """Drop audio for screens other than `keep` (about 7 MB each)."""
        self._sounds = {k: v for k, v in self._sounds.items() if k[0] in keep}
        self._arrays = {k: v for k, v in self._arrays.items() if k[0] in keep}

    def _start_key(self, key):
        previous = self.key
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
        following = next_key(key)
        self._forget_old({key, previous, following})
        self.prefetch(following)

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
        scale = getattr(self.audio, "music_volume", 1.0)
        for voice in list(self.voices):
            if voice.key == self.key:
                voice.target = 0.0 if muted else mix[voice.stem] * MASTER * scale
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
