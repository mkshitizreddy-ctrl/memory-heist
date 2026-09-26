"""
Level 3 - The Laser Loop

Topics:
- for loops
- while loops
- range()
- break
"""

import json
import random
from pathlib import Path

import pygame


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
        # -------------------------
        self.time_limit = 20
        self.time_left = self.time_limit

        # -------------------------
        # Room
        # -------------------------
        self.room_x = 40
        self.room_y = 30
        self.room_width = 880
        self.room_height = 560

        # -------------------------
        # Laser track
        # -------------------------
        self.track_x = 75
        self.track_y = 215
        self.track_width = 810
        self.track_height = 42

        # -------------------------
        # Moving laser
        # -------------------------
        self.laser_x = 100
        self.laser_y = 228
        self.laser_width = 150
        self.laser_height = 14

        self.laser_speed = 280
        self.laser_direction = 1

        # -------------------------
        # Security code
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

        # Load the first random questions
        self.start_questions()

    # =========================================================
    # QUESTION SYSTEM
    # =========================================================

    def load_questions(self):
        """Load Level 3 questions from data/puzzles.json."""

        try:
            base_path = Path(__file__).resolve().parent.parent
            puzzle_path = base_path / "data" / "puzzles.json"

            with open(puzzle_path, "r", encoding="utf-8") as file:
                puzzles = json.load(file)

            for key, puzzle in puzzles.items():
                if key.startswith("level3_"):
                    self.question_pool.append(puzzle)

        except (FileNotFoundError, json.JSONDecodeError):
            self.question_pool = []

    def start_questions(self):
        """Select random questions for this level."""

        if len(self.question_pool) < self.total_questions:
            self.selected_questions = self.question_pool.copy()
        else:
            self.selected_questions = random.sample(
                self.question_pool,
                self.total_questions
            )

        self.current_question_number = 0
        self.load_current_question()

    def load_current_question(self):
        """Load the current question and randomize its answer options."""

        if self.current_question_number >= len(self.selected_questions):
            self.complete_level()
            return

        self.current_question = self.selected_questions[
            self.current_question_number
        ]

        correct_answer = self.current_question["answer"]

        # Create answer options from the question pool.
        possible_answers = list(
            {
                question["answer"]
                for question in self.question_pool
            }
        )

        # Remove the correct answer first.
        wrong_answers = [
            answer
            for answer in possible_answers
            if answer != correct_answer
        ]

        # Pick two wrong answers.
        if len(wrong_answers) >= 2:
            wrong_answers = random.sample(wrong_answers, 2)
        else:
            wrong_answers = wrong_answers[:2]

        self.options = wrong_answers + [correct_answer]

        # Randomize the position of the correct answer.
        random.shuffle(self.options)

        self.correct_option_index = self.options.index(correct_answer)

        self.selected_option = None
        self.feedback = ""

        # Reset timer for each question.
        self.time_left = self.time_limit

    def complete_level(self):
        """Complete Level 3."""

        self.complete = True
        self.feedback = "LEVEL COMPLETE! All laser loops bypassed."

        if self.game:
            self.game.score.add(100)

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, dt):
        """Update the timer and moving laser."""

        if self.complete:
            return

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

            # Give the player another attempt.
            self.time_left = self.time_limit

        # -------------------------
        # Move laser
        # -------------------------
        self.laser_x += (
            self.laser_speed
            * self.laser_direction
            * dt
        )

        # Left boundary
        if self.laser_x <= self.track_x:
            self.laser_x = self.track_x
            self.laser_direction = 1

        # Right boundary
        elif (
            self.laser_x + self.laser_width
            >= self.track_x + self.track_width
        ):
            self.laser_x = (
                self.track_x
                + self.track_width
                - self.laser_width
            )
            self.laser_direction = -1

    # =========================================================
    # RENDER
    # =========================================================

    def render(self, surface):
        """Draw the Level 3 room and puzzle."""

        # =====================================================
        # ROOM
        # =====================================================

        pygame.draw.rect(
            surface,
            (24, 28, 42),
            (
                self.room_x,
                self.room_y,
                self.room_width,
                self.room_height,
            ),
        )

        pygame.draw.rect(
            surface,
            (140, 45, 45),
            (
                self.room_x,
                self.room_y,
                self.room_width,
                self.room_height,
            ),
            3,
        )

        # =====================================================
        # TITLE
        # =====================================================

        title_text = self.title_font.render(
            "LEVEL 3 - THE LASER LOOP",
            True,
            (255, 255, 255),
        )

        surface.blit(
            title_text,
            (self.room_x + 25, self.room_y + 50),
        )

        # =====================================================
        # QUESTION COUNTER
        # =====================================================

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

        # =====================================================
        # TIMER
        # =====================================================

        timer_text = self.timer_font.render(
            f"SECURITY TIMER: {self.time_left:.1f}s",
            True,
            (255, 210, 60),
        )

        timer_rect = timer_text.get_rect(
            topright=(
                self.room_x + self.room_width - 25,
                self.room_y + 25,
            )
        )

        surface.blit(
            timer_text,
            timer_rect,
        )

        # =====================================================
        # OBJECTIVE
        # =====================================================

        objective_text = self.objective_font.render(
            "Objective: Solve the loop challenge.",
            True,
            (190, 195, 205),
        )

        surface.blit(
            objective_text,
            (
                self.room_x + 25,
                self.room_y + 65,
            ),
        )

        # =====================================================
        # SECURITY SYSTEM HEADING
        # =====================================================

        security_text = self.heading_font.render(
            "LASER SECURITY SYSTEM",
            True,
            (255, 90, 90),
        )

        surface.blit(
            security_text,
            (
                self.room_x + 25,
                self.room_y + 105,
            ),
        )

        # =====================================================
        # LASER TRACK
        # =====================================================

        pygame.draw.rect(
            surface,
            (42, 46, 58),
            (
                self.track_x,
                self.track_y,
                self.track_width,
                self.track_height,
            ),
        )

        pygame.draw.rect(
            surface,
            (65, 68, 80),
            (
                self.track_x,
                self.track_y,
                self.track_width,
                self.track_height,
            ),
            2,
        )

        # Moving laser
        pygame.draw.rect(
            surface,
            (255, 45, 45),
            (
                self.laser_x,
                self.laser_y,
                self.laser_width,
                self.laser_height,
            ),
        )

        # =====================================================
        # SECURITY CODE PANEL
        # =====================================================

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

        # Panel title
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

        # Code lines
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

        # =====================================================
        # QUESTION
        # =====================================================

        if self.current_question:
            question_text = self.current_question["prompt"]

            question_surface = self.option_font.render(
                question_text,
                True,
                (245, 245, 245),
            )

            question_rect = question_surface.get_rect(
                centerx=self.room_x + self.room_width // 2,
                y=415,
            )

            surface.blit(
                question_surface,
                question_rect,
            )

        # =====================================================
        # ANSWERS
        # =====================================================

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
                centerx=self.room_x + self.room_width // 2,
                y=option_y,
            )

            surface.blit(
                option_text,
                option_rect,
            )

            option_y += 27

        # =====================================================
        # PROGRESS
        # =====================================================

        progress_text = self.instruction_font.render(
            f"Progress: {self.current_question_number}"
            f"/{self.total_questions} questions solved",
            True,
            (180, 200, 210),
        )

        progress_rect = progress_text.get_rect(
            center=(
                self.room_x + self.room_width // 2,
                535,
            )
        )

        surface.blit(
            progress_text,
            progress_rect,
        )

        # =====================================================
        # FEEDBACK
        # =====================================================

        if self.feedback:

            if self.complete:
                feedback_color = (60, 230, 110)
            elif "CORRECT" in self.feedback:
                feedback_color = (60, 230, 110)
            else:
                feedback_color = (255, 100, 100)

            feedback_text = self.feedback_font.render(
                self.feedback,
                True,
                feedback_color,
            )

            feedback_rect = feedback_text.get_rect(
                center=(
                    self.room_x + self.room_width // 2,
                    565,
                )
            )

            surface.blit(
                feedback_text,
                feedback_rect,
            )

        # =====================================================
        # INSTRUCTION
        # =====================================================

        instruction_text = self.instruction_font.render(
            "Press 1, 2 or 3 to choose an answer",
            True,
            (180, 180, 190),
        )

        instruction_rect = instruction_text.get_rect(
            center=(
                self.room_x + self.room_width // 2,
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

        # -------------------------
        # Option 1, 2 or 3
        # -------------------------

        if event.key == pygame.K_1:
            selected = 1

        elif event.key == pygame.K_2:
            selected = 2

        elif event.key == pygame.K_3:
            selected = 3

        else:
            return

        self.selected_option = selected

        # Convert option number to list index.
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

            self.current_question_number += 1

            # If all questions are solved, complete the level.
            if self.current_question_number >= self.total_questions:
                self.complete_level()
            else:
                # Load next question.
                self.load_current_question()

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