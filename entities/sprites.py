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
