"""
core/player.py
Owner: Member 1 - Core Game System

Player position, movement (WASD or arrow keys), and collision response.
"""

import pygame

WASD = {
    "left": pygame.K_a,
    "right": pygame.K_d,
    "up": pygame.K_w,
    "down": pygame.K_s,
}

ARROWS = {
    "left": pygame.K_LEFT,
    "right": pygame.K_RIGHT,
    "up": pygame.K_UP,
    "down": pygame.K_DOWN,
}


class Player:
    def __init__(self, x, y, speed=200, controls=None, color=(0, 200, 255)):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.speed = speed
        self.controls = controls or WASD
        self.color = color

    def reset_position(self, x, y):
        """Reset the player to the given position."""
        self.rect.topleft = (x, y)

    def handle_input(self, keys, dt, blocked=None):
        dx = dy = 0

        if keys[self.controls["left"]]:
            dx -= 1
        if keys[self.controls["right"]]:
            dx += 1
        if keys[self.controls["up"]]:
            dy -= 1
        if keys[self.controls["down"]]:
            dy += 1

        if dx != 0 and dy != 0:
            dx *= 0.7071
            dy *= 0.7071

        # Move horizontally and resolve collision.
        move_x = int(dx * self.speed * dt)
        self.rect.x += move_x

        if blocked and blocked(self.rect):
            self.rect.x -= move_x

        # Move vertically and resolve collision.
        move_y = int(dy * self.speed * dt)
        self.rect.y += move_y

        if blocked and blocked(self.rect):
            self.rect.y -= move_y

    def draw(self, surface):
        pygame.draw.rect(
            surface,
            self.color,
            self.rect
        )