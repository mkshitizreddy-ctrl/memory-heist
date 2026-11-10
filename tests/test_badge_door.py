"""
tests/test_badge_door.py

The shared sliding badge door: its sequence (locked, scan, slide, open), that it draws
differently at each step, and that each floor drives it from its own logic.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from levels import badge_door
from levels.level3_loops import PatrolGate
from tests.test_level3_lasers import make_level

DOOR = pygame.Rect(60, 40, 28, 120)


def paint(progress):
    surface = pygame.Surface((160, 220))
    surface.fill((0, 0, 0))
    badge_door.draw_badge_door(surface, DOOR, progress, 1.0)
    return pygame.image.tostring(surface, "RGB")


def test_sequence_runs_locked_scanning_opening_open():
    assert badge_door.state(0.0) == "locked"
    assert badge_door.state(badge_door.SCAN_END / 2) == "scanning"
    assert badge_door.state(badge_door.SCAN_END + 0.1) == "opening"
    assert badge_door.state(1.0) == "open"


def test_leaves_stay_shut_while_the_reader_scans_then_slide_apart():
    assert badge_door.slide_amount(0.0) == 0.0
    assert badge_door.slide_amount(badge_door.SCAN_END) == 0.0
    middle = badge_door.slide_amount(0.7)
    assert 0.0 < middle < 1.0
    assert badge_door.slide_amount(1.0) == 1.0


def test_the_lamp_goes_red_amber_green():
    assert badge_door.lamp_colour(0.0) == badge_door.LOCKED
    assert badge_door.lamp_colour(0.2) == badge_door.SCANNING
    assert badge_door.lamp_colour(0.8) == badge_door.GRANTED


def test_every_step_looks_different_and_the_door_opens_to_a_dark_gap():
    frames = [paint(p) for p in (0.0, 0.2, 0.7, 1.0)]
    assert len(set(frames)) == 4

    surface = pygame.Surface((160, 220))
    badge_door.draw_badge_door(surface, DOOR, 1.0, 0.0)
    middle = surface.get_at(DOOR.center)[:3]
    assert sum(middle) < 200                         # no steel left in the middle of the opening


def test_drawing_leaves_the_clip_rect_alone():
    surface = pygame.Surface((160, 220))
    clip = pygame.Rect(5, 5, 100, 100)
    surface.set_clip(clip)
    badge_door.draw_badge_door(surface, DOOR, 0.6, 0.0)
    assert surface.get_clip() == clip


def test_the_reader_is_beside_the_door_on_the_approach_side():
    reader = badge_door.reader_rect(DOOR)
    assert reader.right < DOOR.left and reader.centery == DOOR.centery


def test_floor3_gate_scans_then_slides_and_stays_solid_until_done():
    gate = PatrolGate(850, 180, width=20, height=120)
    assert gate.progress == 0.0
    gate.unlock()
    assert 0.0 < gate.progress < 0.01
    assert gate.blocks(pygame.Rect(850, 200, 10, 10))
    gate.update(gate.SECONDS * 0.7)
    assert badge_door.state(gate.progress) == "opening" and gate.blocks(pygame.Rect(850, 200, 10, 10))
    gate.update(gate.SECONDS)
    assert gate.progress == 1.0 and gate.is_open()
    assert not gate.blocks(pygame.Rect(850, 200, 10, 10))


def test_floor3_renders_the_badge_door_in_every_gate_state():
    level, _ = make_level(1)
    surface = pygame.Surface((960, 640))
    level.render(surface)
    level.gate1.unlock()
    level.gate1.update(0.3)
    level.render(surface)
    level.gate1.update(2.0)
    level.render(surface)
    assert level.gate1.is_open()


def test_floor2_exit_door_runs_on_a_linear_clock():
    from tests.test_grid_room import QS, answer, make_room, set_pool

    room, _, player = make_room()
    set_pool(room, QS)
    for label in ("42", "True", "False"):
        answer(room, player, label)
    room.update(0.3)
    first = room.gate_open[2]
    room.update(0.3)
    second = room.gate_open[2]
    assert second - first == pytest.approx(first - 0.0, rel=0.4)     # same step each tick, not an ease
    for _ in range(120):
        room.update(1 / 60)
    assert room.gate_open[2] == 1.0
