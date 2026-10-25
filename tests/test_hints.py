
import json

from systems.hints import HintSystem


def test_get_hint_for_existing_puzzle(tmp_path):
    puzzles_file = tmp_path / "puzzles.json"
    puzzles_file.write_text(
        json.dumps({
            "puzzle_1": {
                "hint": "Check the variable's data type."
            }
        }),
        encoding="utf-8",
    )

    hints = HintSystem(str(puzzles_file))

    assert hints.get_hint("puzzle_1") == "Check the variable's data type."


def test_missing_puzzle_returns_default_hint(tmp_path):
    puzzles_file = tmp_path / "puzzles.json"
    puzzles_file.write_text("{}", encoding="utf-8")

    hints = HintSystem(str(puzzles_file))

    assert hints.get_hint("unknown_puzzle") == "No hint available."


def test_puzzle_without_hint_returns_default(tmp_path):
    puzzles_file = tmp_path / "puzzles.json"
    puzzles_file.write_text(
        json.dumps({"puzzle_1": {"question": "What is a variable?"}}),
        encoding="utf-8",
    )

    hints = HintSystem(str(puzzles_file))

    assert hints.get_hint("puzzle_1") == "No hint available."


def test_hints_are_enabled_by_default(tmp_path):
    puzzles_file = tmp_path / "puzzles.json"
    puzzles_file.write_text("{}", encoding="utf-8")

    hints = HintSystem(str(puzzles_file))

    assert hints.enabled is True


def test_hints_can_be_disabled(tmp_path):
    puzzles_file = tmp_path / "puzzles.json"
    puzzles_file.write_text("{}", encoding="utf-8")

    hints = HintSystem(str(puzzles_file))
    hints.enabled = False

    assert hints.enabled is False
    assert hints.get_hint("unknown_puzzle") == "No hint available."
