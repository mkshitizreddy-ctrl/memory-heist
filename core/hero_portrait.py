"""
core/hero_portrait.py
Owner: Member 1 - Core Game System

Large, animated portraits of the two thieves for story cards. They reuse the
in-game pixel sprites, scaled up without smoothing, and add a pulsing visor
glow and chip-slot light so the card feels alive. No image files needed.
"""

import math

import pygame

from entities.sprites import make_player_frames

# Character -> in-game sprite palette.
CHARACTERS = {
    "ghost": "cyan",
    "echo": "orange",
}

# Glow colour per character (matches the visor colour of each palette).
GLOW = {
    "ghost": (0, 230, 255),
    "echo": (255, 190, 60),
}

_SOURCE = 32  # the in-game sprite is 32x32 pixels


def make_portrait(name, size, tick=0):
    """Return a size x size SRCALPHA portrait of `name`; tick drives the glow."""
    if name not in CHARACTERS:
        raise ValueError(f"Unknown character: {name!r}")

    sprite = make_player_frames(CHARACTERS[name])["idle"]
    portrait = pygame.transform.scale(sprite, (size, size))  # nearest neighbour
    unit = size / _SOURCE
    color = GLOW[name]
    pulse = 0.5 + 0.5 * math.sin(tick * 0.2)

    # Soft halo behind the visor, drawn under the sprite so edges stay crisp.
    halo = pygame.Surface((size, size), pygame.SRCALPHA)
    center = (int(size * 0.5), int(size * 0.28))
    pygame.draw.circle(halo, (*color, int(25 + 45 * pulse)), center, int(size * 0.22))
    pygame.draw.circle(halo, (*color, int(15 + 30 * pulse)), center, int(size * 0.3))

    # Brighter visor and a small chip-slot light on the jacket.
    glow = pygame.Surface((size, size), pygame.SRCALPHA)
    visor = pygame.Rect(int(12 * unit), int(8 * unit), int(8 * unit), max(1, int(2 * unit)))
    pygame.draw.rect(glow, (*color, int(90 + 140 * pulse)), visor)
    chip = pygame.Rect(int(15 * unit), int(16 * unit), max(1, int(2 * unit)), max(1, int(2 * unit)))
    pygame.draw.rect(glow, (*color, int(60 + 150 * (1 - pulse))), chip)

    result = pygame.Surface((size, size), pygame.SRCALPHA)
    result.blit(halo, (0, 0))
    result.blit(portrait, (0, 0))
    result.blit(glow, (0, 0))
    return result
