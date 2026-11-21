"""Integration checks for the three-room Laser Loop progression."""

from types import SimpleNamespace
import math

import pygame
import pytest

from core.difficulty import get_difficulty
from levels.level3_loops import Level3LaserLoop
from systems.scoring import ScoreTracker


def make_level(coop=False):
    pygame.font.init()
    game = SimpleNamespace(
        difficulty=get_difficulty("medium"),
        score=ScoreTracker(),
        security=SimpleNamespace(increase=lambda _amount: None),
        player=SimpleNamespace(rect=pygame.Rect(100, 250, 32, 32)),
        coop=coop,
    )
    if coop:
        game.player2 = SimpleNamespace(rect=pygame.Rect(140, 250, 32, 32))
    level = Level3LaserLoop(game=game)
    level.room_requests.pop(1, None)     # pad geometry: every pad lit (board choice: test_level3_board_loops.py)
    level.setup_room_hazards()
    return level


def test_level_has_three_distinct_rooms_and_sequential_gate_exits():
    level = make_level()
    assert len(level.room_map.rooms) == 3
    assert level.current_room_number() == 1
    assert level.room.bounds == pygame.Rect(40, 150, 880, 300)
    assert [len(room.gates) for room in level.rooms] == [1, 1, 1]
    assert [gate.rect.x for gate in level.gates] == [850, 850, 850]
    assert [exit_data[0] for exit_data in level.room_map.exits] == list(level.room_names[:2])


def test_locked_gate_and_bulkheads_block_bypass_but_open_gate_passes():
    level = make_level()
    gate = level.gate1
    aperture = pygame.Rect(gate.rect.x, gate.rect.y + 20, 32, 32)
    assert level.room_map.blocked(aperture)
    assert level.room_map.blocked(pygame.Rect(gate.rect.x, 160, 32, 32))
    assert level.room_map.blocked(pygame.Rect(gate.rect.x, 435, 32, 12))
    assert level.room_map.blocked(pygame.Rect(20, 250, 32, 32))
    gate.unlock()
    gate.update(1.0)
    assert not level.room_map.blocked(aperture)


def finish_gate_walkthrough(level):
    """Walk every player through the airlock corridor to the next room."""
    for _ in range(1500):
        tx = level._tx
        if tx is None:
            break
        if tx["phase"] == "walk":
            for rect in level._player_rects():
                moved = rect.move(4, 0)
                if not level.room_map.blocked(moved):
                    rect.topleft = moved.topleft
        level.update(1 / 60)
    assert level._tx is None


def test_checkpoint_progression_uses_open_gates_and_finishes_at_exit():
    level = make_level()
    for checkpoint, gate in enumerate(level.gates, start=1):
        assert level.current_checkpoint == checkpoint
        gate.unlock()
        gate.update(1.0)
        level.game.player.rect.topleft = (860, 250)
        level.try_room_transition()
        if checkpoint < 3:
            assert level.current_checkpoint == checkpoint + 1
            assert level.room_map.current_name == level.room_names[checkpoint]
            assert level.current_question["room"] == checkpoint + 1
            finish_gate_walkthrough(level)
            assert level.game.player.rect.topleft == (80, 280)
    assert level.is_complete()


def test_each_checkpoint_unlocks_its_own_gate():
    level = make_level()
    for checkpoint, gate in enumerate(level.gates, start=1):
        level.current_checkpoint = checkpoint
        if checkpoint == 2:
            level.room2_gate_challenge_survived = True
        level.unlock_current_gate()
        assert gate.state == "unlocking" or gate.is_open()


def test_room2_gate_waits_for_the_clean_emitter_cycle_after_question_answer():
    level = make_level()
    level.current_checkpoint = 2
    level.setup_room_hazards()

    level.unlock_current_gate()
    assert level.gate2.state == "locked"
    assert level.room2_gate_question_solved

    emitter = level.emitters[0]
    emitter.update({"state": "active", "timer": 0.01})
    level.room2_gate_challenge_armed = True
    level._update_emitters(0.02)

    assert level.room2_gate_challenge_survived
    assert level.gate2.state == "unlocking"


def test_room2_override_modal_does_not_make_players_invulnerable():
    level = make_level()
    level.current_checkpoint = 2
    level.setup_room_hazards()
    level.room2_override_panel_open = True
    level.laser_phase = lambda _index: "active"
    level._laser_rect = lambda _laser: level.game.player.rect.copy()
    events = []
    level.game.security.increase = events.append

    level.check_laser_collision(0.0)

    assert events == [10]


def test_room2_gate_emitter_hit_cancels_clean_cycle_progress():
    level = make_level()
    level.current_checkpoint = 2
    level.setup_room_hazards()
    emitter = level.emitters[0]
    emitter["state"] = "active"
    level.room2_gate_challenge_armed = True
    level.laser_phase = lambda _index: "off"
    level._emitter_beam_hits_rect = lambda _emitter, _rect: True

    level.check_laser_collision(0.0)

    assert not level.room2_gate_challenge_armed
    assert not level.room2_gate_challenge_survived


def test_room2_emitter_hit_during_penalty_cooldown_still_cancels_clean_cycle():
    level = make_level()
    level.current_checkpoint = 2
    level.setup_room_hazards()
    emitter = level.emitters[0]
    emitter["state"] = "active"
    level.room2_gate_challenge_armed = True
    level.laser_penalty_cooldown = 0.5
    level._emitter_beam_hits_rect = lambda _emitter, _rect: True

    level.check_laser_collision(0.1)

    assert not level.room2_gate_challenge_armed
    assert level.laser_penalty_cooldown == pytest.approx(0.4)


def test_room2_wrong_terminal_answer_does_not_reveal_the_answer():
    level = make_level()
    level._select_session_override_question()
    assert level.room2_override_question is not None
    correct = level.room2_override_question["options"].index(
        level.room2_override_question["answer"])

    level._submit_room2_override_answer((correct + 1) % 4)

    assert "Correct answer" not in level.room2_override_feedback
    assert level.room2_override_feedback.startswith("Incorrect.")


def test_room2_override_questions_load_from_shared_puzzle_data():
    level = make_level()

    assert len(level.room2_override_pool) == 6
    assert {difficulty: sum(item["difficulty"] == difficulty
                            for item in level.room2_override_pool)
            for difficulty in ("easy", "medium", "hard")} == {
                "easy": 2, "medium": 2, "hard": 2}
    assert not any(item.get("category") == "override"
                   for item in level.room_question_pools[2])


def test_coop_room_transition_waits_for_both_players_and_spawns_together():
    level = make_level(coop=True)
    level.gate1.unlock()
    level.gate1.update(1.0)
    level.game.player.rect.topleft = (860, 250)
    level.game.player2.rect.topleft = (500, 250)
    level.try_room_transition()
    assert level.current_room_number() == 1
    level.game.player2.rect.topleft = (860, 300)
    level.try_room_transition()
    assert level.current_room_number() == 2
    finish_gate_walkthrough(level)
    assert level.game.player.rect.topleft == (80, 280)
    assert level.game.player2.rect.topleft == (118, 280)


def test_safe_zone_requires_full_rectangle_containment():
    level = make_level()
    pocket = level.safe_zones[0]
    fully_inside = pygame.Rect(pocket.left + 4, pocket.top + 4, 32, 32)
    partial = pygame.Rect(pocket.left - 8, pocket.top + 4, 32, 32)
    assert level.player_in_safe_pocket(fully_inside)
    assert not level.player_in_safe_pocket(partial)


def test_room1_has_three_reachable_safe_spaces_and_other_rooms_keep_their_layout():
    level = make_level()
    expected = [pygame.Rect(80, 386, 140, 54),
                pygame.Rect(265, 162, 132, 52),
                pygame.Rect(650, 384, 136, 52)]
    assert level.safe_zones == expected
    for pocket in level.safe_zones:
        assert level.room.bounds.contains(pocket)
        player = pygame.Rect(pocket.centerx - 16, pocket.centery - 16, 32, 32)
        assert pocket.contains(player)
        assert not level.room_map.blocked(player)

    level.current_checkpoint = 2
    level.setup_room_hazards()
    assert level.safe_zones == [pygame.Rect(80, 386, 140, 54)]
    level.current_checkpoint = 3
    level.setup_room_hazards()
    # Room 3 keeps its start bay and gained the right-hand rest pocket.
    assert level.safe_zones == [pygame.Rect(80, 386, 140, 54),
                                pygame.Rect(668, 332, 70, 46)]


@pytest.mark.parametrize("space_index", (0, 1, 2))
def test_each_room1_safe_space_protects_from_tracking_beam(space_index):
    level = make_level()
    pocket = level.safe_zones[space_index]
    player = pygame.Rect(pocket.centerx - 16, pocket.centery - 16, 32, 32)
    level.game.player.rect = player
    emitter = level.emitters[0]
    emitter["state"] = "active"
    emitter["angle"] = math.degrees(math.atan2(
        player.centery - emitter["origin"][1],
        player.centerx - emitter["origin"][0]))
    level.laser_phase = lambda _index: "off"
    level.floor_zone_phase = lambda _index: "off"
    events = []
    level.game.security.increase = events.append

    assert level.player_in_safe_pocket(player)
    assert level._emitter_beam_hits_rect(emitter, player)
    level.check_laser_collision(0.0)
    assert events == []


def test_room1_safe_protection_is_independent_for_coop_players():
    level = make_level(coop=True)
    pocket = level.safe_zones[1]
    level.game.player.rect.topleft = (pocket.centerx - 16, pocket.centery - 16)
    level.game.player2.rect.topleft = (600, 284)
    emitter = level.emitters[0]
    emitter["state"] = "active"
    emitter["angle"] = math.degrees(math.atan2(
        level.game.player2.rect.centery - emitter["origin"][1],
        level.game.player2.rect.centerx - emitter["origin"][0]))
    level.laser_phase = lambda _index: "off"
    level.floor_zone_phase = lambda _index: "off"
    events = []
    level.game.security.increase = events.append

    assert level.player_in_safe_pocket(level.game.player.rect)
    assert not level.player_in_safe_pocket(level.game.player2.rect)
    level.check_laser_collision(0.0)
    assert events == [10]


@pytest.mark.parametrize("space_index", (0, 1, 2))
def test_room1_safe_spaces_do_not_hide_rotating_laser_damage(space_index):
    level = make_level()
    pocket = level.safe_zones[space_index]
    level.game.player.rect.topleft = (pocket.centerx - 16,
                                      pocket.centery - 16)
    level.laser_phase = lambda _index: "active"
    level._scanner_hits_rect = lambda _laser, _rect: True
    events = []
    level.game.security.increase = events.append

    assert level.player_in_safe_pocket(level.game.player.rect)
    level.check_laser_collision(0.0)
    assert events == [10]


def test_room1_rotor_has_one_long_beam_and_local_fair_cycle():
    level = make_level()
    rotor = level.lasers[0]
    assert rotor["beam_offsets"] == (0.0,)
    assert rotor["half"] == 386
    assert rotor["layout_radius"] == 145
    assert rotor["beam_width"] == 14
    assert rotor["speed"] == pytest.approx(32.0)

    start = level.LASER_ENTRY_GRACE + rotor["phase_offset"]
    level.laser_clock = start - rotor["warning_duration"] / 2
    assert level.laser_phase(0) == "warning"
    level.laser_clock = start
    assert level.laser_phase(0) == "active"
    level.laser_clock = start + rotor["active_duration"]
    assert level.laser_phase(0) == "off"
    level.laser_clock = (start + rotor["active_duration"]
                         + rotor["cooldown_duration"])
    assert level.laser_phase(0) == "warning"


def test_room2_and_room3_rotor_cycle_stays_on_shared_timing():
    level = make_level()
    # Room 2 contains no rotor; Room 3 retains its existing rotor cycle.
    level.current_checkpoint = 3
    level.setup_room_hazards()
    rotor = next(laser for laser in level.lasers if laser.get("axis") == "r")
    assert "warning_duration" not in rotor
    assert "active_duration" not in rotor
    assert "cooldown_duration" not in rotor


def test_safe_pockets_are_clear_of_each_room_hazard_sweep():
    level = make_level()
    for checkpoint in (1, 2, 3):
        level.current_checkpoint = checkpoint
        level.setup_room_hazards()
        for pocket in level.safe_zones:
            for laser in level.lasers:
                if laser["axis"] == "x":
                    swept = pygame.Rect(laser["min_x"], laser["y"],
                                        laser["max_x"] + level.laser_width - laser["min_x"],
                                        level.laser_height)
                elif laser["axis"] == "t":
                    swept = pygame.Rect(laser["x"], laser["min_y"],
                                        laser["span"], laser["max_y"] - laser["min_y"])
                elif laser["axis"] == "y":
                    swept = pygame.Rect(laser["x"], laser["top"],
                                        level.laser_height,
                                        laser["bottom"] - laser["top"])
                else:
                    if checkpoint == 1:
                        # Room 1's deliberate long rotor sweep crosses some
                        # old safe-pocket regions; those pockets only shelter
                        # from the tracking emitter, not this beam.
                        continue
                    radius = laser["half"] + level.laser_height
                    swept = pygame.Rect(laser["cx"] - radius,
                                        laser["cy"] - radius,
                                        2 * radius, 2 * radius)
                assert not pocket.colliderect(swept)
            assert all(not pocket.colliderect(zone) for zone in level.floor_zones)


def test_laser_sweeps_stop_before_each_room_gate():
    level = make_level()
    for checkpoint, gate in enumerate(level.gates, start=1):
        level.current_checkpoint = checkpoint
        level.setup_room_hazards()
        for laser in level.lasers:
            if laser.get("axis", "x") == "x":
                sweep = pygame.Rect(laser["min_x"], laser["y"],
                                    laser["max_x"] + level.laser_width - laser["min_x"],
                                    level.laser_height)
                assert not sweep.colliderect(gate.rect)


def test_rotating_scanner_uses_beam_geometry_not_its_bounding_box():
    level = make_level()
    level.current_checkpoint = 3
    level.setup_room_hazards()
    scanner = next(item for item in level.lasers if item["axis"] == "r")
    scanner["angle"] = 45
    near_beam = pygame.Rect(int(scanner["cx"] - 20), int(scanner["cy"] - 20), 20, 20)
    outside_beam_inside_aabb = pygame.Rect(int(scanner["cx"] - 4), int(scanner["cy"] + 30), 20, 20)
    assert level._scanner_hits_rect(scanner, near_beam)
    assert not level._scanner_hits_rect(scanner, outside_beam_inside_aabb)


def test_robot_direction_cone_respects_safe_pocket_and_wall_occlusion():
    level = make_level()
    level.current_checkpoint = 2
    level.setup_room_hazards()
    level.robot_x = 390
    level.robot_direction = 1
    visible = pygame.Rect(505, 310, 32, 32)
    behind = pygame.Rect(360, 310, 32, 32)
    sheltered = pygame.Rect(level.safe_zones[0].left + 5, level.safe_zones[0].top + 5, 32, 32)
    across_bulkhead = pygame.Rect(860, 430, 32, 32)
    assert level.robot_can_see_rect(visible)
    assert not level.robot_can_see_rect(behind)
    assert not level.robot_can_see_rect(sheltered)
    assert not level.robot_can_see_rect(across_bulkhead)


def test_robot_checks_exposed_coop_partner_while_first_player_is_sheltered():
    level = make_level(coop=True)
    level.current_checkpoint = 2
    level.setup_room_hazards()
    pocket = level.safe_zones[0]
    level.game.player.rect.topleft = (pocket.left + 5, pocket.top + 5)
    level.game.player2.rect.topleft = (505, 310)
    events = []
    level.game.security.increase = events.append
    level.robot_x = 390
    level.robot_direction = 1
    level._update_robot(0.1)
    assert level.robot_alert
    assert events == [20]


def test_robot_patrol_turns_at_its_assigned_boundary():
    level = make_level()
    level.current_checkpoint = 2
    level.setup_room_hazards()
    level.game.player.rect.topleft = (80, 400)
    level.robot_x, level.robot_y = level.robot_waypoints[1]
    level.robot_waypoint_index = 1
    level._update_robot(0.1)
    assert level.robot_state == "SCAN"
    level.robot_waypoint_index = 2
    level.robot_state = "PATROL"
    level._update_robot(0.1)
    assert level.robot_y > level.robot_waypoints[1][1]
    level.robot_x, level.robot_y = level.robot_waypoints[2]
    level.robot_waypoint_index = 2
    level.robot_state = "PATROL"
    level._update_robot(0.1)
    assert level.robot_state == "SCAN"
    assert level.robot_y == level.robot_waypoints[2][1]


def test_robot_respects_closed_gate_collision_during_chase_movement():
    level = make_level()
    level.current_checkpoint = 2
    level.setup_room_hazards()
    level.robot_state = "CHASE"
    level.robot_x, level.robot_y = (780, 300)
    blocked_move = level._move_robot_towards((900, 300), 1.0, 200)
    assert blocked_move in (None, True)  # it may slide along the gate wall
    assert level.robot_x < level.gate2.rect.left
    assert not level.room_map.blocked(
        pygame.Rect(round(level.robot_x), round(level.robot_y),
                    level.robot_width, level.robot_height))


def test_tracking_laser_triggers_warns_tracks_then_locks_for_firing():
    level = make_level()
    level.game.player.rect.topleft = (320, 330)
    emitter = level.emitters[0]
    assert emitter["mount"] == "wall"
    assert emitter["state"] == "closed"
    assert not level._emitter_beam_hits_rect(emitter, level.game.player.rect)

    level.update(0.1)
    assert emitter["state"] == "opening"
    for _ in range(3):
        level.update(0.1)
    assert emitter["state"] == "tracking"
    old_angle = emitter["angle"]
    level.update(0.1)
    assert emitter["angle"] != old_angle
    assert abs(emitter["angle"] - old_angle) <= emitter["turn_rate"] * 0.1 + 0.01

    while emitter["state"] == "tracking":
        level.update(0.1)
    assert emitter["state"] == "warning"
    assert emitter["warn_time"] >= 1.5
    for _ in range(20):
        level.update(0.1)
        if emitter["state"] == "locking":
            break
    assert emitter["state"] == "locking"
    locked_angle = emitter["angle"]
    level.game.player.rect.topleft = (90, 400)  # escape into Safe Space A
    for _ in range(5):
        level.update(0.1)
        if emitter["state"] == "active":
            break
    assert emitter["state"] == "active"
    assert emitter["angle"] == locked_angle
    assert not level._emitter_beam_hits_rect(emitter, level.game.player.rect)
    level.update(0.1)
    assert emitter["angle"] == locked_angle
    for _ in range(12):
        level.update(0.1)
    assert emitter["state"] in ("cooldown", "closed")


def test_emitter_mount_types_are_assigned_by_room():
    level = make_level()
    assert [item["mount"] for item in level.emitters] == ["wall"]
    level.current_checkpoint = 2
    level.setup_room_hazards()
    assert [item["mount"] for item in level.emitters] == ["floor"]
    level.current_checkpoint = 3
    level.setup_room_hazards()
    assert [item["mount"] for item in level.emitters] == ["ceiling"]


def test_room_two_floor_emitter_opens_warns_fires_and_retracts():
    level = make_level()
    level.current_checkpoint = 2
    level.setup_room_hazards()
    level.game.player.rect.topleft = (700, 300)
    emitter = level.emitters[0]
    assert emitter["mount"] == "floor"
    level.update(0.1)
    assert emitter["state"] == "opening"
    clock_when_opening = level.laser_clock
    for _ in range(30):
        level.update(0.1)
        if emitter["state"] == "active":
            break
    assert emitter["state"] == "active"
    assert level.laser_clock == clock_when_opening
    level.game.player.rect.topleft = (90, 400)
    for _ in range(12):
        level.update(0.1)
    assert emitter["state"] in ("cooldown", "closed")
    level.render(pygame.Surface((960, 640)))


def test_emitter_warning_and_firing_geometry_matches_the_visible_beam():
    level = make_level()
    emitter = level.emitters[0]
    emitter["state"] = "warning"
    emitter["angle"] = 0
    target = pygame.Rect(250, 231, 8, 8)
    outside = pygame.Rect(250, 252, 8, 8)
    assert level._emitter_beam_hits_rect(emitter, target)
    assert not level._emitter_beam_hits_rect(emitter, outside)
    assert not level._emitter_beam_hits_rect(emitter, level.game.player.rect)

    emitter["state"] = "active"
    assert level._emitter_beam_hits_rect(emitter, target)
    surface = pygame.Surface((960, 640))
    level.render(surface)
    assert tuple(surface.get_at((250, 232)))[:3] == (255, 45, 45)


def test_room_three_rotor_has_two_collision_matched_rotating_arms():
    level = make_level()
    level.current_checkpoint = 3
    level.setup_room_hazards()
    rotor = next(laser for laser in level.lasers if laser.get("axis") == "r")
    assert rotor["beam_offsets"] == (0.0, 90.0)
    rotor["angle"] = 0
    vertical_arm = pygame.Rect(int(rotor["cx"] - 2), int(rotor["cy"] + 22), 4, 4)
    assert level._scanner_hits_rect(rotor, vertical_arm)
    rotor["angle"] = 45
    assert not level._scanner_hits_rect(rotor, vertical_arm)


def test_circular_rotor_speed_scales_with_game_difficulty():
    level = make_level()
    level.game.difficulty = get_difficulty("easy")
    level.setup_room_hazards()
    easy_speed = level.lasers[0]["speed"]
    level.game.difficulty = get_difficulty("hard")
    level.setup_room_hazards()
    hard_speed = level.lasers[0]["speed"]
    assert easy_speed < hard_speed


def test_room_three_emitter_waits_for_safe_laser_window_and_staggers_fire():
    level = make_level()
    level.current_checkpoint = 3
    level.setup_room_hazards()
    level.game.player.rect.topleft = (620, 300)
    level.laser_clock = 2.1  # the bottom lane is active; the box must wait.
    for _ in range(60):
        level.update(1 / 60)
    emitter = level.emitters[0]
    assert emitter["state"] == "pending"
    for _ in range(400):
        level.update(1 / 60)
        if emitter["state"] in ("opening", "warning", "active", "retracting"):
            break
    assert emitter["state"] in ("opening", "warning", "active", "retracting")
    clock = level.laser_clock
    level.update(0.1)
    assert level.laser_clock == clock


def test_robot_alert_chase_investigate_search_and_patrol_states():
    level = make_level()
    level.current_checkpoint = 2
    level.setup_room_hazards()
    level.robot_x, level.robot_y = (390, 172)
    level.robot_state = "PATROL"
    level.robot_patrol_vector = pygame.Vector2(1, 0.25).normalize()
    # This position is inside the robot's cone but outside the new hard cover.
    level.game.player.rect.topleft = (450, 180)
    events = []
    level.game.security.increase = events.append

    level._update_robot(0.1)
    assert level.robot_state == "ALERT"
    assert events == [20]
    assert level.robot_alert

    level._update_robot(0.7)
    assert level.robot_state == "CHASE"
    chase_x = level.robot_x
    level._update_robot(0.1)
    assert level.robot_x != chase_x or level.robot_y != 172

    pocket = level.safe_zones[0]
    level.game.player.rect.topleft = (pocket.left + 10, pocket.top + 10)
    level._update_robot(0.1)
    assert level.robot_state == "INVESTIGATE"
    assert not level.robot_can_see_rect(level.game.player.rect)

    known = level.robot_last_known
    level.robot_x = known.x - level.robot_width / 2
    level.robot_y = known.y - level.robot_height / 2
    level._update_robot(0.1)
    assert level.robot_state == "SEARCH"
    level._update_robot(3.0)
    assert level.robot_state == "PATROL"


def test_render_does_not_change_robot_or_gameplay_state():
    level = make_level()
    snapshot = (level.robot_x, level.robot_direction, level.laser_clock,
                tuple(item.get("angle") for item in level.lasers),
                level.game.score.get_score())
    level.render(pygame.Surface((960, 640)))
    assert level.safe_zones
    assert snapshot == (level.robot_x, level.robot_direction, level.laser_clock,
                       tuple(item.get("angle") for item in level.lasers),
                       level.game.score.get_score())


def test_render_does_not_advance_level3_sparks_or_gate_animation():
    level = make_level()
    level.unlock_current_gate()
    surface = pygame.Surface((960, 640))
    vis = level._vis_state()
    before = (vis["time"], level._gate_progress(level.gate1),
              tuple((spark["x"], spark["y"], spark["age"])
                    for spark in vis["sparks"]))

    level.render(surface)
    level.render(surface)

    after = (vis["time"], level._gate_progress(level.gate1),
             tuple((spark["x"], spark["y"], spark["age"])
                   for spark in vis["sparks"]))
    assert after == before

    level.update(0.1)
    assert vis["time"] == pytest.approx(0.1)
    assert level._gate_progress(level.gate1) > before[1]
    assert any(spark["age"] > 0 for spark in vis["sparks"])


def test_gate_sparks_do_not_carry_over_to_the_next_room():
    level = make_level()
    level.unlock_current_gate()
    assert level._vis_state()["sparks"]
    for _ in range(45):
        level.update(1 / 60)
    level.game.player.rect.topleft = (860, 280)
    level.update(1 / 60)

    assert level.current_room_number() == 2
    assert not level._vis_state()["sparks"]
