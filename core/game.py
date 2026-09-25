"""
core/game.py
Owner: Member 1 - Core Game System

Sets up the Pygame window and runs the main game loop.
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
from levels.common import draw_cyber_background
from ui.menu import MainMenu
from ui.screens import WinScreen, LoseScreen
from ui.hud import HUD
from systems.audio import Audio

from systems.scoring import ScoreTracker
from systems.timer import Timer
from systems.security import SecurityMeter
from systems.hints import HintSystem

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
FPS = 60
TITLE = "Memory Heist"
BG_COLOR = (10, 12, 20)
FADE_DURATION = 0.4  # seconds


class Game:
    """Owns the window, the clock, and the top-level game state."""

    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        self.state = "menu"          # "menu" | "playing" | "win" | "lose"
        self.paused = False

        # Systems (now live)
        self.score = ScoreTracker()
        self.timer = Timer()
        self.security = SecurityMeter(max_level=100)
        self.hints = HintSystem()

        # UI
        self.menu = MainMenu()
        self.win_screen = WinScreen()
        self.lose_screen = LoseScreen()
        self.hud = HUD()
        self.audio = Audio()

        # Player & levels
        self.player = Player(100, 100)
        self.level_manager = LevelManager(self)

        self._register_levels()
        self.level_manager.start("level1")
        self.wall = pygame.Rect(400, 200, 160, 40)   # only used by Level 4

        # Level-transition fade
        self._last_level_name = self.level_manager.current_name
        self._fade_timer = 0.0

        # Animated background tick (for the cyber-grid effect)
        self._bg_tick = 0

    def _register_levels(self):
        """Create fresh level instances and register them. Called at
        startup and again on every retry, so a level a player already
        completed doesn't stay marked complete on the next run."""
        self.level_manager.register("level1", Level1(player=self.player, game=self))
        self.level_manager.register("level2", Level2(player=self.player, game=self))
        self.level_manager.register("level3", Level3LaserLoop(game=self))
        self.level_manager.register("level4", Level4MemoryVault(player=self.player, game=self))
        self.level_manager.register("level5", Level5ControlCenter(game=self))
        self.level_manager.register("final_vault", FinalVault(game=self))

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.render()

        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == "playing":
                        self.paused = not self.paused
                    elif self.state in ("win", "lose", "menu"):
                        self.running = False

                elif event.key == pygame.K_RETURN:
                    if self.state == "menu":
                        self._start_new_run()

                elif event.key == pygame.K_r:
                    if self.state == "lose":
                        self._start_new_run()

            if self.state == "playing" and not self.paused:
                self.level_manager.handle_event(event)

    def update(self, dt):
        if self._fade_timer > 0:
            self._fade_timer = max(0.0, self._fade_timer - dt)

        if self.state != "playing" or self.paused:
            return

        # Level 4 movement (unchanged)
        if self.level_manager.current_name == "level4":
            keys = pygame.key.get_pressed()
            old_rect = self.player.rect.copy()
            self.player.handle_input(keys, dt)
            if self.player.rect.colliderect(self.wall):
                self.player.rect = old_rect
            self.player.rect.clamp_ip(self.screen.get_rect())

        # Update current level
        self.level_manager.update(dt)

        # Detect a level change and start a fade
        if self.level_manager.current_name != self._last_level_name:
            self._last_level_name = self.level_manager.current_name
            self._fade_timer = FADE_DURATION

        # Update global timer
        self.timer.update(dt)

        # Lose conditions
        if self.security.is_lockdown() or self.timer.expired():
            self.change_state("lose")

    def render(self):
        self._bg_tick += 1

        if self.state == "playing":
            draw_cyber_background(self.screen, self._bg_tick)
        else:
            self.screen.fill(BG_COLOR)

        if self.state == "menu":
            self.menu.render(self.screen)

        elif self.state == "playing":
            self.level_manager.render(self.screen)

            if self.level_manager.current_name == "level4":
                self.player.draw(self.screen)

            # HUD with live data
            timer_val = self.timer.get_remaining() if self.timer.active else None
            self.hud.render(
                self.screen,
                self.level_manager.current_name,
                score=self.score.get_score(),
                security_level=self.security.level,
                security_max=self.security.max_level,
                timer_remaining=timer_val,
            )

            if self.paused:
                overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                overlay.fill((0, 0, 0, 160))
                self.screen.blit(overlay, (0, 0))
                pause_font = pygame.font.Font(None, 48)
                txt = pause_font.render("PAUSED", True, (220, 220, 220))
                self.screen.blit(
                    txt,
                    (
                        SCREEN_WIDTH // 2 - txt.get_width() // 2,
                        SCREEN_HEIGHT // 2 - 20,
                    ),
                )

        elif self.state == "win":
            self.win_screen.render(self.screen, score=self.score.get_score())

        elif self.state == "lose":
            self.lose_screen.render(self.screen, score=self.score.get_score())

        # Fade overlay: fades from black to transparent right after a level change
        if self._fade_timer > 0:
            alpha = int(255 * (self._fade_timer / FADE_DURATION))
            fade_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            fade_surface.fill((0, 0, 0))
            fade_surface.set_alpha(alpha)
            self.screen.blit(fade_surface, (0, 0))

        pygame.display.flip()

    def change_state(self, new_state: str):
        """Central place to switch between menu / playing / win / lose."""
        self.state = new_state
        self.paused = False

    def _start_new_run(self):
        """Reset systems, get fresh level instances, go back to Level 1."""
        self.score.reset()
        self.security.reset()
        self.timer = Timer()          # fresh timer
        self._register_levels()       # fresh levels — undoes prior completion
        self.level_manager.start("level1")
        self.change_state("playing")
        self._last_level_name = self.level_manager.current_name
        self._fade_timer = 0.0