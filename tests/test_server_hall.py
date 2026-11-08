"""Floor 5 - the server hall: geometry, the unchanged Level 5 rules, the terminal, the game."""

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
from levels import hall_decor as H
from levels import level5_control as L5
from levels.level5_control import Level5ControlCenter
from levels.level5_hall import ServerHall
from levels.level5_questions import GATES, QUESTION_POOL, TERMINAL_LINES
from systems.scoring import ScoreTracker
from systems.security import SecurityMeter

E_KEY = pygame.K_e


@pytest.fixture(autouse=True)
def display_init():
    pygame.init()
    pygame.display.set_mode((960, 640))


class FakeAudio:
    def __init__(self):
        self.played = []

    def play(self, name, group="sfx"):
        self.played.append(name)


def make_hall(hints=True, coop=False, seed=1, difficulty="MEDIUM"):
    game = SimpleNamespace(score=ScoreTracker(), security=SecurityMeter(),
                           hints=SimpleNamespace(enabled=hints), coop=coop, player2=None,
                           difficulty={"label": difficulty}, audio=FakeAudio())
    game.score.add(100)
    player = Player(*H.SPAWNS[0])
    if coop:
        game.player2 = Player(*H.SPAWNS[1])
    hall = ServerHall(player=player, game=game, seed=seed)
    return hall, game, player


def key(k, unicode=""):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode=unicode)


def press(hall, k=E_KEY, unicode=""):
    hall.handle_event(key(k, unicode))


def stand_on(player, rect):
    player.rect.center = rect.center


def answer(hall, player, right=True, which=None):
    """Stand on a pad (the right one, or the first wrong one) and press E."""
    index = hall.correct_option if right else (hall.correct_option + 1) % len(hall.options)
    if which is not None:
        index = which
    stand_on(player, hall.pad_rects()[index])
    press(hall)


def solve_questions(hall, player):
    while hall.phase == "questions":
        answer(hall, player)


def to_terminal(**kw):
    hall, game, player = make_hall(**kw)
    solve_questions(hall, player)
    return hall, game, player


def at_console(hall, player):
    player.rect.midbottom = (H.CONSOLE.centerx, H.CONSOLE.y - 1)
    press(hall)


def type_text(hall, text):
    for ch in text:
        press(hall, ord(ch) if ch.isalnum() else pygame.K_MINUS, ch)


def settle(hall, seconds=3.0):
    for _ in range(int(seconds * 60)):
        hall.update(1 / 60)


# --- geometry ---------------------------------------------------------------
def tile_free(hall, col, row):
    return not hall.room_map.blocked(pygame.Rect(col * TILE + 2, row * TILE + 2, 28, 28))


def reachable(hall, start, goal):
    seen, queue = {start}, deque([start])
    while queue:
        c, r = queue.popleft()
        if (c, r) == goal:
            return True
        for nc, nr in ((c + 1, r), (c - 1, r), (c, r + 1), (c, r - 1)):
            if (nc, nr) not in seen and 0 <= nc < 30 and 0 <= nr < 20 and tile_free(hall, nc, nr):
                seen.add((nc, nr))
                queue.append((nc, nr))
    return False


def test_each_chamber_holds_four_pads_in_a_grid_clear_of_walls_props_and_each_other():
    hall, _, _ = make_hall()
    for gate, (first, last) in enumerate(H.CHAMBERS):
        pads = H.pad_rects(gate, 4)
        floor = pygame.Rect(first * TILE, 6 * TILE, (last - first + 1) * TILE, 12 * TILE)
        for i, pad in enumerate(pads):
            assert floor.contains(pad)
            assert not any(pad.colliderect(p) for p in hall.props)
            assert not any(pad.colliderect(q) for q in pads[:i])
            assert not hall.tilemap.collides(pad)
            assert pad.top >= (H.LANE_ROWS[-1] + 1) * TILE and pad.bottom <= H.RACK_ROW * TILE   # under the lane, above the racks
        assert pads[0].centerx < pads[1].centerx and pads[0].centery < pads[2].centery


def test_the_gates_really_gate_the_way_through():
    hall, _, _ = make_hall()
    lane = H.LANE_ROWS[1]
    start = (3, lane)
    assert reachable(hall, start, (9, lane))                       # chamber 1
    assert not reachable(hall, start, (12, lane))                  # gate 1 shut
    hall.gate_blocks[0].size = (0, 0)
    assert reachable(hall, start, (12, lane)) and not reachable(hall, start, (21, lane))
    hall.gate_blocks[1].size = (0, 0)
    assert reachable(hall, start, (21, lane)) and not reachable(hall, start, (29, lane))
    hall.gate_blocks[2].size = (0, 0)
    assert reachable(hall, start, (29, lane))


def test_every_pad_and_the_console_can_be_reached_once_the_gates_are_open():
    hall, _, _ = make_hall()
    for block in hall.gate_blocks:
        block.size = (0, 0)
    start = (3, H.LANE_ROWS[1])
    for gate in range(3):
        for pad in H.pad_rects(gate, 4):
            assert reachable(hall, start, (pad.centerx // TILE, pad.centery // TILE))
    front = (H.CONSOLE.centerx // TILE, H.CONSOLE.y // TILE - 1)
    assert reachable(hall, start, front)


def test_racks_the_console_and_the_code_blocks_are_solid():
    hall, _, _ = make_hall()
    for prop in H.rack_rects() + list(H.CODE_BLOCKS) + [H.CONSOLE]:
        assert hall.room_map.blocked(prop.inflate(-4, -4))
        assert hall.room_map.blocked(pygame.Rect(prop.center, (4, 4)))


def test_props_stand_off_the_lane_and_the_spawns_and_the_console_is_in_chamber_three():
    hall, _, _ = make_hall()
    lane = pygame.Rect(2 * TILE, H.LANE_ROWS[0] * TILE, 26 * TILE, 3 * TILE)
    for prop in hall.props:
        assert not prop.colliderect(lane)
        for spawn in H.SPAWNS:
            assert not prop.colliderect(pygame.Rect(spawn, (32, 32)))
    first, last = H.CHAMBERS[2]
    assert first * TILE <= H.CONSOLE.left and H.CONSOLE.right <= (last + 1) * TILE
    assert H.CONSOLE in hall.props


def test_code_blocks_hang_under_the_screens_and_above_the_lane():
    for block in H.CODE_BLOCKS:
        assert block.top >= H.G.SCREEN_Y + H.G.SCREEN_H + 8
        assert block.bottom <= H.LANE_ROWS[0] * TILE
    assert not H.CODE_BLOCKS[0].colliderect(H.CODE_BLOCKS[1])
    assert H.CODE_BLOCKS[0].left == 2 * TILE and H.CODE_BLOCKS[1].right == 28 * TILE
    assert H.CODE_BLOCKS[1].left - H.CODE_BLOCKS[0].right < 32          # too narrow for a player to slip between


def test_the_two_blocks_between_them_show_every_line_of_the_program():
    from levels.level5_questions import CODE_LINES
    shown = sorted(i for lines in H.BLOCK_LINES for i in lines)
    assert shown == [i for i, line in enumerate(CODE_LINES) if line]
    assert set(TERMINAL_LINES) <= set(H.BLOCK_LINES[1])


def test_the_code_and_its_lines_fit_a_block():
    from levels.level5_questions import CODE_LINES
    font = H.code_font(H.code_size())
    longest = max(CODE_LINES, key=len)
    assert font.size(longest)[0] <= H.CODE_W - 16 - 26
    assert H.code_size() >= 14
    most = max(len(lines) for lines in H.BLOCK_LINES)
    assert 24 + most * H.CODE_LINE_H <= H.CODE_H


def test_every_prompt_fits_its_wall_screen():
    rect = H.screen_rect(0)
    for pool in QUESTION_POOL:
        for q in pool:
            font, lines = H.fit_prompt(q.prompt, rect.w - 16, rect.h - H.SCREEN_PROMPT_TOP - 4)
            assert " ".join(lines) == q.prompt
            assert len(lines) * font.get_linesize() <= rect.h - H.SCREEN_PROMPT_TOP - 4
            assert all(font.size(line)[0] <= rect.w - 16 for line in lines)


def test_every_answer_fits_on_a_pad_in_at_most_two_lines():
    for pool in QUESTION_POOL:
        for q in pool:
            for option in (q.answer, *q.distractors):
                font, lines = H.fit_label(option, H.PAD_W - 12, H.PAD_H - 6)
                assert " ".join(lines) == option and len(lines) <= 2
                assert len(lines) * font.get_linesize() <= H.PAD_H - 6
                assert all(font.size(line)[0] <= H.PAD_W - 12 for line in lines)


def test_an_answer_gets_the_biggest_font_and_wraps_to_two_lines_rather_than_shrinking():
    width, height = H.PAD_W - 12, H.PAD_H - 6
    font, lines = H.fit_label("parameter", width, height)
    assert lines == ["parameter"] and font is H.code_font(17)
    font, lines = H.fit_label("the exception object", width, height)
    assert lines == ["the exception", "object"] and font is H.code_font(17)


def test_the_readout_strip_holds_the_longest_hint_and_explanation_together():
    font = H.ui_font(H.READOUT_FONT_SIZE)
    width = H.READOUT.w - 24 - 70
    for pool in QUESTION_POOL:
        for q in pool:
            lines = H.readout_lines([("HINT: " + q.hint, 1), (q.explanation, 2)], font, width)
            assert len(lines) <= 2 and len(lines) * font.get_linesize() + 6 <= H.READOUT.h
            assert " ".join(t for t, _ in lines) == f"HINT: {q.hint} {q.explanation}"


def test_readout_lines_skip_empty_entries_and_cut_to_the_limit():
    font = H.ui_font(16)
    assert H.readout_lines([("", 1), ("hello", 2)], font, 500) == [("hello", 2)]
    assert len(H.readout_lines([("word " * 80, 1)], font, 200, limit=2)) == 2
    assert H.readout_lines([], font, 500) == []


def test_spawns_are_free_floor_apart_from_each_other():
    hall, _, _ = make_hall()
    a, b = (pygame.Rect(s, (32, 32)) for s in H.SPAWNS)
    assert not hall.room_map.blocked(a) and not hall.room_map.blocked(b) and not a.colliderect(b)
    assert hall.spawn_points == H.SPAWNS


# --- it is still Level 5 underneath ---------------------------------------------
def test_it_is_a_level_5_underneath():
    hall, _, _ = make_hall()
    assert isinstance(hall, Level5ControlCenter)
    assert hall.total_questions == 5 and hall.total_steps == 6
    assert hall.is_complete() is False and hall.movement_locked is False


def test_a_right_pad_scores_and_loads_the_next_question():
    hall, game, player = make_hall()
    before = game.score.get_score()
    first = hall.question
    answer(hall, player)
    assert game.score.get_score() == before + L5.POINTS_PER_QUESTION
    assert hall.question is not first and hall.question_index == 1 and hall.gate_index == 0
    assert hall.feedback.startswith("CORRECT")
    assert hall.message == hall.feedback
    assert "door" in game.audio.played


def test_a_wrong_pad_costs_security_and_score_and_the_pad_is_ruled_out():
    hall, game, player = make_hall()
    before = game.score.get_score()
    answer(hall, player, right=False)
    assert game.security.level == L5.WRONG_SECURITY
    assert game.score.get_score() == before - L5.WRONG_SCORE_PENALTY
    assert (hall.correct_option + 1) % 4 in hall.eliminated
    assert hall.pad_flash and hall.shake.trauma > 0
    assert hall.technician.speech == "Exception raised. Careful."
    assert hall.feedback.startswith("INCORRECT")


def test_a_ruled_out_pad_costs_nothing_the_second_time():
    hall, game, player = make_hall()
    answer(hall, player, right=False)
    level, score = game.security.level, game.score.get_score()
    answer(hall, player, right=False)
    assert game.security.level == level and game.score.get_score() == score
    assert "ruled out" in hall.message


def test_a_wrong_pad_can_be_followed_by_the_right_one():
    hall, _, player = make_hall()
    answer(hall, player, right=False)
    answer(hall, player)
    assert hall.question_index == 1


def test_two_right_answers_open_gate_one_and_move_the_questions_to_chamber_two():
    hall, _, player = make_hall()
    assert hall.gates_passed == 0
    answer(hall, player)
    answer(hall, player)
    assert hall.gate_index == 1 and hall.gates_passed == 1
    assert "GATE 1 OPEN" in hall.feedback
    stand_on(player, hall.pad_rects()[0])
    assert hall.pad_rects()[0].x > H.CHAMBERS[1][0] * TILE


def test_gates_open_gradually_and_stop_blocking_only_when_open():
    hall, _, player = make_hall()
    answer(hall, player)
    answer(hall, player)
    hall.update(1 / 60)
    assert 0 < hall.gate_open[0] < 0.9 and hall.gate_blocks[0].size == (TILE, 3 * TILE)
    for _ in range(14):
        hall.update(1 / 60)
    assert 0.1 < hall.gate_open[0] < 0.9 and hall.gate_blocks[0].size == (TILE, 3 * TILE)   # still a wall
    settle(hall)
    assert hall.gate_open[0] > 0.9 and hall.gate_blocks[0].size == (0, 0)
    assert hall.gate_blocks[1].size == (TILE, 3 * TILE) and hall.gate_blocks[2].w > 0


def test_pressing_off_a_pad_only_gives_a_nudge():
    hall, game, player = make_hall()
    player.rect.center = (3 * TILE, 11 * TILE)
    before = (game.score.get_score(), game.security.level, hall.question_index)
    press(hall)
    assert (game.score.get_score(), game.security.level, hall.question_index) == before
    assert "pad" in hall.message


def test_the_pad_zone_is_the_pad_plus_a_little_slack():
    hall, _, player = make_hall()
    pad = hall.pad_rects()[0]
    player.rect.center = (pad.left - 4, pad.centery)
    assert hall.pad_at(player) == 0
    player.rect.center = (pad.left - 8, pad.centery)
    assert hall.pad_at(player) is None


def test_number_keys_do_not_answer_in_the_hall():
    hall, game, _ = make_hall()
    before = game.score.get_score()
    for k in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
        press(hall, k)
    assert hall.question_index == 0 and game.score.get_score() == before
    assert hall.hint_text == "" and hall.feedback == "" and not hall.eliminated


def test_the_second_player_answers_with_right_shift_and_only_in_co_op():
    hall, game, p1 = make_hall(coop=True)
    p1.rect.center = (3 * TILE, 11 * TILE)
    stand_on(game.player2, hall.pad_rects()[hall.correct_option])
    press(hall, pygame.K_RSHIFT)
    assert hall.question_index == 1
    solo, solo_game, _ = make_hall()
    stand_on(Player(0, 0), solo.pad_rects()[0])
    press(solo, pygame.K_RSHIFT)
    assert solo.question_index == 0


# --- hints ------------------------------------------------------------------------
def test_h_shows_the_hint_and_costs_points_on_that_step_only():
    hall, game, player = make_hall()
    press(hall, pygame.K_h, "h")
    assert hall.hint_text.startswith("HINT:") and hall.message.startswith("Hint revealed")
    before = game.score.get_score()
    answer(hall, player)
    assert game.score.get_score() == before + L5.POINTS_PER_QUESTION - L5.HINT_PENALTY
    before = game.score.get_score()
    answer(hall, player)
    assert game.score.get_score() == before + L5.POINTS_PER_QUESTION


def test_tab_is_a_hint_too_and_hard_costs_more():
    hall, game, player = make_hall(difficulty="HARD")
    press(hall, pygame.K_TAB)
    assert hall.hint_text and hall.hint_penalty() == L5.HINT_PENALTY_HARD
    before = game.score.get_score()
    answer(hall, player)
    assert game.score.get_score() == before + L5.POINTS_PER_QUESTION - L5.HINT_PENALTY_HARD


def test_hints_can_be_switched_off():
    hall, _, _ = make_hall(hints=False)
    press(hall, pygame.K_h, "h")
    assert hall.hint_text == "" and "disabled" in hall.message


# --- the terminal --------------------------------------------------------------------
def test_the_last_question_wakes_the_terminal_and_clears_the_pads():
    hall, _, _ = to_terminal()
    assert hall.phase == "terminal" and hall.pad_rects() == []
    assert hall.console_state() == "ready" and hall.gates_passed == 2
    assert "Terminal unlocked" in hall.feedback


def test_the_console_is_locked_until_the_questions_are_done():
    hall, _, player = make_hall()
    assert hall.console_state() == "locked"
    player.rect.midbottom = (H.CONSOLE.centerx, H.CONSOLE.y - 1)
    press(hall)
    assert hall.at_terminal is False


def test_e_at_the_console_logs_in_and_freezes_walking():
    hall, _, player = to_terminal()
    assert hall.movement_locked is False
    at_console(hall, player)
    assert hall.at_terminal is True and hall.movement_locked is True
    assert hall.console_state() == "active"


def test_e_away_from_the_console_does_not_log_in():
    hall, _, player = to_terminal()
    player.rect.center = (3 * TILE, 11 * TILE)
    press(hall)
    assert hall.at_terminal is False and "terminal" in hall.message.lower()


def test_the_e_you_type_is_text_not_a_second_log_in_or_a_walk_away():
    hall, _, player = to_terminal()
    at_console(hall, player)
    type_text(hall, "1e3")
    assert hall.command == "1e3" and hall.at_terminal is True


def test_an_arrow_key_steps_away_and_the_entry_is_kept():
    hall, _, player = to_terminal()
    at_console(hall, player)
    type_text(hall, "42")
    for k in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
        hall.at_terminal = True
        press(hall, k)
        assert hall.at_terminal is False and hall.command == "42"
    assert hall.movement_locked is False


def test_letters_raise_a_real_value_error_that_is_caught():
    hall, game, player = to_terminal()
    at_console(hall, player)
    type_text(hall, "abc")
    before = game.security.level
    press(hall, pygame.K_RETURN)
    assert hall.command_result.startswith("Caught:") and "invalid literal" in hall.command_result
    assert game.security.level - before == L5.INVALID_INPUT_SECURITY
    assert hall.at_terminal is True and hall.phase == "terminal"
    assert hall.command == ""


def test_a_level_below_five_is_denied_by_the_function_and_caught():
    hall, game, player = to_terminal()
    at_console(hall, player)
    type_text(hall, "3")
    level, score = game.security.level, game.score.get_score()
    press(hall, pygame.K_RETURN)
    assert game.security.level - level == L5.DENIED_SECURITY
    assert score - game.score.get_score() == L5.DENIED_SCORE_PENALTY
    assert "Access denied" in hall.command_result and hall.phase == "terminal"
    assert hall.shake.trauma > 0 and hall.technician.speech == "Exception raised. Careful."


def test_an_empty_entry_asks_for_input_and_stays_at_the_terminal():
    hall, _, player = to_terminal()
    at_console(hall, player)
    press(hall, pygame.K_RETURN)
    assert "access level" in hall.feedback and hall.at_terminal is True


def test_backspace_edits_and_symbols_are_not_typed():
    hall, _, player = to_terminal()
    at_console(hall, player)
    type_text(hall, "12")
    press(hall, pygame.K_BACKSPACE)
    press(hall, pygame.K_PERIOD, ".")
    assert hall.command == "1"


def test_tab_at_the_terminal_gives_its_hint():
    hall, game, player = to_terminal()
    at_console(hall, player)
    press(hall, pygame.K_TAB)
    assert hall.hint_text == "HINT: " + L5.TERMINAL_HINT
    type_text(hall, "7")
    before = game.score.get_score()
    press(hall, pygame.K_RETURN)
    gained = game.score.get_score() - before
    assert gained == L5.POINTS_TERMINAL - L5.HINT_PENALTY + L5.POINTS_COMPLETION_BONUS


def test_a_level_of_five_or_more_restores_the_control_center_and_opens_the_exit():
    hall, game, player = to_terminal(hints=True)
    at_console(hall, player)
    press(hall, pygame.K_TAB)
    assert hall.hint_text
    type_text(hall, "7")
    before = game.score.get_score()
    press(hall, pygame.K_RETURN)
    assert hall.phase == "done" and hall.at_terminal is False and hall.movement_locked is False
    assert hall.command_result == "MASTER ACCESS" and hall.console_state() == "done"
    assert game.score.get_score() - before == L5.POINTS_TERMINAL - L5.HINT_PENALTY + L5.POINTS_COMPLETION_BONUS
    assert hall.gates_passed == 3 and hall.hint_text == ""
    assert hall.is_complete() is False                 # you still have to walk out


def test_complete_means_walked_out_so_setting_it_finishes_the_level():
    hall, _, player = to_terminal()
    assert hall.complete is False
    at_console(hall, player)
    type_text(hall, "7")
    press(hall, pygame.K_RETURN)
    assert hall.complete is False and hall.is_complete() is False     # solved is not finished
    hall.complete = True                                              # what the tests' finish_level does
    assert hall.is_complete() is True


def test_the_exit_stays_shut_until_the_terminal_accepts_you():
    hall, _, player = to_terminal()
    settle(hall)
    player.rect.center = hall.exit_zone.center
    hall.update(1 / 60)
    assert hall.is_complete() is False and hall.gate_open[2] < 0.1
    assert hall.gate_blocks[2].w > 0


def test_walking_into_the_open_exit_finishes_the_level_once_with_no_extra_points():
    hall, game, player = to_terminal()
    at_console(hall, player)
    type_text(hall, "5")
    press(hall, pygame.K_RETURN)
    player.rect.center = hall.exit_zone.center
    hall.update(1 / 60)
    assert hall.is_complete() is False                 # the door has barely started to open
    settle(hall)
    assert hall.gate_blocks[2].size == (0, 0)
    score = game.score.get_score()
    hall.update(1 / 60)
    assert hall.is_complete() is True
    settle(hall, 1.0)
    assert game.score.get_score() == score


def test_a_finished_level_ignores_input():
    hall, game, player = to_terminal()
    at_console(hall, player)
    type_text(hall, "9")
    press(hall, pygame.K_RETURN)
    player.rect.center = hall.exit_zone.center
    settle(hall)
    assert hall.is_complete()
    score = game.score.get_score()
    press(hall, pygame.K_e)
    type_text(hall, "7")
    assert game.score.get_score() == score and hall.command == ""


def test_a_whole_run_scores_the_same_as_the_old_level_5():
    hall, game, player = make_hall()
    before = game.score.get_score()
    solve_questions(hall, player)
    at_console(hall, player)
    type_text(hall, "6")
    press(hall, pygame.K_RETURN)
    expected = 5 * L5.POINTS_PER_QUESTION + L5.POINTS_TERMINAL + L5.POINTS_COMPLETION_BONUS
    assert game.score.get_score() - before == expected
    assert game.security.level == 0


def test_gates_passed_climbs_one_gate_at_a_time():
    hall, _, player = make_hall()
    seen = [hall.gates_passed]
    while hall.phase == "questions":
        answer(hall, player)
        seen.append(hall.gates_passed)
    assert seen == [0, 0, 1, 1, 2, 2]
    at_console(hall, player)
    type_text(hall, "8")
    press(hall, pygame.K_RETURN)
    assert hall.gates_passed == 3


def test_the_other_players_answers_and_log_in_work_too():
    hall, game, p1 = make_hall(coop=True)
    solve_questions(hall, p1)
    game.player2.rect.midbottom = (H.CONSOLE.centerx, H.CONSOLE.y - 1)
    p1.rect.center = (3 * TILE, 11 * TILE)
    press(hall, pygame.K_RSHIFT)
    assert hall.at_terminal is True


def test_non_key_events_are_ignored():
    hall, game, player = make_hall()
    stand_on(player, hall.pad_rects()[hall.correct_option])
    hall.handle_event(pygame.event.Event(pygame.KEYUP, key=E_KEY))
    hall.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, pos=(0, 0), button=1))
    assert hall.question_index == 0


# --- the same run is the same questions as the old level ------------------------------------
def test_the_same_seed_asks_the_same_questions_as_the_old_level():
    hall, _, _ = make_hall(seed=9)
    old = Level5ControlCenter(seed=9)
    assert hall.gate_questions == old.gate_questions and hall.options == old.options


# --- drawing --------------------------------------------------------------------------------
def render(hall, size=(960, 640)):
    surface = pygame.Surface(size)
    hall.render(surface)
    return surface


def test_every_phase_renders_and_the_picture_changes():
    hall, game, player = make_hall()
    first = pygame.image.tostring(render(hall), "RGB")
    answer(hall, player, right=False)
    press(hall, pygame.K_h, "h")
    hall.update(1 / 60)
    assert pygame.image.tostring(render(hall), "RGB") != first
    solve_questions(hall, player)
    ready = pygame.image.tostring(render(hall), "RGB")
    at_console(hall, player)
    type_text(hall, "ab")
    typing = pygame.image.tostring(render(hall), "RGB")
    assert typing != ready
    type_text(hall, "1")
    press(hall, pygame.K_RETURN)
    press(hall, pygame.K_TAB)
    render(hall)
    press(hall, pygame.K_BACKSPACE)
    type_text(hall, "7")
    press(hall, pygame.K_RETURN)
    settle(hall, 1.0)
    render(hall)
    assert hall.phase == "done"


def test_the_terminal_window_is_drawn_only_while_someone_is_typing():
    hall, _, player = to_terminal()
    before = pygame.image.tostring(render(hall), "RGB")
    at_console(hall, player)
    assert pygame.image.tostring(render(hall), "RGB") != before
    press(hall, pygame.K_LEFT)
    render(hall)                                       # stepping away redraws without the window


def test_the_active_screen_shows_the_question_and_passed_screens_the_answer():
    hall, _, player = make_hall()
    answer(hall, player)
    answer(hall, player)
    assert hall._screen_state(0) == "accepted" and hall._screen_state(1) == "active"
    assert hall._screen_state(2) == "standby"
    assert hall.last_answer[0]
    solve_questions(hall, player)
    assert [hall._screen_state(g) for g in range(3)] == ["accepted"] * 3


def test_the_right_lines_of_the_program_are_lit_for_each_question_and_the_terminal():
    hall, _, player = make_hall()
    assert hall._highlighted_lines() == set(hall.question.highlight)
    solve_questions(hall, player)
    assert hall._highlighted_lines() == set(TERMINAL_LINES)


def test_the_key_hint_follows_the_phase():
    hall, _, player = make_hall()
    assert "pad" in hall.key_hint()
    solve_questions(hall, player)
    assert "terminal" in hall.key_hint()
    at_console(hall, player)
    assert "ENTER" in hall.key_hint()
    type_text(hall, "7")
    press(hall, pygame.K_RETURN)
    assert "exit" in hall.key_hint()


def test_the_readout_shows_a_tip_then_the_hint_and_the_explanation():
    hall, _, player = make_hall()
    assert "pad" in hall.readout()[0][0].lower()
    press(hall, pygame.K_h, "h")
    assert hall.readout()[0][0].startswith("HINT:")
    answer(hall, player)
    assert any(text for text, _ in hall.readout())
    solve_questions(hall, player)
    assert len(hall.readout()) <= 2


def test_the_technician_walks_the_south_floor_and_never_blocks_anything():
    hall, _, _ = make_hall()
    assert hall.npcs == [hall.technician]
    for _ in range(600):
        hall.update(1 / 60)
    assert hall.technician.rect.y == 16 * TILE


# --- the real game ---------------------------------------------------------------------------
@pytest.fixture
def game():
    from core.game import Game
    g = Game()
    yield g
    g.music.stop()
    pygame.mixer.stop()
    pygame.mixer.set_reserved(0)


def test_the_real_game_uses_the_server_hall_unless_told_otherwise(monkeypatch):
    from core.game import Game
    monkeypatch.delenv("MEMORY_HEIST_OLD_LEVEL5", raising=False)
    g = Game()
    assert isinstance(g.level_manager.levels["level5"], ServerHall)
    g.music.stop()
    for value, cls in (("1", Level5ControlCenter), ("0", ServerHall), ("", ServerHall), ("yes", ServerHall)):
        monkeypatch.setenv("MEMORY_HEIST_OLD_LEVEL5", value)
        g = Game()
        assert type(g.level_manager.levels["level5"]) is cls, value
        g.music.stop()


def hold(monkeypatch, *keys):
    monkeypatch.setattr(pygame.key, "get_pressed", lambda: collections.defaultdict(bool, {k: True for k in keys}))


def enter_level_5(game):
    game.story_enabled = False
    game.level_manager.start("level5")
    game._last_level_name = "level4"                  # so the players are put at the spawn points
    game.state = "playing"
    game.update(1 / 60)
    game._last_level_name = "level5"
    return game.level_manager.current


def test_entering_level_5_in_the_real_game_puts_the_players_in_the_first_chamber(game):
    game.level_manager.start("level5")
    game.state = "playing"
    game._last_level_name = "level4"
    game.update(1 / 60)
    assert game.player.rect.topleft == H.SPAWNS[0] and game.player2.rect.topleft == H.SPAWNS[1]
    assert game.level_manager.current_name == "level5"


def test_walking_works_normally_and_freezes_while_typing_at_the_terminal(game, monkeypatch):
    hall = enter_level_5(game)
    right = game.player.controls["right"]
    hold(monkeypatch, right)
    x = game.player.rect.x
    for _ in range(10):
        game.update(1 / 60)
    assert game.player.rect.x > x
    hall.at_terminal = True
    x = game.player.rect.x
    for _ in range(10):
        game.update(1 / 60)
    assert game.player.rect.x == x and game.player.moving is False
    hall.at_terminal = False
    for _ in range(10):
        game.update(1 / 60)
    assert game.player.rect.x > x


def test_a_level_without_the_lock_flag_is_never_frozen(game, monkeypatch):
    hall = enter_level_5(game)
    hold(monkeypatch, game.player.controls["right"])
    game.level_manager.current = SimpleNamespace(room_map=hall.room_map, update=lambda dt: None,
                                                 is_complete=lambda: False, spawn_points=None)
    x = game.player.rect.x
    for _ in range(10):
        game.update(1 / 60)
    assert game.player.rect.x > x


def test_a_whole_run_through_floor_5_in_the_real_game_reaches_the_final_vault(game):
    hall = enter_level_5(game)
    game.score.add(100)
    solve_questions(hall, game.player)
    for _ in range(30):
        game.update(1 / 60)
    at_console(hall, game.player)
    type_text(hall, "7")
    press(hall, pygame.K_RETURN)
    for _ in range(240):
        game.update(1 / 60)
        game.render()
    assert game.state == "playing" and game.level_manager.current_name == "level5"
    game.player.rect.center = hall.exit_zone.center
    game.update(1 / 60)
    assert game.level_manager.current_name == "final_vault"


def test_radio_for_level_5_still_follows_the_gates(game):
    from core.comms import line_for
    speaker, line = line_for("level5", "enter")
    assert speaker == "Echo" and line
