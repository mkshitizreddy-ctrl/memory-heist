"""
ui/theme.py
Owner: Member 1 - Core Game System

Single source of truth for colour, spacing and type across the whole game.
The tower (levels) is warm pixel-art; menus and HUD are flat and geometric.
Both draw from this palette so the six floors read as one building.

Levels and screens should import from here instead of hard-coding RGB.
"""

# --- Core palette (NovaCorp) ---------------------------------------------
INK = (16, 20, 34)            # deepest background
NAVY = (26, 34, 58)           # panels
SLATE = (52, 64, 96)          # borders, inactive
MIST = (170, 184, 210)        # secondary text
PAPER = (238, 241, 248)       # primary text
GOLD = (255, 196, 64)         # reward, highlights, Ghost accent
TEAL = (64, 214, 190)         # success, Echo accent
CORAL = (255, 107, 94)        # danger, WARDEN accent
SKY = (96, 168, 255)          # info, selection

# --- Spacing / shape ------------------------------------------------------
GRID = 8
PAD = 16
RADIUS = 10
BORDER = 2

# --- Floor palettes: (floor, accent, light) -------------------------------
# One entry per level key in core.level_manager.LEVEL_ORDER.
FLOORS = {
    "level1": {"name": "Reception lobby",   "floor": (44, 66, 110),  "accent": (80, 150, 255)},
    "level2": {"name": "Maintenance grid",  "floor": (74, 54, 48),   "accent": (255, 140, 80)},
    "level3": {"name": "Laser corridor",    "floor": (30, 70, 64),   "accent": (50, 210, 150)},
    "level4": {"name": "Archive vault",     "floor": (28, 38, 78),   "accent": (120, 130, 255)},
    "level5": {"name": "Server hall",       "floor": (70, 36, 66),   "accent": (240, 90, 160)},
    "final_vault": {"name": "Master vault", "floor": (72, 30, 36),   "accent": (255, 96, 84)},
}

_DEFAULT_FLOOR = {"name": "NovaCorp", "floor": NAVY, "accent": SKY}


def floor_palette(level_name):
    """Palette for a level key; unknown keys get a neutral NovaCorp one."""
    return FLOORS.get(level_name, _DEFAULT_FLOOR)


def mix(a, b, t):
    """Blend colour a toward b by t (0..1), returning an int RGB tuple."""
    t = max(0.0, min(1.0, t))
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(3))
