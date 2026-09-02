"""
core/game.py
Owner: Member 1 - Core Game System

Sets up the Pygame window and runs the main game loop.
This is the skeleton every other module plugs into, so keep its
public interface (Game.run, Game.change_state) stable once the
team starts building on top of it.
"""

import sys
import pygame

# --- Config (move to a settings module if it grows) ---
SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
FPS = 60
TITLE = "Memory Heist"
BG_COLOR = (10, 12, 20)


class Game:
    """Owns the window, the clock, and the top-level game state."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        # Placeholder state machine: "menu", "tutorial", "level1"...,
        # "final_vault", "win", "lose". Level modules will register
        # themselves here once built.
        self.state = "menu"

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000  # delta time in seconds
            self.handle_events()
            self.update(dt)
            self.render()

        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False
            # TODO: forward events to the active level/player once built

    def update(self, dt):
        # TODO: update player, active level, systems (timer, security meter)
        pass

    def render(self):
        self.screen.fill(BG_COLOR)
        # TODO: draw active level / HUD here
        pygame.display.flip()

    def change_state(self, new_state: str):
        """Central place to switch between menu/levels so state changes
        are traceable and don't get scattered across modules."""
        self.state = new_state
