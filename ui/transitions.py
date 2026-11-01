"""Elevator-door wipe shown when the run moves to a new floor.

`progress` runs 1.0 (doors shut) down to 0.0 (doors fully open), the same
direction as the game's fade timer.  The doors take the floor's accent colour
and the floor's name is printed across them while they are mostly closed.
"""

import pygame

from core.easing import clamp01, ease_in_out_quad
from ui import theme
from ui.hud import LEVEL_LABELS

SEAM = 4


def door_edges(width, progress):
    """(left door right-edge x, right door left-edge x) for a progress value."""
    p = ease_in_out_quad(clamp01(progress))
    half = width // 2
    reach = int(round(half * p))
    return reach, width - reach


def label_alpha(progress):
    """Floor name is fully visible while shut and gone before doors are wide."""
    return int(255 * clamp01((progress - 0.25) / 0.5))


class ElevatorWipe:
    def __init__(self):
        self.title_font = pygame.font.Font(None, 54)
        self.name_font = pygame.font.Font(None, 28)

    def draw(self, surface, progress, level_name):
        if progress <= 0:
            return
        width, height = surface.get_size()
        palette = theme.floor_palette(level_name)
        accent = palette["accent"]
        steel = theme.mix(theme.NAVY, accent, 0.18)
        left_edge, right_edge = door_edges(width, progress)

        for x0, x1, flip in ((0, left_edge, False), (right_edge, width, True)):
            if x1 - x0 <= 0:
                continue
            door = pygame.Rect(x0, 0, x1 - x0, height)
            pygame.draw.rect(surface, steel, door)
            # brushed highlight and a shaded inner edge
            shine_x = door.right - 30 if not flip else door.x + 20
            pygame.draw.rect(surface, theme.mix(steel, theme.PAPER, 0.06),
                             (shine_x, 0, 10, height))
            edge_x = door.right - SEAM if not flip else door.x
            pygame.draw.rect(surface, accent, (edge_x, 0, SEAM, height))

        alpha = label_alpha(progress)
        if alpha > 0:
            label = LEVEL_LABELS.get(level_name, level_name)
            title = self.title_font.render(label.upper(), True, theme.PAPER)
            name = self.name_font.render(palette["name"].upper(), True, accent)
            plate = pygame.Rect(0, 0, max(title.get_width(), name.get_width()) + 70, 104)
            plate.center = (width // 2, height // 2)
            card = pygame.Surface(plate.size, pygame.SRCALPHA)
            pygame.draw.rect(card, (*theme.INK, 235), card.get_rect(), border_radius=14)
            pygame.draw.rect(card, (*accent, 255), card.get_rect(), width=2, border_radius=14)
            card.blit(title, title.get_rect(center=(plate.w // 2, 38)))
            card.blit(name, name.get_rect(center=(plate.w // 2, 76)))
            card.set_alpha(alpha)
            surface.blit(card, plate)
