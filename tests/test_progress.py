"""systems/progress.py: the saved run behind the menu's Continue."""

import json

import pytest

from core.level_manager import LEVEL_ORDER
from systems import progress as P


@pytest.fixture
def path(tmp_path):
    return str(tmp_path / "saves" / "progress.json")


def good(**over):
    data = dict(level="level3", score=450, remaining=512.3, difficulty="medium", coop=True)
    data.update(over)
    return data


def test_a_saved_run_loads_back_the_same(path):
    assert P.save_progress(**good(), path=path)
    assert P.load_progress(path) == {"level": "level3", "score": 450, "remaining": 512.3,
                                     "difficulty": "medium", "coop": True}


def test_no_file_means_no_saved_run(path):
    assert P.load_progress(path) is None


def test_clear_removes_it_and_is_safe_twice(path):
    P.save_progress(**good(), path=path)
    P.clear_progress(path)
    assert P.load_progress(path) is None
    P.clear_progress(path)


@pytest.mark.parametrize("text", ["", "not json", "[]", "null", "42", '{"level": "level3"}'])
def test_damaged_files_are_ignored(path, text):
    import os
    os.makedirs(os.path.dirname(path))
    with open(path, "w") as f:
        f.write(text)
    assert P.load_progress(path) is None


@pytest.mark.parametrize("bad", [
    {"level": "nowhere"}, {"level": LEVEL_ORDER[0]}, {"score": -1}, {"score": 1.5},
    {"score": True}, {"remaining": 0}, {"remaining": -3}, {"remaining": "9"},
    {"difficulty": "brutal"}, {"coop": 1}, {"coop": "yes"},
])
def test_bad_values_are_refused_on_save_and_on_load(path, bad):
    assert not P.save_progress(**good(**bad), path=path)
    assert P.load_progress(path) is None
    import os
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w") as f:
        json.dump(good(**bad), f)
    assert P.load_progress(path) is None


def test_every_floor_after_the_first_can_be_saved(path):
    for level in LEVEL_ORDER[1:]:
        assert P.save_progress(**good(level=level), path=path)
        assert P.load_progress(path)["level"] == level


def test_an_unwritable_location_does_not_crash(tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("x")
    assert not P.save_progress(**good(), path=str(blocker / "sub" / "p.json"))


def test_the_environment_variable_picks_the_file(tmp_path, monkeypatch):
    target = tmp_path / "elsewhere.json"
    monkeypatch.setenv(P.ENV_VAR, str(target))
    P.save_progress(**good())
    assert target.exists() and P.load_progress()["score"] == 450


def test_describe_names_the_floor_and_score():
    assert P.describe(good()) == "Floor 3 - 450 pts"
    assert P.describe(good(level=LEVEL_ORDER[-1], score=9)) == "Final Vault - 9 pts"
