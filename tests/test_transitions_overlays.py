"""Elevator wipe between floors and the restyled pause overlay."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.game import FADE_DURATION, Game
from ui import theme
from ui.overlays import PauseOverlay
from ui.transitions import SEAM, ElevatorWipe, door_edges, label_alpha

SIZE = (960, 640)


@pytest.fixture(autouse=True)
def init():
    pygame.init()


@pytest.fixture
def surf():
    s = pygame.Surface(SIZE)
    s.fill((1, 2, 3))
    return s


# --- pure helpers --------------------------------------------------------
def test_doors_meet_in_the_middle_when_shut_and_reach_the_edges_when_open():
    assert door_edges(960, 1.0) == (480, 480)
    assert door_edges(960, 0.0) == (0, 960)


def test_doors_open_monotonically():
    prev = door_edges(960, 1.0)
    for i in range(19, -1, -1):
        cur = door_edges(960, i / 20)
        assert cur[0] <= prev[0] and cur[1] >= prev[1]
        prev = cur


def test_door_edges_clamp_out_of_range_progress():
    assert door_edges(960, 5) == (480, 480)
    assert door_edges(960, -3) == (0, 960)


def test_label_alpha_fades_out_as_doors_open():
    assert label_alpha(1.0) == 255
    assert label_alpha(0.75) == 255
    assert 0 < label_alpha(0.5) < 255
    assert label_alpha(0.25) == 0 and label_alpha(0.0) == 0


# --- wipe ----------------------------------------------------------------
def test_open_doors_draw_nothing(surf):
    before = pygame.image.tostring(surf, "RGB")
    ElevatorWipe().draw(surf, 0.0, "level1")
    assert pygame.image.tostring(surf, "RGB") == before


def test_shut_doors_cover_the_whole_screen(surf):
    ElevatorWipe().draw(surf, 1.0, "level2")
    for x in (3, 200, 477, 482, 700, 957):
        assert surf.get_at((x, 20))[:3] != (1, 2, 3)
        assert surf.get_at((x, 620))[:3] != (1, 2, 3)


def test_half_open_shows_a_gap_in_the_middle_with_doors_at_the_sides(surf):
    ElevatorWipe().draw(surf, 0.5, "level1")
    assert surf.get_at((480, 20))[:3] == (1, 2, 3)
    assert surf.get_at((2, 20))[:3] != (1, 2, 3)
    assert surf.get_at((957, 20))[:3] != (1, 2, 3)


def test_door_edge_strip_uses_the_floor_accent(surf):
    ElevatorWipe().draw(surf, 1.0, "level3")
    assert surf.get_at((480 - SEAM // 2, 20))[:3] == theme.floor_palette("level3")["accent"]


def test_floors_have_different_doors():
    a, b = pygame.Surface(SIZE), pygame.Surface(SIZE)
    ElevatorWipe().draw(a, 1.0, "level1")
    ElevatorWipe().draw(b, 1.0, "level5")
    assert pygame.image.tostring(a, "RGB") != pygame.image.tostring(b, "RGB")


def test_floor_name_plate_shows_only_while_mostly_shut():
    w = ElevatorWipe()
    shut, open_ = pygame.Surface(SIZE), pygame.Surface(SIZE)
    w.draw(shut, 1.0, "level4")
    w.draw(open_, 0.2, "level4")
    plate = pygame.Rect(330, 270, 300, 100)
    assert pygame.image.tostring(shut.subsurface(plate), "RGB") != \
        pygame.image.tostring(open_.subsurface(plate), "RGB")
    plain = pygame.Surface(SIZE)
    w.draw(plain, 0.5, "level4")
    centre_a = pygame.image.tostring(plain.subsurface(plate), "RGB")
    plain2 = pygame.Surface(SIZE)
    w.draw(plain2, 0.5, "level4")
    assert centre_a == pygame.image.tostring(plain2.subsurface(plate), "RGB")   # deterministic


def test_unknown_level_still_draws(surf):
    ElevatorWipe().draw(surf, 0.8, "mystery")


# --- pause overlay -------------------------------------------------------
def test_pause_layout_fits_and_stats_sit_inside_the_panel():
    o = PauseOverlay(SIZE)
    screen = pygame.Rect(0, 0, *SIZE)
    assert screen.contains(o.panel) and o.panel.center == (480, 320)
    for slot in o.stat_slots():
        assert o.panel.contains(slot)
    slots = o.stat_slots()
    for i in range(2):
        assert not slots[i].colliderect(slots[i + 1])
    chip = o.resume_chip()
    assert o.panel.contains(chip)
    assert all(not chip.colliderect(s) for s in slots)


def test_pause_dims_the_game_behind_it(surf):
    surf.fill((200, 200, 200))
    PauseOverlay(SIZE).draw(surf, "level1")
    assert surf.get_at((5, 5))[0] < 100


def test_pause_border_uses_the_floor_accent(surf):
    o = PauseOverlay(SIZE)
    o.draw(surf, "level2")
    assert surf.get_at((o.panel.x + 1, o.panel.centery))[:3] == theme.floor_palette("level2")["accent"]


def test_pause_shows_dashes_when_there_is_no_timer():
    seen = []

    class Rec:
        def __init__(self, f): self.f = f
        def render(self, t, *a, **k):
            seen.append(t)
            return self.f.render(t, *a, **k)

    o = PauseOverlay(SIZE)
    o.value_font = Rec(o.value_font)
    o.draw(pygame.Surface(SIZE), "level1", score=40, security=10, security_max=100, remaining=None)
    assert "--:--" in seen and "40" in seen and "10/100" in seen
    seen.clear()
    o.draw(pygame.Surface(SIZE), "level1", remaining=61)
    assert "1:01" in seen


def test_pause_security_turns_red_in_danger():
    o = PauseOverlay(SIZE)
    slot = o.stat_slots()[1]
    def has_colour(security, colour):
        s = pygame.Surface(SIZE)
        o.draw(s, "level1", security=security, security_max=100)
        area = s.subsurface(slot)
        return any(area.get_at((x, y))[:3] == colour
                   for x in range(area.get_width()) for y in range(area.get_height()))
    assert has_colour(90, theme.CORAL) and not has_colour(10, theme.CORAL)
    assert has_colour(10, theme.TEAL)


def test_pause_does_not_create_fonts_while_drawing(monkeypatch):
    o = PauseOverlay(SIZE)
    s = pygame.Surface(SIZE)
    o.draw(s, "level1")
    calls = []
    real = pygame.font.Font
    monkeypatch.setattr(pygame.font, "Font", lambda *a, **k: (calls.append(a), real(*a, **k))[1])
    o.draw(s, "level1")
    o.draw(s, "level1")
    assert calls == []


# --- in the real game ----------------------------------------------------
@pytest.fixture
def game():
    g = Game()
    g._start_new_run()
    g.music.stop()
    return g


def test_fade_duration_is_long_enough_to_see_the_doors():
    assert 0.5 <= FADE_DURATION <= 1.2


def test_level_change_shows_the_elevator_doors(game):
    game.story_enabled = False
    game.state = "playing"
    game._fade_timer = FADE_DURATION
    game.render()
    name = game.level_manager.current_name
    accent = theme.floor_palette(name)["accent"]
    assert game.screen.get_at((480 - SEAM // 2, 20))[:3] == accent


def test_no_doors_when_no_transition(game):
    game.story_enabled = False
    game.state = "playing"
    game._fade_timer = 0.0
    game.render()
    accent = theme.floor_palette(game.level_manager.current_name)["accent"]
    assert game.screen.get_at((480 - SEAM // 2, 20))[:3] != accent


def test_pause_in_the_real_game_draws_the_panel(game):
    game.story_enabled = False
    game.state = "playing"
    game._fade_timer = 0.0
    game.paused = True
    game.render()
    o = game._get_pause_assets()
    assert game.screen.get_at((o.panel.x + 1, o.panel.centery))[:3] == \
        theme.floor_palette(game.level_manager.current_name)["accent"]
    game.paused = False
    game.render()
    assert game.screen.get_at((o.panel.x + 1, o.panel.centery))[:3] != \
        theme.floor_palette(game.level_manager.current_name)["accent"]
