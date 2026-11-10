"""
tests/test_depth_fx.py

The stateless depth effects (light bars, steam, sparks, dust) and the rim light on characters:
they draw from the clock alone, stay inside their region, never leave the clip changed, and
the rim light lifts a character's edge off a dark floor.
"""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame

from core.character import RIM_LIGHT, draw_character
from levels import depth_fx


def blank(size=(200, 160)):
    surface = pygame.Surface(size)
    surface.fill((10, 12, 20))
    return surface


def changed(surface):
    return any(surface.get_at((x, y))[:3] != (10, 12, 20) for x in range(surface.get_width()) for y in range(surface.get_height()))


def test_light_bars_brighten_the_region_and_only_the_region():
    surface = blank()
    region = pygame.Rect(40, 30, 100, 80)
    depth_fx.light_bars(surface, region, 1.0, alpha=60)
    inside = [surface.get_at((x, y))[0] for x in range(region.left, region.right) for y in range(region.top, region.bottom)]
    assert max(inside) > 10
    assert surface.get_at((5, 5))[:3] == (10, 12, 20) and surface.get_at((190, 150))[:3] == (10, 12, 20)


def test_light_bars_drift_over_time():
    a, b = blank(), blank()
    depth_fx.light_bars(a, (0, 0, 200, 160), 0.0, alpha=60)
    depth_fx.light_bars(b, (0, 0, 200, 160), 3.0, alpha=60)
    assert pygame.image.tostring(a, "RGB") != pygame.image.tostring(b, "RGB")


def test_steam_hisses_for_a_burst_then_is_quiet():
    hissing, quiet = blank(), blank()
    depth_fx.steam(hissing, (100, 140), 1.0, period=7.0)
    depth_fx.steam(quiet, (100, 140), 5.5, period=7.0)
    assert changed(hissing)
    assert not changed(quiet)


def test_sparks_fly_only_just_after_the_period_starts():
    soon, later = blank(), blank()
    depth_fx.sparks(soon, (100, 40), 0.2, period=9.0)
    depth_fx.sparks(later, (100, 40), 4.0, period=9.0)
    assert changed(soon)
    assert not changed(later)


def test_motes_stay_inside_their_region_and_are_repeatable():
    region = pygame.Rect(30, 30, 120, 90)
    a, b = blank(), blank()
    depth_fx.motes(a, region, 2.0, count=40)
    depth_fx.motes(b, region, 2.0, count=40)
    assert pygame.image.tostring(a, "RGB") == pygame.image.tostring(b, "RGB")
    for x in range(200):
        for y in range(160):
            if not region.collidepoint(x, y):
                assert a.get_at((x, y))[:3] == (10, 12, 20)


def test_effects_leave_the_clip_rect_alone():
    surface = blank()
    clip = pygame.Rect(10, 10, 150, 100)
    surface.set_clip(clip)
    depth_fx.light_bars(surface, (0, 0, 200, 160), 1.0)
    depth_fx.steam(surface, (100, 140), 1.0)
    depth_fx.sparks(surface, (100, 40), 0.2)
    depth_fx.motes(surface, (0, 0, 200, 160), 1.0)
    assert surface.get_clip() == clip


def test_rim_light_lights_the_edge_above_and_left_of_a_character():
    surface = blank()
    image = pygame.Surface((10, 16), pygame.SRCALPHA)
    image.fill((200, 60, 60, 255))
    rect = pygame.Rect(50, 60, 10, 16)
    draw_character(surface, rect, image, 0, False)
    above = surface.get_at((55, 59))[:3]                       # the row just above the head
    left = surface.get_at((49, 68))[:3]                        # the column just left of the body
    assert above != (10, 12, 20) and left != (10, 12, 20)
    assert above[2] > above[0]                                 # cool, not red like the sprite
    assert RIM_LIGHT[3] < 255
