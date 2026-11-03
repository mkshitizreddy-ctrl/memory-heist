"""
levels/room_base.py
Owner: Member 1 - Core Game System

The plumbing every walkable level needs, so each new floor only has to say what
is different about it:

    class MyFloor(RoomMixin):
        def __init__(self, player=None, game=None, seed=None):
            ...
            self.init_room(seed)             # rng, message line, shake, dust, sparks
        def update(self, dt):
            self.update_room(dt)             # clock, shake, sparks, dust, footsteps
        def render(self, surface):
            world = ...                      # draw the floor
            self.draw_dust(world, floor_colour)
            self.draw_sparks(world)
            self.draw_message(world, "E: do the thing")
            self.present(surface, world)     # shake, then onto the screen

The contract with Game is unchanged: update / render / handle_event /
is_complete, plus a `room_map` with `blocked(rect)` so Game can move the players.
"""

import math
import random

import pygame

from core.animation import Shake
from core.tilemap import TILE
from ui import theme
from ui.kit import shadowed

REACH = 52                      # how close counts as "next to" something
STEP_EVERY = 0.32               # seconds between footstep sounds
DUST_EVERY = 0.12               # seconds between footstep puffs while walking
DUST_LIFE = 0.45
SPARK_LIFE = 0.6
TITLE_Y = 48                    # text on the wall band, between the HUD and the floor
MESSAGE_Y = 74


class RoomMap:
    """What Game asks for: blocked(rect). Walls plus solid props."""

    def __init__(self, tilemap, props):
        self.tilemap = tilemap
        self.props = props

    def blocked(self, rect):
        return self.tilemap.collides(rect) or any(rect.colliderect(p) for p in self.props)


class RoomMixin:
    def init_room(self, seed=None):
        self.rng = random.Random(seed)
        self.message = ""
        self.message_tone = theme.PAPER
        self.shake = Shake(max_offset=8, seed=7)
        self.sparks = []
        self.dust = []
        self.time = 0.0
        self._step_clock = {}
        self._dust_clock = {}

    # --- who is playing ---------------------------------------------------
    def players(self):
        """[(player, interact key)] for one player, or two in co-op."""
        out = []
        if getattr(self, "player", None) is not None:
            out.append((self.player, pygame.K_e))
        game = getattr(self, "game", None)
        if game is not None and getattr(game, "coop", False) and getattr(game, "player2", None):
            out.append((game.player2, pygame.K_RSHIFT))
        return out

    @staticmethod
    def near(player, rect, reach=REACH):
        return pygame.Rect(rect).inflate(reach, reach).colliderect(player.rect)

    # --- feedback ---------------------------------------------------------
    def sfx(self, name):
        """Play a sound effect if the game has audio (tests and previews may not)."""
        audio = getattr(getattr(self, "game", None), "audio", None)
        if audio is not None:
            audio.play(name)

    def say(self, text, tone=theme.PAPER):
        self.message, self.message_tone = text, tone

    def burst(self, pos, colour, count):
        for _ in range(count):
            ang = self.rng.uniform(0, math.tau)
            speed = self.rng.uniform(50, 150)
            self.sparks.append({"x": pos[0], "y": pos[1], "colour": colour, "life": SPARK_LIFE,
                                "vx": math.cos(ang) * speed, "vy": math.sin(ang) * speed - 40})

    # --- per frame --------------------------------------------------------
    def update_room(self, dt):
        dt = max(0.0, dt)
        self.time += dt
        self.shake.update(dt)
        for s in self.sparks:
            s["x"] += s["vx"] * dt
            s["y"] += s["vy"] * dt
            s["vy"] += 260 * dt
            s["life"] -= dt
        self.sparks = [s for s in self.sparks if s["life"] > 0]
        self._update_dust(dt)
        self._update_steps(dt)

    def _update_steps(self, dt):
        for player, _ in self.players():
            clock = self._step_clock.get(id(player), 0.0)
            if getattr(player, "moving", False):
                clock += dt
                if clock >= STEP_EVERY:
                    clock = 0.0
                    self.sfx("step")
            else:
                clock = STEP_EVERY * 0.6      # the first step after standing still is quick
            self._step_clock[id(player)] = clock

    def _update_dust(self, dt):
        for puff in self.dust:
            puff["age"] += dt
            puff["y"] -= 14 * dt
        self.dust = [p for p in self.dust if p["age"] < DUST_LIFE]
        for player, _ in self.players():
            clock = self._dust_clock.get(id(player), 0.0)
            if getattr(player, "moving", False):
                clock += dt
                if clock >= DUST_EVERY:
                    clock = 0.0
                    self.dust.append({"x": player.rect.centerx + self.rng.uniform(-6, 6),
                                      "y": player.rect.bottom - 2, "age": 0.0})
            else:
                clock = 0.0
            self._dust_clock[id(player)] = clock

    # --- drawing ----------------------------------------------------------
    def draw_dust(self, world, floor_colour):
        for puff in self.dust:
            k = puff["age"] / DUST_LIFE
            tint = theme.mix(theme.MIST, floor_colour, k)
            pygame.draw.circle(world, tint, (int(puff["x"]), int(puff["y"])), 2 + int(4 * k))

    def draw_sparks(self, world):
        for s in self.sparks:
            size = max(1, int(4 * s["life"] / SPARK_LIFE))
            pygame.draw.circle(world, s["colour"], (int(s["x"]), int(s["y"])), size)

    def draw_message(self, world, hint, font, hint_font):
        """The message line on the wall band, and a key hint at its right."""
        if self.message:
            msg = shadowed(font, self.message, self.message_tone)
            world.blit(msg, (TILE * 2, MESSAGE_Y))
        tip = shadowed(hint_font, hint, theme.MIST)
        world.blit(tip, (world.get_width() - tip.get_width() - TILE * 2, TITLE_Y + 2))

    def present(self, surface, world):
        ox, oy = self.shake.offset()
        surface.fill(theme.INK)
        surface.blit(world, (ox, oy))
