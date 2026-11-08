"""The Master Vault as a walkable floor: geometry, the unchanged Final Vault rules, the terminal, the game."""

import collections
import os
from collections import deque
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.player import Player
from core.tilemap import TILE
from levels import final_vault_hall as FH
from levels import vault_decor as V
from levels.final_vault import FinalVault
from levels.final_vault_hall import VaultHall
from systems.scoring import ScoreTracker
from systems.security import SecurityMeter

E_KEY = pygame.K_e
CORRECT_PADS = [0, 1, 2, 0, 2, 1]            # the old CORRECT_SEQUENCE [1, 2, 3, 1, 3, 2], zero-based


@pytest.fixture(autouse=True)
def display_init():
    pygame.init()
    pygame.display.set_mode((960, 640))


class FakeAudio:
    def __init__(self):
        self.played = []

    def play(self, name, group="sfx"):
        self.played.append(name)


def make_vault(coop=False, seed=1):
    game = SimpleNamespace(score=ScoreTracker(), security=SecurityMeter(), hints=SimpleNamespace(enabled=True),
                           coop=coop, player2=None, difficulty={"label": "MEDIUM"}, audio=FakeAudio())
    game.score.add(100)
    player = Player(*V.SPAWNS[0])
    if coop:
        game.player2 = Player(*V.SPAWNS[1])
    return VaultHall(player=player, game=game, seed=seed), game, player


def key(k, unicode=""):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode=unicode)


def press(vault, k=E_KEY, unicode=""):
    vault.handle_event(key(k, unicode))


def answer(vault, player, pad):
    player.rect.center = vault.pad_rects()[pad].center
    press(vault)


def solve_to(vault, player, stage):
    while vault.stage < stage:
        answer(vault, player, CORRECT_PADS[vault.stage - 1])


def at_console(vault, player):
    player.rect.midbottom = (V.CONSOLE.centerx, V.CONSOLE.y)
    press(vault)


def type_text(vault, text):
    for ch in text:
        press(vault, ord(ch) if ch.isalnum() else pygame.K_MINUS, ch)


def settle(vault, seconds=3.0):
    for _ in range(int(seconds * 60)):
        vault.update(1 / 60)


def terminal_vault(**kw):
    vault, game, player = make_vault(**kw)
    solve_to(vault, player, 6)
    at_console(vault, player)
    return vault, game, player


# --- geometry ---------------------------------------------------------------
def tile_free(vault, col, row):
    return not vault.room_map.blocked(pygame.Rect(col * TILE + 2, row * TILE + 2, 28, 28))


def reachable(vault, start, goal):
    seen, queue = {start}, deque([start])
    while queue:
        c, r = queue.popleft()
        if (c, r) == goal:
            return True
        for nc, nr in ((c + 1, r), (c - 1, r), (c, r + 1), (c, r - 1)):
            if (nc, nr) not in seen and 0 <= nc < 30 and 0 <= nr < 20 and tile_free(vault, nc, nr):
                seen.add((nc, nr))
                queue.append((nc, nr))
    return False


def test_each_chamber_holds_three_stacked_pads_clear_of_walls_props_and_each_other():
    vault, _, _ = make_vault()
    for chamber, (first, last) in enumerate(V.CHAMBERS):
        pads = V.pad_rects(chamber, 3)
        floor = pygame.Rect(first * TILE, 6 * TILE, (last - first + 1) * TILE, 12 * TILE)
        for i, pad in enumerate(pads):
            assert floor.contains(pad) and not vault.tilemap.collides(pad)
            assert not any(pad.colliderect(p) for p in vault.props)
            assert not any(pad.colliderect(q) for q in pads[:i])
            assert pad.top >= (V.LANE_ROWS[-1] + 1) * TILE
        assert pads[0].top < pads[1].top < pads[2].top and len({p.x for p in pads}) == 1


def test_the_gates_really_gate_the_way_through():
    vault, _, _ = make_vault()
    lane, start = V.LANE_ROWS[1], (3, V.LANE_ROWS[1])
    assert reachable(vault, start, (9, lane)) and not reachable(vault, start, (12, lane))
    vault.gate_blocks[0].size = (0, 0)
    assert reachable(vault, start, (12, lane)) and not reachable(vault, start, (21, lane))
    vault.gate_blocks[1].size = (0, 0)
    assert reachable(vault, start, (21, lane)) and not reachable(vault, start, (29, lane))
    vault.gate_blocks[2].size = (0, 0)
    assert reachable(vault, start, (29, lane))


def test_every_pad_and_the_front_of_the_console_can_be_reached_once_the_gates_are_open():
    vault, _, _ = make_vault()
    for block in vault.gate_blocks:
        block.size = (0, 0)
    start = (3, V.LANE_ROWS[1])
    for chamber in range(3):
        for pad in V.pad_rects(chamber, 3):
            assert reachable(vault, start, (pad.centerx // TILE, pad.centery // TILE))
    assert reachable(vault, start, (V.CONSOLE.centerx // TILE, V.CONSOLE.y // TILE - 1))


def test_standing_at_the_console_is_not_standing_on_a_pad():
    """Walking down into the console must never leave you where E answers a pad."""
    vault, _, player = make_vault()
    vault.stage = 6
    player.rect.midbottom = (V.CONSOLE.centerx, V.CONSOLE.y)
    assert not vault.room_map.blocked(player.rect)
    assert vault.pad_at(player) is None and vault.near(player, V.CONSOLE)
    player.rect.y += 1
    assert vault.room_map.blocked(player.rect)             # the console really is the stop


def test_props_stand_off_the_lane_and_spawns_and_the_console_is_in_chamber_three():
    vault, _, _ = make_vault()
    lane = pygame.Rect(2 * TILE, V.LANE_ROWS[0] * TILE, 26 * TILE, 3 * TILE)
    for prop in vault.props:
        assert not prop.colliderect(lane)
        assert not any(prop.colliderect(pygame.Rect(s, (32, 32))) for s in V.SPAWNS)
    first, last = V.CHAMBERS[2]
    assert first * TILE <= V.CONSOLE.left and V.CONSOLE.right <= (last + 1) * TILE
    for prop in V.rack_rects() + [V.code_rect(c) for c in range(3)] + [V.CONSOLE]:
        assert vault.room_map.blocked(pygame.Rect(prop.center, (4, 4)))


def test_code_monitors_hang_inside_their_chambers_under_the_screens():
    for c, (first, last) in enumerate(V.CHAMBERS):
        r = V.code_rect(c)
        assert first * TILE <= r.left and r.right <= (last + 1) * TILE
        assert r.top >= V.G.SCREEN_Y + V.G.SCREEN_H + 8 and r.bottom <= V.LANE_ROWS[0] * TILE


def test_every_stage_fits_its_screen_monitor_and_pads():
    vault, _, _ = make_vault()
    screen = V.screen_rect(0)
    for stage in range(1, 7):
        vault.stage = stage
        font, lines = V.fit_prompt(vault._get_objective(), screen.w - 16, screen.h - V.SCREEN_PROMPT_TOP - 4)
        assert " ".join(lines) == vault._get_objective()
        assert len(lines) * font.get_linesize() <= screen.h - V.SCREEN_PROMPT_TOP - 4
        code = vault._get_code_lines()
        cfont = V.fit_code(code, V.CODE_W - 24)
        assert all(cfont.size(line)[0] <= V.CODE_W - 24 for line in code)
        assert 24 + len(code) * V.CODE_LINE_H <= V.CODE_H
        for option in vault._get_options():
            pfont, plines = V.fit_label(option, V.PAD_W - 12, V.PAD_H - 6)
            assert " ".join(plines) == option and len(plines) * pfont.get_linesize() <= V.PAD_H - 6


def test_the_blank_in_a_snippet_is_the_lit_line():
    assert V.lit_lines(["a = 1", "b = a ? 2", "c"]) == {1}
    assert V.lit_lines(["x"]) == set() and V.fit_code([], 100) is not None


# --- it is still the Final Vault underneath ---------------------------------------
def test_it_is_a_final_vault_underneath():
    vault, _, _ = make_vault()
    assert isinstance(vault, FinalVault) and vault.total_stages == 6 and vault.stage == 1
    assert vault.is_complete() is False and vault.movement_locked is False and vault.solved is False


def test_the_right_pads_are_the_old_right_answers_in_the_same_order():
    vault, _, _ = make_vault()
    old = FinalVault()
    for stage, pad in enumerate(CORRECT_PADS, start=1):
        vault.stage = old.stage = stage
        assert vault._is_correct_option(pad + 1) and old._is_correct_option(pad + 1)
        assert len(vault.pad_rects()) == 3


def test_a_right_pad_scores_advances_and_clears_the_terminal():
    vault, game, player = make_vault()
    before = game.score.get_score()
    vault.command, vault.command_result = "12", "old"
    answer(vault, player, 0)
    assert game.score.get_score() == before + FH.STAGE_POINTS
    assert vault.stage == 2 and vault.command == "" and vault.command_result == ""
    assert vault.feedback.startswith("CORRECT") and vault.message == vault.feedback
    assert "door" in game.audio.played


def test_a_wrong_pad_costs_security_and_score_and_can_be_retried():
    vault, game, player = make_vault()
    before = game.score.get_score()
    answer(vault, player, 1)
    assert vault.stage == 1 and "INCORRECT" in vault.feedback
    assert game.security.level == 20                        # the old Final Vault's numbers, spelled out
    assert game.score.get_score() == before - 10
    assert vault.pad_flash and vault.shake.trauma > 0
    answer(vault, player, 1)                                # no elimination: same pad costs again
    assert game.security.level == 40
    answer(vault, player, 0)
    assert vault.stage == 2


def test_a_whole_run_scores_the_same_as_the_old_final_vault():
    vault, game, player = make_vault()
    before = game.score.get_score()
    solve_to(vault, player, 6)
    answer(vault, player, CORRECT_PADS[5])
    assert game.score.get_score() - before == 6 * 50 + 150
    assert vault.solved and "MASTER VAULT UNLOCKED" in vault.feedback and game.security.level == 0
    assert vault.pad_rects() == [] and vault.pad_at(player) is None
    assert vault.complete is False and vault.is_complete() is False      # walk out to finish


def test_the_completion_bonus_is_paid_once():
    vault, game, player = make_vault()
    solve_to(vault, player, 6)
    answer(vault, player, 1)
    score = game.score.get_score()
    vault.stage = 6
    vault.solved = False
    answer(vault, player, 1)
    assert game.score.get_score() == score                 # that stage and the bonus were already paid


def test_gates_passed_climbs_two_stages_at_a_time():
    vault, _, player = make_vault()
    seen = [vault.gates_passed]
    for pad in CORRECT_PADS:
        answer(vault, player, pad)
        seen.append(vault.gates_passed)
    assert seen == [0, 0, 1, 1, 2, 2, 3]


def test_gates_open_gradually_and_the_vault_door_waits_for_stage_six():
    vault, _, player = make_vault()
    solve_to(vault, player, 2)
    settle(vault)
    assert vault.gate_blocks[0].size == (TILE, 3 * TILE)    # one stage in: gate 1 still shut
    solve_to(vault, player, 3)
    for _ in range(14):
        vault.update(1 / 60)
    assert 0.1 < vault.gate_open[0] < 0.9 and vault.gate_blocks[0].size == (TILE, 3 * TILE)
    settle(vault)
    assert vault.gate_blocks[0].size == (0, 0) and vault.gate_blocks[1].w > 0 and vault.gate_blocks[2].w > 0
    solve_to(vault, player, 5)
    settle(vault)
    assert vault.gate_blocks[1].size == (0, 0) and vault.gate_blocks[2].w > 0
    solve_to(vault, player, 6)
    assert vault.gate_blocks[2].w > 0
    answer(vault, player, 1)
    settle(vault)
    assert vault.gate_blocks[2].size == (0, 0)


def test_pressing_off_a_pad_only_gives_a_nudge_and_number_keys_do_nothing():
    vault, game, player = make_vault()
    player.rect.center = (3 * TILE, 11 * TILE)
    before = (game.score.get_score(), game.security.level)
    press(vault)
    for k in (pygame.K_1, pygame.K_2, pygame.K_3):
        press(vault, k)
    assert (game.score.get_score(), game.security.level) == before and "pad" in vault.message
    assert vault.stage == 1


def test_the_pad_zone_is_the_pad_plus_a_little_slack():
    vault, _, player = make_vault()
    pad = vault.pad_rects()[0]
    player.rect.center = (pad.left - 4, pad.centery)
    assert vault.pad_at(player) == 0
    player.rect.center = (pad.left - 8, pad.centery)
    assert vault.pad_at(player) is None


def test_the_second_player_answers_with_right_shift_only_in_co_op():
    vault, game, p1 = make_vault(coop=True)
    p1.rect.center = (3 * TILE, 11 * TILE)
    game.player2.rect.center = vault.pad_rects()[0].center
    press(vault, pygame.K_RSHIFT)
    assert vault.stage == 2
    solo, _, _ = make_vault()
    Player(0, 0).rect.center = solo.pad_rects()[0].center
    press(solo, pygame.K_RSHIFT)
    assert solo.stage == 1


# --- the stage 6 terminal ----------------------------------------------------------
def test_the_console_is_locked_until_stage_six_and_e_there_does_nothing():
    vault, _, player = make_vault()
    assert vault.console_state() == "locked"
    player.rect.midbottom = (V.CONSOLE.centerx, V.CONSOLE.y)
    press(vault)
    assert vault.at_terminal is False


def test_e_at_the_console_on_stage_six_logs_in_without_answering_a_pad():
    vault, game, player = make_vault()
    solve_to(vault, player, 6)
    before = (game.score.get_score(), game.security.level)
    at_console(vault, player)
    assert vault.at_terminal and vault.movement_locked and vault.console_state() == "active"
    assert (game.score.get_score(), game.security.level) == before and vault.stage == 6


def test_e_away_from_the_console_and_pads_does_not_log_in():
    vault, _, player = make_vault()
    solve_to(vault, player, 6)
    player.rect.center = (3 * TILE, 11 * TILE)
    press(vault)
    assert vault.at_terminal is False


def test_digits_one_to_three_can_be_typed_at_the_terminal():
    """The old screen used 1-3 as answer keys, so these digits could not be typed on stage 6."""
    vault, _, _ = terminal_vault()
    type_text(vault, "123")
    assert vault.command == "123" and vault.stage == 6


def test_the_terminal_takes_four_characters_and_backspace_edits():
    vault, _, _ = terminal_vault()
    type_text(vault, "12345")
    assert vault.command == "1234"
    press(vault, pygame.K_BACKSPACE)
    assert vault.command == "123"


def test_text_shows_a_caught_value_error_and_costs_five_security():
    vault, game, _ = terminal_vault()
    type_text(vault, "ab")
    before = game.security.level
    press(vault, pygame.K_RETURN)
    assert "ValueError caught" in vault.command_result and "EXCEPTION HANDLED" in vault.feedback
    assert game.security.level - before == 5 and vault.command == "" and vault.at_terminal
    assert vault.feedback_good() and vault.stage == 6 and vault.solved is False


def test_the_right_number_is_accepted_for_free_and_a_wrong_one_costs_five():
    vault, game, _ = terminal_vault()
    type_text(vault, "5")
    press(vault, pygame.K_RETURN)
    assert "clearance level verified" in vault.command_result and game.security.level == 0
    assert vault.feedback_good() and vault.solved is False
    type_text(vault, "9")
    press(vault, pygame.K_RETURN)
    assert vault.command_result == "Integer received: 9" and game.security.level == 5
    assert not vault.feedback_good() and vault.shake.trauma > 0


def test_an_empty_entry_asks_for_a_value():
    vault, _, _ = terminal_vault()
    press(vault, pygame.K_RETURN)
    assert "Enter a value" in vault.feedback and vault.at_terminal


def test_an_arrow_key_steps_away_and_keeps_the_entry():
    vault, _, _ = terminal_vault()
    type_text(vault, "42")
    for k in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
        vault.at_terminal = True
        press(vault, k)
        assert vault.at_terminal is False and vault.command == "42"
    assert vault.movement_locked is False


def test_the_terminal_alone_never_finishes_the_vault_you_still_choose_try_except():
    vault, _, player = terminal_vault()
    type_text(vault, "5")
    press(vault, pygame.K_RETURN)
    assert vault.solved is False
    press(vault, pygame.K_LEFT)
    answer(vault, player, 1)
    assert vault.solved is True and vault.console_state() == "done"


# --- the way out -------------------------------------------------------------------------
def test_the_exit_stays_shut_until_stage_six_is_answered():
    vault, _, player = make_vault()
    solve_to(vault, player, 6)
    settle(vault)
    player.rect.center = vault.exit_zone.center
    vault.update(1 / 60)
    assert vault.is_complete() is False and vault.gate_blocks[2].w > 0


def test_walking_into_the_open_door_finishes_the_vault_once_with_no_extra_points():
    vault, game, player = make_vault()
    solve_to(vault, player, 6)
    answer(vault, player, 1)
    player.rect.center = vault.exit_zone.center
    vault.update(1 / 60)
    assert vault.is_complete() is False                     # the door has barely started to open
    settle(vault)
    score = game.score.get_score()
    vault.update(1 / 60)
    assert vault.is_complete() and vault.complete
    settle(vault, 1.0)
    assert game.score.get_score() == score


def test_a_finished_vault_ignores_input():
    vault, game, player = make_vault()
    solve_to(vault, player, 6)
    answer(vault, player, 1)
    player.rect.center = vault.exit_zone.center
    settle(vault)
    assert vault.is_complete()
    score = game.score.get_score()
    press(vault)
    type_text(vault, "7")
    assert game.score.get_score() == score and vault.command == "" and vault.at_terminal is False


def test_setting_complete_finishes_the_level_like_the_other_floors():
    vault, _, _ = make_vault()
    assert vault.complete is False
    vault.complete = True
    assert vault.is_complete() is True


def test_non_key_events_are_ignored():
    vault, _, player = make_vault()
    player.rect.center = vault.pad_rects()[0].center
    vault.handle_event(pygame.event.Event(pygame.KEYUP, key=E_KEY))
    vault.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(0, 0), button=1))
    assert vault.stage == 1


# --- drawing --------------------------------------------------------------------------------
def render(vault):
    surface = pygame.Surface((960, 640))
    vault.render(surface)
    return surface


def test_every_stage_and_state_renders_and_the_picture_changes():
    vault, _, player = make_vault()
    first = pygame.image.tostring(render(vault), "RGB")
    answer(vault, player, 1)
    vault.update(1 / 60)
    assert pygame.image.tostring(render(vault), "RGB") != first
    for pad in CORRECT_PADS[:5]:
        answer(vault, player, pad)
        render(vault)
    at_console(vault, player)
    type_text(vault, "a")
    render(vault)
    press(vault, pygame.K_RETURN)
    render(vault)
    press(vault, pygame.K_UP)
    answer(vault, player, 1)
    settle(vault, 1.0)
    render(vault)
    assert vault.solved


def test_the_screens_and_monitors_follow_the_stage():
    vault, _, player = make_vault()
    assert [vault.chamber_state(c) for c in range(3)] == ["active", "standby", "standby"]
    solve_to(vault, player, 3)
    assert [vault.chamber_state(c) for c in range(3)] == ["accepted", "active", "standby"]
    assert vault.last_answer[2] == "*"
    solve_to(vault, player, 6)
    answer(vault, player, 1)
    assert [vault.chamber_state(c) for c in range(3)] == ["accepted"] * 3


def test_the_key_hint_and_readout_follow_the_state():
    vault, _, player = make_vault()
    assert "pad" in vault.key_hint() and "press E" in vault.readout()[0][0]
    solve_to(vault, player, 6)
    assert "terminal" in vault.key_hint() and "terminal" in vault.readout()[0][0].lower()
    at_console(vault, player)
    assert "ENTER" in vault.key_hint()
    press(vault, pygame.K_UP)
    answer(vault, player, 1)
    assert "vault door" in vault.key_hint() and "open" in vault.readout()[0][0]


# --- the real game ---------------------------------------------------------------------------
@pytest.fixture
def game():
    from core.game import Game
    g = Game()
    yield g
    g.music.stop()
    pygame.mixer.stop()
    pygame.mixer.set_reserved(0)


def test_the_real_game_uses_the_vault_hall_unless_told_otherwise(monkeypatch):
    from core.game import Game
    monkeypatch.delenv("MEMORY_HEIST_OLD_FINAL_VAULT", raising=False)
    g = Game()
    assert isinstance(g.level_manager.levels["final_vault"], VaultHall)
    g.music.stop()
    for value, cls in (("1", FinalVault), ("0", VaultHall), ("", VaultHall), ("yes", VaultHall)):
        monkeypatch.setenv("MEMORY_HEIST_OLD_FINAL_VAULT", value)
        g = Game()
        assert type(g.level_manager.levels["final_vault"]) is cls, value
        g.music.stop()


def enter_vault(game):
    game.story_enabled = False
    game.level_manager.start("final_vault")
    game._last_level_name = "level5"
    game.state = "playing"
    game.update(1 / 60)
    game._last_level_name = "final_vault"
    return game.level_manager.current


def test_entering_the_vault_puts_the_players_in_the_first_chamber(game):
    game.level_manager.start("final_vault")
    game.state = "playing"
    game._last_level_name = "level5"
    game.update(1 / 60)
    assert game.player.rect.topleft == V.SPAWNS[0] and game.player2.rect.topleft == V.SPAWNS[1]


def test_walking_freezes_while_typing_at_the_vault_terminal(game, monkeypatch):
    vault = enter_vault(game)
    monkeypatch.setattr(pygame.key, "get_pressed",
                        lambda: collections.defaultdict(bool, {game.player.controls["right"]: True}))
    x = game.player.rect.x
    for _ in range(10):
        game.update(1 / 60)
    assert game.player.rect.x > x
    vault.at_terminal = True
    x = game.player.rect.x
    for _ in range(10):
        game.update(1 / 60)
    assert game.player.rect.x == x


def test_a_whole_run_through_the_vault_in_the_real_game_ends_the_run(game):
    vault = enter_vault(game)
    game.score.add(100)
    solve_to(vault, game.player, 6)
    answer(vault, game.player, 1)
    for _ in range(240):
        game.update(1 / 60)
        game.render()
    assert game.state == "playing"
    game.player.rect.center = vault.exit_zone.center
    game.update(1 / 60)
    assert game.state == "win"                              # the story cards are off in this test
