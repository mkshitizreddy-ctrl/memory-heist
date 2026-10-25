"""
entities/gate.py
Owner: Member 1 - Core Game System

A locked gate that blocks the player until its challenge is solved.
States: locked -> unlocking (short animation) -> open.
Spawns a small spark burst the moment it starts unlocking.
"""

import pygame

from entities.particles import ParticleSystem

LOCKED_COLOR = (200, 60, 60)
UNLOCKING_COLOR = (240, 200, 70)
OPEN_COLOR = (60, 200, 120)
UNLOCK_DURATION = 0.6  # seconds


class Gate:
    def __init__(self, x, y, width=20, height=100):
        self.rect = pygame.Rect(x, y, width, height)
        self.state = "locked"      # "locked" | "unlocking" | "open"
        self._timer = 0.0
        self._particles = ParticleSystem()

    def unlock(self):
        """Start the unlock animation (only works if currently locked)."""
        if self.state == "locked":
            self.state = "unlocking"
            self._timer = UNLOCK_DURATION
            self._particles.spawn(self.rect.centerx, self.rect.centery)

    def is_open(self):
        return self.state == "open"

    def reset(self):
        """Return the gate to its initial locked state."""
        self.state = "locked"
        self._timer = 0.0

    def blocks(self, player_rect):
        """True if the gate is still solid and the player is touching it."""
        return self.state != "open" and self.rect.colliderect(player_rect)

    def update(self, dt):
        if self.state == "unlocking":
            self._timer -= dt
            if self._timer <= 0:
                self.state = "open"
                self._timer = 0.0
        self._particles.update(dt)

    def draw(self, surface):
        if self.state == "open":
            pygame.draw.rect(surface, OPEN_COLOR, self.rect, 2)
            self._particles.draw(surface)
            return

        color = LOCKED_COLOR if self.state == "locked" else UNLOCKING_COLOR
        pygame.draw.rect(surface, color, self.rect)

        if self.state == "unlocking":
            progress = 1 - (self._timer / UNLOCK_DURATION)
            shrink = int(self.rect.height * progress)
            cover = pygame.Rect(self.rect.x, self.rect.y, self.rect.width, shrink)
            pygame.draw.rect(surface, (10, 12, 20), cover)

        self._particles.draw(surface)