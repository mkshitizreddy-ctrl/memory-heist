"""Fixes from the 22 Nov play-through: Floor 1 spawn spacing, Floor 3 wrong-answer colour, Floor 3 lose tip."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest


@pytest.fixture(autouse=True)
def display():
    pygame.init()
    pygame.display.set_mode((960, 640))


def test_floor1_heroes_start_without_their_sprites_overlapping():
    from core.hero_sprites import make_hero_frames
    from levels.floor1_lobby import FloorOneLobby
    (x1, y1), (x2, y2) = FloorOneLobby().spawn_points
    tall = make_hero_frames("ghost")["idle"].get_height()
    ghost_feet = y1 + 32
    echo_head = y2 + 32 - tall
    assert x1 == x2 and echo_head >= ghost_feet


def test_floor3_wrong_answer_text_is_red_not_green():
    import levels.level3_loops as L
    src = open(L.__file__, encoding="utf-8").read()
    red_first = src.index('if "INCORRECT" in self.feedback:')
    green = src.index('"CORRECT" in self.feedback or "SUCCESSFUL"')
    assert red_first < green


def test_floor3_lose_tip_matches_the_laser_rooms_not_the_old_lanes():
    from ui.screens import LOSE_TIPS
    assert "lane" not in LOSE_TIPS["level3"].lower()
    assert "pad" in LOSE_TIPS["level3"]
