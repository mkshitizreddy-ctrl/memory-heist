"""The story card types its text out, and keys skip ahead in two steps."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.story import STORY
from ui.story_screens import StoryScreen

BEAT = STORY["intro"]
TOTAL = sum(len(line) for line in BEAT["lines"])


class RecordingFont:
    def __init__(self, font):
        self._font = font
        self.texts = []

    def render(self, text, *args, **kwargs):
        self.texts.append(text)
        return self._font.render(text, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._font, name)


def key(k=pygame.K_SPACE):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode="")


def shown(screen):
    return sum(len(line) for line in screen.visible_lines())


@pytest.fixture
def screen():
    pygame.init()
    pygame.display.set_mode((960, 640))
    s = StoryScreen()
    s.begin(BEAT)
    return s


def test_nothing_is_shown_before_any_time_passes(screen):
    assert screen.visible_lines() == []
    assert screen.done is False and screen.typing_done is False


def test_text_appears_at_a_steady_speed(screen):
    screen.update(0.1)

    assert shown(screen) == int(0.1 * StoryScreen.CHARS_PER_SECOND)


def test_all_text_appears_and_never_overshoots(screen):
    screen.update(1000)

    assert screen.visible_lines() == BEAT["lines"]
    assert screen.typing_done is True


def test_first_key_completes_the_typing_but_does_not_leave(screen):
    screen.handle_event(key())

    assert screen.visible_lines() == BEAT["lines"]
    assert screen.typing_done is True and screen.done is False


def test_second_key_leaves_the_card(screen):
    screen.handle_event(key())
    screen.handle_event(key())

    assert screen.done is True


def test_other_events_do_nothing(screen):
    screen.handle_event(pygame.event.Event(pygame.MOUSEMOTION, pos=(5, 5), rel=(0, 0), buttons=(0, 0, 0)))

    assert screen.typing_done is False and screen.done is False


def test_skip_leaves_at_once(screen):
    screen.skip()

    assert screen.done is True


def test_begin_starts_over(screen):
    screen.handle_event(key())
    screen.handle_event(key())

    screen.begin(STORY["outro"])

    assert screen.done is False and screen.visible_lines() == []
    assert screen.title == STORY["outro"]["title"]


def test_render_draws_the_title_and_the_typed_lines(screen):
    screen.title_font = RecordingFont(screen.title_font)
    screen.body_font = RecordingFont(screen.body_font)
    screen.update(1000)

    screen.render(pygame.Surface((960, 640)))

    assert BEAT["title"] in screen.title_font.texts
    assert all(line in screen.body_font.texts for line in BEAT["lines"])


def test_render_works_in_coop_mode(screen):
    screen.begin(BEAT, coop=True)

    screen.render(pygame.Surface((960, 640)))
