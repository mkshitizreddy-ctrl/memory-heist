"""
core/hero_sprites.py
Owner: Member 1 - Core Game System

In-world sprites for Ghost and Echo: 20x20 pixel art drawn from text grids,
scaled 2x nearest-neighbour to 40 x 42, about a third taller than any NPC
(the player's collision box stays 32x32; the sprite stands on its feet, centred).
They match the portraits (Ghost: hood, cyan visor, chip slot. Echo: orange
ponytail, gold goggles, headset) so the hero reads as the same person on the
HUD, in cutscenes and in the levels.

Same shape as entities.sprites.make_player_frames, plus a blink frame:
    {"idle": surface, "walk": [4 surfaces], "blink": surface}
facing right (Player flips for left).
"""

import pygame

SCALE = 2
GRID = 16

# The NPCs' 16-wide leg rows (core/npc_sprites.py builds on them).
_LEGS = {
    "idle":   ["....CCC.CCC.....", "....BBB.BBB....."],
    "step_a": ["...CCC....CCC...", "...BBB....BBB..."],
    "step_b": ["......CCCC......", "......BBBB......"],
}

# --- the main characters: 20 x 20 source pixels, drawn at 40 x 42 -----------------
# NPCs are 16 x 16 chibi office staff (32 px). The heroes are built differently on
# purpose: a wider grid, adult proportions (small head, long body) and silhouettes
# nobody at NovaCorp has, so they read as the leads at a glance, not as more guards.
# They stand about a third taller than an NPC; the collision box stays 32 x 32 at their feet.
#
# Ghost (Ash): a peaked hood over a deep void with a cyan visor slit, a pale scarf
#   whose tail hangs behind, a long slate cloak split into tails at the knee, and the
#   glowing chip slot on the chest (the memory chip from the story).
# Echo (radio handler): orange hair in a ponytail, gold goggles pushed up, a headset
#   with a whip antenna and a red tip lamp, a teal field jacket with amber trim and a
#   radio pack on her back with amber status lamps.
#
# Legend: H/h hood, D hood void, V visor, v visor glint, S/s scarf, C cloak, c cloak edge,
#   I inner coat, X chip glow, G glove, L belt, b buckle, N trousers, B boots,
#   O hair, K skin, e eye, Y goggles, M headset, m mic, r antenna lamp, J jacket,
#   T trim, P radio pack, p pack lamp.
HERO_GRID = 20
_GHOST_TALL_HEAD = [
    "....................",
    "......HH............",
    ".....HhhHH..........",
    "....HhhhhhHH........",
    "...HhhhhDDDDH.......",
    "...HhhhDVVVvH.......",
    "...HhhhDDDDDH.......",
    "...HHhhhDDDH........",
]
_GHOST_TALL_BODY = [
    "...SSSSSSSSSS.......",
    "..ssSSCCCCCCCC......",
    "..s.cCCCIICCCCG.....",
    "..s.cCCCIXICCCG.....",
    "....cCCLLLbLCCC.....",
    "...GcCCCIIICCCC.....",
    "....cCCCC.CCCCC.....",
    "...cCCCC...CCCCc....",
]
_ECHO_TALL_HEAD = [
    "....................",
    "........r...........",
    "........M.OOOO......",
    ".......OMOOOOOOO....",
    "......OOMOYYYYYO....",
    "..OO.OOMMOOKKKKK....",
    ".OOOOOOMMOKKeKKK....",
    "..OO..OOOKKKKKmm....",
    ".......OOKKKK.......",
]
_ECHO_TALL_BODY = [
    "...PPTJJJJJJT.......",
    "..PPpPJTJJJJJJ......",
    "..PPPPJJTJJJJJG.....",
    "..PPpPJJJTJJJJG.....",
    "...PPJLLLbLLJJ......",
    "....JJJJJJJJJJ......",
    "....JJJJJJJJJJ......",
]
_HERO_LEGS = {
    "idle":   [".....NNN..NNN.......", ".....NNN..NNN.......",
               ".....BBB..BBBB......", "....BBBB..BBBBB....."],
    "step_a": ["....NNN....NNN......", "...NNN......NNN.....",
               "...BBB......BBBB....", "..BBBB.......BBBB..."],
    "step_b": ["......NNNN..........", "......NNNN..........",
               "......BBBBB.........", ".....BBBBBB........."],
}
_ECHO_HERO_LEGS = _HERO_LEGS
HERO_ROWS = len(_GHOST_TALL_HEAD) + len(_GHOST_TALL_BODY) + len(_HERO_LEGS["idle"])     # 20

PALETTES = {
    "ghost": {
        "H": (70, 80, 104), "h": (104, 116, 146), "D": (6, 10, 20),
        "V": (90, 240, 255), "v": (210, 252, 255),
        "S": (184, 204, 210), "s": (150, 172, 182),
        "C": (76, 86, 110), "c": (140, 164, 190), "I": (34, 38, 54),
        "X": (90, 240, 255), "G": (178, 186, 206),
        "L": (34, 36, 50), "b": (90, 240, 255), "N": (46, 50, 66), "B": (20, 22, 32),
    },
    "echo": {
        "O": (214, 110, 44), "K": (232, 192, 156), "e": (34, 28, 34),
        "Y": (250, 190, 70), "M": (58, 62, 74), "m": (120, 126, 140), "r": (255, 70, 60),
        "J": (44, 128, 126), "T": (240, 170, 60), "G": (232, 192, 156),
        "P": (70, 74, 84), "p": (255, 190, 70),
        "L": (74, 50, 32), "b": (240, 200, 90), "N": (52, 48, 62), "B": (50, 34, 28),
    },
}
# Each hero's rim light, in place of the cool grey one the NPCs get: a thin coloured
# edge (Ghost cyan, Echo amber) that marks the player characters in every room.
HERO_RIM = {"ghost": (90, 240, 255, 150), "echo": (255, 180, 70, 150)}
_PARTS = {
    "ghost": (_GHOST_TALL_HEAD, _GHOST_TALL_BODY, _HERO_LEGS),
    "echo": (_ECHO_TALL_HEAD, _ECHO_TALL_BODY, _ECHO_HERO_LEGS),
}

HEROES = tuple(PALETTES)

# --- the courier disguise (Floor 1) ------------------------------------------
# A red delivery cap with a brim over the hood or hair, and a hi-vis orange
# vest with a silver reflective stripe over the coat. The visor, goggles and
# silhouette stay, so the hero is still recognisable.
# Legend: P cap, p brim, R hi-vis vest, r reflective stripe.
OUTFITS = ("courier",)
COURIER_COLOURS = {
    "P": (196, 62, 52), "p": (112, 30, 28),
    "R": (255, 150, 34), "r": (226, 232, 238),
}
_COURIER_CAP = [".....PPPPPP.........", "....PPPPPPPPpp......"]
_VEST_CLOTH = {"ghost": "CcI", "echo": "JT"}


def _courier_parts(name):
    """Red cap over the hood or hair; the torso cloth becomes a hi-vis vest with one
    reflective stripe. Cloak tails, scarf, visor, goggles and radio pack stay."""
    head, body, legs = _PARTS[name]
    head = head[:1] + _COURIER_CAP + head[3:]
    cloth = _VEST_CLOTH[name]
    vest = []
    for i, row in enumerate(body):
        if i >= len(body) - 2:                          # the tails / hem keep the hero's own colour
            vest.append(row)
            continue
        fill = "r" if i == 2 else "R"
        vest.append("".join(fill if ch in cloth else ch for ch in row))
    return head, vest, legs

# What the eyes become mid-blink: the visor / goggles dim to a thin dark band.
BLINK_COLOURS = {
    "ghost": {"V": (24, 70, 86), "v": (24, 70, 86)},
    "echo": {"e": (226, 188, 152)},                      # her goggles are up; her eyes close
}


OUTLINE = (6, 10, 20, 255)


# Pixels that keep their exact colour when the shading pass runs: eyes, visor,
# goggles, the dark hood void, and the guard's badge.
UNSHADED = frozenset("VvYDegbXrp")
LIGHT_AMOUNT = 0.22      # top edges catch light
SHADE_AMOUNT = 0.26      # undersides fall into shadow
SIDE_SHADE = 0.12        # the right edge turns away from the light


def _tone(colour, target, amount):
    return tuple(round(c + (t - c) * amount) for c, t in zip(colour, target))


def _filled(rows, x, y):
    return 0 <= y < len(rows) and 0 <= x < len(rows[y]) and rows[y][x] != "."


def _shaded(rows, x, y, ch, palette):
    """One pixel's colour: lit on a top edge, darker on an underside or right edge."""
    colour = palette[ch]
    if ch in UNSHADED:
        return colour
    if not _filled(rows, x, y - 1):
        return _tone(colour, (255, 255, 255), LIGHT_AMOUNT)
    if not _filled(rows, x, y + 1):
        return _tone(colour, (0, 0, 0), SHADE_AMOUNT)
    if not _filled(rows, x + 1, y):
        return _tone(colour, (0, 0, 0), SIDE_SHADE)
    return colour


def _build(rows, palette):
    width = len(rows[0])                                 # NPCs are 16 wide, the heroes 20
    height = max(GRID, len(rows) + 1)                    # NPCs are 16 rows; the heroes are taller (+ an outline row)
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                surf.set_at((x, y), _shaded(rows, x, y, ch, palette) + (255,))
    # 1px dark outline so the hero reads on light and dark floors alike.
    edge = []
    for y in range(height):
        for x in range(width):
            if surf.get_at((x, y))[3] == 0:
                near = any(
                    0 <= x + dx < width and 0 <= y + dy < height
                    and surf.get_at((x + dx, y + dy))[3] > 0
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if near:
                    edge.append((x, y))
    for pos in edge:
        surf.set_at(pos, OUTLINE)
    return pygame.transform.scale(surf, (width * SCALE, height * SCALE))


def bob_rows(head, body):
    """Squash-and-stretch on a stride: the crown row goes, so the face sits a pixel higher,
    and the torso gains a row. The blank top row stays, so the outline still fits."""
    return head[:1] + head[2:] + body + [body[-1]]


def make_hero_frames(name, outfit=None):
    """{"idle": surf, "walk": [surf x4]} for 'ghost' or 'echo', optionally in an outfit."""
    if name not in _PARTS:
        raise ValueError(f"unknown hero {name!r}; expected one of {HEROES}")
    if outfit is not None and outfit not in OUTFITS:
        raise ValueError(f"unknown outfit {outfit!r}; expected one of {OUTFITS}")
    head, body, legs = _PARTS[name]
    palette = PALETTES[name]
    if outfit == "courier":
        head, body, legs = _courier_parts(name)
        palette = {**palette, **COURIER_COLOURS}

    def frame(key):
        upper = bob_rows(head, body) if key.startswith("step") else head + body
        return _build(upper + legs[key], palette)

    blink_palette = {**palette, **BLINK_COLOURS[name]}
    return {
        "idle": frame("idle"),
        "walk": [frame("step_a"), frame("idle"), frame("step_b"), frame("idle")],
        "blink": _build(head + body + legs["idle"], blink_palette),
    }
