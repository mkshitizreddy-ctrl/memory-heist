"""Fonts must be created once, not on every frame (Font() costs ~2 ms)."""

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


def show(game, name):
    game.level_manager.start(name)
    game._last_level_name = name  # no level-change fade
    game._fade_timer = 0.0


@pytest.mark.parametrize("name", ["level4", "final_vault"])
def test_level_creates_no_fonts_after_its_first_frame(game, font_calls, name):
    show(game, name)
    game.render()  # the first frame may create them
    del font_calls[:]

    game.render()
    game.render()
    game.render()

    assert font_calls == []


def test_pause_screen_creates_nothing_after_its_first_frame(game, font_calls):
    game.paused = True
    game.render()  # the first paused frame may create the font and overlay
    del font_calls[:]

    game.render()
    game.render()
    game.render()

    assert font_calls == []
