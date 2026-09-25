"""
levels/level3_loops.py
Owner: Member 3

Level 3 - The Laser Loop

Topics:
- for loops
- while loops
- range()
- break
"""

import pygame


class Level3LaserLoop:
    """Controls the Laser Loop level."""

    def __init__(self, game=None):
        self.game = game

        # -------------------------
        # Level state
        # -------------------------
        self.complete = False
        self.selected_option = None
        self.feedback = ""

        # -------------------------
        # Security timer (visual)
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
        # Answer options
        # -------------------------
        self.options = [
            "for",
            "while",
            "break",
        ]

        # -------------------------
        # Fonts (created once, not every frame)
        # -------------------------
        self.title_font = pygame.font.Font(None, 34)
        self.timer_font = pygame.font.Font(None, 28)
        self.objective_font = pygame.font.Font(None, 23)
        self.heading_font = pygame.font.Font(None, 26)
        self.code_font = pygame.font.Font(None, 24)
        self.option_font = pygame.font.Font(None, 24)
        self.feedback_font = pygame.font.Font(None, 23)
        self.instruction_font = pygame.font.Font(None, 21)

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, dt):
        """Update the timer and moving laser."""

        # Once completed, freeze the level
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
            # Restart the timer so the player can keep trying
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
            "Objective: Identify the statement that stops the loop.",
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

        panel_x = 270
        panel_y = 275
        panel_width = 420
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
        # ANSWERS
        # =====================================================

        options_heading = self.heading_font.render(
            "SELECT THE CORRECT ANSWER",
            True,
            (245, 245, 245),
        )

        options_heading_rect = options_heading.get_rect(
            center=(
                self.room_x + self.room_width // 2,
                425,
            )
        )

        surface.blit(
            options_heading,
            options_heading_rect,
        )

        # Answer positions
        option_y = 455

        for index, option in enumerate(self.options):

            # Default color
            text_color = (240, 240, 240)

            # Correct answer
            if (
                self.selected_option == index + 1
                and index + 1 == 3
            ):
                text_color = (60, 230, 110)

            # Wrong answer
            elif self.selected_option == index + 1:
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
        # FEEDBACK
        # =====================================================

        if self.feedback:

            if self.complete:
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
                    540,
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
                570,
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

        # Don't allow input after completion
        if self.complete:
            return

        # -------------------------
        # Option 1 (wrong)
        # -------------------------
        if event.key == pygame.K_1:
            self.selected_option = 1
            self.feedback = "INCORRECT! 'for' does not stop the loop."
            if self.game:
                self.game.security.increase(20)
                self.game.score.penalize(10)

        # -------------------------
        # Option 2 (wrong)
        # -------------------------
        elif event.key == pygame.K_2:
            self.selected_option = 2
            self.feedback = "INCORRECT! 'while' creates the loop."
            if self.game:
                self.game.security.increase(20)
                self.game.score.penalize(10)

        # -------------------------
        # Option 3 (correct)
        # -------------------------
        elif event.key == pygame.K_3:
            self.selected_option = 3
            self.feedback = (
                "CORRECT! break stops the loop. "
                "Security bypassed!"
            )
            self.complete = True
            if self.game:
                self.game.score.add(50)
                self.game.score.add(100)   # level completion bonus

    # =========================================================
    # COMPLETION
    # =========================================================

    def is_complete(self):
        """Return True when the level is complete."""
        return self.complete