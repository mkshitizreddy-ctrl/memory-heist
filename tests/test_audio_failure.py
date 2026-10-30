"""Audio must stay usable (and silent) when the mixer cannot start."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from systems.audio import Audio


@pytest.fixture
def audio_without_mixer(monkeypatch):
    """An Audio built on a machine where pygame.mixer.init() fails."""

    def fail(*args, **kwargs):
        raise pygame.error("no audio device")

    monkeypatch.setattr(pygame.mixer, "init", fail)
    return Audio()


def test_failed_mixer_init_leaves_audio_disabled(audio_without_mixer):
    assert audio_without_mixer.enabled is False


def test_toggle_without_a_mixer_does_not_crash_or_enable(audio_without_mixer):
    audio_without_mixer.toggle()

    assert audio_without_mixer.enabled is False


def test_play_without_a_mixer_is_silent(audio_without_mixer):
    audio_without_mixer.play("correct")
