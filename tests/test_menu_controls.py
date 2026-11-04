"""The how-to-play panel must describe the game as it plays now."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from ui import menu as menu_module
from ui.menu import CONTROLS, MainMenu


@pytest.fixture(autouse=True)
def display_init():
    pygame.init()
    pygame.display.set_mode((960, 640))


def rows():
    return dict(CONTROLS)


def test_no_row_still_tells_the_player_to_use_the_mouse():
    text = " ".join(f"{label} {action}" for label, action in CONTROLS).lower()
    assert "mouse" not in text and "click" not in text


def test_the_two_walkable_first_levels_say_how_to_move_and_use_things():
    action = rows()["Levels 1, 2"]
    assert "WASD" in action and "E " in action + " "
    assert "pick up" in action and "answer" in action


def test_the_answer_key_levels_still_say_1_to_4():
    assert "1-4" in rows()["Levels 3, 5, Final Vault"]


def test_every_label_is_unique_and_the_co_op_and_pause_rows_remain():
    labels = [label for label, _ in CONTROLS]
    assert len(labels) == len(set(labels))
    assert "Co-op (C)" in labels and "Any time" in labels


def test_every_control_line_fits_inside_the_panel():
    menu = MainMenu()
    panel = menu.layout(960)["panel"]
    for label, action in CONTROLS:
        assert menu.control_font.size(label)[0] <= 250 - 24 - 8, label           # label column
        assert 250 + menu.control_font.size(action)[0] <= panel.width - 12, action


def test_the_menu_still_renders_with_the_new_text():
    surface = pygame.Surface((960, 640))
    MainMenu().render(surface)
    assert menu_module.CONTROLS is CONTROLS
