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
        self.gates = gates or []

    def update(self, dt):
        for gate in self.gates:
            gate.update(dt)

    def blocked(self, rect):
        """Return True if rect hits a wall or a closed gate."""
        if any(rect.colliderect(wall) for wall in self.walls):
            return True

        return any(gate.blocks(rect) for gate in self.gates)

    def draw(self, surface):
        pygame.draw.rect(surface, FLOOR_COLOR, self.bounds)

        for wall in self.walls:
            pygame.draw.rect(surface, WALL_COLOR, wall)

        for gate in self.gates:
            gate.draw(surface)

        pygame.draw.rect(surface, WALL_COLOR, self.bounds, 3)


class RoomMap:
    """Holds several rooms and tracks the player's current room.

    exits is a list of:
        (from_room, trigger_rect, to_room, spawn_pos)

    Each spawn position should be outside the destination room's
    exit trigger to prevent immediate bouncing back.
    """

    def __init__(self, rooms, exits=None):
        self.rooms = {room.name: room for room in rooms}
        self.current_name = rooms[0].name

        self.exits = [
            (
                source,
                pygame.Rect(trigger),
                destination,
                spawn,
            )
            for source, trigger, destination, spawn
            in (exits or [])
        ]

    @property
    def current(self):
        """Return the room currently occupied by the player."""
        return self.rooms[self.current_name]

    def update(self, dt):
        """Update the active room and its gates."""
        self.current.update(dt)

    def blocked(self, rect):
        """Return True when the active room blocks the given rectangle.

        This is the public collision interface used by Core.
        Core does not need to know how rooms implement their
        individual walls and gates.
        """
        return self.current.blocked(rect)

    def check_exit(self, player_rect):
        """Switch rooms if the player touches an active exit.

        Returns True when a room transition occurs.
        """
        for source, trigger, destination, spawn in self.exits:
            if (
                source == self.current_name
                and player_rect.colliderect(trigger)
            ):
                self.current_name = destination
                player_rect.topleft = spawn
                return True

        return False

    def draw(self, surface):
        """Draw the currently active room."""
        self.current.draw(surface)