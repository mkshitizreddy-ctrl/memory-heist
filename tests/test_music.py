import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import threading

import numpy as np
import pygame
import pytest

from core.level_manager import LEVEL_ORDER
from systems import composer, music
from systems.music import (FLOOR_ROOTS, STEMS, MusicPlayer, approach, key_for,
                           mix_for, next_key, synth_stem)

KEYS = list(FLOOR_ROOTS) + ["menu"]

pytestmark = pytest.mark.real_music


class FakeAudio:
    def __init__(self, ready=True):
        self.mixer_ready = ready
        self.enabled = True


@pytest.fixture
def mixer():
    pygame.mixer.pre_init(44100, -16, 2)
    pygame.mixer.init(frequency=44100, size=-16, channels=2)
    pygame.mixer.stop()
    yield
    pygame.mixer.stop()
    pygame.mixer.set_reserved(0)


def test_every_level_has_a_root_and_they_rise():
    roots = [FLOOR_ROOTS[n] for n in LEVEL_ORDER]
    assert roots == sorted(roots) and len(set(roots)) == len(roots)


def test_calm_screens_have_no_drive_and_no_alarm():
    for state in ("menu", "intro", "outro", "win"):
        mix = mix_for(state, "level3", 1.0)
        assert mix == {"pad": 0.8, "pulse": 0.0, "arp": 0.35, "lead": 0.45, "alert": 0.0}
        assert key_for(state, "level3") == "menu"


def test_every_stem_has_a_volume_in_every_state():
    for state in ("menu", "playing", "lose", "briefing"):
        for level in LEVEL_ORDER:
            assert set(mix_for(state, level, 0.5)) == set(STEMS)


def test_the_melody_gives_way_to_the_alert_as_the_meter_rises():
    leads = [mix_for("playing", "level3", a)["lead"] for a in (0, .25, .5, .75, 1)]
    assert leads[0] > 0 and leads == sorted(leads, reverse=True) and leads[-1] == 0.0


def test_arpeggio_thins_under_alert_but_never_vanishes():
    calm = mix_for("playing", "level3", 0.0)["arp"]
    tense = mix_for("playing", "level3", 1.0)["arp"]
    assert 0 < tense < calm


def test_pulse_grows_with_depth_alert_follows_meter():
    pulses = [mix_for("playing", n, 0.0)["pulse"] for n in LEVEL_ORDER]
    assert pulses == sorted(pulses) and pulses[-1] > pulses[0]
    alerts = [mix_for("playing", "level2", a)["alert"] for a in (0, .25, .5, .75, 1)]
    assert alerts[0] == 0 and alerts == sorted(alerts) and alerts[-1] == 1.0


def test_lose_is_all_alert_and_input_clamped():
    m = mix_for("lose", "level4", 0.0)
    assert m["alert"] == 1.0 and m["pulse"] == 0.0 and m["pad"] < 0.5
    assert m["lead"] == 0.0 and m["arp"] == 0.0
    assert mix_for("playing", "level1", 9)["alert"] == 1.0
    assert mix_for("playing", "level1", -9)["alert"] == 0.0


def test_unknown_level_treated_calm():
    assert mix_for("playing", "nope", 1.0)["alert"] == 0.0
    assert key_for("playing", "nope") == "menu"


def test_approach_never_overshoots():
    assert approach(0.0, 1.0, 0.3) == pytest.approx(0.3)
    assert approach(0.9, 1.0, 0.3) == 1.0
    assert approach(1.0, 0.0, 0.3) == pytest.approx(0.7)
    assert approach(0.1, 0.0, 0.3) == 0.0


@pytest.mark.parametrize("stem", STEMS)
@pytest.mark.parametrize("key", ["menu", "level1", "final_vault"])
def test_stem_is_stereo_int16_correct_length_and_loud_enough(stem, key):
    data = synth_stem(stem, key)
    assert data.dtype == np.int16 and data.shape == (composer.loop_samples(key), 2)
    assert np.abs(data).max() > 2000
    assert np.abs(data).max() < 32767


@pytest.mark.parametrize("stem", STEMS)
@pytest.mark.parametrize("key", KEYS)
def test_stem_loops_without_a_click(stem, key):
    d = synth_stem(stem, key)[:, 0].astype(float)
    jump = abs(d[0] - d[-1])
    typical = np.abs(np.diff(d)).max()
    assert jump <= typical * 1.5 + 1


def test_unknown_stem_rejected():
    with pytest.raises(ValueError):
        synth_stem("kazoo", "level1")


def test_unknown_floor_rejected():
    with pytest.raises(ValueError):
        synth_stem("pad", "level9")


def test_every_floor_has_a_theme_and_a_root():
    assert set(KEYS) == set(composer.THEMES)


def test_next_floor_follows_the_building_and_menu_leads_to_the_first():
    assert next_key("menu") == LEVEL_ORDER[0]
    assert [next_key(n) for n in LEVEL_ORDER[:-1]] == list(LEVEL_ORDER[1:])
    assert next_key(LEVEL_ORDER[-1]) is None and next_key("nope") is None


def test_player_inert_without_mixer():
    p = MusicPlayer(FakeAudio(ready=False))
    p.update(0.1, "playing", "level1", 0.5)
    assert p.voices == [] and p.key is None


def test_player_starts_every_stem_and_fades_in(mixer):
    p = MusicPlayer(FakeAudio())
    p.update(0.0, "playing", "level2", 0.0)
    assert p.key == "level2" and {v.stem for v in p.voices} == set(STEMS)
    assert all(v.volume == 0 for v in p.voices)
    for _ in range(120):
        p.update(1 / 60, "playing", "level2", 0.0)
    vol = {v.stem: v.volume for v in p.voices}
    assert vol["pad"] == pytest.approx(0.8 * music.MASTER)
    assert vol["alert"] == 0.0 and vol["pulse"] > 0
    assert vol["arp"] > 0 and vol["lead"] == pytest.approx(0.6 * music.MASTER)


def test_player_alert_swells_with_security(mixer):
    p = MusicPlayer(FakeAudio())
    for _ in range(200):
        p.update(1 / 60, "playing", "level3", 1.0)
    assert {v.stem: v.volume for v in p.voices}["alert"] == pytest.approx(music.MASTER)


def test_floor_change_crossfades_and_retires_old_voices(mixer):
    p = MusicPlayer(FakeAudio())
    for _ in range(120):
        p.update(1 / 60, "playing", "level1", 0.0)
    p.update(1 / 60, "playing", "level2", 0.0)
    keys = {v.key for v in p.voices}
    assert keys == {"level1", "level2"}              # both audible mid-fade
    for _ in range(300):
        p.update(1 / 60, "playing", "level2", 0.0)
    assert {v.key for v in p.voices} == {"level2"}
    assert len(p.voices) == len(STEMS)


def test_mute_fades_to_silence_and_back(mixer):
    a = FakeAudio()
    p = MusicPlayer(a)
    for _ in range(120):
        p.update(1 / 60, "playing", "level1", 0.5)
    a.enabled = False
    for _ in range(300):
        p.update(1 / 60, "playing", "level1", 0.5)
    assert all(v.volume == 0 for v in p.voices)
    a.enabled = True
    for _ in range(300):
        p.update(1 / 60, "playing", "level1", 0.5)
    assert any(v.volume > 0 for v in p.voices)


def test_stop_clears_everything(mixer):
    p = MusicPlayer(FakeAudio())
    p.update(0.0, "menu", "", 0.0)
    p.stop()
    assert p.voices == [] and p.key is None


def test_music_uses_reserved_channels_and_effects_cannot_steal_them(mixer):
    p = MusicPlayer(FakeAudio())
    p.update(0.0, "playing", "level1", 0.0)
    assert sorted(v.index for v in p.voices) == list(range(len(STEMS)))
    for _ in range(10):                      # a hectic level's effects, after
        pygame.mixer.Sound(buffer=bytes(4000)).play(loops=-1)
    assert all(v.channel.get_busy() for v in p.voices)
    assert pygame.mixer.get_num_channels() >= music.TOTAL_CHANNELS


def test_music_survives_ambient_loops_filling_default_channels(mixer):
    for _ in range(8):                       # what leftover looping sounds do
        pygame.mixer.Sound(buffer=bytes(4000)).play(loops=-1)
    p = MusicPlayer(FakeAudio())
    p.update(0.0, "playing", "level2", 0.0)
    assert {v.stem for v in p.voices} == set(STEMS)


def test_crossfade_never_needs_more_than_reserved_channels(mixer):
    p = MusicPlayer(FakeAudio())
    for _ in range(60):
        p.update(1 / 60, "playing", "level1", 0.5)
    p.update(1 / 60, "playing", "level2", 0.5)
    assert len(p.voices) == 2 * len(STEMS)
    assert len({v.index for v in p.voices}) == 2 * len(STEMS)
    assert all(v.index < music.MUSIC_CHANNELS for v in p.voices)


def test_music_starting_never_cuts_off_a_playing_effect(mixer):
    p = MusicPlayer(FakeAudio())             # reserves channels before any effect
    sounds = [pygame.mixer.Sound(buffer=bytes(40000)) for _ in range(8)]
    playing = [snd.play(loops=-1) for snd in sounds]
    assert all(c is not None for c in playing)
    p.update(0.0, "playing", "level1", 0.0)  # music starts now
    assert all(c.get_sound() is snd for c, snd in zip(playing, sounds))


# --- rendering ahead and memory ------------------------------------------------

def test_next_floor_is_prepared_in_the_background(mixer):
    p = MusicPlayer(FakeAudio())
    p.update(0.0, "playing", "level1", 0.0)
    p.wait_for_prefetch()
    assert {stem for (key, stem) in p._arrays if key == "level2"} == set(STEMS)


def test_arriving_on_a_prepared_floor_does_not_synthesise_on_the_spot(mixer, monkeypatch):
    p = MusicPlayer(FakeAudio())
    p.update(0.0, "playing", "level1", 0.0)
    p.wait_for_prefetch()

    real = music.synth_stem

    def boom(stem, key):
        if threading.current_thread() is threading.main_thread():
            raise AssertionError("synthesised on the main thread")
        return real(stem, key)               # the background thread may still work ahead

    monkeypatch.setattr(music, "synth_stem", boom)
    p.update(1 / 60, "playing", "level2", 0.0)
    assert p.key == "level2" and {v.key for v in p.voices} == {"level2"}
    assert len(p.voices) == len(STEMS)
    p.wait_for_prefetch()


def test_an_unprepared_floor_still_plays(mixer):
    p = MusicPlayer(FakeAudio())
    p.update(0.0, "playing", "level1", 0.0)
    p.update(1 / 60, "playing", "level4", 0.0)        # skipped ahead
    assert p.key == "level4" and {v.key for v in p.voices} == {"level4"}
    assert len(p.voices) == len(STEMS)


def test_only_nearby_floors_are_kept_in_memory(mixer):
    p = MusicPlayer(FakeAudio())
    for name in ("level1", "level2", "level3", "level4"):
        p.update(0.0, "playing", name, 0.0)
        p.wait_for_prefetch()
    held = {key for key, _ in list(p._sounds) + list(p._arrays)}
    assert held <= {"level3", "level4", "level5"}
    assert "level1" not in held


def test_prefetch_never_runs_twice_for_the_same_floor(mixer):
    p = MusicPlayer(FakeAudio())
    p.prefetch("level2")
    p.prefetch("level2")
    p.wait_for_prefetch()
    assert len(p._threads) == 1
