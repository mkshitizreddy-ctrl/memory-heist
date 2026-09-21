"""
core/level_manager.py
Owner: Member 1 - Core Game System

Loads and switches between levels. Each level module (see levels/)
must expose a class with .update(dt), .render(surface),
.handle_event(event), and .is_complete() so the manager can treat
them uniformly.
"""

LEVEL_ORDER = ["level1", "level2", "level3", "level4", "level5"]


class LevelManager:
    def __init__(self, game):
        self.game = game
        self.levels = {}   # e.g. {"level1": Level1Instance}
        self.current = None
        self.current_name = None

    def register(self, name, level_instance):
        self.levels[name] = level_instance

    def start(self, name):
        self.current = self.levels.get(name)
        self.current_name = name

    def update(self, dt):
        if not self.current:
            return
        self.current.update(dt)
        if self.current.is_complete():
            self._advance()

    def _advance(self):
        idx = LEVEL_ORDER.index(self.current_name)
        if idx + 1 < len(LEVEL_ORDER):
            self.start(LEVEL_ORDER[idx + 1])
        else:
            self.game.change_state("win")

    def render(self, surface):
        if self.current:
            self.current.render(surface)

    def handle_event(self, event):
        if self.current:
            self.current.handle_event(event)