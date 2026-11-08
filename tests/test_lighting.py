"""Tests for levels/lighting.py: the light map, bloom and blob shadows."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import numpy as np
import pygame
import pytest

from levels import lighting as L


@pytest.fixture(autouse=True)
def _pg():
    pygame.init()
    pygame.display.set_mode((64, 64))
    yield


def _px(surf, pos):
    return tuple(surf.get_at(pos))[:3]


def test_glow_is_one_at_centre_zero_at_edge_and_falls_off_monotonically():
    g = L.glow(40)
    assert g.shape == (80, 80)
    assert g[40, 40] > 0.95
    assert g[0, 0] == 0.0
    row = g[40, 40:]
    assert all(a >= b for a, b in zip(row, row[1:]))


def test_lightmap_is_ambient_far_from_lights_and_brighter_near_one():
    layer = L.LightLayer(ambient=(100, 100, 100), bloom=False)
    lm = layer.lightmap((200, 100), [L.Light((50, 50), 40)])
    assert _px(lm, (190, 90)) == (100, 100, 100)
    assert _px(lm, (50, 50))[0] > 160


def test_lightmap_never_exceeds_full_brightness():
    layer = L.LightLayer(ambient=(200, 200, 200), bloom=False)
    lights = [L.Light((50, 50), 40) for _ in range(6)]
    assert max(_px(layer.lightmap((100, 100), lights), (50, 50))) == 255


def test_apply_darkens_unlit_areas_and_keeps_lit_areas_brighter():
    world = pygame.Surface((200, 100))
    world.fill((200, 200, 200))
    L.LightLayer(ambient=(100, 100, 100), bloom=False).apply(world, [L.Light((40, 50), 40)])
    assert _px(world, (190, 50))[0] < 90                 # far corner is dim
    assert _px(world, (40, 50))[0] > _px(world, (190, 50))[0] + 60


def test_light_colour_tints_its_pool():
    world = pygame.Surface((120, 120))
    world.fill((120, 120, 120))
    L.LightLayer(ambient=(255, 255, 255), bloom=False).apply(world, [L.Light((60, 60), 50, (255, 0, 0), 1.0)])
    r, g, b = _px(world, (60, 60))
    assert r > g + 20 and r > b + 20


def test_bloom_spreads_light_from_bright_pixels_into_dark_neighbours():
    plain = pygame.Surface((160, 160))
    plain.fill((10, 10, 10))
    pygame.draw.rect(plain, (255, 255, 255), (70, 70, 20, 20))
    bloomed = plain.copy()
    L.LightLayer._bloom(bloomed)
    assert _px(bloomed, (96, 80))[0] > _px(plain, (96, 80))[0] + 5 and _px(bloomed, (100, 80))[0] > 10
    assert _px(bloomed, (5, 5))[0] <= _px(plain, (5, 5))[0] + 2    # far pixels barely change


def test_bloom_ignores_dim_scenes():
    world = pygame.Surface((160, 160))
    world.fill((60, 60, 60))
    before = world.copy()
    L.LightLayer._bloom(world)
    assert _px(world, (80, 80)) == _px(before, (80, 80))


def test_blob_shadow_darkens_under_the_rect_only():
    surf = pygame.Surface((100, 100))
    surf.fill((200, 200, 200))
    L.blob_shadow(surf, pygame.Rect(40, 40, 20, 20), alpha=120)
    assert _px(surf, (50, 60))[0] < 190
    assert _px(surf, (5, 5)) == (200, 200, 200)


def test_light_cache_is_bounded():
    layer = L.LightLayer(bloom=False)
    for r in range(10, 260):
        layer._surface(r, (255, 255, 255), 1.0)
    assert len(layer._surfaces) <= 161


def test_floor1_lights_include_beam_and_vending_and_drop_taken_chips():
    from tests.test_lobby_extras import make_level
    level, _game, _p1 = make_level()
    n = len(level._lights())
    assert n >= 10
    level.chips[0].taken = True
    assert len(level._lights()) == n - 1
    level.complete = True
    assert len(level._lights()) == n - 2                 # beam light gone once the floor is done
