"""The 'floor cleared' panel: points, time and mistakes for the floor just finished."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.floor_stats import (MAX_STARS, floor_summary, format_duration, snapshot,
                              stars_for)
from core.game import Game
from core.level_manager import LEVEL_ORDER
from ui import theme
from ui.story_screens import StoryScreen


def press(game, key, char=""):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=char))
    game.handle_events()


def close_card(game):
    press(game, pygame.K_SPACE, " ")
    press(game, pygame.K_SPACE, " ")


def finish_level(game):
    game.level_manager.current.is_complete = lambda: True
    game.update(0.016)


@pytest.fixture
def game():
    g = Game()
    g.music.stop()
    press(g, pygame.K_RETURN)
    press(g, pygame.K_ESCAPE)          # skip the intro: straight into Level 1
    assert g.state == "playing"
    return g


# --- pure helpers --------------------------------------------------------
@pytest.mark.parametrize("mistakes, stars", [(0, 3), (1, 2), (2, 1), (9, 1), (-1, 3)])
def test_stars_depend_on_mistakes(mistakes, stars):
    assert stars_for(mistakes) == stars
    assert 1 <= stars_for(mistakes) <= MAX_STARS


def test_summary_is_the_difference_between_two_snapshots():
    start = snapshot(100, 800, 1)
    end = snapshot(450, 716.4, 3)
    info = floor_summary("level2", start, end)
    assert info == {"name": "level2", "points": 350, "seconds": 84,
                    "mistakes": 2, "stars": 1}


def test_summary_never_reports_negative_time_or_mistakes():
    info = floor_summary("level1", snapshot(0, 100, 5), snapshot(0, 120, 2))
    assert info["seconds"] == 0 and info["mistakes"] == 0 and info["stars"] == 3


def test_points_may_be_negative_if_penalties_outweigh_gains():
    assert floor_summary("level1", snapshot(100, 50, 0), snapshot(60, 40, 1))["points"] == -40


def test_summary_without_a_start_snapshot_is_none():
    assert floor_summary("level1", None, snapshot(0, 0, 0)) is None


@pytest.mark.parametrize("secs, text", [(0, "0:00"), (59, "0:59"), (84, "1:24"), (3600, "60:00"), (-5, "0:00")])
def test_format_duration(secs, text):
    assert format_duration(secs) == text


# --- security mistakes counter ------------------------------------------
def test_every_security_increase_counts_as_a_mistake_and_reset_clears_it(game):
    assert game.security.mistakes == 0
    game.security.increase(10)
    game.security.increase(10)
    assert game.security.mistakes == 2
    game.security.reset()
    assert game.security.mistakes == 0


def test_a_new_run_starts_the_mistake_count_at_zero(game):
    game.security.increase(10)
    game._start_new_run()
    assert game.security.mistakes == 0


# --- in the game ---------------------------------------------------------
def test_the_first_briefing_has_no_cleared_panel():
    g = Game()
    g.music.stop()
    press(g, pygame.K_RETURN)
    close_card(g)                                   # intro -> level 1 briefing
    assert g.state == "briefing"
    assert g.story_screen.cleared is None


def test_finishing_a_level_hands_its_result_to_the_next_briefing(game):
    game.score.add(300)
    game.security.increase(20)
    game.timer.update(75)
    finish_level(game)
    assert game.state == "briefing"
    info = game.story_screen.cleared
    assert info["name"] == "level1"
    assert info["points"] == 300 and info["mistakes"] == 1 and info["stars"] == 2
    assert info["seconds"] == 75


def test_each_floor_is_measured_from_its_own_start(game):
    game.score.add(300)
    finish_level(game)
    close_card(game)
    game.score.add(120)
    game.timer.update(40)
    finish_level(game)
    info = game.story_screen.cleared
    assert info["name"] == "level2"
    assert info["points"] == 120 and info["mistakes"] == 0 and info["seconds"] == 40


def test_time_on_the_briefing_card_is_not_counted_against_the_floor(game):
    finish_level(game)
    for _ in range(120):
        game.update(0.05)                           # a long time reading the card
    close_card(game)
    game.timer.update(10)
    finish_level(game)
    assert game.story_screen.cleared["seconds"] == 10


def test_skipping_a_card_with_escape_still_keeps_the_floor_stats_straight(game):
    finish_level(game)
    press(game, pygame.K_ESCAPE)
    assert game.state == "playing"
    game.score.add(77)
    finish_level(game)
    assert game.story_screen.cleared["points"] == 77


def test_the_ending_card_shows_the_final_vault_result(game):
    for _ in LEVEL_ORDER[:-1]:
        finish_level(game)
        close_card(game)
    game.score.add(500)
    game.security.increase(10)
    finish_level(game)
    assert game.state == "outro"
    info = game.story_screen.cleared
    assert info["name"] == "final_vault"
    assert info["points"] == 500 and info["mistakes"] == 1


def test_no_summary_when_levels_are_switched_by_hand_out_of_order(game):
    game.level_manager.start("level4")              # skips ahead, nothing was cleared
    game.update(0.016)
    assert game.story_screen.cleared is None


def test_a_story_free_run_still_tracks_stats_without_crashing(game):
    game.story_enabled = False
    finish_level(game)
    assert game.state == "playing"
    game.score.add(5)
    game.render()


def test_a_new_run_does_not_carry_stats_over(game):
    game.score.add(900)
    finish_level(game)
    game._start_new_run()
    game.score.add(10)
    close_card(game) if game.state == "briefing" else None
    finish_level(game)
    assert game.story_screen.cleared["points"] == 10


# --- the panel itself ----------------------------------------------------
@pytest.fixture
def card():
    pygame.init()
    return StoryScreen(), pygame.Surface((960, 640))


def summary(**kw):
    base = {"name": "level1", "points": 250, "seconds": 90, "mistakes": 0, "stars": 3}
    base.update(kw)
    return base


def beat():
    return {"title": "LEVEL 2", "lines": ["x"], "concept": "Operators"}


def gold_pixels(surface, rect):
    area = surface.subsurface(rect)
    return sum(1 for x in range(area.get_width()) for y in range(area.get_height())
               if area.get_at((x, y))[:3] == theme.GOLD)


def test_panel_is_drawn_only_when_there_is_a_result(card):
    screen, surf = card
    screen.begin(beat(), progress=(1, 6))
    screen.render(surf)
    without = pygame.image.tostring(surf.subsurface(screen.CLEARED_RECT), "RGB")
    screen.begin(beat(), progress=(1, 6), cleared=summary())
    screen.render(surf)
    assert pygame.image.tostring(surf.subsurface(screen.CLEARED_RECT), "RGB") != without


def test_begin_without_a_result_clears_the_old_one(card):
    screen, _ = card
    screen.begin(beat(), cleared=summary())
    screen.begin(beat())
    assert screen.cleared is None


def test_more_stars_means_more_gold(card):
    screen, surf = card
    counts = []
    for stars in (1, 2, 3):
        screen.begin(beat(), cleared=summary(stars=stars, mistakes=3 - stars))
        screen.render(surf)
        counts.append(gold_pixels(surf, screen.CLEARED_RECT))
    assert counts[0] < counts[1] < counts[2]


def test_panel_border_takes_the_cleared_floors_accent(card):
    screen, surf = card
    r = screen.CLEARED_RECT
    edge = {}
    for name in ("level1", "level2", "level3"):
        screen.begin(beat(), cleared=summary(name=name))
        screen.render(surf)
        edge[name] = max((surf.get_at((x, y))[:3] for x in (r.x, r.x + 1) for y in range(r.y + 30, r.y + 100)),
                         key=sum)
    assert len(set(edge.values())) == 3
    assert edge["level1"][2] > edge["level1"][0]        # blue floor
    assert edge["level2"][0] > edge["level2"][2]        # orange floor
    assert edge["level3"][1] > edge["level3"][0]        # green floor


def test_stat_text_values_and_colours(card):
    screen, surf = card
    seen = []

    class Rec:
        def __init__(self, f): self.f = f
        def render(self, t, aa, colour, *a, **k):
            seen.append((t, colour))
            return self.f.render(t, aa, colour, *a, **k)

    screen.stat_font = Rec(screen.stat_font)
    screen.begin(beat(), cleared=summary(points=-20, seconds=125, mistakes=2, stars=1))
    screen.render(surf)
    assert ("-20", theme.SKY) in seen
    assert ("2:05", theme.GOLD) in seen
    assert ("2", theme.CORAL) in seen
    seen.clear()
    screen.begin(beat(), cleared=summary(mistakes=0))
    screen.render(surf)
    assert ("0", theme.TEAL) in seen and ("+250", theme.SKY) in seen


def test_panel_does_not_overlap_the_body_text_or_hero(card):
    screen, _ = card
    r = screen.CLEARED_RECT
    assert r.bottom < 270                               # body text starts at y=270
    assert r.right < 312                                # co-op Ghost portrait starts at x=312


def test_star_points_make_a_ten_point_star_around_the_centre():
    pts = StoryScreen.star_points((100, 100), 20)
    assert len(pts) == 10
    assert pts[0] == pytest.approx((100, 80))           # top point straight up
    assert min(p[1] for p in pts) == pytest.approx(80)
