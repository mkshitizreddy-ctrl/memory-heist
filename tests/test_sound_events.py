"""Sound effects are triggered centrally, so every level gets them for free."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.game import Game
from systems.sound_events import SoundEvents


class SpyAudio:
    def __init__(self):
        self.played = []

    def play(self, name):
        self.played.append(name)


def snap(state="playing", score=0, security=0, level="level1", gates=0):
    return dict(state=state, score=score, security=security, level=level, gates=gates)


@pytest.fixture
def events():
    spy = SpyAudio()
    ev = SoundEvents(spy)
    ev.observe(**snap())          # first look only records the starting point
    return ev, spy


# ---- the observer on its own -------------------------------------------

def test_the_first_look_is_silent():
    spy = SpyAudio()
    SoundEvents(spy).observe(**snap(score=500, security=50))

    assert spy.played == []


def test_a_quiet_frame_makes_no_sound(events):
    ev, spy = events
    for _ in range(5):
        ev.observe(**snap())

    assert spy.played == []


def test_a_security_rise_plays_wrong(events):
    ev, spy = events
    ev.observe(**snap(security=20))

    assert spy.played == ["wrong"]


def test_a_score_rise_plays_correct(events):
    ev, spy = events
    ev.observe(**snap(score=100))

    assert spy.played == ["correct"]


def test_wrong_wins_when_both_happen_in_one_frame(events):
    ev, spy = events
    ev.observe(**snap(score=100, security=20))

    assert spy.played == ["wrong"]


def test_losing_points_alone_is_silent(events):
    ev, spy = events
    ev.observe(**snap(score=100))
    spy.played.clear()

    ev.observe(**snap(score=90))   # a hint costing points

    assert spy.played == []


def test_an_opened_gate_plays_unlock(events):
    ev, spy = events
    ev.observe(**snap(score=100, gates=1))

    assert "unlock" in spy.played


def test_gates_resetting_with_a_new_level_is_silent(events):
    ev, spy = events
    ev.observe(**snap(gates=2))
    spy.played.clear()

    ev.observe(**snap(gates=0))

    assert spy.played == []


def test_clearing_a_level_without_cards_plays_unlock(events):
    ev, spy = events
    ev.observe(**snap(level="level2"))

    assert spy.played == ["unlock"]


@pytest.mark.parametrize("state", ["briefing", "outro", "win"])
def test_leaving_play_after_a_clear_plays_unlock(events, state):
    ev, spy = events
    ev.observe(**snap(state=state))

    assert spy.played == ["unlock"]


def test_losing_the_run_plays_wrong(events):
    ev, spy = events
    ev.observe(**snap(state="lose"))

    assert spy.played == ["wrong"]


def test_starting_a_run_resets_quietly():
    spy = SpyAudio()
    ev = SoundEvents(spy)
    ev.observe(**snap(state="intro", score=900, security=60, level="level5"))
    ev.observe(**snap(state="playing", score=0, security=0, level="level1"))

    assert spy.played == []


def test_retrying_after_a_loss_is_quiet():
    spy = SpyAudio()
    ev = SoundEvents(spy)
    ev.observe(**snap(state="lose", security=100, level="level3"))
    ev.observe(**snap(state="playing", security=0, level="level1"))

    assert spy.played == []


def test_menus_and_cards_make_no_gameplay_sounds():
    spy = SpyAudio()
    ev = SoundEvents(spy)
    ev.observe(**snap(state="menu"))
    ev.observe(**snap(state="menu", score=50, security=30))

    assert spy.played == []


def test_click_plays_click():
    spy = SpyAudio()
    SoundEvents(spy).click()

    assert spy.played == ["click"]


# ---- wired into the real game ---------------------------------------------

def key(game, k, ch=""):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=k, unicode=ch))
    game.handle_events()


@pytest.fixture
def game():
    g = Game()
    g.sounds.audio = SpyAudio()
    return g


@pytest.fixture
def playing(game):
    key(game, pygame.K_RETURN)
    key(game, pygame.K_ESCAPE)       # skip the story
    assert game.state == "playing"
    game.update(0.016)
    game.sounds.audio.played.clear()
    return game


def test_the_game_owns_a_sound_observer(game):
    assert isinstance(game.sounds, SoundEvents)


def test_a_wrong_answer_in_any_level_plays_wrong(playing):
    playing.security.increase(20)
    playing.update(0.016)

    assert playing.sounds.audio.played == ["wrong"]


def test_a_scored_answer_in_any_level_plays_correct(playing):
    playing.score.add(100)
    playing.update(0.016)

    assert playing.sounds.audio.played == ["correct"]


def test_finishing_a_level_plays_unlock(playing):
    playing.level_manager.current.complete = True
    playing.update(0.016)

    assert "unlock" in playing.sounds.audio.played


def test_running_out_of_time_plays_wrong(playing):
    playing.timer.remaining = 0.01
    playing.update(1.0)

    assert playing.state == "lose"
    assert playing.sounds.audio.played == ["wrong"]


def test_a_quiet_playing_frame_is_silent(playing):
    for _ in range(10):
        playing.update(0.016)

    assert playing.sounds.audio.played == []


def test_keys_on_the_menu_click(game):
    key(game, pygame.K_DOWN)

    assert game.sounds.audio.played == ["click"]


def test_keys_on_a_story_card_click(game):
    key(game, pygame.K_RETURN)
    game.sounds.audio.played.clear()

    key(game, pygame.K_SPACE, " ")

    assert game.sounds.audio.played == ["click"]


def test_f11_does_not_click(game):
    game.sounds.audio.played.clear()
    original = pygame.display.toggle_fullscreen
    pygame.display.toggle_fullscreen = lambda: 1
    try:
        key(game, pygame.K_F11)
    finally:
        pygame.display.toggle_fullscreen = original

    assert game.sounds.audio.played == []


def test_playing_keys_do_not_click(playing):
    key(playing, pygame.K_a, "a")

    assert "click" not in playing.sounds.audio.played


def test_a_muted_game_still_runs(game):
    game.audio.enabled = False
    game.sounds.audio = game.audio
    key(game, pygame.K_RETURN)
    key(game, pygame.K_ESCAPE)
    game.security.increase(20)
    game.update(0.016)

    assert game.state == "playing"
