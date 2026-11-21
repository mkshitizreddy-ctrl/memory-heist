"""Playable airlock corridors between Level 3 rooms. Headless."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
import pygame
import test_level3_room3_core as C

pygame.init()
DT = 1 / 60


def start(room=1, coop=True):
    level, game = C.make3(coop=coop)
    level.current_checkpoint = room
    level.room = level.room_map.current
    level.barrier_walls = level.room.walls
    level.current_question_number = room - 1
    level.setup_room_hazards()
    level.load_current_question()
    gate = level.gates[room - 1]
    gate.unlock()
    gate.update(1.0)
    game.player.rect.topleft = (860, 250)
    game.player2.rect.topleft = (860, 320)
    level.update(DT)
    return level, game


def run_until(level, phase, limit=300):
    for _ in range(limit):
        if level._tx is None or level._tx["phase"] == phase:
            break
        level.update(DT)
    assert level._tx is not None and level._tx["phase"] == phase


def walk(level, dx=4, frames=1, who=None):
    for _ in range(frames):
        for rect in (who or level._player_rects()):
            moved = rect.move(dx, 0)
            if not level.room_map.blocked(moved):
                rect.topleft = moved.topleft
        level.update(DT)


def test_hand_in_then_player_control_inside_corridor():
    level, game = start()
    assert level._tx["phase"] == "in"
    assert level.room_map.blocked(pygame.Rect(300, 300, 32, 32)) is True
    run_until(level, "walk")
    assert level._tx["t"] == 0.0
    assert game.player.rect.topleft[0] == 92 and game.player2.rect.topleft[0] == 130
    # corridor floor is free to walk on once the hand-in has finished
    assert level.room_map.blocked(pygame.Rect(300, 300, 32, 32)) is False


def test_hand_in_and_out_last_about_0_4_seconds():
    assert abs(type(start()[0]).TX_IN - 0.4) < 1e-9
    assert abs(type(start()[0]).TX_OUT - 0.4) < 1e-9


def test_hazards_and_challenge_timer_paused_during_whole_walkthrough():
    level, game = start()
    snapshot = (level.laser_clock, level.time_left, level.robot_x, level.robot_y,
                level.core_state, level.core_timer)
    run_until(level, "walk")
    walk(level, frames=40)
    assert (level.laser_clock, level.time_left, level.robot_x, level.robot_y,
            level.core_state, level.core_timer) == snapshot


def test_entry_door_seals_only_after_both_players_inside():
    level, game = start()
    run_until(level, "walk")
    walk(level, frames=60, who=[game.player.rect])      # only player 1 walks
    assert game.player.rect.left >= level.CORR_INSIDE_X
    assert level._tx["entry"] == "open"
    walk(level, frames=40, who=[game.player2.rect])     # now player 2 follows
    for _ in range(40):
        level.update(DT)
    assert level._tx["entry"] == "sealed"


def test_exit_door_does_not_start_until_entry_sealed():
    level, game = start()
    run_until(level, "walk")
    game.player.rect.left = level.CORR_APPROACH_X
    game.player2.rect.left = level.CORR_INSIDE_X - 50   # not yet inside
    for _ in range(30):
        level.update(DT)
    assert level._tx["entry"] == "open" and level._tx["exit"] == "red"
    game.player2.rect.left = level.CORR_INSIDE_X
    states = []
    for _ in range(120):
        level.update(DT)
        states.append((level._tx["entry"], level._tx["exit"]))
    first_exit = next(i for i, s in enumerate(states) if s[1] != "red")
    assert states[first_exit][0] == "sealed"


def test_exit_door_blocks_until_open_and_handout_needs_both_players():
    level, game = start()
    run_until(level, "walk")
    game.player.rect.left = game.player2.rect.left = level.CORR_INSIDE_X + 20
    for _ in range(40):
        level.update(DT)
    assert level.room_map.blocked(pygame.Rect(level.CORR_EXIT.x, 280, 32, 32))
    game.player.rect.left = game.player2.rect.left = level.CORR_APPROACH_X
    for _ in range(80):
        level.update(DT)
    assert level._tx["exit"] == "open"
    game.player.rect.left = level.CORR_CLEAR_X + 10
    game.player2.rect.left = level.CORR_CLEAR_X - 80
    for _ in range(10):
        level.update(DT)
    assert level._tx["phase"] == "walk"
    game.player2.rect.left = level.CORR_CLEAR_X + 10
    level.update(DT)
    assert level._tx["phase"] == "out"


def test_full_corridor_ends_in_next_room_at_spawn_with_progress_kept():
    level, game = start()
    for _ in range(1500):
        if level._tx is None:
            break
        if level._tx["phase"] == "walk":
            walk(level)
        else:
            level.update(DT)
    assert level._tx is None and level.current_room_number() == 2
    assert game.player.rect.topleft == (80, 280)
    assert game.player2.rect.topleft == (118, 280)
    assert level.gate1.state != "locked" and level.current_question_number == 1
    assert level.room_map.blocked(pygame.Rect(180, 200, 32, 32)) is False


def test_corridor_cannot_be_walked_back_into_previous_room():
    level, game = start()
    run_until(level, "walk")
    walk(level, dx=-6, frames=60)
    assert game.player.rect.left >= level.CORR.left


def test_events_ignored_during_corridor():
    level, game = start()
    run_until(level, "walk")
    before = level.feedback
    level.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1))
    assert level.feedback == before


def test_both_players_must_reach_the_gate_first():
    level, game = C.make3(coop=True)
    level.current_checkpoint = 1
    level.room = level.room_map.current
    level.setup_room_hazards()
    level.gate1.unlock()
    level.gate1.update(1.0)
    game.player.rect.topleft = (860, 250)
    game.player2.rect.topleft = (500, 250)
    level.update(DT)
    assert level._tx is None and level.current_room_number() == 1


def test_second_corridor_has_its_own_identity_and_title():
    level, _ = start(2)
    assert level._tx["next_sector"] == 3
    assert level.CORR_TITLES[3] == "SECTOR 3 · CORE SECURITY"
    assert level.CORR_TITLES[2] == "SECTOR 2 · LASER CORRIDOR"
    assert level.CORR_PALETTE[2]["accent"] != level.CORR_PALETTE[3]["accent"]


def test_every_phase_renders_both_corridors_with_question_cover():
    for room in (1, 2):
        level, game = start(room)
        surf = pygame.Surface((960, 640))
        for phase in ("in", "walk"):
            run_until(level, phase)
            level.render(surf)
        walk(level, frames=200)
        level.render(surf)
        game.player.rect.left = game.player2.rect.left = level.CORR_CLEAR_X + 10
        for _ in range(40):
            level.update(DT)
            level.render(surf)


def test_coop_and_single_player_both_complete():
    for coop in (False, True):
        level, game = start(1, coop=coop)
        for _ in range(1500):
            if level._tx is None:
                break
            if level._tx["phase"] == "walk":
                walk(level)
            else:
                level.update(DT)
        assert level._tx is None and level.current_room_number() == 2
