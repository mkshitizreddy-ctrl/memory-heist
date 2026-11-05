"""systems/achievements.py: stats and badges."""

import json
import os

import pytest

from systems import achievements as A


def result(**over):
    data = dict(mistakes=3, time_left=100, run_seconds=900, difficulty="medium",
                coop=False, continued=False)
    data.update(over)
    return data


@pytest.fixture
def path(tmp_path):
    return str(tmp_path / "saves" / "stats.json")


def test_every_win_earns_first_escape_and_nothing_else_by_default():
    assert A.earned_badges(result(), wins=1) == ["escape"]


def test_flawless_needs_zero_mistakes():
    assert "flawless" in A.earned_badges(result(mistakes=0), 1)
    assert "flawless" not in A.earned_badges(result(mistakes=1), 1)


def test_speed_runner_needs_half_the_clock_left():
    assert "speed" in A.earned_badges(result(time_left=450), 1)
    assert "speed" not in A.earned_badges(result(time_left=449), 1)
    assert "speed" not in A.earned_badges(result(time_left=10, run_seconds=0), 1)


def test_co_op_and_hard_badges():
    assert "duo" in A.earned_badges(result(coop=True), 1)
    assert "duo" not in A.earned_badges(result(), 1)
    assert "nerves" in A.earned_badges(result(difficulty="hard"), 1)
    assert "nerves" not in A.earned_badges(result(difficulty="easy"), 1)


def test_veteran_arrives_on_the_third_win():
    assert "veteran" not in A.earned_badges(result(), A.VETERAN_WINS - 1)
    assert "veteran" in A.earned_badges(result(), A.VETERAN_WINS)


def test_a_continued_run_is_never_flawless_or_fast():
    got = A.earned_badges(result(mistakes=0, time_left=800, continued=True), 1)
    assert "flawless" not in got and "speed" not in got and "escape" in got


def test_badges_come_back_in_display_order():
    got = A.earned_badges(result(mistakes=0, time_left=800, coop=True, difficulty="hard"), 5)
    assert got == list(A.BADGE_IDS)


def test_recording_wins_and_losses_persists(path):
    s = A.Stats(path)
    earned, new = s.record_win(1500, result(mistakes=0, coop=True))
    assert earned == ["escape", "flawless", "duo"] and new == earned
    s.record_loss()
    again = A.Stats(path)
    assert (again.wins, again.losses, again.best_score) == (1, 1, 1500)
    assert again.badges == ["escape", "flawless", "duo"]


def test_only_unseen_badges_are_new(path):
    s = A.Stats(path)
    s.record_win(100, result(mistakes=0))
    earned, new = s.record_win(200, result(mistakes=0, coop=True))
    assert earned == ["escape", "flawless", "duo"] and new == ["duo"]


def test_bests_only_go_up(path):
    s = A.Stats(path)
    s.record_win(900, result(time_left=300))
    s.record_win(400, result(time_left=100))
    assert s.best_score == 900 and s.best_time_left == 300


@pytest.mark.parametrize("text", ["", "junk", "[]", "7", "null"])
def test_a_damaged_file_gives_fresh_stats(path, text):
    os.makedirs(os.path.dirname(path))
    open(path, "w").write(text)
    s = A.Stats(path)
    assert (s.wins, s.losses, s.best_score, s.badges) == (0, 0, 0, [])


def test_bad_values_inside_a_valid_file_are_ignored(path):
    os.makedirs(os.path.dirname(path))
    json.dump({"wins": -4, "losses": "x", "best_score": True, "best_time_left": 2.5,
               "badges": ["flawless", "cheater", 7]}, open(path, "w"))
    s = A.Stats(path)
    assert (s.wins, s.losses, s.best_score, s.best_time_left) == (0, 0, 0, 0)
    assert s.badges == ["flawless"]


def test_an_unwritable_location_does_not_crash(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    A.Stats(str(blocker / "sub" / "s.json")).record_loss()


def test_the_environment_variable_picks_the_file(tmp_path, monkeypatch):
    target = tmp_path / "elsewhere.json"
    monkeypatch.setenv(A.ENV_VAR, str(target))
    A.Stats().record_loss()
    assert target.exists() and A.Stats().losses == 1


def test_badge_tables_agree():
    assert len(set(A.BADGE_IDS)) == len(A.BADGES) == len(A.BADGE_NAMES)


def test_unlocked_badges_stay_unlocked_after_a_plainer_win(path):
    s = A.Stats(path)
    s.record_win(100, result(mistakes=0, coop=True))
    s.record_win(50, result())                         # no flawless, no co-op this time
    assert A.Stats(path).badges == ["escape", "flawless", "duo"]
