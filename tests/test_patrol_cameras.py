"""Floor 3, Room 2: the camera gallery (levels/patrol_cameras.py)."""

import math

import pygame
import pytest

from levels import patrol_cameras as C
from tests.test_level3_lasers import make_level


def aim(bank, index, point_below=200):
    """Freeze a camera pointing straight down; return a rect directly in its cone."""
    bank.speed = 0.0
    bank.clock = C.GRACE + 1
    x, _ = bank.mount(index)
    return pygame.Rect(x - 16, C.MOUNT_Y + point_below, 32, 32)


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_cameras_look_away_during_the_entry_grace(difficulty):
    bank = C.CameraBank(difficulty)
    rect = pygame.Rect(0, 0, 32, 32)
    for index in range(len(bank.cameras)):
        rect.midtop = (bank.mount(index)[0], C.MOUNT_Y + 100)
        bank.clock = 0.0
        for _ in range(int((C.GRACE - 0.05) * 60)):
            assert bank.update(1 / 60, [rect]) is None


def test_standing_in_a_cone_is_spotted_after_a_short_dwell_not_instantly():
    bank = C.CameraBank("medium")
    rect = aim(bank, 0)
    assert bank.update(1 / 60, [rect]) is None                 # one frame is not enough
    spotted = []
    for _ in range(45):
        result = bank.update(1 / 60, [rect])
        if result is not None:
            spotted.append(result)
    assert spotted == [0]


def test_a_player_outside_every_cone_is_never_spotted():
    bank = C.CameraBank("hard")
    rect = aim(bank, 0)
    rect.x = 60                                                  # far left, behind every cone
    rect.y = 440
    bank.speed = 0.0
    for _ in range(300):
        assert bank.update(1 / 60, [rect]) is None


def test_cone_edges_match_the_detection_test():
    bank = C.CameraBank("medium")
    aim(bank, 0)
    mx, my = bank.mount(0)
    inside = (mx + 20, my + 200)
    outside = (mx + 200, my + 200)
    assert bank.inside(0, inside) and not bank.inside(0, outside)
    assert not bank.inside(0, (mx, my - 10))                     # nothing above the mount
    assert not bank.inside(0, (mx, my + C.CONE_LENGTH + 10))     # nothing beyond its reach


def test_switching_off_stops_detection():
    bank = C.CameraBank("medium")
    rect = aim(bank, 0)
    bank.switch_off()
    for _ in range(120):
        assert bank.update(1 / 60, [rect]) is None


def test_room_two_uses_cameras_and_a_sighting_costs_score_only():
    level, events = make_level(2)
    assert level.camera_bank is not None and level.lasers == [] and level.lane_loop is None
    level.game.score.add(100)
    rect = aim(level.camera_bank, 0)
    level.game.player.rect.topleft = rect.topleft
    for _ in range(90):
        level.check_laser_collision(1 / 60)
    assert events == [10]                                        # one hit; the cooldown stops a repeat
    assert level.camera_bank.clock < C.GRACE                     # re-armed: cameras look away again


def test_opening_the_gate_switches_the_cameras_off():
    level, events = make_level(2)
    level.gate2.unlock()
    level.gate2.update(2.0)
    level.check_laser_collision(1 / 60)
    assert level.camera_bank.on is False


def test_cone_amplitude_keeps_every_cone_over_the_floor():
    bank = C.CameraBank("hard")
    for index, (x, amplitude, period, phase) in enumerate(bank.cameras):
        assert amplitude + bank.half < 75                         # a cone never points sideways along the wall
