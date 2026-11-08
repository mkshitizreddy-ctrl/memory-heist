"""Floor 1 (the reception lobby) is Level 1; MEMORY_HEIST_OLD_LEVEL1=1 brings back the old one."""

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


def make(monkeypatch, old_level1=None):
    """A game; `old_level1` is the value of MEMORY_HEIST_OLD_LEVEL1 (None = unset)."""
    if old_level1 is None:
        monkeypatch.delenv("MEMORY_HEIST_OLD_LEVEL1", raising=False)
    else:
        monkeypatch.setenv("MEMORY_HEIST_OLD_LEVEL1", old_level1)
    return Game()


def test_default_level_1_is_the_reception_lobby(monkeypatch):
    g = make(monkeypatch)
    assert isinstance(g.level_manager.levels["level1"], FloorOneLobby)
    g.music.stop()


def test_the_old_level_1_comes_back_only_when_the_switch_is_exactly_1(monkeypatch):
    for value in ("0", "", "true", "yes"):
        g = make(monkeypatch, value)
        assert isinstance(g.level_manager.levels["level1"], FloorOneLobby), value
        g.music.stop()
    g = make(monkeypatch, "1")
    assert isinstance(g.level_manager.levels["level1"], Level1)
    g.music.stop()


def test_reference_floor_runs_inside_the_real_game_loop(monkeypatch):
    g = make(monkeypatch)
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
    g = make(monkeypatch)
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
    g = make(monkeypatch)
    g.story_enabled = False
    g.level_manager.start("level1")
    g._last_level_name = "level1"
    g.state = "playing"
    g.level_manager.current.complete = True
    g.update(1 / 60)
    assert g.level_manager.current_name == "level2"
    g.music.stop()


def test_the_level_1_briefing_describes_the_lobby_not_the_old_gate():
    from core.story import beat_for
    beat = beat_for("level1")
    text = " ".join([beat["title"], *beat["lines"]]).lower()
    assert "lobby" in beat["title"].lower() and "parcel" in text and "chute" in text
    assert "gate checks" not in text and "clearance" not in text
    assert beat["concept"] == "Data types"
