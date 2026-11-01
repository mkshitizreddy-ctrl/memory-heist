"""The pause screen must not rebuild its font and overlay on every frame."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.game import Game


@pytest.fixture
def game():
    g = Game()
    g._start_new_run()
    return g


@pytest.fixture
def font_calls(monkeypatch):
    """Records every pygame.font.Font() call made while a test runs."""
    calls = []
    real_font = pygame.font.Font

    def counting_font(*args, **kwargs):
        calls.append(args)
        return real_font(*args, **kwargs)

    monkeypatch.setattr(pygame.font, "Font", counting_font)
    return calls


def test_pause_screen_creates_no_fonts_after_its_first_frame(game, font_calls):
    game.paused = True
    game.render()  # the first paused frame may create the font and overlay
    del font_calls[:]

    game.render()
    game.render()
    game.render()

    assert font_calls == []


def test_pause_overlay_and_font_are_reused(game):
    first = game._get_pause_assets()
    second = game._get_pause_assets()

    assert first is second
