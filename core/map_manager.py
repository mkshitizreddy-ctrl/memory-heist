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
        """Return True if rect is outside the room or hits an obstacle."""
        if not self.bounds.contains(rect):
            return True

        if any(rect.colliderect(wall) for wall in self.walls):
            return True

        return any(
            gate.blocks(rect)
            for gate in self.gates
        )

    def draw(self, surface):
        pygame.draw.rect(
            surface,
            FLOOR_COLOR,
            self.bounds
        )

        for wall in self.walls:
            pygame.draw.rect(
                surface,
                WALL_COLOR,
                wall
            )

        for gate in self.gates:
            gate.draw(surface)

        pygame.draw.rect(
            surface,
            WALL_COLOR,
            self.bounds,
            3
        )


class RoomMap:
    """Holds several rooms and tracks the player's current room.

    exits is a list of either:
        (from_room, trigger_rect, to_room, spawn_pos)
        (from_room, trigger_rect, to_room, spawn_pos, gate)

    Each spawn position should be outside the destination room's
    exit trigger to prevent immediate bouncing back.
    """

    def __init__(self, rooms, exits=None, start_room=None):
        rooms = list(rooms)
        if not rooms:
            raise ValueError("RoomMap requires at least one room.")

        self.rooms = {}
        for room in rooms:
            if room.name in self.rooms:
                raise ValueError(
                    f"RoomMap contains duplicate room name: {room.name!r}"
                )
            self.rooms[room.name] = room

        self.start_name = (
            rooms[0].name
            if start_room is None
            else start_room
        )
        if self.start_name not in self.rooms:
            raise ValueError(
                f"RoomMap start room does not exist: {self.start_name!r}"
            )

        self.current_name = self.start_name

        self.exits = []
        for exit_data in (exits or []):
            if len(exit_data) == 4:
                source, trigger, destination, spawn = exit_data
                required_gate = None
            elif len(exit_data) == 5:
                source, trigger, destination, spawn, required_gate = exit_data
            else:
                raise ValueError(
                    "RoomMap exits must contain four or five values."
                )

            if source not in self.rooms:
                raise ValueError(
                    f"RoomMap exit references unknown source room: {source!r}"
                )
            if destination not in self.rooms:
                raise ValueError(
                    "RoomMap exit references unknown destination room: "
                    f"{destination!r}"
                )
            if (
                required_gate is not None
                and required_gate not in self.rooms[source].gates
            ):
                raise ValueError(
                    f"RoomMap exit gate is not in source room {source!r}."
                )

            self.exits.append(
                (
                    source,
                    pygame.Rect(trigger),
                    destination,
                    spawn,
                    required_gate,
                )
            )

    def reset(self, start_room=None):
        """Reset the map and its gates to the configured start room."""
        if start_room is not None:
            if start_room not in self.rooms:
                raise ValueError(
                    f"RoomMap start room does not exist: {start_room!r}"
                )
            self.start_name = start_room

        self.current_name = self.start_name
        for room in self.rooms.values():
            for gate in room.gates:
                gate.reset()

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

    def get_exit_gates(self, source, trigger_rect):
        """Return the gates associated with an exit in a source room."""
        trigger_rect = pygame.Rect(trigger_rect)
        for (
            exit_source,
            trigger,
            _destination,
            _spawn,
            required_gate,
        ) in self.exits:
            if exit_source != source or trigger != trigger_rect:
                continue

            if required_gate is not None:
                return (required_gate,)

            return tuple(
                gate
                for gate in self.rooms[source].gates
                if gate.rect.colliderect(trigger)
            )

        return ()

    def check_exit(self, player_rect):
        """Switch rooms through an exit only when its gate is open.

        Returns True when a room transition occurs.
        """
        for source, trigger, destination, spawn, _required_gate in self.exits:
            if source != self.current_name:
                continue

            if not player_rect.colliderect(trigger):
                continue

            exit_gates = self.get_exit_gates(source, trigger)
            if any(not gate.is_open() for gate in exit_gates):
                continue

            spawn_rect = player_rect.copy()
            spawn_rect.topleft = spawn
            destination_room = self.rooms[destination]
            if destination_room.blocked(spawn_rect):
                continue

            if any(
                next_source == destination
                and spawn_rect.colliderect(next_trigger)
                for next_source, next_trigger, _, _, _ in self.exits
            ):
                continue

            self.current_name = destination
            player_rect.topleft = spawn_rect.topleft
            return True

        return False

    def draw(self, surface):
        """Draw the currently active room."""
        self.current.draw(surface)
