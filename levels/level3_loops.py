"""
levels/level3_loops.py
Owner: Member 3

Level 3 - The Laser Loop
Topics: for loops, while loops, range(), break
"""

import pygame


class Level3LaserLoop:
    """Controls the Laser Loop level."""

    def __init__(self):
        # Level completion
        self.complete = False

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

        # Answer choices
        self.options = [
            "for",
            "while",
            "break",
        ]

        # Font
        self.font = pygame.font.Font(None, 28)

    def update(self, dt):
        """Update the laser movement."""

        # Move the laser horizontally.
        self.laser_x += self.laser_speed * self.laser_direction * dt

        # Right boundary
        if self.laser_x + self.laser_width >= (
            self.room_x + self.room_width
        ):
            self.laser_x = (
                self.room_x + self.room_width - self.laser_width
            )
            self.laser_direction = -1

        # Left boundary
        elif self.laser_x <= self.room_x:
            self.laser_x = self.room_x
            self.laser_direction = 1

    def render(self, surface):
        """Draw the Level 3 room, laser, code and options."""

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

        # Laser
        pygame.draw.rect(
            surface,
            (255, 50, 50),
            (
                self.laser_x,
                self.laser_y,
                self.laser_width,
                self.laser_height,
            ),
        )

        # Level title
        title = self.font.render(
            "LEVEL 3 - THE LASER LOOP",
            True,
            (255, 255, 255),
        )
        surface.blit(title, (80, 75))

        # Code section
        code_title = self.font.render(
            "Security Code:",
            True,
            (255, 255, 255),
        )
        surface.blit(code_title, (250, 170))

        y = 210

        for line in self.code_lines:
            code_text = self.font.render(
                line,
                True,
                (100, 220, 255),
            )
            surface.blit(code_text, (300, y))
            y += 30

        # Options
        option_title = self.font.render(
            "Choose the correct concept:",
            True,
            (255, 255, 255),
        )
        surface.blit(option_title, (250, 460))

        option_y = 500

        for index, option in enumerate(self.options):
            option_text = self.font.render(
                f"{index + 1}. {option}",
                True,
                (255, 255, 255),
            )
            surface.blit(option_text, (250, option_y))
            option_y += 30

        # Temporary instruction
        instruction = self.font.render(
            "Press SPACE to complete the level",
            True,
            (180, 180, 180),
        )
        surface.blit(instruction, (250, 600))

    def handle_event(self, event):
        """Handle keyboard input for the Level 3 puzzle."""

        if event.type == pygame.KEYDOWN:

           if event.key == pygame.K_1:
              self.selected_option = 1
              self.feedback = "Wrong! Try again."

           elif event.key == pygame.K_2:
              self.selected_option = 2
              self.feedback = "Wrong! Try again."

           elif event.key == pygame.K_3:
              self.selected_option = 3
              self.feedback = "Correct! The break statement stops the loop."
              self.complete = True

    def is_complete(self):
        """Return True when the level is complete."""

        return self.complete