"""
core/npc_sprites.py
Owner: Member 1 - Core Game System

Pixel art for the people who work at NovaCorp: 16x16 grids scaled 2x like the
heroes (core/hero_sprites.py), facing right, drawn through the same outline
and frame layout so they animate with the same code.

    make_npc_frames("guard")  ->  {"idle", "walk": [4], "blink"?}

Adding a person: add a head, a body, a palette and an entry in _PARTS.
"""

from core.hero_sprites import _LEGS, _build

# Legend: A cap, a cap shine, P brim, K skin, S sunglasses, U uniform, b badge,
#         G hand, B boots, O hair, e eye, T headset, J blazer, L lapel.
_GUARD_HEAD = [
    "................",
    "....AAAAAA......",
    "...AAaaaaAA.....",
    "..AAAAAAAAAAP...",
    "...KKKKKKKK.....",
    "...KSSSSSKK.....",
    "...KKKKKKKK.....",
    "....KKKKKK......",
]
_GUARD_BODY = [
    "...UUUUUUUUU....",
    "..UUUbUUUUUUU...",
    "..UUUUUUUUUGG...",
    "..UUUUUUUUGG....",
    "...UUUUUUUUU....",
]
_RECEPTIONIST_HEAD = [
    "................",
    "....OOOOOO......",
    "...OOOOOOOO.....",
    "..OOOOKKKKO.....",
    "..OOOKKKeKK.....",
    "..OOOKKKKKT.....",
    "..OOOOKKKK......",
    "...OOOKKK.......",
]
_RECEPTIONIST_BODY = [
    "...JJJJJJJJJ....",
    "..JJJLLJJJJJJ...",
    "..JJJLLJJJGGJ...",
    "..JJJJJJJJGG....",
    "...JJJJJJJJJ....",
]


def _legs(letter):
    """The shared leg poses, in a different trouser colour."""
    return {key: [row.replace("C", letter) for row in rows] for key, rows in _LEGS.items()}


PALETTES = {
    "guard": {
        "A": (36, 52, 60), "a": (70, 98, 108), "P": (20, 28, 34),
        "K": (232, 184, 148), "S": (10, 12, 20), "U": (52, 74, 82),
        "b": (255, 200, 60), "G": (200, 170, 140), "B": (14, 16, 24),
    },
    "receptionist": {
        "O": (90, 52, 40), "K": (222, 170, 130), "e": (20, 20, 30),
        "T": (64, 214, 190), "J": (110, 70, 150), "L": (200, 170, 230),
        "G": (222, 170, 130), "B": (40, 30, 48),
    },
}
_PARTS = {
    "guard": (_GUARD_HEAD, _GUARD_BODY, _legs("U")),
    "receptionist": (_RECEPTIONIST_HEAD, _RECEPTIONIST_BODY, _legs("J")),
}
# What the eyes become in a blink. A guard in sunglasses has none to close.
BLINK_COLOURS = {
    "guard": {},
    "receptionist": {"e": (222, 170, 130)},
}

KINDS = tuple(PALETTES)


def make_npc_frames(kind):
    """{"idle": surf, "walk": [surf x4], "blink": surf (if the kind blinks)}."""
    if kind not in _PARTS:
        raise ValueError(f"unknown NPC {kind!r}; expected one of {KINDS}")
    head, body, legs = _PARTS[kind]
    palette = PALETTES[kind]

    def frame(key, colours=palette):
        return _build(head + body + legs[key], colours)

    frames = {
        "idle": frame("idle"),
        "walk": [frame("step_a"), frame("idle"), frame("step_b"), frame("idle")],
    }
    if BLINK_COLOURS[kind]:
        frames["blink"] = frame("idle", {**palette, **BLINK_COLOURS[kind]})
    return frames
