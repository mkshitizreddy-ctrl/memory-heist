"""Room 3: approved layout, reactive core and CORE OVERRIDE terminal. Headless."""

import math
import os
import random
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.difficulty import get_difficulty
from levels.level3_loops import Level3LaserLoop as L

pygame.init()
pygame.display.set_mode((960, 640))


class Sec:
    def __init__(self):
        self.level = 0

    def increase(self, n):
        self.level += n


class Score:
    def __init__(self):
        self.value = 0

    def add(self, n):
        self.value += n

    def penalize(self, n):
        self.value -= n


def make3(difficulty="medium", coop=False):
    game = SimpleNamespace(
        player=SimpleNamespace(rect=pygame.Rect(80, 400, 32, 32)),
        player2=SimpleNamespace(rect=pygame.Rect(118, 400, 32, 32)),
        coop=coop, security=Sec(), score=Score(),
        difficulty=get_difficulty(difficulty), audio=None, state="playing")
    level = L(game=game)
    level.current_checkpoint = 3
    level.room = level.room_map.current
    level.barrier_walls = level.room.walls
    level.current_question_number = 2
    level.setup_room_hazards()
    level.load_current_question()
    return level, game


def step(level, seconds, dt=1 / 60):
    for _ in range(int(round(seconds / dt))):
        level.update(dt)


def to_state(level, state, limit=20.0):
    t = 0.0
    while level.core_state != state and t < limit:
        level.update(1 / 60)
        t += 1 / 60
    assert level.core_state == state
    return t


def go_near_core(level, game, dist=120):
    cx, cy = level._core_center()
    game.player.rect.center = (cx - dist, cy)


def at_terminal(game):
    game.player.rect.center = (310, 340)       # beside the console, clear of the core


# ---- layout ---------------------------------------------------------------

def test_layout_has_every_element_and_no_overlaps():
    level, _ = make3()
    axes = [laser.get("axis", "x") for laser in level.lasers]
    assert axes == ["x", "y", "r"]
    assert level.floor_zones == []
    core = level._core_laser()
    ring_edge = (core["cy"] + L.CORE_RING_MAX + L.CORE_RING_WIDTH / 2)
    lane = level.lasers[0]
    assert ring_edge < lane["y"] - level.RAIL_TOP_PAD          # ring never reaches the lane
    terminal = L.R3_TERMINAL_RECT
    d = math.hypot(terminal.right - core["cx"], terminal.centery - core["cy"])
    assert d - L.CORE_RING_MAX - L.CORE_RING_WIDTH / 2 >= 40    # >= 40 px clearance
    for pocket in level.safe_zones:
        assert level.room.bounds.contains(pocket)
        assert not pocket.colliderect(terminal)
        assert not pocket.colliderect(level.final_exit_rect)
    assert not terminal.colliderect(level.safe_zones[0])


def test_robot_patrols_a_short_top_line_and_never_enters_a_pocket():
    level, game = make3()
    game.player.rect.topleft = (80, 400)
    xs = []
    for _ in range(1200):
        level.update(1 / 60)
        xs.append(level.robot_x)
        r = pygame.Rect(int(level.robot_x), int(level.robot_y),
                        level.robot_width, level.robot_height)
        assert not any(r.colliderect(p) for p in level.safe_zones[1:])
    assert min(xs) >= 250 and max(xs) <= 620


def test_original_laser_start_times_are_preserved():
    level, _ = make3()
    starts = [L.LASER_ENTRY_GRACE + i * L.LASER_STAGGER + laser.get("phase_offset", 0.0)
              for i, laser in enumerate(level.lasers)]
    assert starts == pytest.approx([2.0, 5.0, 6.5])


def test_emitter_zone_and_sync_follow_the_new_lanes():
    level, _ = make3()
    emitter = level.emitters[0]
    assert tuple(emitter["trigger"]) == (640, 195, 170, 205)
    assert emitter["sync_lasers"] == (0, 1, 2)
    assert emitter["track_time"] > 0 and emitter["lock_time"] > 0


# ---- core -----------------------------------------------------------------

def test_core_state_sequence_has_a_warning_before_the_pulse():
    level, game = make3()
    go_near_core(level, game)
    seen = []
    for _ in range(60 * 14):
        level.update(1 / 60)
        if not seen or seen[-1] != level.core_state:
            seen.append(level.core_state)
        if "recovery" in seen:
            break
    assert seen[:5] == ["idle", "alert", "charge", "pulse", "recovery"] or \
        seen[:4] == ["alert", "charge", "pulse", "recovery"]


def test_ring_visual_and_collision_agree_and_hit_once_per_pulse():
    level, game = make3()
    go_near_core(level, game, 100)
    to_state(level, "pulse")
    cx, cy = level._core_center()
    game.player.rect.center = (cx - level.core_radius, cy)
    before = game.security.level
    level.laser_penalty_cooldown = 0.0
    level.check_laser_collision(0.0)
    assert game.security.level == before + 10
    level.laser_penalty_cooldown = 0.0
    level.check_laser_collision(0.0)
    assert game.security.level == before + 10       # once per player per pulse


def test_safe_pocket_is_immune_to_the_ring():
    level, game = make3()
    pocket = level.safe_zones[1]
    game.player.rect.center = pocket.center
    level.core_state = "pulse"
    level.core_radius = math.hypot(pocket.centerx - 520, pocket.centery - 285)
    assert not level._rect_touches_active_laser(game.player.rect) or \
        level.player_in_safe_pocket(game.player.rect)
    before = game.security.level
    level.check_laser_collision(0.0)
    assert game.security.level == before


def test_emitter_never_fires_while_the_core_charges_or_pulses():
    level, game = make3()
    level.core_state = "charge"
    assert not level._emitter_can_start(level.emitters[0])
    level.core_state = "pulse"
    assert not level._emitter_can_start(level.emitters[0])


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_difficulty_scales_the_core(difficulty):
    level, _ = make3(difficulty)
    assert level.core_difficulty == difficulty
    assert L.CORE_CHARGE["easy"] > L.CORE_CHARGE["hard"]
    assert L.CORE_COOLDOWN["easy"] > L.CORE_COOLDOWN["hard"]


# ---- terminal ---------------------------------------------------------------

def correct_index(level):
    return level.r3_term_question["correct"]


def test_terminal_needs_proximity_and_e_opens_it():
    level, game = make3()
    game.player.rect.topleft = (700, 400)
    level.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    assert not level.r3_term_open
    at_terminal(game)
    level.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))
    assert level.r3_term_open


def test_one_question_per_session_matching_the_difficulty():
    for difficulty in ("easy", "medium", "hard"):
        level, _ = make3(difficulty)
        assert level.r3_term_question["difficulty"] == difficulty
        first = level.r3_term_question
        level.update(1 / 60)
        assert level.r3_term_question is first


def test_bank_has_six_questions_two_per_difficulty():
    bank = L.R3_TERMINAL_BANK
    assert len(bank) == 6
    for difficulty in ("easy", "medium", "hard"):
        assert sum(q["difficulty"] == difficulty for q in bank) == 2
    for q in bank:
        assert 0 <= q["correct"] < len(q["options"]) == 4


def test_correct_answer_takes_the_core_offline_then_it_reboots():
    level, game = make3()
    at_terminal(game)
    level.r3_term_open = True
    level._r3_terminal_submit(correct_index(level))
    assert level.core_state == "offline" and level.r3_term_ok
    level.r3_term_open = False
    # No arm or ring damage while offline, even standing on the core.
    game.player.rect.center = level._core_center()
    level.laser_clock = 6.6                       # rotor window
    before = game.security.level
    step(level, 1.0)
    assert level.core_state == "offline"
    assert game.security.level == before
    angle = level._core_laser()["angle"]
    step(level, 1.0)
    assert level._core_laser()["angle"] == pytest.approx(angle, abs=2.0)  # no spin
    game.player.rect.topleft = (80, 400)
    step(level, L.R3_OFFLINE_TIME)
    assert level.core_state in ("idle", "alert")
    assert level.core_cooldown > 0 or level.core_state == "alert"


def test_wrong_answer_costs_security_and_score_and_keeps_the_core_on():
    level, game = make3()
    at_terminal(game)
    level.r3_term_open = True
    wrong = next(i for i in range(4) if i != correct_index(level))
    level._r3_terminal_submit(wrong)
    assert game.security.level == 5 and game.score.value == -5
    assert level.core_state != "offline" and not level.r3_term_ok
    level._r3_terminal_submit(wrong)            # repeating a wrong pick costs nothing more
    assert game.security.level == 5


def test_timer_robot_and_core_hold_while_the_console_is_open():
    level, game = make3()
    at_terminal(game)
    level.r3_term_open = True
    t0, rx = level.time_left, level.robot_x
    cd = level.core_cooldown
    step(level, 1.0)
    assert level.time_left == pytest.approx(t0)
    assert level.robot_x == rx
    assert level.core_cooldown == cd


def test_console_closes_by_itself_when_you_walk_away():
    level, game = make3()
    at_terminal(game)
    level.r3_term_open = True
    game.player.rect.topleft = (700, 400)
    level.update(1 / 60)
    assert not level.r3_term_open


def test_number_keys_go_to_the_console_not_the_main_question():
    level, game = make3()
    at_terminal(game)
    level.r3_term_open = True
    q = level.current_question_number
    level.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1))
    assert level.current_question_number == q


def test_room_2_terminal_state_is_untouched_by_room_3():
    level, game = make3()
    assert level.room2_override_panel_open is False
    assert level.room2_override_solved is False
    level.r3_term_open = True
    level._r3_terminal_submit(correct_index(level))
    assert level.room2_override_solved is False
    assert level.room2_robot_disabled_timer == 0


# ---- rendering ------------------------------------------------------------

@pytest.mark.parametrize("state", ["idle", "alert", "charge", "pulse", "recovery", "offline"])
def test_all_core_states_and_the_console_render(state):
    level, game = make3()
    level.core_state = state
    level.core_timer = 1.0
    level.r3_term_open = state == "offline"
    surface = pygame.Surface((960, 640))
    level.render(surface)
