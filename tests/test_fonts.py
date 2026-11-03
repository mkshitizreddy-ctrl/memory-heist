"""The shared font helper: real font, cached, same layout size, safe fallback."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from ui import fonts


@pytest.fixture(autouse=True)
def _fresh():
    pygame.font.init()
    fonts.clear_cache()
    yield
    fonts.clear_cache()


def test_font_files_are_bundled():
    assert (fonts.FONT_DIR / fonts.REGULAR).is_file()
    assert (fonts.FONT_DIR / fonts.BOLD).is_file()


def test_same_request_returns_same_font_object():
    assert fonts.ui_font(24) is fonts.ui_font(24)
    assert fonts.ui_font(24) is not fonts.ui_font(26)


def test_bold_is_a_different_font_and_looks_heavier():
    regular, bold = fonts.ui_font(40), fonts.ui_font(40, bold=True)
    assert regular is not bold

    def ink(font):
        surf = font.render("MEMORY HEIST", True, (255, 255, 255))
        return sum(1 for x in range(surf.get_width()) for y in range(surf.get_height())
                   if surf.get_at((x, y))[3] > 128)

    assert ink(bold) > ink(regular)


def test_width_stays_close_to_the_old_default_font():
    """Switching over must not move layouts: text width within 10%."""
    sample = "NOVACORP RECEPTION  Security 45%  Press E to pick up"
    for size in (16, 20, 22, 24, 26, 28, 34, 64):
        old = pygame.font.Font(None, size).size(sample)[0]
        new = fonts.ui_font(size).size(sample)[0]
        assert abs(new - old) / old < 0.10, (size, old, new)


def test_tiny_sizes_stay_readable():
    assert fonts.pixel_size(1) == fonts.MIN_PIXELS


def test_missing_font_file_falls_back_instead_of_crashing(monkeypatch, tmp_path):
    monkeypatch.setattr(fonts, "FONT_DIR", tmp_path)
    font = fonts.ui_font(24)
    assert font.render("still works", True, (255, 255, 255)).get_width() > 0


def test_cache_is_dropped_when_pygame_quits():
    """A font made before pygame.quit() is dead; reusing it would crash."""
    before = fonts.ui_font(24)
    pygame.quit()
    pygame.font.init()
    after = fonts.ui_font(24)
    assert after is not before
    assert after.render("alive", True, (255, 255, 255)).get_width() > 0
