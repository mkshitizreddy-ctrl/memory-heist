"""The NovaCorp sound pack: every effect has the character its name promises."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import numpy as np
import pytest

from systems.sfx import SAMPLE_RATE, SFX_NAMES, SFX_VOLUME, synth_sfx
from tools import sound_test

NEW = ("bell", "vending", "chip", "alarm", "switch", "zap", "drone", "laser",
       "stamp", "chime", "fanfare", "step_metal", "step_server", "step_marble")


def crossings(w):
    return int(np.sum(np.abs(np.diff(np.sign(w))) > 0))


def rate(w):
    """Zero crossings per second: a stand-in for pitch."""
    return crossings(w) * SAMPLE_RATE / max(1, w.size)


def window(name, start, stop):
    w = synth_sfx(name)
    return w[int(start * SAMPLE_RATE):int(stop * SAMPLE_RATE)]


def test_names_and_volumes_line_up_with_no_duplicates():
    assert len(set(SFX_NAMES)) == len(SFX_NAMES)
    assert set(SFX_VOLUME) == set(SFX_NAMES)
    assert set(NEW) <= set(SFX_NAMES) and SFX_NAMES[:4] == ("pickup", "drop", "step", "door")


def test_the_bell_rings_at_its_main_pitch():
    w = synth_sfx("bell")
    spectrum = np.abs(np.fft.rfft(w))
    peak = np.fft.rfftfreq(w.size, 1 / SAMPLE_RATE)[int(np.argmax(spectrum))]
    assert abs(peak - 1760) < 40


def test_chip_and_fanfare_rise_and_laser_falls():
    chip = synth_sfx("chip")
    h = chip.size // 2
    assert crossings(chip[h:]) > crossings(chip[:h])
    assert rate(window("chip", 0.035, 0.065)) > rate(window("chip", 0.0, 0.03)) * 1.02    # each blip rises
    assert rate(window("chip", 0.13, 0.16)) > rate(window("chip", 0.08, 0.11)) * 1.05
    assert rate(window("fanfare", 0.0, 0.1)) < rate(window("fanfare", 0.23, 0.33))
    laser = synth_sfx("laser")
    h = laser.size // 2
    assert crossings(laser[:h]) > crossings(laser[h:])


def test_the_alarm_alternates_between_two_pitches():
    seg = [rate(window("alarm", i / 8, (i + 1) / 8)) for i in range(4)]
    assert seg[0] > seg[1] * 1.15 and seg[2] > seg[1] * 1.15 and seg[0] == pytest.approx(seg[2], rel=0.1)


def test_the_chime_is_two_notes_the_second_lower():
    first, second = rate(window("chime", 0.05, 0.25)), rate(window("chime", 0.35, 0.55))
    assert first > second * 1.15


def test_the_drone_swells_and_fades():
    w = synth_sfx("drone")
    third = w.size // 3
    mid = np.abs(w[third:2 * third]).mean()
    assert mid > 3 * np.abs(w[:third // 4]).mean() and mid > 3 * np.abs(w[-third // 4:]).mean()


def test_the_switch_clicks_before_it_clunks():
    w = synth_sfx("switch")
    early = rate(w[:int(0.04 * SAMPLE_RATE)])
    late = rate(w[int(0.08 * SAMPLE_RATE):])
    assert early > late * 3


def test_the_three_footsteps_sound_different():
    metal, server, marble = (synth_sfx(n) for n in ("step_metal", "step_server", "step_marble"))
    assert rate(metal) > rate(server) * 2                   # bright steel against a muffled floor
    assert marble.size > server.size and marble.size > metal.size
    tail = lambda w: np.abs(w[int(0.065 * SAMPLE_RATE):]).max()
    assert tail(marble) > 5 * tail(server)                  # the marble echo


def test_the_zap_is_noisy_and_the_stamp_is_low():
    zap, stamp = synth_sfx("zap"), synth_sfx("stamp")
    assert rate(zap) > rate(stamp) * 3
    assert np.abs(stamp[:int(0.05 * SAMPLE_RATE)]).max() > 0.5
    assert rate(window("stamp", 0, 0.05)) < 900              # a low thud, not a zing


def test_the_vending_machine_has_a_second_thunk():
    w = synth_sfx("vending")
    a = np.abs(w[int(0.12 * SAMPLE_RATE):int(0.19 * SAMPLE_RATE)]).max()
    b = np.abs(w[int(0.2 * SAMPLE_RATE):int(0.27 * SAMPLE_RATE)]).max()
    assert b > a


# --- the listening script ------------------------------------------------
def test_sound_test_lists_every_effect_without_playing(capsys):
    assert sound_test.main(play=False) == 0
    out = capsys.readouterr().out
    assert all(name in out for name in SFX_NAMES)


def test_sound_test_plays_the_chosen_effects_in_order(capsys):
    waits = []
    assert sound_test.main(["bell", "zap"], wait=waits.append) == 0
    out = capsys.readouterr().out
    assert out.index("bell") < out.index("zap") and "stamp" not in out
    assert len(waits) == 2 and waits[0] == pytest.approx(sound_test.length_of("bell") + 0.6)


def test_sound_test_rejects_unknown_names(capsys):
    assert sound_test.main(["nope"], play=False) == 1
    assert "Unknown effect" in capsys.readouterr().out
