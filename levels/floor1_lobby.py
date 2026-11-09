"""
levels/floor1_lobby.py
Owner: Member 1 - Core Game System (reference floor for the overhaul)

Floor 1 - Reception Lobby  (topic: data types)

Ghost arrives from the elevator. Six crates sit around the lobby, each marked
with a real Python value. Carry each crate to the bin for its data type
(int, str, float, bool). The right answer is Python's own `type(value)`, so
it can never disagree with the language.

    E            pick up / put down (player 1)      Right Shift (player 2)
    2 crates     open a gate (3 gates)
    3 gates      unlock the exit door on the right wall

Built on the shared kit: ui.theme, core.tilemap, core.animation, core.easing.
Wrong bin: crate returns, security +20, score -10 (same amounts as Level 1).
This is Level 1. The original question-screen Level 1 stays in levels/level1.py
and returns with MEMORY_HEIST_OLD_LEVEL1=1.
"""

import math
import random

import pygame

from core.animation import Shake, SquashStretch
from core.easing import Tween, ease_out_cubic
from core.npc import NPC
from core.tilemap import TILE, TileMap, make_tiles
from levels import lighting, lobby_decor, lobby_extras, lobby_juice, novacorp_style
from ui import theme
from ui.kit import draw_panel, shadowed
from ui.fonts import code_font, ui_font

LEVEL_KEY = "level1"
COLS, ROWS = 30, 20            # 960 x 640: exactly one screen
GATES = 3
CRATES_PER_GATE = 2
CRATE_POINTS = 25               # two crates = 50, same per-gate value as Level 1
FINISH_BONUS = 100
WRONG_SECURITY = 20
WRONG_PENALTY = 10
REACH = 52                      # how close counts as "next to" a crate or bin

BIN_TYPES = ("int", "str", "float", "bool")
BIN_COLOURS = {
    "int": theme.SKY, "str": theme.GOLD, "float": theme.TEAL, "bool": theme.CORAL,
}
HINTS = {
    "int": "A whole number with no decimal point is an int.",
    "str": "Anything inside quotes is a str, even digits.",
    "float": "A number with a decimal point is a float.",
    "bool": "Only True and False are bool.",
}

_BASE = {
    "int": [42, -7, 1000, 5],
    "str": ["hello", "agent", "NovaCorp", "A-4471"],
    "float": [3.14, 0.5, 9.99, 2.5],
    "bool": [True, False],
}
_TRAPS = {
    "easy": {},
    "medium": {"str": ["42"], "float": [2.0]},
    "hard": {"str": ["42", "True"], "float": [2.0, 1.0], "int": [0]},
}

# Tile spots where crates may start (col, row), clear of bins, desk and plants.
CRATE_SPOTS = [(6, 7), (10, 6), (14, 6), (18, 6), (22, 7), (7, 12),
               (12, 11), (17, 11), (22, 12), (25, 7)]
BIN_COLS = (8, 12, 16, 20)       # bin i spans cols [c, c+1], row BIN_ROW
BIN_ROW = 4
EXIT_ROWS = (9, 10, 11)
# The people who work here (tile col, row). The receptionist stands behind the
# desk; the guard patrols the open floor to its right.
RECEPTIONIST_TILE = (15, 16)
GUARD_ROUTE = [(19, 16), (25, 16), (25, 14)]
# Parcel intake: reception is also the mail room, and Ghost walks in as a courier.
START_MESSAGE = "Belt jammed: file each parcel by type."
PICKUP_FORMAT = "Got {value}. Which chute?"
FILED_FORMAT = "{value} is {kind}. Stamped!"
BELT_SIGN = ("BELT OUT OF ORDER", "FILE BY HAND")
BELT_FIXED_SIGN = ("BELT RESTARTED", "THANK YOU")      # once every parcel is filed
BELT_PLATE = (722, 100, 138, 38)
# The visitor queue: brass posts and red rope funnel people to the middle of the desk.
QUEUE_Y = 14 * TILE + 6
QUEUE_POSTS = (11 * TILE, 13 * TILE, 17 * TILE, 19 * TILE)      # x of the four posts
BELT_JAM = (236, 106)            # where the jammed parcels sit on the belt
GREETINGS = ("Welcome to NovaCorp.", "Courier? Chutes are ahead.", "Mind the parcels.")
CLEANER_ROUTE = [(6, 16), (11, 16)]
CLEANER_LINES = ("Mind the wet floor.", "Nobody thanks the cleaner.", "Please keep moving.")
GUARD_LINES = ("Move along, courier.", "Badges stay visible.")
PRAISE = ("Stamped. Next.", "Filed correctly.")
SCOLD = "Wrong chute, courier."
FAREWELL = "Have a good day."
CLEARED_MESSAGE = "All parcels stamped. The elevator is waiting."

# Text on the wall band (y 48..96, between the HUD and the floor).
TITLE_Y = 48
MESSAGE_Y = 74
DUST_EVERY = 0.12               # seconds between footstep puffs while walking
DUST_LIFE = 0.45
STEP_EVERY = 0.32                       # seconds between footstep sounds
PA_LINES = ("PA: Remain visible.", "PA: Badges on show.", "PA: Smile, please.",
            "PA: Stay in line.", "PA: Report. Relax.")
PA_SPEAKER = (392, 60)                  # ceiling speaker on the wall band
PA_CAPTION = (412, 52)                  # where its caption is written


def type_name(value):
    """The bin a value belongs in: Python's own answer."""
    return type(value).__name__


def with_article(name):
    """'an int', 'a str': the right article for a type name."""
    return ("an " if name[0] in "aeiou" else "a ") + name


def display(value):
    """How a value reads on a crate (strings keep their quotes)."""
    return f'"{value}"' if isinstance(value, str) else repr(value)


def pick_crates(difficulty, rng, count=GATES * CRATES_PER_GATE):
    """`count` distinct values covering all four types; harder = more traps."""
    pools = {t: list(_BASE[t]) + list(_TRAPS.get(difficulty, {}).get(t, ()))
             for t in BIN_TYPES}
    for pool in pools.values():
        rng.shuffle(pool)
    order = list(BIN_TYPES)
    rng.shuffle(order)
    values = [pools[t].pop() for t in order]            # one of each type
    extra = list(BIN_TYPES)
    rng.shuffle(extra)
    for t in extra:
        if len(values) >= count:
            break
        values.append(pools[t].pop())
    rng.shuffle(values)
    return values[:count]


def layout_rows(cols=COLS, rows=ROWS):
    """Lobby shell: walls on every edge, exit gap on the right, rug in the middle."""
    out = []
    for y in range(rows):
        if y <= 2 or y >= rows - 2:
            out.append("#" * cols)
            continue
        row = ["#", "#"] + ["."] * (cols - 4) + ["#", "#"]
        if y in EXIT_ROWS:
            row[cols - 2] = row[cols - 1] = "."
        if 8 <= y <= 13:
            for x in range(9, 21):
                row[x] = ","
        out.append("".join(row))
    return out


class RoomMap:
    """What Game asks for: blocked(rect). Walls plus solid props."""

    def __init__(self, tilemap, props):
        self.tilemap = tilemap
        self.props = props

    def blocked(self, rect):
        return self.tilemap.collides(rect) or any(rect.colliderect(p) for p in self.props)


class Crate:
    def __init__(self, value, home):
        self.value = value
        self.answer = type_name(value)
        self.home = pygame.Rect(home)
        self.rect = self.home.copy()
        self.carrier = None
        self.sorted = False
        self.bob = random.random() * 6.28


class FloorOneLobby:
    def __init__(self, player=None, game=None, seed=None):
        self.player = player
        self.game = game
        self.rng = random.Random(seed)
        self.complete = False
        self.gates_passed = 0
        self.sorted_count = 0
        self.message = START_MESSAGE
        self.message_tone = theme.PAPER
        self._message_age = 0.0

        self.tilemap = TileMap(layout_rows())
        self.tiles = make_tiles(LEVEL_KEY)
        self.bins = {}
        for t, col in zip(BIN_TYPES, BIN_COLS):
            self.bins[t] = pygame.Rect(col * TILE, BIN_ROW * TILE, TILE * 2, TILE)
        self.props = list(self.bins.values())
        self.desk = pygame.Rect(12 * TILE, 15 * TILE, 6 * TILE, TILE)
        self.props.append(self.desk)
        self.plants = [pygame.Rect(col * TILE, row * TILE, TILE, TILE)
                       for col, row in ((3, 15), (26, 15), (3, 8), (26, 4))]
        self.sofa = pygame.Rect(4 * TILE, 13 * TILE, 3 * TILE, TILE)
        self.vending = pygame.Rect(26 * TILE, 12 * TILE, TILE, 2 * TILE)
        self.props += self.plants + [self.sofa, self.vending]
        self.cabinets = [pygame.Rect(2 * TILE, row * TILE, TILE, TILE) for row in (10, 11)]
        self.cooler = pygame.Rect(27 * TILE, 5 * TILE, TILE, 2 * TILE)
        self.props += self.cabinets + [self.cooler]
        self.posts = [pygame.Rect(x - 5, QUEUE_Y - 6, 10, 12) for x in QUEUE_POSTS]
        self.ropes = [pygame.Rect(QUEUE_POSTS[0] + 5, QUEUE_Y - 3, QUEUE_POSTS[1] - QUEUE_POSTS[0] - 10, 6),
                      pygame.Rect(QUEUE_POSTS[2] + 5, QUEUE_Y - 3, QUEUE_POSTS[3] - QUEUE_POSTS[2] - 10, 6)]
        self.props += self.posts + self.ropes
        self.receptionist = NPC("receptionist", (RECEPTIONIST_TILE[0] * TILE, RECEPTIONIST_TILE[1] * TILE),
                                facing_left=True)
        self._manifests_read = 0
        self._cooler_uses = 0
        self._sofa_uses = 0
        self._banters = 0
        self._banter_wait = lobby_extras.BANTER_GAP / 2
        self.guard = NPC("guard", (0, 0), patrol=[(c * TILE, r * TILE) for c, r in GUARD_ROUTE])
        self.cleaner = NPC("cleaner", (0, 0), patrol=[(c * TILE, r * TILE) for c, r in CLEANER_ROUTE],
                           speed=34.0, pause=1.6)
        self.npcs = [self.receptionist, self.guard, self.cleaner]
        self._lines_said = {"receptionist": 0, "guard": 0, "cleaner": 0, "praise": 0}
        self.led_pos = (20 * TILE + 16, 2 * TILE + 10)      # WARDEN camera light
        self.door = pygame.Rect(28 * TILE, EXIT_ROWS[0] * TILE, TILE * 2, TILE * len(EXIT_ROWS))
        self.door_block = self.door.copy()
        self.room_map = RoomMap(self.tilemap, self.props + [self.door_block])
        self.exit_zone = pygame.Rect(28 * TILE + 8, self.door.y, TILE * 2, self.door.h)

        difficulty = "medium"
        if game is not None:
            diff = getattr(game, "difficulty", None) or {}
            difficulty = {0.5: "easy", 1.0: "medium", 1.5: "hard"}.get(
                diff.get("security_penalty_multiplier"), "medium")
        spots = list(CRATE_SPOTS)
        self.rng.shuffle(spots)
        self.crates = []
        for value, (col, row) in zip(pick_crates(difficulty, self.rng), spots):
            self.crates.append(Crate(value, (col * TILE + 2, row * TILE + 2, 28, 28)))

        self.carried = {}                       # id(player) -> Crate
        self.shake = Shake(max_offset=8, seed=7)
        self.bin_pulse = {t: SquashStretch() for t in BIN_TYPES}
        self.crate_pop = SquashStretch()
        self.door_tween = None
        self.door_open = 0.0                    # 0 closed .. 1 open
        self.lamps = [0.0] * GATES
        self.sparks = []
        self.dust = []
        self._step_clock = {}
        self._dust_clock = {}
        self.time = 0.0
        self.ambience = lobby_decor.Ambience(seed=11)   # own rng: crate layout stays untouched
        self.pa = novacorp_style.PA(PA_LINES)
        # The WARDEN camera sweeps the floor; visitor chips are hidden around it.
        # Both use their own rng, so the crate layout above is unchanged.
        self.beam = lobby_extras.SweepBeam((self.led_pos[0], self.led_pos[1] + 6))
        self.watch = lobby_extras.Watch(self.beam)
        extras_rng = random.Random(seed)
        spots = [s for s in lobby_extras.CHIP_SPOTS if not self._spot_blocked(s)]
        self.chips = [lobby_extras.Chip(s) for s in extras_rng.sample(spots, lobby_extras.CHIPS_HIDDEN)]
        self.chips_found = 0
        self.vending_used = False
        self._bell_rings = 0
        self.phone = lobby_extras.Phone()
        self._beam_overlay = None
        self.lightlayer = lighting.LightLayer()
        self._dressed = False
        for hero, _ in self._players():
            hero.set_outfit(None)              # a fresh run starts in the usual look
        self.juice = lobby_juice.Juice()
        self.popup_font = ui_font(20, bold=True)
        self._title = None

        self.font = ui_font(22)
        self.small = ui_font(20)
        self.big = ui_font(30)
        self.code = code_font(20)       # crate values
        self.code_big = code_font(30)   # bin type names
        self._background = None

    def _spot_blocked(self, spot):
        probe = pygame.Rect(0, 0, lobby_extras.CHIP_SIZE, lobby_extras.CHIP_SIZE)
        probe.center = (spot[0] * TILE + TILE // 2, spot[1] * TILE + TILE // 2)
        return self.room_map.blocked(probe)

    # --- players --------------------------------------------------------
    def _players(self):
        out = []
        if self.player is not None:
            out.append((self.player, pygame.K_e))
        game = self.game
        if game is not None and getattr(game, "coop", False) and getattr(game, "player2", None):
            out.append((game.player2, pygame.K_RSHIFT))
        return out

    # --- interaction ----------------------------------------------------
    def handle_event(self, event):
        if event.type != pygame.KEYDOWN or self.complete:
            return
        for player, key in self._players():
            if event.key == key:
                self._interact(player)

    def _near(self, player, rect):
        return pygame.Rect(rect).inflate(REACH, REACH).colliderect(player.rect)

    def _interact(self, player):
        crate = self.carried.get(id(player))
        if crate is None:
            if self._pickup_target(player) is None and self._use_prop(player):
                return
            self._pick_up(player)
            return
        bin_type = self._bin_in_reach(player)
        if bin_type is not None:
            self._drop_in_bin(player, crate, bin_type)
            return
        self._put_down(player, crate)

    def _use_prop(self, player):
        """E with empty hands and no crate in reach: ring the bell or use the vending machine."""
        if self._near(player, self.desk):
            line = lobby_extras.BELL_LINES[self._bell_rings % len(lobby_extras.BELL_LINES)]
            self._bell_rings += 1
            self._sfx("bell")
            self.receptionist.say(line)
            return True
        for cab in self.cabinets:
            if self._near(player, cab):
                self._read_manifest()
                return True
        if self._near(player, self.sofa):
            line = lobby_extras.SOFA_LINES[self._sofa_uses % len(lobby_extras.SOFA_LINES)]
            self._sofa_uses += 1
            self._say(line, theme.MIST)
            return True
        if self._near(player, self.cooler):
            line = lobby_extras.COOLER_LINES[self._cooler_uses % len(lobby_extras.COOLER_LINES)]
            self._cooler_uses += 1
            self._say(line, theme.MIST)
            return True
        if self._near(player, self.vending):
            self._sfx("vending")
            if self.vending_used:
                self._say(lobby_extras.VENDING_EMPTY, theme.MIST)
            else:
                self.vending_used = True
                if self.game:
                    self.game.score.add(lobby_extras.VENDING_POINTS)
                self._burst(self.vending.center, theme.GOLD, 8)
                self._say(lobby_extras.VENDING_LINE, theme.GOLD)
            return True
        return False

    def _bin_in_reach(self, player):
        for t, rect in self.bins.items():
            if self._near(player, rect):
                return t
        return None

    def _pickup_target(self, player):
        """The nearest free crate within reach of `player`, or None."""
        best, best_d = None, 1e9
        for crate in self.crates:
            if crate.sorted or crate.carrier is not None:
                continue
            if not self._near(player, crate.rect):
                continue
            d = math.dist(crate.rect.center, player.rect.center)
            if d < best_d:
                best, best_d = crate, d
        return best

    def _prompted_crates(self):
        """Crates a player with free hands could pick up right now (drawn highlighted)."""
        out = []
        for player, _ in self._players():
            if id(player) not in self.carried:
                crate = self._pickup_target(player)
                if crate is not None and crate not in out:
                    out.append(crate)
        return out

    def _prompted_bins(self):
        """Bins a player carrying a crate is close enough to drop into."""
        out = set()
        for player, _ in self._players():
            if id(player) in self.carried:
                bin_type = self._bin_in_reach(player)
                if bin_type is not None:
                    out.add(bin_type)
        return out

    def _pick_up(self, player):
        best = self._pickup_target(player)
        if best is None:
            return
        best.carrier = player
        self.carried[id(player)] = best
        self._sync_carried()
        self.crate_pop.trigger(0.35)
        self._sfx("pickup")
        self._say(PICKUP_FORMAT.format(value=display(best.value)), theme.PAPER)

    def _put_down(self, player, crate):
        spot = pygame.Rect(0, 0, 28, 28)
        spot.midtop = (player.rect.centerx, player.rect.bottom + 2)
        if self.room_map.blocked(spot):
            spot.midbottom = (player.rect.centerx, player.rect.top - 2)
        if self.room_map.blocked(spot):
            return
        crate.rect = spot
        crate.carrier = None
        del self.carried[id(player)]
        self._sfx("drop")

    def _drop_in_bin(self, player, crate, bin_type):
        del self.carried[id(player)]
        crate.carrier = None
        self.bin_pulse[bin_type].trigger(0.5)
        centre = self.bins[bin_type].center
        if crate.answer == bin_type:
            crate.sorted = True
            self.sorted_count += 1
            self.juice.filed(crate.rect.center, centre, bin_type, f"+{CRATE_POINTS}", theme.TEAL)
            self._burst(centre, BIN_COLOURS[bin_type], 18)
            if self.game:
                self.game.score.add(CRATE_POINTS)
            self._sfx("stamp")
            self._say(FILED_FORMAT.format(value=display(crate.value), kind=with_article(bin_type)), theme.TEAL)
            self._npc_react("praise")
            self._check_gates()
        else:
            self.juice.missed((centre[0], centre[1] - 26), f"-{WRONG_PENALTY}", theme.CORAL)
            crate.rect = crate.home.copy()
            self.shake.add(0.55)
            self._burst(centre, theme.CORAL, 12)
            hint = HINTS[crate.answer]
            if self.game and not self.game.hints.enabled:
                hint = "Hints are off on this difficulty."
            self._say(f"Not {with_article(bin_type)}. {hint}", theme.CORAL)
            self.guard.alert(player.rect, 1.6)
            self.guard.say(SCOLD)
            if self.game:
                self.game.security.increase(WRONG_SECURITY)
                self.game.score.penalize(WRONG_PENALTY)

    def _check_gates(self):
        gates = min(GATES, self.sorted_count // CRATES_PER_GATE)
        if gates > self.gates_passed:
            self.gates_passed = gates
        if self.sorted_count >= GATES * CRATES_PER_GATE and self.door_tween is None \
                and self.door_open < 1.0:
            self.door_tween = Tween(0.0, 1.0, 0.8, ease_out_cubic)
            self._sfx("door")
            self._say("Badge reader online. The exit is open.", theme.GOLD)

    # --- helpers --------------------------------------------------------
    def _sfx(self, name):
        """Play a sound effect if the game has audio (tests and previews may not)."""
        audio = getattr(self.game, "audio", None)
        if audio is not None:
            audio.play(name)

    def _update_steps(self, dt):
        for player, _ in self._players():
            clock = self._step_clock.get(id(player), 0.0)
            if getattr(player, "moving", False):
                clock += dt
                if clock >= STEP_EVERY:
                    clock = 0.0
                    self._sfx("step")
            else:
                clock = STEP_EVERY * 0.6      # the first step after standing still is quick
            self._step_clock[id(player)] = clock

    def _npc_react(self, event):
        """The people nearby comment on what just happened; each line is said in turn."""
        if event == "praise":
            n = self._lines_said["praise"]
            self._lines_said["praise"] = n + 1
            if n % 2 == 0:                       # every other correct sort, not every one
                self.receptionist.say(PRAISE[(n // 2) % len(PRAISE)])

    def _update_npcs(self, dt):
        for npc in self.npcs:
            npc.update(dt)
        self._banter(dt)
        for player, _ in self._players():
            for npc, lines in ((self.receptionist, GREETINGS), (self.guard, GUARD_LINES),
                               (self.cleaner, CLEANER_LINES)):
                if npc.notice(player.rect, id(player)):
                    n = self._lines_said[npc.kind]
                    self._lines_said[npc.kind] = n + 1
                    npc.say(lines[n % len(lines)])

    def _read_manifest(self):
        """E at a filing cabinet: read the next chute rule (type hint) from the manifests."""
        n = self._manifests_read
        self._manifests_read += 1
        if self.game and not self.game.hints.enabled:
            self._say(lobby_extras.MANIFEST_OFF, theme.MIST)
            return
        kind = BIN_TYPES[n % len(BIN_TYPES)]
        self._say(lobby_extras.MANIFEST_TITLE.format(n=n % len(BIN_TYPES) + 1) + HINTS[kind],
                  BIN_COLOURS[kind])

    def _banter(self, dt):
        """The guard and receptionist swap a line when he walks past her desk."""
        self._banter_wait = max(0.0, self._banter_wait - dt)
        if self._banter_wait > 0 or self.complete:
            return
        gx, gy = self.guard.rect.center
        rx, ry = self.receptionist.rect.center
        if math.hypot(gx - rx, gy - ry) <= lobby_extras.BANTER_RANGE:
            a, b = lobby_extras.BANTER[self._banters % len(lobby_extras.BANTER)]
            self._banters += 1
            self._banter_wait = lobby_extras.BANTER_GAP
            self.guard.say(a)
            self.receptionist.say(b)

    def _say(self, text, tone):
        self.message, self.message_tone, self._message_age = text, tone, 0.0

    def _burst(self, pos, colour, count):
        for _ in range(count):
            ang = self.rng.uniform(0, 6.283)
            speed = self.rng.uniform(50, 150)
            self.sparks.append({"x": pos[0], "y": pos[1], "colour": colour, "life": 0.6,
                                "vx": math.cos(ang) * speed, "vy": math.sin(ang) * speed - 40})

    def _sync_carried(self):
        """A carried crate rides above its carrier's head."""
        for player, _ in self._players():
            crate = self.carried.get(id(player))
            if crate is not None:
                crate.rect.size = (28, 28)
                crate.rect.midbottom = (player.rect.centerx, player.rect.top - 2)

    # --- update ---------------------------------------------------------
    def update(self, dt):
        dt = max(0.0, dt)
        self._dress()
        self._sync_carried()
        self.time += dt
        self._message_age += dt
        self.shake.update(dt)
        self.crate_pop.update(dt)
        self.juice.update(dt)
        for pulse in self.bin_pulse.values():
            pulse.update(dt)
        for s in self.sparks:
            s["x"] += s["vx"] * dt
            s["y"] += s["vy"] * dt
            s["vy"] += 260 * dt
            s["life"] -= dt
        self.sparks = [s for s in self.sparks if s["life"] > 0]
        self._update_dust(dt)
        self.ambience.update(dt)
        self._update_steps(dt)
        self._update_npcs(dt)
        if not self.complete:
            self._update_extras(dt)
        if self.pa.update(dt):
            self._sfx("chime")
        for i in range(GATES):
            target = 1.0 if i < self.gates_passed else 0.0
            self.lamps[i] += (target - self.lamps[i]) * min(1.0, dt * 8)
        if self.door_tween is not None:
            self.door_open = self.door_tween.update(dt)
            if self.door_tween.done:
                self.door_tween = None
                self.door_block.size = (0, 0)
        if self.door_open >= 1.0 and not self.complete:
            for player, _ in self._players():
                if player.rect.colliderect(self.exit_zone):
                    self._finish()
                    break

    def _update_extras(self, dt):
        """The camera's beam and the hidden chips."""
        points = {id(p): p.rect.center for p, _ in self._players()}
        if self.watch.update(dt, self.time, points) is not None:
            self.shake.add(0.3)
            if self.game:
                self.game.score.penalize(lobby_extras.SPOT_PENALTY)
            self.guard.say("Hey! Stay out of the beam.")
            self._sfx("alarm")
            self._say(f"WARDEN spotted you! -{lobby_extras.SPOT_PENALTY}", theme.CORAL)
        event = self.phone.update(dt)
        if event == "ring":
            self._sfx("phone")
        elif event == "answer":
            self.receptionist.say(self.phone.line())
        for chip in self.chips:
            if chip.taken:
                continue
            for player, _ in self._players():
                if player.rect.colliderect(chip.rect):
                    self._take_chip(chip)
                    break

    def _take_chip(self, chip):
        chip.taken = True
        self.chips_found += 1
        self._burst(chip.rect.center, theme.TEAL, 10)
        self._sfx("chip")
        points = lobby_extras.CHIP_POINTS
        self.juice.pop((chip.rect.centerx, chip.rect.top - 6), f"+{points}", theme.TEAL)
        if self.chips_found == len(self.chips):
            points += lobby_extras.CHIP_BONUS
            self._say(f"All visitor chips found! +{points}", theme.GOLD)
        else:
            self._say(f"Visitor chip {self.chips_found}/{len(self.chips)}. +{points}", theme.TEAL)
        if self.game:
            self.game.score.add(points)

    def _update_dust(self, dt):
        for puff in self.dust:
            puff["age"] += dt
            puff["y"] -= 14 * dt
        self.dust = [p for p in self.dust if p["age"] < DUST_LIFE]
        for player, _ in self._players():
            clock = self._dust_clock.get(id(player), 0.0)
            if getattr(player, "moving", False):
                clock += dt
                if clock >= DUST_EVERY:
                    clock = 0.0
                    self.dust.append({"x": player.rect.centerx + self.rng.uniform(-6, 6),
                                      "y": player.rect.bottom - 2, "age": 0.0})
            else:
                clock = 0.0
            self._dust_clock[id(player)] = clock

    def _belt_restarted(self):
        """Every parcel filed: the jammed belt is running again."""
        return bool(self.crates) and all(crate.sorted for crate in self.crates)

    @staticmethod
    def _draw_belt_sign(world):
        plate = pygame.Rect(BELT_PLATE)
        pygame.draw.rect(world, theme.INK, plate, border_radius=4)
        pygame.draw.rect(world, theme.TEAL, plate, 1, border_radius=4)
        font = ui_font(12, bold=True)
        for i, line in enumerate(BELT_FIXED_SIGN):
            img = font.render(line, True, theme.TEAL if i == 0 else theme.PAPER)
            world.blit(img, img.get_rect(midtop=(plate.centerx, plate.y + 5 + i * 15)))

    def _finish(self):
        self.complete = True
        for hero, _ in self._players():
            hero.set_outfit(None)              # the disguise comes off in the elevator
        self.receptionist.say(FAREWELL)
        if self.game:
            self.game.score.add(FINISH_BONUS)
        self._say(CLEARED_MESSAGE, theme.GOLD)

    def is_complete(self):
        return self.complete

    # --- drawing --------------------------------------------------------
    def _build_background(self):
        size = self.tilemap.pixel_size
        bg = pygame.Surface(size)
        cam = type("Cam", (), {})()
        cam.offset = lambda: (0, 0)
        cam.x = cam.y = 0
        cam.view_w, cam.view_h = size
        self.tilemap.render(bg, cam, self.tiles)
        pal = theme.floor_palette(LEVEL_KEY)
        accent = pal["accent"]
        novacorp_style.draw_walls(bg, self.tilemap, pal["floor"])
        # reception desk
        draw_panel(bg, self.desk, fill=theme.mix(theme.NAVY, accent, 0.25),
                   border=accent, radius=6)
        label = ui_font(22).render("NOVACORP RECEPTION", True, theme.PAPER)
        bg.blit(label, label.get_rect(center=self.desk.center))
        lobby_decor.draw_static(bg, accent, self.desk)
        for rect in self.plants:
            self._draw_plant(bg, rect)
        self._draw_sofa(bg, self.sofa, accent)
        self._draw_vending(bg, self.vending)
        self._draw_wall_lights(bg, accent)
        self._draw_camera_mount(bg)
        # elevator (left wall)
        elev = pygame.Rect(0, 3 * TILE, 2 * TILE, 3 * TILE)
        draw_panel(bg, elev, fill=theme.NAVY, border=theme.MIST, radius=0, shadow=False)
        pygame.draw.line(bg, theme.SLATE, (elev.centerx, elev.y + 6), (elev.centerx, elev.bottom - 6), 3)
        tag = ui_font(16).render("ELEVATOR", True, theme.MIST)
        bg.blit(tag, tag.get_rect(midtop=(elev.centerx, elev.bottom + 2)))
        # soft pools of light (additive, built once)
        for centre, radius, colour in (
                ((15 * TILE, 10 * TILE), 170, (34, 44, 66)),
                ((2 * TILE, 4 * TILE + 16), 120, (30, 70, 70)),
                ((27 * TILE, 10 * TILE), 110, (60, 40, 40)),
                ((15 * TILE, 15 * TILE), 150, (60, 48, 24))):
            glow = self._glow(radius, colour)
            bg.blit(glow, (centre[0] - radius, centre[1] - radius),
                    special_flags=pygame.BLEND_RGB_ADD)
        # the NovaCorp look: washed out, dark corners, grime, stencils, posters
        for cab in self.cabinets:
            novacorp_style.draw_cabinet(bg, cab)
        self._draw_queue(bg)
        novacorp_style.draw_cooler(bg, self.cooler)
        novacorp_style.grade(bg, seed=4)
        novacorp_style.stains(bg, (2 * TILE, 3 * TILE, 26 * TILE, 15 * TILE), seed=9)
        stencil_font = ui_font(22, bold=True)
        novacorp_style.stencil(bg, "PLEASE REMAIN VISIBLE", (15 * TILE, 10 * TILE), stencil_font, alpha=70)
        novacorp_style.dashed_line(bg, (11 * TILE, 14 * TILE + 6), (19 * TILE, 14 * TILE + 6))
        novacorp_style.stencil(bg, "WAIT HERE", (15 * TILE, 13 * TILE + 10), ui_font(18, bold=True), alpha=90)
        self._draw_belt(bg)
        poster_font = ui_font(12, bold=True)
        novacorp_style.draw_poster(bg, (4, 10 * TILE, 56, 88), ("SMILE!", "WE'RE", "WATCHING"), poster_font)
        novacorp_style.draw_poster(bg, (4, 13 * TILE + 4, 56, 88), ("A CLEAR", "DESK IS", "LOYAL"), poster_font)
        # title on the wall
        title = shadowed(ui_font(26, bold=True), "FLOOR 1 - RECEPTION LOBBY",
                         theme.mix(accent, theme.PAPER, 0.4))
        bg.blit(title, (TILE * 2, TITLE_Y))
        self._title = (title, (TILE * 2, TITLE_Y))
        self._background = bg

    def _lights(self):
        """Every light source on the floor: fixed lamps plus the moving ones."""
        accent = theme.floor_palette(LEVEL_KEY)["accent"]
        warm = theme.mix(accent, theme.PAPER, 0.6)
        out = [lighting.Light((col * TILE, 2 * TILE + 30), 150, warm,
                              0.9 * (lobby_juice.flicker(self.time, col) if col == 12 else 1.0))
               for col in range(4, 28, 4)]
        out.append(lighting.Light((15 * TILE, 9 * TILE), 260, (210, 225, 255), 0.75))          # ceiling panel
        out.append(lighting.Light((15 * TILE, 15 * TILE), 130, (255, 214, 140), 0.8))          # desk lamp
        out.append(lighting.Light((self.vending.centerx, self.vending.centery), 120, (120, 230, 255), 0.9))
        out.append(lighting.Light((2 * TILE, 4 * TILE + 16), 110, (90, 220, 200), 0.7))        # elevator
        lamp = theme.mix(theme.CORAL, theme.TEAL, self.door_open)
        out.append(lighting.Light((self.door.x - 10, self.door.centery), 100, lamp, 0.8))
        alert = 1.0 if self._alerted() else 0.0
        led = theme.mix(theme.CORAL, (255, 40, 40), alert)
        out.append(lighting.Light(self.led_pos, 70, led, 0.7 + 0.3 * math.sin(self.time * 4.0)))
        if not self.complete:
            a = self.beam.angle(self.time)
            reach = self.beam.length * 0.62
            tip = (self.beam.origin[0] + math.cos(a) * reach, self.beam.origin[1] + math.sin(a) * reach)
            danger = self.watch.danger()
            out.append(lighting.Light((int(tip[0]), int(tip[1])), 120,
                                      theme.mix(theme.TEAL, theme.CORAL, danger), 0.9))
        for chip in self.chips:
            if not chip.taken:
                out.append(lighting.Light(chip.rect.center, 36, theme.TEAL, 0.8))
        blink = 0.5 + 0.5 * math.sin(self.time * 5.0)
        out.append(lighting.Light((BELT_JAM[0], BELT_JAM[1] - 4), 56, theme.CORAL, 0.35 + 0.55 * blink))   # jam lamp
        return out

    def _draw_shadows(self, world):
        for crate in self.crates:
            if not crate.sorted and crate.carrier is None:
                lighting.blob_shadow(world, crate.rect, 90)
        for npc in self.npcs:
            lighting.blob_shadow(world, npc.rect, 90)
        for rect in (self.desk, self.vending, self.cooler, *self.cabinets, *self.plants):
            lighting.blob_shadow(world, rect.inflate(10, 0), 60, squash=0.3)
        for rect in self.posts:
            lighting.blob_shadow(world, rect, 70, squash=0.5)

    def _dress(self):
        """Ghost (and Echo) wear the courier vest for as long as this floor is running."""
        if not self.complete:
            for hero, _ in self._players():
                hero.set_outfit("courier")

    def _draw_queue(self, bg):
        """Posts and sagging red rope: the visitor queue ends in a gap in front of the desk."""
        pairs = ((QUEUE_POSTS[0], QUEUE_POSTS[1]), (QUEUE_POSTS[2], QUEUE_POSTS[3]))
        for a, b in pairs:
            top_a, top_b = (a, QUEUE_Y - 18), (b, QUEUE_Y - 18)
            mid = ((a + b) // 2, QUEUE_Y - 18 + 7)
            points = [((1 - u) ** 2 * top_a[0] + 2 * (1 - u) * u * mid[0] + u ** 2 * top_b[0],
                       (1 - u) ** 2 * top_a[1] + 2 * (1 - u) * u * mid[1] + u ** 2 * top_b[1])
                      for u in [i / 12 for i in range(13)]]
            pygame.draw.lines(bg, (92, 18, 26), False, points, 5)
            pygame.draw.lines(bg, (176, 44, 52), False, points, 3)
        for x in QUEUE_POSTS:
            pygame.draw.ellipse(bg, (14, 16, 22), (x - 8, QUEUE_Y + 1, 16, 7))                  # base
            pygame.draw.line(bg, (150, 156, 168), (x, QUEUE_Y + 3), (x, QUEUE_Y - 16), 3)        # pole
            pygame.draw.line(bg, (214, 220, 230), (x - 1, QUEUE_Y + 2), (x - 1, QUEUE_Y - 15), 1)
            pygame.draw.circle(bg, (206, 168, 64), (x, QUEUE_Y - 18), 4)                        # brass cap
            pygame.draw.circle(bg, (246, 218, 130), (x - 1, QUEUE_Y - 19), 1)

    def _draw_belt(self, bg):
        """The intake belt above the chutes: it feeds them, but it is jammed, which is
        why the parcels are on the floor. A sign says so."""
        belt = pygame.Rect(BELT_JAM[0] - 20, 98, 712 - (BELT_JAM[0] - 20), 14)
        pygame.draw.rect(bg, (30, 34, 44), belt)
        pygame.draw.rect(bg, (70, 78, 92), belt, 1)
        for x in range(belt.x + 6, belt.right - 4, 8):               # rollers
            pygame.draw.line(bg, (54, 60, 74), (x, belt.y + 2), (x, belt.bottom - 3), 2)
        for dx, dy, w in ((0, 0, 16), (10, -6, 14), (22, 1, 12)):    # parcels stuck at the jam
            box = pygame.Rect(BELT_JAM[0] - 8 + dx, 98 + dy, w, 12)
            pygame.draw.rect(bg, (170, 128, 84), box, border_radius=2)
            pygame.draw.rect(bg, (96, 70, 44), box, 1, border_radius=2)
        plate = pygame.Rect(BELT_PLATE)
        pygame.draw.rect(bg, theme.INK, plate, border_radius=4)
        pygame.draw.rect(bg, theme.CORAL, plate, 1, border_radius=4)
        font = ui_font(12, bold=True)
        for i, line in enumerate(BELT_SIGN):
            img = font.render(line, True, theme.PAPER if i else theme.CORAL)
            bg.blit(img, img.get_rect(midtop=(plate.centerx, plate.y + 5 + i * 15)))

    @staticmethod
    def _glow(radius, colour):
        """Radial falloff on black, meant for additive blending."""
        surf = pygame.Surface((radius * 2, radius * 2))
        for r in range(radius, 0, -3):
            k = (1.0 - r / radius) ** 2
            pygame.draw.circle(surf, tuple(int(c * k) for c in colour), (radius, radius), r)
        return surf

    @staticmethod
    def _draw_plant(bg, rect):
        pot = pygame.Rect(rect.x + 8, rect.y + 18, 16, 12)
        pygame.draw.rect(bg, (0, 0, 0), pot.move(2, 2), border_radius=3)
        pygame.draw.rect(bg, (150, 96, 70), pot, border_radius=3)
        pygame.draw.rect(bg, (190, 130, 96), (pot.x, pot.y, pot.w, 3), border_radius=2)
        for dx, dy, r in ((0, 4, 9), (-7, 8, 7), (7, 8, 7), (0, -2, 7)):
            pygame.draw.circle(bg, (46, 150, 100), (rect.centerx + dx, rect.y + 12 + dy), r)
        for dx, dy in ((-3, 0), (4, 4), (-8, 7)):
            pygame.draw.circle(bg, (110, 210, 150), (rect.centerx + dx, rect.y + 8 + dy), 3)

    @staticmethod
    def _draw_sofa(bg, rect, accent):
        base = theme.mix(accent, theme.NAVY, 0.55)
        body = rect.inflate(0, 6)
        pygame.draw.rect(bg, (0, 0, 0), body.move(2, 3), border_radius=8)
        pygame.draw.rect(bg, base, body, border_radius=8)
        pygame.draw.rect(bg, theme.mix(base, theme.PAPER, 0.18),
                         (body.x + 4, body.y + 3, body.w - 8, 10), border_radius=5)
        third = body.w // 3
        for i in (1, 2):
            pygame.draw.line(bg, theme.mix(base, theme.INK, 0.4),
                             (body.x + i * third, body.y + 14), (body.x + i * third, body.bottom - 3), 2)
        pygame.draw.rect(bg, theme.mix(base, theme.INK, 0.4), body, 2, border_radius=8)

    @staticmethod
    def _draw_vending(bg, rect):
        draw_panel(bg, rect, fill=theme.mix(theme.NAVY, theme.CORAL, 0.2),
                   border=theme.CORAL, radius=4)
        window = pygame.Rect(rect.x + 5, rect.y + 6, rect.w - 10, rect.h - 28)
        pygame.draw.rect(bg, theme.INK, window, border_radius=3)
        for row in range(3):
            for col in range(2):
                pygame.draw.rect(bg, (theme.GOLD, theme.TEAL, theme.SKY)[(row + col) % 3],
                                 (window.x + 3 + col * 11, window.y + 4 + row * 11, 8, 7),
                                 border_radius=2)
        pygame.draw.rect(bg, theme.MIST, (rect.x + 8, rect.bottom - 16, rect.w - 16, 6), border_radius=2)

    @staticmethod
    def _draw_wall_lights(bg, accent):
        glow = theme.mix(accent, theme.PAPER, 0.55)
        for col in range(4, 28, 4):
            x = col * TILE
            pygame.draw.rect(bg, theme.mix(theme.INK, accent, 0.4), (x - 14, 2 * TILE + 24, 28, 6), border_radius=3)
            pygame.draw.rect(bg, glow, (x - 10, 2 * TILE + 26, 20, 2), border_radius=1)

    @staticmethod
    def _draw_camera_mount(bg):
        x, y = 20 * TILE, 2 * TILE + 4
        pygame.draw.rect(bg, theme.SLATE, (x, y, 22, 12), border_radius=3)
        pygame.draw.rect(bg, theme.MIST, (x, y, 22, 12), 1, border_radius=3)
        pygame.draw.circle(bg, theme.INK, (x + 6, y + 6), 4)
        pygame.draw.circle(bg, theme.MIST, (x + 6, y + 6), 4, 1)

    def _alerted(self):
        """True once security is at half or more: the camera turns red."""
        return bool(self.game is not None and getattr(self.game, "security", None)
                    and self.game.security.level >= self.game.security.max_level * 0.5)

    def _draw_camera_led(self, world):
        pulse = 0.5 + 0.5 * math.sin(self.time * 4.0)
        alert = 1.0 if self._alerted() else 0.0
        colour = theme.mix(theme.mix(theme.SLATE, theme.CORAL, 0.35 + 0.65 * pulse),
                           theme.CORAL, alert)
        pygame.draw.circle(world, colour, self.led_pos, 3)

    def _draw_jam_lamp(self, world):
        on = math.sin(self.time * 5.0) > 0
        colour = theme.CORAL if on else theme.mix(theme.SLATE, theme.CORAL, 0.25)
        pygame.draw.circle(world, colour, (BELT_JAM[0], BELT_JAM[1] - 14), 3)

    def _draw_beam(self, world):
        if self.complete:
            return
        if self._beam_overlay is None or self._beam_overlay.get_size() != world.get_size():
            self._beam_overlay = pygame.Surface(world.get_size(), pygame.SRCALPHA)
        lobby_extras.draw_beam(self._beam_overlay, self.beam, self.time, self.watch.danger())
        world.blit(self._beam_overlay, (0, 0))

    def _draw_dust(self, world):
        for puff in self.dust:
            k = puff["age"] / DUST_LIFE
            radius = 2 + int(4 * k)
            tint = theme.mix(theme.MIST, theme.floor_palette(LEVEL_KEY)["floor"], k)
            pygame.draw.circle(world, tint, (int(puff["x"]), int(puff["y"])), radius)

    def _draw_bins(self, surf, active=()):
        for t, rect in self.bins.items():
            sx, sy = self.bin_pulse[t].scale
            w, h = int(rect.w * sx), int(rect.h * sy)
            r = pygame.Rect(0, 0, w, h)
            r.midbottom = rect.midbottom
            colour = BIN_COLOURS[t]
            draw_panel(surf, r, fill=theme.mix(theme.NAVY, colour, 0.3), border=colour, radius=6)
            txt = self.code_big.render(t, True, theme.PAPER)
            surf.blit(txt, txt.get_rect(center=r.center))
            if t in active:                                  # a player is carrying a crate to this bin
                glow = theme.mix(colour, theme.PAPER, 0.5 + 0.5 * math.sin(self.time * 6))
                pygame.draw.rect(surf, glow, r.inflate(8, 8), 2, border_radius=9)

    def _draw_crate(self, surf, crate, rect, highlight=False):
        """A cardboard parcel with packing tape, a shipping label and a floating value
        tag (neutral colour: the tag must not give away the chute)."""
        hit = pygame.Rect(rect)
        body = pygame.Rect(0, 0, int(hit.w * 1.3), int(hit.h * 1.15))
        body.center = hit.center
        pal = theme.floor_palette(LEVEL_KEY)
        wood = theme.mix((178, 136, 88), pal["floor"], 0.10)
        dark = theme.mix(wood, theme.INK, 0.5)
        pygame.draw.rect(surf, (0, 0, 0), body.move(2, 3), border_radius=4)
        pygame.draw.rect(surf, wood, body, border_radius=4)
        pygame.draw.rect(surf, theme.mix(wood, theme.PAPER, 0.22),
                         (body.x + 2, body.y + 2, body.w - 4, 5), border_radius=2)   # lit top flap
        tape = pygame.Rect(0, body.y, 6, body.h)
        tape.centerx = body.centerx
        pygame.draw.rect(surf, (214, 190, 140), tape)                                # packing tape
        label = pygame.Rect(body.x + 4, body.bottom - 13, 13, 9)
        pygame.draw.rect(surf, (238, 238, 232), label)                               # shipping label
        for bx in range(label.x + 2, label.right - 1, 2):
            pygame.draw.line(surf, theme.INK, (bx, label.y + 4), (bx, label.bottom - 2), 1)
        pygame.draw.rect(surf, (200, 60, 50), (label.x + 2, label.y + 1, 5, 2))
        pygame.draw.rect(surf, dark, body, 2, border_radius=4)
        txt = self.code.render(display(crate.value), True, theme.PAPER)
        tag = txt.get_rect().inflate(10, 4)
        tag.midbottom = (body.centerx, body.top - 3)
        tag.clamp_ip(pygame.Rect(0, 0, *self.tilemap.pixel_size))
        pygame.draw.rect(surf, theme.INK, tag, border_radius=4)
        pygame.draw.rect(surf, theme.MIST, tag, 1, border_radius=4)
        surf.blit(txt, txt.get_rect(center=tag.center))
        if highlight:                                        # "you can pick this up": a ring and an E key
            ring = theme.mix(theme.PAPER, theme.TEAL, 0.5 + 0.5 * math.sin(self.time * 6))
            pygame.draw.rect(surf, ring, body.inflate(8, 8), 2, border_radius=6)
            key = pygame.Rect(0, 0, 18, 18)
            key.midbottom = (tag.centerx, tag.top - 3)
            key.clamp_ip(pygame.Rect(0, 0, *self.tilemap.pixel_size))
            pygame.draw.rect(surf, theme.INK, key, border_radius=4)
            pygame.draw.rect(surf, ring, key, 1, border_radius=4)
            letter = self.small.render("E", True, ring)
            surf.blit(letter, letter.get_rect(center=key.center))

    def _draw_exit(self, surf):
        d = self.door
        pygame.draw.rect(surf, theme.INK, d)
        open_px = int((d.h // 2) * self.door_open)
        top = pygame.Rect(d.x, d.y - open_px, d.w, d.h // 2)
        bot = pygame.Rect(d.x, d.centery + open_px, d.w, d.h // 2)
        for half in (top, bot):
            pygame.draw.rect(surf, theme.SLATE, half)
            pygame.draw.rect(surf, theme.MIST, half, 2)
        lamp = theme.mix(theme.CORAL, theme.TEAL, self.door_open)
        pygame.draw.circle(surf, lamp, (d.x - 10, d.centery), 6)
        if self.door_open >= 1.0:
            pulse = 0.5 + 0.5 * math.sin(self.time * 6)
            arrow = theme.mix(theme.TEAL, theme.PAPER, pulse)
            cx, cy = d.centerx + 8, d.centery
            pygame.draw.polygon(surf, arrow, [(cx - 12, cy - 10), (cx + 8, cy), (cx - 12, cy + 10)])
        tag = self.small.render("EXIT", True, theme.MIST)
        surf.blit(tag, tag.get_rect(midbottom=(d.centerx, d.y - 12)))
        stamps = self.small.render("STAMPS", True, theme.MIST)
        surf.blit(stamps, stamps.get_rect(midbottom=(d.x - 2, d.y - 44)))
        for i in range(GATES):                       # one lamp (stamp) per gate, above the door
            colour = theme.mix(theme.SLATE, theme.TEAL, self.lamps[i])
            pos = (d.x - 30 + i * 28, d.y - 34)
            pygame.draw.circle(surf, colour, pos, 8)
            pygame.draw.circle(surf, theme.MIST, pos, 8, 2)

    def render(self, surface):
        if self._background is None:
            self._build_background()
        world = self._background.copy()
        if self._belt_restarted():
            self._draw_belt_sign(world)
        self.ambience.draw(world, self.desk, self.vending, self._alerted())
        for t, rect in self.bins.items():
            lobby_juice.draw_chute(world, rect, BIN_COLOURS[t], 96, self.time, self.juice.flash.get(t, 0.0))
        self._draw_bins(world, self._prompted_bins())
        self._draw_exit(world)
        self._draw_beam(world)
        self._draw_camera_led(world)
        self._draw_jam_lamp(world)
        lobby_extras.draw_phone(world, self.desk, self.phone.is_ringing, self.time)
        for chip in self.chips:
            if not chip.taken:
                lobby_extras.draw_chip(world, chip, self.time)
        self._draw_dust(world)
        lobby_juice.draw_fan_shadow(world, (15 * TILE, 10 * TILE), self.time)
        self._draw_shadows(world)
        prompted = self._prompted_crates()
        for crate in self.crates:
            if crate.sorted or crate.carrier is not None:
                continue
            bob = int(math.sin(self.time * 2 + crate.bob) * 1.5)
            self._draw_crate(world, crate, crate.rect.move(0, bob), crate in prompted)
        for player, _ in self._players():
            crate = self.carried.get(id(player))
            if crate is not None:
                sx, sy = self.crate_pop.scale
                r = pygame.Rect(0, 0, int(28 * sx), int(28 * sy))
                r.midbottom = (player.rect.centerx, player.rect.top - 2)
                crate.rect = r
                self._draw_crate(world, crate, r)
        for npc in self.npcs:
            npc.draw(world, self.small)
        for s in self.sparks:
            size = max(1, int(4 * s["life"] / 0.6))
            pygame.draw.circle(world, s["colour"], (int(s["x"]), int(s["y"])), size)
        self.juice.draw_flyers(world, self.small)
        self.lightlayer.apply(world, self._lights())
        self.juice.draw_popups(world, self.popup_font)
        if self._title is not None:
            world.blit(*self._title)           # the title stays readable above the lighting
        # message strip on the wall, under the HUD
        if self.message:
            msg = shadowed(self.font, self.message, self.message_tone)
            world.blit(msg, (TILE * 2, MESSAGE_Y))
        novacorp_style.draw_speaker(world, PA_SPEAKER, self.time, self.pa.active)
        if self.pa.active:
            line = shadowed(ui_font(16), self.pa.caption, theme.PAPER)
            line.set_alpha(self.pa.alpha())
            world.blit(line, PA_CAPTION)
        hint = shadowed(self.small, "E: pick up / put down", theme.MIST)
        world.blit(hint, (world.get_width() - hint.get_width() - TILE * 2, TITLE_Y + 2))
        chips = shadowed(self.small, f"CHIPS {self.chips_found}/{len(self.chips)}",
                         theme.TEAL if self.chips_found else theme.MIST)
        world.blit(chips, (world.get_width() - chips.get_width() - TILE * 2, TITLE_Y + 24))
        if self.juice.streak_visible():
            streak = shadowed(self.small, f"STREAK x{self.juice.streak}", theme.GOLD)
            world.blit(streak, (world.get_width() - chips.get_width() - streak.get_width() - TILE * 2 - 16, TITLE_Y + 24))
        ox, oy = self.shake.offset()
        surface.fill(theme.INK)
        surface.blit(world, (ox, oy))
