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

    def handle_input(self, keys, dt):
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
            dx *= 0.7071  # 1/sqrt(2), keeps diagonal speed equal to straight-line speed
            dy *= 0.7071
        self.rect.x += dx * self.speed * dt
        self.rect.y += dy * self.speed * dt

    def draw(self, surface):
        pygame.draw.rect(surface, (0, 200, 255), self.rect)
