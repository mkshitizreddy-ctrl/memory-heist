"""Large portraits of Ghost and Echo for the story cards."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.hero_portrait import make_portrait


@pytest.fixture(autouse=True)
def display():
    pygame.init()
    pygame.display.set_mode((64, 64))


def pixels(surface):
    return pygame.image.tostring(surface, "RGBA")


def test_portrait_is_a_square_surface_of_the_requested_size():
    image = make_portrait("ghost", 192)

    assert image.get_size() == (192, 192)


def test_ghost_and_echo_look_different():
    assert pixels(make_portrait("ghost", 96)) != pixels(make_portrait("echo", 96))


def test_the_visor_glow_animates_over_time():
    assert pixels(make_portrait("ghost", 96, tick=0)) != pixels(make_portrait("ghost", 96, tick=30))


def test_the_same_tick_gives_the_same_picture():
    assert pixels(make_portrait("ghost", 96, tick=7)) == pixels(make_portrait("ghost", 96, tick=7))


def test_background_is_transparent_so_it_sits_on_any_card():
    image = make_portrait("ghost", 96)

    assert image.get_at((0, 0)).a == 0


def test_unknown_character_is_rejected():
    with pytest.raises(ValueError):
        make_portrait("nobody", 96)
