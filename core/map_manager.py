"""
core/map_manager.py
Owner: Member 1 - Core Game System

Rooms with walls and gates. Levels build their layouts from Room objects.
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