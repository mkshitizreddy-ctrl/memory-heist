"""Practice: Easy floors and questions, no clocks, no security, and never saved."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

pygame.init()

from core.difficulty import DIFFICULTIES, PRACTICE
from core.game import Game
from systems import progress as P
from ui import menu as M

STORY_SAVE = dict(level="level4", score=640, remaining=301.5, difficulty="medium", coop=False)


@pytest.fixture
def game():
    g = Game()
    g.running = True
    return g


def press(game, key):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, unicode="", mod=0, scancode=0))
    game.handle_events()


def start_practice(game):
    press(game, pygame.K_4)
    assert game.menu.selected_difficulty == PRACTICE
    press(game, pygame.K_RETURN)                       # menu -> intro
    game.story_screen.done = True
    game._leave_story()                                # intro -> Level 1 briefing
    game._end_briefing()
    assert game.state == "playing"


def clear_current_floor(game):
    game.level_manager.current.is_complete = lambda: True
    game.update(1 / 60)


# --- the menu ----------------------------------------------------------------------------
def test_key_4_picks_practice_and_the_menu_says_what_it_does():
    menu = M.MainMenu()
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_4))
    assert menu.selected_difficulty == PRACTICE
    assert M.difficulty_blurb(PRACTICE) == M.PRACTICE_BLURB
    assert len(menu.layout()["chips"]) == len(M.DIFFICULTY_ORDER) == 4


def test_the_four_chips_fit_the_screen_without_overlapping():
    chips = M.MainMenu().layout()["chips"]
    screen = pygame.Rect(0, 0, 960, 640)
    assert all(screen.contains(c) for c in chips)
    assert all(not chips[i].colliderect(chips[i + 1]) for i in range(3))


def test_practice_is_never_a_saveable_difficulty():
    assert PRACTICE not in DIFFICULTIES          # so the save file can never hold or load it


# --- the run -----------------------------------------------------------------------------
def test_practice_plays_easy_with_no_run_clock_and_no_security(game):
    start_practice(game)
    assert game.practice is True
    assert game.difficulty == DIFFICULTIES["easy"]          # every floor sees plain Easy content
    assert not game.timer.active
    game.update(5.0)
    assert not game.timer.expired() and game.state == "playing"
    game.security.increase(20)
    assert game.security.level == 0 and game.security.mistakes == 0


def test_question_clocks_and_the_reactor_never_run_in_practice():
    from types import SimpleNamespace
    from levels.room_base import RoomMixin
    room = RoomMixin()
    room.game = SimpleNamespace(practice=True)
    assert room.clock_dt(3.0) == 0.0
    room.game.practice = False
    room.read_hold = 0.0
    assert room.clock_dt(3.0) == 3.0


def test_practice_never_writes_or_clears_the_story_save(game):
    assert P.save_progress(**STORY_SAVE)
    path = os.environ[P.ENV_VAR]
    with open(path, "rb") as f:
        before = f.read()
    start_practice(game)
    clear_current_floor(game)                            # a clear would normally save
    assert game.level_manager.current_name == "level2"
    game.change_state("win")                             # a win would normally clear the save
    with open(path, "rb") as f:
        assert f.read() == before
    assert P.load_progress() == STORY_SAVE


def test_a_practice_win_shows_a_score_but_no_leaderboard_or_badges(game, monkeypatch):
    recorded = []
    monkeypatch.setattr(game.stats, "record_win", lambda *a, **k: recorded.append(a) or ([], []))
    start_practice(game)
    game.score.add(200)
    game.change_state("win")
    assert game.win_screen.difficulty == "Practice" and game.win_screen.score > 0
    assert game.win_screen.entering is False and game.win_screen.badges == []   # no name entry
    assert recorded == []                                                        # no badges, no win stats


def test_continue_still_loads_the_story_run_after_practice(game):
    assert P.save_progress(**STORY_SAVE)
    start_practice(game)
    press(game, pygame.K_ESCAPE)                         # pause
    press(game, pygame.K_m)                              # back to the menu
    assert game.state == "menu" and game.saved_run == STORY_SAVE
    press(game, pygame.K_l)                              # Continue
    assert game.practice is False
    assert game.level_manager.current_name == "level4"
    assert game.difficulty == DIFFICULTIES["medium"] and game.timer.active
    assert game.security.penalty_multiplier == DIFFICULTIES["medium"]["security_penalty_multiplier"]
