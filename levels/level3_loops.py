"""
levels/level3_loops.py
Owner: Member 3 - Yashovardhan

Level 3 - The Laser Loop

    Room 1 -> Gate 1 -> Room 2 -> Gate 2 -> Room 3 -> Gate 3 -> Exit

The global Easy/Medium/Hard difficulty is used to select questions.
"""

import json
import math
import os
import random
from pathlib import Path

import pygame

from core.difficulty import DIFFICULTIES
from core.map_manager import Room, RoomMap
from entities.gate import Gate
from levels import laser_requests, patrol_cameras


class PatrolGate(Gate):
    """Team's badge-scan door: a Gate whose unlock runs a short scan, then the slide.

    Kept for compatibility with levels.badge_door and its tests.  The approved
    Level 3 vault gates are still plain Gates, so the room layout is unchanged.
    """

    SECONDS = 1.2

    def unlock(self):
        if self.state == "locked":
            super().unlock()
            self._timer = self.SECONDS

    @property
    def progress(self):
        """0 locked .. 1 open, the number levels.badge_door draws from."""
        if self.state == "locked":
            return 0.0
        if self.state == "open":
            return 1.0
        return max(0.001, 1.0 - self._timer / self.SECONDS)


class Level3LaserLoop:
    """Controls the Level 3 Laser Loop level."""

    @property
    def current_checkpoint(self):
        """Compatibility view of the active room's checkpoint number."""
        room_map = getattr(self, "room_map", None)
        if room_map is not None:
            try:
                return self.room_names.index(room_map.current_name) + 1
            except (ValueError, AttributeError):
                pass
        return getattr(self, "_current_checkpoint", 1)

    @current_checkpoint.setter
    def current_checkpoint(self, value):
        self._current_checkpoint = max(1, min(3, int(value)))
        room_map = getattr(self, "room_map", None)
        names = getattr(self, "room_names", ())
        if room_map is not None and names:
            room_map.current_name = names[self._current_checkpoint - 1]
            self.room = room_map.current
            self.barrier_walls = self.room.walls

    def __init__(self, game=None):
        self.game = game

        # -------------------------
        # Level state
        # -------------------------
        self.complete = False
        self.selected_option = None
        self.feedback = ""
        self.room_transition_timer = 0.0
        self.room_transition_duration = 1.15
        self._tx = None   # gate walk-through transition (see _begin_gate_transition)
        self.room_transition_title = ""

        # -------------------------
        # Question system
        # One challenge per room.
        # -------------------------
        self.total_questions = 3
        self.current_question_number = 0
        self.current_checkpoint = 1

        self.question_pool = []
        self.room2_override_pool = []
        self.selected_questions = []
        self.current_question = None

        self.options = []
        self.correct_option_index = None

        # Question support features
        self.current_hint = ""
        self.current_explanation = ""
        self.show_hint = False
        self.hint_used = False
        self.question_points = 50
        self.current_difficulty = "medium"

        self.load_questions()

        # -------------------------
        # Security timer
        # -------------------------
        self.base_time_limit = 20
        self.time_limit = self.base_time_limit
        self.time_left = self.time_limit

        # -------------------------
        # Room layout
        # -------------------------
        self.room_x = 40
        self.room_y = 30
        self.room_width = 880
        self.room_height = 560
        self.play_top = 150
        # The bottom edge stops player sprites above the question panel.
        self.play_bottom = 450
        self.spawn_points = ((80, 280), (118, 280))

        # Room 2 approved solid cover objects (Cover 2 and Cover 3; Cover 1 removed)
        self.room2_cover_rects = (
            pygame.Rect(275, 295, 86, 52),  # Cover 2: lower-middle tactical cover
            pygame.Rect(505, 225, 86, 52),  # Cover 3: upper-right-center tactical cover
        )

        # Each chamber uses the existing Room / RoomMap contract. Its exit
        # is a real gate in the right-side bulkhead, with a clear passage
        # destination in the next chamber.
        self.gate1 = Gate(850, 190, width=20, height=240)
        self.gate2 = Gate(850, 190, width=20, height=240)
        self.gate3 = Gate(850, 190, width=20, height=240)
        self.gates = [self.gate1, self.gate2, self.gate3]
        self.room_names = (
            "level3_room1", "level3_room2", "level3_room3"
        )
        room_bounds = (self.room_x, self.play_top, self.room_width,
                       self.play_bottom - self.play_top)
        self.rooms = []
        for name, gate in zip(self.room_names, self.gates):
            base_walls = (
                pygame.Rect(gate.rect.x, self.play_top, gate.rect.width,
                            gate.rect.top - self.play_top),
                pygame.Rect(gate.rect.x, gate.rect.bottom, gate.rect.width,
                            self.play_bottom - gate.rect.bottom),
            )
            if name == "level3_room2":
                walls = base_walls + self.room2_cover_rects
            else:
                walls = base_walls
            self.rooms.append(Room(name, room_bounds, walls=walls, gates=[gate]))

        self.exit_triggers = {
            1: pygame.Rect(850, 190, 70, 240),
            2: pygame.Rect(850, 190, 70, 240),
        }
        self.room_map = RoomMap(
            self.rooms,
            exits=[
                (self.room_names[0], self.exit_triggers[1], self.room_names[1],
                 (80, 280), self.gate1),
                (self.room_names[1], self.exit_triggers[2], self.room_names[2],
                 (80, 280), self.gate2),
            ],
        )
        # Core reads room_map.blocked every frame; freezing it holds the
        # players still while the gate walk-through plays.
        self._rm_blocked = self.room_map.blocked
        self.room_map.blocked = self._tx_blocked
        self.room = self.room_map.current
        self.barrier_walls = self.room.walls
        self.room_entry_spawns = {name: ((80, 280), (118, 280))
                                  for name in self.room_names}
        self.final_exit_rect = pygame.Rect(870, 190, 50, 240)

        # -------------------------
        # Room 2 Override Terminal & Overload state
        # -------------------------
        self.room2_terminal_rect = pygame.Rect(378, 156, 58, 36)
        self.room2_terminal_interact_rect = self.room2_terminal_rect.inflate(44, 40)
        self.room2_override_question = None
        self.room2_override_panel_open = False
        self.room2_override_solved = False
        self.room2_override_attempted = False
        self.room2_override_selected = None
        self.room2_override_hover = None
        self.room2_override_feedback = ""
        self.room2_override_explanation = ""
        self.room2_robot_disabled_timer = 0.0
        self.room2_robot_disable_duration = 6.5

        # Robot overload state (Room 2)
        self.room2_overload_warning_timer = 0.0
        self.room2_overload_warning_duration = 1.6
        self.room2_overload_active_timer = 0.0
        self.room2_overload_active_duration = 4.5
        self.room2_overload_cooldown = 9.0

        # Room 2 Gate 2 final tracking challenge state
        self.room2_gate_challenge_survived = False
        self.room2_gate_challenge_armed = False
        self.room2_gate_question_solved = False

        # -------------------------
        # Laser settings
        # -------------------------
        self.track_x = 75
        self.track_y = 215
        self.track_width = 775
        self.track_height = 42

        self.laser_width = 150
        self.laser_height = 14
        self.laser_speed = 200

        self.laser_penalty_cooldown = 0.0
        self.laser_penalty_duration = 1.0
        self.laser_hit_feedback_timer = 0.0

        # Team-architecture compatibility: no patrol lanes, droid or night guard here.
        self.lane_loop = None
        self.camera_bank = None
        self.guard = None
        self.droid = None
        self.answer_at_door = False

        # Each room's door question is about the loop that room really runs
        # (levels/laser_requests.py): lit pads, sweeping cameras, core pulses.
        # MEMORY_HEIST_OLD_LEVEL3=1 brings back the fixed question bank in data/puzzles.json.
        self.room_requests = {}
        if os.environ.get("MEMORY_HEIST_OLD_LEVEL3") != "1":
            difficulty = self.get_selected_difficulty()
            self.room_requests = {room: laser_requests.make_request(room, difficulty)
                                  for room in (1, 2, 3)}
        self.lit_pads = None              # Room 1: pads the board lights (None = all)
        self.core_vent_after = None       # Room 3: pulses before the core vents (None = never)

        self.lasers = []
        self.emitters = []
        self.floor_zones = []
        self.safe_zones = []

        # -------------------------
        # Security robot
        # -------------------------
        self.robot_x = 120
        self.robot_y = 170
        self.robot_width = 70
        self.robot_height = 35

        self.robot_speed = 120
        self.robot_direction = 1

        self.robot_left_boundary = 100
        self.robot_right_boundary = 810

        # -------------------------
        # Robot detection system
        # -------------------------
        self.robot_scan_radius = 180
        self.robot_alert = False
        self.robot_alert_timer = 0
        self.robot_alert_duration = 2.5
        self.robot_detection_cooldown = 0
        self.robot_vision_half_angle = 38.0
        self.robot_hunt_speed_bonus = 45
        self.robot_speed = 120
        self.robot_left_boundary = 100
        self.robot_right_boundary = 270
        self.robot_scan_surface = pygame.Surface((960, 640), pygame.SRCALPHA)

        # -------------------------
        # Robot scanning animation
        # -------------------------
        self.robot_scan_phase = 0.0
        self.robot_alert_latched = False
        self.robot_state = "PATROL"
        self.robot_waypoints = []
        self.robot_waypoint_index = 0
        self.robot_waypoint_pause = 0.0
        self.robot_scan_offset = 0.0
        self.robot_aim_vector = None
        self.robot_patrol_vector = pygame.Vector2(1, 0.25).normalize()
        self.robot_last_known = None
        self.robot_search_timer = 0.0

        self._select_session_override_question()
        self._reset_core_state("medium")
        self.setup_room_hazards()

        # -------------------------
        # Security code display
        # -------------------------
        self.code_lines = [
            "while True:",
            "    if laser_detected:",
            "        break",
        ]

        # -------------------------
        # Fonts
        # -------------------------
        self.title_font = pygame.font.Font(None, 34)
        self.timer_font = pygame.font.Font(None, 28)
        self.objective_font = pygame.font.Font(None, 23)
        self.heading_font = pygame.font.Font(None, 26)
        self.code_font = pygame.font.Font(None, 24)
        self.option_font = pygame.font.Font(None, 24)
        self.feedback_font = pygame.font.Font(None, 23)
        self.instruction_font = pygame.font.Font(None, 21)

        self.start_questions()

    # =========================================================
    # ROOM 2 OVERRIDE TERMINAL HELPERS
    # =========================================================

    def _select_session_override_question(self):
        """Select one Room 2 override question from the shared puzzle data."""
        difficulty = self.get_selected_difficulty()
        pool = [item for item in self.room2_override_pool
                if item.get("difficulty", "medium").lower() == difficulty]
        if not pool:
            pool = self.room2_override_pool
        chosen = random.choice(pool) if pool else None
        self.room2_override_question = None if chosen is None else {
            "id": chosen.get("id"),
            "difficulty": chosen.get("difficulty", difficulty),
            "prompt": chosen.get("prompt", chosen.get("question", "")),
            "code": list(chosen.get("code", ())),
            "options": list(chosen.get("options", ())),
            "answer": chosen.get("answer", ""),
            "explanation": chosen.get("explanation", ""),
        }
        self.room2_override_panel_open = False
        self.room2_override_solved = False
        self.room2_override_attempted = False
        self.room2_override_selected = None
        self.room2_override_hover = None
        self.room2_override_feedback = ""
        self.room2_override_explanation = ""

    def _player_near_room2_terminal(self):
        """Return True if any active player is within the Room 2 terminal interaction zone."""
        if self.current_room_number() != 2:
            return False
        return any(
            rect.colliderect(self.room2_terminal_interact_rect)
            for rect in self._player_rects()
        )

    def _room2_override_modal_geometry(self):
        """Return consistent layout rectangles for the Room 2 override modal."""
        modal = pygame.Rect(190, 145, 580, 330)
        option_rects = []
        start_y = modal.y + 150
        col_w = 258
        row_h = 38
        for i in range(4):
            col = i % 2
            row = i // 2
            x = modal.x + 24 + col * (col_w + 16)
            y = start_y + row * (row_h + 10)
            option_rects.append(pygame.Rect(x, y, col_w, row_h))
        close_rect = pygame.Rect(modal.right - 92, modal.y + 12, 78, 26)
        return modal, option_rects, close_rect

    def _submit_room2_override_answer(self, option_index):
        """Evaluate the player's choice on the Room 2 override terminal."""
        if not self.room2_override_question or self.room2_override_solved:
            return
        options = self.room2_override_question["options"]
        if not (0 <= option_index < len(options)):
            return

        self.room2_override_selected = option_index
        self.room2_override_attempted = True
        chosen_text = options[option_index]
        correct_text = self.room2_override_question["answer"]

        if chosen_text == correct_text:
            self.room2_override_explanation = self.room2_override_question["explanation"]
            self.room2_override_solved = True
            self.room2_robot_disabled_timer = self.room2_robot_disable_duration
            self.robot_state = "DISABLED"
            self.robot_alert = False
            self.robot_alert_timer = 0.0
            self.robot_aim_vector = None
            self.room2_overload_warning_timer = 0.0
            self.room2_overload_active_timer = 0.0
            self.room2_override_feedback = (
                f"OVERRIDE ACCEPTED! SENTRY DISABLED ({self.room2_robot_disable_duration:.0f}s)."
            )
            self.feedback = "OVERRIDE SUCCESSFUL! SENTRY OFFLINE."
            self._spawn_sparks(
                (self.robot_x + self.robot_width / 2, self.robot_y + self.robot_height / 2),
                (90, 230, 255),
                (255, 210, 90),
            )
        else:
            self.room2_override_feedback = "Incorrect. Security +5; try again."
            self.feedback = "TERMINAL OVERRIDE FAILED — SENTRY STILL ACTIVE."
            if self.game:
                self.game.security.increase(5)

    # =========================================================
    # PLAYER HELPERS
    # =========================================================


    def _player_rects(self):
        """Return active player rectangles."""
        if not self.game or not hasattr(self.game, "player"):
            return []
        rects = [self.game.player.rect]

        if getattr(self.game, "coop", False) and hasattr(self.game, "player2"):
            rects.append(self.game.player2.rect)

        return rects

    def _bring_partner(self, mover_rect):
        """Move the second player next to the player changing rooms."""
        if not getattr(self.game, "coop", False):
            return

        # In a connected room both players cross an open gate themselves;
        # never teleport a partner through a wall or into a hazard.

    # =========================================================
    # LASER SYSTEM
    # =========================================================

    LASER_ENTRY_GRACE = 2.0
    LASER_STAGGER = 1.0
    LASER_ON = 1.2
    LASER_OFF = 5.0
    LASER_WARN = 1.0

    ROOM_NAMES = {1: "LASER TRAINING", 2: "LASER NETWORK", 3: "CORE INFILTRATION"}
    ROOM_TITLES = {
        1: "ROOM 1 - SECURITY ENTRY",
        2: "ROOM 2 - LASER CORRIDOR",
        3: "ROOM 3 - CORE SECURITY",
    }
    # ---- Room 3 (Core Security): reactive rotating core ----------------
    CORE_PROXIMITY = 175.0          # player-to-core distance that wakes it
    CORE_HUB_RADIUS = 24.0          # ring starts at the reactor hub
    CORE_RING_MAX = 120.0           # largest ring radius (clear of the bottom lane)
    CORE_RING_WIDTH = 12.0          # ring thickness (visual == collision)
    CORE_ALERT_TIME = 0.9           # alert before charging
    CORE_ALERT_GRACE = 1.2          # no one nearby this long -> back to idle
    CORE_RECOVERY_TIME = 2.0
    CORE_CHARGE = {"easy": 1.7, "medium": 1.45, "hard": 1.25}   # warning
    CORE_PULSE = {"easy": 1.7, "medium": 1.5, "hard": 1.35}     # ring travel
    CORE_COOLDOWN = {"easy": 4.5, "medium": 3.5, "hard": 2.5}   # breathing room
    CORE_ROT_MULT = {"idle": 1.0, "alert": 2.0, "charge": 2.8,
                     "pulse": 2.0, "recovery": 1.0, "offline": 0.0}

    ROOM_OBJECTIVES = {
        1: "Read the board: only lit pads shield you. Cross when the beam powers down.",
        2: "Read the board: it picks the cameras that sweep. Use cover, evade the sentry.",
        3: "Read the board: the core vents after its loop. Cross while it is offline.",
    }
    CORE_VENT_TIME = 6.0            # seconds the core stays offline once its board loop ends

    def laser_phase(self, index):
        """Return 'off' (safe), 'warning' (safe, about to fire) or 'active'."""

        laser = self.lasers[index]
        if laser.get("type") == "tracking":
            return {"idle": "off", "warning": "warning", "active": "active",
                    "cooldown": "off"}.get(laser.get("state", "idle"), "off")

        warning_duration = laser.get(
            "warning_duration",
            self.LASER_WARN * getattr(self, "hazard_warning_scale", 1.0))
        active_duration = laser.get("active_duration", self.LASER_ON)
        cooldown_duration = laser.get("cooldown_duration", self.LASER_OFF)
        start = (self.LASER_ENTRY_GRACE + index * self.LASER_STAGGER
                 + laser.get("phase_offset", 0.0))
        clock = self.laser_clock

        if clock < start - warning_duration:
            return "off"

        if clock < start:
            return "warning"

        position = (clock - start) % (
            active_duration + cooldown_duration + warning_duration)

        if position < active_duration:
            return "active"

        if position < active_duration + cooldown_duration:
            return "off"

        return "warning"

    def active_beam_rects(self):
        """Axis-aligned active beam rectangles, retained for compatibility."""
        result = []
        for index, laser in enumerate(self.lasers):
            if self.laser_phase(index) != "active" or laser.get("axis", "x") == "r":
                continue
            result.append(self._laser_rect(laser))
        result.extend(zone.copy() for i, zone in enumerate(self.floor_zones)
                      if self.floor_zone_phase(i) == "active")
        return result

    def _laser_rect(self, laser):
        if laser.get("axis") == "t":
            return pygame.Rect(int(laser["x"]), int(laser["y"]),
                               int(laser.get("span", self.track_width)),
                               int(laser.get("thickness", self.laser_height)))
        if laser.get("axis", "x") == "y":
            return pygame.Rect(int(laser["x"]), int(laser["y"]),
                               self.laser_height, laser.get("length", 120))
        return pygame.Rect(int(laser["x"]), int(laser["y"]),
                           laser.get("width", self.laser_width), self.laser_height)

    @staticmethod
    def _scanner_corners(laser, thickness=None, angle=None):
        thickness = 14 if thickness is None else thickness
        angle = math.radians(laser["angle"] if angle is None else angle)
        ux, uy = math.cos(angle), math.sin(angle)
        vx, vy = -uy, ux
        half, thick = laser["half"], thickness / 2
        cx, cy = laser["cx"], laser["cy"]
        return [(cx + ux*a + vx*b, cy + uy*a + vy*b)
                for a, b in ((-half,-thick),(half,-thick),(half,thick),(-half,thick))]

    def _scanner_hits_rect(self, laser, rect):
        box = ((rect.left, rect.top), (rect.right, rect.top),
               (rect.right, rect.bottom), (rect.left, rect.bottom))
        thickness = laser.get("beam_width", 14)
        for offset in laser.get("beam_offsets", (0.0,)):
            beam_angle = laser["angle"] + offset
            beam = self._scanner_corners(laser, thickness=thickness, angle=beam_angle)
            angle = math.radians(beam_angle)
            axes = ((math.cos(angle), math.sin(angle)),
                    (-math.sin(angle), math.cos(angle)), (1.0, 0.0), (0.0, 1.0))
            overlaps = True
            for ax, ay in axes:
                a = [x * ax + y * ay for x, y in beam]
                b = [x * ax + y * ay for x, y in box]
                if max(a) <= min(b) or max(b) <= min(a):
                    overlaps = False
                    break
            if overlaps:
                return True
        return False

    @staticmethod
    def _ray_rect_interval(origin, direction, rect):
        """Return the ray's entry/exit distances through a rectangle."""
        near, far = float("-inf"), float("inf")
        bounds = ((rect.left, rect.right - 1), (rect.top, rect.bottom - 1))
        for coordinate, delta, (low, high) in zip(
                origin, direction, bounds):
            if abs(delta) < 1e-9:
                if coordinate < low or coordinate > high:
                    return None
                continue
            first = (low - coordinate) / delta
            second = (high - coordinate) / delta
            near = max(near, min(first, second))
            far = min(far, max(first, second))
            if far < near:
                return None
        if far < 0:
            return None
        return near, far

    def _emitter_beam_laser(self, emitter, angle=None):
        """Return the source-to-endpoint beam shared by rendering and hits.

        The configured reach is clipped against the room shell, its bulkhead
        and the closed gate, so an emitter cannot draw or damage through a
        wall into another room.
        """
        angle = math.radians(emitter["angle"] if angle is None else angle)
        dx, dy = math.cos(angle), math.sin(angle)
        ox, oy = emitter["origin"]
        length = float(emitter["beam_length"])
        room_interval = self._ray_rect_interval(
            (ox, oy), (dx, dy), self.room.bounds)
        if room_interval is not None:
            length = min(length, max(0.0, room_interval[1] - 1.0))

        blockers = list(self.room.walls)
        gate = self.gates[self.current_room_number() - 1]
        blockers.append(gate.rect)
        for blocker in blockers:
            interval = self._ray_rect_interval((ox, oy), (dx, dy), blocker)
            if interval is not None and interval[1] >= 0 and interval[0] >= 0:
                length = min(length, max(0.0, interval[0] - 1.0))

        return {
            "cx": ox + dx * length / 2,
            "cy": oy + dy * length / 2,
            "half": length / 2,
            "angle": math.degrees(angle),
            "beam_width": emitter.get("beam_width", 10),
            "beam_offsets": (0.0,),
            "length": length,
        }

    @staticmethod
    def _turn_towards_degrees(current, target, max_step):
        difference = (target - current + 180.0) % 360.0 - 180.0
        return current + max(-max_step, min(max_step, difference))

    def _emitter_can_start(self, emitter):
        if (self.current_room_number() == 3
                and self.core_state in ("charge", "pulse")):
            return False
        if any(other is not emitter and other["state"] in
               ("opening", "tracking", "warning", "locking", "active", "retracting")
               for other in self.emitters):
            return False
        if emitter.get("sync_lasers"):
            if any(self.laser_phase(index) != "off"
                   for index in emitter["sync_lasers"]):
                return False
            if any(self.floor_zone_phase(index) != "off"
                   for index in range(len(self.floor_zones))):
                return False
        return True

    def _emitter_targetable(self, emitter, rect):
        """Limit acquisition to targets its warning beam can actually reach."""
        if (not emitter["trigger"].colliderect(rect)
                or self.player_in_safe_pocket(rect)):
            return False
        ox, oy = emitter["origin"]
        target_x, target_y = rect.center
        angle = math.degrees(math.atan2(target_y - oy, target_x - ox))
        if not emitter["min_angle"] <= angle <= emitter["max_angle"]:
            return False
        beam = self._emitter_beam_laser(emitter, angle)
        return (beam["length"] > 0
                and self._scanner_hits_rect(beam, rect))

    def _aim_emitter_at_targets(self, emitter, targets, dt):
        """Track the nearest visible target at the emitter's limited turn rate."""
        if not targets:
            return
        target = min(targets, key=lambda rect: math.dist(
            rect.center, emitter["origin"]))
        ox, oy = emitter["origin"]
        desired = math.degrees(math.atan2(target.centery - oy,
                                          target.centerx - ox))
        desired = max(emitter["min_angle"], min(emitter["max_angle"], desired))
        emitter["angle"] = self._turn_towards_degrees(
            emitter["angle"], desired, emitter["turn_rate"] * dt)
        emitter["target"] = (target.centerx, target.centery)

    def _update_emitters(self, dt):
        """Advance mounted shutter, aim, warning, fire and cooldown states."""
        room_num = self.current_room_number()

        for emitter in self.emitters:
            targets = [rect for rect in self._player_rects()
                       if self._emitter_targetable(emitter, rect)]
            state = emitter["state"]
            if state == "closed" and targets:
                emitter["state"] = state = "pending"
                if room_num == 2:
                    self.room2_gate_challenge_armed = True
            if state == "pending":
                if not targets:
                    emitter["state"] = "closed"
                    continue
                if self._emitter_can_start(emitter):
                    emitter["state"] = "opening"
                    emitter["timer"] = emitter["open_time"]
                    state = "opening"
            if state == "opening":
                emitter["timer"] -= dt
                if emitter["timer"] <= 0:
                    if room_num in (1, 2):
                        emitter["state"] = "tracking"
                        emitter["timer"] = emitter["track_time"]
                    else:
                        emitter["state"] = "warning"
                        emitter["timer"] = emitter["warn_time"]
                continue
            if state == "tracking":
                self._aim_emitter_at_targets(emitter, targets, dt)
                emitter["timer"] -= dt
                if emitter["timer"] <= 0:
                    emitter["state"] = "warning"
                    emitter["timer"] = emitter["warn_time"]
                continue
            if state == "warning":
                self._aim_emitter_at_targets(emitter, targets, dt)
                emitter["timer"] -= dt
                if emitter["timer"] <= 0:
                    if room_num in (1, 2):
                        emitter["state"] = "locking"
                        emitter["locked_angle"] = emitter["angle"]
                        emitter["timer"] = emitter["lock_time"]
                    else:
                        emitter["state"] = "active"
                        emitter["timer"] = emitter["active_time"]
                continue
            if state == "locking":
                # Visibly settles the aim before firing so the player can dodge.
                emitter["angle"] = emitter.get("locked_angle", emitter["angle"])
                emitter["timer"] -= dt
                if emitter["timer"] <= 0:
                    emitter["state"] = "active"
                    emitter["timer"] = emitter["active_time"]
                continue
            if state == "active":
                emitter["timer"] -= dt
                if emitter["timer"] <= 0:
                    emitter["state"] = "retracting"
                    emitter["timer"] = emitter["retract_time"]
                    if room_num == 2 and self.room2_gate_challenge_armed:
                        self.room2_gate_challenge_survived = True
                        self.room2_gate_challenge_armed = False
                        if self.room2_gate_question_solved:
                            self.unlock_current_gate()
                continue
            if state == "retracting":
                emitter["timer"] -= dt
                if emitter["timer"] <= 0:
                    emitter["state"] = "cooldown"
                    emitter["timer"] = emitter["cooldown_time"]
                continue
            if state == "cooldown":
                emitter["timer"] -= dt
                if emitter["timer"] <= 0:
                    emitter["state"] = "closed"
                    emitter["timer"] = 0.0

    def _emitter_beam_hits_rect(self, emitter, rect):
        return self._scanner_hits_rect(self._emitter_beam_laser(emitter), rect)

    def floor_zone_phase(self, index):
        warning_duration = self.LASER_WARN * getattr(
            self, "hazard_warning_scale", 1.0)
        start = self.LASER_ENTRY_GRACE + index * 1.5
        if self.laser_clock < start - warning_duration:
            return "off"
        if self.laser_clock < start:
            return "warning"
        active_time = 0.8
        cycle = warning_duration + self.LASER_ON + self.LASER_OFF
        off_time = cycle - warning_duration - active_time
        position = (self.laser_clock - start) % cycle
        if position < active_time:
            return "active"
        if position < active_time + off_time:
            return "off"
        return "warning"

    def check_laser_collision(self, dt):
        """Apply a penalty when a player touches an active laser."""

        if not self.game or not hasattr(self.game, "player"):
            return

        if self.laser_penalty_cooldown > 0:
            self.laser_penalty_cooldown = max(
                0.0,
                self.laser_penalty_cooldown - dt,
            )

        if self.laser_hit_feedback_timer > 0:
            self.laser_hit_feedback_timer = max(
                0.0,
                self.laser_hit_feedback_timer - dt,
            )

        camera_spotted = self._update_cameras(dt)

        if self.laser_penalty_cooldown > 0:
            if self.current_room_number() == 2 and self.room2_gate_challenge_armed:
                exposed = [r for r in self._player_rects()
                           if not self.player_in_safe_pocket(r)]
                if any(emitter["state"] == "active"
                       and any(self._emitter_beam_hits_rect(emitter, rect)
                               for rect in exposed)
                       for emitter in self.emitters):
                    self.room2_gate_challenge_armed = False
            return

        if camera_spotted:
            self._camera_hit()
            return

        all_players = self._player_rects()
        emitter_players = [r for r in all_players
                           if not self.player_in_safe_pocket(r)]
        laser_players = (all_players if self.current_room_number() == 1
                         else emitter_players)
        hit = False
        hit_rect = None
        for index, laser in enumerate(self.lasers):
            if self.laser_phase(index) != "active":
                continue
            if (laser.get("axis") == "r" and self.current_room_number() == 3
                    and self.core_state == "offline"):
                continue
            if laser.get("axis", "x") == "r":
                rotor_players = (all_players if self.current_room_number() == 1
                                 else laser_players)
                hit_rect = next((r for r in rotor_players
                                 if self._scanner_hits_rect(laser, r)), None)
            else:
                beam = self._laser_rect(laser)
                hit_rect = next((r for r in laser_players
                                 if r.colliderect(beam)), None)
            hit = hit_rect is not None
            if hit:
                break
        if not hit:
            for index, zone in enumerate(self.floor_zones):
                if self.floor_zone_phase(index) != "active":
                    continue
                hit_rect = next((r for r in laser_players
                                 if r.colliderect(zone)), None)
                if hit_rect is not None:
                    hit = True
                    break
        emitter_hit_rect = None
        for emitter in self.emitters:
            if emitter["state"] != "active":
                continue
            emitter_hit_rect = next((r for r in emitter_players
                                     if self._emitter_beam_hits_rect(emitter, r)), None)
            if emitter_hit_rect is not None:
                break

        if emitter_hit_rect is not None and self.current_room_number() == 2:
            self.room2_gate_challenge_armed = False

        if not hit and emitter_hit_rect is not None:
            hit_rect = emitter_hit_rect
            hit = True

        if (not hit and self.current_room_number() == 3
                and self.core_state == "pulse"):
            for player_index, rect in enumerate(all_players):
                if (player_index in self.core_hit_players
                        or self.player_in_safe_pocket(rect)
                        or not self._core_ring_hits_rect(rect)):
                    continue
                self.core_hit_players.add(player_index)
                hit_rect, hit = rect, True
                break

        if hit:
            self.laser_penalty_cooldown = self.laser_penalty_duration
            self.laser_hit_feedback_timer = 1.0

            self.feedback = "LASER HIT! SECURITY +10"

            if hit_rect is not None:
                self._spawn_sparks(hit_rect.center,
                                   (255, 125, 145), (130, 100, 255))

            self.game.security.increase(10)
            self.game.score.penalize(10)

            self.laser_clock = 0.0

    def _rect_touches_active_laser(self, rect):
        if (self.current_room_number() == 3 and self.core_state == "pulse"
                and self._core_ring_hits_rect(rect)):
            return True
        for index, laser in enumerate(self.lasers):
            if self.laser_phase(index) != "active":
                continue
            if (laser.get("axis") == "r" and self.current_room_number() == 3
                    and self.core_state == "offline"):
                continue
            if (self._scanner_hits_rect(laser, rect) if laser.get("axis") == "r"
                    else rect.colliderect(self._laser_rect(laser))):
                return True
        if any(self.floor_zone_phase(i) == "active" and rect.colliderect(zone)
               for i, zone in enumerate(self.floor_zones)):
            return True
        return any(emitter["state"] == "active"
                   and self._emitter_beam_hits_rect(emitter, rect)
                   for emitter in self.emitters)

    # =========================================================
    # ROOM / PROGRESSION
    # =========================================================

    def current_room_number(self):
        """Return the checkpoint represented by the active RoomMap room."""
        return self.current_checkpoint

    def current_room_name(self):
        return f"CHECKPOINT {self.current_room_number()}"

    def _update_cameras(self, dt):
        """Advance Room 2's cameras; True when a camera spots a player this frame.

        A sighting is ignored while the hostile robot is alerting or chasing,
        while its detection cooldown runs, or while the shared hazard cooldown
        runs, so one mistake is never charged twice.
        """
        bank = self.camera_bank
        if bank is None:
            return False
        if self.gate2.is_open() and bank.on:
            bank.switch_off()
        suppressed = (self.laser_penalty_cooldown > 0
                      or self.robot_state in ("ALERT", "CHASE")
                      or self.robot_detection_cooldown > 0)
        rects = [] if suppressed else self._player_rects()
        spotted = bank.update(dt, rects)
        return spotted is not None and not suppressed

    def _camera_hit(self):
        """Camera sighting: score only (team rule), shared cooldown, robot not double-charged."""
        self.laser_penalty_cooldown = self.laser_penalty_duration
        self.laser_hit_feedback_timer = 1.0
        self.robot_detection_cooldown = max(self.robot_detection_cooldown,
                                            self.laser_penalty_duration)
        self.feedback = "CAMERA SPOTTED! SCORE -10"
        if self.game:
            self.game.score.penalize(10)
        if self.camera_bank is not None:
            self.camera_bank.rearm()

    def setup_room_hazards(self):
        """Create laser patterns for the current room."""

        room = self.current_room_number()
        difficulty_name = self.get_selected_difficulty()
        self.hazard_speed_scale = {
            "easy": 0.90, "medium": 1.0, "hard": 1.10,
        }[difficulty_name]
        self.robot_speed_scale = {
            "easy": 0.92, "medium": 1.0, "hard": 1.08,
        }[difficulty_name]
        self.emitter_warning_scale = {
            "easy": 1.15, "medium": 1.0, "hard": 0.92,
        }[difficulty_name]
        self.hazard_warning_scale = self.emitter_warning_scale

        request = getattr(self, "room_requests", {}).get(room)
        fires = request["fires"] if request else None      # the room does what its board says
        self.camera_bank = (patrol_cameras.CameraBank(difficulty_name, active=fires)
                            if room == 2 else None)
        self.lit_pads = set(fires) if room == 1 and request else None
        self.core_vent_after = len(fires) if room == 3 and request else None

        laser_patterns = {
            1: [
                {
                    "axis": "r", "cx": 475, "cy": 310, "half": 386,
                    "angle": 0.0, "direction": 1, "speed": 32,
                    "beam_offsets": (0.0,), "beam_width": 14,
                    "danger_radius": 145,
                    "layout_radius": 145,
                    "warning_duration": 0.90 * self.hazard_warning_scale,
                    "active_duration": 1.0,
                    "cooldown_duration": 5.2,
                    "phase_offset": 2.2,
                },
            ],

            2: [
                # Horizontal laser barrier guarding the central-upper crossing lane
                # between the override terminal and the mid-corridor route.
                {
                    "x": 270,
                    "y": 212,
                    "width": 165,
                    "min_x": 230,
                    "max_x": 495 - 165,
                    "direction": 1,
                    "speed": 145,
                    "axis": "x",
                    "warning_duration": 1.0 * self.hazard_warning_scale,
                    "active_duration": 1.25,
                    "cooldown_duration": 4.2,
                    "phase_offset": 0.0,
                },
                # Vertical laser barrier at a separate downstream crossing point
                # between Cover 3 and the Gate 2 approach bay (zero visual overlap).
                {
                    "axis": "y",
                    "x": 638,
                    "y": 195.0,
                    "length": 115,
                    "top": 170,
                    "bottom": 425,
                    "direction": 1,
                    "speed": 58,
                    "warning_duration": 1.0 * self.hazard_warning_scale,
                    "active_duration": 1.25,
                    "cooldown_duration": 4.2,
                    "phase_offset": 1.8,
                },
            ],

            3: [
                {
                    # One bottom lane. Phase offsets keep every laser's
                    # original start time after the second lane was removed.
                    "x": 255,
                    "y": 415,
                    "direction": 1,
                    "speed": 175,
                    "axis": "x",
                    "max_x": 540,
                },
                {
                    # Right-side crossing, well clear of the core's ring.
                    "axis": "y", "x": 760, "y": 240.0, "length": 80,
                    "top": 235, "bottom": 335, "direction": -1, "speed": 52,
                    "phase_offset": 2.0,
                },
                {
                    "axis": "r", "cx": 520, "cy": 285, "half": 64,
                    "angle": 35.0, "direction": -1, "speed": 38,
                    "beam_offsets": (0.0, 90.0), "beam_width": 16,
                    "danger_radius": 62, "phase_offset": 2.5,
                },
            ],
        }

        self.lasers = [
            laser.copy()
            for laser in laser_patterns[room]
        ]
        rotation_scale = {"easy": 0.82, "medium": 1.0, "hard": 1.22}.get(
            difficulty_name, 1.0)
        for laser in self.lasers:
            if laser.get("axis") == "r":
                laser["speed"] *= rotation_scale
            else:
                laser["speed"] *= self.hazard_speed_scale

        zone_left, zone_right = ((190, 760), (230, 790), (235, 780))[room - 1]
        for laser in self.lasers:
            if laser.get("axis", "x") == "x":
                laser.setdefault("min_x", zone_left)
                w = laser.get("width", self.laser_width)
                laser.setdefault("max_x", zone_right - w)
                laser["x"] = min(max(laser["x"], laser["min_x"]), laser["max_x"])

        self.room_pattern_name = self.ROOM_NAMES[room]
        emitter_specs = {
            1: [
                {"mount": "wall", "origin": (80, 235),
                 "trigger": pygame.Rect(180, 170, 590, 260),
                 "angle": 0.0, "min_angle": -52.0, "max_angle": 52.0,
                 "beam_length": 420.0, "beam_width": 10, "turn_rate": 62.0,
                 "sync_lasers": (0,)},
            ],
            2: [
                # Tracking laser emitter mounted near Gate 2 for the final security challenge
                {"mount": "floor", "origin": (758, 424),
                 "trigger": pygame.Rect(655, 185, 185, 235),
                 "angle": -110.0, "min_angle": -162.0, "max_angle": -35.0,
                 "beam_length": 235.0, "beam_width": 10, "turn_rate": 56.0,
                 "sync_lasers": (1,)},
            ],
            3: [
                {"mount": "ceiling", "origin": (740, 172),
                 "trigger": pygame.Rect(640, 195, 170, 205),
                 "angle": 132.0, "min_angle": 94.0, "max_angle": 174.0,
                 "beam_length": 275.0, "beam_width": 10, "turn_rate": 60.0,
                 "sync_lasers": (0, 1, 2)},
            ],
        }
        self.emitters = []
        for spec in emitter_specs[room]:
            emitter = dict(spec)
            player_width, player_height = 32, 32
            target_area = emitter["trigger"].inflate(player_width,
                                                       player_height)
            ox, oy = emitter["origin"]
            farthest_target = max(
                math.hypot(x - ox, y - oy)
                for x, y in ((target_area.left, target_area.top),
                             (target_area.right, target_area.top),
                             (target_area.right, target_area.bottom),
                             (target_area.left, target_area.bottom))
            )
            emitter["beam_length"] = max(
                emitter["beam_length"], farthest_target + 2.0)
            emitter["turn_rate"] *= self.hazard_speed_scale
            emitter.update({
                "state": "closed", "timer": 0.0, "target": None,
                "open_time": 0.28,
                "track_time": (0.36 if room in (1, 3) else 0.42 if room == 2 else 0.0),
                "warn_time": ((1.65 if room == 1 else 1.25 if room == 2 else 1.2)
                              * self.emitter_warning_scale),
                "lock_time": 0.18 if room in (1, 3) else 0.22 if room == 2 else 0.0,
                "active_time": 0.72, "retract_time": 0.24,
                "cooldown_time": 2.8 if room == 2 else 2.4,
            })
            self.emitters.append(emitter)

        self.floor_zones = []
        self.safe_zones = {
            1: [pygame.Rect(80, 386, 140, 54),
                pygame.Rect(265, 162, 132, 52),
                pygame.Rect(650, 384, 136, 52)],
            2: [pygame.Rect(80, 386, 140, 54)],
            3: [pygame.Rect(80, 386, 140, 54), pygame.Rect(668, 332, 70, 46)],
        }[room]

        self.robot_speed = (120 + ((room - 1) * 30)) * self.robot_speed_scale

        self.time_limit = self.base_time_limit - (room - 1)
        if self.core_vent_after and self.core_vent_after > 1:
            self.time_limit += 5          # waiting out a second board pulse costs ~9 s; the clock pays some back
        self.time_left = self.time_limit

        # Room 2 waypoints navigate cleanly around Cover 2 (275,295,86,52)
        # and Cover 3 (505,225,86,52) through the open lower-left/middle area.
        self.robot_waypoints = {
            1: [],
            2: [
                (145, 240),
                (390, 240),
                (405, 365),
                (165, 340),
            ],
            3: [(260, 168), (600, 168)],
        }[room]
        self.robot_waypoint_index = 0
        self.robot_waypoint_pause = 0.0
        if self.robot_waypoints:
            self.robot_x, self.robot_y = self.robot_waypoints[0]
            self.robot_left_boundary = min(point[0] for point in self.robot_waypoints)
            self.robot_right_boundary = max(point[0] for point in self.robot_waypoints)
        else:
            self.robot_x, self.robot_y = 310, 172
            self.robot_left_boundary, self.robot_right_boundary = 310, 650
        self.robot_direction = 1
        self.robot_state = "PATROL"
        self.robot_aim_vector = None
        self.robot_patrol_vector = pygame.Vector2(1, 0.25).normalize()
        self.robot_scan_offset = 0.0
        self.robot_last_known = None
        self.robot_search_timer = 0.0
        self.robot_alert_duration = 0.75
        self.robot_detection_cooldown = 0
        self.robot_alert = False
        self.robot_alert_timer = 0

        self.room2_override_panel_open = False
        self.room2_gate_challenge_survived = False
        self.room2_gate_challenge_armed = False
        self.room2_gate_question_solved = False
        self.room2_robot_disabled_timer = 0.0
        self.room2_overload_warning_timer = 0.0
        self.room2_overload_active_timer = 0.0
        self.room2_overload_cooldown = 8.5
        self._reset_core_state(difficulty_name)

        self.laser_penalty_cooldown = 0.0
        self.laser_hit_feedback_timer = 0.0
        self.laser_clock = 0.0

    def try_room_transition(self):
        """Move through the active room's unlocked gate into the next room."""
        if not self.game or not hasattr(self.game, "player"):
            return
        stage = self.current_room_number()
        gate = (self.gate1, self.gate2, self.gate3)[stage - 1]
        if not gate.is_open():
            return

        players = self._player_rects()
        trigger = self.exit_triggers.get(stage)
        if trigger is not None and not all(rect.colliderect(trigger) for rect in players):
            return
        if stage == 3:
            if all(rect.colliderect(self.final_exit_rect) or rect.left >= gate.rect.right
                   for rect in players):
                self.complete_level()
            return

        if not players:
            return
        from_pos = [rect.topleft for rect in players]
        snapshot = self._tx_snapshot()
        if not self.room_map.check_exit(players[0]):
            return
        if len(players) > 1:
            players[1].topleft = self.room_entry_spawns[self.room_map.current_name][1]
        to_pos = [rect.topleft for rect in players]
        self.room = self.room_map.current
        self.barrier_walls = self.room.walls
        self.current_checkpoint = stage + 1
        self.current_question_number = stage
        self.setup_room_hazards()
        self.load_current_question()
        self._vis_state()["sparks"].clear()
        self.room_transition_title = self.ROOM_TITLES[stage + 1]
        self.room_transition_timer = self.room_transition_duration
        self.feedback = f"CHECKPOINT {stage} CLEARED! ENTERED CHECKPOINT {stage + 1}."
        self._begin_gate_transition(stage, snapshot, players, from_pos, to_pos)

    def _robot_eye_center(self):
        return (self.robot_x + self.robot_width / 2.0,
                self.robot_y + self.robot_height)

    def _robot_vision_direction(self):
        if self.robot_aim_vector is not None and self.robot_aim_vector.length_squared():
            return self.robot_aim_vector.normalize()
        base = getattr(self, "robot_patrol_vector", None)
        if base is None:
            base = pygame.Vector2(self.robot_direction * 0.62, 0.78)
        return base.rotate_rad(self.robot_scan_offset).normalize()

    def _has_line_of_sight(self, start, end):
        start = (int(start[0]), int(start[1]))
        end = (int(end[0]), int(end[1]))
        if any(wall.clipline(start, end) for wall in self.room.walls):
            return False
        return not any(not gate.is_open() and gate.rect.clipline(start, end)
                       for gate in self.room.gates)

    def robot_can_see_rect(self, rect):
        if self.current_room_number() == 2 and self.room2_robot_disabled_timer > 0:
            return False
        if self.player_in_safe_pocket(rect):
            return False
        origin = pygame.Vector2(self._robot_eye_center())
        delta = pygame.Vector2(rect.center) - origin
        distance = delta.length()
        scan_r = self.robot_scan_radius + (
            28 if self.current_room_number() == 2 and self.room2_overload_active_timer > 0 else 0
        )
        if not distance or distance > scan_r:
            return False
        if self._robot_vision_direction().dot(delta.normalize()) < math.cos(math.radians(self.robot_vision_half_angle)):
            return False
        return self._has_line_of_sight(origin, rect.center)

    def _move_robot_towards(self, point, dt, speed):
        """Move the sentry through the active room's actual collision map."""
        target = pygame.Vector2(point)
        current = pygame.Vector2(self.robot_x, self.robot_y)
        delta = target - current
        distance = delta.length()
        if distance <= 0.001:
            return True
        direction = delta / distance
        step = min(distance, max(0.0, speed * dt))
        candidate = current + direction * step
        candidate_rect = pygame.Rect(round(candidate.x), round(candidate.y),
                                     self.robot_width, self.robot_height)
        if self.room_map.blocked(candidate_rect):
            moved = False
            # Try sliding along X or Y, or steering around cover corners
            perp_left = pygame.Vector2(-direction.y, direction.x) * step
            perp_right = pygame.Vector2(direction.y, -direction.x) * step
            for axis_candidate in (
                pygame.Vector2(candidate.x, current.y),
                pygame.Vector2(current.x, candidate.y),
                current + perp_left,
                current + perp_right,
            ):
                if axis_candidate.distance_squared_to(current) < 0.01:
                    continue
                test_rect = pygame.Rect(round(axis_candidate.x), round(axis_candidate.y),
                                        self.robot_width, self.robot_height)
                if not self.room_map.blocked(test_rect):
                    candidate = axis_candidate
                    moved = True
                    break
            if not moved:
                return None
        self.robot_x, self.robot_y = float(candidate.x), float(candidate.y)
        if abs(direction.x) > 0.08:
            self.robot_direction = 1 if direction.x > 0 else -1
        if self.robot_state == "PATROL":
            self.robot_patrol_vector = direction
        return distance <= step + 0.5

    def _robot_raise_alert(self, target):
        """Telegraph a valid sighting before the robot pursues it."""
        self.robot_state = "ALERT"
        self.robot_alert = True
        self.robot_alert_timer = 0.65
        self.robot_last_known = pygame.Vector2(target.center)
        self.robot_aim_vector = self.robot_last_known - pygame.Vector2(self._robot_eye_center())
        self.robot_scan_offset = 0.0
        self.feedback = "SECURITY ALERT! BREAK LINE OF SIGHT OR HIDE."
        if self.robot_detection_cooldown <= 0 and self.game:
            self.game.security.increase(20)
            self.game.score.penalize(10)
            self.robot_detection_cooldown = 4.0

    def _trigger_room2_overload_warning(self):
        """Start the short, telegraphed overload warning in Room 2."""
        if self.current_room_number() != 2 or self.room2_robot_disabled_timer > 0:
            return
        self.room2_overload_warning_timer = self.room2_overload_warning_duration
        self.feedback = "ROBOT OVERLOAD! SEEK COVER OR USE OVERRIDE CONSOLE!"
        if self.game and hasattr(self.game, "sound") and hasattr(self.game.sound, "play"):
            try:
                self.game.sound.play("alert")
            except Exception:
                pass

    def _update_robot(self, dt):
        """Waypoint patrol, scanning, investigate, chase, overload, and disabled states."""
        if not self.robot_waypoints:
            return
        dt = max(0.0, dt)
        room_num = self.current_room_number()

        # Handle temporary shutdown from the Room 2 Override Terminal
        if room_num == 2 and self.room2_robot_disabled_timer > 0:
            self.room2_robot_disabled_timer = max(0.0, self.room2_robot_disabled_timer - dt)
            self.robot_state = "DISABLED"
            self.robot_alert = False
            self.robot_aim_vector = None
            if self.room2_robot_disabled_timer == 0.0:
                self.robot_state = "PATROL"
                self.feedback = "SENTRY REBOOTED — PATROL RESUMED."
            return

        # Handle Room 2 Robot Overload cycle
        if room_num == 2:
            if self.room2_overload_warning_timer > 0:
                self.room2_overload_warning_timer = max(0.0, self.room2_overload_warning_timer - dt)
                self.robot_scan_phase += dt * 5.0
                if self.room2_overload_warning_timer == 0.0:
                    self.room2_overload_active_timer = self.room2_overload_active_duration
                return
            elif self.room2_overload_active_timer > 0:
                self.room2_overload_active_timer = max(0.0, self.room2_overload_active_timer - dt)
                if self.room2_overload_active_timer == 0.0:
                    self.room2_overload_cooldown = 11.0
            else:
                self.room2_overload_cooldown = max(0.0, self.room2_overload_cooldown - dt)
                if self.room2_overload_cooldown == 0.0 and self.robot_state in ("PATROL", "SCAN", "SEARCH"):
                    self._trigger_room2_overload_warning()
                    return

        self.robot_detection_cooldown = max(0.0, self.robot_detection_cooldown - dt)
        overload_mult = 1.22 if (room_num == 2 and self.room2_overload_active_timer > 0) else 1.0
        self.robot_scan_phase += dt * 2.4 * overload_mult

        exposed = [rect for rect in self._player_rects()
                   if not self.player_in_safe_pocket(rect)]
        visible = [rect for rect in exposed if self.robot_can_see_rect(rect)]
        seen_player = min(visible, key=lambda rect: pygame.Vector2(rect.center).distance_to(
            self._robot_eye_center())) if visible else None

        if seen_player is not None:
            self.robot_last_known = pygame.Vector2(seen_player.center)
            if self.robot_state not in ("ALERT", "CHASE"):
                self._robot_raise_alert(seen_player)
            elif self.robot_state == "ALERT":
                self.robot_aim_vector = self.robot_last_known - pygame.Vector2(self._robot_eye_center())

        if self.robot_state == "ALERT":
            self.robot_alert = True
            self.robot_aim_vector = self.robot_last_known - pygame.Vector2(self._robot_eye_center())
            self.robot_alert_timer = max(0.0, self.robot_alert_timer - dt)
            if self.robot_alert_timer == 0:
                self.robot_state = "CHASE" if seen_player is not None else "INVESTIGATE"
            return

        if self.robot_state == "CHASE":
            self.robot_alert = True
            if seen_player is None:
                self.robot_state = "INVESTIGATE"
                self.robot_aim_vector = None
            else:
                self.robot_aim_vector = pygame.Vector2(seen_player.center) - pygame.Vector2(self._robot_eye_center())
                target = pygame.Vector2(seen_player.center) - pygame.Vector2(
                    self.robot_width / 2, self.robot_height / 2)
                chase_speed = (self.robot_speed + self.robot_hunt_speed_bonus) * overload_mult
                moved = self._move_robot_towards(target, dt, chase_speed)
                if moved is None:
                    self.robot_state = "INVESTIGATE"
                    self.robot_aim_vector = None
            return

        self.robot_alert = self.robot_state in ("INVESTIGATE", "SEARCH")
        self.robot_aim_vector = None

        if self.robot_state == "INVESTIGATE":
            self.robot_scan_offset = 0.0
            target = (self.robot_last_known - pygame.Vector2(
                self.robot_width / 2, self.robot_height / 2)
                if self.robot_last_known is not None else None)
            if self.robot_last_known is not None:
                self.robot_aim_vector = (self.robot_last_known
                                         - pygame.Vector2(self._robot_eye_center()))
            progress = (None if target is None else
                        self._move_robot_towards(target, dt, self.robot_speed * 0.9 * overload_mult))
            if target is None or progress is True or progress is None:
                self.robot_state = "SEARCH"
                self.robot_search_timer = 2.8
            return

        if self.robot_state == "SEARCH":
            self.robot_search_timer = max(0.0, self.robot_search_timer - dt)
            self.robot_scan_offset = math.sin(self.robot_scan_phase * 1.8) * 0.85
            if self.robot_search_timer == 0:
                self.robot_state = "PATROL"
                self.robot_scan_offset = 0.0
                self.robot_waypoint_index = min(
                    range(len(self.robot_waypoints)),
                    key=lambda i: pygame.Vector2(self.robot_waypoints[i]).distance_to(
                        (self.robot_x, self.robot_y)),
                )
            return

        self.robot_scan_offset = 0.0
        if self.robot_state == "SCAN":
            self.robot_waypoint_pause = max(0.0, self.robot_waypoint_pause - dt)
            self.robot_scan_offset = math.sin(self.robot_scan_phase * 2.0) * 0.72
            if self.robot_waypoint_pause == 0:
                self.robot_waypoint_index = (self.robot_waypoint_index + 1) % len(self.robot_waypoints)
                self.robot_state = "PATROL"
            return

        if self.robot_state == "PATROL":
            waypoint = self.robot_waypoints[self.robot_waypoint_index]
            moved = self._move_robot_towards(waypoint, dt, self.robot_speed * overload_mult)
            if moved is True:
                self.robot_state = "SCAN"
                self.robot_waypoint_pause = 0.8
            elif moved is None:
                self.robot_waypoint_index = (self.robot_waypoint_index + 1) % len(self.robot_waypoints)

    # =========================================================
    # ROOM 3 VISUAL POLISH (drawing only; no gameplay state is touched)
    # Hazard colours: yellow = warning, red = active, cyan = cooldown.
    # =========================================================

    R3_YELLOW = (255, 205, 60)
    R3_RED = (255, 62, 66)
    R3_CYAN = (72, 190, 255)

    def _r3_phase_colour(self, phase):
        """Warning is yellow, firing is red, cooldown/idle is cyan."""
        return {"warning": self.R3_YELLOW, "active": self.R3_RED}.get(
            phase, self.R3_CYAN)

    def _r3_device(self, surface, anchor, facing, colour, phase):
        """A security emitter module whose glowing lens sits on `anchor`.

        Drawn pointing right, then rotated; the lens colour, blink and halo
        follow the real hazard phase passed in by the caller.
        """
        t = self._seconds()
        lit = True if phase != "warning" else int(t * 8) % 2 == 0
        pulse = 0.5 + 0.5 * math.sin(t * (8.0 if phase == "active" else 2.5))
        lens_colour = colour if lit else self._mix(colour, (20, 22, 34), 0.75)

        size = 40
        cx = cy = size // 2
        dev = pygame.Surface((size, size), pygame.SRCALPHA)
        body = pygame.Rect(cx - 14, cy - 11, 22, 22)
        pygame.draw.rect(dev, (10, 12, 24), body.inflate(4, 4), border_radius=6)
        pygame.draw.rect(dev, (36, 40, 64), body, border_radius=5)
        pygame.draw.rect(dev, (128, 116, 176), body, 1, border_radius=5)
        for i in range(3):
            pygame.draw.line(dev, (62, 68, 102), (body.x + 4, body.y + 6 + i * 5),
                             (body.x + 9, body.y + 6 + i * 5), 1)
        for yy in (body.y + 5, body.bottom - 6):
            pygame.draw.circle(dev, (10, 12, 20), (body.x + 14, yy), 3)
            pygame.draw.circle(dev, lens_colour, (body.x + 14, yy), 2)
        flange = pygame.Rect(body.right - 1, cy - 7, 6, 14)
        pygame.draw.rect(dev, (56, 62, 92), flange, border_radius=2)
        pygame.draw.rect(dev, (156, 146, 200), flange, 1, border_radius=2)
        pygame.draw.circle(dev, (8, 10, 18), (cx + 12, cy), 6)
        pygame.draw.circle(dev, lens_colour, (cx + 12, cy), 4)
        pygame.draw.circle(dev, (255, 255, 255), (cx + 11, cy - 1), 1)

        angle = {"right": 0, "up": 90, "left": 180, "down": 270}[facing]
        rotated = pygame.transform.rotate(dev, angle)
        offset = pygame.math.Vector2(12, 0).rotate(-angle)
        centre = (anchor[0] - offset.x, anchor[1] - offset.y)

        halo_alpha = (95 + 70 * pulse) if phase == "active" else (
            85 if phase == "warning" and lit else 38)
        halo_r = 17 if phase == "active" else 13
        halo = pygame.Surface((halo_r * 2 + 2, halo_r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(halo, tuple(colour) + (int(halo_alpha),),
                           (halo_r + 1, halo_r + 1), halo_r)
        pygame.draw.circle(halo, tuple(colour) + (int(halo_alpha * 0.6),),
                           (halo_r + 1, halo_r + 1), max(2, halo_r // 2))
        surface.blit(halo, halo.get_rect(center=(int(anchor[0]), int(anchor[1]))))
        surface.blit(rotated, rotated.get_rect(center=(int(centre[0]), int(centre[1]))))

    def _r3_emitter_overlay(self, surface, emitter, housing, colour):
        """Tracking-laser head: lamp row, glowing lens, state tag, lock reticle."""
        state = emitter["state"]
        t = self._seconds()
        slow = 0.5 + 0.5 * math.sin(t * 3.0)
        fast = int(t * 10) % 2 == 0

        # Three-lamp progress row: track -> warn -> lock-on (red when firing).
        lit_count = {"opening": 1, "tracking": 1, "warning": 2,
                     "locking": 3, "active": 3}.get(state, 0)
        row_y = housing.top + 5
        for i in range(3):
            lamp = (housing.centerx - 10 + i * 10, row_y)
            pygame.draw.circle(surface, (22, 24, 38), lamp, 4)
            if i < lit_count and not (state == "locking" and not fast):
                pygame.draw.circle(surface, colour, lamp, 3)
            elif lit_count == 0:
                dim = self._mix(colour, (22, 24, 38), 0.45 + 0.4 * (1 - slow)
                                if i == 0 else 0.8)
                pygame.draw.circle(surface, dim, lamp, 2)
            else:
                pygame.draw.circle(surface, (46, 50, 72), lamp, 2)

        # Glowing lens ring on the aperture side.
        mount = emitter["mount"]
        if mount == "ceiling":
            lens = (housing.centerx, housing.bottom - 1)
        elif mount == "floor":
            lens = (housing.centerx, housing.top + 1)
        else:
            lens = (housing.right - 1, housing.centery)
        strong = state in ("warning", "locking", "active")
        glow_r = 16 if state == "active" else 12
        glow = pygame.Surface((glow_r * 2 + 2, glow_r * 2 + 2), pygame.SRCALPHA)
        alpha = 130 if state == "active" else 90 if strong else 46
        if state == "locking" and not fast:
            alpha = 40
        pygame.draw.circle(glow, tuple(colour) + (alpha,),
                           (glow_r + 1, glow_r + 1), glow_r)
        surface.blit(glow, glow.get_rect(center=lens))
        pygame.draw.circle(surface, (8, 10, 18), lens, 6)
        pygame.draw.circle(surface, colour, lens, 4, 2)
        pygame.draw.circle(surface, colour if state != "active" else (255, 210, 210),
                           lens, 2)

        # State tag, so warning / lock-on / firing can be read at a glance.
        text = {"closed": "STANDBY", "pending": "STANDBY", "opening": "ARMING",
                "tracking": "TRACKING", "warning": "WARNING", "locking": "LOCK-ON",
                "active": "FIRING", "retracting": "COOLING",
                "cooldown": "COOLING"}[state]
        label = self._font(15).render(text, True, colour)
        tag = label.get_rect().inflate(12, 6)
        tag.midright = (housing.left - 6, housing.centery)
        pygame.draw.rect(surface, (10, 12, 22), tag, border_radius=5)
        pygame.draw.rect(surface, colour, tag, 1, border_radius=5)
        if not (state == "locking" and not fast):
            surface.blit(label, label.get_rect(center=tag.center))

        # Lock-on reticle: brackets close in on the aimed target.
        if state == "locking" and emitter.get("target") is not None:
            target = tuple(map(int, emitter["target"]))
            remaining = max(0.0, emitter["timer"]) / max(0.001, emitter["lock_time"])
            r = int(9 + 13 * remaining)
            ink = (255, 255, 255) if fast else colour
            for sx, sy in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                px, py = target[0] + sx * r, target[1] + sy * r
                pygame.draw.line(surface, ink, (px, py), (px - sx * 6, py), 2)
                pygame.draw.line(surface, ink, (px, py), (px, py - sy * 6), 2)

    def _draw_core_floor(self, surface, center, laser, phase):
        """Subtle industrial deck markings and warning lights round the core.

        Purely decorative; the reactor itself is drawn separately and the
        lights simply mirror the rotor's real laser phase.
        """
        cx, cy = int(center[0]), int(center[1])
        deck_r = int(min(laser.get("danger_radius", laser["half"] + 18) + 22, 104))
        size = deck_r * 2 + 16
        mid = size // 2

        def build():
            deck = pygame.Surface((size, size), pygame.SRCALPHA)
            pygame.draw.circle(deck, (34, 40, 68, 70), (mid, mid), deck_r)
            pygame.draw.circle(deck, (96, 104, 150, 120), (mid, mid), deck_r, 1)
            pygame.draw.circle(deck, (70, 78, 120, 80), (mid, mid), deck_r - 7, 1)
            for deg in range(0, 360, 15):
                a = math.radians(deg)
                inner = deck_r - (7 if deg % 45 == 0 else 4)
                pygame.draw.line(
                    deck, (120, 128, 175, 110),
                    (mid + math.cos(a) * inner, mid + math.sin(a) * inner),
                    (mid + math.cos(a) * deck_r, mid + math.sin(a) * deck_r), 1)
            # Yellow / black hazard stripes on the four compass arcs.
            for centre_deg in (0, 90, 180, 270):
                for k in range(-4, 4):
                    start = math.radians(centre_deg + k * 4)
                    end = math.radians(centre_deg + k * 4 + 4)
                    ink = (232, 190, 62, 170) if k % 2 == 0 else (24, 26, 42, 190)
                    pts = [(mid + math.cos(start) * (deck_r - 2),
                            mid + math.sin(start) * (deck_r - 2)),
                           (mid + math.cos(end) * (deck_r - 2),
                            mid + math.sin(end) * (deck_r - 2)),
                           (mid + math.cos(end) * (deck_r - 9),
                            mid + math.sin(end) * (deck_r - 9)),
                           (mid + math.cos(start) * (deck_r - 9),
                            mid + math.sin(start) * (deck_r - 9))]
                    pygame.draw.polygon(deck, ink, pts)
            return deck

        deck = self._cached(("r3_core_deck", deck_r), build)
        clip_before = surface.get_clip()
        surface.set_clip(self.room.bounds)
        surface.blit(deck, (cx - mid, cy - mid))

        # Warning lights on the diagonals mirror the rotor's real phase.
        t = self._seconds()
        flash = int(t * 8) % 2 == 0
        if phase == "active":
            colour, lit = self.R3_RED, True
        elif phase == "warning":
            colour, lit = self.R3_YELLOW, flash
        else:
            colour, lit = self.R3_CYAN, True
        for diag in (45, 135, 225, 315):
            a = math.radians(diag)
            lamp = (int(cx + math.cos(a) * (deck_r - 2)),
                    int(cy + math.sin(a) * (deck_r - 2)))
            pygame.draw.circle(surface, (14, 16, 28), lamp, 6)
            pygame.draw.circle(surface, (88, 96, 140), lamp, 6, 1)
            if lit:
                halo = pygame.Surface((26, 26), pygame.SRCALPHA)
                pygame.draw.circle(halo, tuple(colour) + (70,), (13, 13), 12)
                surface.blit(halo, halo.get_rect(center=lamp))
                pygame.draw.circle(surface, colour, lamp, 3)
            else:
                pygame.draw.circle(surface, self._mix(colour, (14, 16, 28), 0.8),
                                   lamp, 3)
        surface.set_clip(clip_before)

    def _draw_room3_vault(self, surface, gate):
        """Approved vault door: chevrons, status tag, 3 lamps, green unlock."""
        t = self._seconds()
        rect = gate.rect
        progress = self._gate_progress(gate)
        locked = gate.state == "locked"
        opening = (not locked) and progress < 1.0
        red, amber, green = (215, 70, 70), (240, 200, 70), (70, 215, 140)
        if locked:
            tone = red
        elif progress < 0.5:
            tone = self._mix(red, amber, progress * 2)
        else:
            tone = self._mix(amber, green, (progress - 0.5) * 2)

        frame = rect.inflate(34, 26)
        pygame.draw.rect(surface, (10, 12, 24), frame, border_radius=9)
        pygame.draw.rect(surface, (46, 50, 78), frame.inflate(-6, -6),
                         border_radius=7)
        for y in range(frame.top + 6, frame.bottom - 12, 14):
            for x in (frame.left + 4, frame.right - 12):
                pygame.draw.polygon(
                    surface, (230, 190, 70) if (y // 14) % 2 else (30, 32, 48),
                    [(x, y), (x + 8, y + 7), (x, y + 14)])
        pygame.draw.rect(surface, tone, frame, 2, border_radius=9)
        pygame.draw.rect(surface, (8, 12, 22), rect)

        # Door leaves retract with the same eased progress as the gate logic.
        leaf_h = int(round(rect.height * (1.0 - progress) / 2.0))
        if leaf_h > 0:
            leaf_colour = (38, 40, 62) if locked else self._mix(tone, (24, 27, 42), 0.35)
            for leaf in (pygame.Rect(rect.x + 1, rect.y, rect.width - 2, leaf_h),
                         pygame.Rect(rect.x + 1, rect.bottom - leaf_h,
                                     rect.width - 2, leaf_h)):
                pygame.draw.rect(surface, leaf_colour, leaf)
                for dy in range(leaf.top + 4, leaf.bottom - 4, 18):
                    pygame.draw.rect(surface, (38, 40, 62) if locked else leaf_colour,
                                     (leaf.x, dy, leaf.width, 12))
                    pygame.draw.line(surface, tone, (leaf.x, dy + 6),
                                     (leaf.right - 1, dy + 6), 1)

        if locked or progress < 0.5:
            c = rect.center
            pygame.draw.arc(surface, (240, 240, 245),
                            (c[0] - 8, c[1] - 17, 16, 20), 0, 3.1416, 3)
            pygame.draw.rect(surface, (240, 240, 245),
                             (c[0] - 10, c[1] - 5, 20, 16), border_radius=3)
            pygame.draw.circle(surface, (60, 20, 24), (c[0], c[1] + 2), 3)

        # Green unlock animation: glow, expanding ring and flowing arrows.
        if not locked:
            ease = self._ease_out_cubic(progress)
            glow = pygame.Surface((120, 260), pygame.SRCALPHA)
            for i in range(6):
                pygame.draw.rect(glow, (70, 215, 140, int(18 * (0.4 + 0.6 * ease))),
                                 glow.get_rect().inflate(-i * 16, -i * 30))
            surface.blit(glow, glow.get_rect(center=rect.center))
            ring = pygame.Surface((220, 220), pygame.SRCALPHA)
            if opening:
                radius = int(20 + 70 * progress)
                alpha = int(150 * (1.0 - progress) + 40)
            else:
                radius = int(66 + 5 * math.sin(t * 2.5))
                alpha = 90
            pygame.draw.circle(ring, (130, 255, 190, alpha), (110, 110), radius, 3)
            surface.blit(ring, ring.get_rect(center=rect.center))
            for i in range(3):
                cx = rect.left - 26 - i * 14
                strength = 0.45 + 0.55 * (0.5 + 0.5 * math.sin(t * 6.0 - i * 1.2))
                col = self._mix((20, 60, 44), green, strength)
                pygame.draw.polygon(surface, col, [(cx, rect.centery - 10),
                                                   (cx + 9, rect.centery),
                                                   (cx, rect.centery + 10)])

        # Three progress lamps: one per cleared checkpoint.
        cleared = sum(1 for g in self.gates if g.state != "locked")
        for i in range(3):
            lx = frame.centerx - 18 + i * 18
            ly = frame.bottom - 9
            pygame.draw.circle(surface, (14, 16, 28), (lx, ly), 6)
            pygame.draw.circle(surface, green if i < cleared else (110, 50, 55),
                               (lx, ly), 4)

        label = ("GATE 3 · LOCKED" if locked
                 else "GATE 3 · UNLOCKING" if opening else "GATE 3 · OPEN")
        text = self._font(19).render(label, True, tone)
        tag = text.get_rect().inflate(14, 6)
        tag.midbottom = (frame.centerx, frame.top - 2)
        tag.right = min(tag.right, 917)
        tag.top = max(tag.top, 152)
        pygame.draw.rect(surface, (10, 12, 22), tag, border_radius=5)
        pygame.draw.rect(surface, tone, tag, 1, border_radius=5)
        surface.blit(text, text.get_rect(center=tag.center))

        if not locked and progress >= 0.75:
            ex = pygame.transform.rotate(
                self._font(26).render("EXIT", True, (150, 255, 200)), -90)
            surface.blit(ex, ex.get_rect(center=(905, rect.centery)))

        self._draw_sparks(surface)

    # =========================================================
    # ROOM 3: REACTIVE ROTATING CORE + EXPANDING OVERLOAD RING
    # idle -> alert -> charge (warning) -> pulse (ring) -> recovery
    # Everything below is gated to Room 3 (checkpoint 3).
    # =========================================================

    def _reset_core_state(self, difficulty_name="medium"):
        self.core_difficulty = difficulty_name
        self.core_state = "idle"
        self.core_timer = 0.0
        self.core_grace = 0.0
        self.core_cooldown = 0.0
        self.core_radius = self.CORE_HUB_RADIUS
        self.core_hit_players = set()
        self.core_rot_mult = 1.0
        self.core_spin = 0.0
        self.core_pulse_count = 0
        # CORE OVERRIDE terminal (Room 3 only)
        if not hasattr(self, "_r3_rng"):
            self._r3_rng = random.Random()
        pool = [q for q in self.R3_TERMINAL_BANK
                if q["difficulty"] == difficulty_name] or list(self.R3_TERMINAL_BANK)
        self.r3_term_question = self._r3_rng.choice(pool)
        self.r3_term_open = False
        self.r3_term_selected = None
        self.r3_term_hover = None
        self.r3_term_wrong = set()
        self.r3_term_feedback = ""
        self.r3_term_explanation = ""
        self.r3_term_ok = False

    def _core_laser(self):
        """The rotating-core laser (the only 'r' laser in Room 3)."""
        if self.current_room_number() != 3:
            return None
        return next((laser for laser in self.lasers
                     if laser.get("axis") == "r"), None)

    def _core_center(self):
        laser = self._core_laser()
        return (laser["cx"], laser["cy"]) if laser else None

    @staticmethod
    def _rect_distance(rect, point):
        """Shortest distance from a point to a rectangle (0 when inside)."""
        dx = max(rect.left - point[0], 0, point[0] - rect.right)
        dy = max(rect.top - point[1], 0, point[1] - rect.bottom)
        return math.hypot(dx, dy)

    def _core_player_near(self):
        """True when any exposed player (each checked separately) is close."""
        center = self._core_center()
        if center is None:
            return False
        return any(self._rect_distance(rect, center) <= self.CORE_PROXIMITY
                   for rect in self._player_rects()
                   if not self.player_in_safe_pocket(rect))

    def _core_can_start(self):
        """Do not stack the overload on another hazard's firing window."""
        core = self._core_laser()
        if core is not None and self.laser_phase(self.lasers.index(core)) == "active":
            return False
        return not any(emitter["state"] in ("warning", "locking", "active")
                       for emitter in self.emitters)

    def _update_core(self, dt):
        if self.current_room_number() != 3:
            self.core_state = "idle"
            self.core_rot_mult = 1.0
            return
        difficulty = self.core_difficulty
        state = self.core_state
        near = self._core_player_near()

        if state == "offline":
            # Shut down by the CORE OVERRIDE terminal: no arms, no ring.
            self.core_timer -= dt
            if self.core_timer <= 0:
                self.core_state = "idle"
                self.core_cooldown = self.CORE_COOLDOWN[difficulty]
                self.feedback = "CORE REBOOTED."
        elif state == "idle":
            self.core_cooldown = max(0.0, self.core_cooldown - dt)
            if near and self.core_cooldown == 0.0:
                self.core_state = "alert"
                self.core_timer = self.CORE_ALERT_TIME
                self.core_grace = 0.0
        elif state == "alert":
            self.core_grace = 0.0 if near else self.core_grace + dt
            if self.core_grace >= self.CORE_ALERT_GRACE:
                self.core_state = "idle"       # everyone left: stand down
            else:
                self.core_timer -= dt
                if self.core_timer <= 0 and self._core_can_start():
                    self.core_state = "charge"
                    self.core_timer = self.CORE_CHARGE[difficulty]
                    self.feedback = "CORE OVERLOAD CHARGING! MOVE AWAY."
                    self._play_sound("wrong")
        elif state == "charge":
            # The warning is committed: it always completes, then pulses.
            self.core_timer -= dt
            if self.core_timer <= 0:
                self.core_state = "pulse"
                self.core_timer = self.CORE_PULSE[difficulty]
                self.core_radius = self.CORE_HUB_RADIUS
                self.core_hit_players = set()
                self.core_pulse_count += 1
        elif state == "pulse":
            span = self.CORE_RING_MAX - self.CORE_HUB_RADIUS
            self.core_radius = min(
                self.CORE_RING_MAX,
                self.core_radius + span / self.CORE_PULSE[difficulty] * dt)
            self.core_timer -= dt
            if self.core_timer <= 0 or self.core_radius >= self.CORE_RING_MAX:
                if (self.core_vent_after is not None
                        and self.core_pulse_count >= self.core_vent_after):
                    # The board's loop has ended: vent() takes the core offline.
                    self.core_state = "offline"
                    self.core_timer = self.CORE_VENT_TIME
                    self.core_pulse_count = 0
                    self.core_radius = self.CORE_HUB_RADIUS
                    self.feedback = "LOOP ENDED - CORE VENTING. CROSS NOW!"
                else:
                    self.core_state = "recovery"
                    self.core_timer = self.CORE_RECOVERY_TIME
        elif state == "recovery":
            self.core_timer -= dt
            if self.core_timer <= 0:
                self.core_state = "idle"
                self.core_cooldown = self.CORE_COOLDOWN[difficulty]

        target = self.CORE_ROT_MULT[self.core_state]
        self.core_rot_mult += (target - self.core_rot_mult) * min(1.0, dt * 3.0)
        self.core_spin = (self.core_spin
                          + 80.0 * self.core_rot_mult * dt) % 360.0

    def _core_ring_hits_rect(self, rect):
        """Annulus (radius +/- half the ring width) vs rectangle.

        Uses the same radius and width the renderer draws with, so the
        visible ring and its collision cannot drift apart.
        """
        if self.core_state != "pulse":
            return False
        center = self._core_center()
        if center is None:
            return False
        half = self.CORE_RING_WIDTH / 2.0
        near = self._rect_distance(rect, center)
        far = math.hypot(max(abs(rect.left - center[0]), abs(rect.right - center[0])),
                         max(abs(rect.top - center[1]), abs(rect.bottom - center[1])))
        return near <= self.core_radius + half and far >= self.core_radius - half

    def _r3_banner(self):
        """HUD banner (text, fill, ink) for the core's danger states."""
        if self.core_state == "offline":
            return (f"CORE OFFLINE  -  SAFE TO CROSS FOR {max(0.0, self.core_timer):.1f}s",
                    (20, 90, 105, 225), (225, 250, 255))
        if self.core_state == "charge":
            flash = int(self._seconds() * 6) % 2 == 0
            return (f"CORE OVERLOAD IN {max(0.0, self.core_timer):.1f}s  -  MOVE AWAY",
                    (190, 25, 25, 230) if flash else (110, 18, 24, 220),
                    (255, 245, 245))
        if self.core_state == "pulse":
            return ("OVERLOAD PULSE!  KEEP MOVING OUTWARD",
                    (170, 30, 30, 225), (255, 245, 245))
        if self.core_state == "alert":
            return ("CORE ALERT  -  IT HAS DETECTED YOU",
                    (120, 80, 12, 215), (255, 240, 200))
        return None

    def _draw_core_reactor(self, surface, center):
        """Reactor hub, state lighting, proximity hint and the pulse ring."""
        state = self.core_state
        t = self._seconds()
        flash = int(t * 8) % 2 == 0
        palette = {
            "idle": (110, 205, 255), "alert": (255, 190, 70),
            "charge": (255, 70, 70) if flash else (255, 225, 225),
            "pulse": (255, 70, 70), "recovery": (90, 150, 255),
            "offline": (90, 140, 160),
        }
        colour = palette[state]
        cx, cy = int(center[0]), int(center[1])
        clip_before = surface.get_clip()
        surface.set_clip(self.room.bounds)

        # Faint proximity boundary while the core is awake (dotted, not a wall).
        if state in ("alert", "charge"):
            for step in range(0, 360, 12):
                a = math.radians(step + self.core_spin * 0.25)
                p = (cx + math.cos(a) * self.CORE_PROXIMITY,
                     cy + math.sin(a) * self.CORE_PROXIMITY)
                pygame.draw.circle(surface, colour, (int(p[0]), int(p[1])), 1)
        # Charging telegraphs the exact outer edge of the coming ring.
        if state == "charge":
            for step in range(0, 360, 6):
                if (step // 6) % 2:
                    continue
                a = math.radians(step)
                p = (cx + math.cos(a) * self.CORE_RING_MAX,
                     cy + math.sin(a) * self.CORE_RING_MAX)
                pygame.draw.circle(surface, (255, 120, 120), (int(p[0]), int(p[1])), 2)

        # Glow behind the hub.
        glow_radius = int(self.CORE_HUB_RADIUS + 16
                          + (8 * (0.5 + 0.5 * math.sin(t * 5.0))
                             if state != "idle" else 3))
        glow = pygame.Surface((glow_radius * 2, glow_radius * 2), pygame.SRCALPHA)
        pygame.draw.circle(glow, colour + (60,), (glow_radius, glow_radius), glow_radius)
        surface.blit(glow, (cx - glow_radius, cy - glow_radius))

        # Reactor body: housing, spinning segments and a bright core.
        hub = int(self.CORE_HUB_RADIUS)
        pygame.draw.circle(surface, (14, 16, 30), (cx, cy), hub + 3)
        pygame.draw.circle(surface, (46, 52, 84), (cx, cy), hub)
        for seg in range(6):
            a = math.radians(self.core_spin + seg * 60)
            inner = (cx + math.cos(a) * (hub - 12), cy + math.sin(a) * (hub - 12))
            outer = (cx + math.cos(a) * (hub - 2), cy + math.sin(a) * (hub - 2))
            pygame.draw.line(surface, colour, inner, outer, 3)
        pygame.draw.circle(surface, colour, (cx, cy), hub, 2)
        pygame.draw.circle(surface, (12, 14, 26), (cx, cy), 9)
        pygame.draw.circle(surface, colour, (cx, cy), 6)
        pygame.draw.circle(surface, (255, 255, 255), (cx - 2, cy - 2), 2)

        # The expanding overload ring: same radius/width as the collision.
        if state == "pulse":
            outer = int(round(self.core_radius + self.CORE_RING_WIDTH / 2))
            pygame.draw.circle(surface, (120, 20, 34), (cx, cy), outer + 5, 4)
            pygame.draw.circle(surface, (255, 55, 60), (cx, cy), outer,
                               int(self.CORE_RING_WIDTH))
            pygame.draw.circle(surface, (255, 190, 190), (cx, cy),
                               int(round(self.core_radius)), 2)
        surface.set_clip(clip_before)


    # =========================================================
    # ROOM 3: CORE OVERRIDE TERMINAL (Python loops)
    # =========================================================

    R3_TERMINAL_RECT = pygame.Rect(284, 280, 52, 40)
    R3_OFFLINE_TIME = 5.0
    # Six questions, two per difficulty; one of the two that match the
    # session difficulty is drawn once and kept for the session.
    R3_TERMINAL_BANK = (
        {"id": "core_easy_1", "difficulty": "easy",
         "prompt": "What does this loop print?",
         "code": ("for i in range(3):", "    print(i)"),
         "options": ("0 1 2", "1 2 3", "0 1 2 3", "3"), "correct": 0,
         "explanation": "range(3) gives 0, 1 and 2, so the body runs 3 times."},
        {"id": "core_easy_2", "difficulty": "easy",
         "prompt": "What is printed after the loop ends?",
         "code": ("count = 0", "while count < 3:", "    count += 1", "print(count)"),
         "options": ("2", "4", "3", "0"), "correct": 2,
         "explanation": "The loop stops as soon as count reaches 3."},
        {"id": "core_medium_1", "difficulty": "medium",
         "prompt": "What is the final value of total?",
         "code": ("total = 0", "for n in range(1, 5):", "    total += n", "print(total)"),
         "options": ("4", "10", "15", "6"), "correct": 1,
         "explanation": "range(1, 5) is 1, 2, 3, 4 and 1+2+3+4 = 10."},
        {"id": "core_medium_2", "difficulty": "medium",
         "prompt": "Which numbers does this loop print?",
         "code": ("for i in range(5):", "    if i % 2 == 0:", "        continue",
                  "    print(i)"),
         "options": ("0 2 4", "0 1 2 3 4", "1 3", "1 2 3 4"), "correct": 2,
         "explanation": "continue skips even values, so only 1 and 3 are printed."},
        {"id": "core_hard_1", "difficulty": "hard",
         "prompt": "What does this nested loop print?",
         "code": ("count = 0", "for i in range(4):", "    for j in range(i):",
                  "        count += 1", "print(count)"),
         "options": ("4", "10", "6", "3"), "correct": 2,
         "explanation": "The inner loop runs 0+1+2+3 = 6 times in total."},
        {"id": "core_hard_2", "difficulty": "hard",
         "prompt": "What is steps after the loop ends?",
         "code": ("n = 20", "steps = 0", "while n > 1:", "    n //= 2",
                  "    steps += 1"),
         "options": ("3", "5", "10", "4"), "correct": 3,
         "explanation": "n goes 20 -> 10 -> 5 -> 2 -> 1, which is 4 halvings."},
    )

    def _play_sound(self, name):
        audio = getattr(self.game, "audio", None)
        if audio is not None:
            try:
                audio.play(name)
            except Exception:
                pass

    @staticmethod
    def _r3_terminal_geometry():
        """Modal, four answer buttons and the close button (room-3 sized)."""
        modal = pygame.Rect(190, 145, 580, 330)
        options = []
        for i in range(4):
            options.append(pygame.Rect(modal.x + 24 + (i % 2) * 274,
                                       modal.y + 166 + (i // 2) * 44, 258, 36))
        close = pygame.Rect(modal.right - 92, modal.y + 12, 78, 26)
        return modal, options, close

    def _r3_terminal_near(self):
        if self.current_room_number() != 3:
            return False
        zone = self.R3_TERMINAL_RECT.inflate(44, 40)
        return any(rect.colliderect(zone) for rect in self._player_rects())

    def _r3_terminal_paused(self):
        """The room timer, sentry and core hold still while the console is open."""
        return self.current_room_number() == 3 and self.r3_term_open

    def _r3_terminal_submit(self, index):
        question = self.r3_term_question
        if (question is None or self.r3_term_ok
                or index in self.r3_term_wrong
                or not 0 <= index < len(question["options"])):
            return
        self.r3_term_selected = index
        if index == question["correct"]:
            self.r3_term_ok = True
            self.r3_term_explanation = question["explanation"]
            self.r3_term_feedback = (
                f"OVERRIDE ACCEPTED! CORE OFFLINE ({self.R3_OFFLINE_TIME:.0f}s).")
            self.feedback = "OVERRIDE SUCCESSFUL! CORE OFFLINE."
            self.core_state = "offline"
            self.core_timer = self.R3_OFFLINE_TIME
            self.core_radius = self.CORE_HUB_RADIUS
            self.core_hit_players = set()
            self.core_grace = 0.0
            center = self._core_center()
            if center is not None:
                self._spawn_sparks(center, (90, 230, 255), (255, 210, 90))
            self._play_sound("correct")
        else:
            self.r3_term_wrong.add(index)
            self.r3_term_feedback = "INCORRECT. Security +5, score -5. Try again."
            self.feedback = "TERMINAL OVERRIDE FAILED - CORE STILL ACTIVE."
            if self.game:
                self.game.security.increase(5)
                self.game.score.penalize(5)
            self._play_sound("wrong")

    def _handle_r3_terminal_event(self, event):
        """Return True when the CORE OVERRIDE terminal consumed this event."""
        if self.r3_term_open:
            _, option_rects, close_rect = self._r3_terminal_geometry()
            if event.type == pygame.MOUSEMOTION:
                self.r3_term_hover = next(
                    (i for i, r in enumerate(option_rects)
                     if r.collidepoint(event.pos)), None)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if close_rect.collidepoint(event.pos):
                    self.r3_term_open = False
                else:
                    for idx, r in enumerate(option_rects):
                        if r.collidepoint(event.pos):
                            self._r3_terminal_submit(idx)
                            break
            elif event.type == pygame.KEYDOWN:
                keys = {pygame.K_a: 0, pygame.K_b: 1, pygame.K_c: 2, pygame.K_d: 3,
                        pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3}
                if event.key in (pygame.K_ESCAPE, pygame.K_e, pygame.K_RETURN):
                    self.r3_term_open = False
                elif event.key in keys:
                    self._r3_terminal_submit(keys[event.key])
            return True
        if not self._r3_terminal_near():
            return False
        if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
            self.r3_term_open = True
            self.r3_term_selected = None
            self._play_sound("click")
            return True
        if (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1
                and self.R3_TERMINAL_RECT.inflate(16, 16).collidepoint(event.pos)):
            self.r3_term_open = True
            self.r3_term_selected = None
            return True
        return False

    def _draw_room3_terminal(self, surface):
        """The CORE OVERRIDE console: a small, readable machine on the floor."""
        term = self.R3_TERMINAL_RECT
        t = self._seconds()
        pulse = 0.5 + 0.5 * math.sin(t * 4.5)
        near = self._r3_terminal_near()
        spent = self.r3_term_ok
        teal = (70, 235, 150) if spent else (70, 215, 190)
        glow = pygame.Surface((104, 84), pygame.SRCALPHA)
        pygame.draw.ellipse(glow, teal + (int(22 + 22 * pulse),), glow.get_rect())
        surface.blit(glow, glow.get_rect(center=term.center))
        pygame.draw.rect(surface, (14, 17, 30), term.inflate(8, 6), border_radius=6)
        pygame.draw.rect(surface, (30, 36, 62), term, border_radius=5)
        screen = term.inflate(-12, -14)
        pygame.draw.rect(surface, (10, 56, 44) if spent else (8, 22, 34),
                         screen, border_radius=3)
        for i, width in enumerate((10, 22, 15)):
            pygame.draw.line(surface, teal, (screen.x + 4, screen.y + 5 + i * 6),
                             (screen.x + 4 + width, screen.y + 5 + i * 6), 1)
        pygame.draw.rect(surface, teal, term, 2, border_radius=5)
        text = "OVERRIDE USED" if spent else "CORE OVERRIDE"
        label = self._font(17).render(text, True, (140, 230, 215))
        rect = label.get_rect(midtop=(term.centerx, term.bottom + 6))
        pygame.draw.rect(surface, (10, 12, 22), rect.inflate(10, 4), border_radius=5)
        surface.blit(label, rect)
        if near and not self.r3_term_open and not spent:
            prompt = self._font(16).render("E: USE", True, (240, 244, 255))
            pill = pygame.Rect(0, 0, 70, 20)
            pill.center = (term.centerx, term.top - 18)
            pygame.draw.rect(surface, (10, 12, 22), pill, border_radius=6)
            pygame.draw.rect(surface, teal, pill, 1, border_radius=6)
            surface.blit(prompt, prompt.get_rect(center=pill.center))

    def _draw_room3_terminal_modal(self, surface):
        if self.current_room_number() != 3 or not self.r3_term_open:
            return
        question = self.r3_term_question
        if not question:
            return
        backdrop = pygame.Surface((self.room_width, self.room_height), pygame.SRCALPHA)
        backdrop.fill((6, 10, 22, 165))
        surface.blit(backdrop, (self.room_x, self.room_y))

        modal, option_rects, close_rect = self._r3_terminal_geometry()
        pygame.draw.rect(surface, (12, 17, 32), modal, border_radius=10)
        pygame.draw.rect(surface, (75, 210, 255), modal, 2, border_radius=10)
        header = pygame.Rect(modal.x + 2, modal.y + 2, modal.width - 4, 38)
        pygame.draw.rect(surface, (18, 28, 52), header, border_radius=8)
        title = self._font(23).render(
            f"CORE OVERRIDE CONSOLE  ·  {question['difficulty'].upper()} LOOP CHALLENGE",
            True, (115, 235, 255))
        surface.blit(title, (modal.x + 18, modal.y + 11))
        pygame.draw.rect(surface, (42, 30, 56), close_rect, border_radius=5)
        pygame.draw.rect(surface, (175, 130, 220), close_rect, 1, border_radius=5)
        close_label = self._font(17).render("ESC / E", True, (235, 230, 250))
        surface.blit(close_label, close_label.get_rect(center=close_rect.center))

        surface.blit(self._font(22).render(question["prompt"], True, (240, 245, 255)),
                     (modal.x + 24, modal.y + 48))
        code_box = pygame.Rect(modal.x + 24, modal.y + 72, modal.width - 48, 84)
        pygame.draw.rect(surface, (8, 12, 24), code_box, border_radius=6)
        pygame.draw.rect(surface, (55, 145, 195), code_box, 1, border_radius=6)
        lines = len(question["code"])
        size, step = ((21, 20) if lines <= 3 else (19, 18) if lines == 4 else (17, 14))
        code_font = self._font(size)
        for idx, line in enumerate(question["code"]):
            surface.blit(code_font.render(line, True, (115, 235, 255)),
                         (code_box.x + 14, code_box.y + 6 + idx * step))

        letters = ("A", "B", "C", "D")
        for idx, rect in enumerate(option_rects):
            text = question["options"][idx]
            chosen_ok = self.r3_term_ok and idx == question["correct"]
            if chosen_ok:
                fill, edge = (20, 88, 62), (70, 240, 155)
            elif idx in self.r3_term_wrong:
                fill, edge = (98, 28, 42), (255, 95, 110)
            elif self.r3_term_hover == idx:
                fill, edge = (28, 46, 78), (110, 225, 255)
            else:
                fill, edge = (20, 28, 48), (72, 145, 200)
            pygame.draw.rect(surface, fill, rect, border_radius=7)
            pygame.draw.rect(surface, edge, rect, 2, border_radius=7)
            badge = pygame.Rect(rect.x + 8, rect.centery - 10, 20, 20)
            pygame.draw.rect(surface, edge, badge, border_radius=4)
            letter = self._font(18).render(letters[idx], True, (10, 14, 24))
            surface.blit(letter, letter.get_rect(center=badge.center))
            answer = self._font(20).render(text, True, (240, 244, 255))
            surface.blit(answer, (badge.right + 10,
                                  rect.centery - answer.get_height() // 2))

        if self.r3_term_feedback:
            colour = (75, 240, 155) if self.r3_term_ok else (255, 115, 125)
            surface.blit(self._font(20).render(self.r3_term_feedback, True, colour),
                         (modal.x + 24, modal.bottom - 72))
            for row, line in enumerate(self._wrap_text(
                    self._font(19), self.r3_term_explanation,
                    modal.width - 48, 2)):
                surface.blit(self._font(19).render(line, True, (195, 215, 235)),
                             (modal.x + 24, modal.bottom - 48 + row * 18))
        else:
            surface.blit(self._font(19).render(
                "The room timer, sentry and core are paused while this console is open.",
                True, (165, 190, 215)), (modal.x + 24, modal.bottom - 34))

    # =========================================================
    # GATE CORRIDORS (one-way gates, Rooms 1 -> 2 -> 3)
    # =========================================================
    # Gate -> 0.4 s hand-in slide -> playable airlock corridor -> 0.4 s
    # hand-out slide -> next room. The next room's hazards and question are
    # prepared at hand-in but stay frozen (update() returns early) until the
    # hand-out has finished. Collision inside the corridor is routed through
    # room_map.blocked (see _tx_blocked), so core/game.py is untouched.

    TX_IN, TX_OUT = 0.40, 0.40
    TX_BAND = pygame.Rect(0, 148, 960, 312)
    CORR = pygame.Rect(60, 250, 780, 120)            # walkable floor
    CORR_ENTRY = pygame.Rect(176, 250, 16, 120)      # blast door behind players
    CORR_EXIT = pygame.Rect(744, 250, 16, 120)       # blast door ahead
    CORR_INSIDE_X = 216       # both players left edge past this -> seal entry
    CORR_APPROACH_X = 634     # a player this close wakes the exit door
    CORR_CLEAR_X = 776        # both players past this -> hand-out
    CORR_SEAL_TIME, CORR_CYCLE_TIME, CORR_OPEN_TIME = 0.45, 0.60, 0.35
    CORR_STARTS = ((92, 0), (130, 0))
    CORR_TITLES = {2: "SECTOR 2 · LASER CORRIDOR", 3: "SECTOR 3 · CORE SECURITY"}
    CORR_PALETTE = {
        2: {"wall": (20, 29, 56), "wall2": (28, 40, 78), "pipe": (88, 112, 176),
            "accent": (82, 156, 255), "glow": (72, 200, 255)},
        3: {"wall": (22, 14, 40), "wall2": (34, 20, 60), "pipe": (110, 78, 160),
            "accent": (170, 96, 245), "glow": (176, 96, 255)},
    }

    def _tx_snapshot(self):
        """Capture the room being left, before the active room changes."""
        snap = pygame.Surface((960, 640))
        snap.fill((10, 12, 22))
        self.render(snap)
        return snap

    def _begin_gate_transition(self, stage, snapshot, players, from_pos, to_pos):
        """Start the hand-in slide; the next room is already prepared."""
        starts = []
        for index, (fx, fy) in enumerate(from_pos):
            sx = self.CORR_STARTS[min(index, 1)][0]
            starts.append((sx, max(self.CORR.top + 6,
                                   min(self.CORR.bottom - 38, fy))))
        self._tx = {
            "phase": "in", "t": 0.0, "clock": 0.0, "stage": stage,
            "next_sector": stage + 1, "snap": snapshot, "players": players,
            "from": from_pos, "starts": starts, "to": to_pos,
            "out_from": list(from_pos), "drawing": False,
            "card": self.room_transition_timer,
            "entry": "open", "entry_t": 0.0,
            "exit": "red", "exit_t": 0.0, "exit_open_t": 0.0,
            "lead": 0.0, "new": None, "window": None,
        }
        self.room_transition_timer = 0.0
        for rect, pos in zip(players, from_pos):
            rect.topleft = pos
        new_room = pygame.Surface((960, 640))
        new_room.fill((10, 12, 22))
        self._tx["drawing"] = True
        try:
            self.render(new_room)
        finally:
            self._tx["drawing"] = False
        self._tx["new"] = new_room
        self._tx["window"] = pygame.transform.smoothscale(
            new_room.subsurface(pygame.Rect(40, 150, 880, 300)), (170, 58))

    @staticmethod
    def _smooth(x):
        x = max(0.0, min(1.0, x))
        return x * x * (3.0 - 2.0 * x)

    def _corridor_blocked(self, rect, tx):
        """Corridor collision: walls plus any door that is not open."""
        if not self.CORR.contains(rect):
            return True
        if tx["entry"] != "open" and self.CORR_ENTRY.colliderect(rect):
            return True
        if tx["exit"] != "open" and self.CORR_EXIT.colliderect(rect):
            return True
        return False

    def _tx_blocked(self, rect):
        """Collision callback: rooms normally, the corridor while it plays."""
        tx = self._tx
        if tx is None:
            return self._rm_blocked(rect)
        if tx["phase"] == "walk":
            return self._corridor_blocked(rect, tx)
        return True   # hand-in / hand-out slides: players are carried

    def _update_gate_transition(self, dt):
        tx = self._tx
        tx["clock"] += dt
        self.room_map.update(dt)
        players = tx["players"]
        phase = tx["phase"]

        if phase == "in":
            tx["t"] += dt
            p = self._smooth(tx["t"] / self.TX_IN)
            for rect, a, b in zip(players, tx["from"], tx["starts"]):
                rect.topleft = (int(a[0] + (b[0] - a[0]) * p),
                                int(a[1] + (b[1] - a[1]) * p))
            if tx["t"] >= self.TX_IN:
                for rect, b in zip(players, tx["starts"]):
                    rect.topleft = b
                tx["phase"], tx["t"] = "walk", 0.0
            return

        if phase == "walk":
            tx["t"] += dt
            tx["lead"] = max([tx["lead"]] + [r.centerx for r in players])
            # Entry door seals only once every player is inside.
            if tx["entry"] == "open" and all(
                    r.left >= self.CORR_INSIDE_X for r in players):
                tx["entry"], tx["entry_t"] = "closing", 0.0
            elif tx["entry"] == "closing":
                tx["entry_t"] += dt
                if tx["entry_t"] >= self.CORR_SEAL_TIME:
                    tx["entry"] = "sealed"
            # Exit door only starts once the entry door is sealed.
            if (tx["exit"] == "red" and tx["entry"] == "sealed"
                    and any(r.right >= self.CORR_APPROACH_X for r in players)):
                tx["exit"], tx["exit_t"] = "cycling", 0.0
            elif tx["exit"] == "cycling":
                tx["exit_t"] += dt
                if tx["exit_t"] >= self.CORR_CYCLE_TIME:
                    tx["exit"] = "open"
            elif tx["exit"] == "open":
                tx["exit_open_t"] += dt
                if all(r.left >= self.CORR_CLEAR_X for r in players):
                    tx["phase"], tx["t"] = "out", 0.0
                    tx["out_from"] = [r.topleft for r in players]
            return

        tx["t"] += dt                      # phase == "out"
        p = self._smooth(tx["t"] / self.TX_OUT)
        for rect, a, b in zip(players, tx["out_from"], tx["to"]):
            rect.topleft = (int(a[0] + (b[0] - a[0]) * p),
                            int(a[1] + (b[1] - a[1]) * p))
        if tx["t"] >= self.TX_OUT:
            for rect, pos in zip(players, tx["to"]):
                rect.topleft = pos
            self.room_transition_timer = tx["card"]
            self._tx = None

    # ----------------------------------------------------------------- draw

    def _draw_gate_transition(self, surface, tx):
        new_room = tx["new"]
        surface.blit(new_room, (0, 0))
        band = self.TX_BAND
        phase, t = tx["phase"], tx["t"]
        scene = self._corridor_scene(tx)
        layer = pygame.Surface(band.size)
        layer.fill((9, 11, 20))
        cam = 0.0
        if phase == "in":
            cam = 960 * self._smooth(t / self.TX_IN)
            layer.blit(tx["snap"], (-cam, -band.y))
            layer.blit(scene, (960 - cam, 0))
        elif phase == "walk":
            layer.blit(scene, (0, 0))
        else:
            cam = 960 * self._smooth(t / self.TX_OUT)
            layer.blit(scene, (-cam, 0))
            layer.blit(new_room, (960 - cam, -band.y))
        surface.blit(layer, band.topleft)
        if phase == "in" and t < 0.25:
            self._draw_gate_open_flare(surface, tx, t, cam)
        self._draw_airlock_cover(surface, tx)

    def _draw_gate_open_flare(self, surface, tx, t, cam):
        gate = self.gates[tx["stage"] - 1].rect
        pulse = 0.5 + 0.5 * math.sin(t * 22.0)
        glow = pygame.Surface((gate.width + 70, gate.height + 30), pygame.SRCALPHA)
        pygame.draw.rect(glow, (70, 230, 160, int(40 + 55 * pulse)),
                         glow.get_rect(), border_radius=12)
        surface.blit(glow, (gate.x - 35 - cam, gate.y - 15))

    def _draw_airlock_cover(self, surface, tx):
        """Hides the next question; fades in at hand-in and out at hand-out."""
        alpha = 1.0
        if tx["phase"] == "in":
            alpha = min(1.0, tx["t"] / 0.15)
        elif tx["phase"] == "out":
            alpha = max(0.0, 1.0 - max(0.0, tx["t"] - 0.2) / 0.2)
        if alpha <= 0.0:
            return
        pal = self.CORR_PALETTE[tx["next_sector"]]
        rect = pygame.Rect(48, 460, 864, 130)
        cover = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(cover, (10, 12, 26, 255), cover.get_rect(), border_radius=14)
        pygame.draw.rect(cover, pal["accent"] + (255,), cover.get_rect(), 2,
                         border_radius=14)
        title = self._font(30).render("AIRLOCK · NEXT SECTOR AHEAD", True,
                                      pal["glow"])
        cover.blit(title, title.get_rect(center=(rect.w // 2, 52)))
        sub = self._font(17).render(
            "ROOM HAZARDS AND CHALLENGE TIMER PAUSED", True, (150, 160, 200))
        cover.blit(sub, sub.get_rect(center=(rect.w // 2, 92)))
        cover.set_alpha(int(255 * alpha))
        surface.blit(cover, rect.topleft)

    @staticmethod
    def _lamp(surface, centre, colour, strength=1.0, radius=5):
        strength = max(0.0, min(1.0, strength))
        halo = pygame.Surface((radius * 6, radius * 6), pygame.SRCALPHA)
        pygame.draw.circle(halo, colour + (int(70 * strength),),
                           (radius * 3, radius * 3), radius * 3)
        surface.blit(halo, (centre[0] - radius * 3, centre[1] - radius * 3))
        dim = tuple(int(c * (0.25 + 0.75 * strength)) for c in colour)
        pygame.draw.circle(surface, dim, centre, radius)

    @staticmethod
    def _flicker(clock, seed):
        """Mostly steady; an occasional brief dip on a few lamps."""
        dip = math.sin(clock * 7.0 + seed * 3.1) * math.sin(clock * 2.3 + seed)
        return 0.45 if dip > 0.93 else 1.0

    def _corridor_scene(self, tx):
        """Full-width corridor scene (band-local), static art + live lights."""
        sector = tx["next_sector"]
        pal = self.CORR_PALETTE[sector]
        base = self._cached(("corridor", sector),
                            lambda: self._build_corridor_static(sector))
        scene = base.copy()
        oy = self.TX_BAND.y
        clock, lead = tx["clock"], tx["lead"]
        glow = pal["glow"]

        # Floor arrows + edge lights switch on just ahead of the front player.
        mid = 310 - oy
        reach = lead + 120
        for x in range(236, 716, 60):
            lit = x < reach
            col = glow if lit else self._mix(pal["wall"], glow, 0.18)
            pygame.draw.polygon(scene, col, [(x, mid - 16), (x + 22, mid),
                                             (x, mid + 16), (x + 8, mid)])
        for x in range(70, 830, 30):
            lit = x < reach
            col = glow if lit else self._mix(pal["wall"], glow, 0.15)
            for yy in (258 - oy, 362 - oy):
                pygame.draw.circle(scene, col, (x, yy), 2)

        # Doors: leaves slide in from top and bottom; lamps show the state.
        entry_amt = (0.0 if tx["entry"] == "open" else
                     self._smooth(tx["entry_t"] / self.CORR_SEAL_TIME)
                     if tx["entry"] == "closing" else 1.0)
        exit_amt = (1.0 if tx["exit"] != "open" else
                    1.0 - self._smooth(tx["exit_open_t"] / self.CORR_OPEN_TIME))
        for door, amt in ((self.CORR_ENTRY, entry_amt), (self.CORR_EXIT, exit_amt)):
            reach_h = int(door.height / 2 * amt)
            for y0, y1 in ((door.top, door.top + reach_h),
                           (door.bottom - reach_h, door.bottom)):
                if y1 - y0 <= 0:
                    continue
                leaf = pygame.Rect(door.x, y0 - oy, door.width, y1 - y0)
                pygame.draw.rect(scene, (36, 40, 66), leaf)
                pygame.draw.rect(scene, (100, 110, 156), leaf, 2)
                for yy in range(leaf.top + 4, leaf.bottom - 6, 14):
                    pygame.draw.line(scene, (230, 185, 55),
                                     (leaf.left + 3, yy + 8), (leaf.right - 4, yy), 3)

        red, amber, cyan = (255, 64, 70), (255, 190, 60), (80, 230, 255)
        entry_col = {"open": cyan, "closing": amber, "sealed": red}[tx["entry"]]
        exit_col = {"red": red, "cycling": amber, "open": cyan}[tx["exit"]]
        self._lamp(scene, (self.CORR_ENTRY.centerx, 96),
                   entry_col, self._flicker(clock, 1))
        self._lamp(scene, (self.CORR_EXIT.centerx, 96),
                   exit_col, self._flicker(clock, 2))
        # Red warning beacons beside blast doors that are not open.
        beat = 0.5 + 0.5 * math.sin(clock * 6.0)
        heavy = 1.0 if sector == 3 else 0.6
        for door, active in ((self.CORR_ENTRY, tx["entry"] != "open"),
                             (self.CORR_EXIT, tx["exit"] != "open")):
            for dy in (-20, 20):
                self._lamp(scene, (door.centerx, door.centery - oy + dy * 3),
                           red, (0.25 + 0.75 * beat) * heavy if active else 0.12, 3)
        # Cyan corridor ceiling lamps with a slight flicker.
        for k, x in enumerate((250, 420, 590)):
            self._lamp(scene, (x, 108 - 6), glow, self._flicker(clock, 5 + k), 4)

        # Sector display: title + live status.
        disp = pygame.Rect(210, 40, 300, 56)
        if tx["exit"] == "open":
            status = "NEXT SECTOR >>"
        elif tx["entry"] == "open":
            status = "ACCESS GRANTED"
        else:
            status = "GATE SEALED"
        title = self._font(20).render(self.CORR_TITLES[sector], True, (232, 244, 255))
        scene.blit(title, title.get_rect(center=(disp.centerx, disp.y + 19)))
        stat = self._font(15).render(status, True, glow)
        scene.blit(stat, stat.get_rect(center=(disp.centerx, disp.y + 41)))

        # Window onto the next room: dim, brightening as players approach.
        win = pygame.Rect(570, 38, 170, 58)
        prox = self._smooth((lead - 120) / (self.CORR_APPROACH_X - 120))
        if tx["exit"] == "open":
            prox = 1.0
        scene.blit(tx["window"], win.topleft)
        shade = pygame.Surface(win.size, pygame.SRCALPHA)
        shade.fill((6, 8, 18, int(228 - 168 * prox)))
        scene.blit(shade, win.topleft)
        for yy in range(win.top, win.bottom, 4):
            pygame.draw.line(scene, (0, 0, 0), (win.left, yy), (win.right - 1, yy))
        pygame.draw.rect(scene, glow, win, 2)
        return scene

    def _build_corridor_static(self, sector):
        """Walls, pipes, cables, vents, machinery and frames for one corridor."""
        pal = self.CORR_PALETTE[sector]
        oy = self.TX_BAND.y
        w, h = 960, self.TX_BAND.height
        s = pygame.Surface((w, h))
        s.fill(pal["wall"])
        for x in range(0, w, 48):
            pygame.draw.line(s, pal["wall2"], (x, 0), (x, h))
        for y in (0, 60, 232, 290):
            pygame.draw.line(s, pal["wall2"], (0, y), (w, y), 2)
        floor = self.CORR.move(0, -oy)
        pygame.draw.rect(s, (13, 15, 27), floor)
        for x in range(floor.left, floor.right, 40):
            pygame.draw.line(s, (20, 23, 38), (x, floor.top), (x, floor.bottom))
        pygame.draw.line(s, (20, 23, 38), (floor.left, floor.centery),
                         (floor.right, floor.centery))
        # Hazard stripes along both floor edges.
        for edge in (floor.top, floor.bottom - 5):
            for x in range(floor.left, floor.right, 16):
                pygame.draw.polygon(s, (214, 170, 52),
                                    [(x, edge + 5), (x + 8, edge + 5),
                                     (x + 13, edge), (x + 5, edge)])
        pygame.draw.rect(s, pal["accent"], floor, 2)

        # Upper wall: pipes, sagging cables, vents, security details.
        for y, th in ((14, 7), (30, 5)):
            pygame.draw.line(s, pal["pipe"], (0, y), (w, y), th)
            pygame.draw.line(s, self._mix(pal["pipe"], (255, 255, 255), 0.3),
                             (0, y - 1), (w, y - 1), 1)
            for x in range(40, w, 120):
                pygame.draw.rect(s, (46, 52, 86), (x, y - 6, 8, 12))
        for x0, drop in ((60, 20), (330, 26), (610, 18)):
            pts = [(x0 + i * 10, 44 + int(drop * math.sin(math.pi * i / 24)))
                   for i in range(25)]
            pygame.draw.lines(s, (150, 70, 90) if sector == 3 else (70, 130, 150),
                              False, pts, 2)
        vent_w = 110 if sector == 3 else 80
        for vx in (70, 800):
            vent = pygame.Rect(vx, 46, vent_w if vx == 70 else 100, 40)
            pygame.draw.rect(s, (14, 16, 28), vent)
            for yy in range(vent.top + 5, vent.bottom - 3, 6):
                pygame.draw.line(s, pal["pipe"], (vent.left + 4, yy),
                                 (vent.right - 4, yy), 2)
            pygame.draw.rect(s, pal["accent"], vent, 1)
        # Sector display and window frames.
        for frame in (pygame.Rect(210, 40, 300, 56), pygame.Rect(570, 38, 170, 58)):
            pygame.draw.rect(s, (8, 10, 20), frame.inflate(10, 8), border_radius=6)
        pygame.draw.rect(s, (8, 10, 20), (210, 40, 300, 56), border_radius=5)
        pygame.draw.rect(s, pal["accent"], (210, 40, 300, 56), 2, border_radius=5)
        # Camera dome + keypad by the entry door.
        pygame.draw.circle(s, (52, 58, 92), (772 + 40, 20), 11)
        pygame.draw.circle(s, (255, 70, 80), (812, 22), 3)
        pygame.draw.rect(s, (14, 16, 28), (150, 44, 20, 34), border_radius=3)
        pygame.draw.rect(s, pal["accent"], (150, 44, 20, 34), 1, border_radius=3)
        for ky in (50, 58, 66):
            pygame.draw.rect(s, pal["pipe"], (154, ky, 12, 4))

        # Lower wall: machinery. Corridor 3 is heavier reactor plant.
        lo = self.CORR.bottom - oy + 6
        if sector == 3:
            for x in (90, 250, 410, 570, 730):
                coil = pygame.Rect(x, lo + 4, 70, 56)
                pygame.draw.rect(s, (30, 20, 54), coil, border_radius=8)
                pygame.draw.rect(s, pal["accent"], coil, 2, border_radius=8)
                for cx in range(coil.left + 12, coil.right - 6, 14):
                    pygame.draw.line(s, (120, 60, 200), (cx, coil.top + 6),
                                     (cx, coil.bottom - 6), 3)
                pygame.draw.circle(s, (255, 64, 70), (coil.centerx, coil.top - 6), 4)
            pygame.draw.line(s, (170, 70, 255), (0, lo + 68), (w, lo + 68), 4)
            for x in (40, 900):
                pygame.draw.rect(s, (44, 30, 78), (x, lo - 4, 18, 70))
        else:
            for x in range(80, 780, 130):
                box = pygame.Rect(x, lo + 8, 84, 38)
                pygame.draw.rect(s, (24, 34, 66), box, border_radius=4)
                pygame.draw.rect(s, pal["accent"], box, 1, border_radius=4)
                for yy in range(box.top + 7, box.bottom - 4, 8):
                    pygame.draw.line(s, pal["pipe"], (box.left + 8, yy),
                                     (box.right - 8, yy), 2)
            pygame.draw.line(s, pal["pipe"], (0, lo + 58), (w, lo + 58), 6)
            pygame.draw.line(s, (70, 160, 200), (0, lo + 66), (w, lo + 66), 2)

        # Door frames.
        for door in (self.CORR_ENTRY, self.CORR_EXIT):
            frame = pygame.Rect(door.x - 10, door.y - oy - 8, door.width + 20,
                                door.height + 16)
            pygame.draw.rect(s, (10, 12, 22), frame, border_radius=4)
            pygame.draw.rect(s, pal["accent"], frame, 2, border_radius=4)
            pygame.draw.rect(s, (7, 9, 16), (door.x, door.y - oy, door.width,
                                            door.height))
        return s

    def player_in_safe_pocket(self, rect):
        return any(zone.contains(rect) for zone in self.safe_zones_live())

    def safe_zones_live(self):
        """Safe zones that shield right now: in Room 1 only the pads the board lights."""
        if self.current_room_number() == 1 and self.lit_pads is not None:
            return [zone for index, zone in enumerate(self.safe_zones) if index in self.lit_pads]
        return self.safe_zones

    # =========================================================
    # QUESTION SYSTEM
    # =========================================================

    def load_questions(self):
        """
        Load Level 3 questions from data/puzzles.json.

        Questions are divided by their room field.

        If room/difficulty fields are missing, the old
        level3_loop_1 ... level3_loop_10 format is still supported.
        """

        self.room_question_pools = {
            1: [],
            2: [],
            3: [],
        }
        self.room2_override_pool = []

        try:
            base_path = Path(__file__).resolve().parent.parent
            puzzle_path = base_path / "data" / "puzzles.json"

            with open(
                puzzle_path,
                "r",
                encoding="utf-8",
            ) as file:
                puzzles = json.load(file)

            for key, puzzle in puzzles.items():

                if key.startswith("level3_room2_override_"):
                    self.room2_override_pool.append(puzzle)
                    continue

                if not key.startswith("level3_loop_"):
                    continue

                room = puzzle.get("room")

                if room in (1, 2, 3):
                    self.room_question_pools[room].append(puzzle)
                    continue

                try:
                    question_number = int(
                        key.split("_")[-1]
                    )
                except ValueError:
                    continue

                if 1 <= question_number <= 4:
                    self.room_question_pools[1].append(puzzle)

                elif 5 <= question_number <= 7:
                    self.room_question_pools[2].append(puzzle)

                elif 8 <= question_number <= 10:
                    self.room_question_pools[3].append(puzzle)

        except (
            FileNotFoundError,
            json.JSONDecodeError,
        ):
            self.room_question_pools = {
                1: [],
                2: [],
                3: [],
            }
            self.room2_override_pool = []

        self.question_pool = (
            self.room_question_pools[1]
            + self.room_question_pools[2]
            + self.room_question_pools[3]
        )

    def get_selected_difficulty(self):
        """Safely read the game's global difficulty."""

        difficulty = getattr(
            self.game,
            "difficulty",
            None,
        )

        if isinstance(difficulty, dict):
            value = difficulty.get(
                "name",
                difficulty.get("level"),
            )

            if value is None:
                value = next(
                    (
                        key
                        for key, preset in DIFFICULTIES.items()
                        if preset == difficulty
                    ),
                    None,
                )

        else:
            value = difficulty

        if not isinstance(value, str):
            return "medium"

        value = value.lower().strip()

        if value not in {
            "easy",
            "medium",
            "hard",
        }:
            return "medium"

        return value

    def start_questions(self):
        """Select one question for every room."""

        difficulty = self.get_selected_difficulty()

        self.current_difficulty = difficulty
        self.selected_questions = []

        for room_number in (1, 2, 3):

            if room_number in self.room_requests:
                self.selected_questions.append(self.room_requests[room_number])
                continue

            room_pool = self.room_question_pools.get(
                room_number,
                [],
            )

            filtered_pool = [
                question
                for question in room_pool
                if question.get(
                    "difficulty",
                    "medium",
                ).lower() == difficulty
            ]

            pool = (
                filtered_pool
                if filtered_pool
                else room_pool
            )

            if pool:
                self.selected_questions.append(
                    random.choice(pool)
                )
            else:
                self.selected_questions.append(None)

        self.current_question_number = 0

        self.load_current_question()

    def load_current_question(self):
        """Load the question for the current room."""

        room_number = self.current_room_number()

        if room_number > len(
            self.selected_questions
        ):
            self.complete_level()
            return

        self.current_question = (
            self.selected_questions[
                room_number - 1
            ]
        )

        if self.current_question is None:
            self.options = []
            self.correct_option_index = None
            self.selected_option = None
            self.question_points = 0
            self.current_hint = ""
            self.current_explanation = ""
            self.show_hint = False
            self.hint_used = False
            self.feedback = f"QUESTION DATA MISSING FOR CHECKPOINT {room_number}. GATE REMAINS LOCKED."
            return

        correct_answer = (
            self.current_question.get("answer")
        )

        if not isinstance(correct_answer, str) or not correct_answer or not self.current_question.get("question"):
            self.current_question = None
            self.options = []
            self.correct_option_index = None
            self.selected_option = None
            self.question_points = 0
            self.current_hint = ""
            self.current_explanation = ""
            self.show_hint = False
            self.hint_used = False
            self.feedback = f"INVALID QUESTION DATA FOR CHECKPOINT {room_number}. GATE REMAINS LOCKED."
            return

        stored_options = (
            self.current_question.get(
                "options",
                [],
            )
        )

        if (
            isinstance(stored_options, list)
            and correct_answer in stored_options
            and len(stored_options) >= 2
        ):
            self.options = list(
                stored_options
            )

        else:
            room_pool = self.room_question_pools.get(
                room_number,
                [],
            )

            possible_answers = list({
                question.get("answer")
                for question in room_pool
                if question.get("answer")
                and question.get("answer")
                != correct_answer
            })

            if len(possible_answers) < 2:

                possible_answers = list({
                    question.get("answer")
                    for question in self.question_pool
                    if question.get("answer")
                    and question.get("answer")
                    != correct_answer
                })

            if len(possible_answers) >= 2:

                wrong_answers = random.sample(
                    possible_answers,
                    2,
                )

            else:
                wrong_answers = possible_answers[:2]

            self.options = (
                wrong_answers
                + [correct_answer]
            )

        self.options = self.options[:4]

        random.shuffle(self.options)

        if correct_answer not in self.options:

            self.options = (
                [correct_answer]
                + self.options[:3]
            )

        self.correct_option_index = (
            self.options.index(
                correct_answer
            )
        )

        self.question_points = int(
            self.current_question.get(
                "points",
                50,
            )
        )

        self.current_hint = (
            self.current_question.get(
                "hint",
                "Think about the Python loop concept "
                "shown in the question.",
            )
        )

        self.current_explanation = (
            self.current_question.get(
                "explanation",
                "Review the loop concept and try "
                "applying it to the example.",
            )
        )

        self.hint_used = False
        self.show_hint = False
        self.selected_option = None
        self.feedback = ""

        self.time_left = self.time_limit

    def complete_level(self):
        """Complete Level 3."""

        self.complete = True

        self.feedback = (
            "LEVEL COMPLETE! All laser loops bypassed."
        )

        if self.game:
            self.game.score.add(100)

    # =========================================================
    # GATE SYSTEM
    # =========================================================

    def _current_gate(self):
        """The active room's exit gate (team-architecture compatibility name)."""
        return self.gates[self.current_room_number() - 1]

    def unlock_current_gate(self):
        """Unlock the gate belonging to the current room."""

        room = self.current_room_number()
        if room == 2 and not self.room2_gate_challenge_survived:
            self.room2_gate_question_solved = True
            self.feedback = "GATE 2 SEALED: SURVIVE THE GATE EMITTER CYCLE."
            return

        gate = self.gates[room - 1]
        was_locked = gate.state == "locked"
        gate.unlock()
        if was_locked and gate.state == "unlocking":
            self._vis_state()["gates"][id(gate)] = {
                "state": gate.state, "elapsed": 0.0,
            }
            self._spawn_sparks(gate.rect.center)

        if room == 1:
            self.feedback = "GATE 1 UNLOCKING!"

        elif room == 2:
            self.feedback = "GATE 2 UNLOCKING!"

        elif room == 3:
            self.feedback = "GATE 3 UNLOCKING! REACH THE FINAL EXIT."

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, dt):
        """Update timer, rooms, lasers and security robot."""

        if self.complete:
            return

        if self._tx is not None:
            self._update_gate_transition(max(0.0, dt))
            return

        self.room_map.update(dt)
        self._update_visual_effects(max(0.0, dt))
        self.room_transition_timer = max(
            0.0, self.room_transition_timer - max(0.0, dt))

        # -------------------------
        # Countdown timer
        # -------------------------

        if self.current_room_number() == 3 and self.r3_term_open \
                and not self._r3_terminal_near():
            self.r3_term_open = False       # walked away: nothing stays frozen
        r3_paused = self._r3_terminal_paused()
        if not r3_paused:
            self.time_left -= dt

        if self.time_left <= 0:

            self.time_left = 0

            self.feedback = (
                "TIME'S UP! Security increased."
            )

            if self.game:

                self.game.security.increase(25)
                self.game.score.penalize(15)

            self.time_left = self.time_limit

        # -------------------------
        # Move lasers
        # -------------------------

        if not r3_paused:
            self._update_core(max(0.0, dt))
        self._update_emitters(max(0.0, dt))
        emitters_busy = any(emitter["state"] in
                            ("opening", "tracking", "warning", "locking",
                             "active", "retracting")
                            for emitter in self.emitters)

        for index, laser in enumerate(self.lasers):
            if laser.get("type") == "tracking":
                trigger = laser["trigger"]
                possible_targets = [r for r in self._player_rects()
                                    if trigger.colliderect(r)
                                    and not self.player_in_safe_pocket(r)]
                state = laser.get("state", "idle")
                if state == "idle" and possible_targets:
                    laser["state"] = state = "warning"
                    laser["state_timer"] = laser["warn_duration"]
                if state == "warning":
                    if possible_targets:
                        target = min(possible_targets,
                                     key=lambda r: abs(r.centery - laser["target_y"]))
                        laser["target_x"] = float(target.centerx)
                        desired_y = max(laser["min_y"],
                                        min(laser["max_y"], float(target.centery)))
                        difference = desired_y - laser["target_y"]
                        max_step = laser["tracking_speed"] * dt
                        laser["target_y"] += max(-max_step, min(max_step, difference))
                    laser["state_timer"] -= dt
                    if laser["state_timer"] <= 0:
                        laser["state"], laser["state_timer"] = "active", laser["active_duration"]
                elif state == "active":
                    laser["state_timer"] -= dt
                    if laser["state_timer"] <= 0:
                        laser["state"], laser["state_timer"] = "cooldown", laser["cooldown"]
                elif state == "cooldown":
                    laser["state_timer"] -= dt
                    if laser["state_timer"] <= 0:
                        laser["state"], laser["state_timer"] = "idle", 0.0
                laser["y"] = laser["target_y"]
                continue
            axis = laser.get("axis", "x")
            if axis == "x":
                laser["x"] += laser["speed"] * laser["direction"] * dt
                minimum = laser.get("min_x", self.track_x)
                w = laser.get("width", self.laser_width)
                maximum = laser.get(
                    "max_x", self.track_x + self.track_width - w
                )
                if laser["x"] <= minimum:
                    laser["x"], laser["direction"] = minimum, 1
                elif laser["x"] >= maximum:
                    laser["x"], laser["direction"] = maximum, -1
            elif axis == "y":
                laser["y"] += laser["speed"] * laser["direction"] * dt
                minimum = laser["top"]
                maximum = laser["bottom"] - laser["length"]
                if laser["y"] <= minimum:
                    laser["y"], laser["direction"] = minimum, 1
                elif laser["y"] >= maximum:
                    laser["y"], laser["direction"] = maximum, -1
            else:
                spin = self.core_rot_mult if self.current_room_number() == 3 else 1.0
                laser["angle"] = (laser["angle"]
                                  + laser["speed"] * spin * laser["direction"] * dt) % 360.0

        if not emitters_busy:
            self.laser_clock += max(0.0, dt)
        self.check_laser_collision(dt)

        if self.current_room_number() >= 2 and not r3_paused:
            self._update_robot(max(0.0, dt))

        self.try_room_transition()

    # =========================================================
    # ROBOT DRAWING
    # =========================================================

    def _draw_room2_robot(self, surface):
        """Draw the redesigned futuristic security sentry for Room 2."""
        x, y = float(self.robot_x), float(self.robot_y)
        disabled = self.room2_robot_disabled_timer > 0 or self.robot_state == "DISABLED"
        overloading = self.room2_overload_warning_timer > 0 or self.room2_overload_active_timer > 0
        moving = not disabled and self.robot_state in ("PATROL", "CHASE", "INVESTIGATE")
        bob = 0.0 if disabled else math.sin(self.robot_scan_phase * (2.6 if moving else 1.5)) * (1.2 if moving else 0.5)
        top = y + (3.0 if disabled else bob)

        if disabled:
            shell, trim, cyan_detail, eye = (28, 31, 40), (70, 76, 92), (48, 64, 78), (45, 38, 44)
        elif overloading:
            flash = int(self._seconds() * 12) % 2 == 0
            shell = (42, 24, 36) if flash else (30, 34, 48)
            trim = (255, 70, 90) if flash else (255, 145, 70)
            cyan_detail = (255, 95, 115)
            eye = (255, 40, 60)
        elif self.robot_state in ("ALERT", "CHASE"):
            shell, trim, cyan_detail, eye = (32, 36, 50), (235, 75, 100), (70, 210, 255), (255, 50, 70)
        elif self.robot_state in ("INVESTIGATE", "SEARCH"):
            shell, trim, cyan_detail, eye = (30, 35, 48), (245, 180, 75), (72, 200, 240), (255, 175, 65)
        else:
            # Metallic dark-grey/black chassis with glowing cyan details and red optical sensor
            shell, trim, cyan_detail, eye = (26, 30, 42), (76, 195, 245), (60, 220, 255), (255, 58, 76)

        # Ground hover shadow
        shadow = pygame.Rect(round(x + 6), round(y + 28), self.robot_width - 12, 10)
        pygame.draw.ellipse(surface, (8, 10, 20), shadow)

        # Dual armored propulsion treads
        tread_y = round(top + 24)
        for wheel_x in (x + 15, x + self.robot_width - 15):
            pygame.draw.circle(surface, (16, 19, 30), (round(wheel_x), tread_y + 5), 9)
            pygame.draw.circle(surface, trim, (round(wheel_x), tread_y + 5), 6, 1)
            pygame.draw.circle(surface, cyan_detail, (round(wheel_x), tread_y + 5), 2)
        track = pygame.Rect(round(x + 7), tread_y, self.robot_width - 14, 12)
        pygame.draw.rect(surface, (18, 22, 34), track, border_radius=6)
        pygame.draw.rect(surface, (72, 88, 118), track, 1, border_radius=6)

        # Metallic dark-grey/black angular armored hull with cyan industrial seams
        body = [
            (x + 9, top + 20),
            (x + 16, top + 6),
            (x + 26, top + 2),
            (x + 44, top + 2),
            (x + 54, top + 6),
            (x + 61, top + 20),
            (x + 53, top + 25),
            (x + 17, top + 25),
        ]
        pygame.draw.polygon(surface, shell, body)
        pygame.draw.lines(surface, trim, True, body, 2)
        pygame.draw.line(surface, cyan_detail, (round(x + 18), round(top + 19)),
                         (round(x + 52), round(top + 19)), 2)

        # Visor housing & bright red optical sensor
        head = pygame.Rect(round(x + 17), round(top - 2), 36, 17)
        pygame.draw.rect(surface, (38, 43, 58), head, border_radius=7)
        pygame.draw.rect(surface, trim, head, 1, border_radius=7)
        visor = pygame.Rect(round(x + 20), round(top + 3), 30, 9)
        pygame.draw.rect(surface, (10, 13, 24), visor, border_radius=4)

        if not disabled:
            scan_shift = int(math.sin(self.robot_scan_phase * 3.2) * 4)
            eye_r = 4 if overloading else 3
            for eye_x in (x + 29 + scan_shift // 2, x + 41 + scan_shift // 2):
                pygame.draw.circle(surface, eye, (round(eye_x), round(top + 7)), eye_r)
                pygame.draw.circle(surface, (255, 225, 230), (round(eye_x - 1), round(top + 6)), 1)
        else:
            pygame.draw.line(surface, (65, 70, 82),
                             (visor.left + 4, visor.centery),
                             (visor.right - 4, visor.centery), 1)

        # Rotating top radar/sensor dish
        sensor_base = pygame.Vector2(x + self.robot_width / 2, top - 2)
        sensor_dir = self._robot_vision_direction()
        sensor_tip = sensor_base + sensor_dir * 13
        pygame.draw.line(surface, cyan_detail, sensor_base, sensor_tip, 2)
        pygame.draw.circle(surface, (16, 20, 32), (round(sensor_tip.x), round(sensor_tip.y)), 5)
        pygame.draw.circle(surface, eye if not disabled else (65, 70, 85),
                           (round(sensor_tip.x), round(sensor_tip.y)), 2)

        # Status badge above the sentry when disabled or overloading
        if disabled:
            tag = self._font(16).render(
                f"OFFLINE {self.room2_robot_disabled_timer:.1f}s", True, (90, 235, 255)
            )
            badge = tag.get_rect(center=(round(x + self.robot_width / 2), round(top - 12)))
            pygame.draw.rect(surface, (10, 16, 28), badge.inflate(10, 4), border_radius=4)
            pygame.draw.rect(surface, (70, 210, 250), badge.inflate(10, 4), 1, border_radius=4)
            surface.blit(tag, badge)
        elif overloading:
            label_txt = "OVERLOAD!" if self.room2_overload_active_timer > 0 else "CHARGING!"
            tag = self._font(16).render(label_txt, True, (255, 90, 105))
            badge = tag.get_rect(center=(round(x + self.robot_width / 2), round(top - 12)))
            pygame.draw.rect(surface, (28, 10, 16), badge.inflate(10, 4), border_radius=4)
            pygame.draw.rect(surface, (255, 75, 95), badge.inflate(10, 4), 1, border_radius=4)
            surface.blit(tag, badge)

    def draw_robot(self, surface):
        """Draw the sentry as a compact armored patrol drone."""
        if self.current_room_number() in (2, 3):
            self._draw_room2_robot(surface)
            return

        x, y = float(self.robot_x), float(self.robot_y)
        moving = self.robot_state in ("PATROL", "CHASE", "INVESTIGATE")
        bob = math.sin(self.robot_scan_phase * (2.3 if moving else 1.6)) * (1.0 if moving else 0.45)
        top = y + bob

        if self.robot_state in ("ALERT", "CHASE"):
            shell, trim, eye = (54, 45, 72), (222, 93, 142), (255, 76, 105)
        elif self.robot_state in ("INVESTIGATE", "SEARCH"):
            shell, trim, eye = (53, 52, 76), (235, 177, 86), (255, 194, 92)
        else:
            shell, trim, eye = (49, 55, 79), (141, 131, 202), (108, 224, 255)

        shadow = pygame.Rect(round(x + 8), round(y + 28), self.robot_width - 16, 10)
        pygame.draw.ellipse(surface, (10, 12, 25), shadow)
        tread_y = round(top + 25)
        for wheel_x in (x + 16, x + self.robot_width - 16):
            pygame.draw.circle(surface, (18, 21, 36), (round(wheel_x), tread_y + 5), 9)
            pygame.draw.circle(surface, (91, 91, 128), (round(wheel_x), tread_y + 5), 6, 2)
            pygame.draw.circle(surface, (163, 151, 204), (round(wheel_x), tread_y + 5), 2)
        track = pygame.Rect(round(x + 7), tread_y, self.robot_width - 14, 13)
        pygame.draw.rect(surface, (25, 28, 45), track, border_radius=6)
        pygame.draw.rect(surface, (104, 101, 144), track, 1, border_radius=6)
        tread_shift = int(self.robot_scan_phase * 10) % 8 if moving else 0
        for offset in range(-4, track.width, 8):
            px = track.x + offset + tread_shift
            if track.left + 2 <= px <= track.right - 2:
                pygame.draw.line(surface, (137, 133, 171), (px, track.top + 3),
                                 (px, track.bottom - 3), 1)

        lower = [(x + 13, top + 24), (x + 18, top + 17),
                 (x + 52, top + 17), (x + 58, top + 24),
                 (x + 52, top + 29), (x + 18, top + 29)]
        pygame.draw.polygon(surface, (22, 26, 43), lower)
        body = [(x + 12, top + 19), (x + 18, top + 8),
                (x + 27, top + 4), (x + 44, top + 4),
                (x + 53, top + 9), (x + 58, top + 20),
                (x + 52, top + 25), (x + 19, top + 25)]
        pygame.draw.polygon(surface, shell, body)
        pygame.draw.lines(surface, trim, True, body, 2)
        pygame.draw.line(surface, (118, 126, 166), (round(x + 18), round(top + 20)),
                         (round(x + 52), round(top + 20)), 1)

        head = pygame.Rect(round(x + 19), round(top - 1), 32, 18)
        pygame.draw.rect(surface, (69, 75, 103), head, border_radius=8)
        pygame.draw.rect(surface, trim, head, 1, border_radius=8)
        visor = pygame.Rect(round(x + 21), round(top + 5), 28, 9)
        pygame.draw.rect(surface, (13, 18, 34), visor, border_radius=4)
        pulse = 0.5 + 0.5 * math.sin(self.robot_scan_phase * 5.0)
        eye_radius = 2 + int(pulse > 0.82)
        for eye_x in (x + 29, x + 41):
            pygame.draw.circle(surface, eye, (round(eye_x), round(top + 9)), eye_radius)
            pygame.draw.circle(surface, (240, 242, 255),
                               (round(eye_x - 1), round(top + 8)), 1)

        sensor_base = pygame.Vector2(x + self.robot_width / 2, top + 1)
        sensor_tip = sensor_base + self._robot_vision_direction() * 12
        pygame.draw.line(surface, (116, 125, 164), sensor_base, sensor_tip, 3)
        pygame.draw.circle(surface, (18, 21, 37),
                           (round(sensor_tip.x), round(sensor_tip.y)), 5)
        pygame.draw.circle(surface, eye,
                           (round(sensor_tip.x), round(sensor_tip.y)), 2)

    # =========================================================
    # ROBOT SECURITY
    # =========================================================

    def trigger_robot_alert(self):

        self.robot_alert = True

        self.robot_alert_timer = (
            self.robot_alert_duration
        )

        self.feedback = (
            "SECURITY ALERT! "
            "ROBOT DETECTED INTRUSION!"
        )

        if self.game:

            self.game.security.increase(25)
            self.game.score.penalize(15)

    def draw_robot_scan(self, surface):
        if self.current_room_number() == 2 and (
            self.room2_robot_disabled_timer > 0 or self.robot_state == "DISABLED"
        ):
            return

        origin = self._robot_eye_center()
        direction = self._robot_vision_direction()
        half_angle = math.radians(self.robot_vision_half_angle)
        scan_r = self.robot_scan_radius + (
            28 if self.current_room_number() == 2 and self.room2_overload_active_timer > 0 else 0
        )

        # Clip vision rays against solid walls/covers in Room 2 so the cone
        # visually respects Cover 2 and Cover 3.
        points = [origin]
        steps = 14 if self.current_room_number() == 2 else 2
        for i in range(steps + 1):
            offset = -half_angle + (2 * half_angle * i / steps)
            ray_dir = direction.rotate_rad(offset)
            reach = float(scan_r)
            if self.current_room_number() == 2:
                for wall in self.room.walls:
                    interval = self._ray_rect_interval(origin, (ray_dir.x, ray_dir.y), wall)
                    if interval is not None and interval[0] >= 0:
                        reach = min(reach, max(0.0, interval[0]))
            points.append((origin[0] + ray_dir.x * reach, origin[1] + ray_dir.y * reach))

        layer = self.robot_scan_surface
        layer.fill((0, 0, 0, 0))
        overloading = self.current_room_number() == 2 and (
            self.room2_overload_warning_timer > 0 or self.room2_overload_active_timer > 0
        )
        if overloading:
            fill, edge = (255, 50, 70, 34), (255, 110, 125, 68)
        elif self.robot_alert:
            fill, edge = (255, 70, 75, 24), (255, 100, 120, 44)
        elif self.current_room_number() == 2:
            fill, edge = (65, 195, 245, 18), (95, 225, 255, 38)
        else:
            fill, edge = (145, 105, 220, 12), (150, 135, 205, 20)
        pygame.draw.polygon(layer, fill, points)
        pygame.draw.lines(layer, edge, False, points[1:], 1)
        surface.blit(layer, (0, 0))

    # =========================================================
    # PHASE 1 VISUALS (presentation only)
    # =========================================================

    LAYOUT_ACCENT = (150, 110, 255)
    PANEL_FILL = (10, 12, 22, 238)
    BODY_SIZE = 27
    RAIL_TOP_PAD = 3
    RAIL_HEIGHT = 18
    PANEL_BOTTOM = 587
    GATE_OPEN_SECONDS = 0.6
    ROBOT_LABEL_GAP = 16

    def _vis_state(self):
        if not hasattr(self, "_vis"):
            self._vis = {
                "fonts": {},
                "gates": {},
                "cache": {},
                "panel_surfaces": {},
                "sparks": [],
                "rng": random.Random(7),
                "time": 0.0,
            }

        return self._vis

    def _font(self, size):
        fonts = self._vis_state()["fonts"]

        if size not in fonts:
            fonts[size] = pygame.font.Font(None, size)

        return fonts[size]

    def _cached(self, key, builder):
        cache = self._vis_state()["cache"]

        if key not in cache:
            cache[key] = builder()

        return cache[key]

    @staticmethod
    def _mix(a, b, t):
        t = max(0.0, min(1.0, t))

        return tuple(
            int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3)
        )

    @staticmethod
    def _ease_out_cubic(t):
        t = max(0.0, min(1.0, t))

        return 1 - (1 - t) ** 3

    def _seconds(self):
        """Level-local animation time, advanced only by update(dt)."""
        return self._vis_state()["time"]

    def _draw_panel(self, surface, rect, fill=None):
        """Dark translucent panel with a subtle violet border."""
        color = fill or self.PANEL_FILL
        key = (rect.size, color)
        panels = self._vis_state()["panel_surfaces"]
        panel = panels.get(key)
        if panel is None:
            panel = pygame.Surface(rect.size, pygame.SRCALPHA)
            pygame.draw.rect(panel, color, panel.get_rect(), border_radius=8)
            pygame.draw.rect(panel, self.LAYOUT_ACCENT, panel.get_rect(),
                             2, border_radius=8)
            panels[key] = panel
        surface.blit(panel, rect.topleft)

    def _wrap_text(self, font, text, max_width, max_lines):
        """Split text into at most max_lines lines that fit max_width."""

        lines = []
        current = ""

        for word in text.split():
            trial = f"{current} {word}".strip()

            if font.size(trial)[0] <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = word

        lines.append(current)

        if len(lines) > max_lines:
            lines = lines[:max_lines]
            last = lines[-1]

            while last and font.size(last + "...")[0] > max_width:
                last = last[:-1]

            lines[-1] = last.rstrip() + "..."

        return lines

    def _build_floor(self):
        """Futuristic tiled floor with shaded edges and violet wall trim."""

        width, height = self.room_width, self.room_height
        tile = 40
        floor = pygame.Surface((width, height))

        dark, light = (17, 20, 36), (23, 27, 48)

        for ty in range(0, height, tile):
            for tx in range(0, width, tile):
                checker = (tx // tile + ty // tile) % 2 == 0

                pygame.draw.rect(
                    floor,
                    light if checker else dark,
                    (tx, ty, tile, tile),
                )

        lines = pygame.Surface((width, height), pygame.SRCALPHA)

        for x in range(0, width, tile):
            pygame.draw.line(lines, (130, 100, 230, 26), (x, 0), (x, height))

        for y in range(0, height, tile):
            pygame.draw.line(lines, (130, 100, 230, 26), (0, y), (width, y))

        floor.blit(lines, (0, 0))

        shade = pygame.Surface((width, height), pygame.SRCALPHA)

        for i in range(40):
            alpha = int(170 * (1 - i / 40) ** 2)

            pygame.draw.rect(
                shade,
                (0, 0, 0, alpha),
                (i, i, width - 2 * i, height - 2 * i),
                1,
            )

        floor.blit(shade, (0, 0))

        pygame.draw.rect(floor, (11, 12, 24), (0, 0, width, height), 8)
        pygame.draw.rect(
            floor,
            self.LAYOUT_ACCENT,
            (8, 8, width - 16, height - 16),
            2,
        )

        glow = pygame.Surface((width, height), pygame.SRCALPHA)

        pygame.draw.rect(
            glow,
            (150, 110, 255, 40),
            (10, 10, width - 20, height - 20),
            3,
        )
        floor.blit(glow, (0, 0))

        for cx in (0, width - 14):
            for cy in (0, height - 14):
                pygame.draw.rect(
                    floor,
                    self.LAYOUT_ACCENT,
                    (cx, cy, 14, 14),
                    border_radius=3,
                )
                pygame.draw.rect(
                    floor,
                    (11, 12, 24),
                    (cx + 4, cy + 4, 6, 6),
                    border_radius=2,
                )

        return floor

    def _build_stripes(self):
        """Yellow/black hazard stripe strip for the rail edges."""

        strip = pygame.Surface((self.track_width, 4))
        strip.fill((22, 22, 28))

        for x in range(-4, self.track_width + 8, 8):
            pygame.draw.polygon(
                strip,
                (240, 190, 40),
                [(x, 4), (x + 4, 4), (x + 8, 0), (x + 4, 0)],
            )

        return strip

    def _build_glow(self):
        """Soft red halo drawn behind each laser beam."""

        glow = pygame.Surface(
            (self.laser_width + 16, self.laser_height + 16),
            pygame.SRCALPHA,
        )

        for pad, alpha in ((8, 18), (6, 32), (4, 52)):
            pygame.draw.rect(
                glow,
                (255, 50, 50, alpha),
                glow.get_rect().inflate(-(8 - pad) * 2, -(8 - pad) * 2),
                border_radius=8,
            )

        return glow

    def _lowest_rail_bottom(self):
        return max(
            (
                (laser["bottom"] + 4 if laser.get("axis") == "y"
                 else laser["cy"] + laser.get("layout_radius", laser["half"]) + 14
                 if laser.get("axis") == "r"
                 else laser["y"] - self.RAIL_TOP_PAD + self.RAIL_HEIGHT)
                for laser in self.lasers
            ),
            default=0,
        )

    def _laser_label_rects(self):
        font = self._font(self.BODY_SIZE)

        band = pygame.Rect(
            self.robot_left_boundary - 10,
            154,
            self.robot_right_boundary
            - self.robot_left_boundary
            + self.robot_width
            + 20,
            62,
        )

        rects = []

        for index, laser in enumerate(self.lasers):

            width, height = font.size(f"LASER {index + 1}")
            axis = laser.get("axis", "x")
            if axis == "t":
                rects.append(pygame.Rect(laser["x"] + 6,
                                         laser["max_y"] + 5,
                                         width, height))
                continue
            if axis == "y":
                rects.append(pygame.Rect(laser["x"] + 25, laser["bottom"] + 5, width, height))
                continue
            if axis == "r":
                reach = laser.get("layout_radius", laser["half"])
                rects.append(pygame.Rect(laser["cx"] + reach + 8,
                                         laser["cy"] + reach + 5, width, height))
                continue
            rail_top = laser["y"] - self.RAIL_TOP_PAD

            rect = pygame.Rect(
                self.track_x + 5,
                rail_top - height - 3,
                width,
                height,
            )

            if rect.colliderect(band):
                rect.y = rail_top + self.RAIL_HEIGHT + 3

            rects.append(rect)

        return rects

    def _draw_floor_zones(self, surface):
        """Render the core tripwire plates in the same timed safety states."""

        palettes = {
            "off": ((28, 30, 46), (93, 83, 128), (115, 107, 150)),
            "warning": ((87, 58, 22), (255, 190, 60), (255, 225, 145)),
            "active": ((104, 25, 38), (255, 65, 75), (255, 175, 180)),
        }
        for index, zone in enumerate(self.floor_zones):
            phase = self.floor_zone_phase(index)
            fill, edge, detail = palettes[phase]
            pygame.draw.rect(surface, (18, 20, 34), zone, border_radius=4)
            pygame.draw.rect(surface, fill, zone.inflate(-4, -4), border_radius=3)
            pygame.draw.rect(surface, edge, zone, 1, border_radius=4)
            for x in (zone.left + 8, zone.centerx, zone.right - 8):
                pygame.draw.line(surface, detail,
                                 (x, zone.top + 6), (x, zone.bottom - 7), 2)

    def _draw_room1_safe_space(self, surface, pocket, index):
        """One Room 1 pad.  All pads look alike until a beam warms up; then the
        pads the board's loop lit glow as shields and the rest show OFF, so the
        player who read the code is already standing in the right place."""
        threatened = (any(emitter["state"] in ("warning", "locking", "active")
                          for emitter in self.emitters)
                      or any(self.laser_phase(i) in ("warning", "active")
                             for i in range(len(self.lasers))))
        lit = self.lit_pads is None or index in self.lit_pads
        if not threatened:
            glow, fill, edge, ink, text = ((12, 43, 43), (12, 47, 50), (62, 206, 168),
                                           (151, 242, 210), f"PAD {index}")
        elif lit:
            glow, fill, edge, ink, text = ((24, 90, 70), (16, 70, 58), (120, 255, 190),
                                           (205, 255, 230), f"PAD {index}  SHIELD")
        else:
            glow, fill, edge, ink, text = ((60, 16, 22), (40, 18, 26), (220, 70, 80),
                                           (255, 170, 175), f"PAD {index}  OFF")
        pygame.draw.rect(surface, glow, pocket.inflate(6, 6), border_radius=9)
        pygame.draw.rect(surface, fill, pocket, border_radius=8)
        pygame.draw.rect(surface, edge, pocket, 2, border_radius=8)
        label = self._font(16).render(text, True, ink)
        surface.blit(label, label.get_rect(center=pocket.center))

    def _draw_room2_covers_and_terminal(self, surface):
        """Render Cover 2, Cover 3, and the Python Loops Override Terminal in Room 2."""
        for idx, cover in enumerate(self.room2_cover_rects, start=2):
            shadow = cover.move(0, 4)
            pygame.draw.rect(surface, (8, 10, 20), shadow, border_radius=7)
            pygame.draw.rect(surface, (24, 32, 54), cover, border_radius=6)
            pygame.draw.rect(surface, (68, 165, 225), cover, 2, border_radius=6)
            inner = cover.inflate(-10, -10)
            pygame.draw.rect(surface, (17, 23, 40), inner, border_radius=4)
            pygame.draw.line(surface, (85, 205, 250),
                             (inner.left + 4, inner.top + 3),
                             (inner.right - 4, inner.top + 3), 1)
            tag = self._font(15).render(f"COVER {idx}", True, (150, 215, 245))
            surface.blit(tag, tag.get_rect(center=cover.center))

        # Futuristic Override Terminal near the upper-middle area
        term = self.room2_terminal_rect
        pulse = 0.5 + 0.5 * math.sin(self._seconds() * 4.5)
        near = self._player_near_room2_terminal()
        solved = self.room2_override_solved

        base_pad = term.inflate(12, 8)
        pygame.draw.rect(surface, (12, 16, 30), base_pad, border_radius=7)
        border_col = (60, 230, 155) if solved else (90, 225, 255) if near else (62, 150, 210)
        pygame.draw.rect(surface, border_col, base_pad, 1, border_radius=7)

        # Metallic housing
        pygame.draw.rect(surface, (30, 36, 54), term, border_radius=5)
        pygame.draw.rect(surface, (110, 145, 190), term, 2, border_radius=5)

        # Glowing cyan/blue screen
        screen = pygame.Rect(term.x + 8, term.y + 6, term.width - 16, 16)
        scr_col = (24, 95, 78) if solved else (20, int(95 + 35 * pulse), int(145 + 45 * pulse))
        pygame.draw.rect(surface, scr_col, screen, border_radius=3)
        pygame.draw.rect(surface, (95, 235, 255), screen, 1, border_radius=3)
        for line_y in (screen.y + 5, screen.y + 10):
            pygame.draw.line(surface, (170, 245, 255),
                             (screen.x + 4, line_y), (screen.right - 6, line_y), 1)

        # Small red security warning lights on the console bezel
        led_col = (65, 235, 145) if solved else (255, 65, 80) if pulse > 0.4 else (140, 30, 45)
        for lx in (term.x + 7, term.right - 7):
            pygame.draw.circle(surface, led_col, (lx, term.bottom - 6), 3)

        # Interaction prompt when player approaches
        if near and not self.room2_override_panel_open:
            prompt_txt = "OVERRIDE ACTIVE" if solved else "[E] OVERRIDE SENTRY"
            prompt_col = (110, 245, 175) if solved else (115, 235, 255)
            lbl = self._font(17).render(prompt_txt, True, prompt_col)
            pill = lbl.get_rect(center=(term.centerx, term.bottom + 13)).inflate(12, 5)
            pygame.draw.rect(surface, (10, 15, 28), pill, border_radius=5)
            pygame.draw.rect(surface, prompt_col, pill, 1, border_radius=5)
            surface.blit(lbl, lbl.get_rect(center=pill.center))

    def _draw_room2_override_modal(self, surface):
        """Render the Room 2 Python Loops Override modal when open."""
        if self.current_room_number() != 2 or not self.room2_override_panel_open:
            return
        question = self.room2_override_question
        if not question:
            return

        # Dim playfield backdrop slightly
        backdrop = pygame.Surface((self.room_width, self.room_height), pygame.SRCALPHA)
        backdrop.fill((6, 10, 22, 165))
        surface.blit(backdrop, (self.room_x, self.room_y))

        modal, option_rects, close_rect = self._room2_override_modal_geometry()
        pygame.draw.rect(surface, (12, 17, 32), modal, border_radius=10)
        pygame.draw.rect(surface, (75, 210, 255), modal, 2, border_radius=10)

        # Header bar
        header = pygame.Rect(modal.x + 2, modal.y + 2, modal.width - 4, 38)
        pygame.draw.rect(surface, (18, 28, 52), header, border_radius=8)
        title = self._font(23).render(
            f"SENTRY OVERRIDE CONSOLE  ·  {question['difficulty'].upper()} LOOP CHALLENGE",
            True, (115, 235, 255),
        )
        surface.blit(title, (modal.x + 18, modal.y + 11))

        pygame.draw.rect(surface, (42, 30, 56), close_rect, border_radius=5)
        pygame.draw.rect(surface, (175, 130, 220), close_rect, 1, border_radius=5)
        close_lbl = self._font(17).render("ESC / E", True, (235, 230, 250))
        surface.blit(close_lbl, close_lbl.get_rect(center=close_rect.center))

        # Prompt & formatted Python code block
        prompt_surf = self._font(22).render(question["prompt"], True, (240, 245, 255))
        surface.blit(prompt_surf, (modal.x + 24, modal.y + 48))

        code_box = pygame.Rect(modal.x + 24, modal.y + 72, modal.width - 48, 66)
        pygame.draw.rect(surface, (8, 12, 24), code_box, border_radius=6)
        pygame.draw.rect(surface, (55, 145, 195), code_box, 1, border_radius=6)
        code_font = self._font(21)
        for idx, line in enumerate(question["code"]):
            surface.blit(
                code_font.render(line, True, (115, 235, 255)),
                (code_box.x + 14, code_box.y + 8 + idx * 18),
            )

        # Answer buttons (A-D / 1-4)
        letters = ("A", "B", "C", "D")
        for idx, rect in enumerate(option_rects):
            opt_text = question["options"][idx]
            is_selected = self.room2_override_selected == idx
            is_hover = self.room2_override_hover == idx
            is_correct = opt_text == question["answer"]

            if is_selected:
                if is_correct:
                    fill, edge = (20, 88, 62), (70, 240, 155)
                else:
                    fill, edge = (98, 28, 42), (255, 95, 110)
            elif is_hover:
                fill, edge = (28, 46, 78), (110, 225, 255)
            else:
                fill, edge = (20, 28, 48), (72, 145, 200)

            pygame.draw.rect(surface, fill, rect, border_radius=7)
            pygame.draw.rect(surface, edge, rect, 2, border_radius=7)

            badge = pygame.Rect(rect.x + 8, rect.centery - 10, 20, 20)
            pygame.draw.rect(surface, edge, badge, border_radius=4)
            b_txt = self._font(18).render(letters[idx], True, (10, 14, 24))
            surface.blit(b_txt, b_txt.get_rect(center=badge.center))

            ans_surf = self._font(20).render(opt_text, True, (240, 244, 255))
            surface.blit(ans_surf, (badge.right + 10, rect.centery - ans_surf.get_height() // 2))

        # Feedback and explanation footer inside modal
        if self.room2_override_feedback:
            fb_col = (75, 240, 155) if self.room2_override_solved else (255, 115, 125)
            fb_surf = self._font(20).render(self.room2_override_feedback, True, fb_col)
            surface.blit(fb_surf, (modal.x + 24, modal.bottom - 72))

            exp_lines = self._wrap_text(
                self._font(19), self.room2_override_explanation, modal.width - 48, 2
            )
            for row, line in enumerate(exp_lines):
                surface.blit(
                    self._font(19).render(line, True, (195, 215, 235)),
                    (modal.x + 24, modal.bottom - 48 + row * 18),
                )
        else:
            hint_line = self._font(19).render(
                "Choose quickly: room hazards stay active while this terminal is open.",
                True, (165, 190, 215),
            )
            surface.blit(hint_line, (modal.x + 24, modal.bottom - 34))

    def _draw_rails(self, surface):
        """Draw compact checkpoint-local rails and their timed beams."""

        glow = self._cached("glow", self._build_glow)
        pulse = 0.5 + 0.5 * math.sin(self._seconds() * 6.0)
        is_room2 = self.current_room_number() == 2
        r3 = self.current_room_number() == 3

        for index, laser in enumerate(self.lasers):

            phase = self.laser_phase(index)
            axis = laser.get("axis", "x")
            if r3 and axis == "r" and self.core_state == "offline":
                phase = "off"
            if laser.get("type") == "tracking":
                x, span = int(laser["x"]), int(laser["span"])
                track_top = int(laser["min_y"])
                track_height = int(laser["max_y"] - laser["min_y"])
                for rail_x in (x, x + span):
                    track = pygame.Rect(rail_x - 5, track_top, 10, track_height)
                    pygame.draw.rect(surface, (20, 23, 39), track, border_radius=4)
                    pygame.draw.rect(surface, (77, 70, 112), track, 1, border_radius=4)
                    pygame.draw.line(surface, (48, 44, 72),
                                     (rail_x, track.top + 7),
                                     (rail_x, track.bottom - 7), 1)
                    for cap_y in (track.top + 4, track.bottom - 4):
                        pygame.draw.circle(surface, (112, 99, 158),
                                           (rail_x, cap_y), 2)
                beam = self._laser_rect(laser)
                beam_color = {"off": (88, 76, 112),
                              "warning": (255, 190, 60),
                              "active": (255, 55, 70)}[phase]
                pygame.draw.line(surface, (34, 31, 50), beam.midleft,
                                 beam.midright, 5)
                if phase == "active":
                    pygame.draw.line(surface, (255, 45, 45), beam.midleft,
                                     beam.midright, beam.height)
                    pygame.draw.line(surface, (255, 195, 200), beam.midleft,
                                     beam.midright, 2)
                elif phase == "warning":
                    pygame.draw.line(surface, beam_color, beam.midleft,
                                     beam.midright, 3)
                    pygame.draw.circle(surface, (255, 215, 110),
                                       (int(laser["target_x"]), beam.centery), 8, 2)
                    pygame.draw.line(surface, (255, 215, 110),
                                     (int(laser["target_x"]) - 12, beam.centery),
                                     (int(laser["target_x"]) + 12, beam.centery), 1)
                else:
                    pygame.draw.line(surface, beam_color, beam.midleft,
                                     beam.midright, 1)
                for ex in (x, x + span):
                    pygame.draw.circle(surface, (25, 24, 39),
                                       (ex, beam.centery), 7)
                    pygame.draw.circle(surface, beam_color,
                                       (ex, beam.centery), 4)
                continue
            if axis == "y":
                rail = pygame.Rect(laser["x"] - 14, laser["top"] - 8, 42,
                                   laser["bottom"] - laser["top"] + 16)
                off_col = (60, 195, 240) if is_room2 else (85, 85, 105)
                color = {"off": off_col, "warning": (255, 190, 60),
                         "active": (255, 55, 65)}[phase]
                if r3:
                    color = self._r3_phase_colour(phase)
                pygame.draw.rect(surface, (12, 15, 28), rail.inflate(4, 2),
                                 border_radius=7)
                pygame.draw.rect(surface, (27, 30, 48), rail, border_radius=6)
                pygame.draw.rect(surface, (91, 81, 128), rail, 1, border_radius=6)
                slot = pygame.Rect(rail.centerx - 5, rail.y + 10,
                                   10, rail.height - 20)
                pygame.draw.rect(surface, (13, 16, 29), slot, border_radius=4)
                pygame.draw.line(surface, (65, 58, 94), slot.midtop,
                                 slot.midbottom, 1)
                for cap_y in (rail.top + 5, rail.bottom - 5):
                    cap = pygame.Rect(rail.left - 3, cap_y - 4, rail.width + 6, 8)
                    pygame.draw.rect(surface, (38, 41, 62), cap, border_radius=3)
                    pygame.draw.rect(surface, (118, 104, 160), cap, 1,
                                     border_radius=3)
                    pygame.draw.circle(surface, color, (rail.centerx, cap_y), 2)
                beam = self._laser_rect(laser)
                if phase == "active":
                    pygame.draw.rect(surface, color, beam)
                    pygame.draw.line(surface, (255, 190, 190), beam.midtop, beam.midbottom, 2)
                elif phase == "warning":
                    pygame.draw.rect(surface, (95, 62, 24), beam)
                    pygame.draw.rect(surface, color, beam, 2)
                else:
                    fill_off = (22, 68, 95) if (is_room2 or r3) else (49, 39, 62)
                    line_off = (75, 210, 250) if (is_room2 or r3) else (95, 76, 116)
                    pygame.draw.rect(surface, fill_off, beam, border_radius=2)
                    pygame.draw.line(surface, line_off, beam.midtop,
                                     beam.midbottom, 2 if is_room2 else 1)
                for cy in (rail.top, rail.bottom - 1):
                    pygame.draw.circle(surface, color, (rail.centerx, cy), 5)
                if r3:
                    self._r3_device(surface, (rail.centerx, rail.top + 4), "down",
                                    color, phase)
                    self._r3_device(surface, (rail.centerx, rail.bottom - 4), "up",
                                    color, phase)
                continue
            if axis == "r":
                center = (int(laser["cx"]), int(laser["cy"]))
                color = {"off": (105, 105, 145), "warning": (255, 190, 60),
                         "active": (255, 55, 65)}[phase]
                if r3:
                    color = self._r3_phase_colour(phase)
                    self._draw_core_floor(surface, center, laser, phase)
                danger_radius = int(laser.get("danger_radius", laser["half"] + 18))
                base_radius = danger_radius + 9

                if self.current_room_number() != 1:
                    pygame.draw.circle(surface, (17, 19, 34), center, base_radius)
                    pygame.draw.circle(surface, (74, 66, 112), center, base_radius, 2)
                    pygame.draw.circle(surface, color, center, danger_radius, 1)
                    for tick in range(8):
                        radians = math.radians(tick * 45)
                        inner = danger_radius - 4
                        outer = danger_radius + 3
                        start = (int(center[0] + math.cos(radians) * inner),
                                 int(center[1] + math.sin(radians) * inner))
                        end = (int(center[0] + math.cos(radians) * outer),
                               int(center[1] + math.sin(radians) * outer))
                        pygame.draw.line(surface, color, start, end, 2)

                    pulse = int((math.sin(self._seconds() * 7.0) + 1) * 1.5)
                    for lamp in range(4):
                        radians = math.radians(lamp * 90 + 45)
                        lamp_pos = (int(center[0] + math.cos(radians) * (danger_radius + 5)),
                                    int(center[1] + math.sin(radians) * (danger_radius + 5)))
                        lamp_color = color if phase != "off" else (100, 116, 180)
                        pygame.draw.circle(surface, (27, 28, 44), lamp_pos, 5 + pulse)
                        pygame.draw.circle(surface, lamp_color, lamp_pos, 3 + pulse)

                clip_before = surface.get_clip()
                if self.current_room_number() == 1:
                    surface.set_clip(self.room_map.current.bounds)

                for offset in laser.get("beam_offsets", (0.0,)):
                    beam_angle = laser["angle"] + offset
                    corners = self._scanner_corners(
                        laser, thickness=laser.get("beam_width", 14), angle=beam_angle)
                    ghost = self._scanner_corners(
                        laser, thickness=(laser.get("beam_width", 14) + 12), angle=beam_angle)
                    if phase == "active":
                        pygame.draw.polygon(surface, (115, 25, 40), ghost)
                        pygame.draw.polygon(surface, (255, 45, 45), corners)
                    elif phase == "warning":
                        pygame.draw.polygon(surface, (110, 72, 30), ghost)
                        pygame.draw.polygon(surface, color,
                                            self._scanner_corners(laser, 4, beam_angle))
                    else:
                        pygame.draw.polygon(surface, (52, 120, 172) if r3 else (94, 83, 126),
                                            self._scanner_corners(laser, 3, beam_angle))
                    radians = math.radians(beam_angle)
                    endpoint = (int(center[0] + math.cos(radians) * laser["half"]),
                                int(center[1] + math.sin(radians) * laser["half"]))
                    pygame.draw.circle(surface, (20, 22, 38), endpoint, 7)
                    pygame.draw.circle(surface, color, endpoint, 4)

                surface.set_clip(clip_before)

                if self.current_room_number() == 1:
                    pygame.draw.circle(surface, (12, 14, 25), center, 13)
                    pygame.draw.circle(surface, color, center, 13, 2)
                    pygame.draw.circle(surface, color, center, 4)
                else:
                    pygame.draw.circle(surface, (12, 14, 25), center, 15)
                    pygame.draw.circle(surface, (139, 121, 196), center, 15, 2)
                    pygame.draw.circle(surface, (50, 60, 88), center, 9)
                    pygame.draw.circle(surface, color, center, 4)
                    for bolt in range(4):
                        radians = math.radians(bolt * 90 + 45)
                        point = (int(center[0] + math.cos(radians) * 11),
                                 int(center[1] + math.sin(radians) * 11))
                        pygame.draw.circle(surface, (188, 190, 220), point, 1)
                if r3:
                    self._draw_core_reactor(surface, center)
                continue

            w = laser.get("width", self.laser_width)
            rail_left = int(laser.get("min_x", self.track_x))
            rail_right = int(
                laser.get("max_x", self.track_x + self.track_width - w) + w
            )
            rail = pygame.Rect(
                rail_left,
                laser["y"] - self.RAIL_TOP_PAD,
                rail_right - rail_left,
                self.RAIL_HEIGHT,
            )

            pygame.draw.rect(surface, (20, 22, 38), rail, border_radius=5)
            pygame.draw.rect(surface, (92, 76, 142), rail, 1, border_radius=5)
            pygame.draw.line(surface, (48, 43, 76),
                             (rail.x + 7, rail.centery),
                             (rail.right - 8, rail.centery), 1)
            off_lens = (65, 205, 250) if is_room2 else (105, 103, 132)
            lens = {"active": (255, 70, 80),
                    "warning": (255, 190, 65),
                    "off": off_lens}[phase]
            if r3:
                lens = self._r3_phase_colour(phase)
            for ex in (rail.x + 6, rail.right - 6):
                pygame.draw.circle(surface, (31, 29, 50), (ex, rail.centery), 5)
                pygame.draw.circle(surface, lens, (ex, rail.centery), 3)
            if r3:
                self._r3_device(surface, (rail.x + 14, rail.centery), "right",
                                lens, phase)
                self._r3_device(surface, (rail.right - 14, rail.centery), "left",
                                lens, phase)

            beam = pygame.Rect(
                int(laser["x"]),
                int(laser["y"]),
                w,
                self.laser_height,
            )

            if phase == "active":

                glow.set_alpha(int(170 + 70 * pulse))
                surface.blit(glow, (laser["x"] - 8, laser["y"] - 8))

                pygame.draw.rect(surface, (255, 45, 45), beam)
                pygame.draw.line(
                    surface,
                    (255, 175, 175),
                    (beam.x, beam.centery),
                    (beam.right - 1, beam.centery),
                    2,
                )

            elif phase == "warning":

                lit = int(self._seconds() * 8) % 2 == 0

                pygame.draw.rect(
                    surface, (110, 62, 30) if lit else (62, 32, 30), beam
                )

                if lit:
                    pygame.draw.rect(surface, (255, 190, 60), beam, 1)

            else:

                fill_off = (22, 68, 95) if (is_room2 or r3) else (49, 39, 62)
                line_off = (75, 210, 250) if (is_room2 or r3) else (95, 76, 116)
                pygame.draw.rect(surface, fill_off, beam, border_radius=4)
                pygame.draw.line(surface, line_off, beam.midleft,
                                 beam.midright, 2 if is_room2 else 1)

    @staticmethod
    def _emitter_open_fraction(emitter):
        if emitter["state"] in ("tracking", "warning", "locking", "active"):
            return 1.0
        if emitter["state"] == "opening":
            return 1.0 - max(0.0, emitter["timer"]) / emitter["open_time"]
        if emitter["state"] == "retracting":
            return max(0.0, emitter["timer"]) / emitter["retract_time"]
        return 0.0

    def _draw_emitters(self, surface):
        """Draw the physical box, animated shutters and source-matched beam."""
        is_room2 = self.current_room_number() == 2
        colors = {
            "closed": (65, 200, 245) if is_room2 else (112, 130, 205),
            "pending": (95, 215, 255) if is_room2 else (170, 125, 245),
            "tracking": (255, 205, 75) if is_room2 else (162, 135, 245),
            "opening": (255, 190, 70),
            "warning": (255, 190, 60),
            "locking": (255, 150, 48),
            "active": (255, 58, 64),
            "retracting": (255, 154, 72),
            "cooldown": (60, 190, 235) if is_room2 else (118, 111, 175),
        }
        r3 = self.current_room_number() == 3
        if r3:
            yellow, red, cyan = self.R3_YELLOW, self.R3_RED, self.R3_CYAN
            colors = {"closed": cyan, "pending": cyan, "tracking": yellow,
                      "opening": yellow, "warning": yellow, "locking": yellow,
                      "active": red, "retracting": cyan, "cooldown": cyan}
        for emitter in self.emitters:
            state = emitter["state"]
            color = colors[state]
            ox, oy = emitter["origin"]
            mount = emitter["mount"]
            if mount == "wall":
                housing = pygame.Rect(int(ox - 40), int(oy - 20), 40, 40)
                aperture = pygame.Rect(int(ox - 3), int(oy - 9), 7, 18)
                shutter_axis = "vertical"
            elif mount == "ceiling":
                housing = pygame.Rect(int(ox - 22), int(oy - 24), 44, 24)
                aperture = pygame.Rect(int(ox - 9), int(oy - 3), 18, 7)
                shutter_axis = "horizontal"
            else:
                housing = pygame.Rect(int(ox - 22), int(oy), 44, 26)
                aperture = pygame.Rect(int(ox - 9), int(oy - 4), 18, 7)
                shutter_axis = "horizontal"

            if state in ("tracking", "warning", "locking", "active"):
                geometry = self._emitter_beam_laser(emitter)
                beam_color = ((255, 45, 45) if state == "active" else
                              (255, 200, 70) if (state == "tracking" and is_room2) else
                              (172, 143, 250) if state == "tracking" else
                              (255, 190, 60))
                if r3:
                    beam_color = (colors[state] if state != "locking"
                                  else ((255, 245, 190) if int(self._seconds() * 10) % 2
                                        else colors[state]))
                width = emitter.get("beam_width", 10 if state == "active" else 3)
                corners = self._scanner_corners(geometry, width)
                if state == "active":
                    pygame.draw.polygon(surface, (115, 24, 35),
                                        self._scanner_corners(geometry, width + 12))
                elif state == "tracking":
                    pygame.draw.polygon(surface, (96, 78, 24) if r3 else (67, 52, 104),
                                        self._scanner_corners(geometry, width + 8))
                else:
                    pygame.draw.polygon(surface, (100, 62, 24),
                                        self._scanner_corners(geometry, width + 8))
                pygame.draw.polygon(surface, beam_color, corners)
                if state == "active":
                    pygame.draw.polygon(surface, (255, 200, 200),
                                        self._scanner_corners(geometry, 2))
                endpoint = (round(geometry["cx"] + math.cos(math.radians(geometry["angle"]))
                                  * geometry["half"]),
                            round(geometry["cy"] + math.sin(math.radians(geometry["angle"]))
                                  * geometry["half"]))
                pygame.draw.circle(surface, beam_color, endpoint, 6 if state == "active" else 4)
                if state in ("tracking", "warning", "locking") and emitter.get("target") is not None:
                    target = tuple(map(int, emitter["target"]))
                    target_color = ((255, 210, 95) if is_room2 else
                                    (205, 178, 255) if state == "tracking"
                                    else (255, 220, 130))
                    if r3:
                        target_color = (255, 225, 110)
                    pygame.draw.circle(surface, target_color, target, 10, 1)
                    pygame.draw.line(surface, target_color,
                                     (target[0] - 5, target[1]),
                                     (target[0] + 5, target[1]), 1)
                    pygame.draw.line(surface, target_color,
                                     (target[0], target[1] - 5),
                                     (target[0], target[1] + 5), 1)

            pygame.draw.rect(surface, (13, 16, 29), housing, border_radius=5)
            pygame.draw.rect(surface, (105, 94, 150), housing, 2, border_radius=5)
            pygame.draw.rect(surface, (29, 31, 48), aperture, border_radius=3)
            pygame.draw.rect(surface, color, aperture, 1, border_radius=3)

            open_amount = self._emitter_open_fraction(emitter)
            if shutter_axis == "vertical":
                shutter_h = max(0, int(aperture.height * (1 - open_amount) / 2))
                if shutter_h:
                    pygame.draw.rect(surface, (85, 91, 118),
                                     (aperture.x, aperture.y, aperture.width, shutter_h))
                    pygame.draw.rect(surface, (85, 91, 118),
                                     (aperture.x, aperture.bottom - shutter_h,
                                      aperture.width, shutter_h))
            else:
                shutter_w = max(0, int(aperture.width * (1 - open_amount) / 2))
                if shutter_w:
                    pygame.draw.rect(surface, (85, 91, 118),
                                     (aperture.x, aperture.y, shutter_w, aperture.height))
                    pygame.draw.rect(surface, (85, 91, 118),
                                     (aperture.right - shutter_w, aperture.y,
                                      shutter_w, aperture.height))

            for point in (housing.topleft, housing.topright,
                          housing.bottomleft, housing.bottomright):
                pygame.draw.circle(surface, (170, 174, 205), point, 2)
            lamp = (housing.centerx, housing.top + 5)
            if r3:
                self._r3_emitter_overlay(surface, emitter, housing, color)
                continue
            pygame.draw.circle(surface, (27, 28, 43), lamp, 5)
            pygame.draw.circle(surface, color, lamp, 3)

    def _robot_label_rect(self, size):
        width, height = size
        gap = self.ROBOT_LABEL_GAP
        top = int(self.robot_y - 12)

        right_rect = pygame.Rect(
            int(self.robot_x + self.robot_width) + gap,
            top,
            width,
            height,
        )
        left_rect = pygame.Rect(
            int(self.robot_x) - gap - width,
            top,
            width,
            height,
        )

        blocked = [
            rect.inflate(12, 6) for rect in self._laser_label_rects()
        ]
        for laser in self.lasers:
            axis = laser.get("axis", "x")
            if axis == "x":
                blocked.append(pygame.Rect(self.track_x, laser["y"] - self.RAIL_TOP_PAD,
                                           self.track_width, self.RAIL_HEIGHT))
            elif axis == "y":
                blocked.append(pygame.Rect(laser["x"] - 8, laser["top"] - 4, 30,
                                           laser["bottom"] - laser["top"] + 8))
            elif axis == "t":
                blocked.append(pygame.Rect(laser["x"], laser["min_y"],
                                           laser["span"], laser["max_y"] - laser["min_y"]))
            else:
                radius = laser.get("layout_radius", laser["half"]) + 10
                blocked.append(pygame.Rect(laser["cx"] - radius, laser["cy"] - radius,
                                           2 * radius, 2 * radius))
        gate_limit = self.final_exit_rect.left - 22

        def fits(rect):
            return (
                rect.right <= gate_limit
                and rect.left >= self.room_x + 20
                and rect.top >= 108
                and rect.bottom <= 475
                and not any(rect.colliderect(b) for b in blocked)
            )

        candidates = [right_rect, left_rect,
                      pygame.Rect(int(self.robot_x + self.robot_width / 2 - width / 2),
                                  top - height - 6, width, height),
                      pygame.Rect(int(self.robot_x + self.robot_width / 2 - width / 2),
                                  self.robot_y + self.robot_height + 8, width, height)]
        return next((candidate for candidate in candidates if fits(candidate)), candidates[2])

    # ---- exit gate ------------------------------------------------------

    def _gate_progress(self, gate):
        """Read the update-driven eased opening progress without side effects."""
        if gate.state == "locked":
            return 0.0
        entry = self._vis_state()["gates"].get(id(gate))
        if entry is None:
            return 1.0
        return self._ease_out_cubic(
            entry.get("elapsed", self.GATE_OPEN_SECONDS) / self.GATE_OPEN_SECONDS
        )

    def _draw_lock(self, surface, center):
        cx, cy = center
        colour = (235, 235, 242)

        pygame.draw.arc(
            surface,
            colour,
            (cx - 5, cy - 11, 10, 14),
            0,
            3.14159,
            2,
        )
        pygame.draw.rect(
            surface, colour, (cx - 7, cy - 3, 14, 11), border_radius=2
        )
        pygame.draw.circle(surface, (60, 20, 24), (cx, cy + 1), 2)
        pygame.draw.rect(surface, (60, 20, 24), (cx - 1, cy + 1, 2, 4))

    def _spawn_sparks(self, center, start_color=(255, 230, 120),
                      end_color=(60, 200, 120)):
        """Start a small spark burst (own RNG: never touches random's state)."""

        vis = self._vis_state()
        rng = vis["rng"]

        for _ in range(18):
            angle = rng.uniform(0.0, 6.2832)
            speed = rng.uniform(50.0, 170.0)

            vis["sparks"].append(
                {
                    "x": float(center[0]),
                    "y": float(center[1]),
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed,
                    "life": rng.uniform(0.35, 0.8),
                    "age": 0.0,
                    "start_color": start_color,
                    "end_color": end_color,
                }
            )

    def _update_visual_effects(self, dt):
        """Advance Level 3-only effects on the simulation clock."""
        vis = self._vis_state()
        vis["time"] += dt
        for gate in self.gates:
            entry = vis["gates"].get(id(gate))
            if entry is not None and gate.state != "locked":
                entry["state"] = gate.state
                entry["elapsed"] = min(
                    self.GATE_OPEN_SECONDS, entry.get("elapsed", 0.0) + dt
                )

        alive = []
        for spark in vis["sparks"]:
            spark["age"] += dt
            if spark["age"] >= spark["life"]:
                continue
            spark["x"] += spark["vx"] * dt
            spark["y"] += spark["vy"] * dt
            alive.append(spark)
        vis["sparks"] = alive

    def _draw_sparks(self, surface):
        vis = self._vis_state()
        for spark in vis["sparks"]:
            fade = 1.0 - spark["age"] / spark["life"]

            pygame.draw.circle(
                surface,
                self._mix(spark["start_color"], spark["end_color"], 1.0 - fade),
                (int(spark["x"]), int(spark["y"])),
                max(1, int(3 * fade)),
            )

    def _draw_room1_gate(self, surface, gate):
        """Draw Gate 1 as a recognizable bulkhead door and lock."""
        rect = gate.rect
        progress = self._gate_progress(gate)
        locked = gate.state == "locked"
        red, amber, green = (205, 58, 70), (245, 180, 62), (60, 210, 150)
        if locked:
            tone = red
        elif progress < 0.5:
            tone = self._mix(red, amber, progress * 2)
        else:
            tone = self._mix(amber, green, (progress - 0.5) * 2)

        frame = rect.inflate(30, 14)
        pygame.draw.rect(surface, (8, 11, 22), frame, border_radius=8)
        pygame.draw.rect(surface, (48, 50, 73), frame.inflate(-6, -6),
                         border_radius=6)
        pygame.draw.rect(surface, tone, frame, 2, border_radius=8)

        pygame.draw.rect(surface, (7, 10, 20), rect)
        for x in (frame.left + 5, frame.right - 10):
            rail = pygame.Rect(x, frame.top + 7, 5, frame.height - 14)
            pygame.draw.rect(surface, (30, 34, 52), rail, border_radius=2)
            pygame.draw.line(surface, tone, rail.midtop, rail.midbottom, 1)

        leaf_height = int(round((rect.height - 4) * (1.0 - progress) / 2.0))
        if leaf_height > 0:
            leaf_color = self._mix(tone, (24, 27, 42), 0.2)
            leaves = (
                pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, leaf_height),
                pygame.Rect(rect.x + 2, rect.bottom - 2 - leaf_height,
                            rect.width - 4, leaf_height),
            )
            for leaf in leaves:
                pygame.draw.rect(surface, leaf_color, leaf, border_radius=2)
                pygame.draw.line(surface, tone, leaf.midleft, leaf.midright, 2)
                for y in range(leaf.top + 12, leaf.bottom - 4, 24):
                    pygame.draw.line(surface, (75, 78, 99),
                                     (leaf.left + 3, y), (leaf.right - 3, y), 1)

        label = self._font(14).render("GATE 1", True, (230, 225, 240))
        surface.blit(label, label.get_rect(center=(rect.centerx, frame.top - 8)))
        status_text = "LOCKED" if locked else ("OPEN" if gate.is_open() else "RELEASING")
        status_color = red if locked else (green if gate.is_open() else amber)
        status = self._font(13).render(status_text, True, status_color)
        surface.blit(status, status.get_rect(center=(rect.centerx, frame.bottom + 4)))

        badge = (rect.centerx, rect.centery)
        pygame.draw.circle(surface, (16, 18, 29), badge, 15)
        pygame.draw.circle(surface, tone, badge, 15, 2)
        lamp = (rect.centerx, rect.top + 13)
        pygame.draw.circle(surface, (20, 22, 34), lamp, 5)
        pygame.draw.circle(surface, tone, lamp, 3)
        if locked or progress < 0.75:
            self._draw_lock(surface, badge)
        else:
            pygame.draw.circle(surface, green, badge, 5, 2)

        self._draw_sparks(surface)

    def _draw_room2_gate(self, surface, gate):
        """Draw Gate 2 with distinct locked/unlocked visual states and security framing."""
        rect = gate.rect
        progress = self._gate_progress(gate)
        locked = gate.state == "locked"
        red, amber, cyan_open = (225, 60, 75), (255, 195, 70), (65, 235, 190)

        if locked:
            tone = red
        elif progress < 0.5:
            tone = self._mix(red, amber, progress * 2)
        else:
            tone = self._mix(amber, cyan_open, (progress - 0.5) * 2)

        frame = rect.inflate(28, 12)
        pygame.draw.rect(surface, (10, 14, 28), frame, border_radius=8)
        pygame.draw.rect(surface, (36, 44, 68), frame.inflate(-5, -5), border_radius=6)
        pygame.draw.rect(surface, tone, frame, 2, border_radius=8)
        pygame.draw.rect(surface, (8, 11, 22), rect)

        leaf_height = int(round((rect.height - 4) * (1.0 - progress) / 2.0))
        if leaf_height > 0:
            leaf_color = self._mix(tone, (22, 28, 46), 0.25)
            leaves = (
                pygame.Rect(rect.x + 2, rect.y + 2, rect.width - 4, leaf_height),
                pygame.Rect(rect.x + 2, rect.bottom - 2 - leaf_height,
                            rect.width - 4, leaf_height),
            )
            for leaf in leaves:
                pygame.draw.rect(surface, leaf_color, leaf, border_radius=2)
                pygame.draw.line(surface, tone, leaf.midleft, leaf.midright, 2)
                for y in range(leaf.top + 10, leaf.bottom - 4, 20):
                    pygame.draw.line(surface, (75, 110, 145),
                                     (leaf.left + 3, y), (leaf.right - 3, y), 1)

        label = self._font(14).render("GATE 2", True, (220, 235, 250))
        surface.blit(label, label.get_rect(center=(rect.centerx, frame.top - 8)))
        status_text = "LOCKED" if locked else ("UNLOCKED" if gate.is_open() else "OPENING")
        status = self._font(13).render(status_text, True, tone)
        surface.blit(status, status.get_rect(center=(rect.centerx, frame.bottom + 5)))

        badge = (rect.centerx, rect.centery)
        pygame.draw.circle(surface, (14, 18, 32), badge, 14)
        pygame.draw.circle(surface, tone, badge, 14, 2)
        if locked or progress < 0.75:
            self._draw_lock(surface, badge)
        else:
            pygame.draw.circle(surface, cyan_open, badge, 5, 2)

        self._draw_sparks(surface)

    def _draw_gate(self, surface, gate):
        """Draw a framed bulkhead with paired retracting door leaves."""

        if gate is self.gate1:
            self._draw_room1_gate(surface, gate)
            return
        if gate is self.gate2 and self.current_room_number() == 2:
            self._draw_room2_gate(surface, gate)
            return
        if gate is self.gate3 and self.current_room_number() == 3:
            self._draw_room3_vault(surface, gate)
            return

        rect = gate.rect
        progress = self._gate_progress(gate)
        locked = gate.state == "locked"

        red, amber, green = (200, 60, 60), (240, 200, 70), (60, 200, 120)

        if locked:
            tone = red
        elif progress < 0.5:
            tone = self._mix(red, amber, progress * 2)
        else:
            tone = self._mix(amber, green, (progress - 0.5) * 2)

        frame = rect.inflate(20, 8)
        pygame.draw.rect(surface, (10, 12, 24), frame, border_radius=7)
        pygame.draw.rect(surface, (50, 52, 76), frame.inflate(-4, -4),
                         border_radius=5)
        pygame.draw.rect(surface, tone, frame, 2, border_radius=7)

        pygame.draw.rect(surface, (9, 13, 25), rect)
        for x in (rect.left - 5, rect.right - 2):
            track = pygame.Rect(x, rect.top + 3, 7, rect.height - 6)
            pygame.draw.rect(surface, (31, 34, 52), track, border_radius=3)
            pygame.draw.line(surface, (102, 93, 137), track.midtop,
                             track.midbottom, 1)

        leaf_height = int(round(rect.height * (1.0 - progress) / 2.0))
        if leaf_height > 0:
            leaf_color = self._mix(tone, (24, 27, 42), 0.22)
            slat_color = self._mix(leaf_color, (8, 10, 20), 0.5)
            leaves = (
                pygame.Rect(rect.x + 1, rect.y, rect.width - 2, leaf_height),
                pygame.Rect(rect.x + 1, rect.bottom - leaf_height,
                            rect.width - 2, leaf_height),
            )
            for leaf in leaves:
                pygame.draw.rect(surface, leaf_color, leaf)
                pygame.draw.line(surface, tone, leaf.midleft, leaf.midright, 1)
                for y in range(leaf.top + 7, leaf.bottom - 3, 18):
                    pygame.draw.line(surface, slat_color,
                                     (leaf.left + 3, y), (leaf.right - 4, y), 2)

        for lamp_y in (frame.top + 11, frame.bottom - 11):
            pygame.draw.circle(surface, (17, 20, 34), (frame.centerx, lamp_y), 5)
            pygame.draw.circle(surface, tone, (frame.centerx, lamp_y), 2)

        if locked:
            self._draw_lock(surface, rect.center)

        self._draw_sparks(surface)

        gate_number = self.gates.index(gate) + 1
        marker = pygame.Rect(rect.centerx - 9, rect.bottom - 21, 18, 14)
        pygame.draw.rect(surface, (15, 18, 31), marker, border_radius=4)
        pygame.draw.rect(surface, (100, 94, 131), marker, 1, border_radius=4)
        number = self._font(16).render(str(gate_number), True, (245, 245, 252))
        surface.blit(number, number.get_rect(center=marker.center))

    # ---- question panel -------------------------------------------------

    def _bottom_layout(self):
        """Question panel geometry, rebuilt only when its inputs change."""

        key = (
            tuple(self.options),
            self.feedback,
            bool(self.show_hint),
            self._lowest_rail_bottom(),
            id(self.current_question),
            self.current_hint,
            self.current_room_number(),
        )
        cache = self._vis_state()["cache"]

        if cache.get("layout_key") != key:
            cache["layout"] = self._build_bottom_layout()
            cache["layout_key"] = key

        return cache["layout"]

    def _message_texts(self):
        """Longest hint and message each text size must hold untruncated."""

        room = self.current_room_number()
        tail = (
            "GATE 3 UNLOCKED! REACH THE FINAL EXIT."
            if room == 3
            else f"GATE {room} UNLOCKED! CROSS THE GATE TO CONTINUE."
        )
        success = (
            f"CORRECT! +{max(10, self.question_points)} points. "
            f"{tail}  {self.current_explanation}"
        )

        return (
            f"HINT: {self.current_hint}",
            success,
            "Hint revealed. Final score for this question is reduced by 15.",
        )

    def _footer_ink_bottom(self, size):
        """Lowest ink row of the footer font, relative to its y."""

        return self._cached(
            ("foot_ink", size),
            lambda: self._font(size)
            .render("Progress: 0/3 gates/challenges | gHjpq", True, (255, 255, 255))
            .get_bounding_rect()
            .bottom,
        )

    def _build_bottom_layout(self):
        panel_x = self.room_x + 10
        panel_w = self.room_width - 20
        inner_w = panel_w - 24
        # Room 3 keeps a wider right margin so answer text never touches the
        # button edge (the number key occupies the left 30 px).
        pad = 44 if self.current_room_number() == 3 else 36
        available = self.PANEL_BOTTOM - (self._lowest_rail_bottom() + 6)

        options = list(self.options)
        count = max(1, len(options))
        gap = 8

        hint_text, success_text, revealed_text = self._message_texts()
        text_tiers = ((27, 27, 27), (24, 24, 24), (23, 21, 21))

        def tier_fits(tier):
            fb_font, hint_font = self._font(tier[0]), self._font(tier[1])

            return (
                hint_font.size(hint_text)[0] <= inner_w
                and len(self._wrap_text(fb_font, success_text, inner_w, 9)) <= 2
                and len(self._wrap_text(fb_font, revealed_text, inner_w, 9)) <= 1
            )

        def plan(size, wrap):
            font = self._font(size)
            line_h = font.get_height()

            if not wrap:
                equal = min(203, (inner_w - gap * (count - 1)) // count)

                if all(font.size(o)[0] <= equal - pad for o in options):
                    widths = [equal] * count
                else:
                    needed = [font.size(o)[0] + pad for o in options]
                    spare = inner_w - gap * (count - 1) - sum(needed)

                    if spare < 0:
                        return None

                    widths = [w + spare // count for w in needed]

                return (font, widths, [[o] for o in options],
                        line_h, max(24, line_h + 6))

            needed = []

            for option in options:
                full = font.size(option)[0]
                wrap_w = 60

                while (
                    wrap_w < full
                    and len(self._wrap_text(font, option, wrap_w, 9)) > 2
                ):
                    wrap_w += 4

                needed.append(min(wrap_w, full) + pad)

            spare = inner_w - gap * (count - 1) - sum(needed)

            if spare < 0:
                return None

            widths = [w + spare // count for w in needed]
            lines = [
                self._wrap_text(font, o, w - pad, 2)
                for o, w in zip(options, widths)
            ]
            most = max((len(item) for item in lines), default=1)

            return font, widths, lines, line_h, max(24, most * line_h + 6)

        def stack(button_h, question_h, tier):
            fb_h = self._font(tier[0]).get_height()
            hint_h = self._font(tier[1]).get_height()
            message_h = max(hint_h + 2 + fb_h, 2 * (fb_h + 1))
            foot_ink = self._footer_ink_bottom(tier[2])

            return (
                2 + question_h + 2 + button_h + 3 + message_h + 3 + foot_ink + 2,
                message_h,
                foot_ink,
            )

        usable = [tier for tier in text_tiers if tier_fits(tier)] or [text_tiers[-1]]
        chosen = None

        for size in (27, 24, 22, 20, 18):
            for wrap in (False, True):
                attempt = plan(size, wrap)

                if attempt is None:
                    continue

                for tier in usable:
                    for question_size in (self.BODY_SIZE, 24, 22):
                        question_h = self._font(question_size).get_height()
                        total, message_h, foot_ink = stack(
                            attempt[4], question_h, tier
                        )

                        if total <= available:
                            chosen = (attempt, tier, question_size, question_h,
                                      total, message_h, foot_ink)
                            break

                    if chosen:
                        break

                if chosen:
                    break

            if chosen:
                break

        if chosen is None:
            attempt = plan(18, True) or plan(18, False)
            tier = text_tiers[-1]
            question_h = self._font(22).get_height()
            total, message_h, foot_ink = stack(attempt[4], question_h, tier)
            chosen = (attempt, tier, 22, question_h, total, message_h, foot_ink)

        (button_font, widths, button_lines, line_h, button_h), \
            tier, question_size, question_h, total, message_h, foot_ink = chosen

        fb_font = self._font(tier[0])
        hint_font = self._font(tier[1])
        foot_font = self._font(tier[2])
        question_font = self._font(question_size)

        fb_lines = []

        if self.feedback:
            fb_lines = self._wrap_text(fb_font, self.feedback, inner_w, 2)

        show_hint = self.show_hint and len(fb_lines) < 2
        fb_h = fb_font.get_height()

        top = self.PANEL_BOTTOM - total
        panel = pygame.Rect(panel_x, top, panel_w, total)

        question_y = top + 2
        button_y = question_y + question_h + 2
        message_y = button_y + button_h + 3

        group_w = sum(widths) + (count - 1) * gap
        x = panel_x + 12 + (inner_w - group_w) // 2
        buttons = []

        for width in widths:
            buttons.append(pygame.Rect(x, button_y, width, button_h))
            x += width + gap

        hint_y = message_y if show_hint else None

        if len(fb_lines) == 2:
            fb_rows = [message_y, message_y + fb_h + 1]
        elif len(fb_lines) == 1 and show_hint:
            fb_rows = [message_y + hint_font.get_height() + 2]
        elif len(fb_lines) == 1:
            fb_rows = [message_y + message_h - fb_h]
        else:
            fb_rows = []

        return {
            "panel": panel,
            "question_font": question_font,
            "question_y": question_y,
            "button_font": button_font,
            "buttons": buttons,
            "button_lines": button_lines,
            "line_h": line_h,
            "hint_font": hint_font,
            "hint_y": hint_y,
            "fb_font": fb_font,
            "fb_lines": fb_lines,
            "fb_rows": fb_rows,
            "foot_font": foot_font,
            "foot_y": top + total - 2 - foot_ink,
            "text_tier": tier,
            "available": available,
        }

    def _draw_question_panel(self, surface):

        layout = self._bottom_layout()
        panel = layout["panel"]
        center_x = panel.centerx

        self._draw_panel(surface, panel)

        if self.current_question:
            question = layout["question_font"].render(
                self.current_question["question"], True, (245, 245, 245)
            )
            surface.blit(
                question,
                question.get_rect(centerx=center_x, y=layout["question_y"]),
            )

        cap_font = self._font(22)

        for index, rect in enumerate(layout["buttons"]):

            fill, border, cap = (30, 26, 58), (110, 85, 190), self.LAYOUT_ACCENT

            if self.selected_option == index + 1:

                if index == self.correct_option_index:
                    fill, border, cap = (22, 92, 58), (60, 230, 110), (60, 230, 110)
                else:
                    fill, border, cap = (112, 32, 40), (255, 100, 100), (255, 100, 100)

            pygame.draw.rect(surface, fill, rect, border_radius=8)
            pygame.draw.rect(surface, border, rect, 2, border_radius=8)

            key = pygame.Rect(rect.x + 6, rect.centery - 9, 18, 18)

            pygame.draw.rect(surface, cap, key, border_radius=4)

            number = cap_font.render(str(index + 1), True, (16, 14, 32))
            surface.blit(number, number.get_rect(center=key.center))

            lines = layout["button_lines"][index]
            text_top = rect.centery - len(lines) * layout["line_h"] // 2

            for row, line in enumerate(lines):
                surface.blit(
                    layout["button_font"].render(line, True, (240, 240, 240)),
                    (key.right + 6, text_top + row * layout["line_h"]),
                )

        if layout["hint_y"] is not None:
            hint = layout["hint_font"].render(
                f"HINT: {self.current_hint}", True, (255, 210, 80)
            )
            surface.blit(
                hint, hint.get_rect(centerx=center_x, y=layout["hint_y"])
            )

        if self.feedback:

            if self.complete or "CORRECT" in self.feedback or "SUCCESSFUL" in self.feedback:
                colour = (60, 230, 110)
            elif "SECURITY ALERT" in self.feedback or "OVERLOAD" in self.feedback:
                colour = (255, 180, 60)
            elif "GATE" in self.feedback:
                colour = (255, 220, 80)
            else:
                colour = (255, 100, 100)

            for line, y in zip(layout["fb_lines"], layout["fb_rows"]):
                text = layout["fb_font"].render(line, True, colour)
                surface.blit(text, text.get_rect(centerx=center_x, y=y))

        foot = layout["foot_font"]
        footer_left = (
            "Press 1-4 = Gate MCQ  |  H = Hint  |  E = Override Console"
            if self.current_room_number() == 2
            else "Press 1-4 to answer  |  H = hint"
        )
        surface.blit(
            foot.render(footer_left, True, (180, 180, 190)),
            (panel.x + 16, layout["foot_y"]),
        )

        progress = foot.render(
            f"Progress: {self.current_question_number}"
            f"/{self.total_questions} gates/challenges",
            True,
            (180, 200, 210),
        )
        surface.blit(
            progress,
            progress.get_rect(topright=(panel.right - 16, layout["foot_y"])),
        )

    # =========================================================
    # RENDER
    # =========================================================

    def render(self, surface):

        tx = self._tx
        if tx is not None and not tx["drawing"]:
            self._draw_gate_transition(surface, tx)
            return

        self.room_map.draw(surface)

        surface.blit(
            self._cached("floor", self._build_floor),
            (self.room_x, self.room_y),
        )

        room_number = self.current_room_number()

        if room_number >= 2:
            self.draw_robot_scan(surface)

        # Draw bulkhead walls; Room 2 covers are rendered via dedicated industrial art
        for wall in self.barrier_walls:
            if room_number == 2 and wall in self.room2_cover_rects:
                continue
            pygame.draw.rect(surface, (21, 24, 40), wall)
            pygame.draw.line(surface, (82, 70, 128), wall.midleft, wall.midright, 1)

        if room_number == 2:
            self._draw_room2_covers_and_terminal(surface)

        pygame.draw.line(surface, (82, 70, 128),
                         (self.room_x + 2, self.play_top),
                         (self.room_x + self.room_width - 2, self.play_top), 1)
        pygame.draw.line(surface, (82, 70, 128),
                         (self.room_x + 2, self.play_bottom),
                         (self.room_x + self.room_width - 2, self.play_bottom), 1)

        entrance_x = self.room_x + 6
        for top in (190, 378):
            jamb = pygame.Rect(entrance_x, top, 14, 52)
            pygame.draw.rect(surface, (12, 14, 26), jamb, border_radius=4)
            pygame.draw.rect(surface, (116, 89, 180), jamb, 1, border_radius=4)
            pygame.draw.line(surface, (150, 110, 255),
                             (jamb.right, jamb.top + 6),
                             (jamb.right, jamb.bottom - 6), 2)

        for index, pocket in enumerate(self.safe_zones):
            if room_number == 1:
                self._draw_room1_safe_space(surface, pocket, index)
            else:
                pygame.draw.rect(surface, (12, 55, 58), pocket, border_radius=8)
                pygame.draw.rect(surface, (58, 235, 190), pocket, 2, border_radius=8)
                pygame.draw.rect(surface, (28, 115, 105), pocket.inflate(-10, -10), 1,
                                 border_radius=5)
                label = self._font(18).render(
                    "SAFE" if pocket.width < 100 else "SAFE ZONE", True, (150, 255, 220))
                surface.blit(label, label.get_rect(center=pocket.center))

        self._draw_floor_zones(surface)
        if room_number == 3:
            self._draw_room3_terminal(surface)

        left = self.room_x + 20
        right = self.room_x + self.room_width - 20

        # -------------------------
        # Compact local strip
        # -------------------------

        self._draw_panel(surface, pygame.Rect(left, 54, right - left, 46))

        surface.blit(
            self._font(28).render("THE LASER LOOP", True, (246, 241, 255)),
            (left + 12, 55),
        )

        timer_text = self.timer_font.render(
            f"CHALLENGE {self.time_left:.1f}s",
            True,
            (255, 210, 60),
        )
        surface.blit(
            timer_text, timer_text.get_rect(topright=(right - 12, 58))
        )

        status = self._font(18).render(
            f"QUESTION {self.current_question_number + 1}/3  ·  "
            f"{self.current_difficulty.upper()}  ·  {self.question_points} PTS",
            True, (190, 197, 216),
        )
        surface.blit(status, (left + 12, 79))

        room_labels = ("ENTRY", "LASER", "CORE")
        for index in range(3):
            chip = pygame.Rect(690 + index * 68, 77, 64, 18)
            passed = self.gates[index].state != "locked"
            current = index + 1 == room_number and not passed
            fill = (28, 72, 62) if passed else (57, 40, 92) if current else (29, 31, 47)
            edge = (65, 210, 160) if passed else self.LAYOUT_ACCENT if current else (75, 78, 98)
            pygame.draw.rect(surface, fill, chip, border_radius=6)
            pygame.draw.rect(surface, edge, chip, 1, border_radius=6)
            caption = self._font(15).render(
                f"{index + 1} {room_labels[index]}", True,
                (240, 240, 250))
            surface.blit(caption, caption.get_rect(center=chip.center))
            if index < 2:
                pygame.draw.line(surface, (115, 105, 142),
                                 (chip.right + 1, chip.centery),
                                 (chip.right + 5, chip.centery), 2)

        # -------------------------
        # Objective / Alert Banner
        # -------------------------

        board = self._loop_board()
        code_lines, code_font, code_step = board["code"], board["font"], board["step"]
        code_panel, lane = board["panel"], board["lane"]
        tall = len(code_lines) > 3
        banner_text = None

        if self.laser_hit_feedback_timer > 0:
            banner_text = "LASER HIT! SECURITY +10"
            banner_fill, banner_ink = (170, 30, 30, 220), (255, 245, 245)
        elif room_number == 2 and (
            self.room2_overload_warning_timer > 0 or self.room2_overload_active_timer > 0
        ):
            banner_text = "ROBOT OVERLOAD!"
            banner_fill, banner_ink = (185, 24, 42, 230), (255, 240, 240)
        elif room_number == 2 and self.room2_robot_disabled_timer > 0:
            banner_text = f"SENTRY OVERRIDDEN — OFFLINE FOR {self.room2_robot_disabled_timer:.1f}s"
            banner_fill, banner_ink = (18, 82, 96, 220), (145, 245, 255)
        elif room_number == 3 and (r3_banner := self._r3_banner()):
            banner_text, banner_fill, banner_ink = r3_banner
        elif self.robot_alert:
            banner_text = "!! SECURITY ALERT - ROBOT DETECTION !!"
            banner_fill, banner_ink = (150, 20, 20, 210), (255, 240, 240)

        if banner_text:

            banner = pygame.Surface(lane.size, pygame.SRCALPHA)

            pygame.draw.rect(
                banner, banner_fill, banner.get_rect(), border_radius=6
            )

            banner_font = self._font(22)

            if banner_font.size(banner_text)[0] > lane.width - 16:
                banner_font = self._font(20)

            text = banner_font.render(banner_text, True, banner_ink)
            banner.blit(text, text.get_rect(center=banner.get_rect().center))
            surface.blit(banner, lane.topleft)

        else:

            objective_font = self._font(20)
            lines = self._wrap_text(
                objective_font,
                self.ROOM_OBJECTIVES[room_number].replace(". ", "  ·  "),
                lane.width - 12,
                2,
            )

            for row, line in enumerate(lines):
                surface.blit(
                    objective_font.render(line, True, (205, 210, 220)),
                    (lane.x + 4, lane.y + 10 + row * 16),
                )

        self._draw_panel(surface, code_panel)
        surface.blit(self._font(15).render("LOOP LOGIC", True, (166, 151, 220)),
                     (code_panel.x + 8, code_panel.y + 5))

        for row, line in enumerate(code_lines):
            surface.blit(
                code_font.render(line, True, (90, 220, 255)),
                (code_panel.x + 86, code_panel.y + (2 if tall else 4) + row * code_step),
            )

        # -------------------------
        # Rails, lasers and emitters
        # -------------------------

        self._draw_rails(surface)
        self._draw_emitters(surface)
        if self.camera_bank is not None:
            self.camera_bank.draw(surface, self.laser_clock)

        # -------------------------
        # Exit gate and status
        # -------------------------

        active_gate = self.gates[room_number - 1]
        self._draw_gate(surface, active_gate)

        if room_number == 3:
            # The vault draws its own rotated EXIT sign once it is open.
            pygame.draw.line(surface, (65, 200, 160),
                             (self.final_exit_rect.right - 3, self.final_exit_rect.top),
                             (self.final_exit_rect.right - 3, self.final_exit_rect.bottom), 2)

        if room_number >= 2:
            self.draw_robot(surface)

        # -------------------------
        # Question panel & Room 2 Override modal
        # -------------------------

        self._draw_question_panel(surface)
        if room_number == 2:
            self._draw_room2_override_modal(surface)
        if room_number == 3:
            self._draw_room3_terminal_modal(surface)
        self._draw_room_transition(surface)

    def _loop_board(self):
        """Header layout: the LOOP LOGIC board (the loop this room really runs,
        levels/laser_requests.py) on the right, the objective lane in what is left."""
        request = self.room_requests.get(self.current_room_number())
        code = request["code"] if request else self.code_lines
        tall = len(code) > 3                     # four lines still fit the 44 px header band
        font = self._font(15 if tall else 16)
        width = max(font.size(line)[0] for line in code)
        panel = pygame.Rect(0, 102, max(210, width + 96), 44)
        panel.right = 900
        lane = pygame.Rect(60, 102, panel.left - 68, 44)
        return {"code": code, "font": font, "step": 10 if tall else 12, "panel": panel, "lane": lane}

    def _build_room_transition_surface(self, title):
        """Create the cached title card used for a brief room reveal."""
        card = pygame.Surface((610, 44), pygame.SRCALPHA)
        pygame.draw.rect(card, (9, 11, 22, 238), card.get_rect(), border_radius=10)
        pygame.draw.rect(card, (150, 110, 255, 245), card.get_rect(), 2,
                         border_radius=10)
        title_surface = self._font(22).render(title, True, (248, 242, 255))
        card.blit(title_surface,
                  title_surface.get_rect(center=(card.get_width() // 2, 15)))
        sub = self._font(15).render(
            "ACCESS GRANTED  ·  ENTERING NEXT SECTOR", True, (95, 225, 205))
        card.blit(sub, sub.get_rect(center=(card.get_width() // 2, 34)))
        return card

    def _draw_room_transition(self, surface):
        """Fade a short title card in and out without pausing gameplay."""
        if self.room_transition_timer <= 0 or not self.room_transition_title:
            return
        progress = 1.0 - self.room_transition_timer / self.room_transition_duration
        fade = max(0.0, math.sin(math.pi * progress))
        alpha = int(225 * fade)
        if alpha <= 0:
            return
        card = self._cached(
            ("room_transition", self.room_transition_title),
            lambda: self._build_room_transition_surface(
                self.room_transition_title))
        card.set_alpha(alpha)
        y = 102 + int(4 * (1.0 - self._ease_out_cubic(progress)))
        surface.blit(card, (60, y))

    # =========================================================
    # HINT PENALTY
    # =========================================================

    HINT_PENALTY = 10
    HINT_PENALTY_HARD = 15

    def hint_penalty(self):
        """Points deducted for using a hint (higher on Hard)."""

        if self.current_difficulty == "hard":
            return self.HINT_PENALTY_HARD

        return self.HINT_PENALTY

    # =========================================================
    # EVENT HANDLING
    # =========================================================

    def handle_event(self, event):
        """Handle keyboard and mouse input for Level 3 puzzles and Room 2 Override."""

        if self.complete or self._tx is not None:
            return

        # -----------------------------------------------------
        # Room 2 Override Terminal Modal Input
        # -----------------------------------------------------
        if self.current_room_number() == 2:
            if self.room2_override_panel_open:
                _, option_rects, close_rect = self._room2_override_modal_geometry()
                if event.type == pygame.MOUSEMOTION:
                    self.room2_override_hover = next(
                        (i for i, r in enumerate(option_rects) if r.collidepoint(event.pos)),
                        None,
                    )
                    return
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if close_rect.collidepoint(event.pos):
                        self.room2_override_panel_open = False
                        return
                    for idx, r in enumerate(option_rects):
                        if r.collidepoint(event.pos):
                            self._submit_room2_override_answer(idx)
                            return
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_ESCAPE, pygame.K_e, pygame.K_RETURN):
                        self.room2_override_panel_open = False
                        return
                    override_keys = {
                        pygame.K_a: 0, pygame.K_b: 1, pygame.K_c: 2, pygame.K_d: 3,
                        pygame.K_1: 0, pygame.K_2: 1, pygame.K_3: 2, pygame.K_4: 3,
                    }
                    if event.key in override_keys:
                        self._submit_room2_override_answer(override_keys[event.key])
                        return
                return

            # Open the Room 2 terminal when near and pressing E or clicking it
            if event.type == pygame.KEYDOWN and event.key == pygame.K_e:
                if self._player_near_room2_terminal():
                    self.room2_override_panel_open = True
                    return
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if self._player_near_room2_terminal() and self.room2_terminal_rect.inflate(16, 16).collidepoint(event.pos):
                    self.room2_override_panel_open = True
                    return

        if self.current_room_number() == 3 and self._handle_r3_terminal_event(event):
            return

        if event.type != pygame.KEYDOWN:
            return

        # -------------------------
        # Hint
        # -------------------------

        if event.key == pygame.K_h:

            if not self.show_hint:

                self.show_hint = True
                self.hint_used = True

                self.feedback = (
                    "Hint revealed. Final score "
                    "for this question is reduced by "
                    f"{self.hint_penalty()}."
                )

            return

        answer_keys = {
            pygame.K_1: 1,
            pygame.K_2: 2,
            pygame.K_3: 3,
            pygame.K_4: 4,
        }

        if event.key not in answer_keys:
            return

        selected = answer_keys[event.key]

        if selected > len(self.options):
            return

        self.selected_option = selected

        selected_index = selected - 1

        # -------------------------
        # Correct answer
        # -------------------------

        if selected_index == self.correct_option_index:

            earned_points = max(
                10,
                self.question_points,
            )

            if self.hint_used:

                earned_points = max(
                    10,
                    earned_points - self.hint_penalty(),
                )

            if self.game:
                self.game.score.add(
                    earned_points
                )

            explanation = (
                self.current_explanation
            )

            self.unlock_current_gate()

            if self.current_room_number() == 3:

                self.feedback = (
                    f"CORRECT! +{earned_points} points. "
                    "GATE 3 UNLOCKED! "
                    "REACH THE FINAL EXIT."
                )

            elif (self.current_room_number() == 2
                  and not self.room2_gate_challenge_survived):

                self.feedback = (
                    f"CORRECT! +{earned_points} points. "
                    "SURVIVE THE GATE EMITTER CYCLE TO OPEN GATE 2."
                )

            else:

                self.feedback = (
                    f"CORRECT! +{earned_points} points. "
                    f"GATE {self.current_room_number()} "
                    "UNLOCKED! "
                    "CROSS THE GATE TO CONTINUE."
                )

            if explanation:

                self.feedback += (
                    f"  {explanation}"
                )

            if self.current_room_number() == 3:
                return

        # -------------------------
        # Wrong answer
        # -------------------------

        else:

            self.feedback = (
                "INCORRECT! Try again."
            )

            if self.game:

                self.game.security.increase(20)
                self.game.score.penalize(10)

    # =========================================================
    # COMPLETION
    # =========================================================

    def is_complete(self):
        """Return True when Level 3 is complete."""

        return self.complete
