"""
core/map_manager.py
Owner: Member 1 - Core Game System

Rooms with walls and gates, plus a RoomMap that connects rooms with exits.
Levels build their layouts from these.
"""

import pygame

WALL_COLOR = (60, 70, 100)
FLOOR_COLOR = (18, 22, 36)


class Room:
    def __init__(self, name, bounds, walls=None, gates=None):
        self.name = name
        self.bounds = pygame.Rect(bounds)
        self.walls = [pygame.Rect(w) for w in (walls or [])]
        self.gates = gates or []          # list of entities.gate.Gate

    def update(self, dt):
        for gate in self.gates:
            gate.update(dt)

    def blocked(self, rect):
        """True if rect hits a wall or a gate that is not open."""
        if any(rect.colliderect(w) for w in self.walls):
            return True
        return any(g.blocks(rect) for g in self.gates)

    def draw(self, surface):
        pygame.draw.rect(surface, FLOOR_COLOR, self.bounds)
        for wall in self.walls:
            pygame.draw.rect(surface, WALL_COLOR, wall)
        for gate in self.gates:
            gate.draw(surface)
        pygame.draw.rect(surface, WALL_COLOR, self.bounds, 3)


class RoomMap:
    """Holds several rooms and tracks which one the player is in.

    exits is a list of (from_room, trigger_rect, to_room, spawn_pos).
    Keep each spawn_pos outside the destination room's own exit
    triggers, otherwise the player bounces straight back.
    """

    def __init__(self, rooms, exits=None):
        self.rooms = {r.name: r for r in rooms}
        self.current_name = rooms[0].name
        self.exits = [
            (src, pygame.Rect(trigger), dest, spawn)
            for src, trigger, dest, spawn in (exits or [])
        ]

    @property
    def current(self):
        return self.rooms[self.current_name]

    def update(self, dt):
        self.current.update(dt)

    def check_exit(self, player_rect):
        """Switch rooms if the player touches an exit. Returns True on a switch."""
        for src, trigger, dest, spawn in self.exits:
            if src == self.current_name and player_rect.colliderect(trigger):
                self.current_name = dest
                player_rect.topleft = spawn
                return True
        return False

    def draw(self, surface):
        self.current.draw(surface)