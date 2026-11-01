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
Not registered by default; start the game with MEMORY_HEIST_NEW_FLOOR1=1 to
play it in place of Level 1.
"""

import math
import random

import pygame

from core.animation import Shake, SquashStretch
from core.easing import Tween, ease_out_cubic
from core.tilemap import TILE, TileMap, make_tiles
from ui import theme
from ui.kit import draw_panel

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
DUST_EVERY = 0.12               # seconds between footstep puffs while walking
DUST_LIFE = 0.45


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
        self.message = "Carry each crate to the bin for its data type."
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
        self._dust_clock = {}
        self.time = 0.0

        self.font = pygame.font.Font(None, 24)
        self.small = pygame.font.Font(None, 20)
        self.big = pygame.font.Font(None, 30)
        self._background = None

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
            self._pick_up(player)
            return
        for t, rect in self.bins.items():
            if self._near(player, rect):
                self._drop_in_bin(player, crate, t)
                return
        self._put_down(player, crate)

    def _pick_up(self, player):
        best, best_d = None, 1e9
        for crate in self.crates:
            if crate.sorted or crate.carrier is not None:
                continue
            if not self._near(player, crate.rect):
                continue
            d = math.dist(crate.rect.center, player.rect.center)
            if d < best_d:
                best, best_d = crate, d
        if best is None:
            return
        best.carrier = player
        self.carried[id(player)] = best
        self._sync_carried()
        self.crate_pop.trigger(0.35)
        self._say(f"Got {display(best.value)}. Which bin?", theme.PAPER)

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

    def _drop_in_bin(self, player, crate, bin_type):
        del self.carried[id(player)]
        crate.carrier = None
        self.bin_pulse[bin_type].trigger(0.5)
        centre = self.bins[bin_type].center
        if crate.answer == bin_type:
            crate.sorted = True
            self.sorted_count += 1
            self._burst(centre, BIN_COLOURS[bin_type], 18)
            if self.game:
                self.game.score.add(CRATE_POINTS)
            self._say(f"{display(crate.value)} is {with_article(bin_type)}. Correct!", theme.TEAL)
            self._check_gates()
        else:
            crate.rect = crate.home.copy()
            self.shake.add(0.55)
            self._burst(centre, theme.CORAL, 12)
            hint = HINTS[crate.answer]
            if self.game and not self.game.hints.enabled:
                hint = "Hints are off on this difficulty."
            self._say(f"Not {with_article(bin_type)}. {hint}", theme.CORAL)
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
            self._say("Badge reader online. The exit is open.", theme.GOLD)

    # --- helpers --------------------------------------------------------
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
        self._sync_carried()
        self.time += dt
        self._message_age += dt
        self.shake.update(dt)
        self.crate_pop.update(dt)
        for pulse in self.bin_pulse.values():
            pulse.update(dt)
        for s in self.sparks:
            s["x"] += s["vx"] * dt
            s["y"] += s["vy"] * dt
            s["vy"] += 260 * dt
            s["life"] -= dt
        self.sparks = [s for s in self.sparks if s["life"] > 0]
        self._update_dust(dt)
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

    def _finish(self):
        self.complete = True
        if self.game:
            self.game.score.add(FINISH_BONUS)
        self._say("Reception cleared. The elevator is waiting.", theme.GOLD)

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
        # reception desk
        draw_panel(bg, self.desk, fill=theme.mix(theme.NAVY, accent, 0.25),
                   border=accent, radius=6)
        label = pygame.font.Font(None, 22).render("NOVACORP RECEPTION", True, theme.PAPER)
        bg.blit(label, label.get_rect(center=self.desk.center))
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
        tag = pygame.font.Font(None, 16).render("ELEVATOR", True, theme.MIST)
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
        # title on the wall
        title = pygame.font.Font(None, 30).render("FLOOR 1 - RECEPTION LOBBY", True,
                                                  theme.mix(accent, theme.PAPER, 0.4))
        bg.blit(title, (TILE * 2, 2 * TILE + 2))
        self._background = bg

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

    def _draw_camera_led(self, world):
        pulse = 0.5 + 0.5 * math.sin(self.time * 4.0)
        alert = 1.0 if self.game is not None and getattr(self.game, "security", None) \
            and self.game.security.level >= self.game.security.max_level * 0.5 else 0.0
        colour = theme.mix(theme.mix(theme.SLATE, theme.CORAL, 0.35 + 0.65 * pulse),
                           theme.CORAL, alert)
        pygame.draw.circle(world, colour, self.led_pos, 3)

    def _draw_dust(self, world):
        for puff in self.dust:
            k = puff["age"] / DUST_LIFE
            radius = 2 + int(4 * k)
            tint = theme.mix(theme.MIST, theme.floor_palette(LEVEL_KEY)["floor"], k)
            pygame.draw.circle(world, tint, (int(puff["x"]), int(puff["y"])), radius)

    def _draw_bins(self, surf):
        for t, rect in self.bins.items():
            sx, sy = self.bin_pulse[t].scale
            w, h = int(rect.w * sx), int(rect.h * sy)
            r = pygame.Rect(0, 0, w, h)
            r.midbottom = rect.midbottom
            colour = BIN_COLOURS[t]
            draw_panel(surf, r, fill=theme.mix(theme.NAVY, colour, 0.3), border=colour, radius=6)
            txt = self.big.render(t, True, theme.PAPER)
            surf.blit(txt, txt.get_rect(center=r.center))

    def _draw_crate(self, surf, crate, rect):
        """A bigger wooden crate with a floating value tag (neutral colour: the
        tag must not give away the bin)."""
        hit = pygame.Rect(rect)
        body = pygame.Rect(0, 0, int(hit.w * 1.3), int(hit.h * 1.15))
        body.center = hit.center
        pal = theme.floor_palette(LEVEL_KEY)
        wood = theme.mix((150, 100, 60), pal["floor"], 0.12)
        dark = theme.mix(wood, theme.INK, 0.5)
        pygame.draw.rect(surf, (0, 0, 0), body.move(2, 3), border_radius=4)
        pygame.draw.rect(surf, wood, body, border_radius=4)
        for x in (body.x + body.w // 3, body.x + 2 * body.w // 3):
            pygame.draw.line(surf, dark, (x, body.y + 3), (x, body.bottom - 3), 1)
        pygame.draw.rect(surf, theme.mix(wood, theme.PAPER, 0.28),
                         (body.x + 2, body.y + 2, body.w - 4, 5), border_radius=2)
        pygame.draw.rect(surf, dark, body, 2, border_radius=4)
        for cx, cy in ((body.x + 4, body.y + 4), (body.right - 5, body.y + 4),
                       (body.x + 4, body.bottom - 5), (body.right - 5, body.bottom - 5)):
            pygame.draw.circle(surf, theme.MIST, (cx, cy), 1)
        txt = self.small.render(display(crate.value), True, theme.PAPER)
        tag = txt.get_rect().inflate(10, 4)
        tag.midbottom = (body.centerx, body.top - 3)
        tag.clamp_ip(pygame.Rect(0, 0, *self.tilemap.pixel_size))
        pygame.draw.rect(surf, theme.INK, tag, border_radius=4)
        pygame.draw.rect(surf, theme.MIST, tag, 1, border_radius=4)
        surf.blit(txt, txt.get_rect(center=tag.center))

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
        for i in range(GATES):                       # one lamp per gate, above the door
            colour = theme.mix(theme.SLATE, theme.TEAL, self.lamps[i])
            pos = (d.x - 30 + i * 28, d.y - 34)
            pygame.draw.circle(surf, colour, pos, 8)
            pygame.draw.circle(surf, theme.MIST, pos, 8, 2)

    def render(self, surface):
        if self._background is None:
            self._build_background()
        world = self._background.copy()
        self._draw_bins(world)
        self._draw_exit(world)
        self._draw_camera_led(world)
        self._draw_dust(world)
        for crate in self.crates:
            if crate.sorted or crate.carrier is not None:
                continue
            bob = int(math.sin(self.time * 2 + crate.bob) * 1.5)
            self._draw_crate(world, crate, crate.rect.move(0, bob))
        for player, _ in self._players():
            crate = self.carried.get(id(player))
            if crate is not None:
                sx, sy = self.crate_pop.scale
                r = pygame.Rect(0, 0, int(28 * sx), int(28 * sy))
                r.midbottom = (player.rect.centerx, player.rect.top - 2)
                crate.rect = r
                self._draw_crate(world, crate, r)
        for s in self.sparks:
            size = max(1, int(4 * s["life"] / 0.6))
            pygame.draw.circle(world, s["colour"], (int(s["x"]), int(s["y"])), size)
        # message strip on the wall, under the HUD
        if self.message:
            msg = self.font.render(self.message, True, self.message_tone)
            world.blit(msg, (TILE * 2, 2 * TILE + 26))
        hint = self.small.render("E: pick up / put down", True, theme.MIST)
        world.blit(hint, (world.get_width() - hint.get_width() - TILE * 2, 2 * TILE + 4))
        ox, oy = self.shake.offset()
        surface.fill(theme.INK)
        surface.blit(world, (ox, oy))
