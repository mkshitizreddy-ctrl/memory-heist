"""
tests/test_floor_strip.py

The badges screen's floor strip: the deepest floor cleared is saved with the other
stats, never goes down, is recorded as the game moves past each floor, and the six
chips sit between the badges and the back button.
"""

import os
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.level_manager import LEVEL_ORDER, LevelManager
from systems.achievements import FLOOR_COUNT, FLOOR_SHORT_NAMES, Stats
from ui.stats_screen import StatsScreen


@pytest.fixture(autouse=True)
def display_init():
    pygame.init()
    pygame.display.set_mode((960, 640))


def test_there_is_one_chip_name_per_floor():
    assert FLOOR_COUNT == len(LEVEL_ORDER) == len(FLOOR_SHORT_NAMES)


def test_the_deepest_floor_is_saved_and_never_goes_down(tmp_path):
    path = tmp_path / "stats.json"
    stats = Stats(path)
    assert stats.deepest == 0
    stats.record_floor(3)
    stats.record_floor(1)
    assert stats.deepest == 3
    stats.record_floor(99)
    assert stats.deepest == FLOOR_COUNT
    assert Stats(path).deepest == FLOOR_COUNT


def test_an_old_stats_file_without_the_field_reads_as_zero(tmp_path):
    path = tmp_path / "stats.json"
    path.write_text('{"wins": 2, "badges": ["escape"]}', encoding="utf-8")
    stats = Stats(path)
    assert stats.deepest == 0 and stats.wins == 2


def test_moving_past_a_floor_records_it(tmp_path):
    stats = Stats(tmp_path / "stats.json")
    game = SimpleNamespace(stats=stats, change_state=lambda s: None)
    manager = LevelManager(game)
    for name in LEVEL_ORDER:
        manager.register(name, SimpleNamespace(is_complete=lambda: False, update=lambda dt: None))
    manager.start("level3")
    manager._advance()
    assert stats.deepest == 3 and manager.current_name == "level4"


def test_the_strip_sits_between_the_badges_and_the_back_button():
    lay = StatsScreen().layout(960)
    chips = lay["floors"]
    assert len(chips) == FLOOR_COUNT
    assert chips[0].top - 24 > lay["cells"][-1].bottom
    assert chips[0].bottom < lay["back"].top
    assert all(lay["panel"].contains(c) for c in chips)
    assert all(a.right < b.left for a, b in zip(chips, chips[1:]))


@pytest.mark.parametrize("deepest", [0, 3, FLOOR_COUNT])
def test_the_screen_draws_any_progress(tmp_path, deepest):
    stats = Stats(tmp_path / "stats.json")
    stats.deepest = deepest
    StatsScreen().render(pygame.Surface((960, 640)), stats, 10)
