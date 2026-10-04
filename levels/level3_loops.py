"""
levels/level3_loops.py
Owner: Member 3 - Yashovardhan

Level 3 - The Laser Loop

Multi-room progression:
    Room 1 -> Gate 1 -> Room 2 -> Gate 2 -> Room 3 -> Gate 3 -> Level 4

The global Easy/Medium/Hard difficulty remains separate from the
room-by-room progression implemented here.
"""

import json
import random
from pathlib import Path

import pygame

from core.map_manager import Room, RoomMap
from entities.gate import Gate


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

        self.load_questions()

        # -------------------------
        # Security timer
        # Room progression timer:
        # Room 1 = 20s
        # Room 2 = 19s
        # Room 3 = 18s
        #
        # This is separate from the
        # game's Easy/Medium/Hard setting.
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
            gates=[self.gate1],
        )

        room2 = Room(
            "level3_room2",
            (self.room_x, self.room_y, self.room_width, self.room_height),
            gates=[self.gate2],
        )

        room3 = Room(
            "level3_room3",
            (self.room_x, self.room_y, self.room_width, self.room_height),
            gates=[self.gate3],
        )

        self.final_exit_rect = pygame.Rect(850, 180, 50, 120)

        self.room_map = RoomMap(
            [room1, room2, room3],
            exits=[
                (
                    "level3_room1",
                    (850, 180, 50, 120),
                    "level3_room2",
                    (100, 350),
                ),
                (
                    "level3_room2",
                    (850, 180, 50, 120),
                    "level3_room3",
                    (100, 350),
                ),
            ],
        )

        # -------------------------
        # Laser settings
        # -------------------------
        self.track_x = 75
        self.track_y = 215
        self.track_width = 810
        self.track_height = 42

        self.laser_width = 150
        self.laser_height = 14
        # Laser speeds are set per room/per laser in setup_room_hazards().
        self.laser_speed = 200

        # Laser collision / penalty system
        self.laser_penalty_cooldown = 0.0
        self.laser_penalty_duration = 1.0
        self.laser_hit_feedback_timer = 0.0

        self.lasers = []

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

        # -------------------------
        # Robot scanning animation
        # -------------------------
        self.robot_scan_phase = 0.0

        # Create hazards after all robot state has been initialized.
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

        # Start the questions.
        self.start_questions()

    def check_laser_collision(self, dt):
        """Apply a small penalty when the player touches a laser.

        A one-second cooldown prevents repeated penalties while the
        player is still touching the same laser.
        """
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

        if self.laser_penalty_cooldown > 0:
            return

        player_rect = self.game.player.rect

        for laser in self.lasers:
            laser_rect = pygame.Rect(
                int(laser["x"]),
                int(laser["y"]),
                self.laser_width,
                self.laser_height,
            )

            if player_rect.colliderect(laser_rect):
                self.laser_penalty_cooldown = self.laser_penalty_duration
                self.laser_hit_feedback_timer = 1.0
                self.feedback = "LASER HIT! SECURITY +10"

                self.game.security.increase(10)
                self.game.score.penalize(10)
                break

    # =========================================================
    # ROOM / PROGRESSION
    # =========================================================

    def current_room_number(self):
        """Return Room 1, 2 or 3."""
        name = self.room_map.current_name

        if name == "level3_room1":
            return 1
        if name == "level3_room2":
            return 2
        return 3

    def current_room_name(self):
        """Return a short display name."""
        return f"ROOM {self.current_room_number()}"

    def setup_room_hazards(self):
        """Create fair, separated laser patterns for the current room."""
        room = self.current_room_number()

        # Each room adds a laser, but the lasers are separated vertically,
        # start at different positions, and use different speeds. This keeps
        # Room 3 challenging without turning it into an unavoidable wall.
        laser_patterns = {
            1: [
                {"x": 120, "y": 250, "direction": 1, "speed": 200},
            ],
            2: [
                {"x": 120, "y": 230, "direction": 1, "speed": 190},
                {"x": 520, "y": 350, "direction": -1, "speed": 230},
            ],
            3: [
                {"x": 120, "y": 210, "direction": 1, "speed": 180},
                {"x": 450, "y": 330, "direction": -1, "speed": 220},
                {"x": 250, "y": 450, "direction": 1, "speed": 260},
            ],
        }

        self.lasers = [laser.copy() for laser in laser_patterns[room]]

        # Room progression makes the robot faster.
        self.robot_speed = 120 + ((room - 1) * 30)

        # Room progression also reduces the local challenge timer.
        self.time_limit = self.base_time_limit - (room - 1)
        self.time_left = self.time_limit

        # Reset robot position.
        self.robot_x = 120
        self.robot_direction = 1

        # Reset detection cooldown when entering a new room.
        self.robot_detection_cooldown = 0
        self.robot_alert = False
        self.robot_alert_timer = 0

        # Fresh laser-hit cooldown for the new room.
        self.laser_penalty_cooldown = 0.0
        self.laser_hit_feedback_timer = 0.0

    def try_room_transition(self):
        """Move through a gate only after that gate has been opened."""

        if not self.game or not hasattr(self.game, "player"):
            return

        player_rect = self.game.player.rect
        room = self.current_room_number()

        # Keep the player from physically walking through a locked gate.
        if room == 1:
            gate = self.gate1
        elif room == 2:
            gate = self.gate2
        else:
            gate = self.gate3

        if not gate.is_open() and player_rect.colliderect(gate.rect):
            if player_rect.centerx < gate.rect.centerx:
                player_rect.right = gate.rect.left
            else:
                player_rect.left = gate.rect.right
            return

        # Room 1 -> Room 2
        if room == 1:
            if not self.gate1.is_open():
                return

            old_room = self.room_map.current_name
            if self.room_map.check_exit(player_rect):
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
            if self.room_map.check_exit(player_rect):
                if self.room_map.current_name != old_room:
                    self.setup_room_hazards()
                    self.current_question_number = 2
                    self.load_current_question()
                    self.feedback = (
                        f"ENTERED ROOM {self.current_room_number()}!"
                    )
            return

        # Room 3 -> Level 4.
        # The final question only opens Gate 3. The player must
        # physically cross the final gate before Level 3 completes.
        if room == 3:
            if self.gate3.is_open() and player_rect.colliderect(
                self.final_exit_rect
            ):
                self.complete_level()

    # =========================================================
    # QUESTION SYSTEM
    # =========================================================

    def load_questions(self):
        """Load Level 3 questions and organize them by room difficulty.

        Room 1: basic loop concepts (level3_loop_1 to level3_loop_6)
        Room 2: code/output questions (level3_loop_7 to level3_loop_8)
        Room 3: trickier loop behavior (level3_loop_9 to level3_loop_10)
        """

        self.room_question_pools = {
            1: [],
            2: [],
            3: [],
        }

        try:
            base_path = Path(__file__).resolve().parent.parent
            puzzle_path = base_path / "data" / "puzzles.json"

            with open(puzzle_path, "r", encoding="utf-8") as file:
                puzzles = json.load(file)

            for key, puzzle in puzzles.items():
                if not key.startswith("level3_loop_"):
                    continue

                try:
                    question_number = int(key.split("_")[-1])
                except ValueError:
                    continue

                if 1 <= question_number <= 6:
                    self.room_question_pools[1].append(puzzle)
                elif 7 <= question_number <= 8:
                    self.room_question_pools[2].append(puzzle)
                elif 9 <= question_number <= 10:
                    self.room_question_pools[3].append(puzzle)

        except (FileNotFoundError, json.JSONDecodeError):
            self.room_question_pools = {
                1: [],
                2: [],
                3: [],
            }

        # Keep a combined pool for answer-option generation.
        self.question_pool = (
            self.room_question_pools[1]
            + self.room_question_pools[2]
            + self.room_question_pools[3]
        )

    def start_questions(self):
        """Select one random question from each room's question pool."""

        self.selected_questions = []

        for room_number in (1, 2, 3):
            pool = self.room_question_pools.get(room_number, [])

            if pool:
                self.selected_questions.append(random.choice(pool))
            else:
                self.selected_questions.append(None)

        self.current_question_number = 0
        self.load_current_question()

    def load_current_question(self):
        """Load the question assigned to the current room."""

        room_number = self.current_room_number()

        if room_number > len(self.selected_questions):
            self.complete_level()
            return

        self.current_question = self.selected_questions[
            room_number - 1
        ]

        if self.current_question is None:
            self.feedback = "No question available for this room."
            return

        correct_answer = self.current_question["answer"]

        # Generate wrong answers from the same room's question pool first,
        # so the choices stay related to the current room's topic.
        room_pool = self.room_question_pools.get(room_number, [])

        possible_answers = list(
            {
                question["answer"]
                for question in room_pool
                if question.get("answer") != correct_answer
            }
        )

        # If a room has fewer than two different answers, use the
        # complete Level 3 pool as a fallback.
        if len(possible_answers) < 2:
            possible_answers = list(
                {
                    question["answer"]
                    for question in self.question_pool
                    if question.get("answer") != correct_answer
                }
            )

        if len(possible_answers) >= 2:
            wrong_answers = random.sample(possible_answers, 2)
        else:
            wrong_answers = possible_answers[:2]

        self.options = wrong_answers + [correct_answer]
        random.shuffle(self.options)

        self.correct_option_index = self.options.index(
            correct_answer
        )

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
            self.feedback = "GATE 1 UNLOCKING!"
        elif room == 2:
            self.gate2.unlock()
            self.feedback = "GATE 2 UNLOCKING!"
        elif room == 3:
            self.gate3.unlock()
            self.feedback = "GATE 3 UNLOCKING!"

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, dt):
        """Update timer, rooms, lasers and security robot."""

        if self.complete:
            return

        # -------------------------
        # Update current room/gate
        # -------------------------
        self.room_map.update(dt)

        # -------------------------
        # Countdown timer
        # -------------------------
        self.time_left -= dt

        if self.time_left <= 0:
            self.time_left = 0

            self.feedback = "TIME'S UP! Security increased."

            if self.game:
                self.game.security.increase(25)
                self.game.score.penalize(15)

            self.time_left = self.time_limit

        # -------------------------
        # Move lasers
        # -------------------------
        for laser in self.lasers:
            laser["x"] += (
                laser["speed"]
                * laser["direction"]
                * dt
            )

            if laser["x"] <= self.track_x:
                laser["x"] = self.track_x
                laser["direction"] = 1

            elif (
                laser["x"] + self.laser_width
                >= self.track_x + self.track_width
            ):
                laser["x"] = (
                    self.track_x
                    + self.track_width
                    - self.laser_width
                )
                laser["direction"] = -1

        # -------------------------
        # Laser player collision
        # -------------------------
        self.check_laser_collision(dt)

        # -------------------------
        # Robot scanning animation
        # -------------------------
        self.robot_scan_phase += dt * 3.0

        # -------------------------
        # Robot alert countdown
        # -------------------------
        if self.robot_alert:
            self.robot_alert_timer -= dt

            if self.robot_alert_timer <= 0:
                self.robot_alert = False
                self.robot_alert_timer = 0

        # -------------------------
        # Move security robot
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
        # Robot player detection
        # -------------------------
        if self.game and hasattr(self.game, "player"):
            player_rect = self.game.player.rect

            robot_center_x = (
                self.robot_x + self.robot_width / 2
            )
            robot_center_y = (
                self.robot_y + self.robot_height / 2
            )

            player_center_x = player_rect.centerx
            player_center_y = player_rect.centery

            distance = (
                (player_center_x - robot_center_x) ** 2
                + (player_center_y - robot_center_y) ** 2
            ) ** 0.5

            if self.robot_detection_cooldown > 0:
                self.robot_detection_cooldown -= dt

            if (
                distance <= self.robot_scan_radius
                and self.robot_detection_cooldown <= 0
            ):
                self.robot_alert = True
                self.robot_alert_timer = (
                    self.robot_alert_duration
                )
                self.robot_detection_cooldown = 4

                self.feedback = (
                    "SECURITY ROBOT DETECTED YOU!"
                )

                self.game.security.increase(20)
                self.game.score.penalize(10)

        # -------------------------
        # Room transition
        # -------------------------
        self.try_room_transition()

    # =========================================================
    # ROBOT DRAWING
    # =========================================================

    def draw_robot(self, surface):
        """Draw the patrolling security robot."""

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
                int(self.robot_y + self.robot_height),
            ),
            8,
        )

    # =========================================================
    # ROBOT SECURITY SYSTEM
    # =========================================================

    def trigger_robot_alert(self):
        """Trigger the robot security alert manually."""

        self.robot_alert = True
        self.robot_alert_timer = self.robot_alert_duration
        self.feedback = (
            "SECURITY ALERT! ROBOT DETECTED INTRUSION!"
        )

        if self.game:
            self.game.security.increase(25)
            self.game.score.penalize(15)

    def draw_robot_scan(self, surface):
        """Draw an animated scanning field around the robot."""

        center_x = int(
            self.robot_x + self.robot_width // 2
        )
        center_y = int(
            self.robot_y + self.robot_height
        )

        pulse = (
            pygame.math.Vector2(1, 0)
            .rotate(self.robot_scan_phase * 35)
            .x
            + 1
        ) * 0.5

        radius = int(
            self.robot_scan_radius + pulse * 15
        )

        scan_surface = pygame.Surface(
            (surface.get_width(), surface.get_height()),
            pygame.SRCALPHA,
        )

        pygame.draw.circle(
            scan_surface,
            (255, 80, 80, 22),
            (center_x, center_y),
            radius,
            2,
        )

        scan_angle = self.robot_scan_phase * 35

        scan_vector = pygame.math.Vector2(
            radius,
            0,
        ).rotate(scan_angle)

        pygame.draw.line(
            scan_surface,
            (255, 100, 100, 70),
            (center_x, center_y),
            (
                int(center_x + scan_vector.x),
                int(center_y + scan_vector.y),
            ),
            3,
        )

        surface.blit(scan_surface, (0, 0))

    # =========================================================
    # RENDER
    # =========================================================

    def render(self, surface):
        """Draw the current Level 3 room and puzzle."""

        # -------------------------
        # Draw current RoomMap room
        # -------------------------
        self.room_map.draw(surface)

        room_number = self.current_room_number()

        # -------------------------
        # Room title
        # -------------------------
        title_text = self.title_font.render(
            f"LEVEL 3 - THE LASER LOOP | ROOM {room_number}",
            True,
            (255, 255, 255),
        )

        surface.blit(
            title_text,
            (
                self.room_x + 25,
                self.room_y + 50,
            ),
        )

        # -------------------------
        # Question counter
        # -------------------------
        question_text = self.timer_font.render(
            f"QUESTION: {self.current_question_number + 1}"
            f"/{self.total_questions}",
            True,
            (90, 220, 255),
        )

        surface.blit(
            question_text,
            (
                self.room_x + 25,
                self.room_y + 25,
            ),
        )

        # -------------------------
        # Room progression
        # -------------------------
        progression_text = self.instruction_font.render(
            f"SECURITY PROGRESSION: ROOM {room_number}/3",
            True,
            (180, 220, 240),
        )

        surface.blit(
            progression_text,
            (
                self.room_x + 25,
                self.room_y + 80,
            ),
        )

        # -------------------------
        # Timer
        # -------------------------
        timer_text = self.timer_font.render(
            f"SECURITY TIMER: {self.time_left:.1f}s",
            True,
            (255, 210, 60),
        )

        timer_rect = timer_text.get_rect(
            topright=(
                self.room_x
                + self.room_width
                - 25,
                self.room_y + 25,
            )
        )

        surface.blit(timer_text, timer_rect)

        # -------------------------
        # Objective
        # -------------------------
        objective_text = self.objective_font.render(
            "Objective: Solve the loop challenge "
            "to unlock the gate.",
            True,
            (190, 195, 205),
        )

        surface.blit(
            objective_text,
            (
                self.room_x + 25,
                self.room_y + 105,
            ),
        )

        # -------------------------
        # Security heading
        # -------------------------
        security_text = self.heading_font.render(
            "LASER SECURITY SYSTEM",
            True,
            (255, 90, 90),
        )

        surface.blit(
            security_text,
            (
                self.room_x + 25,
                self.room_y + 135,
            ),
        )

        # -------------------------
        # Robot
        # -------------------------
        self.draw_robot_scan(surface)

        robot_label = self.instruction_font.render(
            f"SECURITY ROBOT - SPEED {self.robot_speed}",
            True,
            (255, 180, 80),
        )

        surface.blit(
            robot_label,
            (
                self.robot_x - 10,
                self.robot_y - 32,
            ),
        )

        self.draw_robot(surface)

        # -------------------------
        # Laser tracks
        # -------------------------
        for index, laser in enumerate(self.lasers):
            track_y = laser["y"] - 13

            pygame.draw.rect(
                surface,
                (42, 46, 58),
                (
                    self.track_x,
                    track_y,
                    self.track_width,
                    self.track_height,
                ),
            )

            pygame.draw.rect(
                surface,
                (65, 68, 80),
                (
                    self.track_x,
                    track_y,
                    self.track_width,
                    self.track_height,
                ),
                2,
            )

            pygame.draw.rect(
                surface,
                (255, 45, 45),
                (
                    laser["x"],
                    laser["y"],
                    self.laser_width,
                    self.laser_height,
                ),
            )

            label = self.instruction_font.render(
                f"LASER {index + 1}",
                True,
                (255, 120, 120),
            )

            surface.blit(
                label,
                (
                    self.track_x + 5,
                    track_y - 20,
                ),
            )

        # -------------------------
        # Gate status
        # -------------------------
        if room_number == 1:
            gate = self.gate1
            gate_text = "GATE 1"
        elif room_number == 2:
            gate = self.gate2
            gate_text = "GATE 2"
        else:
            gate = self.gate3
            gate_text = "GATE 3"

        if gate is not None:
            if gate.state == "locked":
                gate_status = "LOCKED"
            elif gate.state == "unlocking":
                gate_status = "UNLOCKING"
            else:
                gate_status = "OPEN"

            gate_surface = self.instruction_font.render(
                f"{gate_text}: {gate_status}",
                True,
                (255, 220, 100),
            )

            surface.blit(
                gate_surface,
                (
                    790,
                    315,
                ),
            )
        else:
            exit_surface = self.instruction_font.render(
                "FINAL EXIT",
                True,
                (60, 230, 110),
            )

            surface.blit(
                exit_surface,
                (
                    790,
                    315,
                ),
            )

        # -------------------------
        # Security code panel
        # -------------------------
        panel_x = 220
        panel_y = 275
        panel_width = 520
        panel_height = 125

        pygame.draw.rect(
            surface,
            (10, 13, 22),
            (
                panel_x,
                panel_y,
                panel_width,
                panel_height,
            ),
        )

        pygame.draw.rect(
            surface,
            (70, 105, 140),
            (
                panel_x,
                panel_y,
                panel_width,
                panel_height,
            ),
            2,
        )

        code_heading = self.heading_font.render(
            "SECURITY CODE",
            True,
            (240, 240, 240),
        )

        surface.blit(
            code_heading,
            (
                panel_x + 25,
                panel_y + 15,
            ),
        )

        code_y = panel_y + 50

        for line in self.code_lines:
            code_text = self.code_font.render(
                line,
                True,
                (90, 220, 255),
            )

            surface.blit(
                code_text,
                (
                    panel_x + 30,
                    code_y,
                ),
            )

            code_y += 23

        # -------------------------
        # Laser hit feedback
        # -------------------------
        if self.laser_hit_feedback_timer > 0:
            laser_hit_surface = pygame.Surface(
                (360, 42),
                pygame.SRCALPHA,
            )

            pygame.draw.rect(
                laser_hit_surface,
                (170, 30, 30, 220),
                laser_hit_surface.get_rect(),
                border_radius=6,
            )

            laser_hit_text = self.feedback_font.render(
                "LASER HIT! SECURITY +10",
                True,
                (255, 245, 245),
            )

            laser_hit_rect = laser_hit_text.get_rect(
                center=(
                    laser_hit_surface.get_width() // 2,
                    laser_hit_surface.get_height() // 2,
                )
            )

            laser_hit_surface.blit(
                laser_hit_text,
                laser_hit_rect,
            )

            surface.blit(
                laser_hit_surface,
                (
                    self.room_x
                    + self.room_width // 2
                    - laser_hit_surface.get_width() // 2,
                    125,
                ),
            )

        # -------------------------
        # Security alert
        # -------------------------
        if self.robot_alert:
            alert_surface = pygame.Surface(
                (self.room_width - 80, 38),
                pygame.SRCALPHA,
            )

            pygame.draw.rect(
                alert_surface,
                (150, 20, 20, 210),
                alert_surface.get_rect(),
                border_radius=6,
            )

            alert_text = self.feedback_font.render(
                "!! SECURITY ALERT - ROBOT DETECTION !!",
                True,
                (255, 240, 240),
            )

            alert_rect = alert_text.get_rect(
                center=(
                    alert_surface.get_width() // 2,
                    alert_surface.get_height() // 2,
                )
            )

            alert_surface.blit(
                alert_text,
                alert_rect,
            )

            surface.blit(
                alert_surface,
                (
                    self.room_x + 40,
                    170,
                ),
            )

        # -------------------------
        # Question
        # -------------------------
        if self.current_question:
            question_text = self.current_question["question"]

            question_surface = self.option_font.render(
                question_text,
                True,
                (245, 245, 245),
            )

            question_rect = question_surface.get_rect(
                centerx=(
                    self.room_x
                    + self.room_width // 2
                ),
                y=415,
            )

            surface.blit(
                question_surface,
                question_rect,
            )

        # -------------------------
        # Answers
        # -------------------------
        option_y = 445

        for index, option in enumerate(self.options):
            text_color = (240, 240, 240)

            if self.selected_option == index + 1:
                if index == self.correct_option_index:
                    text_color = (60, 230, 110)
                else:
                    text_color = (255, 100, 100)

            option_text = self.option_font.render(
                f"[{index + 1}]  {option}",
                True,
                text_color,
            )

            option_rect = option_text.get_rect(
                centerx=(
                    self.room_x
                    + self.room_width // 2
                ),
                y=option_y,
            )

            surface.blit(
                option_text,
                option_rect,
            )

            option_y += 27

        # -------------------------
        # Progress
        # -------------------------
        progress_text = self.instruction_font.render(
            f"Progress: {self.current_question_number}"
            f"/{self.total_questions} gates/challenges",
            True,
            (180, 200, 210),
        )

        progress_rect = progress_text.get_rect(
            center=(
                self.room_x
                + self.room_width // 2,
                535,
            )
        )

        surface.blit(
            progress_text,
            progress_rect,
        )

        # -------------------------
        # Feedback
        # -------------------------
        if self.feedback:
            if self.complete:
                feedback_color = (60, 230, 110)
            elif "CORRECT" in self.feedback:
                feedback_color = (60, 230, 110)
            elif "SECURITY ALERT" in self.feedback:
                feedback_color = (255, 180, 60)
            elif "GATE" in self.feedback:
                feedback_color = (255, 220, 80)
            else:
                feedback_color = (255, 100, 100)

            feedback_text = self.feedback_font.render(
                self.feedback,
                True,
                feedback_color,
            )

            feedback_rect = feedback_text.get_rect(
                center=(
                    self.room_x
                    + self.room_width // 2,
                    565,
                )
            )

            surface.blit(
                feedback_text,
                feedback_rect,
            )

        # -------------------------
        # Instruction
        # -------------------------
        instruction_text = self.instruction_font.render(
            "Press 1, 2 or 3 to choose an answer",
            True,
            (180, 180, 190),
        )

        instruction_rect = instruction_text.get_rect(
            center=(
                self.room_x
                + self.room_width // 2,
                590,
            )
        )

        surface.blit(
            instruction_text,
            instruction_rect,
        )

    # =========================================================
    # EVENT HANDLING
    # =========================================================

    def handle_event(self, event):
        """Handle keyboard input for the Level 3 puzzle."""

        if event.type != pygame.KEYDOWN:
            return

        if self.complete:
            return

        if event.key == pygame.K_1:
            selected = 1
        elif event.key == pygame.K_2:
            selected = 2
        elif event.key == pygame.K_3:
            selected = 3
        else:
            return

        self.selected_option = selected

        selected_index = selected - 1

        # -------------------------
        # Correct answer
        # -------------------------
        if selected_index == self.correct_option_index:
            self.feedback = (
                "CORRECT! Security bypassed."
            )

            if self.game:
                self.game.score.add(50)

            # One correct challenge opens the
            # gate for the current room.
            self.unlock_current_gate()

            # The correct answer only unlocks the gate.
            # The question changes only after the player physically
            # crosses the open gate into the next room.
            if self.current_room_number() == 3:
                self.feedback = (
                    "GATE 3 UNLOCKED! REACH THE FINAL EXIT."
                )
            else:
                self.feedback = (
                    f"GATE {self.current_room_number()} UNLOCKED! "
                    "CROSS THE GATE TO CONTINUE."
                )

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
        """Return True when the level is complete."""

        return self.complete
