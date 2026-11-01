"""Procedural sound effects (no asset files needed).

Each effect is a short mono waveform built with numpy, so the levels can add
tactile feedback (pick up, put down, footsteps, door) without anyone having
to source or license audio.  ``synth_sfx`` is pure and deterministic.
"""

import numpy as np

SAMPLE_RATE = 44100
SFX_NAMES = ("pickup", "drop", "step", "door")
SFX_VOLUME = {"pickup": 0.55, "drop": 0.7, "step": 0.22, "door": 0.6}


def _t(duration):
    return np.linspace(0.0, duration, int(SAMPLE_RATE * duration), endpoint=False)


def _sweep(t, f0, f1):
    """Sine whose frequency glides f0 -> f1 over len(t) samples."""
    freq = np.linspace(f0, f1, t.size)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    return np.sin(phase)


def _decay(t, rate):
    return np.exp(-rate * t)


def _fade_edges(wave, ms=4):
    n = min(int(SAMPLE_RATE * ms / 1000), wave.size // 2)
    if n:
        ramp = np.linspace(0.0, 1.0, n)
        wave[:n] *= ramp
        wave[-n:] *= ramp[::-1]
    return wave


def synth_sfx(name):
    """Return a float mono waveform in [-1, 1] for ``name``."""
    rng = np.random.default_rng(sum(map(ord, name)))        # deterministic noise
    if name == "pickup":                                    # quick rising blip
        t = _t(0.11)
        wave = _sweep(t, 420, 900) * _decay(t, 18)
    elif name == "drop":                                    # soft low thud
        t = _t(0.16)
        wave = _sweep(t, 140, 55) * _decay(t, 22)
        wave += 0.35 * rng.uniform(-1, 1, t.size) * _decay(t, 70)
    elif name == "step":                                    # tiny footfall tick
        t = _t(0.05)
        noise = rng.uniform(-1, 1, t.size)
        noise = np.convolve(noise, np.ones(6) / 6, mode="same")   # crude low-pass
        wave = noise * _decay(t, 60)
    elif name == "door":                                    # sliding whoosh + clunk
        t = _t(0.55)
        hiss = np.convolve(rng.uniform(-1, 1, t.size), np.ones(10) / 10, mode="same")
        swell = np.sin(np.pi * np.clip(t / 0.45, 0, 1)) ** 2
        wave = 0.5 * hiss * swell + 0.4 * _sweep(t, 160, 260) * swell
        thunk = t > 0.45
        wave[thunk] += 0.5 * _sweep(t[thunk], 110, 70) * _decay(t[thunk] - 0.45, 30)
    else:
        raise KeyError(name)
    wave = _fade_edges(wave)
    peak = float(np.max(np.abs(wave))) or 1.0
    return wave / peak * SFX_VOLUME[name]


def to_int16_stereo(wave):
    pcm = (np.clip(wave, -1.0, 1.0) * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack((pcm, pcm)))
