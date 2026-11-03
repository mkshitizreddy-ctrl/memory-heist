"""The hero breathes, blinks, bounces when walking and squashes on start/stop."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from collections import defaultdict

import pygame
import pytest

from core import player as player_mod
from core.hero_sprites import make_hero_frames
from core.player import Player, blink_closed, breath_offset, walk_bounce


@pytest.fixture(autouse=True)
def display():
    pygame.init()
    pygame.display.set_mode((64, 64))


def held(*keys):
    pressed = defaultdict(bool)
    for key in keys:
        pressed[key] = True
    return pressed


def render(player):
    surface = pygame.Surface((96, 96), pygame.SRCALPHA)
    player.rect.topleft = (32, 32)
    player.draw(surface)
    return surface


def top_row(surface):
    """First row that holds a fully opaque sprite pixel (shadow is translucent)."""
    for y in range(surface.get_height()):
        for x in range(surface.get_width()):
            if surface.get_at((x, y))[3] == 255:
                return y
    return None


def same_pixels(a, b):
    return pygame.image.tostring(a, "RGBA") == pygame.image.tostring(b, "RGBA")


# --- timing helpers ---------------------------------------------------------

def test_blink_happens_once_per_period_at_its_end():
    period, length = player_mod.BLINK_PERIOD, player_mod.BLINK_LENGTH
    assert not blink_closed(0.0)
    assert not blink_closed(period - length - 0.01)
    assert blink_closed(period - length)
    assert blink_closed(period - 0.01)
    assert not blink_closed(period)            # reopens and the cycle repeats
    assert blink_closed(2 * period - 0.01)


def test_breath_rises_for_half_of_every_period():
    period = player_mod.BREATH_PERIOD
    assert breath_offset(0.0) == 0
    assert breath_offset(period / 2 - 0.01) == 0
    assert breath_offset(period / 2) == 1
    assert breath_offset(period - 0.01) == 1
    assert breath_offset(period) == 0


def test_walk_bounce_lifts_only_the_passing_frames():
    assert [walk_bounce(i) for i in range(4)] == [0, player_mod.BOUNCE_PX, 0, player_mod.BOUNCE_PX]


# --- drawing ---------------------------------------------------------------

def test_standing_character_breathes_one_pixel():
    p = Player(0, 0, palette="ghost")
    p.idle_time = 0.0
    low = top_row(render(p))
    p.idle_time = player_mod.BREATH_PERIOD * 0.75
    high = top_row(render(p))
    assert low - high == 1


def test_blink_changes_only_the_eyes():
    p = Player(0, 0, palette="ghost")
    p.idle_time = 0.0
    open_eyes = render(p)
    p.idle_time = player_mod.BLINK_PERIOD - 0.05
    shut = render(p)
    assert not same_pixels(open_eyes, shut)
    differing = sum(
        1 for y in range(96) for x in range(96)
        if open_eyes.get_at((x, y)) != shut.get_at((x, y)))
    assert 0 < differing < 60          # a visor-sized patch, not a different sprite


def test_hero_blink_frame_differs_from_idle_in_the_eye_pixels_only():
    for name in ("ghost", "echo"):
        frames = make_hero_frames(name)
        idle, blink = frames["idle"], frames["blink"]
        assert idle.get_size() == blink.get_size()
        diff = [(x, y) for y in range(idle.get_height()) for x in range(idle.get_width())
                if idle.get_at((x, y)) != blink.get_at((x, y))]
        assert diff, name
        assert len(diff) < idle.get_width() * idle.get_height() // 8, name


def test_legacy_palette_sprites_without_a_blink_frame_still_draw():
    p = Player(0, 0, palette="cyan")
    p.idle_time = player_mod.BLINK_PERIOD - 0.05
    assert top_row(render(p)) is not None


def test_walking_bounces_on_passing_frames():
    p = Player(0, 0, palette="ghost")
    p.moving = True
    p.anim_time = 0.5 / player_mod.WALK_FPS           # frame 0: contact pose
    contact = top_row(render(p))
    p.anim_time = 1.5 / player_mod.WALK_FPS           # frame 1: passing pose
    passing = top_row(render(p))
    assert contact - passing == player_mod.BOUNCE_PX


def test_facing_left_draws_the_mirrored_frame():
    p = Player(0, 0, palette="ghost")
    image, lift = p.current_pose()
    p.facing_left = True
    drawn = render(p)

    expected = pygame.Surface((96, 96), pygame.SRCALPHA)
    shadow_only = Player(0, 0, palette="ghost")
    shadow_only.frames = {"idle": pygame.Surface((1, 1), pygame.SRCALPHA)}
    shadow_only.frames["walk"] = [shadow_only.frames["idle"]] * 4
    shadow_only.rect.topleft = (32, 32)
    shadow_only.draw(expected)
    expected.blit(pygame.transform.flip(image, True, False), (32, 32 - lift))
    assert same_pixels(drawn, expected)


# --- squash and stretch ------------------------------------------------------

def walk_for(player, frames=120):
    for _ in range(frames):
        player.handle_input(held(pygame.K_d), 1 / 60)


def test_starting_to_walk_stretches_the_character_tall():
    p = Player(0, 0)
    p.handle_input(held(pygame.K_d), 1 / 60)
    peak = 0.0
    for _ in range(20):
        p.handle_input(held(pygame.K_d), 1 / 60)
        peak = max(peak, p.squash.x)
    assert peak > 0.04                       # taller than rest, by a visible amount


def test_stopping_squashes_the_character_flat_then_settles():
    p = Player(0, 0)
    walk_for(p)
    assert p.squash.at_rest
    low = 0.0
    for _ in range(20):
        p.handle_input(held(), 1 / 60)
        low = min(low, p.squash.x)
    assert low < -0.04                       # squashed by a visible amount
    for _ in range(240):
        p.handle_input(held(), 1 / 60)
    assert p.squash.at_rest


def test_squash_really_changes_the_drawn_sprite():
    p = Player(0, 0, palette="ghost")
    walk_for(p)
    p.moving = False
    p.idle_time = 0.0
    rest = render(p)
    p.squash.x = -0.12                       # mid-squash
    squashed = render(p)
    assert not same_pixels(rest, squashed)
    p.squash.x = 0.0
    p.squash.v = 0.0
    assert same_pixels(render(p), rest)


def test_resting_character_is_drawn_exactly_as_its_frame():
    p = Player(0, 0, palette="ghost")
    p.handle_input(held(), 1 / 60)
    assert p.squash.at_rest
    image, lift = p.current_pose()
    drawn = render(p)
    for y in range(96):
        for x in range(96):
            fx, fy = x - 32, y - (32 - lift)
            if 0 <= fx < 32 and 0 <= fy < 32 and image.get_at((fx, fy))[3] == 255:
                assert drawn.get_at((x, y)) == image.get_at((fx, fy))


def test_idle_clock_restarts_when_the_player_moves():
    p = Player(0, 0)
    for _ in range(30):
        p.handle_input(held(), 1 / 60)
    assert p.idle_time > 0.4
    p.handle_input(held(pygame.K_d), 1 / 60)
    assert p.idle_time == 0.0


def test_shadow_narrows_when_the_body_lifts():
    p = Player(0, 0, palette="ghost")
    p.idle_time = 0.0
    low = render(p)
    p.idle_time = player_mod.BREATH_PERIOD * 0.75

    def shadow_width(surface):
        row = 32 + 32 + 2 - 4          # a row through the middle of the shadow
        xs = [x for x in range(96) if surface.get_at((x, row))[3] > 0]
        return (max(xs) - min(xs) + 1) if xs else 0

    assert shadow_width(render(p)) < shadow_width(low)
