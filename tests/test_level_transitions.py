"""Every level must start with the players at the start positions."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pytest

from core.game import Game, PLAYER_START_POS, PLAYER2_START_POS
from core.level_manager import LEVEL_ORDER

DT = 0.05


@pytest.fixture
def game():
    g = Game()
    g._start_new_run()
    return g


def test_advancing_a_level_puts_both_players_back_at_the_start(game, monkeypatch):
    game.player.rect.topleft = (700, 400)
    game.player2.rect.topleft = (650, 400)
    monkeypatch.setattr(game.level_manager.current, "is_complete", lambda: True)

    game.update(DT)

    assert game.level_manager.current_name == LEVEL_ORDER[1]
    spawns = getattr(game.level_manager.current, "spawn_points", None)
    start1, start2 = spawns if spawns else (PLAYER_START_POS, PLAYER2_START_POS)
    assert game.player.rect.topleft == start1
    assert game.player2.rect.topleft == start2


@pytest.mark.parametrize("name", LEVEL_ORDER)
def test_start_positions_are_free_in_every_spatial_level(game, name):
    game.level_manager.start(name)
    game._reset_player_position()

    blocked = game._get_spatial_blocked()
    if blocked is None:
        pytest.skip(f"{name} has no spatial geometry")

    assert not blocked(game.player.rect)
    assert not blocked(game.player2.rect)
