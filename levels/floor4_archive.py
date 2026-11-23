"""
levels/floor4_archive.py
Owner: Member 1 - Core Game System (Floor 4 rebuilt on the shared kit)

Floor 4 - The Records Archive  (topic: lists, dictionaries and loops)

NovaCorp keeps a file on every citizen down here, and Ghost's stolen memory sits
in the vault at the far end.  The request slip on the wall asks for four things,
one at a time, and you answer each by doing it:

    request 1   pull Ghost's dossier from the shelf          (a list index:   shelf[-2])
    request 2   open the right card-catalogue drawer         (a dictionary:   codes[name])
    request 3   feed one item from your satchel to the vault (a list method:  satchel.pop())
    request 4   set the vault's dial: the number the slip's loop leaves in it (a loop)

    E / Right Shift   pull, open or feed at the thing you stand in front of
    Q                 Echo's drone scans the slip for a hint (once per slip, hints on)
    X                 Echo's drone lures the security drone away for a few seconds

Rules (Floor 4's original numbers):
    right answer   +40, the next request comes up, the clock resets
    wrong answer   security +15, score -10, the same request stays
    out of time    security +25, score -15, a new slip
    security drone score -10 (hard -15) when it catches you in its light (score only);
                   easy runs the loop slowly with long pauses, medium runs it faster,
                   hard roams it and scans at corners.  A red warning comes first.
    walk out       +100 bonus

The original Level 4 stays in levels/legacy/level4_memory.py and returns with
MEMORY_HEIST_OLD_LEVEL4=1.
"""

import math

import pygame

from core.npc import NPC
from core.tilemap import TILE, TileMap, make_tiles
from entities.sprites import draw_drone
from levels import archive_decor as A
from levels import badge_door, depth_fx, lighting
from levels.archive_requests import DIAL_TRAYS, START_SATCHEL, make_request, why_wrong
from levels.room_base import MESSAGE_Y, TITLE_Y, RoomMap, RoomMixin
from ui import theme
from ui.fonts import ui_font
from ui.kit import shadowed

LEVEL_KEY = "level4"
REQUESTS = 4
POINTS = 40
FINISH_BONUS = 100
WRONG_SECURITY, WRONG_PENALTY = 15, 10
TIMEOUT_SECURITY, TIMEOUT_PENALTY = 25, 15
MESSAGE_CHARS = 108                 # what fits on the one message line under the title
EASY_TIMEOUT_SECURITY = 20           # easy is a little gentler on a slip that runs out
BASE_SECONDS = 45
DOOR_SECONDS = 1.2
WARN_SECONDS = 5                 # the last seconds tick and the slip pulses red
SLIP_DROP_SECONDS = 0.45
DRONE_PENALTY = 10               # the medium (default) numbers; DRONE_SETTINGS has all three
DRONE_RANGE = 78                 # its searchlight's reach
DRONE_COOLDOWN = 3.0
DRONE_GRACE = 2.0                # it cannot log you in the first moments
LURE_SECONDS = 3.0
LURE_COOLDOWN = 15.0
DRONE_SETTINGS = {
    # route: "aisle" patrols back and forth, "loop" follows the route, "roam" picks its way round it
    "easy": {"speed": 70.0, "reach": 70, "grace": 2.5, "penalty": 10, "lure_seconds": 4.0,
             "lure_cooldown": 12.0, "lock": 0.6, "route": "loop", "pause": 1.2},
    "medium": {"speed": 105.0, "reach": DRONE_RANGE, "grace": DRONE_GRACE, "penalty": DRONE_PENALTY,
               "lure_seconds": LURE_SECONDS, "lure_cooldown": LURE_COOLDOWN, "lock": 0.4, "route": "loop", "pause": 0.8},
    "hard": {"speed": 125.0, "reach": 90, "grace": 1.5, "penalty": 15, "lure_seconds": 2.5,
             "lure_cooldown": 20.0, "lock": 0.4, "route": "roam"},
}
LOCK_DECAY = 2.0                 # the red warning fades twice as fast as it builds
WRONG_SECONDS = 0.5
AMBIENT = (128, 126, 140)        # a dim, dusty hall; the lamps do the work
LAMP = (210, 230, 150)           # banker's lamps: green glass, warm bulb
SLIP_LIGHT = (240, 236, 214)

IDLE_LINES = ("Index from zero. Always zero.", "Every citizen has a file. Every file has a key.",
              "Quiet. The records are listening.", "Who left a drawer open?")
NOTICE_LINES = ("Courier? Requests come through the slip.", "Read the slip. Then touch nothing else.",
                "The shelf counts from zero, courier.")
PRAISE = ("Filed correctly.", "Accurate. How rare.")
SCOLD = ("That is not the box on the slip.", "Wrong drawer. Keys are exact.", "The vault does not take that.",
         "The dial does not turn to that. Count the passes.")
FAREWELL = "Your file has been... updated."
NOT_YET = ("Not on the slip yet.", "The slip is not asking for that yet.")
DONE_LINE = "Already filed."


class ArchiveFloor(RoomMixin):
    STEP_SOUND = "step"

    def __init__(self, player=None, game=None, seed=None):
        self.player = player
        self.game = game
        self.complete = False
        self.init_room(seed)
        self.difficulty = self._difficulty()
        self.time_limit = max(1, round(BASE_SECONDS * self._timer_multiplier()))
        self.time_left = self.time_limit

        self.stage = 0
        self.satchel = list(START_SATCHEL)
        self.request = make_request(0, self.rng, self.satchel, self.difficulty)
        self.scanned = False
        self.misses = 0                   # wrong answers on the current slip
        self.slip_drop = 0.0              # 0 -> 1 as a new slip drops out of the tube
        self._last_tick = None
        self.say("Read the request slip, then do what it asks. E to act.", theme.PAPER)

        self.tilemap = TileMap(A.layout_rows())
        self.tiles = make_tiles(LEVEL_KEY)
        self.door_block = A.DOOR.copy()
        self.room_map = RoomMap(self.tilemap, A.prop_rects() + [self.door_block])
        self.exit_zone = A.EXIT_ZONE
        self.spawn_points = A.SPAWNS
        self.door_open = 0.0

        self.archivist = NPC("archivist", A.ARCHIVIST_ROUTE[0], patrol=A.ARCHIVIST_ROUTE)
        self.npcs = [self.archivist]
        self._idle_wait = 9.0
        self._idles = 0
        self._notices = 0
        self._praised = 0

        self.drone_cfg = DRONE_SETTINGS[self.difficulty]
        self.drone_reach = self.drone_cfg["reach"]
        self.drone = self._make_drone()
        self.drone_grace = self.drone_cfg["grace"]
        self.drone_lock = {}             # player id -> seconds inside the light (the red warning)
        self.drone_wait = {}             # player id -> seconds until the drone can log them again
        self.drone_hits = 0
        self.lure_left = 0.0
        self.lure_cooldown = 0.0
        start = player.rect.center if player is not None else A.SPAWNS[0]
        self.echo = [float(start[0] - 26), float(start[1] - 30)]

        self.pulled = {}                 # box index -> 0..1 slid out
        self.opened = {}                 # drawer index -> 0..1 pulled out
        self.fed = {}                    # tray index -> 0..1 swallowed by the vault
        self.wrong = {}                  # (stage, index) -> seconds of red flash
        self.card = None                 # the card from the right drawer
        self.solved = []                 # requests answered, in order

        self.title_font = ui_font(26, bold=True)
        self.line_font = ui_font(22)
        self.small = ui_font(20)
        self._background = None
        self._title = None
        self.lightlayer = lighting.LightLayer(ambient=AMBIENT)

    # --- difficulty -------------------------------------------------------------
    def _make_drone(self):
        cfg = self.drone_cfg
        if cfg["route"] == "aisle":
            return A.Drone(speed=cfg["speed"])
        pauses = {i: cfg["pause"] for i in A.ROUTE_CORNERS} if cfg["route"] == "loop" else None
        return A.Drone(speed=cfg["speed"], route=A.DRONE_ROUTE, rng=self.rng,
                       roam=cfg["route"] == "roam", pauses=pauses)

    def _difficulty(self):
        value = getattr(self.game, "difficulty", None)
        if isinstance(value, dict):
            value = value.get("name", value.get("label"))
        value = str(value or "medium").lower().strip()
        return value if value in {"easy", "medium", "hard"} else "medium"

    def _timer_multiplier(self):
        from core.difficulty import question_time_multiplier
        return question_time_multiplier(self.difficulty)

    def _hints_on(self):
        hints = getattr(self.game, "hints", None)
        return True if hints is None else bool(getattr(hints, "enabled", True))

    # --- state the game reads ---------------------------------------------------
    @property
    def gates_passed(self):
        """Requests filed so far: the comms feed and HUD watch this."""
        return min(self.stage, REQUESTS)

    def is_complete(self):
        return self.complete

    def set_player(self, player):
        self.player = player

    # --- where the players stand ------------------------------------------------
    def target_count(self):
        return len(self.request["labels"]) if self.stage < REQUESTS else 0

    def index_at(self, player, stage=None):
        """Index of the box / drawer / tray `player` stands in front of for `stage`, or None."""
        stage = self.stage if stage is None else stage
        if stage >= REQUESTS:
            return None
        count = 5 if stage == 0 else (4 if stage == 1 else DIAL_TRAYS)
        for i in range(count):
            if A.stand_zone(stage, i).collidepoint(player.rect.center):
                return i
        return None

    # --- input --------------------------------------------------------------------
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN or self.complete:
            return
        if event.key == pygame.K_q:
            self._scan()
            return
        if event.key == pygame.K_x:
            self._lure()
            return
        for player, key in self.players():
            if event.key != key:
                continue
            index = self.index_at(player)
            if index is not None:
                self._answer(index)
                continue
            for other in range(REQUESTS):
                if other != self.stage and self.index_at(player, other) is not None:
                    self.say(DONE_LINE if other < self.stage else NOT_YET[other % 2], theme.MIST)
                    break
            else:
                if self.stage < REQUESTS:
                    self.say("Stand in front of what the slip asks for, then press E.", theme.MIST)

    def _scan(self):
        if self.stage >= REQUESTS:
            return
        if not self._hints_on():
            self.say("Echo: the scanner is jammed on this difficulty.", theme.MIST)
            return
        if self.scanned:
            self.say("Echo: I already scanned this slip. " + self.request["hint"], theme.GOLD)
            return
        self.scanned = True
        self.sfx("click")
        self.say("Echo: " + self.request["hint"], theme.GOLD)

    def _lure(self):
        if self.lure_cooldown > 0:
            self.say(f"Echo: drone recharging, {math.ceil(self.lure_cooldown)}s.", theme.MIST)
            return
        px = self.player.rect.centerx if self.player is not None else A.DRONE_X[0]
        if self.drone.route:                                  # the far corner of its route, by its own legs
            here = self.player.rect.center if self.player is not None else (px, A.DRONE_Y)
            self.drone.lure = self.drone.lure_toward(here)
        else:
            far = A.DRONE_X[1] if px < 15 * TILE else A.DRONE_X[0]
            self.drone.lure = (far, A.DRONE_Y)                # along its own aisle, never over the stacks
        self.lure_left = self.drone_cfg["lure_seconds"]
        self.lure_cooldown = self.drone_cfg["lure_cooldown"]
        self.sfx("click")
        self.say("Echo: pulling the drone away. Go.", theme.TEAL)

    # --- the rules ----------------------------------------------------------------
    def _answer(self, index):
        request = self.request
        stage = self.stage
        spot = A.targets(stage, len(request["labels"]))[index].center
        if index == request["answer"]:
            self.solved.append(request)
            if self.game:
                self.game.score.add(POINTS)
            self.burst(spot, A.PAPER, 18)                    # loose file pages
            self.burst(spot, theme.GOLD, 6)
            self.sfx("switch")
            self.sfx("chime")
            self._praise()
            if stage == 0:
                self.pulled[index] = 0.01
            elif stage == 1:
                self.opened[index] = 0.01
                self.card = request["take"]
            else:
                self.fed[index] = 0.01
            if request["take"] is not None:
                self.satchel.append(request["take"])
            elif stage == 2 and 0 <= index < len(self.satchel):
                self.satchel.pop(index)
            self.stage += 1
            self.scanned = False
            self.misses = 0
            if self.stage == 3:
                self.fed = {}                                 # the same trays now carry the dial            self.time_left = self.time_limit
            if self.stage < REQUESTS:
                self.request = make_request(self.stage, self.rng, self.satchel, self.difficulty)
                self.slip_drop = 0.0
                self.say_answer(f"{request['explain']}  Next request is up.", theme.TEAL)
            else:
                self.say_answer(f"{request['explain']}  The vault door is opening.", theme.GOLD)
                self.sfx("door")
        else:
            self.wrong[(stage, index)] = WRONG_SECONDS
            self.shake.add(0.5)
            self.burst(spot, theme.CORAL, 10)
            self.archivist.say(SCOLD[stage])
            self.misses += 1
            if self._hints_on():
                if self.misses == 1:
                    # the reason, plus the hint when both fit on the one message line
                    text = f"Wrong. {why_wrong(request, index)}"
                    if len(text) + len(request["hint"]) + 2 <= MESSAGE_CHARS:
                        text += f"  {request['hint']}"
                else:
                    text = f"Wrong again. {request['walk']}"
                self.say_answer(text, theme.CORAL)
            else:
                self.say_answer("Wrong. Read the slip again.", theme.CORAL)
            if self.game:
                self.game.security.increase(WRONG_SECURITY)
                self.game.score.penalize(WRONG_PENALTY)

    def _praise(self):
        self.archivist.say(PRAISE[self._praised % len(PRAISE)])
        self._praised += 1

    def _tick_timer(self, dt):
        if self.stage >= REQUESTS:
            return
        dt = self.clock_dt(dt)                  # held while the last answer's feedback is read
        self.time_left -= dt
        whole = math.ceil(self.time_left)
        if 0 < whole <= WARN_SECONDS and whole != self._last_tick:
            self._last_tick = whole
            self.sfx("click")                               # the slip's clock ticks out loud near the end
        if self.time_left <= 0:
            self.time_left = self.time_limit
            self.request = make_request(self.stage, self.rng, self.satchel, self.difficulty)
            self.scanned = False
            self.misses = 0
            self.slip_drop = 0.0
            self.say("TIME'S UP! Security increased. A new slip came down the tube.", theme.CORAL)
            self.shake.add(0.5)
            if self.game:
                self.game.security.increase(
                    EASY_TIMEOUT_SECURITY if self.difficulty == "easy" else TIMEOUT_SECURITY)
                self.game.score.penalize(TIMEOUT_PENALTY)

    def _update_drone(self, dt):
        self.drone_grace = max(0.0, self.drone_grace - dt)
        self.lure_cooldown = max(0.0, self.lure_cooldown - dt)
        if self.lure_left > 0:
            self.lure_left -= dt
            if self.lure_left <= 0:
                self.drone.lure = None
        self.drone.update(dt)
        if self.drone.lure is not None or self.drone_grace > 0:
            self.drone_lock.clear()
            return
        lock_needed = self.drone_cfg["lock"]
        for player, _ in self.players():
            key = id(player)
            self.drone_wait[key] = max(0.0, self.drone_wait.get(key, 0.0) - dt)
            if self.drone_wait[key] > 0:
                continue
            inside = math.dist(player.rect.center, self.drone.centre) <= self.drone_reach
            if not inside:
                self.drone_lock[key] = max(0.0, self.drone_lock.get(key, 0.0) - dt * LOCK_DECAY)
                continue
            self.drone_lock[key] = self.drone_lock.get(key, 0.0) + dt
            if self.drone_lock[key] < lock_needed:
                continue                                      # the light is red: step out of it
            self.drone_lock[key] = 0.0
            self.drone_wait[key] = DRONE_COOLDOWN
            self.drone_hits += 1
            self.drone.noticed(player.rect.center)
            self.shake.add(0.3)
            self.sfx("alarm")
            penalty = self.drone_cfg["penalty"]
            self.say(f"The security drone logged you. -{penalty}. Press X to lure it.", theme.CORAL)
            if self.game:
                self.game.score.penalize(penalty)

    def _update_npcs(self, dt):
        self.archivist.update(dt)
        self._idle_wait -= dt
        if self._idle_wait <= 0 and not self.complete:
            self._idle_wait = 17.0
            if not self.archivist.speech:
                self.archivist.say(IDLE_LINES[self._idles % len(IDLE_LINES)])
                self._idles += 1
        for player, _ in self.players():
            if self.archivist.notice(player.rect, id(player)):
                self.archivist.say(NOTICE_LINES[self._notices % len(NOTICE_LINES)])
                self._notices += 1

    def _update_echo(self, dt):
        if self.drone.lure is not None:
            goal = (self.drone.lure[0] + (30 if self.drone.lure[0] < 15 * TILE else -30), self.drone.lure[1] - 18)
        elif self.player is not None:
            goal = (self.player.rect.centerx - 26, self.player.rect.centery - 30)
        else:
            return
        k = min(1.0, dt * 4.0)
        self.echo[0] += (goal[0] - self.echo[0]) * k
        self.echo[1] += (goal[1] - self.echo[1]) * k

    def update(self, dt):
        dt = max(0.0, dt)
        self.update_room(dt)
        self._update_npcs(dt)
        self._update_echo(dt)
        for table in (self.pulled, self.opened, self.fed):
            for k in table:
                table[k] = min(1.0, table[k] + dt * 3)
        self.wrong = {k: v - dt for k, v in self.wrong.items() if v - dt > 0}
        self.slip_drop = min(1.0, self.slip_drop + dt / SLIP_DROP_SECONDS)
        if self.complete:
            return
        self._tick_timer(dt)
        self._update_drone(dt)
        if self.stage >= REQUESTS:
            self.door_open = min(1.0, self.door_open + dt / DOOR_SECONDS)
            if self.door_open > 0.9:
                self.door_block.size = (0, 0)
                for player, _ in self.players():
                    if player.rect.colliderect(self.exit_zone):
                        self._finish()
                        break

    def _finish(self):
        self.complete = True
        self.archivist.say(FAREWELL)
        if self.game:
            self.game.score.add(FINISH_BONUS)
        self.say("Memory recovered. The way down is open.", theme.GOLD)

    # --- drawing --------------------------------------------------------------------
    def _build_background(self):
        size = self.tilemap.pixel_size
        bg = pygame.Surface(size)
        cam = type("Cam", (), {})()
        cam.offset = lambda: (0, 0)
        cam.x = cam.y = 0
        cam.view_w, cam.view_h = size
        self.tilemap.render(bg, cam, self.tiles)
        A.draw_static(bg, self.tilemap)
        accent = theme.floor_palette(LEVEL_KEY)["accent"]
        title = shadowed(self.title_font, "FLOOR 4 - RECORDS ARCHIVE", theme.mix(accent, theme.PAPER, 0.4))
        self._title = (title, (TILE * 2, TITLE_Y))
        self._background = bg

    def _highlight(self):
        for player, _ in self.players():
            index = self.index_at(player)
            if index is not None:
                return index
        return None

    def _lights(self):
        out = [lighting.Light((A.SLIP.centerx, A.SLIP.bottom + 70), 200, SLIP_LIGHT, 0.5),
               lighting.Light((A.CATALOGUE_SIGN.centerx, A.CATALOGUE_SIGN.y - 10), 150, (230, 220, 190), 0.55)]
        for k, pos in enumerate(A.LAMPS):
            out.append(lighting.Light(pos, 95, LAMP, 0.85))
        for k, pos in enumerate(A.CEILING):
            flick = depth_fx._hash(int(self.time * 6) + k * 11) > 0.08 if k == 4 else 1.0
            out.append(lighting.Light(pos, 120, (200, 196, 176), 0.45 * flick))
        out.append(lighting.Light((A.CATALOGUE.centerx, A.CATALOGUE.bottom + 10), 130, (230, 200, 140), 0.8))
        out.append(lighting.Light((A.COUNTER.centerx, A.COUNTER.y - 4), 110, theme.TEAL, 0.5))
        door = badge_door.lamp_colour(self.door_open if self.stage >= REQUESTS else 0.0)
        out.append(lighting.Light((A.DOOR.x - 12, A.DOOR.centery), 100, door, 0.7))
        alert = any(v > DRONE_COOLDOWN - 0.6 for v in self.drone_wait.values())
        warning = any(v > 0 for v in self.drone_lock.values())      # the red warning before a log
        out.append(lighting.Light((self.drone.centre[0], self.drone.centre[1] + 14), self.drone_reach + 10,
                                  theme.CORAL if (alert or warning) else (210, 220, 240), 0.8))
        out.append(lighting.Light((int(self.echo[0]), int(self.echo[1])), 50, theme.TEAL, 0.5))
        return out

    def render(self, surface):
        if self._background is None:
            self._build_background()
        world = self._background.copy()
        t = self.time
        depth_fx.motes(world, A.MOTE_AREA, t, count=34, colour=(214, 206, 180), seed=4)
        here = self._highlight()
        wrong0 = {i for (s, i) in self.wrong if s == 0}
        wrong1 = {i for (s, i) in self.wrong if s == 1}
        wrong2 = {i for (s, i) in self.wrong if s in (2, 3)}
        A.draw_shelf(world, self.pulled, wrong0, here if self.stage == 0 else None, t)
        drawer_labels = self.request["labels"] if self.stage == 1 else (
            self.solved[1]["labels"] if len(self.solved) > 1 else ["", "", "", ""])
        A.draw_drawers(world, drawer_labels, self.opened, wrong1, here if self.stage == 1 else None, self.card, t)
        tray_labels = self.request["labels"] if self.stage in (2, 3) else (
            self.solved[3]["labels"] if len(self.solved) > 3 else [])
        A.draw_trays(world, tray_labels, self.fed, wrong2, here if self.stage in (2, 3) else None, t)
        badge_door.draw_badge_door(world, A.DOOR, self.door_open, t)
        self.draw_dust(world, theme.floor_palette(LEVEL_KEY)["floor"])
        lighting.blob_shadow(world, self.archivist.rect, 90)
        self.archivist.draw(world, self.small)
        cx, cy = self.drone.centre
        reach = self.drone_reach
        warning = any(v > 0 for v in self.drone_lock.values())
        beam = pygame.Surface((reach * 2, reach), pygame.SRCALPHA)
        pygame.draw.ellipse(beam, (255, 90, 90, 46) if warning else (220, 230, 255, 30), beam.get_rect())
        world.blit(beam, (cx - reach, cy + 14 - reach // 2))
        lighting.blob_shadow(world, pygame.Rect(cx - 8, cy + 18, 16, 6), 70)
        bob = int(2 * math.sin(t * 5))
        draw_drone(world, (cx, cy + bob), "enemy_alert" if warning or (self.drone_hits and any(
            v > DRONE_COOLDOWN - 0.6 for v in self.drone_wait.values())) else "enemy", int(t * 12))
        draw_drone(world, (int(self.echo[0]), int(self.echo[1]) + bob), "ally", int(t * 12))
        self.draw_sparks(world)
        self.lightlayer.apply(world, self._lights())
        A.draw_slip(world, self.request, min(self.stage + 1, REQUESTS), REQUESTS,       # paper stays readable
                    self.time_left / self.time_limit, max(0, math.ceil(self.time_left)),
                    self.stage >= REQUESTS, t, drop=self.slip_drop,
                    warn=self.stage < REQUESTS and self.time_left <= WARN_SECONDS)
        A.draw_satchel(world, self.satchel)
        world.blit(*self._title)
        hint = ("E: pull the box", "E: open the drawer", "E: feed the vault", "E: set the dial",
                "Walk into the vault")[min(self.stage, 4)]
        self.draw_message(world, hint + "   Q scan   X lure", self.line_font, self.small)
        self.present(surface, world)
