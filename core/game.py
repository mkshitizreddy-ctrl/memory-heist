"""
core/game.py
Owner: Member 1 - Core Game System

Sets up the Pygame window and runs the main game loop.
"""

import collections
import os

import pygame

from core import display
from core.player import Player, ARROWS
from core.level_manager import LevelManager
from core.difficulty import (
    get_difficulty,
    DEFAULT_DIFFICULTY,
    run_time_seconds,
)
from levels.level1 import Level1
from levels.level2 import Level2
from levels.level2_grid import GridRoom
from levels.level3_loops import Level3LaserLoop
from levels.floor4_archive import ArchiveFloor
from levels.level4_memory import Level4MemoryVault
from levels.level5_control import Level5ControlCenter
from levels.level5_hall import ServerHall
from levels.final_vault import FinalVault
from levels.final_vault_hall import VaultHall
from levels.common import draw_cyber_background
from ui.menu import MainMenu
from ui.screens import WinScreen, LoseScreen
from ui.story_screens import StoryScreen
from core.story import beat_for
from core.level_manager import LEVEL_ORDER
from core.floor_stats import floor_summary, snapshot
from systems.settings import Settings
from ui.hud import HUD
from ui.settings_screen import SettingsScreen
from ui.overlays import PauseOverlay
from ui.transitions import STATE_FADE_SECONDS, ElevatorWipe, draw_state_fade
from ui.atmosphere import Atmosphere, mood_for
from systems.audio import Audio
from systems.voice import VoiceEvents, VoicePlayer
from systems.music import MusicPlayer
from levels.floor1_lobby import FloorOneLobby
from ui.comms import CommsFeed
from systems.sound_events import SoundEvents

from systems.scoring import ScoreTracker, final_score
from systems.achievements import Stats
from systems.progress import clear_progress, describe, load_progress, save_progress
from systems.timer import Timer
from systems.security import SecurityMeter
from systems.hints import HintSystem
from ui.fonts import ui_font
from ui.stats_screen import StatsScreen


SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
FPS = 60
TITLE = "Memory Heist"
BG_COLOR = (10, 12, 20)
FADE_DURATION = 0.7
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
        self.mistakes = 0          # how many times security was raised this run

    def reset(self):
        super().reset()
        self.mistakes = 0

    def increase(self, amount=20):
        """Scale a base security increase before applying it."""
        self.mistakes += 1
        adjusted_amount = round(amount * self.penalty_multiplier)
        super().increase(adjusted_amount)


# A key state with nothing pressed, for levels that freeze walking while the player types.
NO_KEYS = collections.defaultdict(bool)

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
        self.story_screen = StoryScreen()
        # Switch for the story scenes; off goes straight from menu to Level 1.
        self.story_enabled = True
        self.lose_screen = LoseScreen()
        self.hud = HUD()
        self.atmosphere = Atmosphere((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.audio = Audio(ambient=False)   # MusicPlayer replaces the old drone
        self.music = MusicPlayer(self.audio)
        self.settings = Settings.load()
        self.audio.apply_settings(self.settings)
        self.settings_screen = SettingsScreen(
            self.settings, on_change=self._settings_changed,
            size=(SCREEN_WIDTH, SCREEN_HEIGHT),
        )
        self.comms = CommsFeed()
        self.voice = VoicePlayer(self.audio)
        self.voices = VoiceEvents(self.voice)
        self._comms_fonts = None            # built on the first frame it is drawn
        self.sounds = SoundEvents(self.audio)

        # Player & levels
        self.player = Player(*PLAYER_START_POS, palette="ghost")
        self.player2 = Player(
            *PLAYER2_START_POS,
            controls=ARROWS,
            palette="echo",
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
        self._wipe = ElevatorWipe()
        self._state_fade = 0.0      # 1.0 right after a screen change, fading to 0
        self._floor_snap = None     # score, time and mistakes when the floor began
        self.stats = Stats()
        self.stats_screen = StatsScreen()
        self._continued = False     # this run was resumed from a save
        self.saved_run = None       # the run the menu can continue, see _refresh_saved_run
        self._refresh_saved_run()

    def _refresh_saved_run(self):
        """Look for a saved run and tell the menu about it."""
        self.saved_run = load_progress()
        self.menu.saved_text = describe(self.saved_run) if self.saved_run else None

    def _save_run(self, level_name):
        """Remember the floor just reached, so the menu can offer Continue."""
        save_progress(level_name, self.score.get_score(),
                      self.timer.get_remaining() if self.timer.active else 0,
                      self.difficulty["label"].lower(), self.coop)

    def _continue_run(self):
        """Resume the saved run: same floor, score, time left, difficulty and co-op."""
        saved = self.saved_run
        if not saved:
            return
        self.menu.selected_difficulty = saved["difficulty"]
        self.menu.coop = saved["coop"]
        self.difficulty = get_difficulty(saved["difficulty"])
        self.security.penalty_multiplier = self.difficulty["security_penalty_multiplier"]
        self.coop = saved["coop"]
        self.hints.enabled = self.difficulty["hints_enabled"]
        self._continued = True
        self.score.reset()
        self.score.add(saved["score"])
        self.security.reset()
        self.timer = Timer()
        self.timer.start(saved["remaining"])
        self._register_levels()
        self.level_manager.start(saved["level"])
        self._reset_player_position()
        self._last_level_name = saved["level"]
        self._floor_snap = self._take_snapshot()
        self.change_state("playing")
        self._open_briefing(saved["level"])

    def _register_levels(self):
        """Create fresh level instances and register them."""
        if os.environ.get("MEMORY_HEIST_OLD_LEVEL1") == "1":
            # Escape hatch: the original question-screen Level 1.
            level1 = Level1(player=self.player, game=self)
        else:
            # Floor 1, the reception lobby on the shared kit, is Level 1.
            level1 = FloorOneLobby(player=self.player, game=self)
        self.level_manager.register("level1", level1)
        if os.environ.get("MEMORY_HEIST_OLD_LEVEL2") == "1":
            level2 = Level2(player=self.player, game=self)       # escape hatch
        else:
            level2 = GridRoom(player=self.player, game=self)     # Floor 2 on the shared kit
        self.level_manager.register("level2", level2)
        level3 = Level3LaserLoop(game=self)
        self._apply_difficulty_to_room_timer(level3)
        self.level_manager.register(
            "level3",
            level3
        )
        if os.environ.get("MEMORY_HEIST_OLD_LEVEL4") == "1":
            level4 = Level4MemoryVault(player=self.player, game=self)   # escape hatch
        else:
            level4 = ArchiveFloor(player=self.player, game=self)        # Floor 4 on the shared kit
        self.level_manager.register("level4", level4)
        if os.environ.get("MEMORY_HEIST_OLD_LEVEL5") == "1":
            level5 = Level5ControlCenter(game=self)               # escape hatch
        else:
            level5 = ServerHall(player=self.player, game=self)    # Floor 5 on the shared kit
        self.level_manager.register("level5", level5)
        if os.environ.get("MEMORY_HEIST_OLD_FINAL_VAULT") == "1":
            vault = FinalVault(game=self)                          # escape hatch
        else:
            vault = VaultHall(player=self.player, game=self)       # Master Vault on the shared kit
        self.level_manager.register("final_vault", vault)

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
        """Put the players at the level's spawn points, or the default start."""
        spawns = getattr(self.level_manager.current, "spawn_points", None)
        start1, start2 = spawns if spawns else (PLAYER_START_POS, PLAYER2_START_POS)
        self.player.reset_position(*start1)
        self.player2.reset_position(*start2)

    def _handle_level_change(self):
        """Start the transition fade when the active level changes."""
        current_name = self.level_manager.current_name

        if current_name != self._last_level_name:
            previous = self._last_level_name
            self._last_level_name = current_name
            cleared = None
            if self._is_next_floor(previous, current_name):
                cleared = self._floor_summary(previous)
            self._floor_snap = self._take_snapshot()
            if cleared is not None and self.state == "playing":
                self._save_run(current_name)
            self._fade_timer = FADE_DURATION
            # No level places the players itself, so without this a level
            # starts wherever the previous one left them.
            self._reset_player_position()
            # Never cover a win or loss that happened on the same frame.
            if self.state == "playing":
                self._open_briefing(current_name, cleared=cleared)

    @staticmethod
    def _is_next_floor(previous, current):
        """True when `current` is the floor right after `previous` (a real clear)."""
        if previous not in LEVEL_ORDER or current not in LEVEL_ORDER:
            return False
        return LEVEL_ORDER.index(current) == LEVEL_ORDER.index(previous) + 1

    def _take_snapshot(self):
        return snapshot(
            self.score.get_score(),
            self.timer.get_remaining() if self.timer.active else 0,
            getattr(self.security, "mistakes", 0),
        )

    def _floor_summary(self, name):
        return floor_summary(name, self._floor_snap, self._take_snapshot())

    def _open_briefing(self, level_name, cleared=None):
        """Show the story card for a level and freeze the run clock on it."""
        beat = beat_for(level_name)
        if not self.story_enabled or beat is None:
            return
        self.story_screen.begin(
            beat,
            coop=self.coop,
            progress=(LEVEL_ORDER.index(level_name), len(LEVEL_ORDER)),
            cleared=cleared,
        )
        self._fade_timer = 0.0
        self.change_state("briefing")

    def _open_outro(self):
        """Show the ending card with every level marked done."""
        total = len(LEVEL_ORDER)
        self.story_screen.begin(
            beat_for("outro"), coop=self.coop, progress=(total, total),
            cleared=self._floor_summary(self.level_manager.current_name),
        )
        self._fade_timer = 0.0
        # Not change_state: that would restart the win screen and its score.
        self.state = "outro"

    def _end_outro(self):
        """On to the win screen."""
        self.state = "win"

    def _end_briefing(self):
        """Back to the level, fading in."""
        self.change_state("playing")
        self._fade_timer = FADE_DURATION

    def _leave_story(self):
        """A story card finished normally: intro -> Level 1 card -> level."""
        if self.state == "intro":
            self._start_new_run()
            self._open_briefing("level1")
        elif self.state == "outro":
            self._end_outro()
        else:
            self._end_briefing()

    def _skip_story(self):
        """ESC on a story card: skip it (and, from the intro, the whole story)."""
        if self.state == "intro":
            self._start_new_run()
        elif self.state == "outro":
            self._end_outro()
        else:
            self._end_briefing()

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
    def _create_window(fullscreen=None):
        """Open the game window: full-screen by default, as saved in the settings.

        The drawing surface stays 960x640. SCALED stretches it to the screen
        (smoothed, see display.configure_scaling) and maps mouse positions
        back. Setups without a renderer (headless test runs) fall back to
        simpler windows instead of failing.
        """
        if fullscreen is None:
            fullscreen = Settings.load().fullscreen
        size = (SCREEN_WIDTH, SCREEN_HEIGHT)
        display.configure_scaling()
        flags = display.window_flags(fullscreen, pygame.display.get_driver())
        for attempt in (flags, pygame.SCALED, 0):
            try:
                return pygame.display.set_mode(size, attempt)
            except pygame.error:
                continue
        return pygame.display.set_mode(size)

    def _toggle_fullscreen(self):
        """Switch between the window and fullscreen, remember the choice, ignore unsupported setups."""
        try:
            pygame.display.toggle_fullscreen()
        except pygame.error:
            return
        self.settings.fullscreen = display.is_fullscreen()
        self.settings.save()

    def _settings_changed(self, kind):
        """Apply a settings change live; effects get a sample blip to judge by."""
        self.audio.apply_settings(self.settings)
        if kind == "sfx":
            self.audio.play("pickup")
        elif kind == "voice":
            self.voice.speak_clip("preview", "echo", "Good sum.")

    def _can_open_settings(self):
        return self.state == "menu" or (self.state == "playing" and self.paused)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif not self.settings_screen.closed:
                # The settings panel owns the keyboard and mouse while it is open.
                self.settings_screen.handle_event(event)
                continue

            elif event.type == pygame.KEYDOWN:
                if event.key != pygame.K_F11 and self.state != "playing":
                    self.sounds.click()

                if event.key == pygame.K_F11:
                    # Works on every screen and is never forwarded.
                    self._toggle_fullscreen()
                    continue

                elif event.key == pygame.K_s and self._can_open_settings():
                    self.settings_screen.open()
                    continue

                elif event.key == pygame.K_b and self.state == "menu":
                    self.change_state("stats")
                    continue

                elif event.key == pygame.K_ESCAPE and self.state == "stats":
                    self.change_state("menu")
                    continue

                elif event.key == pygame.K_ESCAPE:
                    if self.state == "playing":
                        self.paused = not self.paused
                        # The toggle is consumed here, never forwarded.
                        continue
                    elif self.state in ("intro", "briefing", "outro"):
                        # Skip the story instead of quitting.
                        self.story_screen.skip()
                        self._skip_story()
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
                        self._begin_run()
                        # The key that starts a run must not reach Level 1.
                        continue

                elif event.key == pygame.K_l and self.state == "menu" and self.saved_run:
                    self._continue_run()
                    continue

                elif event.key == pygame.K_r:
                    if self.state == "lose" or self._win_screen_is_done():
                        self._start_new_run()
                        # Same for retry: consume the key.
                        continue

                elif event.key == pygame.K_m:
                    if self.state == "playing" and self.paused:
                        self.change_state("menu")          # leave the floor; Continue keeps the last saved floor
                        continue
                    if self.state == "lose" or self._win_screen_is_done():
                        self.change_state("menu")
                        # The key must not reach the menu it opens.
                        continue

            if self.state in ("intro", "briefing", "outro"):
                self.story_screen.handle_event(event)
                if self.story_screen.done:
                    self._leave_story()
                # The key that ends a story card must not reach the level.
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
        """Advance one frame, then let the sound effects react to what changed."""
        self._update(dt)
        level = self.level_manager.current
        self.sounds.observe(
            self.state,
            self.score.get_score(),
            self.security.level,
            self.level_manager.current_name,
            getattr(level, "gates_passed", 0),
        )
        _, alert = mood_for(
            self.state,
            self.level_manager.current_name,
            self.security.level,
            self.security.max_level,
        )
        self.music.update(dt, self.state, self.level_manager.current_name, alert)
        self.comms.observe(
            self.state,
            self.level_manager.current_name,
            self.security.level,
            self.security.max_level,
            getattr(level, "gates_passed", 0),
        )
        if not self.paused:
            self.comms.update(dt)
        self.voices.observe(self.state, self.comms.current,
                            getattr(level, "npcs", ()), self.story_screen)
        if not self.paused:
            self.voice.update(dt)

    def _update(self, dt):
        if self._state_fade > 0:
            self._state_fade = max(0.0, self._state_fade - dt / STATE_FADE_SECONDS)
        if self._fade_timer > 0:
            self._fade_timer = max(
                0.0,
                self._fade_timer - dt
            )

        if self.state in ("intro", "briefing", "outro"):
            # Story cards only type their text; the run clock stays frozen.
            self.story_screen.update(dt)
            return

        if self.state != "playing" or self.paused:
            return

        # Spatial movement for levels that use direct player movement.
        if self._uses_spatial_player():
            keys = pygame.key.get_pressed()
            if getattr(self.level_manager.current, "movement_locked", False):
                # The level is taking typed input (the Level 5 terminal): stand still.
                keys = NO_KEYS
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

        # The final level just ended the run: show the ending card before
        # the win screen (whose score was already fixed by the win).
        if self.state == "win" and self.story_enabled:
            self._open_outro()
            return

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

    def _apply_mood(self):
        """Grade the screen: deeper levels get warmer, mistakes get redder."""
        depth, alert = mood_for(
            self.state,
            self.level_manager.current_name,
            self.security.level,
            self.security.max_level,
        )
        self.atmosphere.apply(self.screen, depth, alert, self._bg_tick)

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

        elif self.state in ("intro", "briefing", "outro"):
            self.story_screen.render(self.screen)

        elif self.state == "playing":
            self.level_manager.render(self.screen)

            # Draw the player in spatial levels.
            if self._uses_spatial_player():
                self.player.draw(self.screen)
                if self.coop:
                    self.player2.draw(self.screen)

            # Colour grade first, so the HUD stays crisp on top of it.
            self._apply_mood()

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
                coop=self.coop,
                tick=self._bg_tick,
            )

            if self._comms_fonts is None:
                self._comms_fonts = (ui_font(22), ui_font(24))
            self.comms.draw(self.screen, *self._comms_fonts)

            if self.paused:
                self._get_pause_assets().draw(
                    self.screen,
                    self.level_manager.current_name,
                    score=self.score.get_score(),
                    security=self.security.level,
                    security_max=self.security.max_level,
                    remaining=timer_val,
                    tick=self._bg_tick,
                )

        elif self.state == "win":
            self.win_screen.render(
                self.screen,
                score=self.win_screen.score,
            )

        elif self.state == "stats":
            self.stats_screen.render(self.screen, self.stats, self._bg_tick)

        elif self.state == "lose":
            self.lose_screen.render(
                self.screen,
                score=self.score.get_score(),
                level=self.level_manager.current_name,
            )

        if self.state != "playing":
            self._apply_mood()

        draw_state_fade(self.screen, self._state_fade)

        self.settings_screen.draw(self.screen, self._bg_tick)

        # Elevator doors open after a level change.
        if self._fade_timer > 0:
            self._wipe.draw(
                self.screen,
                self._fade_timer / FADE_DURATION,
                self.level_manager.current_name,
            )

        pygame.display.flip()

    def _get_pause_assets(self):
        """Return the pause overlay, building its layers and fonts once.

        Creating them every paused frame cost about 3 ms of a 16.7 ms frame.
        """
        if self._pause_assets is None:
            self._pause_assets = PauseOverlay((SCREEN_WIDTH, SCREEN_HEIGHT))
        return self._pause_assets

    def change_state(self, new_state: str):
        """Central place to switch between game states."""
        previous = self.state
        self.state = new_state
        self.paused = False
        if new_state != previous and new_state != "playing":
            # Screens fade in from black; levels arrive through the elevator doors instead.
            self._state_fade = 1.0

        if new_state == "lose" and previous != "lose":
            self.stats.record_loss()

        if new_state == "menu":
            self._refresh_saved_run()

        if new_state == "win":
            clear_progress()        # a finished run is not something to continue
            # Time left and difficulty turn the run score into the final one.
            result = final_score(
                self.score.get_score(),
                self.timer.get_remaining() if self.timer.active else 0,
                self.difficulty["score_multiplier"],
            )
            remaining = self.timer.get_remaining() if self.timer.active else 0
            earned, new = self.stats.record_win(result["total"], {
                "mistakes": getattr(self.security, "mistakes", 0),
                "time_left": remaining,
                "run_seconds": run_time_seconds(self.difficulty),
                "difficulty": self.difficulty["label"].lower(),
                "coop": self.coop,
                "continued": self._continued,
            })
            self.win_screen.begin(
                result["total"],
                self.difficulty["label"].title(),
                self.coop,
                result,
                badges=[(badge, badge in new) for badge in earned],
            )

    def _begin_run(self):
        """Start from the menu: the intro scene first, or straight to Level 1."""
        if not self.story_enabled:
            self._start_new_run()
            return
        # The run clock stays off until the intro is over.
        self.timer = Timer()
        self.story_screen.begin(beat_for("intro"), coop=self.coop)
        self.change_state("intro")

    def _start_new_run(self):
        """Reset systems, player position, fresh levels, and start Level 1."""
        self._continued = False
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
        self._floor_snap = self._take_snapshot()
        self._fade_timer = 0.0
