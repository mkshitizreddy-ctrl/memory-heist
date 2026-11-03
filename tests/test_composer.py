"""The composer: real harmony, melody and rhythm, looping exactly, different on every floor."""

import numpy as np
import pytest

from systems import composer
from systems.composer import (SAMPLE_RATE, STEMS, THEMES, chord_tones, degree_semitones,
                              loop_samples, render_stem)
from systems.music import FLOOR_ROOTS, MENU_ROOT

ROOTS = {**FLOOR_ROOTS, "menu": MENU_ROOT}
REAL_PLUCK = composer._pluck_note


def hz(root, semitones):
    return root * 2 ** (semitones / 12)


def mono(data):
    return data.astype(float).sum(axis=1)


def band_energy(signal, start_s, length_s, freq):
    """How much of `freq` is in a window: magnitude of its Fourier component."""
    a = int(start_s * SAMPLE_RATE)
    seg = signal[a:a + int(length_s * SAMPLE_RATE)]
    t = np.arange(len(seg)) / SAMPLE_RATE
    window = np.hanning(len(seg))
    return abs(np.sum(seg * window * np.exp(-2j * np.pi * freq * t))) / len(seg)


def dominant_hz(signal, start_s, length_s):
    a = int(start_s * SAMPLE_RATE)
    seg = signal[a:a + int(length_s * SAMPLE_RATE)] * np.hanning(int(length_s * SAMPLE_RATE))
    spectrum = np.abs(np.fft.rfft(seg, 1 << 17))
    return np.argmax(spectrum) * SAMPLE_RATE / (1 << 17)


# --- harmony maths -----------------------------------------------------------

def test_degrees_climb_the_scale_and_wrap_by_octaves():
    assert [degree_semitones("dorian", d) for d in range(8)] == [0, 2, 3, 5, 7, 9, 10, 12]
    assert degree_semitones("dorian", 9) == 12 + 3
    assert degree_semitones("dorian", -1) == 10 - 12


def test_chords_are_stacked_thirds_with_an_octave():
    assert chord_tones("minor", 0) == [0, 3, 7, 12]            # A minor: A C E A
    assert chord_tones("mixolydian", 0) == [0, 4, 7, 12]       # major: bright
    assert chord_tones("minor", 5) == [8, 12, 15, 20]          # VI: F A C F


def test_the_modes_are_what_they_claim():
    assert composer.MODES["phrygian"][1] == 1                  # the flat second
    assert composer.MODES["harmonic_minor"][-1] == 11          # the raised seventh
    assert composer.MODES["mixolydian"][2] == 4 and composer.MODES["mixolydian"][-1] == 10


# --- themes ---------------------------------------------------------------

def test_every_floor_and_the_menu_has_a_theme():
    assert set(THEMES) == set(ROOTS)


@pytest.mark.parametrize("key", THEMES)
def test_theme_is_well_formed(key):
    t = THEMES[key]
    assert t.mode in composer.MODES and t.bass in composer.BASS_PATTERNS
    assert t.arp in composer.ARP_SHAPES and t.kick in ("none", "half", "four")
    assert len(t.progression) == 4 and 50 <= t.bpm <= 160
    assert t.arp_div in (2, 4)


@pytest.mark.parametrize("key", THEMES)
def test_melody_fits_the_four_bars_and_is_one_voice(key):
    notes = sorted((bar * 4 + beat, length) for bar, beat, _deg, length in THEMES[key].lead)
    for (start, length), (next_start, _) in zip(notes, notes[1:]):
        assert start + length <= next_start + 1e-9            # a melody never overlaps itself
    for bar, beat, _deg, length in THEMES[key].lead:
        assert 0 <= bar < 4 and 0 <= beat < 4 and length > 0
        assert bar * 4 + beat + length <= composer.BEATS_PER_LOOP + 1e-9


def test_no_two_floors_share_a_sound():
    seen = set()
    for key, t in THEMES.items():
        identity = (t.mode, t.bpm, t.progression, t.lead)
        assert identity not in seen
        seen.add(identity)
    assert len({t.lead for t in THEMES.values()}) == len(THEMES)
    assert len({t.bpm for t in THEMES.values()}) == len(THEMES)


def test_the_final_vault_is_the_most_driving_and_the_menu_the_calmest():
    assert max(THEMES, key=lambda k: THEMES[k].bpm) == "final_vault"
    assert min(THEMES, key=lambda k: THEMES[k].bpm) == "menu"
    assert THEMES["menu"].kick == "none" and THEMES["final_vault"].kick == "four"


def test_the_memory_floor_is_the_eerie_one():
    assert THEMES["level4"].mode == "phrygian"


# --- tempo and looping -------------------------------------------------------

@pytest.mark.parametrize("key", THEMES)
def test_every_loop_is_exactly_sixteen_beats(key):
    expected = 16 * 60 / THEMES[key].bpm * SAMPLE_RATE
    assert abs(loop_samples(key) - expected) <= 1
    for stem in STEMS:
        assert len(render_stem(stem, key, ROOTS[key])) == loop_samples(key)


def test_rendering_is_deterministic():
    a = render_stem("pulse", "level3", ROOTS["level3"])
    b = render_stem("pulse", "level3", ROOTS["level3"])
    assert np.array_equal(a, b)


def test_every_stem_sounds_different():
    stems = {s: render_stem(s, "level1", ROOTS["level1"]) for s in STEMS}
    flat = {s: stems[s].tobytes() for s in STEMS}
    assert len(set(flat.values())) == len(STEMS)


def test_every_floor_sounds_different():
    for stem in ("pad", "arp", "lead"):
        sounds = {key: hash(render_stem(stem, key, ROOTS[key]).tobytes()) for key in THEMES}
        assert len(set(sounds.values())) == len(THEMES), stem


def test_stems_are_balanced_not_one_swamping_the_rest():
    peaks = {s: np.abs(render_stem(s, "level2", ROOTS["level2"])).max() for s in STEMS}
    assert max(peaks.values()) / min(peaks.values()) < 2.0
    assert all(p < 32767 * 0.6 for p in peaks.values())


def test_all_stems_together_cannot_clip_at_full_volume():
    total = sum(int(np.abs(render_stem(s, "level5", ROOTS["level5"])).max()) for s in STEMS)
    assert total * 0.5 < 32767                                # MASTER is 0.5


# --- pitch and rhythm are what the theme says -----------------------------------

def test_the_melody_starts_on_the_pitch_the_theme_writes():
    """Level 1's first melody note is scale degree 4 of A dorian, three octaves up (E5)."""
    root = ROOTS["level1"]
    first = THEMES["level1"].lead[0]
    want = hz(root, degree_semitones("dorian", first[2]) + 36)
    lead = mono(render_stem("lead", "level1", root))
    assert dominant_hz(lead, 0.30, 0.15) == pytest.approx(want, rel=0.03)


def test_the_pad_plays_the_chord_and_not_a_wrong_note():
    root = ROOTS["level1"]
    pad = mono(render_stem("pad", "level1", root))
    spb = 60 / THEMES["level1"].bpm
    for bar in range(4):
        degree = THEMES["level1"].progression[bar]
        start = bar * 4 * spb + 1.0 * spb                     # let the chord bloom
        for semis in chord_tones("dorian", degree)[:3]:
            on = band_energy(pad, start, spb, hz(root, semis + 24))
            off = band_energy(pad, start, spb, hz(root, semis + 24 + 0.5))   # a quarter-tone away
            assert on > 4 * off, (bar, semis)


def test_each_bar_has_its_own_chord():
    """The progression really moves: bar 0 and bar 1 carry different notes."""
    root = ROOTS["level1"]
    pad = mono(render_stem("pad", "level1", root))
    spb = 60 / THEMES["level1"].bpm
    third_of_bar0 = hz(root, chord_tones("dorian", 0)[1] + 24)
    start0, start1 = 1.0 * spb, 5.0 * spb
    assert band_energy(pad, start0, spb, third_of_bar0) > 3 * band_energy(pad, start1, spb, third_of_bar0)


def with_theme(monkeypatch, key, **changes):
    monkeypatch.setitem(THEMES, key, THEMES[key]._replace(**changes))


def beat_energy(signal, key, beat):
    spb = 60 / THEMES[key].bpm
    a = int(beat * spb * SAMPLE_RATE)
    return np.abs(signal[a:a + int(0.05 * SAMPLE_RATE)]).mean()


def test_a_four_on_the_floor_kick_hits_every_beat_and_a_half_kick_only_two(monkeypatch):
    """Compare each render with itself: stems are level-matched, so absolute loudness lies."""
    key = "level1"                                            # bass "pedal" rests on beats 1 and 3
    with_theme(monkeypatch, key, bass="pedal", hat=False, snare=False, kick="four")
    four = mono(render_stem("pulse", key, ROOTS[key]))
    with_theme(monkeypatch, key, kick="half")
    half = mono(render_stem("pulse", key, ROOTS[key]))
    for beat in (1, 3):
        assert beat_energy(four, key, beat) > 0.5 * beat_energy(four, key, 0)     # kick lands
        assert beat_energy(half, key, beat) < 0.2 * beat_energy(half, key, 0)     # silence
    for beat in (0, 2):
        assert beat_energy(half, key, beat) > 0.5 * beat_energy(half, key, 0)


def test_snare_and_hats_are_switchable(monkeypatch):
    key = "level2"
    with_theme(monkeypatch, key, kick="none", bass="pedal", hat=False, snare=False)
    plain = render_stem("pulse", key, ROOTS[key])
    with_theme(monkeypatch, key, snare=True)
    snare = render_stem("pulse", key, ROOTS[key])
    with_theme(monkeypatch, key, snare=False, hat=True)
    hats = render_stem("pulse", key, ROOTS[key])
    assert not np.array_equal(plain, snare) and not np.array_equal(plain, hats)
    assert not np.array_equal(snare, hats)


def count_arp_notes(monkeypatch, key, arp_div):
    with_theme(monkeypatch, key, arp_div=arp_div)
    calls = []
    monkeypatch.setattr(composer, "_pluck_note", lambda f, d: calls.append(f) or REAL_PLUCK(f, d))
    render_stem("arp", key, ROOTS[key])
    return calls


def test_arpeggio_density_follows_the_theme(monkeypatch):
    slow = count_arp_notes(monkeypatch, "level3", 2)
    fast = count_arp_notes(monkeypatch, "level3", 4)
    assert len(slow) == 16 * 2 and len(fast) == 16 * 4


def test_the_arpeggio_only_plays_notes_of_the_current_chord(monkeypatch):
    key = "level1"
    notes = count_arp_notes(monkeypatch, key, THEMES[key].arp_div)
    root, t = ROOTS[key], THEMES[key]
    per_bar = 4 * t.arp_div
    for bar, degree in enumerate(t.progression):
        allowed = [hz(root, s + 24) for s in chord_tones(t.mode, degree)]
        for freq in notes[bar * per_bar:(bar + 1) * per_bar]:
            assert any(freq == pytest.approx(a, rel=1e-9) for a in allowed), (bar, freq)


def test_the_melody_has_an_echo_that_rings_after_the_note_stops(monkeypatch):
    """Level 4's note ends at beat 3 and its release by ~3.35; beats 3.5-3.9 hold only the echo."""
    key = "level4"
    spb = 60 / THEMES[key].bpm

    def quiet_window_level(signal):
        a, b = int(3.5 * spb * SAMPLE_RATE), int(3.9 * spb * SAMPLE_RATE)
        return np.abs(signal[a:b]).mean() / np.abs(signal).max()

    with_echo = mono(render_stem("lead", key, ROOTS[key]))
    monkeypatch.setattr(composer, "_echo", lambda mix, delays, gains: mix)
    dry = mono(render_stem("lead", key, ROOTS[key]))
    assert quiet_window_level(dry) < 0.001
    assert quiet_window_level(with_echo) > 0.02


def test_stem_count_matches_the_player():
    from systems import music
    assert music.STEMS == composer.STEMS
    assert music.MUSIC_CHANNELS == 2 * len(composer.STEMS)


def test_rejects_unknown_input():
    with pytest.raises(ValueError):
        render_stem("kazoo", "level1", 55.0)
    with pytest.raises(ValueError):
        render_stem("pad", "level9", 55.0)


def test_voices_keep_to_their_own_registers():
    """Bass below the pad and arpeggio, melody above them."""
    assert (composer.BASS_OFFSET, composer.PAD_OFFSET, composer.ARP_OFFSET, composer.LEAD_OFFSET) \
        == (12, 24, 24, 36)
    assert composer.BASS_OFFSET < composer.PAD_OFFSET <= composer.ARP_OFFSET < composer.LEAD_OFFSET


def test_the_bass_plays_the_chord_root_an_octave_above_the_key_note(monkeypatch):
    """Level 1, bar 1: the bass note is A2 (110 Hz); the same bar one chord later is E2."""
    key = "level1"
    with_theme(monkeypatch, key, kick="none", hat=False, snare=False, bass="pedal")
    root = ROOTS[key]
    bass = mono(render_stem("pulse", key, root))
    spb = 60 / THEMES[key].bpm
    assert dominant_hz(bass, 0.02, 0.25) == pytest.approx(root * 2, rel=0.03)
    bar1_degree = THEMES[key].progression[1]               # degree 4: E in A dorian
    want = hz(root, degree_semitones("dorian", bar1_degree) + 12)
    assert dominant_hz(bass, 4 * spb + 0.02, 0.25) == pytest.approx(want, rel=0.03)
