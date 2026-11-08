"""The shared NovaCorp look: grade, grime, markings, furniture, posters and the PA."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import numpy as np
import pygame
import pytest

from levels import novacorp_style as S
from ui.fonts import ui_font


@pytest.fixture(autouse=True)
def display_init():
    pygame.init()
    pygame.display.set_mode((960, 640))


def flat(colour, size=(200, 100)):
    surf = pygame.Surface(size)
    surf.fill(colour)
    return surf


def spread(surf):
    arr = pygame.surfarray.array3d(surf).astype(int)
    return float((arr.max(axis=2) - arr.min(axis=2)).mean())


# --- the grade -----------------------------------------------------------
def test_grade_washes_out_colour_and_keeps_the_size():
    surf = flat((40, 160, 255))
    before = spread(surf)
    S.grade(surf)
    assert surf.get_size() == (200, 100)
    assert spread(surf) < before * 0.8
    plain = flat((40, 160, 255))
    S.grade(plain, tint=(1, 1, 1), vignette=0, grain=0)       # the desaturation alone
    assert before * 0.6 < spread(plain) < before * 0.7


def test_grade_darkens_the_corners_more_than_the_middle():
    surf = flat((120, 120, 120), (200, 120))
    S.grade(surf, grain=0)
    corner = sum(surf.get_at((0, 0))[:3])
    middle = sum(surf.get_at((100, 60))[:3])
    assert corner < middle * 0.8


def test_grade_adds_grain_only_when_asked_and_is_repeatable():
    a, b, c = flat((120, 120, 120)), flat((120, 120, 120)), flat((120, 120, 120))
    S.grade(a, seed=3, vignette=0, desaturate=0, tint=(1, 1, 1))
    S.grade(b, seed=3, vignette=0, desaturate=0, tint=(1, 1, 1))
    S.grade(c, seed=3, vignette=0, desaturate=0, tint=(1, 1, 1), grain=0)
    assert pygame.image.tostring(a, "RGB") == pygame.image.tostring(b, "RGB")
    assert pygame.surfarray.array3d(a).std() > 1.0
    assert pygame.surfarray.array3d(c).std() == 0


def test_grade_tints_toward_yellow():
    surf = flat((120, 120, 120))
    S.grade(surf, grain=0, vignette=0)
    r, g, b = surf.get_at((50, 50))[:3]
    assert r > g > b


# --- grime and markings --------------------------------------------------
def test_stains_stay_inside_their_area_and_darken_it():
    surf = flat((120, 120, 120), (400, 300))
    area = pygame.Rect(100, 80, 200, 120)
    S.stains(surf, area, seed=2)
    arr = pygame.surfarray.array3d(surf)
    outside = arr.copy()
    outside[100:300, 80:200] = 120
    assert (outside == 120).all()
    assert arr[100:300, 80:200].mean() < 120


def test_stains_are_repeatable_and_vary_with_the_seed():
    def run(seed):
        s = flat((120, 120, 120), (300, 200))
        S.stains(s, (0, 0, 300, 200), seed=seed)
        return pygame.image.tostring(s, "RGB")
    assert run(1) == run(1) and run(1) != run(2)


def test_stencil_paints_faded_text_and_returns_where():
    surf = flat((0, 0, 0), (300, 100))
    rect = S.stencil(surf, "WAIT", (150, 50), ui_font(24), alpha=100)
    assert rect.collidepoint(150, 50)
    assert any(surf.get_at((x, y))[:3] != (0, 0, 0) for x in range(rect.x, rect.right) for y in range(rect.y, rect.bottom))
    assert max(surf.get_at((x, y))[0] for x in range(rect.x, rect.right) for y in range(rect.y, rect.bottom)) < 214


def test_dashed_line_has_gaps():
    surf = flat((0, 0, 0), (300, 40))
    S.dashed_line(surf, (10, 20), (290, 20), dash=14, gap=10)
    row = [surf.get_at((x, 20))[:3] != (0, 0, 0) for x in range(10, 290)]
    assert any(row) and not all(row)
    assert surf.get_at((150, 5))[:3] == (0, 0, 0)
    S.dashed_line(surf, (5, 5), (5, 5))                      # zero length is fine


# --- furniture and wall art ----------------------------------------------
@pytest.mark.parametrize("draw, size", [
    (lambda s, r: S.draw_cabinet(s, r), (32, 32)),
    (lambda s, r: S.draw_cooler(s, r), (32, 64)),
    (lambda s, r: S.draw_poster(s, r, ("SMILE", "PLEASE"), ui_font(14)), (48, 64)),
])
def test_furniture_draws_inside_its_rect_plus_shadow(draw, size):
    surf = flat((0, 0, 0), (200, 200))
    rect = pygame.Rect(60, 60, *size)
    draw(surf, rect)
    arr = pygame.surfarray.array3d(surf)
    inside = arr[58:60 + size[0] + 4, 58:60 + size[1] + 4]
    assert inside.sum() > 0
    mask = np.ones(arr.shape[:2], bool)
    mask[56:64 + size[0] + 4, 56:64 + size[1] + 4] = False
    assert arr[mask].sum() == 0


def test_speaker_light_blinks_only_while_speaking():
    def light(t, active):
        s = flat((0, 0, 0), (100, 60))
        S.draw_speaker(s, (40, 30), t, active)
        return s.get_at((58, 30))[:3]
    assert light(0.0, True) != light(1 / 6 + 0.01, True)
    assert light(0.0, False) == light(1 / 6 + 0.01, False)


# --- the PA ----------------------------------------------------------------
def test_pa_stays_quiet_until_its_first_announcement():
    pa = S.PA(("one", "two"))
    assert S.PA.FIRST_AT >= 5 and S.PA.EVERY > S.PA.SHOW
    for _ in range(int(S.PA.FIRST_AT * 60) - 2):
        assert pa.update(1 / 60) is None
    assert not pa.active and pa.alpha() == 0 and pa.caption == ""
    heard = None
    for _ in range(4):
        heard = heard or pa.update(1 / 60)
    assert heard == "one" and pa.active and pa.caption == "one"


def test_pa_cycles_its_lines_and_repeats_on_schedule():
    pa = S.PA(("one", "two"))
    heard = []
    for _ in range(int((S.PA.FIRST_AT + 2.5 * S.PA.EVERY) * 60)):
        line = pa.update(1 / 60)
        if line:
            heard.append(line)
    assert heard == ["one", "two", "one"]


def test_the_caption_fades_in_holds_and_goes_away():
    pa = S.PA(("one",))
    pa.update(S.PA.FIRST_AT)
    assert pa.alpha() == 0                                   # just starting
    pa.update(0.2)
    assert 0 < pa.alpha() < 255
    pa.update(1.0)
    assert pa.alpha() == 255
    pa.update(S.PA.SHOW - 1.2 - 0.2)
    assert 0 < pa.alpha() < 255
    pa.update(1.0)
    assert not pa.active and pa.alpha() == 0 and pa.caption == ""


# --- walls ---------------------------------------------------------------
def room(rows=None):
    from core.tilemap import TILE, TileMap, make_tiles
    rows = rows or ["#" * 12, "#" * 12, "#" * 12] + ["##" + "." * 8 + "##"] * 8 + ["#" * 12] * 2
    tm = TileMap(rows)
    surf = pygame.Surface(tm.pixel_size)
    tiles = make_tiles("level1")
    for y in range(tm.rows):
        for x in range(tm.cols):
            surf.blit(tiles[tm.grid[y][x]], (x * TILE, y * TILE))
    return tm, surf, tiles


def lum(surf, x, y):
    r, g, b = surf.get_at((x, y))[:3]
    return 0.3 * r + 0.59 * g + 0.11 * b


def test_walls_become_lighter_than_the_floor_and_the_floor_stays_a_floor():
    from ui import theme
    tm, surf, _ = room()
    S.draw_walls(surf, tm, theme.floor_palette("level1")["floor"])
    wall = lum(surf, 5 * 32 + 16, 16)                      # inside the north wall
    centre = lum(surf, 6 * 32, 7 * 32)                     # the middle of the room
    assert wall > centre * 1.4


def test_a_wall_casts_a_shadow_that_fades_with_distance():
    from ui import theme
    tm, before, _ = room()
    after = before.copy()
    S.draw_walls(after, tm, theme.floor_palette("level1")["floor"])
    x = 6 * 32 + 5
    y0 = 3 * 32                                            # first floor row, right under the north wall
    near, mid, far = (lum(before, x, y0 + d) - lum(after, x, y0 + d) for d in (1, 14, 28))
    assert near > mid > far >= 0 and near > 30 and far < 8
    assert lum(after, 6 * 32, 7 * 32) == lum(before, 6 * 32, 7 * 32)        # nothing far from a wall


def test_side_walls_cast_a_shorter_softer_shadow_and_the_south_wall_a_contact_shadow():
    from ui import theme
    tm, before, _ = room()
    after = before.copy()
    S.draw_walls(after, tm, theme.floor_palette("level1")["floor"])
    y = 7 * 32 + 16
    left = lum(before, 2 * 32 + 1, y) - lum(after, 2 * 32 + 1, y)
    right = lum(before, 10 * 32 - 2, y) - lum(after, 10 * 32 - 2, y)
    away = lum(before, 2 * 32 + 20, y) - lum(after, 2 * 32 + 20, y)
    assert left > 8 and right > 8 and away < left
    south = lum(before, 6 * 32, 11 * 32 - 2) - lum(after, 6 * 32, 11 * 32 - 2)
    assert south > 8


def test_a_wall_with_open_floor_above_shows_a_lit_cap_and_a_baseboard_below():
    from ui import theme
    tm, surf, _ = room()
    S.draw_walls(surf, tm, theme.floor_palette("level1")["floor"])
    cap = lum(surf, 5 * 32 + 16, 11 * 32 + 2)              # the top of the south wall
    face = lum(surf, 5 * 32 + 16, 11 * 32 + 20)
    assert cap > face * 1.2
    rail = lum(surf, 5 * 32 + 16, 2 * 32)                  # chair rail at the foot of the north wall
    below_rail = lum(surf, 5 * 32 + 16, 2 * 32 + 12)       # the lower panel
    base = lum(surf, 5 * 32 + 16, 3 * 32 - 4)              # the baseboard
    assert rail > below_rail * 1.15 and base < below_rail * 0.8


def test_tall_walls_get_panel_seams_every_third_column_only():
    from ui import theme
    tm, surf, _ = room()
    S.draw_walls(surf, tm, theme.floor_palette("level1")["floor"])
    y = 48                                                 # up in the wall mass, below its cap
    seam = lum(surf, 3 * 32, y)
    plain = lum(surf, 4 * 32 + 8, y)
    assert seam < plain * 0.8
    assert lum(surf, 4 * 32, y) == lum(surf, 4 * 32 + 8, y) == lum(surf, 5 * 32, y)    # no seam on columns 4 and 5


def test_void_tiles_are_not_shadowed_and_drawing_twice_is_stable():
    from core.tilemap import TileMap
    from ui import theme
    tm = TileMap(["####", "#..#", "#  #", "####"])
    a = pygame.Surface(tm.pixel_size)
    a.fill((50, 60, 90))
    b = a.copy()
    base = theme.floor_palette("level1")["floor"]
    S.draw_walls(a, tm, base)
    S.draw_walls(b, tm, base)
    assert pygame.image.tostring(a, "RGB") == pygame.image.tostring(b, "RGB")
    assert a.get_at((40, 2 * 32 + 6))[:3] == (50, 60, 90)  # void tile right of a floor-less row stays as it was


def test_side_walls_have_a_bevelled_edge_facing_the_room():
    from ui import theme
    tm, surf, _ = room()
    S.draw_walls(surf, tm, theme.floor_palette("level1")["floor"])
    y = 7 * 32 + 16
    assert lum(surf, 10 * 32 + 1, y) > lum(surf, 10 * 32 + 20, y) * 1.2        # right wall: a lit edge
    assert lum(surf, 2 * 32 - 2, y) < lum(surf, 32 + 8, y) * 0.8              # left wall: a shaded edge


def test_a_wall_one_tile_thick_has_a_cap_and_a_baseboard():
    from ui import theme
    tm, surf, _ = room(["....", "####", "...."])
    S.draw_walls(surf, tm, theme.floor_palette("level1")["floor"])
    top, middle, bottom = lum(surf, 40, 32 + 2), lum(surf, 40, 32 + 14), lum(surf, 40, 64 - 3)
    assert top > middle * 1.2 and bottom < middle * 0.8
