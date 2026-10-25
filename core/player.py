"""
core/player.py
Owner: Member 1 - Core Game System

Player position, movement (WASD or arrow keys), and collision response.
"""

import pygame

from entities.sprites import make_player_frames

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
    def __init__(self, x, y, speed=200, controls=None, palette="cyan"):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.speed = speed
        self.controls = controls or WASD
        self.frames = make_player_frames(palette)
        self.facing_left = False
        self.moving = False
        self.anim_time = 0.0

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

        self.moving = dx != 0 or dy != 0
        if dx < 0:
            self.facing_left = True
        elif dx > 0:
            self.facing_left = False
        if self.moving:
            self.anim_time += dt

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
        if self.moving:
            walk = self.frames["walk"]
            image = walk[int(self.anim_time * 8) % len(walk)]
        else:
            image = self.frames["idle"]

        if self.facing_left:
            image = pygame.transform.flip(image, True, False)

        # Soft shadow under the feet.
        shadow = pygame.Rect(0, 0, 22, 8)
        shadow.midbottom = (self.rect.centerx, self.rect.bottom + 2)
        shade = pygame.Surface(shadow.size, pygame.SRCALPHA)
        pygame.draw.ellipse(shade, (0, 0, 0, 90), shade.get_rect())
        surface.blit(shade, shadow)

        surface.blit(image, self.rect.topleft)
