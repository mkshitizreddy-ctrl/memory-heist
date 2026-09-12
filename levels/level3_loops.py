"""
Level 3 - The Laser Loop
Owner: Member 3

Topics: for loops, while loops, range(), break
"""

import pygame


class Level3LaserLoop:
    """Controls the Laser Loop level."""

    def __init__(self):
        self.complete = False

    def update(self, dt):
        """Update the level state."""

    def render(self, surface):
        """Draw the Level 3 room."""
        pygame.draw.rect(surface, (30, 30, 50), (40, 40, 880, 560))
        pygame.draw.rect(surface, (200, 50, 50), (100, 180, 700, 10))

    def handle_event(self, event):
        """Handle keyboard and other Pygame events."""

    def is_complete(self):
        """Return whether the level has been completed."""
        return self.complete