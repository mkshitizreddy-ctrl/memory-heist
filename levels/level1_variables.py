"""
levels/level1_variables.py
Owner: Member 2

Level 1 - The Security Gate
Topics: variables, data types, strings, integers, booleans

Every level class should expose:
    update(dt)         - advance puzzle/animation state
    render(surface)     - draw the room and its puzzle UI
    handle_event(event) - react to a single keyboard/mouse event
    is_complete()        - return True once the player has solved it

Keep puzzle DATA (questions, answers, patterns) in data/puzzles.json
rather than hardcoding it here, so it's easy to tweak difficulty
without touching code.
"""

import pygame


class Level1SecurityGate:
    def __init__(self):
        self.complete = False

    def update(self, dt):
        pass

    def render(self, surface):
        pygame.draw.rect(surface, (80, 80, 200), (50, 50, 100, 50))

    def handle_event(self, event):
        pass

    def is_complete(self):
        return self.complete