"""
core/hero_sprites.py
Owner: Member 1 - Core Game System

In-world sprites for Ghost and Echo: 16x16 pixel art drawn from text grids,
scaled 2x nearest-neighbour to the 32x32 player size. They match the portraits
(Ghost: hooded, cyan visor. Echo: orange hair, gold goggles) so the hero reads
as the same person on the HUD, in cutscenes and in the levels.

Same shape as entities.sprites.make_player_frames:
    {"idle": surface, "walk": [4 surfaces]}   facing right (Player flips for left).
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
    "...CCCCCCCCC....",
    "..CCCccCCCCCC...",
    "..CCCccCCCGGC...",
    "..CCCCCCCCGG....",
    "...CCCCCCCCC....",
]
_ECHO_BODY = [
    "...JJJJJJJJJ....",
    "..JJJTTJJJJJJ...",
    "..JJJTTJJJGGJ...",
    "..JJJJJJJJGG....",
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
        "H": (96, 108, 166), "h": (136, 152, 214), "D": (8, 12, 24),
        "V": (90, 240, 255), "C": (76, 92, 150), "c": (130, 200, 255),
        "G": (200, 212, 240), "B": (22, 28, 48),
    },
    "echo": {
        "O": (214, 120, 48), "K": (240, 200, 160), "Y": (255, 196, 64),
        "J": (232, 150, 70), "T": (64, 214, 190), "G": (240, 200, 160),
        "B": (60, 40, 30),
    },
}
_PARTS = {
    "ghost": (_GHOST_HEAD, _GHOST_BODY, _LEGS),
    "echo": (_ECHO_HEAD, _ECHO_BODY, _ECHO_LEGS),
}

HEROES = tuple(PALETTES)


OUTLINE = (6, 10, 20, 255)


def _build(rows, palette):
    surf = pygame.Surface((GRID, GRID), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            if ch != ".":
                surf.set_at((x, y), palette[ch] + (255,))
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


def make_hero_frames(name):
    """{"idle": surf, "walk": [surf x4]} for 'ghost' or 'echo'."""
    if name not in _PARTS:
        raise ValueError(f"unknown hero {name!r}; expected one of {HEROES}")
    head, body, legs = _PARTS[name]
    palette = PALETTES[name]

    def frame(key):
        return _build(head + body + legs[key], palette)

    return {
        "idle": frame("idle"),
        "walk": [frame("step_a"), frame("idle"), frame("step_b"), frame("idle")],
    }
