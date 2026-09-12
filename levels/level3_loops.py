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
        # Level completion
        self.complete = False

        # Answer selection and feedback
        self.selected_option = None
        self.feedback = ""

        # Laser movement
        self.laser_x = 100
        self.laser_speed = 200
        self.laser_direction = 1

        # Laser settings
        self.laser_y = 350
        self.laser_width = 120
        self.laser_height = 12

        # Room boundaries
        self.room_x = 50
        self.room_y = 50
        self.room_width = 760
        self.room_height = 500

        # Code shown to the player
        self.code_lines = [
            "for i in range(5):",
            "    print(i)",
            "",
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
        """Update the moving laser."""

        # Move laser
        self.laser_x += (
            self.laser_speed
            * self.laser_direction
            * dt
        )

        # Reverse direction when laser reaches the room boundaries
        if self.laser_x <= self.room_x:
            self.laser_direction = 1

        elif (
            self.laser_x + self.laser_width
            >= self.room_x + self.room_width
        ):
            self.laser_direction = -1

    def render(self, surface):
        """Draw the Level 3 room, laser, code and options."""

        # Fonts
        title_font = pygame.font.Font(None, 32)
        heading_font = pygame.font.Font(None, 28)
        code_font = pygame.font.Font(None, 26)
        option_font = pygame.font.Font(None, 26)
        feedback_font = pygame.font.Font(None, 24)

        # Room border
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
            (self.room_x + 20, self.room_y + 20),
        )

        # Security Code heading
        heading_text = heading_font.render(
            "Security Code:",
            True,
            (255, 255, 255),
        )

        surface.blit(
            heading_text,
            (self.room_x + 250, self.room_y + 110),
        )

        # Draw code
        y = self.room_y + 150

        for line in self.code_lines:
            code_text = code_font.render(
                line,
                True,
                (100, 220, 255),
            )

            surface.blit(
                code_text,
                (self.room_x + 250, y),
            )

            y += 30

        # Draw moving laser
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

        # Options heading
        options_heading = heading_font.render(
            "Choose the correct concept:",
            True,
            (255, 255, 255),
        )

        surface.blit(
            options_heading,
            (self.room_x + 250, self.room_y + 310),
        )

        # Draw options
        option_y = self.room_y + 345

        for index, option in enumerate(self.options):
            option_text = option_font.render(
                f"{index + 1}. {option}",
                True,
                (255, 255, 255),
            )

            surface.blit(
                option_text,
                (self.room_x + 250, option_y),
            )

            option_y += 30

        # Display feedback
        if self.feedback:
            feedback_text = feedback_font.render(
                self.feedback,
                True,
                (255, 255, 255),
            )

            surface.blit(
                feedback_text,
                (self.room_x + 180, self.room_y + 445),
            )

        # Instruction
        instruction_text = option_font.render(
            "Press 1, 2 or 3 to choose an answer",
            True,
            (180, 180, 180),
        )

        surface.blit(
            instruction_text,
            (self.room_x + 220, self.room_y + 475),
        )

    def handle_event(self, event):
        """Handle keyboard input for the Level 3 puzzle."""

        if event.type == pygame.KEYDOWN:

            # Option 1
            if event.key == pygame.K_1:
                self.selected_option = 1
                self.feedback = "Wrong! Try again."

            # Option 2
            elif event.key == pygame.K_2:
                self.selected_option = 2
                self.feedback = "Wrong! Try again."

            # Option 3
            elif event.key == pygame.K_3:
                self.selected_option = 3
                self.feedback = (
                    "Correct! The break statement stops the loop."
                )
                self.complete = True

    def is_complete(self):
        """Return True when the level is complete."""

        return self.complete