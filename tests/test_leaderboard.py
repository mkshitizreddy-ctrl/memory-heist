"""Leaderboard keeps the best scores, survives bad files, and reports rank."""

import json

import pytest

from systems.leaderboard import MAX_ENTRIES, MAX_NAME_LENGTH, Leaderboard


@pytest.fixture
def path(tmp_path):
    return tmp_path / "saves" / "leaderboard.json"


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data), encoding="utf-8")


def test_new_board_is_empty_and_creates_no_file(path):
    board = Leaderboard(str(path))

    assert board.top(5) == []
    assert not path.exists()


def test_add_returns_one_based_rank_and_keeps_best_first(path):
    board = Leaderboard(str(path))

    assert board.add("A", 100) == 1
    assert board.add("B", 300) == 1
    assert board.add("C", 200) == 2

    assert [e["name"] for e in board.top(5)] == ["B", "C", "A"]


def test_equal_scores_keep_the_earlier_entry_ahead(path):
    board = Leaderboard(str(path))
    board.add("FIRST", 500)

    assert board.add("SECOND", 500) == 2


def test_table_is_capped_and_a_low_score_does_not_place(path):
    board = Leaderboard(str(path))
    for i in range(MAX_ENTRIES):
        board.add(f"P{i}", 1000 + i)

    assert board.add("LOW", 1) is None
    assert len(board.entries) == MAX_ENTRIES
    assert all(e["name"] != "LOW" for e in board.entries)


def test_name_is_trimmed_truncated_and_defaulted(path):
    board = Leaderboard(str(path))

    board.add("  " + "x" * 40 + "  ", 10)
    board.add("   ", 20)
    board.add(None, 30)

    names = [e["name"] for e in board.entries]
    assert "x" * MAX_NAME_LENGTH in names
    assert names.count("PLAYER") == 2


def test_scores_persist_between_instances(path):
    Leaderboard(str(path)).add("ANA", 750, "Hard", coop=True)

    entry = Leaderboard(str(path)).top(1)[0]

    assert (entry["name"], entry["score"]) == ("ANA", 750)
    assert entry["difficulty"] == "Hard"
    assert entry["coop"] is True


@pytest.mark.parametrize("content", ["not json {", "", '{"a": 1}', "42"])
def test_damaged_file_gives_an_empty_board(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

    assert Leaderboard(str(path)).top(5) == []


def test_malformed_entries_are_dropped_and_good_ones_kept(path):
    write(path, [
        {"name": "OK", "score": 50},
        {"name": "NOSCORE"},
        {"score": 99},
        {"name": 7, "score": 10},
        {"name": "FLOAT", "score": 12.5},
        "junk",
    ])

    assert [e["name"] for e in Leaderboard(str(path)).top(5)] == ["OK"]


def test_boolean_scores_in_a_file_are_not_accepted(path):
    # JSON true is an int to Python, but it is not a score.
    write(path, [{"name": "SNEAKY", "score": True}, {"name": "OK", "score": 5}])

    assert [e["name"] for e in Leaderboard(str(path)).top(5)] == ["OK"]


def test_unwritable_location_does_not_crash_the_game(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x", encoding="utf-8")  # a file where a folder is needed
    board = Leaderboard(str(blocker / "sub" / "leaderboard.json"))

    assert board.add("A", 10) == 1
