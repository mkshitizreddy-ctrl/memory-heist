"""
core/npc_sprites.py
Owner: Member 1 - Core Game System

Pixel art for the people who work at NovaCorp: 16x16 grids scaled 2x like the
heroes (core/hero_sprites.py), facing right, drawn through the same outline
and frame layout so they animate with the same code.

    make_npc_frames("guard")  ->  {"idle", "walk": [4], "blink"?}

Adding a person: add a head, a body, a palette and an entry in _PARTS.
"""

from core.hero_sprites import _LEGS, _build, bob_rows

# Legend: A cap, a cap shine, P brim, K skin, S sunglasses, U uniform, b badge,
#         G hand, B boots, O hair, e eye, T headset, J blazer, L lapel,
#         g goggles, V work vest, y reflective stripe, W work trousers.
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
_TECHNICIAN_HEAD = [
    "................",
    "....AAAAAA......",
    "...AAaaaaAA.....",
    "..AAAAAAAAAAP...",
    "...KKKKKKKK.....",
    "...KgggggKK.....",
    "...KKKKKKKK.....",
    "....KKKKKK......",
]
_TECHNICIAN_BODY = [
    "...VVVVVVVVV....",
    "..VVVyVVVVVVV...",
    "..VVVyVVVVVGG...",
    "..VVVyVVVVGG....",
    "...VVVVVVVVV....",
]

# The rest of NovaCorp's staff. Their faces are left blank on purpose.
_CLEANER_HEAD = [
    "................",
    "....AAAAAA......",
    "...AAAAAAAA.....",
    "..AAAAAAAAAA....",
    "...KKKKKKKK.....",
    "...KKKKKKKK.....",
    "...KKKKKKKK.....",
    "....KKKKKK......",
]
_CLEANER_BODY = [
    "...UUUUUUUUU....",
    "..UUUUUUUUUUU...",
    "..UUUbbUUUUGG...",
    "..UUUUUUUUGG....",
    "...UUUUUUUUU....",
]
_ENGINEER_HEAD = [
    "................",
    "....AAAAAA......",
    "...AAAaaAAA.....",
    "..AAAAAAAAAAP...",
    "...KKKKKKKK.....",
    "...KKKKKKKK.....",
    "...KKKKKKKK.....",
    "....KKKKKK......",
]
_ENGINEER_BODY = [
    "...VVVVVVVVV....",
    "..VVVVVVVVVVV...",
    "..VVbVVVVVVGG...",
    "..VVVVVVVVGG....",
    "...VVVVVVVVV....",
]
_SYSADMIN_HEAD = [
    "................",
    "...OOOOOOOO.....",
    "..OOOOOOOOOO....",
    "..OOKKKKKKO.....",
    "..OOKKKKKKK.....",
    "..OOKKKKKKT.....",
    "..OOOKKKKK......",
    "...OOKKKK.......",
]
_SYSADMIN_BODY = [
    "...JJJJJJJJJ....",
    "..JJJLLJJJJJJ...",
    "..JJJLLJJJGGJ...",
    "..JJJJJJJJGG....",
    "...JJJJJJJJJ....",
]
_CURATOR_HEAD = [
    "................",
    ".....AAAAA......",
    "....AAAAAAA.....",
    "..PPPPPPPPPP....",
    "...KKKKKKKK.....",
    "...KKKKKKKK.....",
    "...KKKKKKKK.....",
    "....KKKKKK......",
]
_CURATOR_BODY = [
    "...JJJJJJJJJ....",
    "..JJJJLLJJJJJ...",
    "..JJJJLLJJJGG...",
    "..JJJJLJJJGG....",
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
    "night_guard": {                      # the Floor 3 night guard: navy uniform, teal badge, tired
        "A": (30, 44, 70), "a": (62, 86, 124), "P": (18, 24, 42),
        "K": (196, 150, 120), "S": (10, 12, 20), "U": (40, 52, 80),
        "b": (64, 214, 190), "G": (150, 130, 120), "B": (12, 14, 22),
    },
    "technician": {
        "A": (255, 196, 40), "a": (255, 228, 120), "P": (204, 142, 20),
        "K": (206, 152, 112), "g": (96, 214, 240), "V": (236, 108, 40),
        "y": (250, 240, 160), "G": (58, 58, 68), "W": (58, 68, 96),
        "B": (30, 26, 24),
    },
    "cleaner": {
        "A": (96, 112, 120), "K": (200, 170, 140), "U": (112, 120, 96),
        "b": (190, 170, 90), "G": (200, 170, 140), "W": (62, 66, 58), "B": (26, 26, 24),
    },
    "engineer": {
        "A": (150, 152, 140), "a": (200, 200, 170), "P": (90, 92, 84), "K": (214, 170, 130),
        "V": (70, 96, 130), "b": (230, 200, 80), "G": (60, 60, 64), "W": (50, 60, 84),
        "B": (24, 24, 28),
    },
    "sysadmin": {
        "O": (60, 56, 52), "K": (226, 184, 150), "T": (120, 200, 180), "J": (96, 104, 92),
        "L": (200, 200, 180), "G": (226, 184, 150), "W": (44, 48, 60), "B": (22, 22, 28),
    },
    "curator": {
        "A": (30, 30, 36), "P": (18, 18, 22), "K": (230, 196, 164), "J": (46, 40, 50),
        "L": (170, 40, 40), "G": (220, 190, 160), "W": (40, 36, 44), "B": (16, 16, 20),
    },
}
_PARTS = {
    "guard": (_GUARD_HEAD, _GUARD_BODY, _legs("U")),
    "night_guard": (_GUARD_HEAD, _GUARD_BODY, _legs("U")),
    "receptionist": (_RECEPTIONIST_HEAD, _RECEPTIONIST_BODY, _legs("J")),
    "technician": (_TECHNICIAN_HEAD, _TECHNICIAN_BODY, _legs("W")),
    "cleaner": (_CLEANER_HEAD, _CLEANER_BODY, _legs("W")),
    "engineer": (_ENGINEER_HEAD, _ENGINEER_BODY, _legs("W")),
    "sysadmin": (_SYSADMIN_HEAD, _SYSADMIN_BODY, _legs("W")),
    "curator": (_CURATOR_HEAD, _CURATOR_BODY, _legs("W")),
}
# What the eyes become in a blink. A guard in sunglasses has none to close.
BLINK_COLOURS = {
    "guard": {}, "night_guard": {},
    "receptionist": {"e": (222, 170, 130)},
    "technician": {},                   # goggles never close
    "cleaner": {}, "engineer": {}, "sysadmin": {}, "curator": {},     # no faces to blink
}

KINDS = tuple(PALETTES)


def make_npc_frames(kind):
    """{"idle": surf, "walk": [surf x4], "blink": surf (if the kind blinks)}."""
    if kind not in _PARTS:
        raise ValueError(f"unknown NPC {kind!r}; expected one of {KINDS}")
    head, body, legs = _PARTS[kind]
    palette = PALETTES[kind]

    def frame(key, colours=palette):
        upper = bob_rows(head, body) if key.startswith("step") else head + body
        return _build(upper + legs[key], colours)

    frames = {
        "idle": frame("idle"),
        "walk": [frame("step_a"), frame("idle"), frame("step_b"), frame("idle")],
    }
    if BLINK_COLOURS[kind]:
        frames["blink"] = frame("idle", {**palette, **BLINK_COLOURS[kind]})
    return frames
