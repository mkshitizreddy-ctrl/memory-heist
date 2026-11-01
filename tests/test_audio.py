"""Tests for systems/audio.py."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from systems.audio import Audio

SOUND_NAMES = {"correct", "wrong", "unlock", "click"}


def test_sound_effects_load_from_any_working_directory(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    audio = Audio()

    assert audio.enabled
    assert SOUND_NAMES <= set(audio.sounds)
