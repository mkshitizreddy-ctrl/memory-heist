"""Settings: saved volumes, the panel, and how the game uses them."""

import json
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.game import Game
from systems import settings as S
from systems.audio import Audio
from systems.music import MASTER, MusicPlayer
from ui import theme
from ui.menu import MainMenu
from ui.overlays import PauseOverlay
from ui.settings_screen import (ROW_MUSIC, ROW_SFX, ROW_SOUND, SettingsScreen)


@pytest.fixture(autouse=True)
def init():
    pygame.init()
    yield
    pygame.mixer.stop()
    pygame.mixer.set_reserved(0)


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode="")


def mouse(kind, pos, button=1):
    return pygame.event.Event(kind, pos=pos, button=button)


# --- the settings object -------------------------------------------------
@pytest.mark.parametrize("raw, expected", [
    (0.5, 0.5), (-1, 0.0), (7, 1.0), (0.333, 0.33), ("loud", 0.3), (None, 0.3),
    (True, 0.3), (float("nan"), 0.3), (1, 1.0)])
def test_clamp(raw, expected):
    assert S.clamp(raw, default=0.3) == expected


def test_step_moves_by_a_tenth_and_stays_in_range():
    assert S.step(0.5, 0.1) == 0.6
    assert S.step(0.3, -0.1) == 0.2
    assert S.step(1.0, 0.1) == 1.0 and S.step(0.0, -0.1) == 0.0
    v = 0.0
    for _ in range(10):
        v = S.step(v, S.STEP)
    assert v == 1.0                                   # no float drift after ten steps


def test_defaults_keep_the_games_current_loudness():
    s = S.Settings()
    assert (s.music, s.sfx, s.muted) == (1.0, 1.0, False)


def test_setters_reject_junk_and_keep_the_old_value():
    s = S.Settings(music=0.4)
    s.set_music("x")
    assert s.music == 0.4
    s.set_music(2)
    assert s.music == 1.0


def test_save_and_load_round_trip(tmp_path):
    path = str(tmp_path / "sub" / "s.json")
    s = S.Settings(music=0.3, sfx=0.7, muted=True, path=path)
    assert s.save() is True
    loaded = S.Settings.load(path)
    assert (loaded.music, loaded.sfx, loaded.muted) == (0.3, 0.7, True)


@pytest.mark.parametrize("content", ["", "not json", "[1,2]", "null", '{"music": "x"}'])
def test_damaged_files_give_defaults(tmp_path, content):
    path = tmp_path / "s.json"
    path.write_text(content)
    s = S.Settings.load(str(path))
    assert (s.music, s.sfx, s.muted) == (1.0, 1.0, False)


def test_missing_file_gives_defaults(tmp_path):
    assert S.Settings.load(str(tmp_path / "nope.json")).music == 1.0


def test_wrong_types_are_ignored_field_by_field(tmp_path):
    path = tmp_path / "s.json"
    path.write_text(json.dumps({"music": 0.2, "sfx": "high", "muted": "yes"}))
    s = S.Settings.load(str(path))
    assert s.music == 0.2 and s.sfx == 1.0 and s.muted is False


def test_failed_save_returns_false_instead_of_crashing(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    s = S.Settings(path=str(blocker / "child" / "s.json"))
    assert s.save() is False


def test_env_var_chooses_the_path(monkeypatch, tmp_path):
    monkeypatch.setenv(S.ENV_VAR, str(tmp_path / "elsewhere.json"))
    assert S.settings_path() == str(tmp_path / "elsewhere.json")
    monkeypatch.delenv(S.ENV_VAR)
    assert S.settings_path() == S.DEFAULT_PATH


# --- audio ---------------------------------------------------------------
def test_apply_settings_sets_volumes_and_mute():
    a = Audio(ambient=False)
    a.apply_settings(S.Settings(music=0.3, sfx=0.6, muted=True))
    assert (a.music_volume, a.sfx_volume, a.enabled) == (0.3, 0.6, False)
    a.apply_settings(S.Settings(muted=False))
    assert a.enabled is True


def test_effects_volume_scales_each_sound_from_its_own_base():
    a = Audio(ambient=False)
    a.sounds["pickup"].set_volume(0.5)
    a.apply_settings(S.Settings(sfx=0.4))
    a.play("pickup")
    assert a.sounds["pickup"].get_volume() == pytest.approx(0.2, abs=0.02)
    a.apply_settings(S.Settings(sfx=1.0))
    a.play("pickup")
    assert a.sounds["pickup"].get_volume() == pytest.approx(0.5, abs=0.02)


def test_muted_audio_plays_nothing():
    a = Audio(ambient=False)
    a.apply_settings(S.Settings(muted=True))
    a.sounds["click"].set_volume(0.123)
    a.play("click")
    assert a.sounds["click"].get_volume() == pytest.approx(0.123, abs=0.01)   # untouched: never played


def test_music_target_volume_follows_the_music_slider():
    a = Audio(ambient=False)
    m = MusicPlayer(a)
    def top_volume():
        m.update(5.0, "playing", "level1", 0.0)
        return max(v.target for v in m.voices if v.key == m.key)
    a.apply_settings(S.Settings(music=1.0))
    full = top_volume()
    a.apply_settings(S.Settings(music=0.5))
    assert top_volume() == pytest.approx(full * 0.5)
    a.apply_settings(S.Settings(music=0.0))
    assert top_volume() == 0.0
    m.stop()


def test_music_volume_slider_cannot_exceed_the_designed_mix():
    a = Audio(ambient=False)
    m = MusicPlayer(a)
    a.apply_settings(S.Settings(music=1.0))
    m.update(5.0, "playing", "level1", 1.0)
    assert all(v.target <= MASTER + 1e-9 for v in m.voices)
    m.stop()


# --- the panel -----------------------------------------------------------
@pytest.fixture
def panel(tmp_path):
    calls = []
    s = S.Settings(music=0.5, sfx=0.5, path=str(tmp_path / "p.json"))
    screen = SettingsScreen(s, on_change=calls.append)
    screen.open()
    return screen, s, calls


def test_a_closed_panel_ignores_events(panel):
    screen, s, calls = panel
    screen.close()
    assert screen.handle_event(key(pygame.K_RIGHT)) is False
    assert s.music == 0.5 and calls == []


def test_an_open_panel_consumes_every_event(panel):
    screen, *_ = panel
    assert screen.handle_event(key(pygame.K_F5)) is True
    assert screen.handle_event(mouse(pygame.MOUSEMOTION, (1, 1), 0)) is True


def test_up_down_wrap_around_the_three_rows(panel):
    screen, *_ = panel
    assert screen.selected == ROW_MUSIC
    screen.handle_event(key(pygame.K_UP))
    assert screen.selected == ROW_SOUND
    screen.handle_event(key(pygame.K_DOWN))
    assert screen.selected == ROW_MUSIC


def test_left_right_adjust_the_selected_slider_and_report_what_changed(panel):
    screen, s, calls = panel
    screen.handle_event(key(pygame.K_RIGHT))
    assert s.music == 0.6 and calls == ["music"]
    screen.handle_event(key(pygame.K_DOWN))
    screen.handle_event(key(pygame.K_LEFT))
    screen.handle_event(key(pygame.K_LEFT))
    assert s.sfx == 0.3 and calls[-1] == "sfx" and s.music == 0.6


def test_a_slider_at_its_end_does_not_report_a_change(panel):
    screen, s, calls = panel
    s.set_music(1.0)
    screen.handle_event(key(pygame.K_RIGHT))
    assert calls == []


def test_sound_row_and_m_key_toggle_mute(panel):
    screen, s, calls = panel
    screen.handle_event(key(pygame.K_m))
    assert s.muted is True and calls == ["mute"]
    screen.selected = ROW_SOUND
    screen.handle_event(key(pygame.K_RETURN))
    assert s.muted is False
    screen.handle_event(key(pygame.K_LEFT))
    assert s.muted is True


def test_enter_on_a_slider_closes_and_escape_always_closes(panel):
    screen, s, _ = panel
    screen.handle_event(key(pygame.K_RETURN))
    assert screen.closed
    screen.open()
    screen.selected = ROW_SOUND
    screen.handle_event(key(pygame.K_ESCAPE))
    assert screen.closed


def test_closing_saves_to_disk(panel):
    screen, s, _ = panel
    screen.handle_event(key(pygame.K_RIGHT))
    screen.handle_event(key(pygame.K_ESCAPE))
    assert S.Settings.load(s.path).music == 0.6


def test_clicking_a_track_sets_the_value_from_the_x_position(panel):
    screen, s, calls = panel
    track = screen.track_rect(ROW_SFX)
    screen.handle_event(mouse(pygame.MOUSEBUTTONDOWN, (track.x + track.width // 4, track.centery)))
    assert s.sfx == 0.25 and screen.selected == ROW_SFX and calls == ["sfx"]


def test_dragging_follows_the_mouse_and_stops_on_release(panel):
    screen, s, _ = panel
    track = screen.track_rect(ROW_MUSIC)
    screen.handle_event(mouse(pygame.MOUSEBUTTONDOWN, (track.x + 10, track.centery)))
    screen.handle_event(mouse(pygame.MOUSEMOTION, (track.right + 80, track.centery), 0))
    assert s.music == 1.0
    screen.handle_event(mouse(pygame.MOUSEMOTION, (track.x - 80, track.centery), 0))
    assert s.music == 0.0
    screen.handle_event(mouse(pygame.MOUSEBUTTONUP, (0, 0)))
    screen.handle_event(mouse(pygame.MOUSEMOTION, (track.x + 100, track.centery), 0))
    assert s.music == 0.0                              # no longer dragging


def test_right_click_does_nothing(panel):
    screen, s, calls = panel
    track = screen.track_rect(ROW_MUSIC)
    screen.handle_event(mouse(pygame.MOUSEBUTTONDOWN, (track.x + 20, track.centery), button=3))
    assert s.music == 0.5 and calls == []


def test_clicking_the_chips(panel):
    screen, s, _ = panel
    screen.handle_event(mouse(pygame.MOUSEBUTTONDOWN, screen.sound_chip().center))
    assert s.muted is True
    screen.handle_event(mouse(pygame.MOUSEBUTTONDOWN, screen.done_chip().center))
    assert screen.closed


def test_value_at_clamps_outside_the_track(panel):
    screen, *_ = panel
    track = screen.track_rect(ROW_MUSIC)
    assert screen.value_at(track.x - 500, ROW_MUSIC) == 0.0
    assert screen.value_at(track.right + 500, ROW_MUSIC) == 1.0
    assert screen.value_at(track.centerx, ROW_MUSIC) == 0.5


def test_panel_layout_fits_and_rows_do_not_overlap(panel):
    screen, *_ = panel
    screen_rect = pygame.Rect(0, 0, 960, 640)
    rects = [screen.track_rect(ROW_MUSIC).inflate(0, 20), screen.track_rect(ROW_SFX).inflate(0, 20),
             screen.sound_chip(), screen.done_chip()]
    for r in rects:
        assert screen.panel.contains(r) and screen_rect.contains(r)
    for i, a in enumerate(rects):
        for b in rects[i + 1:]:
            assert not a.colliderect(b)


def test_drawing_shows_the_values_and_a_closed_panel_draws_nothing(panel):
    screen, s, _ = panel
    seen = []

    class Rec:
        def __init__(self, f): self.f = f
        def render(self, t, *a, **k):
            seen.append(t)
            return self.f.render(t, *a, **k)

    screen.small_font = Rec(screen.small_font)
    surf = pygame.Surface((960, 640))
    surf.fill((9, 9, 9))
    screen.draw(surf)
    assert "50%" in seen
    screen.close()
    blank = pygame.Surface((960, 640))
    blank.fill((9, 9, 9))
    before = pygame.image.tostring(blank, "RGB")
    screen.draw(blank)
    assert pygame.image.tostring(blank, "RGB") == before


def test_muted_sliders_are_drawn_grey(panel):
    screen, s, _ = panel
    surf = pygame.Surface((960, 640))
    track = screen.track_rect(ROW_MUSIC)
    probe = (track.x + 20, track.centery)
    screen.draw(surf)
    live = surf.get_at(probe)[:3]
    s.muted = True
    screen.draw(surf)
    assert surf.get_at(probe)[:3] != live


# --- in the game -----------------------------------------------------------
def press(game, k):
    pygame.event.clear()
    pygame.event.post(key(k))
    game.handle_events()


@pytest.fixture
def game():
    g = Game()
    g.music.stop()
    return g


def test_s_opens_settings_from_the_menu(game):
    game.state = "menu"
    press(game, pygame.K_s)
    assert not game.settings_screen.closed


def test_s_opens_settings_from_the_pause_panel_only(game):
    game._start_new_run()
    game.story_enabled = False
    game.state = "playing"
    press(game, pygame.K_s)
    assert game.settings_screen.closed                 # not paused: S is just a game key
    game.paused = True
    press(game, pygame.K_s)
    assert not game.settings_screen.closed


@pytest.mark.parametrize("state", ["intro", "briefing", "win", "lose", "outro"])
def test_s_does_nothing_on_other_screens(game, state):
    game.state = state
    if state == "win":
        game.win_screen.skip_entry()
    press(game, pygame.K_s)
    assert game.settings_screen.closed


def test_typing_s_in_the_name_box_does_not_open_settings(game):
    game.change_state("win")
    assert game.win_screen.entering
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_s, unicode="s"))
    game.handle_events()
    assert game.settings_screen.closed and game.win_screen.name == "s"


def test_escape_closes_only_the_panel_not_the_pause_or_the_game(game):
    game._start_new_run()
    game.state = "playing"
    game.paused = True
    press(game, pygame.K_s)
    press(game, pygame.K_ESCAPE)
    assert game.settings_screen.closed and game.paused is True and game.running


def test_escape_on_the_menu_panel_does_not_quit(game):
    game.state = "menu"
    press(game, pygame.K_s)
    press(game, pygame.K_ESCAPE)
    assert game.running and game.state == "menu"


def test_menu_keys_are_ignored_while_the_panel_is_open(game):
    game.state = "menu"
    press(game, pygame.K_s)
    before = (game.menu.selected_difficulty, game.menu.coop)
    press(game, pygame.K_3)
    press(game, pygame.K_c)
    press(game, pygame.K_RETURN)
    assert (game.menu.selected_difficulty, game.menu.coop) == before and game.state == "menu"


def test_changes_reach_the_audio_live_and_persist_after_closing(game):
    game.state = "menu"
    press(game, pygame.K_s)
    press(game, pygame.K_LEFT)
    press(game, pygame.K_LEFT)
    assert game.audio.music_volume == 0.8
    press(game, pygame.K_m)
    assert game.audio.enabled is False
    press(game, pygame.K_ESCAPE)
    again = Game()
    again.music.stop()
    assert again.settings.music == 0.8 and again.settings.muted is True
    assert again.audio.music_volume == 0.8 and again.audio.enabled is False


def test_adjusting_effects_plays_a_sample_blip(game, monkeypatch):
    played = []
    monkeypatch.setattr(game.audio, "play", played.append)
    game.state = "menu"
    press(game, pygame.K_s)
    played.clear()                                     # the S key itself clicks on the menu
    press(game, pygame.K_DOWN)
    press(game, pygame.K_LEFT)
    assert played == ["pickup"]
    played.clear()
    press(game, pygame.K_UP)
    press(game, pygame.K_LEFT)                         # music slider: silent
    assert "pickup" not in played


def test_mouse_events_do_not_leak_to_the_game_under_the_panel(game, monkeypatch):
    game._start_new_run()
    game.story_enabled = False
    game.state = "playing"
    game.paused = True
    press(game, pygame.K_s)
    seen = []
    monkeypatch.setattr(game.level_manager, "handle_event", seen.append)
    pygame.event.clear()
    pygame.event.post(mouse(pygame.MOUSEBUTTONDOWN, (5, 5)))
    game.handle_events()
    assert seen == []


def test_the_panel_is_drawn_over_the_menu_only_while_open(game):
    game.state = "menu"
    r = game.settings_screen.panel
    edge = (r.x + 1, r.centery)
    game.render()
    assert game.screen.get_at(edge)[:3] != theme.SKY
    game.settings_screen.open()
    game.render()
    assert game.screen.get_at(edge)[:3] == theme.SKY
    game.settings_screen.close()
    game.render()
    assert game.screen.get_at(edge)[:3] != theme.SKY


def test_a_player_who_never_touched_settings_gets_the_defaults(game):
    assert (game.settings.music, game.settings.sfx, game.settings.muted) == (1.0, 1.0, False)
    assert game.audio.enabled is True


# --- hints on menu and pause ---------------------------------------------
def test_menu_hint_line_fits_and_does_not_overlap():
    lay = MainMenu().layout()
    screen = pygame.Rect(0, 0, 960, 640)
    assert screen.contains(lay["hint"]) and not lay["hint"].colliderect(lay["start"])


def test_menu_draws_the_settings_hint():
    seen = []

    class Rec:
        def __init__(self, f): self.f = f
        def render(self, t, *a, **k):
            seen.append(t)
            return self.f.render(t, *a, **k)

    m = MainMenu()
    m.control_font = Rec(m.control_font)
    m.render(pygame.Surface((960, 640)))
    assert any("S: settings" in t for t in seen)


def test_pause_resume_chip_mentions_settings_and_still_fits():
    o = PauseOverlay((960, 640))
    chip = o.resume_chip()
    assert o.panel.contains(chip)
    text = pygame.font.Font(None, 26).render("ESC: resume   |   S: settings", True, (0, 0, 0))
    assert text.get_width() < chip.width - 20


def test_muting_makes_no_sample_blip(game, monkeypatch):
    played = []
    monkeypatch.setattr(game.audio, "play", played.append)
    game.state = "menu"
    press(game, pygame.K_s)
    played.clear()
    press(game, pygame.K_m)
    press(game, pygame.K_m)
    assert played == []
