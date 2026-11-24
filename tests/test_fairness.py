"""Fairness: security cools between floors, kinder question clocks, and F retries the lost floor."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.difficulty import DIFFICULTIES, FLOOR_COOLDOWN, lift_cooldown, question_time_multiplier
from core.game import Game
from systems import progress as P
from systems.security import SecurityMeter
from tests.test_continue import clear_floor_one, press


@pytest.fixture
def game():
    g = Game()
    g.running = True
    return g


def test_cool_never_goes_below_zero():
    s = SecurityMeter()
    s.increase(30)
    s.cool(20)
    assert s.level == 10
    s.cool(50)
    assert s.level == 0


def test_question_clocks_are_kinder_on_easy_and_medium():
    assert question_time_multiplier("easy") > question_time_multiplier("medium") > 1.0
    assert question_time_multiplier("hard") < 1.0
    assert question_time_multiplier(DIFFICULTIES["easy"]) == question_time_multiplier("easy")
    assert question_time_multiplier("nonsense") == question_time_multiplier("medium")


def test_floor4_slip_clock_is_kinder_on_easy():
    pygame.font.init()                     # the floor loads its fonts; run alone, nothing else has
    from types import SimpleNamespace
    from levels.floor4_archive import BASE_SECONDS, ArchiveFloor
    limits = {d: ArchiveFloor(game=SimpleNamespace(difficulty=d)).time_limit for d in ("easy", "medium", "hard")}
    assert limits["easy"] > limits["medium"] > limits["hard"]
    assert limits["easy"] >= round(BASE_SECONDS * question_time_multiplier("easy"))


@pytest.mark.parametrize("level, cooled", [(100, 50), (90, 45), (61, 30), (60, 30), (50, 25),
                                           (40, 15), (25, 0), (20, 0), (0, 0)])
def test_the_lift_takes_off_half_the_meter_but_at_least_the_minimum(level, cooled):
    s = SecurityMeter()
    s.level = level
    s.cool(lift_cooldown(level))
    assert s.level == cooled
    assert lift_cooldown(level) >= FLOOR_COOLDOWN


@pytest.mark.parametrize("level, cooled", [(60, 30), (90, 45), (30, 5)])
def test_security_cools_when_a_floor_is_cleared(game, level, cooled):
    press(game, pygame.K_RETURN)
    game.story_screen.done = True
    game._leave_story()
    game._end_briefing()
    game.security.level = level
    game.level_manager.current.is_complete = lambda: True
    game.update(1 / 60)
    assert game.level_manager.current_name == "level2"
    assert game.security.level == cooled


def test_f_retries_the_floor_that_was_lost(game):
    clear_floor_one(game)
    assert game.level_manager.current_name == "level2"
    if game.state != "playing":
        game._end_briefing()
    game.score.add(300)
    game.change_state("lose")
    assert game._lose_can_retry
    press(game, pygame.K_f)
    assert game.state == "playing"
    assert game.level_manager.current_name == "level2"
    assert game.score.get_score() == P.load_progress()["score"]      # the floor's points start over
    assert game.security.level == 0


def test_floor1_loss_offers_only_a_new_run(game):
    press(game, pygame.K_RETURN)
    game.story_screen.done = True
    game._leave_story()
    game._end_briefing()
    game.change_state("lose")
    assert not game._lose_can_retry
    press(game, pygame.K_f)
    assert game.state == "lose"


def test_lose_prompt_fits():
    from ui.screens import LoseScreen
    surf = pygame.Surface((960, 640))
    LoseScreen().render(surf, 10, "level3", retry_floor=True)
