"""
levels/final_core.py
Owner: Member 1 - Core Game System (the Final Vault rebuilt as WARDEN's Core)

Final Floor - WARDEN's Core  (everything combined)

The Master Memory chip is sealed in the iris at the centre of WARDEN's core.
Six lock pylons ring it, one for every floor of the run: data types, operators,
loops, lists and dictionaries, functions, exceptions.  Open them in any order:
stand on the right one of the three plates in front of a pylon and press E.
WARDEN's eye sweeps a searchlight round the room the whole time, faster with
every lock that falls.  When all six are open the iris opens; take the chip
(E at the core) and run for the extraction lift.

    E / Right Shift   stand on a plate and press to answer; at the open core, take the chip
    H / TAB           a hint for the lock you are nearest (off on Hard)

Rules (the old Final Vault's numbers):
    right plate      +50 for that lock (once)
    wrong plate      security +20, score -10; that plate is ruled out
    take the chip    +150
    the searchlight  score -10 when it catches you (score only), after a short grace

levels/final_vault.py (the original) and levels/final_vault_hall.py (the previous
floor) are untouched; MEMORY_HEIST_OLD_FINAL_VAULT=1 returns the original.
"""

import math

import pygame

from core.tilemap import TILE, TileMap, make_tiles
from levels import badge_door, depth_fx, lighting
from levels import core_decor as C
from levels.core_requests import LOCKS, make_lock
from levels.room_base import TITLE_Y, RoomMap, RoomMixin
from ui import theme
from ui.fonts import ui_font
from ui.kit import shadowed

LEVEL_KEY = "final_vault"
STAGE_POINTS, COMPLETION_BONUS = 50, 150
WRONG_SECURITY, WRONG_PENALTY = 20, 10
BEAM_PENALTY = 10
BEAM_COOLDOWN = 2.5
BEAM_GRACE = 3.0
BEAM_SPEED = 0.45                # radians per second at the start
BEAM_SPEEDUP = 0.08              # added for every lock that falls
IRIS_SECONDS = 1.6
DOOR_SECONDS = 1.2
NEAR_LOCK = 120                  # how close to a pylon counts as "at" that lock
WRONG_SECONDS = 0.5
AMBIENT_SEALED = (150, 96, 100)  # WARDEN's red
AMBIENT_OPEN = (120, 150, 150)   # cooler, calmer, once he falls

TAUNTS = ("That lock held for forty years.", "You are deleting parts of me.",
          "Stop. I kept those memories safe.", "Every file you free, I forget.",
          "Please. Not the last one.")
LAST_WORDS = "...Take it, then. Everything I ever erased."
SCORN = ("Wrong. I knew you would be.", "Guessing? In my core?", "Again. I can wait forever.")
CAUGHT = "WARDEN's light finds you. -10. Move when the beam has passed."


class CoreVault(RoomMixin):
    STEP_SOUND = "step_metal"

    def __init__(self, player=None, game=None, seed=None):
        self.player = player
        self.game = game
        self.complete = False
        self.init_room(seed)
        self.locks = [make_lock(k, self.rng) for k in range(LOCKS)]
        self.solved = {}                 # lock -> plate index chosen
        self.out = {k: set() for k in range(LOCKS)}
        self.wrong = {}                  # (lock, plate) -> seconds of red flash
        self.hint_lock = None
        self.beam_angle = -math.pi / 2
        self.beam_grace = BEAM_GRACE
        self.beam_wait = {}
        self.beam_hits = 0
        self.iris = 0.0                  # 0 sealed .. 1 open
        self.chip_taken = False
        self.door_open = 0.0
        self._scorn = 0
        self.say("Six locks, one for every floor. Stand on a plate by a pylon and press E.")

        self.tilemap = TileMap(C.layout_rows())
        self.tiles = make_tiles(LEVEL_KEY)
        self.door_block = C.DOOR.copy()
        self.room_map = RoomMap(self.tilemap, C.prop_rects() + [self.door_block])
        self.exit_zone = C.EXIT_ZONE
        self.spawn_points = C.SPAWNS

        self.title_font = ui_font(26, bold=True)
        self.line_font = ui_font(22)
        self.small = ui_font(20)
        self._background = None
        self._title = None
        self.lightlayer = lighting.LightLayer(ambient=AMBIENT_SEALED)

    # --- state the game reads ---------------------------------------------------------
    @property
    def gates_passed(self):
        """Pairs of locks opened (the comms feed's progress line), 3 once all six are open."""
        return len(self.solved) // 2

    @property
    def stage(self):
        return len(self.solved)

    def is_complete(self):
        return self.complete

    def set_player(self, player):
        self.player = player

    def _hints_on(self):
        hints = getattr(self.game, "hints", None)
        return True if hints is None else bool(getattr(hints, "enabled", True))

    # --- where the players stand ----------------------------------------------------------
    def plate_at(self, player):
        for k in range(LOCKS):
            if k in self.solved:
                continue
            for j in range(3):
                if C.plate_rect(k, j).inflate(6, 6).collidepoint(player.rect.center):
                    return k, j
        return None

    def nearest_lock(self, player):
        best, dist = None, NEAR_LOCK
        for k in range(LOCKS):
            d = math.dist(player.rect.center, C.pylon_rect(k).center)
            if d < dist:
                best, dist = k, d
        spot = self.plate_at(player)
        return spot[0] if spot else best

    # --- input --------------------------------------------------------------------------------
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN or self.complete:
            return
        if event.key in (pygame.K_h, pygame.K_TAB):
            self._hint()
            return
        for player, key in self.players():
            if event.key != key:
                continue
            spot = self.plate_at(player)
            if spot is not None:
                self._answer(*spot)
            elif self.iris >= 1.0 and not self.chip_taken and self.near(player, C.CORE, 40):
                self._take_chip()
            elif self.chip_taken:
                self.say("You have the chip. Run for the extraction lift!", theme.TEAL)
            else:
                self.say("Stand on one of the plates in front of a lock pylon, then press E.", theme.MIST)

    def _hint(self):
        lock = self.nearest_lock(self.player) if self.player is not None else None
        if lock is None or lock in self.solved:
            self.say("Walk up to a lock that is still sealed, then press H.", theme.MIST)
            return
        if not self._hints_on():
            self.say("Hints are off on this difficulty.", theme.MIST)
            return
        self.hint_lock = lock
        self.say("Echo: " + self.locks[lock]["hint"], theme.GOLD)

    # --- the rules --------------------------------------------------------------------------------
    def _answer(self, k, j):
        lock = self.locks[k]
        spot = C.plate_rect(k, j).center
        if j in self.out[k]:
            self.say("That plate is ruled out. Try another.", theme.MIST)
            return
        if j == lock["answer"]:
            self.solved[k] = j
            if self.game:
                self.game.score.add(STAGE_POINTS)
            self.burst(spot, theme.TEAL, 16)
            self.burst(C.pylon_rect(k).center, theme.TEAL, 10)
            self.shake.add(0.35)
            self.sfx("switch")
            self.sfx("chime")
            left = LOCKS - len(self.solved)
            if left == 0:
                self.sfx("door")
                self.say(f"+{STAGE_POINTS}. {lock['explain']}  WARDEN: \"{LAST_WORDS}\"", theme.GOLD)
            else:
                taunt = TAUNTS[min(len(self.solved) - 1, len(TAUNTS) - 1)]
                self.say(f"+{STAGE_POINTS}. {lock['explain']}  {left} left.  WARDEN: \"{taunt}\"", theme.TEAL)
        else:
            self.out[k].add(j)
            self.wrong[(k, j)] = WRONG_SECONDS
            self.shake.add(0.55)
            self.burst(spot, theme.CORAL, 12)
            self.sfx("alarm")
            self.say(f"WARDEN: \"{SCORN[self._scorn % len(SCORN)]}\"  Security up. That plate is out.", theme.CORAL)
            self._scorn += 1
            if self.game:
                self.game.security.increase(WRONG_SECURITY)
                self.game.score.penalize(WRONG_PENALTY)

    def _take_chip(self):
        self.chip_taken = True
        if self.game:
            self.game.score.add(COMPLETION_BONUS)
        self.burst(C.CENTRE, theme.GOLD, 30)
        self.burst(C.CENTRE, theme.TEAL, 20)
        self.shake.add(0.8)
        self.sfx("chime")
        self.sfx("door")
        self.say(f"+{COMPLETION_BONUS}. The Master Memory is yours. Run for the extraction lift!", theme.GOLD)

    # --- per frame ------------------------------------------------------------------------------
    def _update_beam(self, dt):
        if self.chip_taken:
            return
        self.beam_angle = (self.beam_angle + (BEAM_SPEED + BEAM_SPEEDUP * len(self.solved)) * dt) % math.tau
        self.beam_grace = max(0.0, self.beam_grace - dt)
        for player, _ in self.players():
            key = id(player)
            self.beam_wait[key] = max(0.0, self.beam_wait.get(key, 0.0) - dt)
            if self.beam_grace > 0 or self.beam_wait[key] > 0:
                continue
            if C.in_beam(self.beam_angle, player.rect.center):
                self.beam_wait[key] = BEAM_COOLDOWN
                self.beam_hits += 1
                self.shake.add(0.3)
                self.sfx("alarm")
                self.say(CAUGHT, theme.CORAL)
                if self.game:
                    self.game.score.penalize(BEAM_PENALTY)

    def update(self, dt):
        dt = max(0.0, dt)
        self.update_room(dt)
        self.wrong = {k: v - dt for k, v in self.wrong.items() if v - dt > 0}
        if self.complete:
            return
        self._update_beam(dt)
        if len(self.solved) == LOCKS:
            self.iris = min(1.0, self.iris + dt / IRIS_SECONDS)
        k = len(self.solved) / LOCKS
        self.lightlayer.ambient = tuple(round(a + (b - a) * k) for a, b in zip(AMBIENT_SEALED, AMBIENT_OPEN))
        if self.chip_taken:
            self.door_open = min(1.0, self.door_open + dt / DOOR_SECONDS)
            if self.door_open > 0.9:
                self.door_block.size = (0, 0)
                for player, _ in self.players():
                    if player.rect.colliderect(self.exit_zone):
                        self.complete = True
                        self.say("Extraction. WARDEN goes quiet.", theme.GOLD)
                        break

    # --- drawing -----------------------------------------------------------------------------------
    def _build_background(self):
        size = self.tilemap.pixel_size
        bg = pygame.Surface(size)
        cam = type("Cam", (), {})()
        cam.offset = lambda: (0, 0)
        cam.x = cam.y = 0
        cam.view_w, cam.view_h = size
        self.tilemap.render(bg, cam, self.tiles)
        C.draw_static(bg, self.tilemap)
        accent = theme.floor_palette(LEVEL_KEY)["accent"]
        title = shadowed(self.title_font, "FINAL FLOOR - WARDEN'S CORE", theme.mix(accent, theme.PAPER, 0.4))
        self._title = (title, (TILE * 2, TITLE_Y))
        self._background = bg

    def _lights(self):
        k = len(self.solved) / LOCKS
        core = theme.mix(C.CORE_RED, theme.TEAL, k)
        out = [lighting.Light(C.CENTRE, 170, core, 0.9)]
        for i in range(LOCKS):
            lamp = theme.TEAL if i in self.solved else theme.CORAL
            out.append(lighting.Light(C.pylon_rect(i).center, 80, lamp, 0.7))
        if not self.chip_taken:
            tip = (C.CENTRE[0] + math.cos(self.beam_angle) * 170, C.CENTRE[1] + math.sin(self.beam_angle) * 170)
            out.append(lighting.Light((int(tip[0]), int(tip[1])), 110, (255, 220, 200), 0.8))
        out.append(lighting.Light((C.DOOR.x - 12, C.DOOR.centery), 100, badge_door.lamp_colour(self.door_open), 0.7))
        out.append(lighting.Light(C.TERMINAL.center, 150, (220, 90, 90), 0.4))
        out.append(lighting.Light(C.STATUS.center, 150, (220, 90, 90), 0.4))
        return out

    def render(self, surface):
        if self._background is None:
            self._build_background()
        world = self._background.copy()
        t = self.time
        depth_fx.motes(world, C.MOTE_AREA, t, count=30, colour=(230, 180, 170), seed=6)
        stands = {}
        for player, _ in self.players():
            spot = self.plate_at(player)
            if spot:
                stands[spot[0]] = spot[1]
        near = {self.nearest_lock(p) for p, _ in self.players()} - {None}
        for k in range(LOCKS):
            state = "solved" if k in self.solved else ("near" if k in near else "idle")
            C.draw_pylon(world, k, state, t)
            wrong = {j for (lk, j) in self.wrong if lk == k}
            C.draw_plates(world, k, self.locks[k]["labels"], self.out[k], wrong, stands.get(k), self.solved.get(k), t)
        C.draw_core(world, len(self.solved), self.iris, self.chip_taken, t)
        badge_door.draw_badge_door(world, C.DOOR, self.door_open, t)
        self.draw_dust(world, theme.floor_palette(LEVEL_KEY)["floor"])
        self.draw_sparks(world)
        self.lightlayer.apply(world, self._lights())
        if not self.chip_taken:
            alert = any(v > BEAM_COOLDOWN - 0.6 for v in self.beam_wait.values())
            C.draw_beam(world, self.beam_angle, alert, t)
        focus = self.nearest_lock(self.player) if self.player is not None else None
        C.draw_terminal(world, self.locks[focus] if focus is not None else None, focus in self.solved, t)
        integrity = 1.0 - len(self.solved) / LOCKS
        C.draw_status(world, set(self.solved), integrity, self.chip_taken, t)
        world.blit(*self._title)
        if self.chip_taken:
            hint = "Run for the extraction lift"
        elif len(self.solved) == LOCKS:
            hint = "E at the core: take the chip"
        else:
            hint = "E on a plate   H: hint"
        font = self.line_font if self.line_font.size(self.message)[0] <= 860 else self.small
        self.draw_message(world, hint, font, self.small)
        self.present(surface, world)
