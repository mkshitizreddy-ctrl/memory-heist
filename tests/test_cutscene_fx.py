"""Cutscene effects: data streams, scanlines, glitch, alert WARDEN, story card wiring."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.hero_portrait import make_portrait
from core.story import STORY
from ui.cutscene_fx import (
    FLICKER_SECONDS,
    DataStreams,
    draw_glitch,
    draw_scanlines,
    open_flicker,
    periodic_glitch,
)
from ui.story_screens import StoryScreen


@pytest.fixture(autouse=True)
def display():
    pygame.init()
    pygame.display.set_mode((960, 640))


def pixels(surface):
    return pygame.image.tostring(surface, "RGBA")


def striped(width=200, height=120):
    """A surface with vertical stripes so any shifted slice is visible."""
    s = pygame.Surface((width, height))
    for x in range(width):
        pygame.draw.line(s, ((x * 5) % 256, (x * 11) % 256, (x * 17) % 256), (x, 0), (x, height))
    return s


def grey(value=128, size=(200, 120)):
    s = pygame.Surface(size)
    s.fill((value, value, value))
    return s


# ---- data streams -------------------------------------------------------

def test_streams_fall_over_time():
    streams = DataStreams(400, 300)
    before = streams.heads()

    streams.update(0.5)

    assert streams.heads() != before
    assert all(b2 > b1 for b1, b2 in zip(before, streams.heads()) if b2 - b1 > 0)


def test_streams_are_the_same_for_the_same_seed():
    a, b = DataStreams(400, 300, seed=3), DataStreams(400, 300, seed=3)
    a.update(1.0)
    b.update(1.0)

    assert a.heads() == b.heads()


def test_streams_wrap_so_they_never_run_out():
    streams = DataStreams(400, 300)
    for _ in range(600):
        streams.update(0.1)

    limit = 300 + 20 * 40
    assert all(-limit < h < limit for h in streams.heads())


def test_streams_draw_something_but_stay_faint():
    streams = DataStreams(400, 300)
    streams.update(1.0)
    surface = pygame.Surface((400, 300))
    surface.fill((0, 0, 0))

    streams.draw(surface)

    brightest = max(max(surface.get_at((x, y))[:3]) for x in range(0, 400, 2) for y in range(0, 300, 2))
    assert brightest > 0          # something was drawn
    assert brightest <= 100       # but too dim to fight the story text


def test_streams_draw_safely_on_a_tiny_surface():
    streams = DataStreams(960, 640)
    streams.update(1.0)
    streams.draw(pygame.Surface((64, 48)))


# ---- scanlines ----------------------------------------------------------

def test_scanlines_change_the_picture_but_keep_it_bright():
    surface = grey(128)
    draw_scanlines(surface, tick=0)

    values = [surface.get_at((10, y))[0] for y in range(120)]
    mean = sum(values) / len(values)
    assert min(values) < 128
    assert 90 <= mean <= 140


def test_the_scanline_sweep_moves():
    a, b = grey(), grey()
    draw_scanlines(a, tick=0)
    draw_scanlines(b, tick=40)

    assert pixels(a) != pixels(b)


def test_scanlines_keep_the_surface_size():
    surface = grey(size=(321, 77))
    draw_scanlines(surface, tick=5)

    assert surface.get_size() == (321, 77)


# ---- glitch ---------------------------------------------------------------

def test_no_intensity_means_no_glitch():
    surface = striped()
    before = pixels(surface)

    draw_glitch(surface, tick=3, intensity=0)

    assert pixels(surface) == before


def test_glitch_shifts_slices_of_the_picture():
    surface = striped()
    before = pixels(surface)

    draw_glitch(surface, tick=3, intensity=1.0)

    assert pixels(surface) != before
    assert surface.get_size() == (200, 120)


def test_the_same_glitch_tick_gives_the_same_glitch():
    a, b = striped(), striped()
    draw_glitch(a, tick=9, intensity=0.8)
    draw_glitch(b, tick=9, intensity=0.8)

    assert pixels(a) == pixels(b)


def test_opening_flicker_fades_out():
    assert open_flicker(0) == pytest.approx(1.0)
    assert 0 < open_flicker(FLICKER_SECONDS / 2) < 1
    assert open_flicker(FLICKER_SECONDS) == 0
    assert open_flicker(10) == 0


def test_a_short_glitch_repeats_now_and_then():
    hits = [t for t in range(960) if periodic_glitch(t) > 0]

    assert 0 < len(hits) < 960 * 0.1
    assert periodic_glitch(0) == 0


# ---- alert WARDEN -----------------------------------------------------------

def test_warden_looks_different_when_alert():
    assert pixels(make_portrait("warden", 96, tick=10)) != pixels(
        make_portrait("warden", 96, tick=10, alert=True)
    )


def test_alert_is_off_by_default_so_old_pictures_are_unchanged():
    assert pixels(make_portrait("warden", 96, tick=10)) == pixels(
        make_portrait("warden", 96, tick=10, alert=False)
    )


# ---- story card wiring ------------------------------------------------------

def test_the_card_clock_runs_even_after_the_typing_is_done():
    screen = StoryScreen()
    screen.begin(STORY["level1"])
    screen.update(1000)
    assert screen.typing_done
    age = screen.age

    screen.update(0.5)

    assert screen.age == pytest.approx(age + 0.5)


def test_a_new_card_starts_with_the_opening_flicker():
    screen = StoryScreen()
    screen.begin(STORY["level1"])
    assert screen.flicker() == pytest.approx(1.0)

    screen.update(5)
    assert screen.flicker() == 0

    screen.begin(STORY["level2"])
    assert screen.flicker() == pytest.approx(1.0)


def test_warden_is_alert_only_while_its_words_are_typing():
    screen = StoryScreen()
    screen.begin(STORY["level1"])
    assert screen.warden_alert() is True

    screen.update(1000)
    assert screen.warden_alert() is False

    screen.begin(STORY["outro"])
    assert screen.warden_alert() is False


def test_the_streams_move_while_the_card_is_open():
    screen = StoryScreen()
    screen.begin(STORY["level1"])
    before = screen.streams.heads()

    screen.update(0.3)

    assert screen.streams.heads() != before


@pytest.mark.parametrize("size", [(960, 640), (1280, 720), (320, 240)])
def test_the_card_renders_at_any_window_size(size):
    screen = StoryScreen()
    screen.begin(STORY["level1"], coop=True, progress=(0, 6))
    surface = pygame.Surface(size)

    for _ in range(3):
        screen.update(0.05)
        screen.render(surface)

    assert screen.streams.width == size[0]


def test_the_opening_flicker_really_disturbs_the_first_frame():
    surface_a, surface_b = pygame.Surface((960, 640)), pygame.Surface((960, 640))
    fresh, settled = StoryScreen(), StoryScreen()
    fresh.begin(STORY["level1"])
    settled.begin(STORY["level1"])
    settled.update(5)
    fresh.tick = settled.tick = 0  # same animation phase

    fresh.render(surface_a)
    settled.age = 5.0
    settled.render(surface_b)

    assert pixels(surface_a) != pixels(surface_b)
