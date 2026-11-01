"""The final score rewards time left and the chosen difficulty."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.difficulty import DIFFICULTIES, get_difficulty
from core.game import Game
from systems.scoring import POINTS_PER_SECOND_LEFT, final_score


class RecordingFont:
    def __init__(self, font):
        self._font = font
        self.texts = []

    def render(self, text, *args, **kwargs):
        self.texts.append(text)
        return self._font.render(text, *args, **kwargs)


class SpyLeaderboard:
    def __init__(self):
        self.added = []

    def top(self, count):
        return []

    def add(self, name, score, difficulty, coop):
        self.added.append(score)
        return 1


# ---- the pure calculation -------------------------------------------------

def test_one_point_per_second_left():
    assert POINTS_PER_SECOND_LEFT == 1


def test_time_bonus_is_added_to_the_base_score():
    result = final_score(1000, 300, 1.0)

    assert result == {"base": 1000, "time_bonus": 300, "multiplier": 1.0, "total": 1300}


def test_partial_seconds_do_not_count():
    assert final_score(0, 300.9, 1.0)["time_bonus"] == 300


@pytest.mark.parametrize("left", [0, -5, None])
def test_no_time_left_gives_no_bonus(left):
    assert final_score(500, left, 1.0)["time_bonus"] == 0


@pytest.mark.parametrize("multiplier, expected", [(0.8, 1040), (1.0, 1300), (1.25, 1625)])
def test_difficulty_multiplier_scales_base_plus_bonus(multiplier, expected):
    assert final_score(1000, 300, multiplier)["total"] == expected


def test_total_is_a_whole_number():
    assert isinstance(final_score(333, 77, 0.8)["total"], int)


def test_presets_carry_a_score_multiplier():
    got = {k: v["score_multiplier"] for k, v in DIFFICULTIES.items()}

    assert got == {"easy": 0.8, "medium": 1.0, "hard": 1.25}


# ---- wiring into the game -------------------------------------------------

@pytest.fixture
def game():
    g = Game()
    g.difficulty = get_difficulty("hard")
    g._start_new_run()
    g.win_screen.leaderboard = SpyLeaderboard()
    g.score.add(100)
    g.timer.remaining = 200.4
    return g


def test_winning_applies_time_bonus_and_multiplier(game):
    game.change_state("win")

    assert game.win_screen.score == 375  # (100 + 200) * 1.25 = 375


def test_saved_leaderboard_score_is_the_final_score(game):
    game.change_state("win")
    game.win_screen.handle_event(
        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode="\r")
    )

    assert game.win_screen.leaderboard.added == [375]


def test_the_running_score_is_left_untouched(game):
    game.change_state("win")

    assert game.score.get_score() == 100


def test_win_screen_shows_the_final_score_and_breakdown(game):
    game.change_state("win")
    screen = game.win_screen
    screen.subtitle_font = RecordingFont(screen.subtitle_font)
    screen.row_font = RecordingFont(screen.row_font)
    screen.prompt_font = RecordingFont(screen.prompt_font)

    game.render()

    texts = screen.subtitle_font.texts + screen.row_font.texts + screen.prompt_font.texts
    assert "Final Score: 375" in texts
    joined = " ".join(texts)
    assert "Base 100" in joined and "Time bonus 200" in joined and "x1.25" in joined
