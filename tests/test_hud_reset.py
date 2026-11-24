"""A new, continued or retried run shows its score at once: no count-up, no fake popups."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.game import Game
from systems import progress as P
from tests.test_continue import clear_floor_one, press
from ui.hud import HUD


@pytest.fixture
def game():
    g = Game()
    g.running = True
    return g


def frame(game):
    if game.state == "briefing":
        game._end_briefing()
    game.update(1 / 60)
    game.render()


def test_hud_reset_snaps_the_score_and_drops_old_popups():
    pygame.init()
    hud = HUD()
    surface = pygame.Surface((960, 640))
    hud.render(surface, "level4", score=800, security_level=40)
    hud.render(surface, "level4", score=700, security_level=60)
    assert hud.popups
    hud.reset(950)
    assert hud.popups == [] and hud._score_value(950) == 950
    hud.render(surface, "level4", score=950, security_level=0)
    assert hud.popups == []                              # the jump to 950 is not "+250 earned"


def test_retrying_a_floor_shows_the_saved_score_at_once(game):
    clear_floor_one(game)                                 # saves the run at Floor 2
    saved = P.load_progress()["score"]
    frame(game)
    game.score.add(180)                                   # points earned on the floor...
    for _ in range(30):
        frame(game)
    game.change_state("lose")                             # ...then lost
    press(game, pygame.K_f)                               # F: retry the floor
    assert game.state == "playing" and game.score.get_score() == saved
    frame(game)
    assert game.hud._score_value(saved) == saved          # no count-down from the lost run
    assert game.hud.popups == []


def test_a_new_run_starts_at_zero_on_the_hud(game):
    clear_floor_one(game)
    for _ in range(30):
        frame(game)
    assert game.hud._shown_score > 0
    press(game, pygame.K_ESCAPE)
    press(game, pygame.K_m)
    press(game, pygame.K_RETURN)
    press(game, pygame.K_ESCAPE)                          # skip the story
    frame(game)
    assert game.hud._shown_score == 0 and game.hud.popups == []
