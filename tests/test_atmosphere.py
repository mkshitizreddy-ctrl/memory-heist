"""NovaCorp Lockdown: a cold building that warms and turns WARDEN-red as the player goes deeper."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.game import Game
from core.level_manager import LEVEL_ORDER
from ui.atmosphere import Atmosphere, mood_for

SIZE = (960, 640)
CENTRE = (480, 320)
CORNER = (6, 6)


@pytest.fixture(autouse=True)
def display():
    pygame.init()
    pygame.display.set_mode(SIZE)


def grey(value=160):
    s = pygame.Surface(SIZE)
    s.fill((value, value, value))
    return s


def graded(depth=0.0, alert=0.0, tick=0, value=160):
    s = grey(value)
    Atmosphere(SIZE).apply(s, depth, alert, tick)
    return s


def px(surface, pos):
    return surface.get_at(pos)[:3]


# ---- the grade ------------------------------------------------------------

def test_the_picture_keeps_its_size():
    assert graded().get_size() == SIZE


def test_corners_are_darker_than_the_centre():
    s = graded()

    assert sum(px(s, CORNER)) < sum(px(s, CENTRE))


def test_the_centre_stays_readable():
    # Text lives in the middle: the grade must not crush it.
    for depth, alert in [(0, 0), (1, 1)]:
        s = graded(depth, alert)
        assert sum(px(s, CENTRE)) >= 0.80 * 3 * 160


def test_without_alert_there_is_no_red_cast():
    r, g, b = px(graded(depth=0.0, alert=0.0), CORNER)

    assert r <= b


def test_alert_pushes_the_edges_toward_red():
    calm = px(graded(alert=0.0), CORNER)
    tense = px(graded(alert=1.0, tick=26), CORNER)

    assert tense[0] > calm[0]
    assert tense[0] > tense[2]


def test_more_alert_is_more_red():
    reds = [px(graded(alert=a, tick=26), CORNER)[0] for a in (0.0, 0.3, 0.6, 1.0)]

    assert reds == sorted(reds) and reds[-1] > reds[0]


def test_the_alert_pulses():
    a = px(graded(alert=0.6, tick=0), CORNER)
    b = px(graded(alert=0.6, tick=13), CORNER)

    assert a != b


def test_going_deeper_warms_the_light():
    def warmth(depth):
        r, g, b = px(graded(depth=depth), CENTRE)
        return r / b

    assert warmth(1.0) > warmth(0.0)


def test_out_of_range_values_are_clamped():
    assert pixels_of(graded(depth=5, alert=9, tick=3)) == pixels_of(graded(depth=1, alert=1, tick=3))
    assert pixels_of(graded(depth=-2, alert=-1, tick=3)) == pixels_of(graded(depth=0, alert=0, tick=3))


def pixels_of(surface):
    return pygame.image.tostring(surface, "RGB")


def test_it_works_on_other_window_sizes():
    for size in [(640, 480), (1280, 720)]:
        s = pygame.Surface(size)
        s.fill((120, 120, 120))
        Atmosphere(size).apply(s, 0.5, 0.5, 4)
        assert s.get_size() == size


def test_applying_to_the_wrong_size_rebuilds_instead_of_crashing():
    atmosphere = Atmosphere(SIZE)
    small = pygame.Surface((320, 240))
    atmosphere.apply(small, 0.2, 0.2, 1)

    assert small.get_size() == (320, 240)


# ---- which mood for which screen ----------------------------------------------

def test_menu_intro_ending_and_win_are_calm():
    for state in ["menu", "intro", "outro", "win"]:
        assert mood_for(state, "level5", 90, 100) == (0.0, 0.0), state


def test_losing_is_full_lockdown_at_the_depth_reached():
    depth, alert = mood_for("lose", "level3", 100, 100)

    assert alert == 1.0
    assert depth == mood_for("playing", "level3", 0, 100)[0]


def test_depth_grows_with_every_level_up_to_the_final_vault():
    depths = [mood_for("playing", name, 0, 100)[0] for name in LEVEL_ORDER]

    assert depths == sorted(depths)
    assert depths[0] == 0.0 and depths[-1] == 1.0


def test_alert_follows_the_security_meter():
    low = mood_for("playing", "level2", 10, 100)[1]
    high = mood_for("playing", "level2", 90, 100)[1]

    assert high > low
    assert mood_for("playing", "level2", 100, 100)[1] == 1.0


def test_the_deeper_levels_carry_a_little_alert_even_with_no_mistakes():
    assert mood_for("playing", "level1", 0, 100)[1] == 0.0
    assert mood_for("playing", "final_vault", 0, 100)[1] > 0.0


def test_briefing_cards_use_the_level_mood():
    assert mood_for("briefing", "level4", 30, 100) == mood_for("playing", "level4", 30, 100)


def test_unknown_levels_and_zero_security_max_do_not_crash():
    assert mood_for("playing", "mystery", 50, 0)[0] == 0.0
    mood_for("playing", "level1", 5, 0)


# ---- wired into the game --------------------------------------------------------

@pytest.fixture
def game():
    g = Game()
    g.story_enabled = False
    return g


def test_the_game_has_an_atmosphere(game):
    assert isinstance(game.atmosphere, Atmosphere)


def test_every_screen_gets_the_grade(game, monkeypatch):
    calls = []
    monkeypatch.setattr(game.atmosphere, "apply", lambda *a, **k: calls.append(game.state))
    for state in ["menu", "intro", "briefing", "outro", "win", "lose", "playing"]:
        game.state = state
        if state in ("intro", "briefing", "outro"):
            game.story_screen.begin({"title": "T", "lines": ["x"]})
        if state == "win":
            game.win_screen.begin(100, "Medium", False, None)
        game.render()

    assert calls == ["menu", "intro", "briefing", "outro", "win", "lose", "playing"]


def test_the_hud_is_drawn_after_the_grade(game, monkeypatch):
    order = []
    monkeypatch.setattr(game.atmosphere, "apply", lambda *a, **k: order.append("grade"))
    original = game.hud.render
    monkeypatch.setattr(game.hud, "render", lambda *a, **k: (order.append("hud"), original(*a, **k))[1])
    game.change_state("playing")
    game.render()

    assert order == ["grade", "hud"]


def test_mistakes_make_the_screen_edges_redder(game):
    game.change_state("playing")
    game.render()
    calm = px(game.screen, (4, 600))
    game.security.level = 90
    for _ in range(30):
        game.render()
    tense = px(game.screen, (4, 600))

    assert tense[0] > calm[0]
