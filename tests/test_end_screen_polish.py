"""Win and lose screens: the score counts up, and empty leaderboard slots stay visible."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from ui import screens as S
from ui.screens import LoseScreen, WinScreen, shown_score


class FakeBoard:
    def __init__(self, entries):
        self.entries = entries

    def top(self, n):
        return self.entries[:n]

    def add(self, *args):
        return 1


class Rec:
    def __init__(self, font):
        self.font, self.texts = font, []

    def render(self, text, *args, **kwargs):
        self.texts.append(text)
        return self.font.render(text, *args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.font, name)


@pytest.fixture
def surf():
    pygame.init()
    return pygame.Surface((960, 640))


def test_shown_score_starts_at_zero_and_ends_on_the_real_score():
    assert shown_score(1234, 0) == 0
    assert shown_score(1234, S.COUNT_FRAMES) == 1234
    assert shown_score(1234, S.COUNT_FRAMES + 99) == 1234


def test_shown_score_only_goes_up_and_eases_out():
    values = [shown_score(1000, t) for t in range(S.COUNT_FRAMES + 1)]
    assert values == sorted(values)
    assert values[S.COUNT_FRAMES // 2] > 500          # fast start, slow finish


def test_zero_or_negative_scores_are_shown_as_given():
    assert shown_score(0, 5) == 0
    assert shown_score(-40, 5) == -40


def test_win_screen_counts_up_then_settles(surf):
    win = WinScreen(FakeBoard([]))
    win.begin(800, "Medium", False)
    win.skip_entry()
    win.big_font = Rec(win.big_font)
    for _ in range(S.COUNT_FRAMES + 3):
        win.render(surf, 800)
    shown = [int(t) for t in win.big_font.texts]
    assert shown[0] < 800 and shown[-1] == 800 and shown == sorted(shown)


def test_begin_restarts_the_count_up(surf):
    win = WinScreen(FakeBoard([]))
    win.begin(500, "Medium", False)
    win.skip_entry()
    for _ in range(S.COUNT_FRAMES + 5):
        win.render(surf, 500)
    win.begin(500, "Medium", False)
    assert win.tick == 0


def test_lose_screen_counts_up_too(surf):
    lose = LoseScreen()
    lose.big_font = Rec(lose.big_font)
    for _ in range(S.COUNT_FRAMES + 3):
        lose.render(surf, 420)
    shown = [int(t) for t in lose.big_font.texts]
    assert shown[0] < 420 and shown[-1] == 420


def test_empty_leaderboard_slots_are_drawn_as_placeholders(surf):
    win = WinScreen(FakeBoard([{"name": "ASH", "score": 900, "difficulty": "Hard"}]))
    win.begin(1, "Medium", False)
    win.skip_entry()
    win.row_font = Rec(win.row_font)
    win.render(surf, 1)
    texts = win.row_font.texts
    assert texts.count("- - -") == S.TABLE_ROWS - 1
    assert {"2.", "3.", "4.", "5."} <= set(texts)


def test_a_full_leaderboard_has_no_placeholders(surf):
    rows = [{"name": f"P{i}", "score": 100 - i, "difficulty": "Easy"} for i in range(S.TABLE_ROWS)]
    win = WinScreen(FakeBoard(rows))
    win.begin(1, "Medium", False)
    win.skip_entry()
    win.row_font = Rec(win.row_font)
    win.render(surf, 1)
    assert "- - -" not in win.row_font.texts
