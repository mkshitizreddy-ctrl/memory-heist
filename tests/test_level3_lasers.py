"""
tests/test_level3_lasers.py

Floor 3 hazard rules shared by every room (lanes, cameras): safe entry and
recovery windows, score-only hits applied once, and integration with the
game's lose / retry flow.  The make_level helper is reused by other test files.
"""

import os
import random
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.difficulty import get_difficulty
from levels import patrol_lanes
from levels.level3_loops import Level3LaserLoop
from systems.scoring import ScoreTracker


def make_level(room=1, player_at=(600, 520)):
    pygame.font.init()
    random.seed(3)

    events = []                       # score penalties taken

    def no_security(amount):
        raise AssertionError("a hazard must never raise security")

    score = ScoreTracker()
    original_penalize = score.penalize

    def penalize(amount):
        events.append(amount)
        original_penalize(amount)

    score.penalize = penalize
    game = SimpleNamespace(
        difficulty=get_difficulty("medium"),
        player=SimpleNamespace(rect=pygame.Rect(*player_at, 32, 32)),
        coop=False,
        security=SimpleNamespace(increase=no_security),
        score=score,
    )

    level = Level3LaserLoop(game=game)
    level.room_map.current_name = f"level3_room{room}"
    level.current_question_number = room - 1
    level.setup_room_hazards()
    level.load_current_question()
    level.robot_x = 700          # keep the robot clear of the test player

    return level, events


def hazard_clock(level):
    return (level.lane_loop or level.camera_bank).clock


@pytest.mark.parametrize("room", (1, 2, 3))
def test_room_entry_is_safe_for_the_whole_grace_period(room):
    level, events = make_level(room, player_at=(100, 446))
    player = level.game.player.rect

    for _ in range(int((patrol_lanes.GRACE - 0.05) * 60)):
        level.update(1 / 60)
        assert level.active_beam_rects() == []

    assert events.count(10) == 0                            # no hit
    assert level.game.score.get_score() >= 0


def test_only_live_lanes_hurt_and_a_hit_is_applied_once():
    level, events = make_level(1)
    level.game.score.add(100)
    lane = level.lane_loop
    player = level.game.player.rect
    player.topleft = (lane.rect(0).x + 10, 300)

    for clock in (0.0, patrol_lanes.GRACE - 0.3):           # nothing live, then warning
        lane.clock = clock
        level.laser_penalty_cooldown = 0.0
        level.check_laser_collision(0.0)
        assert lane.phase(0) != "active"
        assert events == []

    lane.clock = patrol_lanes.GRACE + 0.2                   # live
    level.check_laser_collision(0.0)

    assert events == [10]
    assert level.game.score.get_score() == 90
    assert level.feedback == "LASER HIT! SCORE -10"

    lane.clock = patrol_lanes.GRACE + 0.2                   # still overlapping
    level.check_laser_collision(0.0)
    assert events == [10]                                   # cooldown: no repeat hit


@pytest.mark.parametrize("room", (1, 3))
def test_a_hit_rearms_the_loop_giving_a_safe_recovery_window(room):
    level, events = make_level(room)
    lane = level.lane_loop
    lane.clock = patrol_lanes.GRACE + 0.2
    rect = lane.rect(0)
    level.game.player.rect.center = rect.center
    level.check_laser_collision(0.0)

    assert events == [10]
    assert lane.clock == 0.0
    assert level.active_beam_rects() == []


def test_clock_resets_when_entering_the_next_room():
    level, _ = make_level(1)
    level.gate1.unlock()
    level.gate1.update(level.gate1.SECONDS)
    level.game.player.rect.topleft = (860, 200)
    level.lane_loop.clock = 9.0
    level.update(1 / 60)

    assert level.room_map.current_name == "level3_room2"
    assert level.camera_bank.clock < 0.1


def skip_story(game):
    """Dismiss story cards (intro / briefing / outro) the way a player does:
    ESC skips a card. Does nothing when play has already started."""

    for _ in range(5):
        if game.state not in ("intro", "briefing", "outro"):
            break

        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        game.handle_events()


def test_lose_and_retry_start_level3_with_a_fresh_safe_hazard_loop():
    from core.game import Game

    game = Game()
    game.menu.selected_difficulty = "medium"
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    game.handle_events()
    skip_story(game)                      # ENTER opens the story intro first

    assert game.state == "playing"

    level = game.level_manager.levels["level3"]
    level.lane_loop.clock = 30.0
    game.security.level = game.security.max_level
    game.update(0.016)

    assert game.state == "lose"

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
    game.handle_events()
    skip_story(game)                      # a retry may show a story card too

    fresh = game.level_manager.levels["level3"]

    assert game.state == "playing"
    assert fresh is not level
    assert fresh.lane_loop.clock < 0.1
    assert fresh.active_beam_rects() == []
