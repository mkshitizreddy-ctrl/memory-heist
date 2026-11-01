"""MEMORY_HEIST_NEW_FLOOR1=1 plays the reference floor in place of Level 1."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.game import Game
from levels.floor1_lobby import FloorOneLobby
from levels.level1 import Level1


@pytest.fixture(autouse=True)
def cleanup():
    pygame.init()
    yield
    pygame.mixer.stop()
    pygame.mixer.set_reserved(0)


def make(monkeypatch, flag):
    if flag is None:
        monkeypatch.delenv("MEMORY_HEIST_NEW_FLOOR1", raising=False)
    else:
        monkeypatch.setenv("MEMORY_HEIST_NEW_FLOOR1", flag)
    g = Game()
    return g


def test_default_still_uses_the_original_level_1(monkeypatch):
    g = make(monkeypatch, None)
    assert isinstance(g.level_manager.levels["level1"], Level1)
    g.music.stop()


def test_flag_swaps_in_the_reference_floor_only_when_exactly_1(monkeypatch):
    g = make(monkeypatch, "0")
    assert isinstance(g.level_manager.levels["level1"], Level1)
    g.music.stop()
    g = make(monkeypatch, "1")
    assert isinstance(g.level_manager.levels["level1"], FloorOneLobby)
    g.music.stop()


def test_reference_floor_runs_inside_the_real_game_loop(monkeypatch):
    g = make(monkeypatch, "1")
    g.story_enabled = False
    g.level_manager.start("level1")
    g._last_level_name = "level1"
    g.state = "playing"
    assert g._uses_spatial_player()
    for _ in range(120):
        g.update(1 / 60)
        g.render()
    assert g.state == "playing"
    floor = g.level_manager.current
    crate = floor.crates[0]
    g.player.rect.midtop = (crate.rect.centerx, crate.rect.bottom + 2)
    floor.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    assert floor.carried
    g.music.stop()


def test_wrong_sort_in_the_real_game_raises_security_and_warden_speaks(monkeypatch):
    g = make(monkeypatch, "1")
    g.story_enabled = False
    g.level_manager.start("level1")
    g._last_level_name = "level1"
    g.state = "playing"
    for _ in range(10):
        g.update(1 / 60)
    g.comms.clear()
    floor = g.level_manager.current
    c = floor.crates[0]
    wrong = next(t for t in floor.bins if t != c.answer)
    g.player.rect.midtop = (c.rect.centerx, c.rect.bottom + 2)
    floor.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    g.player.rect.midtop = (floor.bins[wrong].centerx, floor.bins[wrong].bottom + 2)
    floor.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    for _ in range(3):
        g.update(1 / 60)
    assert g.security.level > 0
    assert g.comms.current is not None and g.comms.current[0] == "WARDEN"
    g.music.stop()


def test_finishing_the_reference_floor_advances_to_level_2(monkeypatch):
    g = make(monkeypatch, "1")
    g.story_enabled = False
    g.level_manager.start("level1")
    g._last_level_name = "level1"
    g.state = "playing"
    g.level_manager.current.complete = True
    g.update(1 / 60)
    assert g.level_manager.current_name == "level2"
    g.music.stop()
