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

    def __init__(self):
        # Level state
        self.complete = False
        self.failed = False

        # Answer selection and feedback
        self.selected_option = None
        self.feedback = ""

        # Challenge timer
        self.time_limit = 20.0
        self.time_left = self.time_limit

        # Laser movement
        self.laser_x = 100
        self.laser_speed = 200
        self.laser_direction = 1

        # Laser settings
        self.laser_y = 275
        self.laser_width = 140
        self.laser_height = 12

        # Room boundaries
        self.room_x = 50
        self.room_y = 40
        self.room_width = 760
        self.room_height = 540

        # Code shown to the player
        self.code_lines = [
            "while True:",
            "    if laser_detected:",
            "        break",
        ]

        # Answer options
        self.options = [
            "for",
            "while",
            "break",
        ]

    def update(self, dt):
        """Update the timer and moving laser."""

        # Stop updating after the level is finished
        if self.complete or self.failed:
            return

        # Countdown
        self.time_left -= dt

        # Time runs out
        if self.time_left <= 0:
            self.time_left = 0
            self.failed = True
            self.feedback = "TIME UP! Security system activated."
            return

        # Move laser
        self.laser_x += (
            self.laser_speed
            * self.laser_direction
            * dt
        )

        # Reverse direction at boundaries
        if self.laser_x <= self.room_x:
            self.laser_x = self.room_x
            self.laser_direction = 1

        elif (
            self.laser_x + self.laser_width
            >= self.room_x + self.room_width
        ):
            self.laser_x = (
                self.room_x
                + self.room_width
                - self.laser_width
            )
            self.laser_direction = -1

    def render(self, surface):
        """Draw the Level 3 room, laser, puzzle and HUD."""

        # Fonts
        title_font = pygame.font.Font(None, 36)
        heading_font = pygame.font.Font(None, 28)
        code_font = pygame.font.Font(None, 25)
        option_font = pygame.font.Font(None, 26)
        small_font = pygame.font.Font(None, 22)
        feedback_font = pygame.font.Font(None, 25)

        # Room
        pygame.draw.rect(
            surface,
            (25, 30, 45),
            (
                self.room_x,
                self.room_y,
                self.room_width,
                self.room_height,
            ),
        )

        pygame.draw.rect(
            surface,
            (120, 40, 40),
            (
                self.room_x,
                self.room_y,
                self.room_width,
                self.room_height,
            ),
            3,
        )

        # Title
        title_text = title_font.render(
            "LEVEL 3 - THE LASER LOOP",
            True,
            (255, 255, 255),
        )

        surface.blit(
            title_text,
            (self.room_x + 20, self.room_y + 15),
        )

        # Timer
        timer_text = heading_font.render(
            f"SECURITY TIMER: {self.time_left:.1f}s",
            True,
            (255, 220, 100),
        )

        surface.blit(
            timer_text,
            (self.room_x + 500, self.room_y + 20),
        )

        # Objective
        objective_text = small_font.render(
            "Objective: Identify the statement that stops the loop.",
            True,
            (190, 200, 210),
        )

        surface.blit(
            objective_text,
            (self.room_x + 20, self.room_y + 60),
        )

        # Laser warning area
        warning_text = small_font.render(
            "LASER SECURITY SYSTEM",
            True,
            (255, 100, 100),
        )

        surface.blit(
            warning_text,
            (self.room_x + 20, self.room_y + 100),
        )

        # Laser track
        pygame.draw.rect(
            surface,
            (60, 60, 70),
            (
                self.room_x + 20,
                self.laser_y - 8,
                self.room_width - 40,
                self.laser_height + 16,
            ),
            2,
        )

        # Moving laser
        pygame.draw.rect(
            surface,
            (255, 40, 40),
            (
                self.laser_x,
                self.laser_y,
                self.laser_width,
                self.laser_height,
            ),
        )

        # Security code panel
        panel_x = self.room_x + 210
        panel_y = self.room_y + 300
        panel_width = 500
        panel_height = 115

        pygame.draw.rect(
            surface,
            (15, 18, 28),
            (
                panel_x,
                panel_y,
                panel_width,
                panel_height,
            ),
        )

        pygame.draw.rect(
            surface,
            (70, 100, 130),
            (
                panel_x,
                panel_y,
                panel_width,
                panel_height,
            ),
            2,
        )

        # Panel heading
        heading_text = heading_font.render(
            "SECURITY CODE",
            True,
            (255, 255, 255),
        )

        surface.blit(
            heading_text,
            (panel_x + 20, panel_y + 12),
        )

        # Code
        y = panel_y + 45

        for line in self.code_lines:
            code_text = code_font.render(
                line,
                True,
                (100, 220, 255),
            )

            surface.blit(
                code_text,
                (panel_x + 25, y),
            )

            y += 25

        # Answer section
        answer_heading = heading_font.render(
            "SELECT THE CORRECT ANSWER",
            True,
            (255, 255, 255),
        )

        surface.blit(
            answer_heading,
            (self.room_x + 250, self.room_y + 430),
        )

        # Options
        option_y = self.room_y + 465

        for index, option in enumerate(self.options):
            text_color = (255, 255, 255)

            # Highlight selected option
            if self.selected_option == index + 1:
                text_color = (100, 255, 150)

            option_text = option_font.render(
                f"[{index + 1}]  {option}",
                True,
                text_color,
            )

            surface.blit(
                option_text,
                (self.room_x + 270, option_y),
            )

            option_y += 30

        # Feedback
        if self.feedback:
            feedback_text = feedback_font.render(
                self.feedback,
                True,
                (255, 255, 255),
            )

            surface.blit(
                feedback_text,
                (self.room_x + 180, self.room_y + 555),
            )

    def handle_event(self, event):
        """Handle keyboard input for the Level 3 puzzle."""

        if event.type != pygame.KEYDOWN:
            return

        # Don't accept answers after success/failure
        if self.complete or self.failed:
            return

        # Option 1
        if event.key == pygame.K_1:
            self.selected_option = 1
            self.feedback = "Incorrect. Try again."

        # Option 2
        elif event.key == pygame.K_2:
            self.selected_option = 2
            self.feedback = "Incorrect. Try again."

        # Option 3
        elif event.key == pygame.K_3:
            self.selected_option = 3
            self.feedback = (
                "CORRECT! break stops the loop. "
                "Security bypassed!"
            )
            self.complete = True

    def is_complete(self):
        """Return True when the player has solved the level."""

        return self.complete