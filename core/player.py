"""
core/player.py
Owner: Member 1 - Core Game System

Player position, movement (WASD or arrow keys), and collision response.
"""

import pygame

from core.animation import SquashStretch, scaled
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


# --- Animation timing (all in seconds / pixels) ----------------------------
WALK_FPS = 8
BOUNCE_PX = 2          # body lifts this much on the passing frames of a walk
BREATH_PERIOD = 1.6    # idle: one full rise and fall
BLINK_PERIOD = 3.4     # idle: eyes close once per period...
BLINK_LENGTH = 0.14    # ...for this long, at the end of it
START_STRETCH = 0.16   # springy pop when a step begins
STOP_SQUASH = -0.2     # and a little settle when it ends


def blink_closed(idle_time):
    """True while the idle character's eyes are shut."""
    return (idle_time % BLINK_PERIOD) >= BLINK_PERIOD - BLINK_LENGTH


def breath_offset(idle_time):
    """0 or 1 pixel of lift while standing still: a slow, steady breath."""
    return 1 if (idle_time % BREATH_PERIOD) >= BREATH_PERIOD / 2 else 0


def walk_bounce(frame_index):
    """Lift in pixels for a walk frame: up on passing poses, down on steps."""
    return BOUNCE_PX if frame_index % 2 == 1 else 0


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
        if self.moving:
            walk = self.frames["walk"]
            index = int(self.anim_time * WALK_FPS) % len(walk)
            return walk[index], walk_bounce(index)
        if blink_closed(self.idle_time):
            return self.frames.get("blink", self.frames["idle"]), 0
        return self.frames["idle"], breath_offset(self.idle_time)

    def draw(self, surface):
        image, lift = self.current_pose()

        if self.facing_left:
            image = pygame.transform.flip(image, True, False)

        # Soft shadow under the feet; it narrows as the body rises.
        shadow = pygame.Rect(0, 0, 22 - lift * 2, 8 - lift)
        shadow.midbottom = (self.rect.centerx, self.rect.bottom + 2)
        shade = pygame.Surface(shadow.size, pygame.SRCALPHA)
        pygame.draw.ellipse(shade, (0, 0, 0, 90), shade.get_rect())
        surface.blit(shade, shadow)

        x, y = self.rect.topleft
        if not self.squash.at_rest:
            image, (ox, oy) = scaled(image, *self.squash.scale)
            x, y = x + ox, y + oy
        surface.blit(image, (x, y - lift))
