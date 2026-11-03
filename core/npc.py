"""
core/npc.py
Owner: Member 1 - Core Game System

A person who lives in a level: stands, patrols a route, notices the player and
says things. Drawn with the same pose and shadow code as the player, so every
character in the building breathes, blinks and walks alike.

    guard = NPC("guard", (608, 512), patrol=[(608, 512), (800, 512)])
    guard.update(dt)
    guard.notice(player.rect, key="p1")     # True once, as the player comes close
    guard.say("Move along.")
    guard.draw(surface, font)               # font is only needed for speech

NPCs are decoration with manners: they never block the player and never change
the score or the security meter.
"""

import math

import pygame

from core.character import draw_character, pose_for
from core.npc_sprites import make_npc_frames
from ui.kit import draw_speech_bubble

SIZE = 32
DEFAULT_SPEED = 48.0        # pixels per second: a calm walk
DEFAULT_PAUSE = 1.2         # seconds spent at each end of a patrol
NOTICE_RANGE = 96           # how close the player must come to be noticed
NOTICE_HYSTERESIS = 24      # and how far they must go before they can be noticed again
SPEECH_SECONDS = 2.6


class NPC:
    def __init__(self, kind, pos, patrol=None, speed=DEFAULT_SPEED, pause=DEFAULT_PAUSE,
                 facing_left=False, notice_range=NOTICE_RANGE):
        self.kind = kind
        self.frames = make_npc_frames(kind)
        self.speed = speed
        self.pause = pause
        self.notice_range = notice_range
        self.facing_left = facing_left
        self.moving = False
        self.anim_time = 0.0
        self.idle_time = 0.0

        self.route = []
        if patrol:
            waypoints = [tuple(p) for p in patrol]
            pos = waypoints[0]                       # a patrol starts at its first point
            # Out and back: A B C becomes A B C B, repeated.
            self.route = waypoints + waypoints[-2:0:-1] if len(waypoints) > 1 else []
        self._x, self._y = float(pos[0]), float(pos[1])
        self.rect = pygame.Rect(round(self._x), round(self._y), SIZE, SIZE)
        self._target = 1 if self.route else 0
        self._wait = 0.0                              # pause left at a waypoint
        self._alert = 0.0                             # time left looking at the player
        self._noticed = set()
        self.speech = None
        self.said = 0                                 # lines spoken so far (voices watch this)
        self._speech_left = 0.0

    # --- behaviour --------------------------------------------------------
    def face(self, point):
        """Turn to look at a point (an (x, y) pair or a Rect)."""
        x = point.centerx if isinstance(point, pygame.Rect) else point[0]
        if x != self.rect.centerx:
            self.facing_left = x < self.rect.centerx

    def say(self, text, seconds=SPEECH_SECONDS):
        self.speech, self._speech_left = text, seconds
        self.said += 1

    def alert(self, point, seconds=1.5):
        """Stop and look at something for a moment."""
        self.face(point)
        self._alert = max(self._alert, seconds)

    def notice(self, target_rect, key):
        """True the moment `target_rect` first comes within range, not while it stays.

        `key` tells targets apart (player 1, player 2). The NPC turns to look.
        """
        d = math.dist(self.rect.center, target_rect.center)
        if d <= self.notice_range:
            if key in self._noticed:
                return False
            self._noticed.add(key)
            self.face(target_rect)
            return True
        if d > self.notice_range + NOTICE_HYSTERESIS:
            self._noticed.discard(key)
        return False

    # --- per-frame --------------------------------------------------------
    def update(self, dt):
        dt = max(0.0, dt)
        if self.speech is not None:
            self._speech_left -= dt
            if self._speech_left <= 0:
                self.speech = None

        moved = False
        if self._alert > 0:
            self._alert = max(0.0, self._alert - dt)
        elif self._wait > 0:
            self._wait = max(0.0, self._wait - dt)
        elif self.route:
            moved = self._walk(dt)

        self.moving = moved
        if moved:
            self.anim_time += dt
            self.idle_time = 0.0
        else:
            self.idle_time += dt
        self.rect.topleft = (round(self._x), round(self._y))

    def _walk(self, dt):
        tx, ty = self.route[self._target]
        dx, dy = tx - self._x, ty - self._y
        dist = math.hypot(dx, dy)
        if dist == 0:
            self._arrive()
            return False
        if dx:
            self.facing_left = dx < 0
        step = self.speed * dt
        if step >= dist:                  # arrive exactly; never overshoot on a lag spike
            self._x, self._y = float(tx), float(ty)
            self._arrive()
        else:
            self._x += dx / dist * step
            self._y += dy / dist * step
        return True

    def _arrive(self):
        self._target = (self._target + 1) % len(self.route)
        self._wait = self.pause

    # --- drawing ----------------------------------------------------------
    def draw(self, surface, font=None):
        image, lift = pose_for(self.frames, self.moving, self.anim_time, self.idle_time)
        draw_character(surface, self.rect, image, lift, self.facing_left)
        if self.speech and font is not None:
            draw_speech_bubble(surface, font, self.speech, self.rect)
