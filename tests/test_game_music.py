"""Game drives the adaptive music: floor keys, alert from security, no old drone."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.game import Game
from systems import music
from systems.audio import Audio


@pytest.fixture
def game():
    pygame.init()
    g = Game()
    yield g
    g.music.stop()
    pygame.mixer.stop()
    pygame.mixer.set_reserved(0)


def vols(g):
    return {(v.key, v.stem): v.volume for v in g.music.voices}


def run(g, seconds=3.0):
    for _ in range(int(seconds * 60)):
        g.update(1 / 60)


def test_old_drone_is_gone_but_effects_still_load(game):
    assert game.audio.ambient_channel is None
    assert set(game.audio.sounds) == {"correct", "wrong", "unlock", "click"}


def test_audio_default_still_starts_drone_for_other_callers():
    a = Audio()
    assert a.ambient_channel is not None or not a.enabled
    pygame.mixer.stop()


def test_menu_plays_calm_pad_only(game):
    run(game)
    v = vols(game)
    assert game.music.key == "menu"
    assert v[("menu", "pad")] > 0
    assert v[("menu", "pulse")] == 0 and v[("menu", "alert")] == 0


def test_playing_level_uses_its_floor_key_with_pulse(game):
    game.state = "playing"
    game.level_manager.current_name = "level3"
    run(game)
    assert game.music.key == "level3"
    assert vols(game)[("level3", "pulse")] > 0


def test_security_rise_swells_alert_layer(game):
    game.state = "playing"
    game.level_manager.current_name = "level2"
    run(game)
    quiet = vols(game)[("level2", "alert")]
    game.security.level = game.security.max_level
    run(game)
    assert vols(game)[("level2", "alert")] > quiet


def test_losing_goes_full_alert(game):
    game.state = "lose"
    game.level_manager.current_name = "level4"
    run(game)
    v = vols(game)
    assert v[("level4", "alert")] == pytest.approx(music.MASTER)
    assert v[("level4", "pulse")] == 0
