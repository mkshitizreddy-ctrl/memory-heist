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


def test_cam1_label_sits_clear_of_the_room2_beam_rail():
    level, _ = B.at_room(2)
    assert 1 in level.camera_bank.label_left
    rail = level.lasers[1]                          # the vertical beam rail by cam 1
    mount_x = level.camera_bank.mount(1)[0]
    assert rail["axis"] == "y" and mount_x - 16 < rail["x"]   # the tag ends left of the mount


def test_robot_route_is_set_once_per_room():
    import inspect
    from levels.level3_loops import Level3LaserLoop
    init = inspect.getsource(Level3LaserLoop.__init__)
    assert init.count("self.robot_speed =") == 1
    assert init.count("self.robot_right_boundary =") == 1
