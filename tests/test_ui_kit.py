import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from ui import theme
from ui.kit import Button, DialogueBox, Typewriter, draw_panel, wrap_text


@pytest.fixture(autouse=True)
def display():
    pygame.init()
    pygame.display.set_mode((400, 300))


@pytest.fixture
def font():
    return pygame.font.Font(None, 24)


def ev(kind, pos, button=1):
    if kind == pygame.MOUSEMOTION:
        return pygame.event.Event(kind, pos=pos, rel=(0, 0), buttons=(0, 0, 0))
    return pygame.event.Event(kind, pos=pos, button=button)


def test_panel_draws_fill_and_border():
    s = pygame.Surface((200, 100))
    s.fill((0, 0, 0))
    draw_panel(s, (20, 20, 100, 50), fill=(10, 200, 10), border=(200, 10, 10), shadow=False)
    assert s.get_at((70, 45))[:3] == (10, 200, 10)
    assert s.get_at((70, 20))[:3] == (200, 10, 10)
    assert s.get_at((5, 5))[:3] == (0, 0, 0)


def test_panel_shadow_darkens_below_right():
    s = pygame.Surface((200, 100))
    s.fill((100, 100, 100))
    draw_panel(s, (20, 20, 100, 50), shadow=True)
    assert s.get_at((122, 50))[:3] != (100, 100, 100)
    assert s.get_at((122, 8))[:3] == (100, 100, 100)


def test_wrap_never_drops_text_and_respects_width(font):
    text = "The memory chip holds everything WARDEN erased from you.\nSecond line."
    lines = wrap_text(text, font, 160)
    assert " ".join(lines).replace("  ", " ") == text.replace("\n", " ")
    assert all(font.size(l)[0] <= 160 or " " not in l for l in lines)
    assert len(lines) >= 3


def test_wrap_long_word_kept(font):
    assert wrap_text("A" * 80, font, 50) == ["A" * 80]


def test_typewriter_reveals_and_skips():
    t = Typewriter("hello", cps=10)
    assert t.visible == "" and not t.done
    t.update(0.25)
    assert t.visible == "he"
    t.update(-5)
    assert t.visible == "he"
    t.skip()
    assert t.visible == "hello" and t.done


def test_typewriter_empty_text_done():
    assert Typewriter("").done


def test_button_click_requires_press_and_release_inside(font):
    b = Button((100, 100, 120, 40), "GO", font)
    inside, outside = (150, 120), (10, 10)
    assert not b.handle_event(ev(pygame.MOUSEBUTTONDOWN, inside)) is True
    assert b.handle_event(ev(pygame.MOUSEBUTTONUP, inside)) is True
    b.handle_event(ev(pygame.MOUSEBUTTONDOWN, inside))
    assert b.handle_event(ev(pygame.MOUSEBUTTONUP, outside)) is False
    b.handle_event(ev(pygame.MOUSEBUTTONDOWN, outside))
    assert b.handle_event(ev(pygame.MOUSEBUTTONUP, inside)) is False


def test_disabled_button_never_clicks(font):
    b = Button((100, 100, 120, 40), "GO", font, enabled=False)
    b.handle_event(ev(pygame.MOUSEBUTTONDOWN, (150, 120)))
    assert b.handle_event(ev(pygame.MOUSEBUTTONUP, (150, 120))) is False
    assert not b.hover and not b.pressed


def test_button_grows_on_hover_and_returns(font):
    b = Button((100, 100, 120, 40), "GO", font)
    b.handle_event(ev(pygame.MOUSEMOTION, (150, 120)))
    for _ in range(30):
        b.update(0.016)
    assert b.scale == pytest.approx(1.04, abs=1e-6)
    b.handle_event(ev(pygame.MOUSEMOTION, (5, 5)))
    for _ in range(30):
        b.update(0.016)
    assert b.scale == pytest.approx(1.0, abs=1e-6)


def test_button_squashes_when_pressed(font):
    b = Button((100, 100, 120, 40), "GO", font)
    b.handle_event(ev(pygame.MOUSEMOTION, (150, 120)))
    b.handle_event(ev(pygame.MOUSEBUTTONDOWN, (150, 120)))
    for _ in range(30):
        b.update(0.016)
    assert b.scale < 1.0


def test_button_draw_changes_pixels_by_state(font):
    def shot(b):
        s = pygame.Surface((400, 300))
        s.fill(theme.INK)
        b.draw(s)
        return pygame.image.tostring(s, "RGB")
    normal = Button((100, 100, 120, 40), "GO", font)
    hov = Button((100, 100, 120, 40), "GO", font)
    hov.hover = True
    off = Button((100, 100, 120, 40), "GO", font, enabled=False)
    assert len({shot(normal), shot(hov), shot(off)}) == 3


def test_dialogue_skip_then_advance(font):
    d = DialogueBox("Warden", "You should not be here.", cps=10)
    assert d.advance() is False
    assert d.typer.done
    assert d.advance() is True


def test_dialogue_draws_name_and_text(font):
    d = DialogueBox("Echo", "Door is open.", accent=theme.TEAL, cps=1000)
    d.update(1)
    s = pygame.Surface((400, 300))
    s.fill(theme.INK)
    d.draw(s, (10, 150, 380, 120), font)
    assert any(s.get_at((x, 150 + 16 + 4))[:3] == theme.TEAL for x in range(20, 80))
    assert pygame.image.tostring(s, "RGB") != pygame.image.tostring(
        pygame.Surface((400, 300)), "RGB")


def test_dialogue_clips_overflow_inside_panel(font):
    d = DialogueBox("W", "word " * 400, cps=1e6)
    d.update(1)
    s = pygame.Surface((400, 300))
    s.fill((0, 0, 0))
    d.draw(s, (10, 10, 200, 80), font)
    sub = s.subsurface((0, 95, 400, 205))
    assert pygame.image.tostring(sub, "RGB") == bytes(400 * 205 * 3)
