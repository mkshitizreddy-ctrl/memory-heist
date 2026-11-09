"""
levels/level2_grid.py
Owner: Member 1 - Core Game System (Level 2 rebuilt on the shared kit)

Floor 2 - Maintenance Grid  (topic: operators)

Three chambers in a row, each sealed behind an energy gate.  The wall screen of
the chamber you are in shows its gate's question; the answers are pads on the
floor.  Stand on a pad and press the action key to answer.

    E            answer on the pad you stand on (player 1)    Right Shift (player 2)
    3 gates      arithmetic, comparison, logic: one question each
    last gate    opens the exit door on the right wall; walk through it

The rules are exactly the old Level 2's, so scores and security stay comparable:
    right answer  + the question's points, the next gate opens, the clock resets
    wrong answer  security +20, score -10, and the hint (if hints are on)
    out of time   security +25, score -15, same question again
    walk out      +100 bonus

The question pool, difficulty filter and per-question clock come from Level 2
itself (levels/level2.py is untouched and returns with MEMORY_HEIST_OLD_LEVEL2=1).
"""

import math

import pygame

from core.npc import NPC
from core.tilemap import TILE, TileMap, make_tiles
from levels import lighting, lobby_juice
from levels import snake_decor as G
from levels.level2 import GATES_PER_LEVEL, POINTS_FALLBACK, Level2
from levels.room_base import MESSAGE_Y, TITLE_Y, RoomMap, RoomMixin
from ui import theme
from ui.fonts import ui_font
from ui.kit import shadowed

LEVEL_KEY = "level2"
FINISH_BONUS = 100
WRONG_SECURITY, WRONG_PENALTY = 20, 10
TIMEOUT_SECURITY, TIMEOUT_PENALTY = 25, 15
GATE_OPEN_RATE = 3.0            # how fast a gate retracts (per second)
FLASH_SECONDS = 0.5             # a wrong pad flashes red this long
DONE_PAD_SECONDS = 0.9          # the pad you got right lingers in green this long
ENGINEER_ROUTE = [(7 * TILE, 9 * TILE), (17 * TILE, 9 * TILE)]
ENGINEER_LINES = ("Brackets first, then **, then * / // %, then + and -.",
                  "Floor panel with a True expression is live. Walk the False one.",
                  "'and' needs both sides live. 'or' needs one.")
PRAISE = ("Power's flowing.", "That relay likes you.")
SCOLD = "That breaker bites. Careful."
FAREWELL = "Mind the next floor."
AMBIENT = (150, 142, 138)       # the tunnel is dim and warm; the bulbs and screens do the lighting
BULB = (255, 190, 110)          # sodium-amber work bulbs
BULB_COLS = ((6, 14, 21), (8, 16, 23), (7, 14, 22))   # three bulbs along each corridor
PANEL_PENALTY = 5               # a live panel costs score only, never security
PANEL_COOLDOWN = 1.5            # seconds before the same player can be zapped again
PANEL_LINE = "Live panel! True means live. Walk the False one."
FUSE_POINTS = 5
FUSE_LINE = "A spare fuse. +5"
FUSE_EMPTY = "The fuse box is empty."
POSTER_OFF = "The poster has peeled off. Unreadable."
POSTERS = ("SAFETY: brackets first, then **, then * / // %, then + and -.",
           "SAFETY: a floor panel with a True expression is live.",
           "SAFETY: 'and' needs both sides True. 'or' needs only one.")
PROP_REACH = 60                 # how close counts as next to the fuse box or poster


class GridRoom(RoomMixin, Level2):
    STEP_SOUND = "step_metal"                      # boots on a steel grating

    def __init__(self, player=None, game=None, seed=None):
        Level2.__init__(self, player, game)        # question pool, difficulty, clock, gate 1
        self.init_room(seed)
        self.message = "Stand on a breaker, then press E to throw it."
        self.message_tone = theme.PAPER
        self.solved = []                           # questions answered, in order
        self.gate_open = [0.0] * GATES_PER_LEVEL
        self.pad_flash = {}                        # wrong pad index -> seconds left
        self.done_pad = None                       # [rect, label, seconds left] of the last right answer

        self.tilemap = TileMap(G.layout_rows())
        self.tiles = make_tiles(LEVEL_KEY)
        self.props = G.rack_rects() + G.desk_rects() + G.transformer_rects()
        self.gate_blocks = [r.copy() for r in G.GATE_RECTS]
        self.room_map = RoomMap(self.tilemap, self.props + self.gate_blocks)
        self.exit_zone = pygame.Rect(28 * TILE + 8, G.GATE_RECTS[2].y, TILE * 2, G.GATE_RECTS[2].h)
        self.spawn_points = G.SPAWNS

        self.engineer = NPC("engineer", ENGINEER_ROUTE[0], patrol=ENGINEER_ROUTE)
        self.npcs = [self.engineer]
        self._engineer_lines = 0
        self._praised = 0
        self.ambience = G.Ambience(seed=21)

        self.title_font = ui_font(26, bold=True)
        self.line_font = ui_font(22)
        self.small = ui_font(20)
        self._background = None
        self._title = None
        self.zap_wait = {}                         # player id -> seconds until they can be zapped again
        self.zaps = 0
        self.panels = G.panel_tiles(self.rng)
        self.panel_state = {}                      # panel index -> "safe" or "live" once someone has tried it
        self.panel_flash = {}                      # panel index -> seconds of crackle left
        self.zap_said = False
        self.fuse_taken = False
        self._poster_reads = 0
        self.lightlayer = lighting.LightLayer(ambient=AMBIENT)

    # --- state ------------------------------------------------------------
    @property
    def gate_index(self):
        """0-based index of the gate being worked on (3 once all are solved)."""
        return self.gates_passed

    def pad_rects(self):
        if self.gates_passed >= GATES_PER_LEVEL:
            return []
        return G.pad_rects(self.gates_passed, len(self.current_question["options"]))

    def pad_at(self, player):
        """Index of the answer pad `player` stands on, or None."""
        for i, rect in enumerate(self.pad_rects()):
            if rect.inflate(8, 8).collidepoint(player.rect.center):
                return i
        return None

    # --- input ------------------------------------------------------------
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN or self.complete:
            return
        for player, key in self.players():
            if event.key != key:
                continue
            index = self.pad_at(player)
            if index is None:
                if self._use_prop(player):
                    continue
                if self.gates_passed < GATES_PER_LEVEL:
                    self.say("Stand on a breaker, then press E.", theme.MIST)
                continue
            self._check_answer(self.current_question, self.current_question["options"][index])

    def _near(self, player, rect):
        return rect.inflate(PROP_REACH, PROP_REACH).colliderect(player.rect)

    def _use_prop(self, player):
        """E beside the fuse box or the safety poster (when not on a breaker plate)."""
        if self._near(player, G.FUSE_BOX):
            self.sfx("switch")
            if self.fuse_taken:
                self.say(FUSE_EMPTY, theme.MIST)
            else:
                self.fuse_taken = True
                if self.game:
                    self.game.score.add(FUSE_POINTS)
                self.burst(G.FUSE_BOX.center, theme.GOLD, 8)
                self.say(FUSE_LINE, theme.GOLD)
            return True
        if self._near(player, G.POSTER):
            if self.game and not self.game.hints.enabled:
                self.say(POSTER_OFF, theme.MIST)
            else:
                self.say(POSTERS[self._poster_reads % len(POSTERS)], theme.GOLD)
                self._poster_reads += 1
            return True
        return False

    # --- the rules (same numbers as the old Level 2) ------------------------
    def _check_answer(self, question, choice):
        """Open a gate on a correct answer; otherwise raise security and show the hint."""
        index = question["options"].index(choice)
        pad = self.pad_rects()[index]
        spot = pad.center
        if choice == question["answer"]:
            self.solved.append(question)
            self.gates_passed += 1
            if self.game:
                self.game.score.add(question.get("points", POINTS_FALLBACK))
            self.burst(spot, theme.TEAL, 18)
            if self.gates_passed >= GATES_PER_LEVEL:
                self.say("All relays live - the exit is open.", theme.GOLD)
            else:
                self.say(f"Relay {self.gates_passed} live. Power gate {self.gates_passed} open.", theme.TEAL)
                self.time_left = self.time_limit
                self._load_question_for_gate(self.gates_passed + 1)
            self.pad_flash = {}
            self.done_pad = [pad, question["options"][index], DONE_PAD_SECONDS]
            self.sfx("switch")                    # the breaker clunks over, then the gate hums open
            self.sfx("door")
            self._praise()
        else:
            if self.game and not self.game.hints.enabled:
                self.say("Wrong. Hints are off on this difficulty.", theme.CORAL)
            else:
                self.say("Wrong. Hint: " + question.get("hint", "Try again."), theme.CORAL)
            self.pad_flash[index] = FLASH_SECONDS
            self.shake.add(0.55)
            self.burst(spot, theme.CORAL, 12)
            self.engineer.say(SCOLD)
            if self.game:
                self.game.security.increase(WRONG_SECURITY)
                self.game.score.penalize(WRONG_PENALTY)

    def _praise(self):
        n = self._praised
        self._praised += 1
        if n % 2 == 0 and self.gates_passed < GATES_PER_LEVEL:
            self.engineer.say(PRAISE[(n // 2) % len(PRAISE)])

    def _tick_timer(self, dt):
        if self.gates_passed >= GATES_PER_LEVEL:
            return
        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = self.time_limit
            self.say("TIME'S UP! Security increased. Try this gate again.", theme.CORAL)
            self.shake.add(0.5)
            if self.game:
                self.game.security.increase(TIMEOUT_SECURITY)
                self.game.score.penalize(TIMEOUT_PENALTY)

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
        self._tick_timer(dt)
        self._update_panels(dt)
        for i in range(GATES_PER_LEVEL):
            target = 1.0 if i < self.gates_passed else 0.0
            self.gate_open[i] += (target - self.gate_open[i]) * min(1.0, dt * GATE_OPEN_RATE)
            if self.gate_open[i] > 0.9:
                self.gate_blocks[i].size = (0, 0)
        if self.gate_open[2] > 0.9:
            for player, _ in self.players():
                if player.rect.colliderect(self.exit_zone):
                    self._finish()
                    break

    def _update_panels(self, dt):
        """Stepping on a live panel (its expression is True) zaps: score only, never security."""
        self.panel_flash = {k: v - dt for k, v in self.panel_flash.items() if v - dt > 0}
        for player, _ in self.players():
            key = id(player)
            self.zap_wait[key] = max(0.0, self.zap_wait.get(key, 0.0) - dt)
            tile = G.panel_under(self.panels, player.rect)
            if tile is None:
                continue
            index = self.panels.index(tile)
            if not tile["live"]:
                self.panel_state.setdefault(index, "safe")
                continue
            if self.zap_wait[key] > 0:
                continue
            self.zap_wait[key] = PANEL_COOLDOWN
            self.zaps += 1
            self.panel_state[index] = "live"
            self.panel_flash[index] = 0.8
            self.shake.add(0.4)
            self.burst(player.rect.center, theme.PAPER, 10)
            self.sfx("zap")
            self.say(f"ZAP! -{PANEL_PENALTY}. {tile['expr']} is True, so it is live.", theme.CORAL)
            self.engineer.alert(player.rect, 1.2)         # he turns to look at the sparks
            self.engineer.say(PANEL_LINE)
            if self.game:
                self.game.score.penalize(PANEL_PENALTY)

    def _update_npcs(self, dt):
        self.engineer.update(dt)
        for player, _ in self.players():
            if self.engineer.notice(player.rect, id(player)):
                self.engineer.say(ENGINEER_LINES[self._engineer_lines % len(ENGINEER_LINES)])
                self._engineer_lines += 1

    def _finish(self):
        self.complete = True
        self.engineer.say(FAREWELL)
        if self.game:
            self.game.score.add(FINISH_BONUS)
        self.say("Grid powered - the way down is open!", theme.GOLD)

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
        G.draw_static(bg, accent)
        title = shadowed(self.title_font, "FLOOR 2 - MAINTENANCE GRID",
                         theme.mix(accent, theme.PAPER, 0.4))
        bg.blit(title, (TILE * 2, TITLE_Y))
        self._title = (title, (TILE * 2, TITLE_Y))
        self._background = bg

    def _lights(self):
        """Every light in the tunnel: relay screens, amber bulbs (one flickers per corridor), gate lamps."""
        accent = theme.floor_palette(LEVEL_KEY)["accent"]
        out = []
        for gate in range(GATES_PER_LEVEL):
            r = G.screen_rect(gate)
            state = self._screen_state(gate)
            colour = theme.TEAL if state == "accepted" else accent
            out.append(lighting.Light((r.centerx, r.bottom + 8), 150, colour, {"active": 0.95, "accepted": 0.6, "standby": 0.35}[state]))
        for corridor, (row, cols) in enumerate(zip(G.LANE_ROW, BULB_COLS)):
            for k, col in enumerate(cols):
                flick = lobby_juice.flicker(self.time, corridor * 4 + 1.7) if k == 1 else 1.0
                out.append(lighting.Light((col * TILE + TILE // 2, row * TILE + TILE // 2), 125, BULB, 0.85 * flick))
        for i, rect in enumerate(G.GATE_RECTS):
            lamp = theme.mix(theme.CORAL, theme.TEAL, self.gate_open[i])
            centre = (rect.x - 10, rect.centery) if i == 2 else rect.center
            out.append(lighting.Light(centre, 85, lamp, 0.65))
        for rack in G.rack_rects():
            out.append(lighting.Light(rack.center, 55, theme.TEAL, 0.35))
        for index in self.panel_flash:                      # only a panel that has just zapped gives off light
            out.append(lighting.Light(self.panels[index]["rect"].center, 95, theme.CORAL, 0.9))
        for desk in G.desk_rects():
            out.append(lighting.Light(desk.center, 90, BULB, 0.7))
        for sep, (lo, hi) in zip(G.SEPARATORS, G.SHAFTS):
            out.append(lighting.Light(((lo + hi + 1) * TILE // 2, sep * TILE + TILE // 2), 90, BULB, 0.5))
        return out

    def _draw_shadows(self, world):
        lighting.blob_shadow(world, self.engineer.rect, 90)
        for rect in G.rack_rects() + G.desk_rects() + G.transformer_rects():
            lighting.blob_shadow(world, rect.inflate(10, 0), 60, squash=0.3)

    def _screen_state(self, gate):
        if gate < self.gates_passed:
            return "accepted"
        if gate == self.gates_passed:
            return "active"
        return "standby"

    def render(self, surface):
        if self._background is None:
            self._build_background()
        world = self._background.copy()
        accent = theme.floor_palette(LEVEL_KEY)["accent"]
        self.ambience.draw(world, accent)
        for gate in range(GATES_PER_LEVEL):
            state = self._screen_state(gate)
            q = self.current_question if state == "active" else (
                self.solved[gate] if state == "accepted" else None)
            G.draw_screen(world, G.screen_rect(gate), gate, state, accent,
                          prompt=q["prompt"] if q and state == "active" else "",
                          answer=q["answer"] if q and state == "accepted" else "",
                          fraction=G.timer_fraction(self.time_left, self.time_limit),
                          seconds=max(0, math.ceil(self.time_left)), time=self.time)
        for gate_rect, openness in zip(G.GATE_RECTS[:2], self.gate_open[:2]):
            G.draw_gate(world, gate_rect, openness, self.time)
        lamp = theme.mix(theme.CORAL, theme.TEAL, self.gate_open[2])
        G.draw_shutter(world, G.GATE_RECTS[2], self.gate_open[2], lamp)
        G.draw_chevrons(world, self.gate_open[2], self.time)
        standing = {self.pad_at(p) for p, _ in self.players()} - {None}
        if self.gates_passed < GATES_PER_LEVEL:
            for i, (rect, option) in enumerate(zip(self.pad_rects(), self.current_question["options"])):
                state = "wrong" if i in self.pad_flash else ("stand" if i in standing else "idle")
                G.draw_pad(world, rect, option, state, accent, self.time)
        if self.done_pad is not None:
            G.draw_pad(world, self.done_pad[0], self.done_pad[1], "right", accent, self.time)
        for index, tile in enumerate(self.panels):
            G.draw_floor_panel(world, tile, self.panel_state.get(index, "unknown"), self.time)
        self.draw_dust(world, theme.floor_palette(LEVEL_KEY)["floor"])
        self._draw_shadows(world)
        self.engineer.draw(world, self.small)
        self.draw_sparks(world)
        self.lightlayer.apply(world, self._lights())
        world.blit(*self._title)                  # the title stays readable above the lighting
        self.draw_message(world, "E: throw the breaker", self.line_font, self.small)
        self.present(surface, world)
