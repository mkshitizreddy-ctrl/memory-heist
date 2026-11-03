"""
systems/composer.py
Owner: Member 1 - Core Game System

The game's music, composed in code. Each screen has a Theme: a mode (scale),
a tempo, a four-bar chord progression, a bass line, an arpeggio style, a drum
feel and a melody. render_stem() turns a theme into one stem of audio:

    pad    - sustained chords
    pulse  - bass line and drums
    arp    - arpeggiated chord tones
    lead   - the melody, with an echo
    alert  - a tense tritone drone (the WARDEN closing in)

Every stem is exactly four bars long and loops without a click: notes that
ring past the end of the loop are folded back onto its start. Rendering is
deterministic (fixed noise seed), so tests can compare results exactly.
"""

import math
from collections import namedtuple

import numpy as np

SAMPLE_RATE = 44100
BEATS_PER_LOOP = 16                     # four bars of 4/4

MODES = {
    "minor": (0, 2, 3, 5, 7, 8, 10),
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "mixolydian": (0, 2, 4, 5, 7, 9, 10),
    "phrygian": (0, 1, 3, 5, 7, 8, 10),
    "harmonic_minor": (0, 2, 3, 5, 7, 8, 11),
}

# Bass: one slot per eighth note. 0 rest, 1 root, 2 fifth, 3 octave.
BASS_PATTERNS = {
    "steady": (1, 0, 1, 0, 1, 0, 1, 0),
    "offbeat": (1, 0, 0, 1, 0, 1, 0, 2),
    "drive": (1, 1, 0, 1, 1, 0, 1, 2),
    "pedal": (1, 0, 0, 0, 1, 0, 0, 0),
    "march": (1, 0, 2, 0, 1, 0, 3, 0),
}
# Arpeggio: which chord tone (0 root, 1 third, 2 fifth, 3 octave) comes next.
ARP_SHAPES = {
    "up": (0, 1, 2, 3),
    "updown": (0, 1, 2, 3, 2, 1),
    "broken": (0, 2, 1, 3),
    "pedal": (0, 2, 1, 2),
}

Theme = namedtuple("Theme", "mode bpm progression bass arp_div arp kick hat snare lead")
# progression: scale degree of each bar's chord. arp_div: arpeggio notes per beat.
# kick: "none" | "half" (beats 1 and 3) | "four". lead: (bar, beat, degree, length).

THEMES = {
    "menu": Theme("minor", 72, (0, 5, 2, 6), "pedal", 2, "updown", "none", False, False, (
        (0, 0, 4, 2), (0, 2, 2, 1.5), (1, 0, 3, 2), (1, 2, 1, 2),
        (2, 0, 4, 1.5), (2, 2, 6, 1), (2, 3, 5, 1), (3, 0, 4, 3.5))),
    "level1": Theme("dorian", 96, (0, 4, 5, 3), "offbeat", 2, "up", "half", True, False, (
        (0, 0, 4, 1), (0, 1, 5, 0.5), (0, 1.5, 4, 0.5), (0, 2, 2, 2),
        (1, 0, 3, 1), (1, 1, 4, 1), (1, 2, 2, 1.5),
        (2, 0, 5, 1), (2, 1, 6, 1), (2, 2, 4, 1), (2, 3, 2, 1),
        (3, 0, 1, 2), (3, 2, 2, 0.5), (3, 2.5, 0, 1.5))),
    "level2": Theme("mixolydian", 104, (0, 6, 3, 0), "steady", 2, "broken", "half", True, True, (
        (0, 0, 2, 0.5), (0, 0.5, 4, 0.5), (0, 1, 6, 1), (0, 2, 4, 1),
        (1, 0, 5, 0.5), (1, 0.5, 4, 0.5), (1, 1, 2, 1), (1, 2, 0, 2),
        (2, 0, 2, 0.5), (2, 0.5, 4, 0.5), (2, 1, 6, 1), (2, 2, 7, 1),
        (3, 0, 6, 1), (3, 1, 4, 1), (3, 2, 2, 2))),
    "level3": Theme("minor", 118, (0, 5, 2, 6), "drive", 4, "up", "four", True, True, (
        (0, 0, 0, 0.5), (0, 0.5, 2, 0.5), (0, 1, 4, 0.5), (0, 1.5, 2, 0.5), (0, 2, 7, 1.5),
        (1, 0, 5, 0.5), (1, 0.5, 4, 0.5), (1, 1, 2, 0.5), (1, 1.5, 4, 0.5), (1, 2, 5, 1.5),
        (2, 0, 4, 0.5), (2, 0.5, 2, 0.5), (2, 1, 0, 0.5), (2, 1.5, 2, 0.5), (2, 2, 4, 1.5),
        (3, 0, 6, 0.5), (3, 0.5, 5, 0.5), (3, 1, 4, 1), (3, 2, 1, 2))),
    "level4": Theme("phrygian", 84, (0, 1, 0, 6), "pedal", 2, "pedal", "half", False, False, (
        (0, 0, 7, 1.5), (0, 2, 6, 1), (1, 0, 4, 2.5),
        (2, 0, 7, 1), (2, 1, 8, 1), (2, 2, 6, 1.5), (3, 0, 4, 1), (3, 2, 1, 2))),
    "level5": Theme("dorian", 126, (0, 3, 0, 4), "drive", 4, "updown", "four", True, True, (
        (0, 0, 4, 0.5), (0, 0.5, 4, 0.5), (0, 1, 6, 1), (0, 2, 5, 0.5), (0, 2.5, 4, 1.5),
        (1, 0, 3, 0.5), (1, 0.5, 3, 0.5), (1, 1, 5, 1), (1, 2, 4, 0.5), (1, 2.5, 3, 1.5),
        (2, 0, 4, 0.5), (2, 0.5, 6, 0.5), (2, 1, 7, 1), (2, 2, 6, 1), (2, 3, 4, 1),
        (3, 0, 5, 1), (3, 1, 4, 1), (3, 2, 2, 2))),
    "final_vault": Theme("harmonic_minor", 132, (0, 5, 3, 4), "march", 4, "broken", "four", True, True, (
        (0, 0, 7, 1), (0, 1, 6, 0.5), (0, 1.5, 7, 0.5), (0, 2, 9, 2),
        (1, 0, 8, 1), (1, 1, 7, 0.5), (1, 1.5, 8, 0.5), (1, 2, 7, 2),
        (2, 0, 6, 1), (2, 1, 5, 0.5), (2, 1.5, 6, 0.5), (2, 2, 8, 2),
        (3, 0, 6, 1), (3, 1, 8, 1), (3, 2, 7, 0.5), (3, 2.5, 6, 1.5))),
}

STEMS = ("pad", "pulse", "arp", "lead", "alert")
# Peak level of each stem as a share of full scale, so no stem drowns another.
PEAKS = {"pad": 0.42, "pulse": 0.50, "arp": 0.34, "lead": 0.38, "alert": 0.36}
# Register of each voice, in semitones above the theme's root: bass sits low, the pad
# and arpeggio in the middle, the melody on top, so they do not blur together.
BASS_OFFSET, PAD_OFFSET, ARP_OFFSET, LEAD_OFFSET = 12, 24, 24, 36
_TAIL_SECONDS = 4.0                    # room for the longest note to ring out


def loop_samples(key):
    """Length in samples of every stem of this theme (four bars)."""
    return int(round(BEATS_PER_LOOP * 60.0 / THEMES[key].bpm * SAMPLE_RATE))


def degree_semitones(mode, degree):
    """Semitones above the root for a scale degree; 7 is the octave, -1 the note below."""
    octave, index = divmod(degree, 7)
    return MODES[mode][index] + 12 * octave


def chord_tones(mode, degree):
    """Semitones of a chord on `degree`: root, third, fifth, octave."""
    return [degree_semitones(mode, degree + step) for step in (0, 2, 4, 7)]


def _hz(root, semitones):
    return root * 2.0 ** (semitones / 12.0)


# --- instruments (each returns a mono float array) ----------------------------

def _t(seconds):
    return np.arange(int(seconds * SAMPLE_RATE)) / SAMPLE_RATE


def _pad_note(freq, seconds):
    t = _t(seconds + 0.7)
    wave = 0.0
    for detune in (0.996, 1.0, 1.004):
        f = freq * detune
        wave = wave + np.sin(2 * math.pi * f * t) + 0.25 * np.sin(4 * math.pi * f * t) \
            + 0.1 * np.sin(6 * math.pi * f * t)
    attack = np.minimum(1.0, t / 0.35)
    release = np.minimum(1.0, np.maximum(0.0, (seconds + 0.7 - t) / 0.7))
    return wave * attack * release / 3.0


def _bass_note(freq, seconds):
    t = _t(seconds)
    wave = np.sin(2 * math.pi * freq * t) + 0.45 * np.sin(4 * math.pi * freq * t) \
        + 0.2 * np.sin(6 * math.pi * freq * t)
    env = np.exp(-t * 3.0 / max(seconds, 0.1)) * np.minimum(1.0, t / 0.004)
    return wave * env * np.minimum(1.0, (seconds - t) / 0.02 + 0.0)


def _pluck_note(freq, seconds):
    t = _t(seconds)
    wave = np.sin(2 * math.pi * freq * t) + 0.4 * np.sin(4 * math.pi * freq * t) * np.exp(-t * 8) \
        + 0.2 * np.sin(6 * math.pi * freq * t) * np.exp(-t * 12)
    return wave * np.exp(-t * 6.0 / max(seconds, 0.08)) * np.minimum(1.0, t / 0.004)


def _lead_note(freq, seconds):
    t = _t(seconds + 0.25)
    vibrato = 1.0 + 0.004 * np.sin(2 * math.pi * 5.5 * t) * np.minimum(1.0, t / 0.2)
    phase = 2 * math.pi * np.cumsum(freq * vibrato) / SAMPLE_RATE
    wave = np.sin(phase) + 0.25 * np.sin(2 * phase) + 0.1 * np.sin(3 * phase)
    attack = np.minimum(1.0, t / 0.03)
    release = np.minimum(1.0, np.maximum(0.0, (seconds + 0.25 - t) / 0.25))
    return wave * attack * release


def _kick():
    t = _t(0.28)
    phase = 2 * math.pi * np.cumsum(45 + 95 * np.exp(-t * 28)) / SAMPLE_RATE
    return np.sin(phase) * np.exp(-t * 13)


def _snare(rng):
    t = _t(0.22)
    return (rng.uniform(-1, 1, len(t)) * 0.8 + 0.5 * np.sin(2 * math.pi * 185 * t)) * np.exp(-t * 20)


def _hat(rng):
    t = _t(0.07)
    noise = rng.uniform(-1, 1, len(t) + 1)
    return np.diff(noise) * np.exp(-t * 80) * 0.5


# --- laying notes on a looping timeline ------------------------------------------

class _Loop:
    """A stereo buffer that wraps: anything ringing past the end returns at the start."""

    def __init__(self, n):
        self.n = n
        self.buf = np.zeros((n + int(_TAIL_SECONDS * SAMPLE_RATE), 2))

    def add(self, start, mono, pan=0.0, gain=1.0):
        """Mix `mono` in at sample `start`; pan -1 (left) .. +1 (right)."""
        left = gain * math.cos((pan + 1) * math.pi / 4)
        right = gain * math.sin((pan + 1) * math.pi / 4)
        end = start + len(mono)
        self.buf[start:end, 0] += mono * left
        self.buf[start:end, 1] += mono * right

    def finish(self):
        out = self.buf[:self.n].copy()
        tail = self.buf[self.n:]
        k = min(len(tail), self.n)
        out[:k] += tail[:k]
        return out


def _echo(loop, delays, gains):
    """Looping echo: delayed copies wrap around the loop and swap sides."""
    out = loop.copy()
    for delay, gain in zip(delays, gains):
        out += np.roll(loop, delay, axis=0)[:, ::-1] * gain
    return out


# --- stems -----------------------------------------------------------------

def render_stem(stem, key, root):
    """One seamless stereo int16 loop of `stem` for theme `key` in the key of `root` (Hz)."""
    if stem not in STEMS:
        raise ValueError(f"unknown stem {stem!r}")
    if key not in THEMES:
        raise ValueError(f"unknown theme {key!r}")
    theme = THEMES[key]
    n = loop_samples(key)
    spb = 60.0 / theme.bpm                       # seconds per beat
    at = lambda beat: int(round(beat * spb * SAMPLE_RATE))  # noqa: E731
    loop = _Loop(n)
    rng = np.random.default_rng(1234)
    bar_beats = 4

    if stem == "pad":
        for bar, degree in enumerate(theme.progression):
            for semis in chord_tones(theme.mode, degree)[:3]:
                loop.add(at(bar * bar_beats), _pad_note(_hz(root, semis + PAD_OFFSET), bar_beats * spb), gain=0.5)
    elif stem == "pulse":
        for bar, degree in enumerate(theme.progression):
            tones = chord_tones(theme.mode, degree)
            code_to_semis = {1: tones[0], 2: tones[2], 3: tones[3]}
            for slot, code in enumerate(BASS_PATTERNS[theme.bass]):
                if code:
                    start = at(bar * bar_beats + slot * 0.5)
                    loop.add(start, _bass_note(_hz(root, code_to_semis[code] + BASS_OFFSET), spb * 0.5))
            for beat in range(bar_beats):
                if theme.kick == "four" or (theme.kick == "half" and beat % 2 == 0):
                    loop.add(at(bar * bar_beats + beat), _kick(), gain=0.9)
                if theme.snare and beat % 2 == 1:
                    loop.add(at(bar * bar_beats + beat), _snare(rng), gain=0.35)
                if theme.hat:
                    loop.add(at(bar * bar_beats + beat + 0.5), _hat(rng), pan=0.3, gain=0.4)
    elif stem == "arp":
        shape = ARP_SHAPES[theme.arp]
        step = 1.0 / theme.arp_div
        for bar, degree in enumerate(theme.progression):
            tones = chord_tones(theme.mode, degree)
            for i in range(bar_beats * theme.arp_div):
                tone = tones[shape[i % len(shape)]]
                pan = 0.35 if i % 2 == 0 else -0.35
                loop.add(at(bar * bar_beats + i * step), _pluck_note(_hz(root, tone + ARP_OFFSET), step * spb * 2.2),
                         pan=pan, gain=0.6)
    elif stem == "lead":
        for bar, beat, degree, length in theme.lead:
            semis = degree_semitones(theme.mode, degree) + LEAD_OFFSET
            loop.add(at(bar * bar_beats + beat), _lead_note(_hz(root, semis), length * spb), gain=0.7)
    else:  # alert: a throbbing tritone drone that fits the loop exactly
        seconds = n / SAMPLE_RATE
        t = np.arange(n) / SAMPLE_RATE
        throb = 0.6 + 0.4 * np.sin(2 * math.pi * (theme.bpm / 60.0) * t) ** 2
        for ratio, amp in ((1.414, 0.30), (2.0, 0.22), (2.828, 0.10)):
            freq = max(1, round(root * ratio * seconds)) / seconds
            wave = amp * np.sin(2 * math.pi * freq * t) * throb
            loop.add(0, wave, gain=1.0)

    mix = loop.finish()
    if stem == "lead":                                    # a spacious echo, wrapped
        mix = _echo(mix, (at(0.75), at(1.5)), (0.38, 0.18))

    peak = np.abs(mix).max()
    if peak > 0:
        mix = mix * (PEAKS[stem] / peak)
    return np.ascontiguousarray((mix * 32767).astype(np.int16))
