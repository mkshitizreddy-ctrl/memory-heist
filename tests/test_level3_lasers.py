"""
tests/test_level3_lasers.py

Phase 2 laser mechanics: the warning -> active -> off cycle, safe entry and
recovery windows, active-only collisions, unchanged beam movement, and
integration with the game's lose / retry flow.
"""

import os
import random
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.difficulty import get_difficulty
from levels.level3_loops import Level3LaserLoop
from systems.scoring import ScoreTracker

BEAM_RED = (255, 45, 45)
AMBER = (255, 190, 60)


def make_level(room=1, player_at=(600, 520)):
    pygame.font.init()
    random.seed(3)

    events = []
    game = SimpleNamespace(
        difficulty=get_difficulty("medium"),
        player=SimpleNamespace(rect=pygame.Rect(*player_at, 32, 32)),
        coop=False,
        security=SimpleNamespace(increase=lambda amount: events.append(amount)),
        score=ScoreTracker(),
    )

    level = Level3LaserLoop(game=game)
    level.room_map.current_name = f"level3_room{room}"
    level.current_question_number = room - 1
    level.setup_room_hazards()
    level.load_current_question()
    level.robot_x = 700          # keep the robot clear of the test player

    return level, events


def phases(level, index, seconds=40.0, step=0.01):
    runs = []

    for tick in range(int(seconds / step)):
        level.laser_clock = tick * step
        phase = level.laser_phase(index)

        if runs and runs[-1][0] == phase:
            runs[-1][1] += step
        else:
            runs.append([phase, step])

    return runs


@pytest.mark.parametrize("room", (1, 2, 3))
def test_every_laser_follows_warning_active_off_with_fair_timing(room):
    level, _ = make_level(room)
    allowed = {("off", "warning"), ("warning", "active"), ("active", "off")}

    for index in range(len(level.lasers)):
        runs = phases(level, index)

        assert runs[0][0] == "off"

        for (before, _), (after, _) in zip(runs, runs[1:]):
            assert (before, after) in allowed            # never fires unwarned

        for phase, length in runs[1:-1]:
            if phase == "warning":
                assert length == pytest.approx(level.LASER_WARN, abs=0.03)
            elif phase == "active":
                assert length == pytest.approx(level.LASER_ON, abs=0.03)
            else:
                assert length >= level.LASER_OFF - 0.03

        first_active = next(
            i for i, (phase, _) in enumerate(runs) if phase == "active"
        )
        before_first = sum(length for _, length in runs[:first_active])

        assert before_first >= level.LASER_ENTRY_GRACE - 0.03


def test_cycle_is_deterministic():
    level, _ = make_level(3)

    assert phases(level, 1) == phases(level, 1)
    assert phases(level, 0) != phases(level, 2)          # lasers are staggered


@pytest.mark.parametrize(
    "room, spawn",
    [(1, (100, 100)), (2, (100, 350)), (2, (136, 350)), (3, (100, 350))],
)
def test_room_entry_is_safe_for_the_whole_grace_period(room, spawn):
    level, events = make_level(room, player_at=spawn)
    player = level.game.player.rect
    overlapped = False

    for _ in range(int((level.LASER_ENTRY_GRACE - 0.05) * 60)):
        level.update(1 / 60)
        overlapped |= any(
            pygame.Rect(int(l["x"]), int(l["y"]), level.laser_width, level.laser_height)
            .colliderect(player)
            for l in level.lasers
        )

    assert events.count(10) == 0                          # no laser hit
    assert level.game.score.get_score() >= 0

    if (room, spawn) == (2, (100, 350)):
        # The old always-on rule would have hit this spawn point.
        assert overlapped


def test_a_player_in_the_beam_path_is_still_punished_after_the_grace_period():
    level, events = make_level(2, player_at=(100, 350))
    player = level.game.player.rect

    for _ in range(60 * 8):
        beam = level.lasers[1]
        player.topleft = (int(beam["x"]) + 10, int(beam["y"]) - 8)
        level.update(1 / 60)

    assert events.count(10) >= 1


def test_only_active_beams_hurt_and_a_hit_is_applied_once():
    level, events = make_level(1)
    level.game.score.add(100)
    player = level.game.player.rect
    laser = level.lasers[0]
    player.topleft = (int(laser["x"]) + 10, int(laser["y"]) - 8)

    for clock in (0.0, level.LASER_ENTRY_GRACE - 0.5):    # off, then warning
        level.laser_clock = clock
        level.laser_penalty_cooldown = 0.0
        level.check_laser_collision(0.0)

        assert level.laser_phase(0) != "active"
        assert events == []

    level.laser_clock = level.LASER_ENTRY_GRACE + 0.5      # active
    level.check_laser_collision(0.0)

    assert level.laser_phase(0) == "active" or events == [10]
    assert events == [10]
    assert level.game.score.get_score() == 90
    assert level.feedback == "LASER HIT! SECURITY +10"

    level.laser_clock = level.LASER_ENTRY_GRACE + 0.5      # still overlapping
    level.check_laser_collision(0.0)

    assert events == [10]                                  # cooldown: no repeat hit


def test_a_hit_rearms_every_laser_giving_a_safe_recovery_window():
    level, events = make_level(3)
    level.laser_clock = 50.0
    beam = level.lasers[0]
    level.game.player.rect.topleft = (int(beam["x"]) + 10, int(beam["y"]) - 8)
    level.lasers[0]["x"] = float(level.game.player.rect.x)
    level.laser_phase = Level3LaserLoop.laser_phase.__get__(level)

    for clock in range(0, 4000, 5):                        # find an active moment
        level.laser_clock = clock / 100
        if level.laser_phase(0) == "active":
            break

    level.check_laser_collision(0.0)

    assert events == [10]
    assert level.laser_clock == 0.0
    assert all(level.laser_phase(i) == "off" for i in range(len(level.lasers)))

    level.laser_clock = level.LASER_ENTRY_GRACE - 0.01
    assert not any(level.laser_phase(i) == "active" for i in range(len(level.lasers)))


def test_beam_movement_does_not_depend_on_the_cycle_phase():
    first, _ = make_level(3)
    second, _ = make_level(3)

    for step in range(600):
        second.laser_clock = (step * 0.37) % 11.0          # scramble the phase
        first.update(1 / 60)
        second.update(1 / 60)

        assert [l["x"] for l in first.lasers] == [l["x"] for l in second.lasers]
        assert [l["direction"] for l in first.lasers] == [l["direction"] for l in second.lasers]


def test_clock_resets_when_entering_the_next_room():
    level, _ = make_level(1)
    level.gate1.unlock()
    level.gate1.update(1.0)
    level.game.player.rect.topleft = (860, 200)
    level.laser_clock = 9.0
    level.update(1 / 60)

    assert level.room_map.current_name == "level3_room2"
    assert level.laser_clock == 0.0


@pytest.mark.parametrize("phase", ("off", "warning", "active"))
def test_phases_look_different_and_only_active_uses_the_danger_colour(phase, monkeypatch):
    level, _ = make_level(1)
    level.laser_phase = lambda index: phase
    monkeypatch.setattr(level, "_seconds", lambda: 0.0)    # fixed flicker frame
    surface = pygame.Surface((960, 640))
    level.render(surface)

    laser = level.lasers[0]
    colours = {
        tuple(surface.get_at((x, y)))[:3]
        for x in range(int(laser["x"]), int(laser["x"]) + level.laser_width, 3)
        for y in range(int(laser["y"]), int(laser["y"]) + level.laser_height)
    }

    assert (BEAM_RED in colours) == (phase == "active")
    assert (AMBER in colours) == (phase == "warning")


def skip_story(game):
    """Dismiss story cards (intro / briefing / outro) the way a player does:
    ESC skips a card. Does nothing when play has already started."""

    for _ in range(5):
        if game.state not in ("intro", "briefing", "outro"):
            break

        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        game.handle_events()


def test_lose_and_retry_start_level3_with_fresh_safe_lasers():
    from core.game import Game

    game = Game()
    game.menu.selected_difficulty = "medium"
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
    game.handle_events()
    skip_story(game)                      # ENTER opens the story intro first

    assert game.state == "playing"

    level = game.level_manager.levels["level3"]
    level.laser_clock = 30.0
    game.security.level = game.security.max_level
    game.update(0.016)

    assert game.state == "lose"

    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
    game.handle_events()
    skip_story(game)                      # a retry may show a story card too

    fresh = game.level_manager.levels["level3"]

    assert game.state == "playing"
    assert fresh is not level
    assert fresh.laser_clock == 0.0
    assert all(fresh.laser_phase(i) == "off" for i in range(len(fresh.lasers)))