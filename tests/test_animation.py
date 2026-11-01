import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.animation import (Animation, Shake, SpriteSheet, SquashStretch,
                            hit_flash, scaled)


@pytest.fixture(autouse=True)
def display():
    pygame.init()
    pygame.display.set_mode((100, 100))


def strip(n=4, w=8, h=8):
    img = pygame.Surface((w * n, h), pygame.SRCALPHA)
    for i in range(n):
        img.fill((i * 50, 0, 0, 255), (i * w, 0, w, h))
    return img


def test_sheet_cuts_frames_in_order():
    s = SpriteSheet(strip(4), 8, 8)
    assert len(s) == 4
    assert [s[i].get_at((1, 1))[0] for i in range(4)] == [0, 50, 100, 150]
    assert len(s.slice(1, 2)) == 2


def test_sheet_grid_row_major():
    img = pygame.Surface((16, 16))
    img.fill((1, 0, 0), (0, 0, 8, 8)); img.fill((2, 0, 0), (8, 0, 8, 8))
    img.fill((3, 0, 0), (0, 8, 8, 8)); img.fill((4, 0, 0), (8, 8, 8, 8))
    s = SpriteSheet(img, 8, 8)
    assert [s[i].get_at((1, 1))[0] for i in range(4)] == [1, 2, 3, 4]


def test_sheet_rejects_bad_sizes():
    with pytest.raises(ValueError):
        SpriteSheet(strip(), 0, 8)
    with pytest.raises(ValueError):
        SpriteSheet(strip(1, 4, 4), 8, 8)


def test_animation_loops():
    a = Animation(list("abc"), fps=10)
    seen = []
    for _ in range(7):
        seen.append(a.frame)
        a.update(0.1)
    assert seen == list("abcabca")


def test_animation_once_holds_last_and_reports_done():
    a = Animation(list("abc"), fps=10, loop=False)
    assert not a.done
    a.update(5)
    assert a.frame == "c" and a.done
    a.reset()
    assert a.frame == "a" and not a.done


def test_animation_ignores_negative_dt_and_validates():
    a = Animation(["x", "y"], fps=10)
    a.update(-1)
    assert a.time == 0
    with pytest.raises(ValueError):
        Animation([])
    with pytest.raises(ValueError):
        Animation(["x"], fps=0)


def test_squash_stretch_settles_to_rest():
    s = SquashStretch()
    s.trigger(0.3)
    peak = 0.0
    for _ in range(240):
        s.update(1 / 60)
        peak = max(peak, abs(s.x))
    assert peak > 0.05
    assert s.at_rest
    assert s.scale == pytest.approx((1.0, 1.0), abs=1e-2)


def test_stretch_is_taller_and_narrower_squash_opposite():
    up = SquashStretch(); up.trigger(0.4)
    dn = SquashStretch(); dn.trigger(-0.4)
    for _ in range(4):
        up.update(1 / 60); dn.update(1 / 60)
    sx, sy = up.scale
    assert sy > 1 and sx < 1
    sx, sy = dn.scale
    assert sy < 1 and sx > 1


def test_squash_stable_on_huge_dt():
    s = SquashStretch(); s.trigger(0.5)
    for _ in range(50):
        s.update(10.0)
    assert abs(s.x) < 5 and s.scale[1] >= 0.2


def test_scaled_keeps_bottom_anchor():
    img = pygame.Surface((10, 20))
    out, off = scaled(img, 1.0, 1.5)
    assert out.get_size() == (10, 30)
    assert off[1] + 30 == 20          # bottom stays at base bottom
    out, off = scaled(img, 0.5, 0.5)
    assert out.get_size() == (5, 10) and off == (3, 10)


def test_hit_flash_brightens_and_keeps_alpha():
    img = pygame.Surface((4, 4), pygame.SRCALPHA)
    img.fill((10, 20, 30, 255))
    img.set_at((0, 0), (0, 0, 0, 0))
    out = hit_flash(img, 1.0)
    assert out.get_at((2, 2))[:3] == (255, 255, 255)
    assert out.get_at((0, 0))[3] == 0
    assert img.get_at((2, 2))[:3] == (10, 20, 30)       # original untouched
    half = hit_flash(img, 0.5).get_at((2, 2))[:3]
    assert half == (10 + 127, 20 + 127, 30 + 127)
    assert hit_flash(img, 0).get_at((2, 2))[:3] == (10, 20, 30)


def test_shake_decays_to_zero_and_is_bounded():
    sh = Shake(max_offset=10)
    assert sh.offset() == (0, 0)
    sh.add(1.0)
    assert max(abs(v) for v in sh.offset()) <= 10
    for _ in range(120):
        sh.update(1 / 60)
    assert sh.trauma == 0 and sh.offset() == (0, 0)


def test_shake_trauma_clamped_and_squared():
    sh = Shake(max_offset=100, seed=3)
    sh.add(5)
    assert sh.trauma == 1.0
    big = max(abs(v) for v in sh.offset())
    sh.trauma = 0.3
    small = max(abs(v) for v in sh.offset())
    assert small <= 100 * 0.09 + 1 and big > small


def test_animation_once_never_wraps_past_the_end():
    a = Animation(list("abc"), fps=10, loop=False)
    seen = []
    for _ in range(8):
        a.update(0.1)
        seen.append(a.frame)
    assert seen == list("bcccccc") + ["c"]
