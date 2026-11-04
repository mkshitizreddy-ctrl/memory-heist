"""Floating +/- popups beside the score and the security meter."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from ui import hud as H
from ui import theme
from ui.hud import HUD


@pytest.fixture(autouse=True)
def init():
    pygame.init()


@pytest.fixture
def surf():
    return pygame.Surface((960, 640))


def frame(hud, surf, score=0, security=0, tick=0):
    surf.fill((0, 0, 0))
    hud.render(surf, "level1", score=score, security_level=security, security_max=100,
               timer_remaining=600, coop=False, tick=tick)


def texts(hud):
    return [(p["text"], p["colour"]) for p in hud.popups]


# --- pure helpers -------------------------------------------------------------
def test_delta_labels_carry_an_explicit_sign():
    assert H.delta_label(50) == "+50"
    assert H.delta_label(-10) == "-10"
    assert H.delta_label(0) == "+0"


def test_a_popup_rises_and_fades_over_its_life():
    first = H.popup_state(0)
    last = H.popup_state(H.POPUP_LIFE - 1)
    assert first == (0, 255)
    assert last[0] > first[0] and last[1] < 60
    rises = [H.popup_state(a)[0] for a in range(H.POPUP_LIFE)]
    fades = [H.popup_state(a)[1] for a in range(H.POPUP_LIFE)]
    assert rises == sorted(rises) and fades == sorted(fades, reverse=True)
    assert H.popup_state(H.POPUP_LIFE)[1] == 0 and H.popup_state(H.POPUP_LIFE + 50)[1] == 0


# --- what makes a popup ---------------------------------------------------------------
def test_the_first_frame_never_pops_up(surf):
    hud = HUD()
    frame(hud, surf, score=380, security=40)
    assert hud.popups == []


def test_points_gained_pop_up_in_gold_and_points_lost_in_coral(surf):
    hud = HUD()
    frame(hud, surf, score=100)
    frame(hud, surf, score=150)
    assert texts(hud) == [("+50", theme.GOLD)]
    frame(hud, surf, score=140)
    assert texts(hud)[-1] == ("-10", theme.CORAL)


def test_a_security_rise_pops_up_but_a_fall_does_not(surf):
    hud = HUD()
    frame(hud, surf, security=10)
    frame(hud, surf, security=30)
    assert texts(hud) == [("+20", theme.CORAL)] and hud.popups[0]["kind"] == "security"
    frame(hud, surf, security=0)
    assert len(hud.popups) == 1


def test_a_huge_jump_such_as_a_run_reset_is_ignored(surf):
    hud = HUD()
    frame(hud, surf, score=900, security=90)
    frame(hud, surf, score=0, security=0)
    assert hud.popups == []
    frame(hud, surf, score=500)
    assert hud.popups == []


def test_an_unchanged_value_adds_nothing(surf):
    hud = HUD()
    for _ in range(5):
        frame(hud, surf, score=100, security=20)
    assert hud.popups == []


def test_popups_age_out_and_are_capped(surf):
    hud = HUD()
    frame(hud, surf, score=0)
    for i in range(1, 10):
        frame(hud, surf, score=i * 10)
    assert len(hud.popups) == H.MAX_POPUPS
    for _ in range(H.POPUP_LIFE + 1):
        frame(hud, surf, score=90)
    assert hud.popups == []


def test_each_popup_keeps_its_own_age(surf):
    hud = HUD()
    frame(hud, surf, score=0)
    frame(hud, surf, score=10)
    for _ in range(10):
        frame(hud, surf, score=10)
    frame(hud, surf, score=30)
    ages = sorted(p["age"] for p in hud.popups)
    assert len(ages) == 2 and ages[0] < ages[1]


# --- drawing -----------------------------------------------------------------------------
def region(surface, rect):
    return [tuple(surface.get_at((x, y)))[:3] for x in range(rect.left, rect.right, 2)
            for y in range(rect.top, rect.bottom, 2)]


def test_a_score_popup_is_drawn_to_the_right_of_the_score_and_fades_out(surf):
    hud = HUD()
    area = pygame.Rect(262, 2, 90, 44)
    frame(hud, surf, score=100)
    calm = region(surf, area)
    frame(hud, surf, score=150)
    assert region(surf, area) != calm
    for _ in range(H.POPUP_LIFE + 40):
        frame(hud, surf, score=150)
    assert region(surf, area) == calm


def test_a_security_popup_is_drawn_beside_the_meter(surf):
    hud = HUD()
    area = pygame.Rect(560, 2, 100, 44)
    frame(hud, surf, security=0)
    calm = region(surf, area)
    frame(hud, surf, security=20)
    assert region(surf, area) != calm


def test_the_meter_flashes_when_security_rises_then_settles(surf):
    hud = HUD()
    cells = pygame.Rect(360, 22, 160, 14)
    frame(hud, surf, security=41)
    steady = region(surf, cells)
    frame(hud, surf, security=41)
    assert region(surf, cells) == steady and hud._sec_flash == 0
    frame(hud, surf, security=45)                          # 41 and 45 light the same nine cells
    during = region(surf, cells)
    assert hud._sec_flash > 0
    for _ in range(H.SEC_FLASH + 2):
        frame(hud, surf, security=45)
    after = region(surf, cells)
    assert hud._sec_flash == 0 and during != after


def test_the_hud_still_renders_with_every_option(surf):
    hud = HUD()
    for coop in (False, True):
        for timer in (None, 30, 600):
            surf.fill((0, 0, 0))
            hud.render(surf, "final_vault", score=10, security_level=90, security_max=100,
                       timer_remaining=timer, coop=coop, tick=3)
