"""Tests for the three-gate Level 5 (levels/level5_control.py)."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from levels import level5_control as l5
from levels.level5_control import AccessDenied, Level5ControlCenter
from levels.level5_questions import (
    CODE_LINES,
    GATES,
    QUESTION_POOL,
    validate_pool,
)


# ---------------------------------------------------------------------
# Test helpers
# ---------------------------------------------------------------------
class FakeScore:
    def __init__(self):
        self.total = 0

    def add(self, amount):
        self.total += amount

    def penalize(self, amount):
        self.total -= amount


class FakeSecurity:
    def __init__(self):
        self.total = 0

    def increase(self, amount=20):
        self.total += amount


class FakeHints:
    def __init__(self, enabled=True):
        self.enabled = enabled


class FakeGame:
    def __init__(self, difficulty="MEDIUM", hints_enabled=True):
        self.score = FakeScore()
        self.security = FakeSecurity()
        self.hints = FakeHints(hints_enabled)
        self.difficulty = {"label": difficulty}


def key(k, unicode=""):
    return pygame.event.Event(pygame.KEYDOWN, key=k, unicode=unicode)


ANSWER_KEYS = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]


def press_correct(level):
    level.handle_event(key(ANSWER_KEYS[level.correct_option]))


def press_wrong(level):
    for i in range(4):
        if i != level.correct_option and i not in level.eliminated:
            level.handle_event(key(ANSWER_KEYS[i]))
            return i
    raise AssertionError("no wrong option left")


def type_text(level, text):
    for ch in text:
        level.handle_event(key(pygame.K_a, ch))


def submit(level):
    level.handle_event(key(pygame.K_RETURN))


def solve_questions(level):
    for _ in range(level.total_questions):
        press_correct(level)


def make_level(game=None, **kwargs):
    kwargs.setdefault("seed", 7)
    kwargs.setdefault("finish_delay", 0)
    return Level5ControlCenter(game=game, **kwargs)


@pytest.fixture
def game():
    return FakeGame()


@pytest.fixture
def level(game):
    return make_level(game)


# ---------------------------------------------------------------------
# Question pool
# ---------------------------------------------------------------------
def test_question_pool_is_valid():
    validate_pool()


def test_pool_has_three_gates_with_spare_questions():
    assert len(GATES) == 3
    for gate, pool in zip(GATES, QUESTION_POOL):
        assert len(pool) > gate["count"]


def test_every_question_highlights_real_code_lines():
    for pool in QUESTION_POOL:
        for q in pool:
            for index in q.highlight:
                assert CODE_LINES[index].strip()


# ---------------------------------------------------------------------
# Setup, shuffling and the pool
# ---------------------------------------------------------------------
def test_starts_at_gate_one(level):
    assert level.gate_index == 0
    assert level.phase == "questions"
    assert not level.complete
    assert not level.is_complete()
    assert level.current_step == 1
    assert level.total_steps == 6


def test_questions_per_gate_match_design(level):
    assert [len(q) for q in level.gate_questions] == [2, 2, 1]


def test_questions_are_unique_within_a_run(level):
    for gate_qs in level.gate_questions:
        assert len({q.prompt for q in gate_qs}) == len(gate_qs)


def test_each_question_has_four_options_with_answer(level):
    assert len(level.options) == 4
    assert level.options[level.correct_option] == level.question.answer


def test_same_seed_gives_same_run():
    a, b = make_level(seed=11), make_level(seed=11)
    assert a.options == b.options
    assert [[q.prompt for q in g] for g in a.gate_questions] == [
        [q.prompt for q in g] for g in b.gate_questions
    ]


def test_runs_vary_across_seeds():
    layouts = set()
    for seed in range(30):
        lvl = make_level(seed=seed)
        layouts.add((lvl.question.prompt, tuple(lvl.options)))
    assert len(layouts) > 5


def test_correct_answer_position_is_shuffled():
    positions = {make_level(seed=s).correct_option for s in range(40)}
    assert len(positions) > 1


# ---------------------------------------------------------------------
# Answering and gate flow
# ---------------------------------------------------------------------
def test_correct_answer_scores_and_advances(level, game):
    first = level.question
    press_correct(level)
    assert game.score.total == l5.POINTS_PER_QUESTION
    assert level.question is not first
    assert level.question_index == 1
    assert level.explanation == first.explanation
    assert level.current_step == 2


def test_wrong_answer_penalizes_and_eliminates(level, game):
    wrong = press_wrong(level)
    assert game.security.total == l5.WRONG_SECURITY
    assert game.score.total == -l5.WRONG_SCORE_PENALTY
    assert wrong in level.eliminated
    assert level.question_index == 0
    assert "INCORRECT" in level.feedback


def test_eliminated_option_cannot_be_penalized_twice(level, game):
    wrong = press_wrong(level)
    level.handle_event(key(ANSWER_KEYS[wrong]))
    assert game.security.total == l5.WRONG_SECURITY


def test_wrong_answer_can_be_retried(level):
    press_wrong(level)
    press_correct(level)
    assert level.question_index == 1


def test_gate_one_opens_after_two_questions(level):
    assert level.gates[0].state == "locked"
    press_correct(level)
    assert level.gates[0].state == "locked"
    press_correct(level)
    assert level.gates[0].state == "unlocking"
    assert level.gate_index == 1
    assert "GATE 1 OPEN" in level.feedback


def test_gates_finish_opening_after_update(level):
    solve_questions(level)
    for _ in range(40):
        level.update(0.05)
    assert [g.state for g in level.gates[:2]] == ["open", "open"]
    assert level.gates[2].state == "locked"


def test_gate_two_then_gate_three_questions(level):
    press_correct(level)
    press_correct(level)
    assert level.gate_index == 1
    press_correct(level)
    press_correct(level)
    assert level.gate_index == 2
    assert level.phase == "questions"
    assert len(level.gate_questions[2]) == 1


def test_terminal_unlocks_after_last_question(level):
    solve_questions(level)
    assert level.phase == "terminal"
    assert level.terminal_unlocked
    assert not level.complete
    assert level.gates[2].state == "locked"
    assert level.current_step == 6


def test_answer_keys_do_nothing_in_terminal(level):
    solve_questions(level)
    level.handle_event(key(pygame.K_1, "1"))
    assert level.command == "1"
    assert level.phase == "terminal"


def test_progress_counts_all_six_steps(level):
    solve_questions(level)
    type_text(level, "5")
    submit(level)
    assert level._steps_done == 6
    assert level.current_step == 6


# ---------------------------------------------------------------------
# Terminal: real try/except
# ---------------------------------------------------------------------
def to_terminal(game=None):
    lvl = make_level(game)
    solve_questions(lvl)
    return lvl


def test_unlock_vault_raises_below_five():
    lvl = make_level()
    with pytest.raises(ValueError):
        lvl._unlock_vault(4)
    with pytest.raises(AccessDenied):
        lvl._unlock_vault(-1)
    assert lvl._unlock_vault(5) == "MASTER ACCESS"
    assert lvl._unlock_vault(99) == "MASTER ACCESS"


def test_access_denied_is_a_value_error():
    assert issubclass(AccessDenied, ValueError)


def test_terminal_success_completes_level():
    game = FakeGame()
    lvl = to_terminal(game)
    type_text(lvl, "5")
    submit(lvl)
    assert lvl.complete
    assert lvl.phase == "done"
    assert lvl.command_result == "MASTER ACCESS"
    assert lvl.gates[2].state == "unlocking"
    assert "RESTORED" in lvl.feedback


def test_full_playthrough_score():
    game = FakeGame()
    lvl = to_terminal(game)
    type_text(lvl, "5")
    submit(lvl)
    expected = (
        lvl.total_questions * l5.POINTS_PER_QUESTION
        + l5.POINTS_TERMINAL
        + l5.POINTS_COMPLETION_BONUS
    )
    assert game.score.total == expected == 350


def test_low_level_raises_and_is_caught():
    game = FakeGame()
    lvl = to_terminal(game)
    type_text(lvl, "3")
    submit(lvl)
    assert not lvl.complete
    assert lvl.command_result == "Caught: Access denied"
    assert "Access denied" in lvl.feedback
    assert game.security.total == l5.DENIED_SECURITY
    assert game.score.total == (
        lvl.total_questions * l5.POINTS_PER_QUESTION
        - l5.DENIED_SCORE_PENALTY
    )


def test_letters_trigger_real_int_value_error():
    game = FakeGame()
    lvl = to_terminal(game)
    before = game.score.total
    type_text(lvl, "abc")
    submit(lvl)
    assert not lvl.complete
    assert "invalid literal" in lvl.command_result
    assert "int()" in lvl.feedback
    assert game.security.total == l5.INVALID_INPUT_SECURITY
    assert game.score.total == before


def test_negative_number_is_access_denied():
    lvl = to_terminal()
    type_text(lvl, "-3")
    submit(lvl)
    assert lvl.command_result == "Caught: Access denied"


def test_decimal_point_is_not_accepted():
    lvl = to_terminal()
    for ch in "5.5":
        lvl.handle_event(key(pygame.K_5, ch))
    # "." is not accepted, so the entry becomes "55" - that is valid.
    assert lvl.command == "55"


def test_empty_entry_asks_for_input():
    game = FakeGame()
    lvl = to_terminal(game)
    submit(lvl)
    assert "first" in lvl.feedback
    assert not lvl.complete
    assert game.security.total == 0


def test_command_cleared_after_each_submit():
    lvl = to_terminal()
    type_text(lvl, "2")
    submit(lvl)
    assert lvl.command == ""
    type_text(lvl, "x")
    submit(lvl)
    assert lvl.command == ""


def test_terminal_accepts_letters_and_limits_length():
    lvl = to_terminal()
    type_text(lvl, "abcdefghijkl")
    assert lvl.command == "abcdefgh"
    assert len(lvl.command) == l5.MAX_COMMAND_LENGTH


def test_terminal_rejects_symbols_and_non_ascii():
    lvl = to_terminal()
    for ch in ("!", " ", "é", "\n"):
        lvl.handle_event(key(pygame.K_a, ch))
    assert lvl.command == ""


def test_terminal_backspace():
    lvl = to_terminal()
    type_text(lvl, "ab")
    lvl.handle_event(key(pygame.K_BACKSPACE))
    assert lvl.command == "a"
    lvl.handle_event(key(pygame.K_BACKSPACE))
    lvl.handle_event(key(pygame.K_BACKSPACE))
    assert lvl.command == ""


def test_h_is_typed_in_terminal_not_a_hint():
    game = FakeGame()
    lvl = to_terminal(game)
    lvl.handle_event(key(pygame.K_h, "h"))
    assert lvl.command == "h"
    assert not lvl.hint_text


def test_completion_awarded_only_once():
    game = FakeGame()
    lvl = to_terminal(game)
    type_text(lvl, "5")
    submit(lvl)
    total = game.score.total
    lvl._terminal_success("MASTER ACCESS")
    assert game.score.total == total


# ---------------------------------------------------------------------
# Hints and difficulty
# ---------------------------------------------------------------------
def test_hint_shows_text_and_marks_used(level):
    level.handle_event(key(pygame.K_h))
    assert level.hint_used
    assert level.hint_text == f"HINT: {level.question.hint}"
    assert "Hint revealed" in level.feedback


def test_tab_also_gives_hint(level):
    level.handle_event(key(pygame.K_TAB))
    assert level.hint_used


def test_hint_reduces_points_for_that_question_only(level, game):
    level.handle_event(key(pygame.K_h))
    press_correct(level)
    assert game.score.total == l5.POINTS_PER_QUESTION - l5.HINT_PENALTY
    assert not level.hint_used
    assert level.hint_text == ""
    press_correct(level)
    assert game.score.total == (
        2 * l5.POINTS_PER_QUESTION - l5.HINT_PENALTY
    )


def test_hint_penalty_not_charged_twice(level, game):
    level.handle_event(key(pygame.K_h))
    level.handle_event(key(pygame.K_h))
    press_correct(level)
    assert game.score.total == l5.POINTS_PER_QUESTION - l5.HINT_PENALTY


def test_hint_penalty_is_higher_on_hard():
    lvl = make_level(FakeGame(difficulty="HARD"))
    assert lvl.hint_penalty() == l5.HINT_PENALTY_HARD
    assert make_level(FakeGame(difficulty="EASY")).hint_penalty() == l5.HINT_PENALTY
    assert make_level(FakeGame(difficulty="MEDIUM")).hint_penalty() == l5.HINT_PENALTY


def test_hard_penalty_applied_to_score():
    game = FakeGame(difficulty="HARD")
    lvl = make_level(game)
    lvl.handle_event(key(pygame.K_h))
    press_correct(lvl)
    assert game.score.total == l5.POINTS_PER_QUESTION - l5.HINT_PENALTY_HARD


def test_hints_disabled_when_game_disables_them():
    game = FakeGame(difficulty="HARD", hints_enabled=False)
    lvl = make_level(game)
    lvl.handle_event(key(pygame.K_h))
    assert not lvl.hint_used
    assert not lvl.hint_text
    assert "disabled" in lvl.feedback
    press_correct(lvl)
    assert game.score.total == l5.POINTS_PER_QUESTION


def test_terminal_hint_via_tab_costs_points():
    game = FakeGame()
    lvl = to_terminal(game)
    lvl.handle_event(key(pygame.K_TAB))
    assert lvl.hint_text == f"HINT: {l5.TERMINAL_HINT}"
    before = game.score.total
    type_text(lvl, "5")
    submit(lvl)
    gained = game.score.total - before
    assert gained == (
        l5.POINTS_TERMINAL - l5.HINT_PENALTY + l5.POINTS_COMPLETION_BONUS
    )


def test_hint_never_goes_below_zero_points():
    game = FakeGame()
    lvl = make_level(game)
    lvl.hint_used = True
    assert lvl._award(5) == 0


# ---------------------------------------------------------------------
# Finish animation and completion
# ---------------------------------------------------------------------
def test_is_complete_waits_for_finish_delay():
    lvl = make_level(finish_delay=1.0)
    solve_questions(lvl)
    type_text(lvl, "5")
    submit(lvl)
    assert lvl.complete
    assert not lvl.is_complete()
    lvl.update(0.5)
    assert not lvl.is_complete()
    lvl.update(0.6)
    assert lvl.is_complete()


def test_zero_delay_completes_immediately():
    lvl = make_level(finish_delay=0)
    solve_questions(lvl)
    type_text(lvl, "5")
    submit(lvl)
    assert lvl.is_complete()


def test_input_ignored_after_complete():
    game = FakeGame()
    lvl = to_terminal(game)
    type_text(lvl, "5")
    submit(lvl)
    total = game.score.total
    lvl.handle_event(key(pygame.K_1, "1"))
    lvl.handle_event(key(pygame.K_h))
    submit(lvl)
    assert game.score.total == total


def test_non_keydown_events_ignored(level):
    level.handle_event(pygame.event.Event(pygame.KEYUP, key=pygame.K_1))
    assert level.question_index == 0
    assert level.selected_option is None


def test_works_without_a_game():
    lvl = make_level(None)
    press_wrong(lvl)
    solve_questions(lvl)
    type_text(lvl, "x")
    submit(lvl)
    type_text(lvl, "5")
    submit(lvl)
    assert lvl.is_complete()


def test_drone_moves_toward_open_gates(level):
    start = level._token_x
    solve_questions(level)
    for _ in range(120):
        level.update(0.05)
    assert level._token_x > start
    type_text(level, "5")
    submit(level)
    for _ in range(200):
        level.update(0.05)
    assert level._token_x == pytest.approx(l5.TOKEN_VAULT_X, abs=2)


# ---------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------
@pytest.fixture(scope="module")
def surface():
    pygame.init()
    return pygame.display.set_mode((960, 640))


def test_render_every_phase_without_crashing(surface):
    lvl = make_level(FakeGame())
    lvl.render(surface)                      # gate 1
    press_wrong(lvl)
    lvl.handle_event(key(pygame.K_h))
    lvl.render(surface)                      # wrong + hint
    for _ in range(lvl.total_questions):
        press_correct(lvl)
        lvl.update(0.1)
        lvl.render(surface)                  # gates 1-3
    lvl.render(surface)                      # terminal
    type_text(lvl, "abc")
    submit(lvl)
    lvl.render(surface)                      # error output
    type_text(lvl, "5")
    submit(lvl)
    lvl.update(0.3)
    lvl.render(surface)                      # done


def test_render_with_long_text_does_not_crash(surface):
    lvl = make_level(FakeGame())
    lvl.feedback = "word " * 80
    lvl.hint_text = "hint " * 80
    lvl.explanation = "expl " * 80
    lvl.render(surface)


def test_fonts_are_created_once(surface):
    lvl = make_level()
    lvl.render(surface)
    fonts = lvl._fonts
    lvl.render(surface)
    assert lvl._fonts is fonts


def test_code_fits_inside_panel(surface):
    lvl = make_level()
    fonts = lvl._get_fonts()
    longest = max(CODE_LINES, key=len)
    assert fonts["mono"].size(longest)[0] <= l5.CODE_PANEL.width - 46 - 10


def test_wrap_respects_width(surface):
    lvl = make_level()
    font = lvl._get_fonts()["text"]
    lines = lvl._wrap(font, "alpha beta gamma delta epsilon zeta eta theta", 120)
    assert len(lines) > 1
    assert all(font.size(line)[0] <= 120 for line in lines)
    assert lvl._wrap(font, "", 120) == []


@pytest.mark.parametrize("seed", range(30))
def test_every_seed_is_fully_playable(seed):
    game = FakeGame()
    lvl = make_level(game, seed=seed)
    solve_questions(lvl)
    type_text(lvl, "5")
    submit(lvl)
    assert lvl.is_complete()
    assert game.score.total == 350
    assert game.security.total == 0