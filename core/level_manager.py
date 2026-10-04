"""
core/level_manager.py
Owner: Member 1 - Core Game System

Loads and switches between levels. Each level module (see levels/)
must expose a class with .update(dt), .render(surface),
.handle_event(event), and .is_complete() so the manager can treat
them uniformly.
"""

LEVEL_ORDER = [
    "level1",
    "level2",
    "level3",
    "level4",
    "level5",
    "final_vault",
]


class LevelManager:
    def __init__(self, game):
        self.game = game
        self.levels = {}
        self.current = None
        self.current_name = None

    def register(self, name, level_instance):
        """Register a level instance by its game-flow name."""
        self.levels[name] = level_instance

    def start(self, name):
        """Start a registered level.

        Raises a clear error instead of silently creating an invalid
        current level when an unknown name is requested.
        """
        if name not in self.levels:
            raise ValueError(
                f"Cannot start unknown level: {name!r}"
            )

        self.current = self.levels[name]
        self.current_name = name

    def update(self, dt):
        """Update the active level and advance when it completes."""
        if self.current is None:
            return

        self.current.update(dt)

        if self.current.is_complete():
            self._advance()

    def _advance(self):
        """Move to the next level or finish the game."""
        if self.current_name not in LEVEL_ORDER:
            raise ValueError(
                f"Cannot advance unknown level: {self.current_name!r}"
            )

        index = LEVEL_ORDER.index(self.current_name)

        if index + 1 < len(LEVEL_ORDER):
            self.start(LEVEL_ORDER[index + 1])
        else:
            self.game.change_state("win")

    def render(self, surface):
        """Render the active level."""
        if self.current is not None:
            self.current.render(surface)

    def handle_event(self, event):
        """Forward an input event to the active level."""
        if self.current is not None:
            self.current.handle_event(event)