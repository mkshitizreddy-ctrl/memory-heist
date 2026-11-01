"""Game feeds CommsFeed: radio lines appear in play without any level calling them."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.comms import line_for
from core.game import Game


@pytest.fixture
def game():
    pygame.init()
    g = Game()
    yield g
    g.music.stop()
    pygame.mixer.stop()
    pygame.mixer.set_reserved(0)


def frames(g, n):
    for _ in range(n):
        g.update(1 / 60)
        g.render()


def test_entering_play_shows_echo_line(game):
    game.state = "briefing"
    game.level_manager.current_name = "level2"
    frames(game, 3)
    assert game.comms.current is None                  # silent on the story card
    game._last_level_name = "level2"                   # the card has been dismissed
    game.state = "playing"
    frames(game, 5)
    assert game.comms.current is not None
    assert game.comms.current[0] == "Echo"
    assert game.comms.current[1].typer.text == line_for("level2", "enter")[1]


def test_security_rise_in_play_brings_warden(game):
    game.state = "playing"
    game.level_manager.current_name = "level1"
    frames(game, 5)
    game.comms.clear()
    game.security.level += 1
    frames(game, 3)
    assert game.comms.current is not None and game.comms.current[0] == "WARDEN"


def test_comms_clear_when_leaving_play_and_do_not_run_while_paused(game):
    game.state = "playing"
    game.level_manager.current_name = "level1"
    frames(game, 5)
    game.paused = True
    before = game.comms.current[1].typer.time
    frames(game, 30)
    assert game.comms.current[1].typer.time == before
    game.paused = False
    game.state = "lose"
    frames(game, 2)
    assert game.comms.current is None and game.comms.queue == []


def test_render_draws_comms_box_on_screen(game):
    game.state = "playing"
    game.level_manager.current_name = "level1"
    frames(game, 40)
    assert game.comms.current is not None
    game._bg_tick = 100                                # freeze the animated background
    game.render()
    with_box = game.screen.copy()
    game.comms.clear()
    game._bg_tick = 100
    game.render()
    h = game.screen.get_height()
    strip = pygame.Rect(16, h - 48, 700, 40)
    assert pygame.image.tostring(with_box.subsurface(strip), "RGB") != \
        pygame.image.tostring(game.screen.subsurface(strip), "RGB")
    top = pygame.Rect(0, 0, 960, h - 60)              # everything above is untouched
    assert pygame.image.tostring(with_box.subsurface(top), "RGB") == \
        pygame.image.tostring(game.screen.subsurface(top), "RGB")
