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

from core.player import Player
from core.level_manager import LevelManager
from levels.level1 import Level1
from levels.level2 import Level2
from levels.level3_loops import Level3LaserLoop
from levels.level4_memory import Level4MemoryVault
from levels.level5_control import Level5ControlCenter
from levels.final_vault import FinalVault
from ui.menu import MainMenu
from ui.screens import WinScreen
from ui.hud import HUD

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

        self.state = "menu"
        self.paused = False

        self.menu = MainMenu()
        self.win_screen = WinScreen()
        self.hud = HUD()

        self.player = Player(100, 100)
        self.level_manager = LevelManager(self)

        self.level_manager.register("level1", Level1(player=self.player))
        self.level_manager.register("level2", Level2(player=self.player))
        self.level_manager.register("level3", Level3LaserLoop())
        self.level_manager.register("level4", Level4MemoryVault(player=self.player))
        self.level_manager.register("level5", Level5ControlCenter())
        self.level_manager.register("final_vault", FinalVault())
        self.level_manager.start("level1")
        self.wall = pygame.Rect(400, 200, 160, 40)

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000
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
                if self.state == "playing":
                    self.paused = not self.paused
                elif self.state == "win":
                    self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                if self.state == "menu":
                    self.change_state("playing")
            if self.state == "playing":
                self.level_manager.handle_event(event)

    def update(self, dt):
        if self.state != "playing" or self.paused:
            return
        if self.level_manager.current_name == "level4":
            keys = pygame.key.get_pressed()
            old_rect = self.player.rect.copy()
            self.player.handle_input(keys, dt)
            if self.player.rect.colliderect(self.wall):
                self.player.rect = old_rect
            self.player.rect.clamp_ip(self.screen.get_rect())
        self.level_manager.update(dt)

    def render(self):
        self.screen.fill(BG_COLOR)

        if self.state == "menu":
            self.menu.render(self.screen)
        elif self.state == "playing":
            self.level_manager.render(self.screen)
            if self.level_manager.current_name == "level4":
                self.player.draw(self.screen)
            self.hud.render(self.screen, self.level_manager.current_name)
            if self.paused:
                pygame.draw.rect(self.screen, (40, 40, 40), (0, 0, SCREEN_WIDTH, SCREEN_HEIGHT))
        elif self.state == "win":
            self.win_screen.render(self.screen)

        pygame.display.flip()

    def change_state(self, new_state: str):
        """Central place to switch between menu/levels so state changes
        are traceable and don't get scattered across modules."""
        self.state = new_state