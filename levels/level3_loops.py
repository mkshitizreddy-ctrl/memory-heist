"""
levels/level3_loops.py
Owner: Member 3 - Yashovardhan

Level 3 - The Laser Loop

Multi-room progression:
    Room 1 -> Gate 1 -> Room 2 -> Gate 2 -> Room 3 -> Gate 3 -> Level 4

The global Easy/Medium/Hard difficulty is used to select questions.
"""

import json
import math
import random
from pathlib import Path

import pygame

from core.difficulty import DIFFICULTIES
from core.map_manager import Room, RoomMap
from core.npc import NPC
from entities.gate import Gate
from levels import lighting, patrol_cameras, patrol_decor, patrol_lanes
from ui.fonts import ui_font


class Level3LaserLoop:
    """Controls the Level 3 Laser Loop level."""

    def __init__(self, game=None):
        self.game = game

        # -------------------------
        # Level state
        # -------------------------
        self.complete = False
        self.selected_option = None
        self.feedback = ""

        # -------------------------
        # Question system
        # One challenge per room.
        # -------------------------
        self.total_questions = 3
        self.current_question_number = 0

        self.question_pool = []
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

        self.gate1 = Gate(
            850,
            180,
            width=20,
            height=120,
        )

        self.gate2 = Gate(
            850,
            180,
            width=20,
            height=120,
        )

        self.gate3 = Gate(
            850,
            180,
            width=20,
            height=120,
        )

        room1 = Room(
            "level3_room1",
            (self.room_x, self.room_y, self.room_width, self.room_height),
            walls=patrol_decor.WALLS_SCREEN,
            gates=[self.gate1],
        )

        room2 = Room(
            "level3_room2",
            (self.room_x, self.room_y, self.room_width, self.room_height),
            walls=patrol_decor.WALLS_SCREEN,
            gates=[self.gate2],
        )

        room3 = Room(
            "level3_room3",
            (self.room_x, self.room_y, self.room_width, self.room_height),
            walls=patrol_decor.WALLS_SCREEN,
            gates=[self.gate3],
        )

        self.final_exit_rect = pygame.Rect(850, 180, 50, 120)

        # Everyone starts below the curtains; the gates are above them.
        self.spawn_points = ((100, 446), (140, 446))

        self.room_map = RoomMap(
            [room1, room2, room3],
            exits=[
                (
                    "level3_room1",
                    (850, 180, 50, 120),
                    "level3_room2",
                    (100, 446),
                ),
                (
                    "level3_room2",
                    (850, 180, 50, 120),
                    "level3_room3",
                    (100, 446),
                ),
            ],
        )

        # -------------------------
        # Hazards (lasers, lanes and cameras all share one hit rule)
        # -------------------------
        self.laser_penalty_cooldown = 0.0
        self.laser_penalty_duration = 1.0
        self.laser_hit_feedback_timer = 0.0

        self.lane_loop = None               # Rooms 1 and 3: the lane loop (levels/patrol_lanes.py)
        self.camera_bank = None             # Room 2's sweeping cameras (levels/patrol_cameras.py)

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
        self.robot_right_boundary = 760

        # -------------------------
        # Robot detection system
        # -------------------------
        self.robot_scan_radius = 120
        self.robot_alert = False
        self.robot_alert_timer = 0
        self.robot_alert_duration = 2.5
        self.robot_detection_cooldown = 0

        # -------------------------
        # Robot scanning animation
        # -------------------------
        self.robot_scan_phase = 0.0

        self._step_clock = {}
        self.guard = None
        self._guard_wait = patrol_decor.GUARD_IDLE_EVERY
        self._guard_idles = 0

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

        self._lightlayer = lighting.LightLayer(ambient=patrol_decor.AMBIENT)
        self._guard_font = ui_font(16)

        self.start_questions()

    # =========================================================
    # PLAYER HELPERS
    # =========================================================

    def _sfx(self, name):
        """Play a sound effect if the game has audio (tests may not)."""
        audio = getattr(self.game, "audio", None)

        if audio is not None:
            audio.play(name)

    def _guard_says(self, text):
        if self.guard is not None:
            self.guard.say(text)

    STEP_EVERY = 0.32

    def _update_steps(self, dt):
        """Metal footsteps while a player walks the grated floor."""

        if not self.game or not hasattr(self.game, "player"):
            return

        players = [self.game.player]

        if getattr(self.game, "coop", False):
            players.append(self.game.player2)

        for player in players:
            clock = self._step_clock.get(id(player), 0.0)

            if getattr(player, "moving", False):
                clock += dt

                if clock >= self.STEP_EVERY:
                    clock = 0.0
                    self._sfx("step_metal")
            else:
                clock = self.STEP_EVERY * 0.6

            self._step_clock[id(player)] = clock

    def _update_guard(self, dt):
        """The night guard: walks his lap, greets you, grumbles now and then."""

        guard = self.guard

        if guard is None:
            return

        guard.update(dt)
        room = self.current_room_number()

        if self.game and hasattr(self.game, "player"):
            for key, rect in enumerate(self._player_rects()):
                if guard.notice(rect, key):
                    guard.say(patrol_decor.GUARD_GREETING[room])

        self._guard_wait -= dt

        if self._guard_wait <= 0 and guard.speech is None:
            lines = patrol_decor.GUARD_IDLE[room]
            guard.say(lines[self._guard_idles % len(lines)])
            self._guard_idles += 1
            self._guard_wait = patrol_decor.GUARD_IDLE_EVERY

    def _player_rects(self):
        """Return active player rectangles."""
        rects = [self.game.player.rect]

        if getattr(self.game, "coop", False):
            rects.append(self.game.player2.rect)

        return rects

    def _bring_partner(self, mover_rect):
        """Move the second player next to the player changing rooms."""
        if not getattr(self.game, "coop", False):
            return

        for rect in self._player_rects():
            if rect is not mover_rect:
                rect.topleft = (mover_rect.x + 36, mover_rect.y)

                if self.room_map.blocked(rect):
                    rect.topleft = mover_rect.topleft

    # =========================================================
    # LASER SYSTEM
    # =========================================================

    # ---- hazards ------------------------------------------------------
    #
    # Every hazard is safe for HAZARD_GRACE seconds after a room starts and
    # after every hit, and a lane or cone is only dangerous after its own
    # warning (see levels/patrol_lanes.py and levels/patrol_cameras.py).

    def active_beam_rects(self):
        """Collision rectangles of the lanes that are dangerous right now."""

        return self.lane_loop.active_rects() if self.lane_loop is not None else []

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

        player_rects = self._player_rects()
        spotted = None

        if self.camera_bank is not None:
            gate = self._current_gate()

            if gate.is_open() and self.camera_bank.on:
                self.camera_bank.switch_off()               # the answer ran "camera.on = False"
                self._sfx("door")

            spotted = self.camera_bank.update(dt, player_rects)

        if self.laser_penalty_cooldown > 0:
            return

        if spotted is not None:
            self._hazard_hit("CAMERA SPOTTED! SCORE -10", "alarm")
            return

        for laser_rect in self.active_beam_rects():

            if any(r.colliderect(laser_rect) for r in player_rects):
                self._hazard_hit("LASER HIT! SCORE -10", "zap")
                break

    def _hazard_hit(self, text, sound):
        """A hazard caught the player: score only, then everything re-arms."""

        self.laser_penalty_cooldown = self.laser_penalty_duration
        self.laser_hit_feedback_timer = 1.0

        self.feedback = text
        self._sfx(sound)
        self._guard_says(patrol_decor.GUARD_HIT)

        self.game.score.penalize(10)               # a hazard costs score only, never security

        # Recovery: every hazard re-arms, giving a safe window.
        if self.lane_loop is not None:
            self.lane_loop.rearm()

        if self.camera_bank is not None:
            self.camera_bank.rearm()

    def _robot_stood_down(self):
        """Room 3's `while patrol():` ends with `break` once the gate is open."""

        return self.current_room_number() == 3 and self._current_gate().is_open()

    def _current_gate(self):
        return (self.gate1, self.gate2, self.gate3)[self.current_room_number() - 1]

    # =========================================================
    # ROOM / PROGRESSION
    # =========================================================

    def current_room_number(self):
        """Return the current room number."""
        name = self.room_map.current_name

        if name == "level3_room1":
            return 1

        if name == "level3_room2":
            return 2

        return 3

    def current_room_name(self):
        return f"ROOM {self.current_room_number()}"

    def setup_room_hazards(self):
        """Create laser patterns for the current room."""

        room = self.current_room_number()

        difficulty = self.get_selected_difficulty()
        layout = {1: "columns", 3: "rows"}.get(room)
        self.lane_loop = patrol_lanes.LaneLoop(difficulty, layout) if layout else None
        self.camera_bank = patrol_cameras.CameraBank(difficulty) if room == 2 else None

        self.robot_speed = 120 + ((room - 1) * 30)

        self.time_limit = self.base_time_limit - (room - 1)
        self.time_left = self.time_limit

        self.robot_x = 120
        self.robot_direction = 1

        self.robot_detection_cooldown = 0
        self.robot_alert = False
        self.robot_alert_timer = 0

        self.laser_penalty_cooldown = 0.0
        self.laser_hit_feedback_timer = 0.0

        route = patrol_decor.GUARD_ROUTES[room]
        self.guard = NPC("night_guard", route[0], patrol=route)
        self._guard_wait = patrol_decor.GUARD_IDLE_EVERY

    def try_room_transition(self):
        """Move through a gate after it has been unlocked."""

        if not self.game or not hasattr(self.game, "player"):
            return

        player_rects = self._player_rects()
        room = self.current_room_number()

        if room == 1:
            gate = self.gate1
        elif room == 2:
            gate = self.gate2
        else:
            gate = self.gate3

        # Prevent walking through a locked gate.
        if not gate.is_open():
            pushed = False

            for player_rect in player_rects:
                if player_rect.colliderect(gate.rect):

                    if player_rect.centerx < gate.rect.centerx:
                        player_rect.right = gate.rect.left
                    else:
                        player_rect.left = gate.rect.right

                    pushed = True

            if pushed:
                return

        # Room 1 -> Room 2
        if room == 1:

            if not self.gate1.is_open():
                return

            old_room = self.room_map.current_name
            mover = None

            for player_rect in player_rects:
                if self.room_map.check_exit(player_rect):
                    mover = player_rect
                    break

            if mover is not None:
                self._bring_partner(mover)

                if self.room_map.current_name != old_room:
                    self.setup_room_hazards()

                    self.current_question_number = 1
                    self.load_current_question()

                    self.feedback = (
                        f"ENTERED ROOM {self.current_room_number()}!"
                    )

            return

        # Room 2 -> Room 3
        if room == 2:

            if not self.gate2.is_open():
                return

            old_room = self.room_map.current_name
            mover = None

            for player_rect in player_rects:
                if self.room_map.check_exit(player_rect):
                    mover = player_rect
                    break

            if mover is not None:
                self._bring_partner(mover)

                if self.room_map.current_name != old_room:
                    self.setup_room_hazards()

                    self.current_question_number = 2
                    self.load_current_question()

                    self.feedback = (
                        f"ENTERED ROOM {self.current_room_number()}!"
                    )

            return

        # Room 3 -> Level 4
        if room == 3:

            if self.gate3.is_open() and any(
                r.colliderect(self.final_exit_rect)
                for r in player_rects
            ):
                self.complete_level()

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

                if not key.startswith("level3_loop_"):
                    continue

                # Preferred new format:
                #
                # "room": 1
                #
                # If room is not present, use the old numbering.
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

                # Backward-compatible room assignment.
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

            # game.difficulty is a preset dict from
            # core.difficulty.get_difficulty(). Presets carry no
            # "name"/"level" key, so identify which preset it is.
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

            room_pool = self.room_question_pools.get(
                room_number,
                [],
            )

            # Select only questions matching the chosen
            # global difficulty.
            filtered_pool = [
                question
                for question in room_pool
                if question.get(
                    "difficulty",
                    "medium",
                ).lower() == difficulty
            ]

            # If there are no questions for that difficulty,
            # fall back to the room pool.
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

            self.feedback = (
                "No question available for this room."
            )

            return

        correct_answer = (
            self.current_question.get("answer")
        )

        stored_options = (
            self.current_question.get(
                "options",
                [],
            )
        )

        # Use options directly from JSON.
        if (
            isinstance(stored_options, list)
            and correct_answer in stored_options
            and len(stored_options) >= 2
        ):
            self.options = list(
                stored_options
            )

        else:
            # Build fallback choices.
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

        # Maximum of four options.
        self.options = self.options[:4]

        random.shuffle(self.options)

        # Safety check.
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

        # Keep the player's selected global difficulty.
        # The question's difficulty is used only when selecting
        # the question and must not overwrite the global setting.

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

    def unlock_current_gate(self):
        """Unlock the gate belonging to the current room."""

        room = self.current_room_number()

        if room == 1:

            self.gate1.unlock()
            self._sfx("door")
            self.feedback = "GATE 1 UNLOCKING!"

        elif room == 2:

            self.gate2.unlock()
            self._sfx("door")
            self.feedback = "GATE 2 UNLOCKING!"

        elif room == 3:

            self.gate3.unlock()
            self._sfx("door")
            self.feedback = "GATE 3 UNLOCKING!"

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, dt):
        """Update timer, rooms, lasers and security robot."""

        if self.complete:
            return

        self.room_map.update(dt)
        self._update_steps(dt)
        self._update_guard(dt)

        # -------------------------
        # Countdown timer
        # -------------------------

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

        if self.lane_loop is not None:
            self.lane_loop.update(dt)

        self.check_laser_collision(dt)

        # -------------------------
        # Robot animation
        # -------------------------

        self.robot_scan_phase += dt * 3.0

        if self.robot_alert:

            self.robot_alert_timer -= dt

            if self.robot_alert_timer <= 0:

                self.robot_alert = False
                self.robot_alert_timer = 0

        # -------------------------
        # Move robot
        # -------------------------

        self.robot_x += (
            self.robot_speed
            * self.robot_direction
            * dt
        )

        if self.robot_x >= self.robot_right_boundary:

            self.robot_x = self.robot_right_boundary
            self.robot_direction = -1

        elif self.robot_x <= self.robot_left_boundary:

            self.robot_x = self.robot_left_boundary
            self.robot_direction = 1

        # -------------------------
        # Robot detection
        # -------------------------

        if self.game and hasattr(
            self.game,
            "player",
        ):

            robot_center_x = (
                self.robot_x
                + self.robot_width / 2
            )

            robot_center_y = (
                self.robot_y
                + self.robot_height / 2
            )

            distance = min(
                (
                    (
                        r.centerx
                        - robot_center_x
                    ) ** 2
                    +
                    (
                        r.centery
                        - robot_center_y
                    ) ** 2
                ) ** 0.5
                for r in self._player_rects()
            )

            if self.robot_detection_cooldown > 0:
                self.robot_detection_cooldown -= dt

            if (
                distance <= self.robot_scan_radius
                and self.robot_detection_cooldown <= 0
                and not self._robot_stood_down()
            ):

                self.robot_alert = True

                self.robot_alert_timer = (
                    self.robot_alert_duration
                )

                self.robot_detection_cooldown = 4

                self.feedback = (
                    "SECURITY ROBOT DETECTED YOU!"
                )

                self.game.score.penalize(10)               # the patrol robot costs score only
                self._sfx("alarm")
                self._guard_says(patrol_decor.GUARD_ALERT)

        self.try_room_transition()

    # =========================================================
    # ROBOT DRAWING
    # =========================================================

    def draw_robot(self, surface):

        robot_rect = pygame.Rect(
            self.robot_x,
            self.robot_y,
            self.robot_width,
            self.robot_height,
        )

        pygame.draw.rect(
            surface,
            (70, 75, 90),
            robot_rect,
            border_radius=6,
        )

        pygame.draw.rect(
            surface,
            (100, 110, 130),
            robot_rect,
            2,
            border_radius=6,
        )

        face_rect = pygame.Rect(
            self.robot_x + 15,
            self.robot_y + 8,
            40,
            14,
        )

        pygame.draw.rect(
            surface,
            (20, 25, 35),
            face_rect,
            border_radius=3,
        )

        pygame.draw.circle(
            surface,
            (255, 60, 60),
            (
                int(self.robot_x + 25),
                int(self.robot_y + 15),
            ),
            3,
        )

        pygame.draw.circle(
            surface,
            (255, 60, 60),
            (
                int(self.robot_x + 45),
                int(self.robot_y + 15),
            ),
            3,
        )

        pygame.draw.line(
            surface,
            (100, 110, 130),
            (
                int(self.robot_x + 35),
                int(self.robot_y),
            ),
            (
                int(self.robot_x + 35),
                int(self.robot_y - 10),
            ),
            2,
        )

        pygame.draw.circle(
            surface,
            (255, 70, 70),
            (
                int(self.robot_x + 35),
                int(self.robot_y - 12),
            ),
            4,
        )

        pygame.draw.circle(
            surface,
            (30, 32, 40),
            (
                int(self.robot_x + 15),
                int(self.robot_y + self.robot_height),
            ),
            8,
        )

        pygame.draw.circle(
            surface,
            (30, 32, 40),
            (
                int(
                    self.robot_x
                    + self.robot_width
                    - 15
                ),
                int(
                    self.robot_y
                    + self.robot_height
                ),
            ),
            8,
        )

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

            self.game.score.penalize(15)               # an alert costs score only
            self._sfx("alarm")

    def draw_robot_scan(self, surface):

        center_x = int(
            self.robot_x
            + self.robot_width // 2
        )

        center_y = int(
            self.robot_y
            + self.robot_height
        )

        pulse = (
            pygame.math.Vector2(
                1,
                0,
            )
            .rotate(
                self.robot_scan_phase * 35
            )
            .x
            + 1
        ) * 0.5

        radius = int(
            self.robot_scan_radius
            + pulse * 15
        )

        scan_surface = pygame.Surface(
            (
                surface.get_width(),
                surface.get_height(),
            ),
            pygame.SRCALPHA,
        )

        pygame.draw.circle(
            scan_surface,
            (255, 80, 80, 22),
            (
                center_x,
                center_y,
            ),
            radius,
            2,
        )

        scan_angle = (
            self.robot_scan_phase * 35
        )

        scan_vector = pygame.math.Vector2(
            radius,
            0,
        ).rotate(scan_angle)

        pygame.draw.line(
            scan_surface,
            (255, 100, 100, 70),
            (
                center_x,
                center_y,
            ),
            (
                int(
                    center_x
                    + scan_vector.x
                ),
                int(
                    center_y
                    + scan_vector.y
                ),
            ),
            3,
        )

        surface.blit(
            scan_surface,
            (0, 0),
        )

    # =========================================================
    # PHASE 1 VISUALS (presentation only)
    #
    # Nothing here changes gameplay state. Animation timing comes
    # from pygame.time.get_ticks(), so update() stays untouched.
    # =========================================================

    LAYOUT_ACCENT = (150, 110, 255)  # Level 3 violet accent
    PANEL_FILL = (10, 12, 22, 238)
    BODY_SIZE = 27                   # about 18 px of text height
    PANEL_BOTTOM = 587               # footer text (with descenders) ends by y = 585
    GATE_OPEN_SECONDS = 0.6          # matches the Gate unlock animation
    ROBOT_LABEL_GAP = 16

    # ---- small helpers ------------------------------------------------

    def _vis_state(self):
        if not hasattr(self, "_vis"):
            self._vis = {
                "fonts": {},
                "gates": {},
                "cache": {},
                "sparks": [],
                "rng": random.Random(7),
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
        return pygame.time.get_ticks() / 1000.0

    def _draw_panel(self, surface, rect, fill=None):
        """Dark translucent panel with a subtle violet border."""

        panel = pygame.Surface(rect.size, pygame.SRCALPHA)

        pygame.draw.rect(
            panel,
            fill or self.PANEL_FILL,
            panel.get_rect(),
            border_radius=8,
        )
        pygame.draw.rect(
            panel,
            self.LAYOUT_ACCENT,
            panel.get_rect(),
            2,
            border_radius=8,
        )

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

    # ---- cached artwork (pygame drawing only, no image files) ---------

    HAZARD_BOTTOM = 472              # lowest hazard edge: the question panel starts below it

    def _lowest_rail_bottom(self):
        return self.HAZARD_BOTTOM

    def _gate_progress(self, gate):
        """Eased 0..1 opening progress, driven only by gate.state."""

        gates = self._vis_state()["gates"]
        entry = gates.setdefault(
            id(gate), {"state": gate.state, "start": None}
        )
        now = self._seconds()

        if gate.state == "locked":
            entry["state"] = "locked"
            entry["start"] = None

            return 0.0

        if entry["state"] == "locked":
            entry["start"] = now
            self._spawn_sparks(gate.rect.center)

        entry["state"] = gate.state

        if entry["start"] is None:
            return 1.0

        return self._ease_out_cubic(
            (now - entry["start"]) / self.GATE_OPEN_SECONDS
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

    def _spawn_sparks(self, center):
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
                }
            )

        vis["spark_time"] = self._seconds()

    def _draw_sparks(self, surface):
        vis = self._vis_state()

        if not vis["sparks"]:
            return

        now = self._seconds()
        dt = min(0.1, max(0.0, now - vis.get("spark_time", now)))
        vis["spark_time"] = now
        alive = []

        for spark in vis["sparks"]:

            spark["age"] += dt

            if spark["age"] >= spark["life"]:
                continue

            spark["x"] += spark["vx"] * dt
            spark["y"] += spark["vy"] * dt

            fade = 1.0 - spark["age"] / spark["life"]

            pygame.draw.circle(
                surface,
                self._mix((255, 230, 120), (60, 200, 120), 1.0 - fade),
                (int(spark["x"]), int(spark["y"])),
                max(1, int(3 * fade)),
            )

            alive.append(spark)

        vis["sparks"] = alive

    def _draw_gate(self, surface, gate):
        """Framed gate: red when locked, green when open, door retracts."""

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

        frame = rect.inflate(16, 4)

        pygame.draw.rect(surface, (12, 14, 26), frame, border_radius=6)
        pygame.draw.rect(surface, tone, frame, 2, border_radius=6)

        door_height = int(round(rect.height * (1 - progress)))

        if door_height > 0:

            door = pygame.Rect(rect.x, rect.y, rect.width, door_height)
            slat = self._mix(tone, (0, 0, 0), 0.45)

            pygame.draw.rect(surface, tone, door)

            for y in range(door.y + 6, door.bottom - 2, 12):
                pygame.draw.line(
                    surface, slat, (door.x + 2, y), (door.right - 3, y), 2
                )

        if progress >= 1.0:
            glow = pygame.Surface(frame.inflate(20, 20).size, pygame.SRCALPHA)

            pygame.draw.rect(
                glow, (60, 200, 120, 45), glow.get_rect(), border_radius=12
            )
            surface.blit(glow, frame.inflate(20, 20).topleft)

        if locked:
            self._draw_lock(surface, rect.center)

        self._draw_sparks(surface)

        # EXIT marker above the robot's patrol band (y 154-216), with a
        # dotted guide and a down arrow pointing at the gate.
        chip = pygame.Rect(rect.centerx - 11, 134, 60, 18)

        for y in range(chip.bottom + 3, frame.top - 2, 6):
            pygame.draw.line(
                surface,
                self._mix(tone, (12, 14, 26), 0.35),
                (rect.centerx, y),
                (rect.centerx, y + 2),
                2,
            )

        pygame.draw.rect(surface, (12, 14, 26), chip, border_radius=9)
        pygame.draw.rect(surface, tone, chip, 2, border_radius=9)

        nudge = int(round(1.5 * math.sin(self._seconds() * 5.0)))
        cy = chip.centery - 1 + nudge

        pygame.draw.polygon(
            surface,
            tone,
            [(rect.centerx - 5, cy - 3), (rect.centerx + 5, cy - 3), (rect.centerx, cy + 4)],
        )

        sign = self._font(22).render("EXIT", True, (238, 241, 248))
        surface.blit(
            sign, (chip.x + 21, chip.centery - sign.get_height() // 2)
        )

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
        """Geometry of the question panel (used by render and the tests).

        The panel is sized to its content and anchored at y = 587, so the
        footer text ends by y = 585 and the panel never touches a rail.
        Answer text uses the largest size that fits (one line if possible,
        otherwise two lines on buttons sized to their text), and the hint,
        feedback and footer use the largest of three sizes that holds every
        message for this question without truncation.
        """

        panel_x = self.room_x + 10
        panel_w = self.room_width - 20
        inner_w = panel_w - 24
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
            """Button font, widths, lines and height; None if impossible."""

            font = self._font(size)
            line_h = font.get_height()

            if not wrap:
                equal = min(203, (inner_w - gap * (count - 1)) // count)

                if all(font.size(o)[0] <= equal - 36 for o in options):
                    widths = [equal] * count
                else:
                    needed = [font.size(o)[0] + 36 for o in options]
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

                needed.append(min(wrap_w, full) + 36)

            spare = inner_w - gap * (count - 1) - sum(needed)

            if spare < 0:
                return None

            widths = [w + spare // count for w in needed]
            lines = [
                self._wrap_text(font, o, w - 36, 2)
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

        if chosen is None:                  # last resort: smallest tiers
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

            if self.complete or "CORRECT" in self.feedback:
                colour = (60, 230, 110)
            elif "SECURITY ALERT" in self.feedback:
                colour = (255, 180, 60)
            elif "GATE" in self.feedback:
                colour = (255, 220, 80)
            else:
                colour = (255, 100, 100)

            for line, y in zip(layout["fb_lines"], layout["fb_rows"]):
                text = layout["fb_font"].render(line, True, colour)
                surface.blit(text, text.get_rect(centerx=center_x, y=y))

        foot = layout["foot_font"]

        surface.blit(
            foot.render(
                "Press 1-4 to answer  |  H = hint", True, (180, 180, 190)
            ),
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
    #
    # Layout zones (960 x 640, shared HUD covers y 0-48):
    #   y  54-100  header panel (title, timer, question, progression)
    #   y 102-152  top lane: objective / banners + security code panel
    #   y 136      laser heading (below the spawn at 100,100)
    #   y 154-480  gameplay: robot, rails, lasers, gate
    #   y ~478-587 question panel (sized to its content, footer < 585)
    #   y 592-640  reserved for the shared radio toast
    # =========================================================

    def _apply_lighting(self, surface, room_number, gate):
        """Light the room (beams, emitters, robot torch, gate lamp); text is drawn after."""

        region = pygame.Rect(self.room_x, self.room_y, self.room_width, self.room_height)
        world = surface.subsurface(region).copy()
        ox, oy = region.topleft

        beams = []

        if self.lane_loop is not None:
            beams.extend(self.lane_loop.light_rects((ox, oy)))

        if self.camera_bank is not None:
            beams.extend(self.camera_bank.light_rects((ox, oy)))

        emitters = []

        robot_centre = (
            int(self.robot_x + self.robot_width // 2) - ox,
            int(self.robot_y + self.robot_height // 2) - oy,
        )
        gate_centre = (gate.rect.centerx - ox, gate.rect.centery - oy)

        lights = patrol_decor.room_lights(
            room_number, beams, emitters, robot_centre, self.robot_alert, gate_centre, gate.is_open()
        )
        self._lightlayer.apply(world, lights)
        # A laser hit flashes the room red for a moment.
        flash = min(1.0, self.laser_hit_feedback_timer) if self.laser_hit_feedback_timer > 0.6 else 0.0

        if flash:
            tint = pygame.Surface(region.size, pygame.SRCALPHA)
            tint.fill((255, 40, 40, int(110 * (flash - 0.6) / 0.4)))
            world.blit(tint, (0, 0))

        surface.blit(world, region.topleft)

    def render(self, surface):

        # The room: baked floor, wall and furniture, then the live wall parts.
        self.room_map.draw(surface)

        room_number = self.current_room_number()
        size = (self.room_width, self.room_height)

        surface.blit(
            self._cached(
                f"room{room_number}",
                lambda: patrol_decor.build_room(room_number, size),
            ),
            (self.room_x, self.room_y),
        )
        patrol_decor.draw_wall_life(surface, room_number, self._seconds())

        if room_number == 1:
            gate = self.gate1
        elif room_number == 2:
            gate = self.gate2
        else:
            gate = self.gate3

        # -------------------------
        # Rails, lasers and labels
        # -------------------------

        if self.lane_loop is not None:
            self.lane_loop.draw(surface, self._seconds())

        if self.camera_bank is not None:
            self.camera_bank.draw(surface, self._seconds())

        # -------------------------
        # Exit gate and status
        # -------------------------

        self._draw_gate(surface, gate)

        # -------------------------
        # Robot, guard, lighting, then the crisp wall text on top
        # -------------------------

        if not self._robot_stood_down():
            self.draw_robot_scan(surface)

        self.draw_robot(surface)

        if self.guard is not None:
            self.guard.draw(surface, self._guard_font)

        self._apply_lighting(surface, room_number, gate)

        patrol_decor.draw_header(
            surface,
            room_number,
            self.current_question_number + 1,
            self.total_questions,
            self.current_difficulty,
            self.question_points,
            self.time_left,
        )

        # -------------------------
        # Top lane: a banner when something just happened, otherwise
        # the objective pinned to the wall.
        # -------------------------

        lane = patrol_decor.BANNER_LANE
        banner_text = None

        if self.laser_hit_feedback_timer > 0:
            banner_text = "LASER HIT! SCORE -10"
            banner_fill, banner_ink = (170, 30, 30, 220), (255, 245, 245)
        elif self.robot_alert:
            banner_text = "!! SECURITY ALERT - ROBOT DETECTION !!"
            banner_fill, banner_ink = (150, 20, 20, 210), (255, 240, 240)

        if banner_text:

            banner = pygame.Surface(lane.size, pygame.SRCALPHA)

            pygame.draw.rect(
                banner, banner_fill, banner.get_rect(), border_radius=6
            )

            banner_font = self._font(self.BODY_SIZE)

            if banner_font.size(banner_text)[0] > lane.width - 16:
                banner_font = self._font(24)

            text = banner_font.render(banner_text, True, banner_ink)
            banner.blit(text, text.get_rect(center=banner.get_rect().center))
            surface.blit(banner, lane.topleft)

        else:

            patrol_decor.draw_notice(
                surface, ("Answer the loop", "question to open", "the door.")
            )

        if self.camera_bank is not None:
            patrol_decor.draw_camera_board(surface, self.camera_bank, self._seconds())
        elif self.lane_loop is not None:
            patrol_decor.draw_lane_board(
                surface,
                self.lane_loop,
                gate.is_open(),
                self._seconds(),
                nested=room_number == 3,
            )

        # -------------------------
        # Question panel
        # -------------------------

        self._draw_question_panel(surface)

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
        """Handle keyboard input for the Level 3 puzzle."""

        if event.type != pygame.KEYDOWN:
            return

        if self.complete:
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