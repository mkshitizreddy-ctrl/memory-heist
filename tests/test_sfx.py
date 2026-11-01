"""Procedural sound effects and their use on Floor 1."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import numpy as np
import pygame
import pytest

from systems.audio import Audio
from systems.sfx import SAMPLE_RATE, SFX_NAMES, SFX_VOLUME, synth_sfx, to_int16_stereo
from tests.test_floor1_lobby import (carry, deliver, key, make_level, stand_by,
                                     wrong_bin, sort_all)


class Recorder:
    def __init__(self):
        self.played = []

    def play(self, name):
        self.played.append(name)


@pytest.fixture(autouse=True)
def display_init():
    pygame.init()
    yield
    pygame.mixer.stop()


@pytest.mark.parametrize("name", SFX_NAMES)
def test_waveform_is_bounded_nonsilent_and_short(name):
    wave = synth_sfx(name)
    assert wave.ndim == 1 and wave.size > 0
    assert wave.size / SAMPLE_RATE <= 0.6
    peak = float(np.max(np.abs(wave)))
    assert 0.05 < peak <= 1.0
    assert peak == pytest.approx(SFX_VOLUME[name], abs=0.02)
    assert np.all(np.isfinite(wave))


@pytest.mark.parametrize("name", SFX_NAMES)
def test_waveform_is_deterministic_and_starts_and_ends_quietly(name):
    a, b = synth_sfx(name), synth_sfx(name)
    assert np.array_equal(a, b)
    assert abs(a[0]) < 0.02 and abs(a[-1]) < 0.02          # no clicks


def test_effects_are_distinct():
    waves = [synth_sfx(n) for n in SFX_NAMES]
    for i in range(len(waves)):
        for j in range(i + 1, len(waves)):
            n = min(waves[i].size, waves[j].size)
            assert not np.allclose(waves[i][:n], waves[j][:n])


def test_pickup_rises_in_pitch_and_drop_falls():
    def zero_crossings(w):
        return int(np.sum(np.abs(np.diff(np.sign(w))) > 0))
    pick, drop = synth_sfx("pickup"), synth_sfx("drop")
    h = pick.size // 2
    assert zero_crossings(pick[h:]) > zero_crossings(pick[:h])
    h = drop.size // 2
    assert zero_crossings(drop[:h]) > zero_crossings(drop[h:])


def test_unknown_effect_raises():
    with pytest.raises(KeyError):
        synth_sfx("nope")


def test_stereo_conversion_is_int16_and_matches():
    pcm = to_int16_stereo(synth_sfx("step"))
    assert pcm.dtype == np.int16 and pcm.shape[1] == 2
    assert np.array_equal(pcm[:, 0], pcm[:, 1])


def test_audio_registers_the_generated_effects():
    audio = Audio(ambient=False)
    assert set(SFX_NAMES) <= set(audio.sounds)
    audio.play("pickup")                        # must not raise


# --- on Floor 1 ----------------------------------------------------------
def test_pickup_and_drop_play_their_sounds():
    level, game, player = make_level()
    game.audio = Recorder()
    crate = level.crates[0]
    carry(level, player, crate)
    assert game.audio.played == ["pickup"]
    player.rect.midtop = (480, 400)
    level.handle_event(key(pygame.K_e))
    assert game.audio.played == ["pickup", "drop"]


def test_failed_pickup_is_silent():
    level, game, player = make_level()
    game.audio = Recorder()
    player.rect.topleft = (60, 560)
    level.handle_event(key(pygame.K_e))
    assert game.audio.played == []


def test_footsteps_only_while_moving_at_a_steady_rate():
    level, game, player = make_level()
    game.audio = Recorder()
    player.moving = False
    for _ in range(20):
        level.update(0.05)
    assert game.audio.played == []
    player.moving = True
    for _ in range(40):                          # 2 seconds
        level.update(0.05)
    steps = game.audio.played.count("step")
    assert 4 <= steps <= 8


def test_door_sound_plays_once_when_the_exit_opens():
    level, game, player = make_level()
    game.audio = Recorder()
    sort_all(level, player, upto=6)
    for _ in range(60):
        level.update(0.05)
    assert game.audio.played.count("door") == 1


def test_level_works_without_audio():
    level, game, player = make_level()
    assert not hasattr(game, "audio")
    carry(level, player, level.crates[0])        # must not raise
