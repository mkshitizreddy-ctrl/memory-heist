"""A missing or damaged puzzles file must not stop the game from starting."""

import json

import pytest

from systems.hints import HintSystem

NO_HINT = "No hint available."


def test_missing_puzzles_file_gives_no_hints_instead_of_crashing(tmp_path):
    hints = HintSystem(tmp_path / "nope.json")

    assert hints.get_hint("level1_gate_1") == NO_HINT


@pytest.mark.parametrize("content", ["not json {", "", "[1, 2, 3]", "42", "null"])
def test_damaged_or_wrong_shaped_file_gives_no_hints(tmp_path, content):
    path = tmp_path / "puzzles.json"
    path.write_text(content, encoding="utf-8")

    assert HintSystem(path).get_hint("anything") == NO_HINT


def test_a_puzzle_entry_that_is_not_a_dict_gives_no_hint(tmp_path):
    path = tmp_path / "puzzles.json"
    path.write_text(json.dumps({"bad": "just a string", "ok": {"hint": "H"}}), encoding="utf-8")
    hints = HintSystem(path)

    assert hints.get_hint("bad") == NO_HINT
    assert hints.get_hint("ok") == "H"


def test_hints_stay_enabled_when_the_file_is_unreadable(tmp_path):
    assert HintSystem(tmp_path / "nope.json").enabled is True
