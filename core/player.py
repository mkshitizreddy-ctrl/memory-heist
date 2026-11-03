"""
core/player.py
Owner: Member 1 - Core Game System

Player position, movement (WASD or arrow keys), and collision response.
"""

import pygame

from core.animation import SquashStretch
from core.character import (  # noqa: F401  (timing names are re-exported)
    BLINK_LENGTH, BLINK_PERIOD, BOUNCE_PX, BREATH_PERIOD, WALK_FPS,
    blink_closed, breath_offset, draw_character, pose_for, walk_bounce)
from core.hero_sprites import HEROES, make_hero_frames
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


START_STRETCH = 0.16   # springy pop when a step begins
STOP_SQUASH = -0.2     # and a little settle when it ends


class Player:
    def __init__(self, x, y, speed=200, controls=None, palette="cyan"):
        self.rect = pygame.Rect(x, y, 32, 32)
        self.speed = speed
        self.controls = controls or WASD
        # 'ghost' / 'echo' are the story heroes; older palette names still work.
        if palette in HEROES:
            self.frames = make_hero_frames(palette)
        else:
            self.frames = make_player_frames(palette)
        self.facing_left = False
        self.moving = False
        self.anim_time = 0.0
        self.idle_time = 0.0
        self.squash = SquashStretch()
        self._was_moving = False
        # Sub-pixel part of a step that did not fit in a whole pixel.
        self._remainder_x = 0.0
        self._remainder_y = 0.0

    def reset_position(self, x, y):
        """Reset the player to the given position."""
        self.rect.topleft = (x, y)
        self._remainder_x = 0.0
        self._remainder_y = 0.0

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
        self._animate(dt)
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
        if dx == 0:
            self._remainder_x = 0.0
        self._remainder_x += dx * self.speed * dt
        move_x = int(self._remainder_x)
        self._remainder_x -= move_x
        self.rect.x += move_x

        if blocked and blocked(self.rect):
            self.rect.x -= move_x
            self._remainder_x = 0.0

        # Move vertically and resolve collision.
        if dy == 0:
            self._remainder_y = 0.0
        self._remainder_y += dy * self.speed * dt
        move_y = int(self._remainder_y)
        self._remainder_y -= move_y
        self.rect.y += move_y

        if blocked and blocked(self.rect):
            self.rect.y -= move_y
            self._remainder_y = 0.0

    def _animate(self, dt):
        """Advance idle time and fire the squash when walking starts or stops."""
        if self.moving:
            self.idle_time = 0.0
            if not self._was_moving:
                self.squash.trigger(START_STRETCH)
        else:
            self.idle_time += dt
            if self._was_moving:
                self.squash.trigger(STOP_SQUASH)
        self._was_moving = self.moving
        self.squash.update(dt)

    def current_pose(self):
        """(image, lift): the frame to show and how many pixels to raise it."""
        return pose_for(self.frames, self.moving, self.anim_time, self.idle_time)

    def draw(self, surface):
        image, lift = self.current_pose()
        draw_character(surface, self.rect, image, lift, self.facing_left, self.squash)
