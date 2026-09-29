"""
core/player.py
Owner: Member 1 - Core Game System

Player position, movement (WASD), and collision response.
"""

import pygame


class Player:
    def __init__(self, x, y, speed=200):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.speed = speed

    def handle_input(self, keys, dt, blocked=None):
        dx = dy = 0

        if keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_d]:
            dx += 1
        if keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_s]:
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
        pygame.draw.rect(surface, (0, 200, 255), self.rect)