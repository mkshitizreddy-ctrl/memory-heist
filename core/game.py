"""
core/game.py
Owner: Member 1 - Core Game System

Sets up the Pygame window and runs the main game loop.
"""

import pygame

from core.player import Player, ARROWS
from core.level_manager import LevelManager
from core.difficulty import (
    get_difficulty,
    DEFAULT_DIFFICULTY,
    run_time_seconds,
)
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

from systems.scoring import ScoreTracker, final_score
from systems.timer import Timer
from systems.security import SecurityMeter
from systems.hints import HintSystem


SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
FPS = 60
TITLE = "Memory Heist"
BG_COLOR = (10, 12, 20)
FADE_DURATION = 0.4
# Longest frame time (seconds) the game will simulate. Below 20 FPS the game
# slows down instead of taking one huge step.
MAX_DT = 0.05
PLAYER_START_POS = (100, 100)
PLAYER2_START_POS = (150, 100)


class DifficultySecurityMeter(SecurityMeter):
    """Apply the selected difficulty multiplier to security increases."""

    def __init__(self, max_level=100):
        super().__init__(max_level=max_level)
        self.penalty_multiplier = 1.0

    def increase(self, amount=20):
        """Scale a base security increase before applying it."""
        adjusted_amount = round(amount * self.penalty_multiplier)
        super().increase(adjusted_amount)


class Game:
    """Owns the window, the clock, and the top-level game state."""

    def __init__(self):
        pygame.init()
        self.screen = self._create_window()
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        self.state = "menu"
        self.paused = False

        # Systems
        self.score = ScoreTracker()
        self.timer = Timer()
        self.security = DifficultySecurityMeter(max_level=100)
        self.hints = HintSystem()
        self.difficulty = get_difficulty(DEFAULT_DIFFICULTY)

        # UI
        self.menu = MainMenu()
        self.win_screen = WinScreen()
        self.lose_screen = LoseScreen()
        self.hud = HUD()
        self.audio = Audio()

        # Player & levels
        self.player = Player(*PLAYER_START_POS)
        self.player2 = Player(
            *PLAYER2_START_POS,
            controls=ARROWS,
            palette="orange",
        )
        self.coop = False
        self.level_manager = LevelManager(self)

        self._register_levels()
        self.level_manager.start("level1")

        # Level-transition fade
        self._last_level_name = self.level_manager.current_name
        self._fade_timer = 0.0

        # Animated background tick
        self._bg_tick = 0
        # Built on the first paused frame (see _get_pause_assets).
        self._pause_assets = None

    def _register_levels(self):
        """Create fresh level instances and register them."""
        self.level_manager.register(
            "level1",
            Level1(player=self.player, game=self)
        )
        self.level_manager.register(
            "level2",
            Level2(player=self.player, game=self)
        )
        level3 = Level3LaserLoop(game=self)
        self._apply_difficulty_to_room_timer(level3)
        self.level_manager.register(
            "level3",
            level3
        )
        self.level_manager.register(
            "level4",
            Level4MemoryVault(player=self.player, game=self)
        )
        self.level_manager.register(
            "level5",
            Level5ControlCenter(game=self)
        )
        self.level_manager.register(
            "final_vault",
            FinalVault(game=self)
        )

    def _apply_difficulty_to_room_timer(self, level):
        """Scale a level's room countdown using the selected difficulty."""
        base_time = getattr(level, "base_time_limit", None)
        if base_time is None:
            return

        multiplier = self.difficulty["timer_multiplier"]
        level.base_time_limit = max(1, round(base_time * multiplier))

        room_number = 1
        get_room_number = getattr(level, "current_room_number", None)
        if callable(get_room_number):
            room_number = get_room_number()

        level.time_limit = max(
            1,
            level.base_time_limit - (room_number - 1),
        )
        level.time_left = level.time_limit

    def _reset_player_position(self):
        """Reset the player to the configured starting position."""
        self.player.reset_position(*PLAYER_START_POS)
        self.player2.reset_position(*PLAYER2_START_POS)

    def _handle_level_change(self):
        """Start the transition fade when the active level changes."""
        current_name = self.level_manager.current_name

        if current_name != self._last_level_name:
            self._last_level_name = current_name
            self._fade_timer = FADE_DURATION
            # No level places the players itself, so without this a level
            # starts wherever the previous one left them.
            self._reset_player_position()

    def _frame_dt(self):
        """Seconds since the previous frame, capped at MAX_DT.

        A stalled frame (dragging the window, a slow load) would otherwise
        give every update a huge dt: timers would jump and a movement step
        could carry the player through a wall.
        """
        return min(self.clock.tick(FPS) / 1000.0, MAX_DT)

    def run(self):
        while self.running:
            dt = self._frame_dt()
            self.handle_events()
            self.update(dt)
            self.render()

    def _win_screen_is_done(self):
        """True on the win screen once the name is saved and the table shows.

        While a name is being typed, R and M are ordinary letters.
        """
        return self.state == "win" and not self.win_screen.entering

    @staticmethod
    def _create_window():
        """Open the 960x640 window, scaled when the machine supports it.

        SCALED keeps the drawing surface at 960x640 and lets F11 stretch it
        to the screen, with mouse positions mapped back automatically. Setups
        without a renderer (headless test runs) get a plain window instead.
        """
        size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        try:
            return pygame.display.set_mode(size, pygame.SCALED)
        except pygame.error:
            return pygame.display.set_mode(size)

    def _toggle_fullscreen(self):
        """Switch between the window and fullscreen; ignore unsupported setups."""
        try:
            pygame.display.toggle_fullscreen()
        except pygame.error:
            pass

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11:
                    # Works on every screen and is never forwarded.
                    self._toggle_fullscreen()
                    continue

                elif event.key == pygame.K_ESCAPE:
                    if self.state == "playing":
                        self.paused = not self.paused
                        # The toggle is consumed here, never forwarded.
                        continue
                    elif self.state in ("win", "lose", "menu"):
                        if self.state == "win" and self.win_screen.entering:
                            # Skip the leaderboard entry instead of quitting,
                            # so a score being named is not thrown away.
                            self.win_screen.skip_entry()
                            continue
                        self.running = False

                elif event.key == pygame.K_RETURN:
                    if self.state == "menu":
                        self.difficulty = get_difficulty(
                            self.menu.selected_difficulty
                        )
                        self.security.penalty_multiplier = self.difficulty[
                            "security_penalty_multiplier"
                        ]
                        self.coop = self.menu.coop
                        self.hints.enabled = self.difficulty["hints_enabled"]
                        self._start_new_run()
                        # The key that starts a run must not reach Level 1.
                        continue

                elif event.key == pygame.K_r:
                    if self.state == "lose" or self._win_screen_is_done():
                        self._start_new_run()
                        # Same for retry: consume the key.
                        continue

                elif event.key == pygame.K_m:
                    if self.state == "lose" or self._win_screen_is_done():
                        self.change_state("menu")
                        # The key must not reach the menu it opens.
                        continue

            if self.state == "menu":
                self.menu.handle_event(event)

            if self.state == "win":
                self.win_screen.handle_event(event)

            if self.state == "playing" and not self.paused:
                self.level_manager.handle_event(event)

    def _get_spatial_blocked(self):
        """Return the collision callback for the active spatial level."""
        level = self.level_manager.current

        if level is None:
            return None

        room_map = getattr(level, "room_map", None)

        if room_map is not None:
            return room_map.blocked

        get_bounds = getattr(level, "get_bounds", None)
        get_obstacles = getattr(level, "get_obstacles", None)

        if callable(get_bounds) or callable(get_obstacles):

            def blocked(rect):
                bounds = get_bounds() if callable(get_bounds) else None

                if bounds is not None and not bounds.contains(rect):
                    return True

                obstacles = (
                    get_obstacles()
                    if callable(get_obstacles)
                    else []
                )
                return any(
                    rect.colliderect(obstacle)
                    for obstacle in obstacles
                )

            return blocked

        return None

    def _uses_spatial_player(self):
        """Return whether the active level provides spatial world geometry."""
        level = self.level_manager.current
        if level is None:
            return False

        return (
            getattr(level, "room_map", None) is not None
            or callable(getattr(level, "get_bounds", None))
            or callable(getattr(level, "get_obstacles", None))
        )

    def update(self, dt):
        if self._fade_timer > 0:
            self._fade_timer = max(
                0.0,
                self._fade_timer - dt
            )

        if self.state != "playing" or self.paused:
            return

        # Spatial movement for levels that use direct player movement.
        if self._uses_spatial_player():
            keys = pygame.key.get_pressed()
            blocked = self._get_spatial_blocked()

            self.player.handle_input(
                keys,
                dt,
                blocked=blocked,
            )

            self.player.rect.clamp_ip(
                self.screen.get_rect()
            )

            if self.coop:
                self.player2.handle_input(
                    keys,
                    dt,
                    blocked=blocked,
                )
                self.player2.rect.clamp_ip(
                    self.screen.get_rect()
                )

        # Update current level
        self.level_manager.update(dt)

        # Detect level changes
        self._handle_level_change()

        # The level may have just ended the run (win). Do not let the
        # timer or security checks below overwrite that this frame.
        if self.state != "playing":
            return

        # Update global timer
        self.timer.update(dt)

        # Lose conditions
        if (
            self.security.is_lockdown()
            or self.timer.expired()
        ):
            self.change_state("lose")

    def render(self):
        self._bg_tick += 1

        if self.state == "playing":
            draw_cyber_background(
                self.screen,
                self._bg_tick
            )
        else:
            self.screen.fill(BG_COLOR)

        if self.state == "menu":
            self.menu.render(self.screen)

        elif self.state == "playing":
            self.level_manager.render(self.screen)

            # Draw the player in spatial levels.
            if self._uses_spatial_player():
                self.player.draw(self.screen)
                if self.coop:
                    self.player2.draw(self.screen)

            # HUD with live data
            timer_val = (
                self.timer.get_remaining()
                if self.timer.active
                else None
            )

            self.hud.render(
                self.screen,
                self.level_manager.current_name,
                score=self.score.get_score(),
                security_level=self.security.level,
                security_max=self.security.max_level,
                timer_remaining=timer_val,
            )

            if self.paused:
                overlay, pause_font = self._get_pause_assets()
                self.screen.blit(
                    overlay,
                    (0, 0)
                )

                txt = pause_font.render(
                    "PAUSED",
                    True,
                    (220, 220, 220),
                )

                self.screen.blit(
                    txt,
                    (
                        SCREEN_WIDTH // 2
                        - txt.get_width() // 2,
                        SCREEN_HEIGHT // 2 - 20,
                    ),
                )

        elif self.state == "win":
            self.win_screen.render(
                self.screen,
                score=self.win_screen.score,
            )

        elif self.state == "lose":
            self.lose_screen.render(
                self.screen,
                score=self.score.get_score(),
            )

        # Fade overlay after a level change.
        if self._fade_timer > 0:
            alpha = int(
                255 * (
                    self._fade_timer / FADE_DURATION
                )
            )

            fade_surface = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT)
            )
            fade_surface.fill((0, 0, 0))
            fade_surface.set_alpha(alpha)
            self.screen.blit(
                fade_surface,
                (0, 0)
            )

        pygame.display.flip()

    def _get_pause_assets(self):
        """Return (overlay, font) for the pause screen, building them once.

        Creating them every paused frame cost about 3 ms of a 16.7 ms frame.
        """
        if self._pause_assets is None:
            overlay = pygame.Surface(
                (SCREEN_WIDTH, SCREEN_HEIGHT),
                pygame.SRCALPHA,
            )
            overlay.fill((0, 0, 0, 160))
            self._pause_assets = (overlay, pygame.font.Font(None, 48))
        return self._pause_assets

    def change_state(self, new_state: str):
        """Central place to switch between game states."""
        self.state = new_state
        self.paused = False

        if new_state == "win":
            # Time left and difficulty turn the run score into the final one.
            result = final_score(
                self.score.get_score(),
                self.timer.get_remaining() if self.timer.active else 0,
                self.difficulty["score_multiplier"],
            )
            self.win_screen.begin(
                result["total"],
                self.difficulty["label"].title(),
                self.coop,
                result,
            )

    def _start_new_run(self):
        """Reset systems, player position, fresh levels, and start Level 1."""
        self.score.reset()
        self.security.reset()
        self.timer = Timer()
        self.timer.start(run_time_seconds(self.difficulty))
        self._reset_player_position()

        # Fresh levels — undoes prior completion.
        self._register_levels()
        self.level_manager.start("level1")

        self.change_state("playing")
        self._last_level_name = self.level_manager.current_name
        self._fade_timer = 0.0
