"""Fixes from the fresh review: wrong tips, colours, stale radio, names, readable text."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest


@pytest.fixture(autouse=True)
def display():
    pygame.init()
    pygame.display.set_mode((960, 640))


def test_floor2_tip_says_true_panels_zap():
    from ui.screens import LOSE_TIPS
    assert "True zap" in LOSE_TIPS["level2"] and "False" not in LOSE_TIPS["level2"]


def test_progress_drops_stale_radio_lines():
    from ui.comms import CommsFeed
    f = CommsFeed(cooldown=0.0)
    f.observe("playing", "level2", 0, 10, 0)
    f.update(0.0)                                   # the intro is now on air
    f.observe("playing", "level2", 2, 10, 0)        # a mistake line queues
    assert any(f.queue)
    f.observe("playing", "level2", 2, 10, 1)        # ...then the crew opens a relay
    assert len(f.queue) <= 1                        # only the progress line is waiting


def test_names_say_floor_everywhere():
    from core.story import STORY
    from ui.hud import LEVEL_LABELS
    assert LEVEL_LABELS["level3"] == "Floor 3 of 6" and LEVEL_LABELS["final_vault"] == "Final floor"
    titles = [v["title"] for v in STORY.values() if isinstance(v, dict) and "title" in v]
    assert titles and not any(t.startswith("LEVEL") for t in titles)


def test_new_run_starts_on_floor1_spawn():
    from core.game import Game
    g = Game()
    g._start_new_run()
    spawn = g.level_manager.current.spawn_points[0]
    assert (g.player.rect.x, g.player.rect.y) == tuple(spawn)
    assert not g.level_manager.current.room_map.blocked(g.player.rect)


def test_long_final_answer_gets_a_wide_plate():
    from levels import core_decor as C
    narrow = C.plate_rect(5, 0)
    wide = C.plate_rect(5, 0, "ZeroDivisionError")
    assert wide.center == narrow.center and wide.w > narrow.w
    from ui.fonts import code_font
    assert code_font(C.PLATE_FONT).size("ZeroDivisionError")[0] <= wide.w - 6


def test_audio_is_quiet_on_start(capsys):
    from systems.audio import Audio
    Audio(ambient=False)
    assert "Looking for sounds" not in capsys.readouterr().out
