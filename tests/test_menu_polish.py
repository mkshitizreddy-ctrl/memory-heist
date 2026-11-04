"""Menu polish: difficulty summary, animated title, bobbing heroes, smooth Echo fade."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.difficulty import DIFFICULTIES
from ui import menu as M
from ui import theme
from ui.menu import MainMenu

SIZE = (960, 640)


@pytest.fixture(autouse=True)
def init():
    pygame.init()


@pytest.fixture
def surf():
    return pygame.Surface(SIZE)


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


def pixels(surface, rect, step=2):
    return [tuple(surface.get_at((x, y)))[:3] for x in range(rect.left, rect.right, step)
            for y in range(rect.top, rect.bottom, step)]


# --- pure helpers ---------------------------------------------------------------
def test_approach_moves_by_one_step_and_never_overshoots():
    assert M.approach(70, 255, 12) == 82
    assert M.approach(250, 255, 12) == 255
    assert M.approach(255, 70, 12) == 243
    assert M.approach(75, 70, 12) == 70
    assert M.approach(100, 100, 12) == 100


def test_the_title_glow_stays_between_zero_and_one_and_repeats():
    values = [M.title_glow(t) for t in range(0, 400)]
    assert all(0.0 <= v <= 1.0 for v in values)
    assert min(values) < 0.1 and max(values) > 0.9
    assert M.title_glow(10) == M.title_glow(10)


def test_the_shimmer_sweeps_for_a_short_burst_then_rests():
    assert M.shimmer_progress(0) == 0.0
    assert M.shimmer_progress(M.SHIMMER_SWEEP - 1) == 1.0
    assert 0.0 < M.shimmer_progress(M.SHIMMER_SWEEP // 2) < 1.0
    assert M.shimmer_progress(M.SHIMMER_SWEEP) is None
    assert M.shimmer_progress(M.SHIMMER_PERIOD - 1) is None
    assert M.shimmer_progress(M.SHIMMER_PERIOD) == 0.0
    assert M.shimmer_progress(M.SHIMMER_PERIOD * 3 + 5) == M.shimmer_progress(5)
    steps = [M.shimmer_progress(t) for t in range(M.SHIMMER_SWEEP)]
    assert steps == sorted(steps)


def test_bob_is_small_periodic_and_differs_by_phase():
    values = [M.bob(t, 0.0) for t in range(0, 300)]
    assert min(values) == -3 and max(values) == 3
    assert all(isinstance(v, int) for v in values)
    assert [M.bob(t, 0.0) for t in range(40)] != [M.bob(t, 2.0) for t in range(40)]
    assert M.bob(0, 0.0, amplitude=0) == 0


@pytest.mark.parametrize("name", ["easy", "medium", "hard"])
def test_the_difficulty_summary_states_the_real_numbers(name):
    d = DIFFICULTIES[name]
    text = M.difficulty_blurb(name)
    assert f"timer x{d['timer_multiplier']:g}" in text
    assert f"security x{d['security_penalty_multiplier']:g}" in text
    assert f"score x{d['score_multiplier']:g}" in text
    assert ("hints on" in text) == d["hints_enabled"] and ("hints off" in text) != d["hints_enabled"]


def test_an_unknown_difficulty_is_summarised_as_medium():
    assert M.difficulty_blurb("nightmare") == M.difficulty_blurb("medium")


def test_the_three_summaries_are_all_different():
    assert len({M.difficulty_blurb(n) for n in ("easy", "medium", "hard")}) == 3


# --- layout ------------------------------------------------------------------------
def test_the_summary_sits_between_the_chips_and_the_co_op_chip_and_fits():
    lay = MainMenu().layout()
    blurb = lay["blurb"]
    assert blurb.top >= lay["chips"][0].bottom and blurb.bottom <= lay["coop"].top
    blocks = [lay["panel"], *lay["chips"], blurb, lay["coop"], lay["start"], lay["hint"]]
    screen = pygame.Rect(0, 0, *SIZE)
    assert all(screen.contains(b) for b in blocks)
    for i, a in enumerate(blocks):
        assert all(not a.colliderect(b) for b in blocks[i + 1:])
    menu = MainMenu()
    for name in ("easy", "medium", "hard"):
        assert menu.small_font.size(M.difficulty_blurb(name))[0] <= blurb.width


# --- behaviour ---------------------------------------------------------------------
def test_the_summary_on_screen_follows_the_chosen_difficulty(surf):
    menu = MainMenu()
    area = menu.layout()["blurb"]
    shots = {}
    for name, k in (("easy", pygame.K_1), ("medium", pygame.K_2), ("hard", pygame.K_3)):
        menu.handle_event(key(k))
        menu.render(surf)
        shots[name] = pixels(surf, area)
    assert shots["easy"] != shots["medium"] != shots["hard"] and shots["easy"] != shots["hard"]
    assert len(set(shots["hard"])) > 3                                           # real text, not an empty strip


def test_echo_fades_in_over_several_frames_and_back_out(surf):
    menu = MainMenu()
    assert menu.echo_alpha == M.ECHO_DIM
    menu.handle_event(key(pygame.K_c))
    menu.render(surf)
    assert M.ECHO_DIM < menu.echo_alpha < M.ECHO_FULL
    for _ in range(40):
        menu.render(surf)
    assert menu.echo_alpha == M.ECHO_FULL
    menu.handle_event(key(pygame.K_c))
    menu.render(surf)
    assert M.ECHO_DIM < menu.echo_alpha < M.ECHO_FULL
    for _ in range(40):
        menu.render(surf)
    assert menu.echo_alpha == M.ECHO_DIM


def test_changing_difficulty_flashes_the_chip_briefly(surf):
    menu = MainMenu()
    chip = menu.layout()["chips"][2]
    menu.render(surf)
    calm = surf.get_at((chip.x + 14, chip.centery))[:3]
    menu.handle_event(key(pygame.K_3))
    assert menu._flash == M.FLASH_TICKS
    menu.render(surf)
    flashing = surf.get_at((chip.x + 14, chip.centery))[:3]
    assert flashing != theme.CORAL
    for _ in range(M.FLASH_TICKS + 2):
        menu.render(surf)
    assert menu._flash == 0 and surf.get_at((chip.x + 14, chip.centery))[:3] == theme.CORAL
    assert calm != theme.CORAL


def test_pressing_the_same_difficulty_again_does_not_flash():
    menu = MainMenu()
    menu.handle_event(key(pygame.K_2))
    assert menu._flash == 0


def test_the_glow_peaks_and_dips_at_the_expected_beat():
    assert M.title_glow(0) == 0.5
    assert M.title_glow(10) > M.title_glow(0)
    assert M.title_glow(31) > 0.99
    assert M.title_glow(94) < 0.01


def test_the_title_shimmers_only_during_the_sweep(surf, monkeypatch):
    monkeypatch.setattr(M, "title_glow", lambda tick: 0.0)                 # isolate the shimmer from the glow
    monkeypatch.setattr(M, "draw_backdrop", lambda surface, tick, tint=None: surface.fill((9, 12, 30)))
    title = pygame.Rect(300, 40, 360, 60)

    def title_pixels(tick):
        menu = MainMenu()
        menu.tick = tick - 1
        menu.render(surf)
        return pixels(surf, title)
    during = title_pixels(M.SHIMMER_SWEEP // 2)
    resting = title_pixels(M.SHIMMER_SWEEP + 40)
    assert during != resting
    assert resting == title_pixels(M.SHIMMER_SWEEP + 41)                   # nothing else on the title moves


def test_the_title_glow_changes_the_title_pixels(surf, monkeypatch):
    title = pygame.Rect(300, 40, 360, 60)
    seen = []
    for value in (0.0, 1.0):
        monkeypatch.setattr(M, "title_glow", lambda tick, v=value: v)
        menu = MainMenu()
        menu.tick = M.SHIMMER_SWEEP + 10
        menu.render(surf)
        seen.append(pixels(surf, title))
    assert seen[0] != seen[1]


def test_the_heroes_bob_without_leaving_their_slots(surf, monkeypatch):
    block = pygame.Surface((M.PORTRAIT_SIZE, M.PORTRAIT_SIZE), pygame.SRCALPHA)
    block.fill((200, 50, 50, 255))
    monkeypatch.setattr(M, "make_portrait", lambda *a, **k: block)          # a still picture: only the bob can move it
    menu = MainMenu()
    menu.coop = True
    menu.echo_alpha = M.ECHO_FULL
    for slot in menu.layout()["heroes"]:
        area = slot.inflate(0, 14)
        shots = []
        for tick in (0, 26):
            menu.tick = tick - 1
            menu.render(surf)
            shots.append(pixels(surf, area, step=1))
        assert shots[0] != shots[1]
        red = [(x, y) for x in range(area.left, area.right) for y in range(area.top, area.bottom)
               if surf.get_at((x, y))[:3] == (200, 50, 50)]
        assert red and all(area.collidepoint(p) for p in red)
    ghost, echo = menu.layout()["heroes"]
    menu.tick = 25
    menu.render(surf)
    ghost_top = min(y for x in range(ghost.left, ghost.right) for y in range(ghost.top - 8, ghost.bottom + 8)
                    if surf.get_at((x, y))[:3] == (200, 50, 50))
    echo_top = min(y for x in range(echo.left, echo.right) for y in range(echo.top - 8, echo.bottom + 8)
                   if surf.get_at((x, y))[:3] == (200, 50, 50))
    assert (ghost_top - ghost.top) != (echo_top - echo.top)                 # the two do not bob in step


def test_the_menu_still_renders_every_state_without_error(surf):
    menu = MainMenu()
    for k in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_c, pygame.K_c):
        menu.handle_event(key(k))
        for _ in range(3):
            menu.render(surf)
