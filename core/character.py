"""
core/character.py
Owner: Member 1 - Core Game System

How any character on screen is posed and drawn, shared by the player and the
NPCs so everyone breathes, blinks and bounces the same way.

    image, lift = pose_for(frames, moving, anim_time, idle_time)
    draw_character(surface, rect, image, lift, facing_left)

`frames` is {"idle": surface, "walk": [4 surfaces], "blink": surface}
(blink is optional).
"""

import pygame

from core.animation import scaled

# --- Animation timing (all in seconds / pixels) ----------------------------
WALK_FPS = 8
BOUNCE_PX = 2          # body lifts this much on the passing frames of a walk
BREATH_PERIOD = 1.6    # idle: one full rise and fall
BLINK_PERIOD = 3.4     # idle: eyes close once per period...
BLINK_LENGTH = 0.14    # ...for this long, at the end of it


def blink_closed(idle_time):
    """True while the idle character's eyes are shut."""
    return (idle_time % BLINK_PERIOD) >= BLINK_PERIOD - BLINK_LENGTH


def breath_offset(idle_time):
    """0 or 1 pixel of lift while standing still: a slow, steady breath."""
    return 1 if (idle_time % BREATH_PERIOD) >= BREATH_PERIOD / 2 else 0


def walk_bounce(frame_index):
    """Lift in pixels for a walk frame: up on passing poses, down on steps."""
    return BOUNCE_PX if frame_index % 2 == 1 else 0


def pose_for(frames, moving, anim_time, idle_time):
    """(image, lift): the frame to show and how many pixels to raise it."""
    if moving:
        walk = frames["walk"]
        index = int(anim_time * WALK_FPS) % len(walk)
        return walk[index], walk_bounce(index)
    if blink_closed(idle_time):
        return frames.get("blink", frames["idle"]), 0
    return frames["idle"], breath_offset(idle_time)


RIM_LIGHT = (150, 190, 255, 120)                       # the cool rim that lifts characters off a dark floor


def draw_character(surface, rect, image, lift, facing_left, squash=None):
    """Draw a character at `rect`: shadow first, then the sprite.

    The shadow narrows as the body rises. `squash` is an optional
    core.animation.SquashStretch applied around the character's feet.
    """
    if facing_left:
        image = pygame.transform.flip(image, True, False)

    shadow = pygame.Rect(0, 0, 22 - lift * 2, 8 - lift)
    shadow.midbottom = (rect.centerx, rect.bottom + 2)
    shade = pygame.Surface(shadow.size, pygame.SRCALPHA)
    pygame.draw.ellipse(shade, (0, 0, 0, 90), shade.get_rect())
    surface.blit(shade, shadow)

    x, y = rect.topleft
    if squash is not None and not squash.at_rest:
        image, (ox, oy) = scaled(image, *squash.scale)
        x, y = x + ox, y + oy
    rim = pygame.mask.from_surface(image).to_surface(setcolor=RIM_LIGHT, unsetcolor=(0, 0, 0, 0))
    surface.blit(rim, (x - 1, y - lift - 1))            # a thin lit edge, as if the ceiling lamp were up and left
    surface.blit(image, (x, y - lift))
