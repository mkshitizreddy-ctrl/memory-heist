"""Save and continue: floors are saved as they are reached, and the menu resumes them."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.game import Game
from systems import progress as P


@pytest.fixture
def game():
    g = Game()
    g.running = True
    return g


def press(game, key):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, unicode="", mod=0, scancode=0))
    game.handle_events()


def clear_floor_one(game):
    """Finish Level 1 the way the game does: the level reports it is complete."""
    game.menu.selected_difficulty = "hard"
    game.menu.coop = True
    press(game, pygame.K_RETURN)                       # menu -> intro
    game.story_screen.done = True
    game._leave_story()                                # intro -> Level 1 briefing
    game._end_briefing()
    game.coop = True
    game.score.add(120)
    game.level_manager.current.is_complete = lambda: True
    game.update(1 / 60)


def test_a_fresh_game_has_nothing_to_continue(game):
    assert game.saved_run is None and game.menu.saved_text is None
    press(game, pygame.K_l)
    assert game.state == "menu"


def test_clearing_a_floor_saves_the_run(game):
    clear_floor_one(game)
    saved = P.load_progress()
    assert saved["level"] == "level2" and saved["score"] == 120
    assert saved["difficulty"] == "hard" and saved["coop"] is True
    assert 0 < saved["remaining"] <= game.timer.get_remaining() + 1


def test_the_first_floor_alone_is_not_saved(game):
    press(game, pygame.K_RETURN)
    game.story_screen.done = True
    game._leave_story()
    assert P.load_progress() is None


def test_l_on_the_menu_resumes_the_saved_floor(game):
    P.save_progress("level3", 450, 321.5, "easy", True)
    game._refresh_saved_run()
    assert game.menu.saved_text == "Floor 3 - 450 pts"
    press(game, pygame.K_l)
    assert game.state == "briefing"
    assert game.level_manager.current_name == "level3"
    assert game.score.get_score() == 450
    assert game.timer.active and game.timer.get_remaining() == pytest.approx(321.5)
    assert game.coop is True and game.menu.coop is True
    assert game.menu.selected_difficulty == "easy"
    assert game.difficulty["label"] == "EASY" and game.hints.enabled
    assert game.security.level == 0


def test_continuing_does_not_overwrite_the_save_or_skip_the_briefing(game):
    P.save_progress("level3", 450, 321.5, "medium", False)
    game._refresh_saved_run()
    press(game, pygame.K_l)
    game._end_briefing()
    game.update(1 / 60)
    assert P.load_progress()["level"] == "level3"


def test_l_does_nothing_while_playing_or_without_a_save(game):
    P.save_progress("level3", 450, 321.5, "medium", False)
    game._refresh_saved_run()
    game._start_new_run()
    press(game, pygame.K_l)
    assert game.level_manager.current_name == "level1" and game.state == "playing"


def test_winning_clears_the_save(game):
    P.save_progress("level3", 450, 321.5, "medium", False)
    game._refresh_saved_run()
    game.change_state("win")
    assert P.load_progress() is None
    game.change_state("menu")
    assert game.saved_run is None and game.menu.saved_text is None


def test_losing_keeps_the_save_for_the_menu(game):
    P.save_progress("level4", 700, 200.0, "medium", False)
    game._refresh_saved_run()
    game.change_state("lose")
    game.change_state("menu")
    assert game.saved_run["level"] == "level4"
    assert game.menu.saved_text == "Floor 4 - 700 pts"


def test_a_new_game_finds_a_save_from_an_earlier_session():
    P.save_progress("level5", 900, 150.0, "hard", False)
    g = Game()
    assert g.saved_run["level"] == "level5" and g.menu.saved_text == "Floor 5 - 900 pts"


def test_a_continued_run_plays_on_and_a_second_floor_updates_the_save(game):
    P.save_progress("level2", 100, 500.0, "medium", False)
    game._refresh_saved_run()
    press(game, pygame.K_l)
    game._end_briefing()
    game.score.add(50)
    game.level_manager.current.is_complete = lambda: True
    game.update(1 / 60)
    saved = P.load_progress()
    assert saved["level"] == "level3" and saved["score"] == 150


def test_the_menu_shows_the_continue_hint_only_with_a_save():
    pygame.init()
    from ui.menu import MainMenu

    def hint_pixels(text):
        menu = MainMenu()
        menu.saved_text = text
        surf = pygame.Surface((960, 640))
        menu.render(surf)
        rect = menu.layout(960)["hint"].inflate(300, 4)
        return pygame.image.tostring(surf.subsurface(rect), "RGB")

    assert hint_pixels(None) != hint_pixels("Floor 3 - 450 pts")


def test_the_continue_line_stays_inside_the_screen():
    pygame.init()
    from ui.menu import MainMenu
    menu = MainMenu()
    menu.saved_text = "Final Vault - 999999 pts"
    surf = pygame.Surface((960, 640))
    menu.render(surf)
    gold = menu.control_font.render("L: continue (Final Vault - 999999 pts)", True, (1, 1, 1))
    rest = menu.control_font.render("S: settings   |   F11: fullscreen", True, (1, 1, 1))
    assert gold.get_width() + 22 + rest.get_width() < 960 - 40


def test_continuing_applies_the_saved_difficultys_hints_and_penalty(game):
    from core.difficulty import DIFFICULTIES
    P.save_progress("level2", 10, 100.0, "hard", False)
    game._refresh_saved_run()
    press(game, pygame.K_l)
    assert game.hints.enabled == DIFFICULTIES["hard"]["hints_enabled"]
    assert game.security.penalty_multiplier == DIFFICULTIES["hard"]["security_penalty_multiplier"]
