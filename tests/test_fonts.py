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


def test_shadowed_text_is_bigger_by_the_offset_and_has_both_colours():
    from ui.kit import shadowed

    font = fonts.ui_font(30, bold=True)
    plain = font.render("VAULT", True, (250, 250, 250))
    out = shadowed(font, "VAULT", (250, 250, 250), shadow=(10, 20, 30), offset=(2, 3))
    assert out.get_size() == (plain.get_width() + 2, plain.get_height() + 3)
    pixels = [out.get_at((x, y)) for x in range(out.get_width()) for y in range(out.get_height())]
    assert any(p[:3] == (250, 250, 250) and p[3] == 255 for p in pixels)  # the text
    assert any(p[:3] == (10, 20, 30) and p[3] == 255 for p in pixels)     # the shadow
    assert out.get_at((0, out.get_height() - 1))[3] == 0                  # corner stays clear


def test_shadow_sits_behind_and_below_the_text():
    from ui.kit import shadowed

    font = fonts.ui_font(40, bold=True)
    out = shadowed(font, "I", (250, 250, 250), shadow=(0, 0, 0), offset=(0, 4))
    column = [out.get_at((x, y)) for y in range(out.get_height()) for x in range(out.get_width())]
    bottom_rows = [out.get_at((x, out.get_height() - 1)) for x in range(out.get_width())]
    assert all(p[:3] != (250, 250, 250) for p in bottom_rows if p[3] > 0)
    assert any(p[:3] == (250, 250, 250) for p in column)


def test_code_font_is_monospaced():
    font = fonts.code_font(20)
    assert font.size("iiii")[0] == font.size("WWWW")[0] == font.size("0.5.")[0]


def test_code_font_keeps_the_decimal_point_visible():
    """0.5 must not collapse into '05': the point gets its own full cell."""
    font = fonts.code_font(20)
    assert font.size("0.5")[0] == pytest.approx(1.5 * font.size("05")[0], abs=1)


def test_code_font_is_cached_and_falls_back(monkeypatch, tmp_path):
    assert fonts.code_font(20) is fonts.code_font(20)
    fonts.clear_cache()
    monkeypatch.setattr(fonts, "FONT_DIR", tmp_path)
    assert fonts.code_font(20).render("0.5", True, (255, 255, 255)).get_width() > 0
