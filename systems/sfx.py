"""Procedural sound effects (no asset files needed).

Each effect is a short mono waveform built with numpy, so the levels can add
tactile feedback (pick up, put down, footsteps, door) without anyone having
to source or license audio.  ``synth_sfx`` is pure and deterministic.
"""

import numpy as np

SAMPLE_RATE = 44100
# The first four came with Floor 1. The rest are the NovaCorp sound pack:
# props and hazards (bell, vending, chip, alarm, switch, zap, drone, laser,
# stamp), an intercom chime, the vault fanfare, and a footstep for each kind of
# floor (step_metal, step_server, step_marble; plain "step" is tile and carpet).
SFX_NAMES = ("pickup", "drop", "step", "door",
             "bell", "vending", "chip", "alarm", "switch", "zap", "drone", "laser",
             "stamp", "chime", "fanfare", "step_metal", "step_server", "step_marble")
SFX_VOLUME = {"pickup": 0.55, "drop": 0.7, "step": 0.22, "door": 0.6,
              "bell": 0.5, "vending": 0.65, "chip": 0.5, "alarm": 0.6, "switch": 0.55,
              "zap": 0.5, "drone": 0.35, "laser": 0.5, "stamp": 0.7, "chime": 0.45,
              "fanfare": 0.6, "step_metal": 0.25, "step_server": 0.2, "step_marble": 0.24}


def _t(duration):
    return np.linspace(0.0, duration, int(SAMPLE_RATE * duration), endpoint=False)


def _sweep(t, f0, f1):
    """Sine whose frequency glides f0 -> f1 over len(t) samples."""
    freq = np.linspace(f0, f1, t.size)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    return np.sin(phase)


def _decay(t, rate):
    return np.exp(-rate * t)


def _lowpass(noise, width):
    return np.convolve(noise, np.ones(width) / width, mode="same")


def _tone(t, freq, rate):
    """A plain decaying sine at `freq`."""
    return np.sin(2 * np.pi * freq * t) * _decay(t, rate)


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
    elif name == "bell":                                    # reception desk: bright ding
        t = _t(0.55)
        wave = _tone(t, 1760, 7) + 0.5 * _tone(t, 2637, 9) + 0.2 * _tone(t, 4186, 14)
    elif name == "vending":                                 # a can dropping down the chute
        t = _t(0.35)
        wave = _sweep(t, 220, 90) * _decay(t, 16)
        late = t > 0.2
        wave[late] += 0.8 * _sweep(t[late], 140, 60) * _decay(t[late] - 0.2, 30)
        wave += 0.3 * rng.uniform(-1, 1, t.size) * _decay(t, 50)
    elif name == "chip":                                    # two quick rising blips
        t = _t(0.18)
        first = _sweep(t, 880, 1100) * _decay(t, 14)
        second = np.roll(_sweep(t, 1100, 1480) * _decay(t, 14), int(SAMPLE_RATE * 0.07))
        second[: int(SAMPLE_RATE * 0.07)] = 0.0
        wave = first + second
    elif name == "alarm":                                   # harsh two-tone buzz: a mistake
        t = _t(0.5)
        pitch = np.where((t * 8).astype(int) % 2 == 0, 440.0, 330.0)
        wave = np.sign(np.sin(2 * np.pi * np.cumsum(pitch) / SAMPLE_RATE)) * _decay(t, 2.5)
        wave = _lowpass(wave, 3)
    elif name == "switch":                                  # heavy breaker: click then clunk
        t = _t(0.18)
        wave = rng.uniform(-1, 1, t.size) * _decay(t, 220)
        late = t > 0.05
        wave[late] += 0.9 * _sweep(t[late], 180, 70) * _decay(t[late] - 0.05, 35)
    elif name == "zap":                                     # electric crackle
        t = _t(0.3)
        crackle = rng.uniform(-1, 1, t.size) * (rng.uniform(0, 1, t.size) > 0.55)
        buzz = np.sign(np.sin(2 * np.pi * 120 * t))
        wave = (0.7 * crackle + 0.4 * buzz) * _decay(t, 9)
    elif name == "drone":                                   # a drone's rotor whine
        t = _t(0.45)
        vib = 1 + 0.06 * np.sin(2 * np.pi * 30 * t)
        wave = np.sin(2 * np.pi * 190 * t * vib) + 0.5 * np.sin(2 * np.pi * 380 * t * vib)
        wave *= np.sin(np.pi * np.clip(t / 0.45, 0, 1)) ** 1.5
    elif name == "laser":                                   # fast falling zap
        t = _t(0.28)
        wave = _sweep(t, 2000, 260) * _decay(t, 9)
        wave += 0.25 * _sweep(t, 1000, 130) * _decay(t, 9)
    elif name == "stamp":                                   # a rubber stamp slammed on paper
        t = _t(0.22)
        wave = _sweep(t, 110, 45) * _decay(t, 24)
        wave += 0.5 * _lowpass(rng.uniform(-1, 1, t.size), 4) * _decay(t, 55)
    elif name == "chime":                                   # intercom ding-dong
        t = _t(0.6)
        wave = _tone(t, 660, 5) * (t < 0.3)
        low = t >= 0.3
        wave[low] += _tone(t[low] - 0.3, 524, 6)
    elif name == "fanfare":                                 # three rising notes, then a held chord
        t = _t(0.6)
        wave = np.zeros(t.size)
        for i, f in enumerate((523, 659, 784)):
            start = int(SAMPLE_RATE * 0.11 * i)
            tt = t[: t.size - start]
            wave[start:] += _tone(tt, f, 5) + 0.4 * _tone(tt, f * 2, 7)
    elif name == "step_metal":                              # boot on a steel grating
        t = _t(0.09)
        wave = (rng.uniform(-1, 1, t.size) + 0.8 * _tone(t, 900, 45)) * _decay(t, 45)
    elif name == "step_server":                             # muffled, raised-floor thud
        t = _t(0.07)
        wave = _lowpass(rng.uniform(-1, 1, t.size), 14) * _decay(t, 55)
    elif name == "step_marble":                             # hard heel click with an echo
        t = _t(0.16)
        tick = rng.uniform(-1, 1, t.size) * _decay(t, 120) + 0.6 * _tone(t, 2200, 90)
        echo = np.zeros(t.size)
        d = int(SAMPLE_RATE * 0.06)
        echo[d:] = 0.3 * tick[: t.size - d]
        wave = tick + echo
    else:
        raise KeyError(name)
    wave = _fade_edges(wave)
    peak = float(np.max(np.abs(wave))) or 1.0
    return wave / peak * SFX_VOLUME[name]


def to_int16_stereo(wave):
    pcm = (np.clip(wave, -1.0, 1.0) * 32767).astype(np.int16)
    return np.ascontiguousarray(np.column_stack((pcm, pcm)))
