import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.level_manager import LEVEL_ORDER
from core.tilemap import TILE, Camera, TileMap, make_tiles

ROOM = [
    "#######",
    "#.....#",
    "#..#..#",
    "#.....#",
    "#######",
]


@pytest.fixture(autouse=True)
def display():
    pygame.init()
    pygame.display.set_mode((320, 240))


def test_parse_and_size():
    m = TileMap(ROOM)
    assert (m.cols, m.rows) == (7, 5)
    assert m.pixel_size == (7 * TILE, 5 * TILE)
    assert m.name_at(0, 0) == "wall" and m.name_at(1, 1) == "floor"


def test_ragged_rows_padded_with_void():
    m = TileMap(["###", "#"])
    assert m.name_at(2, 1) == "void" and m.is_solid(2, 1)


def test_unknown_char_and_empty_map_rejected():
    with pytest.raises(ValueError, match="unknown tile"):
        TileMap(["#?#"])
    with pytest.raises(ValueError):
        TileMap([])


def test_outside_map_is_solid():
    m = TileMap(ROOM)
    assert m.is_solid(-1, 0) and m.is_solid(0, 99)


def test_coordinate_conversions():
    m = TileMap(ROOM)
    assert m.to_tile(0, 0) == (0, 0)
    assert m.to_tile(TILE - 1, TILE) == (0, 1)
    assert m.to_tile(-1, -1) == (-1, -1)             # floor division, not truncation
    assert m.tile_rect(2, 3) == pygame.Rect(2 * TILE, 3 * TILE, TILE, TILE)


def test_collides_with_wall_and_free_floor():
    m = TileMap(ROOM)
    assert not m.collides(pygame.Rect(TILE + 2, TILE + 2, 20, 20))
    assert m.collides(pygame.Rect(2, 2, 20, 20))
    assert m.collides(pygame.Rect(3 * TILE + 4, 2 * TILE + 4, 10, 10))


def test_rect_touching_but_not_overlapping_a_wall_is_free():
    m = TileMap(ROOM)
    assert not m.collides(pygame.Rect(TILE, TILE, 10, 10))


def test_move_stops_flush_against_wall():
    m = TileMap(ROOM)
    r = pygame.Rect(TILE + 2, TILE + 2, 20, 20)
    out = m.move(r, -50, 0)
    assert out.left == TILE and out.y == r.y
    out = m.move(r, 0, 500)
    assert out.bottom == 4 * TILE


def test_move_slides_along_a_wall():
    m = TileMap(ROOM)
    r = pygame.Rect(TILE + 2, TILE + 2, 20, 20)
    out = m.move(r, -10, 10)                          # push into the left wall diagonally
    assert out.topleft == (TILE, r.y + 10)
    assert not m.collides(out)


def test_move_free_space_moves_exactly():
    m = TileMap(ROOM)
    r = pygame.Rect(2 * TILE, TILE + 2, 10, 10)
    assert m.move(r, 3, 4).topleft == (r.x + 3, r.y + 4)


def test_visible_tiles_cull_to_view_and_map():
    m = TileMap(ROOM)
    tiles = m.visible_tiles(pygame.Rect(0, 0, TILE * 2, TILE * 2))
    assert sorted(tiles) == [(0, 0), (0, 1), (1, 0), (1, 1)]
    far = m.visible_tiles(pygame.Rect(-500, -500, 5000, 5000))
    assert len(far) == 35


def test_camera_clamps_to_world():
    c = Camera(100, 100, 500, 400)
    c.snap(-999, -999)
    assert (c.x, c.y) == (0, 0)
    c.snap(9999, 9999)
    assert (c.x, c.y) == (400, 300)
    c.snap(250, 200)
    assert (c.x, c.y) == (200, 150)


def test_camera_centres_a_world_smaller_than_the_view():
    c = Camera(100, 100, 60, 40)
    c.snap(30, 20)
    assert (c.x, c.y) == (-20, -30)


def test_camera_follow_is_smooth_and_converges():
    c = Camera(100, 100, 1000, 1000)
    c.snap(50, 50)
    c.follow(800, 800, 1 / 60)
    assert 0 < c.x < 750
    for _ in range(600):
        c.follow(800, 800, 1 / 60)
    assert c.x == pytest.approx(750, abs=0.5)
    before = c.x
    c.follow(0, 0, 0.0)
    assert c.x == before


def test_camera_conversions_roundtrip_and_shake_shifts_view():
    c = Camera(100, 100, 1000, 1000)
    c.snap(500, 500)
    sx, sy = c.world_to_screen(520, 530)
    assert c.screen_to_world(sx, sy) == (520, 530)
    base = c.offset()
    c.shake = (3, -2)
    assert c.offset() == (base[0] - 3, base[1] + 2)


def test_camera_visibility():
    c = Camera(100, 100, 1000, 1000)
    c.snap(500, 500)
    assert c.is_visible(pygame.Rect(c.x + 10, c.y + 10, 5, 5))
    assert not c.is_visible(pygame.Rect(0, 0, 5, 5))
    assert c.is_visible(pygame.Rect(c.x - 8, c.y + 10, 5, 5), margin=10)


def test_render_draws_tiles_at_camera_offset():
    m = TileMap(ROOM)                                  # 224 x 160 px
    tiles = make_tiles("level1")
    cam = Camera(160, 120, *m.pixel_size)              # view smaller than the map
    cam.snap(0, 0)
    s = pygame.Surface((160, 120))
    s.fill((1, 2, 3))
    m.render(s, cam, tiles)
    assert s.get_at((8, TILE - 4))[:3] == tiles["wall"].get_at((8, TILE - 4))[:3]
    floor_px = tiles["floor"].get_at((8, 8))[:3]
    assert s.get_at((TILE + 8, TILE + 8))[:3] == floor_px
    cam.x = TILE                                       # scroll one tile right
    s2 = pygame.Surface((160, 120))
    s2.fill((1, 2, 3))
    m.render(s2, cam, tiles)
    assert s2.get_at((8, TILE + 8))[:3] == floor_px    # left edge is now floor (col 1)
    assert s2.get_at((8, 8))[:3] == tiles["wall"].get_at((8, 8))[:3]   # top row still wall
    assert s.get_at((8, TILE + 8))[:3] != floor_px     # unscrolled left edge was wall column


def test_render_small_map_is_centred_not_top_left():
    m = TileMap(ROOM)
    cam = Camera(320, 240, *m.pixel_size)
    cam.snap(0, 0)
    s = pygame.Surface((320, 240))
    s.fill((1, 2, 3))
    m.render(s, cam, make_tiles("level1"))
    assert s.get_at((2, 2))[:3] == (1, 2, 3)           # outside the centred map
    assert s.get_at((48 + 8, 40 + 8))[:3] != (1, 2, 3)


@pytest.mark.parametrize("level", LEVEL_ORDER)
def test_tiles_per_floor_cover_the_legend_and_differ_between_floors(level):
    t = make_tiles(level)
    assert set(t) == {"floor", "floor_alt", "wall", "void"}
    assert all(img.get_size() == (TILE, TILE) for img in t.values())


def test_floors_have_different_wall_and_floor_colours():
    seen = {tuple(make_tiles(n)["floor"].get_at((8, 8))[:3]) for n in LEVEL_ORDER}
    assert len(seen) == len(LEVEL_ORDER)
