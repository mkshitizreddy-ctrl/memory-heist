"""
levels/floor5_server.py
Owner: Member 1 - Core Game System (Floor 5 rebuilt on the shared kit)

Floor 5 - WARDEN's Server Hall  (topic: functions and exceptions)

Every machine here is a function, its def stencilled on the casing.  The job
ticket on the wall asks for three jobs, one at a time, and you do them:

    job 1  ROUTER    patch its cable to the port whose value lands in a parameter (arguments)
    job 2  PRESS     route its conveyor to the bay its return value goes to     (return values)
    job 3  REACTOR   pull the except breaker that catches its error, before it  (exceptions)
                     overheats
    then   WARDEN's console: type an access level; the real try/except runs it

    E / Right Shift   act at the port, bay, breaker or console you stand at
    H / TAB           a hint (costs points; off on Hard)
    console           type, ENTER to run, arrow keys step away

Rules: Floor 5's numbers, all from Level5ControlCenter (Apporov's Level 5):
    right job      +40 (less the hint cost if a hint was used)
    wrong choice   security +20, score -10; that choice is ruled out
    reactor trips  security +20, score -10, a new error comes up (job 3 only)
    console        the real try/except; denied or invalid input as before, +50 then +100 on success
    steam vents    score -5 if a vent catches you (score only)

The previous Floor 5 (levels/level5_hall.py) and the original Level 5
(levels/level5_control.py) are untouched; MEMORY_HEIST_OLD_LEVEL5=1 still
returns the original.
"""

import math

import pygame

from core.npc import NPC
from core.tilemap import TILE, TileMap, make_tiles
from levels import badge_door, depth_fx, lighting
from levels import server_decor as S
from levels.level5_control import (
    POINTS_PER_QUESTION, WRONG_SCORE_PENALTY, WRONG_SECURITY, Level5ControlCenter)
from levels.level5_questions import CODE_LINES
from levels.room_base import TITLE_Y, RoomMap, RoomMixin
from levels.server_requests import make_request
from ui import theme
from ui.fonts import ui_font
from ui.kit import shadowed

LEVEL_KEY = "level5"
JOBS = 3
DOOR_SECONDS = 1.2
HEAT_SECONDS = 40                # the reactor's fuse at medium; scaled by the difficulty's timer
VENT_PENALTY = 5
VENT_COOLDOWN = 1.5
WRONG_SECONDS = 0.5
ARROWS = (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT)
AMBIENT = (110, 122, 138)        # cold, blue-grey; the racks and screens do the lighting

IDLE_LINES = ("WARDEN logs everything I do. Everything.", "Every machine is a function. In, out. Simple.",
              "Don't touch the reactor. Please.", "Forty years of uptime. Not on my shift.")
NOTICE_LINES = ("You're not on the rota. Read the ticket, do the job.",
                "Arguments in, return value out. That's the whole hall.",
                "If the reactor raises, catch the right error. Not any error.")
PRAISE = ("Clean call.", "That one returned.", "Caught. Nice.")
SCOLD = ("Wrong port. Parameters go in order.", "Wrong bay. Read the return.", "Wrong breaker! It's still raising!")
FAREWELL = "Go. Before WARDEN reads my logs."


class ServerFloor(RoomMixin, Level5ControlCenter):
    STEP_SOUND = "step_metal"

    def __init__(self, player=None, game=None, seed=None):
        Level5ControlCenter.__init__(self, game=game, seed=seed, finish_delay=0.0)
        self.player = player
        self.init_room(seed)
        self.difficulty = self._difficulty_name()
        self.phase = "questions"
        self.total_steps = JOBS + 1
        self.current_step = 1
        self._steps_done = 0
        self.stage = 0
        self.request = make_request(0, self.rng, self.difficulty)
        self.out = set()                 # choices ruled out on this job
        self.done = {}                   # stage -> index chosen
        self.wrong = {}                  # (stage, index) -> seconds of red flash
        self.heat = 0.0
        self.heat_seconds = max(10, round(HEAT_SECONDS * self._timer_multiplier()))
        self.at_terminal = False
        self.door_open = 0.0
        self.vent_wait = {}
        self.vent_hits = 0
        self.say("Read the job ticket, then do the job. E at the machine's port, bay or breaker.")

        self.tilemap = TileMap(S.layout_rows())
        self.tiles = make_tiles(LEVEL_KEY)
        self.door_block = S.DOOR.copy()
        self.room_map = RoomMap(self.tilemap, S.prop_rects() + [self.door_block])
        self.exit_zone = S.EXIT_ZONE
        self.spawn_points = S.SPAWNS

        self.sysadmin = NPC("sysadmin", S.SYSADMIN_ROUTE[0], patrol=S.SYSADMIN_ROUTE)
        self.npcs = [self.sysadmin]
        self._idle_wait = 10.0
        self._idles = 0
        self._notices = 0
        self._praised = 0

        self.title_font = ui_font(26, bold=True)
        self.line_font = ui_font(22)
        self.small = ui_font(20)
        self._background = None
        self._title = None
        self.lightlayer = lighting.LightLayer(ambient=AMBIENT)

    # --- difficulty -------------------------------------------------------------
    def _timer_multiplier(self):
        from core.difficulty import DIFFICULTIES
        return DIFFICULTIES.get(self.difficulty, {}).get("timer_multiplier", 1.0)

    # --- state the game reads -----------------------------------------------------
    @property
    def movement_locked(self):
        return self.at_terminal

    @property
    def gates_passed(self):
        return self.stage + (1 if self.phase == "done" else 0)

    def is_complete(self):
        return self.complete

    def set_player(self, player):
        self.player = player

    def index_at(self, player, stage=None):
        stage = self.stage if stage is None else stage
        if stage >= JOBS:
            return None
        for i in range(4):
            if S.stand_zone(stage, i).collidepoint(player.rect.center):
                return i
        return None

    # --- input --------------------------------------------------------------------
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN or self.complete:
            return
        if self.at_terminal:
            if event.key in ARROWS:
                self.at_terminal = False
                self.say("You step away from the console.", theme.MIST)
            else:
                self._handle_terminal_key(event)
            return
        if event.key in (pygame.K_h, pygame.K_TAB) and self.phase == "questions":
            self._use_hint(self.request["hint"])
            self.say(self.hint_text if self.hint_text else self.feedback, theme.GOLD if self.hint_text else theme.CORAL)
            return
        for player, key in self.players():
            if event.key != key:
                continue
            if self.phase == "terminal":
                if self.near(player, S.CONSOLE):
                    self.at_terminal = True
                    self.say("Type an access level, then ENTER.", theme.GOLD)
                else:
                    self.say("Walk to WARDEN's console (bottom right) and press E.", theme.MIST)
                continue
            if self.phase != "questions":
                continue
            index = self.index_at(player)
            if index is not None:
                self._choose(index)
                continue
            if any(self.index_at(player, s) is not None for s in range(JOBS) if s != self.stage):
                self.say("That machine is not on the ticket right now.", theme.MIST)
            else:
                self.say("Stand at the machine's port, bay or breaker the ticket asks for, then press E.", theme.MIST)

    # --- the rules ------------------------------------------------------------------
    def _choose(self, index):
        request, stage = self.request, self.stage
        spot = S.targets(stage)[index].center
        if index in self.out:
            self.say("That one is ruled out. Try another.", theme.MIST)
            return
        if index == request["answer"]:
            earned = self._award(POINTS_PER_QUESTION)
            self._finish_step()
            self.done[stage] = index
            self._solved_labels[stage] = list(request["labels"])
            self._solved_machines[stage] = list(request["machine"])
            self.burst(spot, theme.TEAL, 16)
            self.sfx("switch")
            self.sfx("chime")
            self.sysadmin.say(PRAISE[stage])
            self.feedback, self.feedback_good = f"CORRECT! +{earned} points.", True
            self.explanation = request["explain"]
            self.stage += 1
            self.out = set()
            self.heat = 0.0
            self.hint_used, self.hint_text = False, ""
            if self.stage < JOBS:
                self.request = make_request(self.stage, self.rng, self.difficulty)
                self.say(f"+{earned}. {request['explain']} Next job is up.", theme.TEAL)
            else:
                self.phase = "terminal"
                self.terminal_unlocked = True
                self.say(f"+{earned}. {request['explain']} WARDEN's console is unlocked.", theme.GOLD)
        else:
            self.out.add(index)
            self.wrong[(stage, index)] = WRONG_SECONDS
            self.shake.add(0.5)
            self.burst(spot, theme.CORAL, 10)
            self.sysadmin.alert(pygame.Rect(spot, (1, 1)), 1.2)
            self.sysadmin.say(SCOLD[stage])
            self.say("Wrong - that choice is ruled out. H for a hint.", theme.CORAL)
            if self.game:
                self.game.security.increase(WRONG_SECURITY)
                self.game.score.penalize(WRONG_SCORE_PENALTY)

    def _update_heat(self, dt):
        if self.stage != 2 or self.phase != "questions":
            return
        self.heat += dt / self.heat_seconds
        if self.heat >= 1.0:
            self.heat = 0.0
            self.out = set()
            self.request = make_request(2, self.rng, self.difficulty)
            self.shake.add(0.8)
            self.burst(S.MACHINES[2].center, theme.CORAL, 20)
            self.sfx("alarm")
            self.sysadmin.say("It tripped! New fault coming up!")
            self.say("The reactor tripped a fuse. Security up. A new fault is on the ticket.", theme.CORAL)
            if self.game:
                self.game.security.increase(WRONG_SECURITY)
                self.game.score.penalize(WRONG_SCORE_PENALTY)

    def _update_vents(self, dt):
        for player, _ in self.players():
            key = id(player)
            self.vent_wait[key] = max(0.0, self.vent_wait.get(key, 0.0) - dt)
            if self.vent_wait[key] > 0:
                continue
            for i in range(len(S.VENTS)):
                if S.vent_state(i, self.time) == "blow" and S.plume_rect(i).colliderect(player.rect):
                    self.vent_wait[key] = VENT_COOLDOWN
                    self.vent_hits += 1
                    self.shake.add(0.3)
                    self.sfx("zap")
                    self.say(f"Scalded by a cooling vent. -{VENT_PENALTY}. Wait for the hiss to stop.", theme.CORAL)
                    if self.game:
                        self.game.score.penalize(VENT_PENALTY)
                    break

    def _update_npcs(self, dt):
        self.sysadmin.update(dt)
        self._idle_wait -= dt
        if self._idle_wait <= 0 and not self.complete:
            self._idle_wait = 18.0
            if not self.sysadmin.speech:
                self.sysadmin.say(IDLE_LINES[self._idles % len(IDLE_LINES)])
                self._idles += 1
        for player, _ in self.players():
            if self.sysadmin.notice(player.rect, id(player)):
                self.sysadmin.say(NOTICE_LINES[self._notices % len(NOTICE_LINES)])
                self._notices += 1

    # --- the console (Level5ControlCenter's real try/except) ---------------------------
    def _handle_terminal_error(self, err):
        super()._handle_terminal_error(err)
        self.shake.add(0.4)
        self.burst(S.CONSOLE.midtop, theme.CORAL, 10)
        self.sysadmin.say("Exception caught. It's still locked.")

    def _terminal_success(self, result):
        super()._terminal_success(result)
        self.at_terminal = False
        self.complete = False                      # solved, but you still walk out
        self.hint_text = ""
        self.burst(S.CONSOLE.midtop, theme.GOLD, 26)
        self.sfx("door")
        self.sysadmin.say("Master access? It... it worked.")
        self.say("MASTER ACCESS - the vault door is opening.", theme.GOLD)

    def _finish(self):
        self.complete = True
        self.sysadmin.say(FAREWELL)
        self.say("Server hall cleared. On to the vault!", theme.GOLD)

    # --- per frame ----------------------------------------------------------------
    def update(self, dt):
        dt = max(0.0, dt)
        self.update_room(dt)
        self._update_npcs(dt)
        self.wrong = {k: v - dt for k, v in self.wrong.items() if v - dt > 0}
        if self.complete:
            return
        self._update_heat(dt)
        self._update_vents(dt)
        if self.phase == "done":
            self.door_open = min(1.0, self.door_open + dt / DOOR_SECONDS)
            if self.door_open > 0.9:
                self.door_block.size = (0, 0)
                for player, _ in self.players():
                    if player.rect.colliderect(self.exit_zone):
                        self._finish()
                        break

    # --- drawing --------------------------------------------------------------------
    def _build_background(self):
        size = self.tilemap.pixel_size
        bg = pygame.Surface(size)
        cam = type("Cam", (), {})()
        cam.offset = lambda: (0, 0)
        cam.x = cam.y = 0
        cam.view_w, cam.view_h = size
        self.tilemap.render(bg, cam, self.tiles)
        S.draw_static(bg, self.tilemap)
        accent = theme.floor_palette(LEVEL_KEY)["accent"]
        title = shadowed(self.title_font, "FLOOR 5 - SERVER HALL", theme.mix(accent, theme.PAPER, 0.4))
        self._title = (title, (TILE * 2, TITLE_Y))
        self._background = bg

    def _highlight(self):
        for player, _ in self.players():
            index = self.index_at(player)
            if index is not None:
                return index
        return None

    def _lights(self):
        out = [lighting.Light((S.TICKET.centerx, S.TICKET.bottom + 50), 180, S.COLD, 0.55),
               lighting.Light((S.EYE_SCREEN.centerx, S.EYE_SCREEN.bottom + 30), 140, theme.CORAL, 0.5)]
        for k, rect in enumerate(S.MACHINES):
            active = k == self.stage and self.phase == "questions"
            colour = theme.mix(S.COLD, theme.CORAL, self.heat) if k == 2 else S.COLD
            out.append(lighting.Light((rect.centerx, rect.bottom + 16), 130, colour, 0.75 if active else 0.4))
        for rect in S.RACKS:
            out.append(lighting.Light(rect.center, 70, (80, 230, 160), 0.35))
        console = theme.GOLD if self.phase == "terminal" else (theme.TEAL if self.phase == "done" else (60, 70, 90))
        out.append(lighting.Light((S.CONSOLE.centerx, S.CONSOLE.y - 6), 110, console, 0.7))
        for i, (x, y) in enumerate(S.VENTS):
            state = S.vent_state(i, self.time)
            if state != "rest":
                out.append(lighting.Light((x, y), 70, (255, 160, 80) if state == "warn" else (220, 226, 232), 0.6))
        out.append(lighting.Light((S.DOOR.x - 12, S.DOOR.centery), 100, badge_door.lamp_colour(self.door_open), 0.7))
        return out

    def render(self, surface):
        if self._background is None:
            self._build_background()
        world = self._background.copy()
        t = self.time
        depth_fx.motes(world, S.MOTE_AREA, t, count=24, colour=(170, 210, 230), seed=5)
        S.draw_racks_live(world, t)
        here = self._highlight()
        for k in range(JOBS):
            lines = self.request["machine"] if k == self.stage else self._solved_machines.get(k, (
                ("def route(floor, door):", "    lift.go(floor, door)"), ("def press(x):", "    return x"),
                ("def run():", "    reactor.heat()"))[k])
            S.draw_machine(world, k, list(lines), k == self.stage and self.phase == "questions", k in self.done,
                           self.heat if k == 2 else 0.0, t)
        labels = self.request["labels"]
        wrong = {i for (s, i) in self.wrong if s == self.stage}
        S.draw_ports(world, labels if self.stage == 0 else self._done_labels(0), self.out | wrong if self.stage == 0 else set(),
                     here if self.stage == 0 else None, self.done.get(0), t)
        S.draw_conveyor(world, self.done.get(1), t, running=self.stage >= 1)
        S.draw_bays(world, labels if self.stage == 1 else self._done_labels(1), self.out | wrong if self.stage == 1 else set(),
                    here if self.stage == 1 else None, self.done.get(1), t)
        S.draw_breakers(world, labels if self.stage == 2 else self._done_labels(2),
                        self.out | wrong if self.stage == 2 else set(), here if self.stage == 2 else None,
                        self.done.get(2), t)
        S.draw_vents(world, t)
        if self.stage == 2 and self.phase == "questions" and self.heat > 0.4:
            depth_fx.steam(world, (S.MACHINES[2].centerx, S.MACHINES[2].y + 6), t, period=2.0, seed=0.3)
        badge_door.draw_badge_door(world, S.DOOR, self.door_open, t)
        self.draw_dust(world, theme.floor_palette(LEVEL_KEY)["floor"])
        lighting.blob_shadow(world, self.sysadmin.rect, 90)
        self.sysadmin.draw(world, self.small)
        self.draw_sparks(world)
        self.lightlayer.apply(world, self._lights())
        S.draw_eye_screen(world, t, alarm=bool(self.wrong) or self.heat > 0.75)
        S.draw_gauges(world, self.heat if self.stage == 2 else 0.0, self._steps_done, t)
        done_text = {"terminal": "ALL JOBS DONE - WARDEN'S CONSOLE IS OPEN", "done": "MASTER ACCESS GRANTED - TO THE VAULT"}
        S.draw_ticket(world, self.request, min(self.stage + 1, JOBS), JOBS, done_text.get(self.phase), t)
        world.blit(*self._title)
        hint = {"questions": "E: do the job   H: hint", "terminal": "E: use the console",
                "done": "Walk through the vault door"}[self.phase]
        font = self.line_font if self.line_font.size(self.message)[0] <= 860 else self.small
        self.draw_message(world, hint, font, self.small)
        if self.at_terminal:
            S.draw_console_window(world, list(CODE_LINES), self.command, self.command_result, self.feedback,
                                  self.feedback_good, self.hint_text, self.hint_penalty(), t)
        self.present(surface, world)

    def _done_labels(self, stage):
        """Labels stay on a finished machine's ports, bays or breakers; blank before its job."""
        if stage in self.done:
            return self._solved_labels.get(stage, [])
        return []

    @property
    def _solved_labels(self):
        if not hasattr(self, "_labels_kept"):
            self._labels_kept = {}
        return self._labels_kept

    @property
    def _solved_machines(self):
        """The def each machine showed when its job was done; it stays on the casing."""
        if not hasattr(self, "_machines_kept"):
            self._machines_kept = {}
        return self._machines_kept
