"""
levels/level5_hall.py
Owner: Member 4 - Apporov Sahu's Level 5, rebuilt as a walkable floor

Floor 5 - Server Hall  (topic: functions and exceptions)

Three chambers in a row, each sealed behind an energy gate.  The program is on the
wall and the question of the chamber you are in is on its screen; the answers are
pads on the floor.  Stand on a pad and press the action key to answer.

    E            answer on the pad you stand on (player 1)    Right Shift (player 2)
    H / TAB      show a hint (costs points; switched off on Hard)
    gate 1       PARAMETERS   2 questions      gate 2   RETURN   2 questions
    gate 3       EXCEPTIONS   1 question, then the control terminal:
                 walk to the console, press E, type an access level, ENTER.
                 Arrow keys step away from it.  The exit door opens when it accepts you.

The rules are exactly the old Level 5's.  Scores, penalties, hints and the real
try/except in the terminal all come from Level5ControlCenter, which this class
extends; only the way you give your answers has changed.  levels/level5_control.py
is untouched and returns with MEMORY_HEIST_OLD_LEVEL5=1.
"""

import pygame

from core.npc import NPC
from core.tilemap import TILE, TileMap, make_tiles
from levels import hall_decor as H
from levels import grid_decor as G
from levels.level5_control import Level5ControlCenter
from levels.level5_questions import GATES
from levels.room_base import MESSAGE_Y, TITLE_Y, RoomMap, RoomMixin
from ui import theme
from ui.fonts import code_font, ui_font
from ui.kit import shadowed

LEVEL_KEY = "level5"
GATE_COUNT = len(GATES)
GATE_OPEN_RATE = 3.0            # how fast a gate retracts (per second)
FLASH_SECONDS = 0.5             # a wrong pad flashes red this long
DONE_PAD_SECONDS = 0.9          # the pad you got right lingers in green this long
ARROWS = (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)
TECH_ROUTE = [(12 * TILE, 16 * TILE), (17 * TILE, 16 * TILE)]
TECH_LINES = ("A parameter is the name in the def.", "An argument is the value you pass in.",
              "return hands a value back.", "try the risky line. except catches it.")
PRAISE = ("Clean call.", "That one returned.")
SCOLD = "Exception raised. Careful."
FAREWELL = "Mind the vault."
TERMINAL_TIP = "Walk to the control terminal (bottom right) and press E."


class ServerHall(RoomMixin, Level5ControlCenter):
    def __init__(self, player=None, game=None, seed=None):
        Level5ControlCenter.__init__(self, game=game, seed=seed, finish_delay=0.0)
        self.player = player
        self.init_room(seed)
        self.say("Stand on the right answer, then press E.")
        self.at_terminal = False                   # a player is typing at the console
        self.gate_open = [0.0] * GATE_COUNT
        self.pad_flash = {}                        # wrong pad index -> seconds left
        self.done_pad = None                       # [rect, label, seconds left] of the last right answer
        self.last_answer = {}                      # gate -> the answer that opened it

        self.tilemap = TileMap(H.layout_rows())
        self.tiles = make_tiles(LEVEL_KEY)
        self.props = H.solid_props()
        self.gate_blocks = [r.copy() for r in H.GATE_RECTS]
        self.room_map = RoomMap(self.tilemap, self.props + self.gate_blocks)
        self.exit_zone = pygame.Rect(28 * TILE + 8, H.GATE_RECTS[2].y, TILE * 2, H.GATE_RECTS[2].h)
        self.spawn_points = H.SPAWNS

        self.technician = NPC("technician", TECH_ROUTE[0], patrol=TECH_ROUTE)
        self.npcs = [self.technician]
        self._tech_lines = 0
        self._praised = 0
        self.ambience = H.Ambience(seed=51)

        self.title_font = ui_font(26, bold=True)
        self.line_font = ui_font(22)
        self.small = ui_font(20)
        self._background = None

    # --- state ------------------------------------------------------------
    @property
    def movement_locked(self):
        """Game stops walking while someone types at the terminal."""
        return self.at_terminal

    @property
    def gates_passed(self):
        """Gates opened so far (3 once the terminal has accepted you)."""
        return GATE_COUNT if self.phase == "done" else self.gate_index

    def pad_rects(self):
        if self.phase != "questions":
            return []
        return H.pad_rects(self.gate_index, len(self.options))

    def pad_at(self, player):
        """Index of the answer pad `player` stands on, or None."""
        for i, rect in enumerate(self.pad_rects()):
            if rect.inflate(8, 8).collidepoint(player.rect.center):
                return i
        return None

    def console_state(self):
        if self.phase == "done":
            return "done"
        if self.at_terminal:
            return "active"
        return "ready" if self.phase == "terminal" else "locked"

    # --- input ------------------------------------------------------------
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN or self.complete:
            return
        if self.phase == "questions":
            self._question_event(event)
        elif self.phase == "terminal":
            if self.at_terminal:
                self._terminal_event(event)
            else:
                self._console_event(event)

    def _question_event(self, event):
        if event.key in (pygame.K_h, pygame.K_TAB):
            self._use_hint(self.question.hint)
            self.say(self.feedback, theme.GOLD if self.feedback_good else theme.CORAL)
            return
        for player, key in self.players():
            if event.key != key:
                continue
            index = self.pad_at(player)
            if index is None:
                self.say("Stand on an answer pad, then press E.", theme.MIST)
                continue
            self._press_pad(index)

    def _console_event(self, event):
        for player, key in self.players():
            if event.key != key:
                continue
            if self.near(player, H.CONSOLE):
                self.at_terminal = True
                self.say("Type an access level, then ENTER.", theme.GOLD)
            else:
                self.say(TERMINAL_TIP, theme.MIST)

    def _terminal_event(self, event):
        if event.key in ARROWS:
            self.at_terminal = False
            self.say("You step away from the terminal.", theme.MIST)
            return
        self._handle_terminal_key(event)

    # --- the rules (all from Level5ControlCenter) ---------------------------
    def _press_pad(self, index):
        if index in self.eliminated:
            self.say("That option is ruled out. Try another pad.", theme.MIST)
            return
        pad = self.pad_rects()[index]
        label = self.options[index]
        gate = self.gate_index
        right = index == self.correct_option
        self._answer(index)
        if right:
            self.last_answer[gate] = label
            self.pad_flash = {}
            self.done_pad = [pad, label, DONE_PAD_SECONDS]
            self.burst(pad.center, theme.TEAL, 18)
            self.sfx("door")
            self.say(self.feedback, theme.GOLD if self.phase == "terminal" else theme.TEAL)
            self._praise()
        else:
            self.pad_flash[index] = FLASH_SECONDS
            self.shake.add(0.55)
            self.burst(pad.center, theme.CORAL, 12)
            self.say(self.feedback, theme.CORAL)
            self.technician.say(SCOLD)

    def _handle_terminal_error(self, err):
        super()._handle_terminal_error(err)
        self.shake.add(0.4)
        self.burst(H.CONSOLE.midtop, theme.CORAL, 10)
        self.technician.say(SCOLD)

    def _terminal_success(self, result):
        super()._terminal_success(result)
        self.at_terminal = False
        self.complete = False                      # solved, but you still have to walk out
        self.hint_text = ""                        # the readout now explains what just ran
        self.burst(H.CONSOLE.midtop, theme.GOLD, 26)
        self.sfx("door")
        self.say("CONTROL CENTER RESTORED - the exit is open.", theme.GOLD)

    def _praise(self):
        n = self._praised
        self._praised += 1
        if n % 2 == 0 and self.phase == "questions":
            self.technician.say(PRAISE[(n // 2) % len(PRAISE)])

    # --- per frame ----------------------------------------------------------
    def update(self, dt):
        dt = max(0.0, dt)
        self.update_room(dt)
        self.ambience.update(dt)
        self._update_npcs(dt)
        self.pad_flash = {i: left - dt for i, left in self.pad_flash.items() if left - dt > 0}
        if self.done_pad is not None:
            self.done_pad[2] -= dt
            if self.done_pad[2] <= 0:
                self.done_pad = None
        if self.complete:
            return
        targets = (self.gate_index >= 1, self.gate_index >= 2, self.phase == "done")
        for i, want in enumerate(targets):
            self.gate_open[i] += ((1.0 if want else 0.0) - self.gate_open[i]) * min(1.0, dt * GATE_OPEN_RATE)
            if self.gate_open[i] > 0.9:
                self.gate_blocks[i].size = (0, 0)
        if self.gate_open[2] > 0.9:
            for player, _ in self.players():
                if player.rect.colliderect(self.exit_zone):
                    self._finish()
                    break

    def _update_npcs(self, dt):
        self.technician.update(dt)
        for player, _ in self.players():
            if self.technician.notice(player.rect, id(player)):
                self.technician.say(TECH_LINES[self._tech_lines % len(TECH_LINES)])
                self._tech_lines += 1

    def _finish(self):
        self.complete = True
        self.technician.say(FAREWELL)
        self.say("Control center restored - on to the vault!", theme.GOLD)

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
        H.draw_static(bg, accent)
        title = shadowed(self.title_font, "FLOOR 5 - SERVER HALL", theme.mix(accent, theme.PAPER, 0.4))
        bg.blit(title, (TILE * 2, TITLE_Y))
        self._background = bg

    def _screen_state(self, gate):
        if gate < self.gate_index or (gate == GATE_COUNT - 1 and self.phase != "questions"):
            return "accepted"
        return "active" if gate == self.gate_index else "standby"

    def key_hint(self):
        if self.phase == "questions":
            return "E: answer on a pad   H: hint"
        if self.phase == "terminal":
            return "Type, ENTER to run" if self.at_terminal else "E: use the terminal"
        return "Walk through the exit"

    def readout(self):
        """(text, colour) lines for the strip on the south wall."""
        entries = [(self.hint_text, theme.GOLD), (self.explanation, theme.MIST)]
        if not any(text for text, _ in entries):
            tip = {"questions": "Stand on a pad and press E. H shows a hint. The lit lines are the code the question is about.",
                   "terminal": TERMINAL_TIP, "done": "Walk through the open door on the right."}[self.phase]
            entries = [(tip, theme.MIST)]
        return H.readout_lines(entries, ui_font(H.READOUT_FONT_SIZE), H.READOUT.w - 24 - 70)

    def render(self, surface):
        if self._background is None:
            self._build_background()
        world = self._background.copy()
        accent = theme.floor_palette(LEVEL_KEY)["accent"]
        self.ambience.draw(world, accent)
        for gate in range(GATE_COUNT):
            state = self._screen_state(gate)
            H.draw_screen(world, H.screen_rect(gate), gate, state,
                          prompt=self.question.prompt if state == "active" else "",
                          index=self.question_index, count=len(self.gate_questions[gate]),
                          answer=self.last_answer.get(gate, ""), time=self.time)
        for rect, openness in zip(H.GATE_RECTS[:2], self.gate_open[:2]):
            G.draw_gate(world, rect, openness, self.time)
        lamp = theme.mix(theme.CORAL, theme.TEAL, self.gate_open[2])
        G.draw_shutter(world, H.GATE_RECTS[2], self.gate_open[2], lamp)
        G.draw_chevrons(world, self.gate_open[2], self.time)
        standing = {self.pad_at(p) for p, _ in self.players()} - {None}
        colour = GATES[self.gate_index]["color"]
        for i, (rect, option) in enumerate(zip(self.pad_rects(), self.options)):
            state = ("wrong" if i in self.pad_flash else "out" if i in self.eliminated
                     else "stand" if i in standing else "idle")
            H.draw_pad(world, rect, option, state, colour, self.time)
        if self.done_pad is not None:
            H.draw_pad(world, self.done_pad[0], self.done_pad[1], "right", colour, self.time)
        H.draw_console(world, self.console_state(), self.time)
        H.draw_code_blocks(world, self._highlighted_lines(), self.time)
        H.draw_readout(world, self.readout(), ui_font(H.READOUT_FONT_SIZE))
        steps = code_font(16).render(f"STEP {min(self.current_step, self.total_steps)}/{self.total_steps}",
                                     True, theme.MIST)
        world.blit(steps, (TILE * 2 + 330, TITLE_Y + 8))
        self.draw_dust(world, theme.floor_palette(LEVEL_KEY)["floor"])
        self.technician.draw(world, self.small)
        self.draw_sparks(world)
        font = self.line_font if self.line_font.size(self.message)[0] <= 640 else self.small
        self.draw_message(world, self.key_hint(), font, self.small)
        if self.at_terminal:
            H.draw_terminal(world, self.command, self.command_result, self.feedback, self.feedback_good,
                            self.hint_text, self.hint_penalty(), self.time)
        self.present(surface, world)
