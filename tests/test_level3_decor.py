"""Floor 3's laser rooms in the NovaCorp look (levels/laser_decor.py). Headless."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from levels import laser_decor as D
import test_level3_board_loops as B

pygame.init()


def baked(room):
    level, _ = B.at_room(room)
    return level, D.build_room(room, (level.room_width, level.room_height),
                               level._decor_geometry(room), level.play_top, level.play_bottom)


def test_each_room_bakes_its_own_floor():
    surfaces = [baked(room)[1] for room in (1, 2, 3)]
    for surface in surfaces:
        assert surface.get_size() == (880, 560)
    raw = [pygame.image.tobytes(s, "RGB") for s in surfaces]
    assert len(set(raw)) == 3                     # three different rooms, not one floor reused


def test_room_dressing_follows_the_live_positions():
    level, _ = baked(2)
    geo = level._decor_geometry(2)
    assert geo["waypoints"] == list(level.robot_waypoints) and len(geo["waypoints"]) >= 2
    level, _ = baked(3)
    assert level._decor_geometry(3)["core"] == level._core_center()


def test_rooms_render_in_the_floor_palette_not_violet():
    level, _ = B.at_room(1)
    r, g, b = level.LAYOUT_ACCENT
    assert g >= b and g > r                        # teal-grey, the Night Patrol accent
    for room in (1, 2, 3):
        level, _ = B.at_room(room)
        surface = pygame.Surface((960, 640))
        level.render(surface)                       # bake, walls and jambs draw without error
