"""Floor 4's recap panel holds every row and note it is given. Headless."""
import os
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
import pygame

from levels import archive_decor as A

pygame.init()


def test_four_misses_fit_inside_the_recap_panel():
    rows = [("1 INDEX    [slice]  1 miss", (255, 255, 255))] * 4
    notes = [("INDEX [slice]: [0] - Off by one.", (255, 100, 100))] * 4
    r = A.recap_rect(len(rows), len(notes))
    last_note_bottom = r.y + 32 + 4 * 18 + 6 + 18 + 4 * 16
    assert last_note_bottom <= r.bottom - 4
    assert r.bottom <= 18 * A.TILE                     # still above the bottom wall
    surface = pygame.Surface((960, 640))
    A.draw_recap(surface, rows, notes, 0.0)            # draws without error


def test_a_short_recap_keeps_the_usual_size():
    assert A.recap_rect(4, 1) == A.RECAP_PANEL
