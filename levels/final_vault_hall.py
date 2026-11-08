"""
levels/final_vault_hall.py
Owner: Member 4 - Apporov Sahu's Final Vault, rebuilt as a walkable floor

Final Floor - Master Vault  (everything combined)

Three chambers, two of the six stages in each.  The stage's objective is on the
screen of the chamber you are in, its code is on the monitor below, and the three
answers are pads on the floor.  Stand on a pad and press the action key.

    E            answer on the pad you stand on (player 1)    Right Shift (player 2)
    stages 1-2   data types, operators        gate 1 opens after stage 2
    stages 3-4   loops, dictionaries          gate 2 opens after stage 4
    stages 5-6   functions, exceptions        the vault door opens after stage 6
    stage 6      also has a terminal: walk to the console, press E, type an integer
                 or some text, ENTER.  It shows a ValueError being caught (optional).
                 Arrow keys step away from it.

The rules are exactly the old Final Vault's: +50 per stage (once each), +150 for
unlocking the vault, a wrong pad costs security +20 and score -10, and the terminal
adds security +5 for text or a wrong number.  The questions, code and the terminal
check come from FinalVault, which this class extends; levels/final_vault.py is
untouched and returns with MEMORY_HEIST_OLD_FINAL_VAULT=1.

Typing at the terminal no longer clashes with the answer keys (the old screen used
1-3 for answers, so those digits could not be typed on stage 6).
"""

import pygame

from core.tilemap import TILE, TileMap, make_tiles
from levels import grid_decor as G
from levels import vault_decor as V
from levels.final_vault import FinalVault
from levels.room_base import TITLE_Y, RoomMap, RoomMixin
from ui import theme
from ui.fonts import code_font, ui_font
from ui.kit import shadowed

LEVEL_KEY = "final_vault"
STAGE_POINTS, COMPLETION_BONUS = 50, 150
WRONG_SECURITY, WRONG_PENALTY = 20, 10
GATE_COUNT = 3
GATE_OPEN_RATE = 3.0
FLASH_SECONDS = 0.5
DONE_PAD_SECONDS = 0.9
ARROWS = (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)
MAX_INPUT = 4
TERMINAL_STAGE = 6
TERMINAL_TIP = "Optional: walk to the terminal (bottom right) and press E to watch a ValueError get caught."
GOOD_STARTS = ("CORRECT", "MASTER", "Correct", "EXCEPTION")


class VaultHall(RoomMixin, FinalVault):
    def __init__(self, player=None, game=None, seed=None):
        FinalVault.__init__(self, game=game)
        self.player = player
        self.init_room(seed)
        self.say("Stand on the right answer, then press E.")
        self.solved = False                        # stage 6 answered; the door is opening
        self.at_terminal = False
        self.gate_open = [0.0] * GATE_COUNT
        self.pad_flash = {}
        self.done_pad = None
        self.last_answer = {}                      # stage -> the answer that passed it

        self.tilemap = TileMap(V.layout_rows())
        self.tiles = make_tiles(LEVEL_KEY)
        self.props = V.solid_props()
        self.gate_blocks = [r.copy() for r in V.GATE_RECTS]
        self.room_map = RoomMap(self.tilemap, self.props + self.gate_blocks)
        self.exit_zone = pygame.Rect(28 * TILE + 8, V.GATE_RECTS[2].y, TILE * 2, V.GATE_RECTS[2].h)
        self.spawn_points = V.SPAWNS
        self.npcs = []
        self.ambience = V.Ambience(seed=61)

        self.title_font = ui_font(26, bold=True)
        self.line_font = ui_font(22)
        self.small = ui_font(20)
        self._background = None

    # --- state ------------------------------------------------------------
    @property
    def movement_locked(self):
        return self.at_terminal

    @property
    def gates_passed(self):
        return GATE_COUNT if self.solved else (self.stage - 1) // V.PER_CHAMBER

    @property
    def chamber(self):
        return V.chamber_of(self.stage)

    def pad_rects(self):
        if self.solved:
            return []
        return V.pad_rects(self.chamber, len(self._get_options()))

    def pad_at(self, player):
        for i, rect in enumerate(self.pad_rects()):
            if rect.inflate(8, 8).collidepoint(player.rect.center):
                return i
        return None

    def console_state(self):
        if self.solved:
            return "done"
        if self.at_terminal:
            return "active"
        return "ready" if self.stage == TERMINAL_STAGE else "locked"

    def feedback_good(self):
        return self.feedback.startswith(GOOD_STARTS)

    # --- input ------------------------------------------------------------
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN or self.complete:
            return
        if self.at_terminal:
            self._terminal_event(event)
            return
        if self.solved:
            return
        for player, key in self.players():
            if event.key != key:
                continue
            index = self.pad_at(player)
            if index is not None:
                self._press_pad(index)
            elif self.stage == TERMINAL_STAGE and self.near(player, V.CONSOLE):
                self.at_terminal = True
                self.say("Type an integer or some text, then ENTER.", theme.GOLD)
            else:
                self.say("Stand on an answer pad, then press E.", theme.MIST)

    def _terminal_event(self, event):
        if event.key in ARROWS:
            self.at_terminal = False
            self.say("You step away from the terminal.", theme.MIST)
        elif event.key == pygame.K_BACKSPACE:
            self.command = self.command[:-1]
        elif event.key == pygame.K_RETURN:
            before = self.game.security.level if self.game else 0
            self._submit_terminal()
            if self.game and self.game.security.level > before:
                self.shake.add(0.3)
                self.burst(V.CONSOLE.midtop, theme.CORAL, 8)
            self.say(self.feedback, theme.TEAL if self.feedback_good() else theme.CORAL)
        elif event.unicode and event.unicode.isprintable() and len(self.command) < MAX_INPUT:
            self.command += event.unicode

    # --- the rules (the old Final Vault's numbers) ----------------------------
    def _press_pad(self, index):
        pad = self.pad_rects()[index]
        label = self._get_options()[index]
        self.selected_option = index + 1
        if self._is_correct_option(index + 1):
            if self.game and self.stage not in self._stage_scores:
                self.game.score.add(STAGE_POINTS)
                self._stage_scores.add(self.stage)
            self.last_answer[self.stage] = label
            self.burst(pad.center, theme.TEAL, 18)
            self.sfx("door")
            self.pad_flash = {}
            self.done_pad = [pad, label, DONE_PAD_SECONDS]
            if self.stage >= self.total_stages:
                self.solved = True
                self.feedback = "MASTER VAULT UNLOCKED! ESCAPE SEQUENCE COMPLETE!"
                if self.game and not self._completion_awarded:
                    self.game.score.add(COMPLETION_BONUS)
                    self._completion_awarded = True
            else:
                self.stage += 1
                self.selected_option = None
                self.command = self.command_result = ""
                self.feedback = "CORRECT! Next security challenge unlocked."
            self.say(self.feedback, theme.GOLD if self.solved else theme.TEAL)
        else:
            self.feedback = "INCORRECT! Review the Python concept and try again."
            self.pad_flash[index] = FLASH_SECONDS
            self.shake.add(0.55)
            self.burst(pad.center, theme.CORAL, 12)
            self.say(self.feedback, theme.CORAL)
            if self.game:
                self.game.security.increase(WRONG_SECURITY)
                self.game.score.penalize(WRONG_PENALTY)

    # --- per frame ----------------------------------------------------------
    def update(self, dt):
        dt = max(0.0, dt)
        self.update_room(dt)
        self.ambience.update(dt)
        self.pad_flash = {i: left - dt for i, left in self.pad_flash.items() if left - dt > 0}
        if self.done_pad is not None:
            self.done_pad[2] -= dt
            if self.done_pad[2] <= 0:
                self.done_pad = None
        if self.complete:
            return
        targets = (self.stage >= 3, self.stage >= 5, self.solved)
        for i, want in enumerate(targets):
            self.gate_open[i] += ((1.0 if want else 0.0) - self.gate_open[i]) * min(1.0, dt * GATE_OPEN_RATE)
            if self.gate_open[i] > 0.9:
                self.gate_blocks[i].size = (0, 0)
        if self.gate_open[2] > 0.9:
            for player, _ in self.players():
                if player.rect.colliderect(self.exit_zone):
                    self.complete = True
                    self.say("MASTER VAULT UNLOCKED - escape!", theme.GOLD)
                    break

    def is_complete(self):
        return self.complete

    # --- drawing ------------------------------------------------------------
    def _build_background(self):
        size = self.tilemap.pixel_size
        bg = pygame.Surface(size)
        cam = type("Cam", (), {})()
        cam.offset = lambda: (0, 0)
        cam.x = cam.y = 0
        cam.view_w, cam.view_h = size
        self.tilemap.render(bg, cam, self.tiles)
        accent = theme.floor_palette(LEVEL_KEY)["accent"]
        V.draw_static(bg, accent)
        title = shadowed(self.title_font, "FINAL FLOOR - MASTER VAULT", theme.mix(accent, theme.PAPER, 0.4))
        bg.blit(title, (TILE * 2, TITLE_Y))
        self._background = bg

    def chamber_state(self, chamber):
        if self.solved or chamber < self.chamber:
            return "accepted"
        return "active" if chamber == self.chamber else "standby"

    def key_hint(self):
        if self.solved:
            return "Walk through the vault door"
        if self.at_terminal:
            return "Type, ENTER to run"
        return "E: pad or terminal" if self.stage == TERMINAL_STAGE else "E: answer on a pad"

    def readout(self):
        if self.solved:
            tip = "The vault door is open. Walk through it."
        elif self.stage == TERMINAL_STAGE:
            tip = TERMINAL_TIP
        else:
            tip = "Stand on the answer you think is right and press E. The lit line is the part to fill in."
        return V.readout_lines([(tip, theme.MIST)], ui_font(V.READOUT_FONT_SIZE), V.READOUT.w - 24 - 70)

    def render(self, surface):
        if self._background is None:
            self._build_background()
        world = self._background.copy()
        accent = theme.floor_palette(LEVEL_KEY)["accent"]
        self.ambience.draw(world, accent)
        for c in range(GATE_COUNT):
            state = self.chamber_state(c)
            last = (c + 1) * V.PER_CHAMBER
            V.draw_screen(world, V.screen_rect(c), c, state, stage=self.stage,
                          prompt=self._get_objective() if state == "active" else "",
                          answer=self.last_answer.get(last, ""))
            mon = {"active": "active", "accepted": "solved", "standby": "sealed"}[state]
            V.draw_code_monitor(world, c, mon, self._get_code_lines() if mon == "active" else (), self.time)
        for rect, openness in zip(V.GATE_RECTS[:2], self.gate_open[:2]):
            G.draw_gate(world, rect, openness, self.time)
        lamp = theme.mix(theme.CORAL, theme.TEAL, self.gate_open[2])
        G.draw_shutter(world, V.GATE_RECTS[2], self.gate_open[2], lamp)
        G.draw_chevrons(world, self.gate_open[2], self.time)
        standing = {self.pad_at(p) for p, _ in self.players()} - {None}
        colour = V.COLOURS[self.chamber]
        for i, (rect, option) in enumerate(zip(self.pad_rects(), self._get_options())):
            state = "wrong" if i in self.pad_flash else "stand" if i in standing else "idle"
            V.draw_pad(world, rect, option, state, colour, self.time)
        if self.done_pad is not None:
            V.draw_pad(world, self.done_pad[0], self.done_pad[1], "right", colour, self.time)
        V.draw_console(world, self.console_state(), self.time)
        V.draw_readout(world, self.readout(), ui_font(V.READOUT_FONT_SIZE))
        steps = code_font(16).render(f"STAGE {min(self.stage, self.total_stages)}/{self.total_stages}", True, theme.MIST)
        world.blit(steps, (TILE * 2 + 330, TITLE_Y + 8))
        self.draw_dust(world, theme.floor_palette(LEVEL_KEY)["floor"])
        self.draw_sparks(world)
        font = self.line_font if self.line_font.size(self.message)[0] <= 640 else self.small
        self.draw_message(world, self.key_hint(), font, self.small)
        if self.at_terminal:
            V.draw_terminal(world, self.command, self.command_result, self.feedback, self.feedback_good(), self.time)
        self.present(surface, world)
