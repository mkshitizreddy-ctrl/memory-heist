"""
entities/sprites.py
Owner: Member 1 - Core Game System

Pixel-art character sprites drawn from small character maps, so the game
needs no image files. Each map is 16x16 and is scaled up 2x to match the
32x32 player rect.
"""

import pygame

SCALE = 2

# Legend: O outline, H hood, h hood light, V visor glow, S skin,
#         B jacket, b jacket shade, L legs, F feet, . transparent
_HEAD = [
    "................",
    "......OOOO......",
    ".....OHHHHO.....",
    "....OHhhhhHO....",
    "....OHVVVVHO....",
    "....OHSSSSHO....",
    ".....OHHHHO.....",
]

_TORSO = [
    "....OBBBBBBO....",
    "...OBBbBBbBBO...",
    "...OBBbBBbBBO...",
    "...OSBBBBBBSO...",
]

_LEGS = {
    "idle": [
        "....OLLOOLLO....",
        "....OLLOOLLO....",
        "....OFFOOFFO....",
        "................",
        "................",
    ],
    "step_a": [
        "....OLLOOLLO....",
        "...OLLO..OLLO...",
        "...OFFO..OFFO...",
        "................",
        "................",
    ],
    "step_b": [
        "....OLLOOLLO....",
        ".....OLLLLO.....",
        ".....OFFFFO.....",
        "................",
        "................",
    ],
}

# Colour sets: Player 1 is cyan, Player 2 is orange.
PALETTES = {
    "cyan": {
        "O": (10, 20, 30), "H": (30, 60, 90), "h": (50, 95, 135),
        "V": (0, 230, 255), "S": (240, 200, 170),
        "B": (0, 150, 200), "b": (0, 110, 150),
        "L": (40, 50, 80), "F": (20, 25, 45),
    },
    "orange": {
        "O": (30, 15, 5), "H": (90, 50, 25), "h": (135, 80, 40),
        "V": (255, 190, 60), "S": (240, 200, 170),
        "B": (225, 120, 30), "b": (170, 85, 20),
        "L": (80, 50, 40), "F": (45, 25, 20),
    },
}


def _build(rows, palette):
    """Turn a 16-row character map into a scaled-up surface."""
    surf = pygame.Surface((16, 16), pygame.SRCALPHA)
    for y, row in enumerate(rows):
        for x, ch in enumerate(row):
            color = palette.get(ch)
            if color is not None:
                surf.set_at((x, y), color)
    return pygame.transform.scale(surf, (16 * SCALE, 16 * SCALE))


def make_player_frames(palette_name="cyan"):
    """Return {"idle": surf, "walk": [surf, surf, surf]} facing right."""
    palette = PALETTES[palette_name]
    upper = _HEAD + _TORSO

    def frame(legs_key):
        return _build(upper + _LEGS[legs_key], palette)

    return {
        "idle": frame("idle"),
        "walk": [frame("step_a"), frame("idle"), frame("step_b"), frame("idle")],
    }


# ---------------------------------------------------------------------
# Drones (Level 4)
# Legend: O outline, B body, R rotor, E eye ring, e eye centre
# ---------------------------------------------------------------------

_DRONE_TOP = {
    0: "..RRR......RRR..",
    1: ".RRR........RRR.",
}

_DRONE_BODY = [
    ".....OOOOOO.....",
    "...OOBBBBBBOO...",
    "..OBBBBBBBBBBO..",
    "..OBBBEEEEBBBO..",
    "..OBBBEeeEBBBO..",
    "..OBBBBBBBBBBO..",
    "...OOBBBBBBOO...",
    ".....OOOOOO.....",
    "......OOOO......",
]

DRONE_PALETTES = {
    "ally": {
        "O": (10, 40, 60), "B": (35, 205, 245), "R": (190, 245, 255),
        "E": (255, 255, 255), "e": (20, 110, 160),
    },
    "enemy": {
        "O": (60, 30, 10), "B": (230, 145, 65), "R": (255, 200, 140),
        "E": (255, 230, 190), "e": (150, 60, 20),
    },
    "enemy_alert": {
        "O": (70, 10, 10), "B": (255, 85, 75), "R": (255, 170, 160),
        "E": (255, 240, 200), "e": (200, 20, 20),
    },
    "enemy_distracted": {
        "O": (15, 40, 70), "B": (100, 190, 255), "R": (200, 230, 255),
        "E": (255, 255, 255), "e": (40, 90, 170),
    },
}

_drone_cache = {}


def get_drone_frame(kind, tick):
    """Return the drone surface for a kind; tick flips the rotors."""
    phase = tick % 2
    key = (kind, phase)
    if key not in _drone_cache:
        rows = [_DRONE_TOP[phase]] + _DRONE_BODY
        surf = pygame.Surface((16, len(rows)), pygame.SRCALPHA)
        palette = DRONE_PALETTES[kind]
        for y, row in enumerate(rows):
            for x, ch in enumerate(row):
                color = palette.get(ch)
                if color is not None:
                    surf.set_at((x, y), color)
        _drone_cache[key] = pygame.transform.scale(
            surf, (16 * SCALE, len(rows) * SCALE)
        )
    return _drone_cache[key]


def draw_drone(surface, center, kind, tick=0):
    """Draw a drone sprite centred on the given point."""
    image = get_drone_frame(kind, tick)
    surface.blit(image, image.get_rect(center=center))
