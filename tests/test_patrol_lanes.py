"""Floor 3, Room 1: the four-lane loop (levels/patrol_lanes.py)."""

import pygame
import pytest

from levels import patrol_lanes as L
from tests.test_level3_lasers import make_level


def run_to(loop, seconds, dt=1 / 60):
    for _ in range(int(seconds / dt)):
        loop.update(dt)


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_nothing_fires_during_the_entry_grace(difficulty):
    loop = L.LaneLoop(difficulty)
    for _ in range(int((L.GRACE - 0.05) * 60)):
        loop.update(1 / 60)
        assert loop.active_rects() == []


@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
def test_lanes_fire_in_order_and_every_lane_warns_first(difficulty):
    loop = L.LaneLoop(difficulty)
    seen, previous = [], {}
    for _ in range(int((loop.cycle + L.GRACE) * 60)):
        loop.update(1 / 60)
        for lane, phase in enumerate(loop.phases()):
            if previous.get(lane) == "off" and phase == "active":
                raise AssertionError("a lane fired without a warning")
            if previous.get(lane) != "active" and phase == "active":
                seen.append(lane)
            previous[lane] = phase
    assert seen[:4] == [0, 1, 2, 3]


def test_the_loop_rests_and_never_has_every_lane_live():
    loop = L.LaneLoop("hard")
    rested = False
    for _ in range(int(loop.cycle * 2 * 60)):
        loop.update(1 / 60)
        assert len(loop.active_rects()) < L.COLUMN_COUNT
        rested |= loop.resting()
    assert rested


def test_a_hit_rearms_the_loop_with_a_fresh_grace():
    loop = L.LaneLoop("medium")
    run_to(loop, 5.0)
    loop.rearm()
    assert loop.clock == 0.0 and loop.active_rects() == []


def test_lanes_span_the_room_so_there_is_no_walking_round_them():
    loop = L.LaneLoop()
    for lane in range(L.COLUMN_COUNT):
        rect = loop.rect(lane)
        assert rect.top <= 170 and rect.bottom >= 460          # wall's foot to the question panel


def test_room_one_uses_the_lane_loop_and_a_live_lane_hurts_score_only():
    level, events = make_level(1)
    assert level.lane_loop is not None and level.camera_bank is None
    lane = level.lane_loop
    level.game.score.add(100)
    lane.clock = L.GRACE + 0.1                                  # lane 0 live
    rect = lane.rect(0)
    level.game.player.rect.topleft = (rect.x + 10, 300)
    level.check_laser_collision(0.0)
    assert events == [10]
    assert lane.clock == 0.0                                    # re-armed


def test_each_room_uses_its_own_hazard():
    one, _ = make_level(1)
    two, _ = make_level(2)
    three, _ = make_level(3)
    assert one.lane_loop.layout == "columns" and one.lane_loop.count == 4 and one.camera_bank is None
    assert two.lane_loop is None and two.camera_bank is not None
    assert three.lane_loop.layout == "rows" and three.lane_loop.count == 3 and three.camera_bank is None


def test_room_three_rows_sit_between_the_walls_and_below_the_door():
    loop = L.LaneLoop("medium", "rows")
    for rect in loop.rects:
        assert rect.left == 64 and rect.right == 846           # wall to wall: no walking round them
        assert rect.top > 300                                   # the door's opening ends at y 300: every route crosses a row
        assert rect.bottom <= 446                               # the spawn row stays clear



def test_the_room_one_guard_paces_between_lanes_never_through_one():
    from levels import patrol_decor as P

    loop = L.LaneLoop()
    route = P.GUARD_ROUTES[1]
    lap = pygame.Rect(route[0][0], route[0][1], route[1][0] - route[0][0] + 32, 32)
    for lane in range(L.COLUMN_COUNT):
        assert not lap.colliderect(loop.rect(lane).inflate(12, 0))


def test_a_player_can_wait_between_two_rows():
    loop = L.LaneLoop("medium", "rows")
    for upper, lower in zip(loop.rects, loop.rects[1:]):
        assert lower.top - upper.bottom >= 32 + 6               # a 32 px player fits with room to spare
