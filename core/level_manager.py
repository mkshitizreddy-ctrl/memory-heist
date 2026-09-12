"""
core/level_manager.py
Owner: Member 1 - Core Game System

Loads and switches between levels. Each level module (see levels/)
must expose a class with .update(dt), .render(surface),
.handle_event(event), and .is_complete() so the manager can treat
them uniformly.
"""


class LevelManager:
    def __init__(self, game):
        self.game = game
        self.levels = {}   # e.g. {"level1": Level1Instance}
        self.current = None

    def register(self, name, level_instance):
        self.levels[name] = level_instance

    def start(self, name):
        self.current = self.levels.get(name)

    def update(self, dt):
        if self.current:
            self.current.update(dt)
            if self.current.is_complete():
                # TODO: advance to next level via game.change_state
                pass

    def render(self, surface):
        if self.current:
            self.current.render(surface)

    def handle_event(self, event):
        if self.current:
            self.current.handle_event(event)