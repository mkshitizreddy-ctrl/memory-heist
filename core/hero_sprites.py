"""
core/hero_sprites.py
Owner: Member 1 - Core Game System

In-world sprites for Ghost and Echo: 16x16 pixel art drawn from text grids,
scaled 2x nearest-neighbour to the 32x32 player size. They match the portraits
(Ghost: hooded, cyan visor. Echo: orange hair, gold goggles) so the hero reads
as the same person on the HUD, in cutscenes and in the levels.

Same shape as entities.sprites.make_player_frames, plus a blink frame:
    {"idle": surface, "walk": [4 surfaces], "blink": surface}
facing right (Player flips for left).
"""

import pygame

SCALE = 2
GRID = 16

# Legend: . clear, H/h hood, D hood void, V visor, C coat, c coat trim,
#         G glove, B boots, O hair, K skin, Y goggles, J jacket, T trim.
_GHOST_HEAD = [
    "................",
    "....HHHHHH......",
    "...HHhhhhHH.....",
    "..HHhhhhhhHH....",
    "..HHhhhhDDDH....",
    "..HHhhhDVVVH....",
    "..HHHhhDDDDH....",
    "...HHHHHHHH.....",
]
_ECHO_HEAD = [
    "................",
    "....OOOOOO......",
    "...OOOOOOOO.....",
    "..OOOOOOOOOO....",
    "..OOOOKKKKO.....",
    "..OOOKYYYKK.....",
    "..OOOKKKKKK.....",
    "...OOOKKKK......",
]
_GHOST_BODY = [
    "..cCCCCCCCCCC...",
    ".CCCccCCCCCCCC..",
    ".CCCccCCCCCGGC..",
    "..CCCCccccCGG...",
    "..CCCCCCCCCCC...",
]
_ECHO_BODY = [
    "..OJJJJJJJJJ....",
    ".OOJTJJJJJJJJ...",
    ".OJJJTJJJJGGJ...",
    "..JJJJTJJJGG....",
    "...JJJJJJJJJ....",
]
_LEGS = {
    "idle":   ["....CCC.CCC.....", "....BBB.BBB....."],
    "step_a": ["...CCC....CCC...", "...BBB....BBB..."],
    "step_b": ["......CCCC......", "......BBBB......"],
}
_ECHO_LEGS = {k: [row.replace("C", "J") for row in v] for k, v in _LEGS.items()}

PALETTES = {
    "ghost": {
        "H": (74, 84, 124), "h": (104, 116, 164), "D": (8, 12, 24),
        "V": (90, 240, 255), "C": (58, 70, 112), "c": (96, 156, 196),
        "G": (178, 186, 206), "B": (18, 22, 38),
    },
    "echo": {
        "O": (178, 100, 48), "K": (226, 188, 152), "Y": (250, 190, 70),
        "J": (190, 122, 70), "T": (52, 168, 156), "G": (226, 188, 152),
        "B": (50, 34, 28),
    },
}
_PARTS = {
    "ghost": (_GHOST_HEAD, _GHOST_BODY, _LEGS),
    "echo": (_ECHO_HEAD, _ECHO_BODY, _ECHO_LEGS),
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
_COURIER_CAP = ["....PPPPPP......", "...PPPPPPPPpp..."]
_COURIER_VEST = [
    "...CRRCCCRRC....",
    "..CCRRRRRRRRC...",
    "..CCrrrrrrGGC...",
    "..CCRRRRRRGG....",
    "...CRRRRRRRC....",
]


def _courier_parts(name):
    head, body, legs = _PARTS[name]
    vest = [row.replace("C", "J") for row in _COURIER_VEST] if name == "echo" else list(_COURIER_VEST)
    return head[:1] + _COURIER_CAP + head[3:], vest, legs

# What the eyes become mid-blink: the visor / goggles dim to a thin dark band.
BLINK_COLOURS = {
    "ghost": {"V": (24, 70, 86)},
    "echo": {"Y": (120, 84, 40)},
}


OUTLINE = (6, 10, 20, 255)


# Pixels that keep their exact colour when the shading pass runs: eyes, visor,
# goggles, the dark hood void, and the guard's badge.
UNSHADED = frozenset("VYDegb")
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
    surf = pygame.Surface((GRID, GRID), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                surf.set_at((x, y), _shaded(rows, x, y, ch, palette) + (255,))
    # 1px dark outline so the hero reads on light and dark floors alike.
    edge = []
    for y in range(GRID):
        for x in range(GRID):
            if surf.get_at((x, y))[3] == 0:
                near = any(
                    0 <= x + dx < GRID and 0 <= y + dy < GRID
                    and surf.get_at((x + dx, y + dy))[3] > 0
                    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)))
                if near:
                    edge.append((x, y))
    for pos in edge:
        surf.set_at(pos, OUTLINE)
    return pygame.transform.scale(surf, (GRID * SCALE, GRID * SCALE))


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
