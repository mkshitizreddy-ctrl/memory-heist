"""Badges and stats in the game: earned on a win, shown on the win screen, listed on B."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.game import Game
from systems.achievements import BADGE_IDS, BADGES, Stats
from ui import stats_screen as SS
from ui.screens import WinScreen
from ui.stats_screen import StatsScreen, star_points, stat_values


@pytest.fixture
def game():
    g = Game()
    g.running = True
    return g


def press(game, key):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, unicode="", mod=0, scancode=0))
    game.handle_events()


def start_run(game, difficulty="hard", coop=True):
    game.menu.selected_difficulty = difficulty
    game.menu.coop = coop
    from core.difficulty import get_difficulty
    game.difficulty = get_difficulty(difficulty)
    game.coop = coop
    game._start_new_run()


# --- game wiring ---------------------------------------------------------------
def test_a_clean_fast_win_earns_the_badges_and_marks_them_new(game):
    start_run(game)
    game.change_state("win")
    ids = [b for b, _ in game.win_screen.badges]
    assert ids == ["escape", "flawless", "speed", "duo", "nerves"]
    assert all(is_new for _, is_new in game.win_screen.badges)
    assert game.stats.wins == 1 and Stats().wins == 1


def test_a_second_win_shows_old_badges_as_not_new(game):
    start_run(game)
    game.change_state("win")
    start_run(game)
    game.change_state("win")
    assert game.win_screen.badges and not any(is_new for _, is_new in game.win_screen.badges)


def test_mistakes_cost_the_flawless_badge(game):
    start_run(game, "medium", False)
    game.security.increase(10)
    game.change_state("win")
    assert "flawless" not in [b for b, _ in game.win_screen.badges]


def test_a_continued_run_is_not_flawless(game):
    from systems import progress as P
    P.save_progress("level3", 100, 800.0, "medium", False)
    game._refresh_saved_run()
    press(game, pygame.K_l)
    game.change_state("win")
    ids = [b for b, _ in game.win_screen.badges]
    assert "flawless" not in ids and "speed" not in ids and "escape" in ids


def test_a_fresh_run_after_a_continue_can_be_flawless_again(game):
    from systems import progress as P
    P.save_progress("level3", 100, 800.0, "medium", False)
    game._refresh_saved_run()
    press(game, pygame.K_l)
    start_run(game, "medium", False)
    game.change_state("win")
    assert "flawless" in [b for b, _ in game.win_screen.badges]


def test_losing_counts_once_per_loss(game):
    game.change_state("lose")
    game.change_state("lose")
    assert game.stats.losses == 1
    game.change_state("menu")
    game.change_state("lose")
    assert game.stats.losses == 2


def test_b_opens_the_stats_page_from_the_menu_and_esc_returns(game):
    press(game, pygame.K_b)
    assert game.state == "stats"
    game.render()
    press(game, pygame.K_ESCAPE)
    assert game.state == "menu" and game.running


def test_b_does_nothing_outside_the_menu(game):
    game._start_new_run()
    press(game, pygame.K_b)
    assert game.state == "playing"


def test_the_menu_hint_mentions_badges():
    pygame.init()
    from ui.menu import MainMenu
    menu = MainMenu()
    menu.saved_text = "Final Vault - 999999 pts"
    gold = menu.control_font.size("L: continue (Final Vault - 999999 pts)")[0]
    rest = menu.control_font.size("S: settings  |  B: badges  |  F11: fullscreen")[0]
    assert gold + 22 + rest < 960 - 40


# --- stats screen --------------------------------------------------------------
def test_stat_values_format_the_four_numbers(tmp_path):
    s = Stats(str(tmp_path / "s.json"))
    assert stat_values(s) == [("WINS", "0"), ("LOSSES", "0"), ("BEST SCORE", "0"),
                              ("BEST TIME LEFT", "--:--")]
    s.wins, s.losses, s.best_score, s.best_time_left = 4, 2, 1234, 605
    assert stat_values(s) == [("WINS", "4"), ("LOSSES", "2"), ("BEST SCORE", "1234"),
                              ("BEST TIME LEFT", "10:05")]


def test_star_points_are_a_ten_corner_star_pointing_up():
    pts = star_points((100, 100), 20)
    assert len(pts) == 10
    assert pts[0] == pytest.approx((100, 80))                 # top point
    outer = [pts[i] for i in range(0, 10, 2)]
    inner = [pts[i] for i in range(1, 10, 2)]
    dist = lambda p: ((p[0] - 100) ** 2 + (p[1] - 100) ** 2) ** 0.5
    assert all(dist(p) == pytest.approx(20) for p in outer)
    assert all(dist(p) == pytest.approx(9) for p in inner)


def test_the_stats_layout_keeps_every_cell_inside_the_panel_without_overlap():
    lay = StatsScreen().layout(960)
    assert len(lay["cells"]) == len(BADGES) and len(lay["slots"]) == 4
    for rect in lay["cells"] + lay["slots"] + [lay["back"]]:
        assert lay["panel"].contains(rect)
    cells = lay["cells"]
    for i, a in enumerate(cells):
        assert not any(a.colliderect(b) for b in cells[i + 1:])
    assert all(c.bottom < lay["back"].top for c in cells)
    assert lay["panel"].bottom <= 640


def test_earned_badges_look_different_from_locked_ones(tmp_path):
    pygame.init()
    screen = StatsScreen()
    locked, earned = Stats(str(tmp_path / "a.json")), Stats(str(tmp_path / "b.json"))
    earned.badges = list(BADGE_IDS)
    a, b = pygame.Surface((960, 640)), pygame.Surface((960, 640))
    screen.render(a, locked, 5)
    screen.render(b, earned, 5)
    cell = screen.layout(960)["cells"][0]
    assert pygame.image.tostring(a.subsurface(cell), "RGB") != pygame.image.tostring(b.subsurface(cell), "RGB")


def test_each_badge_cell_changes_only_when_its_own_badge_is_earned(tmp_path):
    pygame.init()
    screen = StatsScreen()
    base = Stats(str(tmp_path / "a.json"))
    one = Stats(str(tmp_path / "b.json"))
    one.badges = ["duo"]
    a, b = pygame.Surface((960, 640)), pygame.Surface((960, 640))
    screen.render(a, base, 5)
    screen.render(b, one, 5)
    cells = screen.layout(960)["cells"]
    index = BADGE_IDS.index("duo")
    for i, cell in enumerate(cells):
        same = pygame.image.tostring(a.subsurface(cell), "RGB") == pygame.image.tostring(b.subsurface(cell), "RGB")
        assert same == (i != index)


# --- win screen strip -------------------------------------------------------------
class Board:
    def top(self, n):
        return []

    def add(self, *args):
        return 1


def test_the_badge_strip_sits_between_the_table_and_the_prompt():
    lay = WinScreen(Board()).layout(960)
    assert lay["badges"].top > lay["table"].bottom
    assert lay["badges"].bottom < 640 - 50 - 14


def test_the_win_screen_draws_badge_chips_only_when_there_are_some():
    pygame.init()
    win = WinScreen(Board())
    strip = win.layout(960)["badges"]
    shots = []
    for badges in (None, [("escape", True), ("flawless", False)]):
        win.begin(100, "Medium", False, None, badges=badges)
        win.skip_entry()
        win.tick = 10
        surf = pygame.Surface((960, 640))
        win.render(surf, 100)
        shots.append(pygame.image.tostring(surf.subsurface(strip), "RGB"))
    assert shots[0] != shots[1]


def test_all_six_badges_fit_across_the_screen():
    pygame.init()
    win = WinScreen(Board())
    total = 0
    for badge_id, name, _ in BADGES:
        total += win.badge_font.size("NEW " + name)[0] + 28 + 8
    assert total < win.layout(960)["badges"].width


def test_begin_without_badges_clears_the_old_ones():
    win = WinScreen(Board())
    win.begin(1, "Medium", False, None, badges=[("escape", True)])
    win.begin(1, "Medium", False)
    assert win.badges == []
