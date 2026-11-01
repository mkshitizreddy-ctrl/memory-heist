"""Character art pass: richer Ghost and Echo, a WARDEN portrait, blinking."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.hero_portrait import BLINK_LENGTH, BLINK_PERIOD, is_blinking, make_portrait
from core.story import STORY
from ui.story_screens import StoryScreen

NAMES = ["ghost", "echo", "warden"]


@pytest.fixture(autouse=True)
def display():
    pygame.init()
    pygame.display.set_mode((960, 640))


def pixels(surface):
    return pygame.image.tostring(surface, "RGBA")


def colours(surface):
    """Distinct opaque colours in a portrait."""
    found = set()
    w, h = surface.get_size()
    for x in range(w):
        for y in range(h):
            c = surface.get_at((x, y))
            if c.a == 255:
                found.add((c.r, c.g, c.b))
    return found


def silhouette(surface):
    """The set of pixels that are not transparent."""
    w, h = surface.get_size()
    return {(x, y) for x in range(w) for y in range(h) if surface.get_at((x, y)).a > 0}


@pytest.mark.parametrize("name", NAMES)
def test_every_character_is_detailed_not_flat(name):
    # Shading, highlights and glow need many tones; the old sprite had few.
    assert len(colours(make_portrait(name, 192))) >= 14


@pytest.mark.parametrize("name", NAMES)
@pytest.mark.parametrize("size", [64, 128, 256])
def test_every_character_renders_at_every_card_size(name, size):
    assert make_portrait(name, size, tick=3).get_size() == (size, size)


@pytest.mark.parametrize("name", NAMES)
def test_every_character_leaves_a_transparent_background(name):
    assert make_portrait(name, 96).get_at((0, 0)).a == 0


@pytest.mark.parametrize("name", NAMES)
def test_every_character_fills_a_good_part_of_the_card(name):
    covered = len(silhouette(make_portrait(name, 96)))
    assert covered > 0.25 * 96 * 96


def test_echo_has_her_own_silhouette_not_a_recolour():
    assert silhouette(make_portrait("ghost", 96)) != silhouette(make_portrait("echo", 96))


def test_warden_is_neither_thief():
    warden = silhouette(make_portrait("warden", 96))
    assert warden != silhouette(make_portrait("ghost", 96))
    assert warden != silhouette(make_portrait("echo", 96))


def test_warden_glows_red():
    image = make_portrait("warden", 96)
    reds = [c for c in colours(image) if c[0] > 200 and c[1] < 90 and c[2] < 90]
    assert reds


@pytest.mark.parametrize("name", NAMES)
def test_every_character_animates(name):
    assert pixels(make_portrait(name, 96, tick=0)) != pixels(make_portrait(name, 96, tick=40))


@pytest.mark.parametrize("name", NAMES)
def test_the_same_tick_gives_the_same_picture(name):
    assert pixels(make_portrait(name, 96, tick=11)) == pixels(make_portrait(name, 96, tick=11))


def test_blinking_is_brief_and_regular():
    blinking = [t for t in range(BLINK_PERIOD * 3) if is_blinking(t)]

    assert len(blinking) == 3 * BLINK_LENGTH
    assert not is_blinking(0)
    assert is_blinking(BLINK_PERIOD - 1)
    assert not is_blinking(BLINK_PERIOD)


@pytest.mark.parametrize("name", ["ghost", "echo"])
def test_a_blink_changes_the_face(name):
    open_eyes = make_portrait(name, 96, tick=0)
    shut = make_portrait(name, 96, tick=BLINK_PERIOD - 1)
    # Same glow phase is not guaranteed, so compare only the eye band.
    band = pygame.Rect(0, int(96 * 0.18), 96, int(96 * 0.2))
    assert pixels(open_eyes.subsurface(band)) != pixels(shut.subsurface(band))


def test_a_blink_dims_the_visor():
    def bright(surface):
        band = pygame.Rect(0, int(96 * 0.18), 96, int(96 * 0.2))
        part = surface.subsurface(band)
        return sum(1 for x in range(96) for y in range(band.height)
                   if part.get_at((x, y)).b > 220 and part.get_at((x, y)).a == 255)

    assert bright(make_portrait("ghost", 96, tick=BLINK_PERIOD - 1)) < bright(
        make_portrait("ghost", 96, tick=0)
    )


def test_warden_appears_on_the_intro_and_every_level_but_not_the_ending():
    for key in ["intro", "level1", "level2", "level3", "level4", "level5", "final_vault"]:
        assert STORY[key].get("warden") is True, key
    assert not STORY["outro"].get("warden")


def test_the_story_screen_remembers_whether_warden_is_on_the_card():
    screen = StoryScreen()
    screen.begin(STORY["level1"])
    assert screen.warden is True
    screen.begin(STORY["outro"])
    assert screen.warden is False


def test_a_card_with_warden_draws_differently_from_one_without():
    surface = pygame.Surface((960, 640))
    with_w = StoryScreen()
    with_w.begin(STORY["level1"])
    with_w.render(surface)
    first = pixels(surface.copy())

    without = StoryScreen()
    beat = dict(STORY["level1"], warden=False)
    without.begin(beat)
    without.render(surface)

    assert first != pixels(surface)
