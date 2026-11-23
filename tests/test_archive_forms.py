"""Floor 4's request forms: every form is answerable, every difficulty has its own set."""

import random
import re

import pytest

from levels import archive_requests as R

DIFFS = ("easy", "medium", "hard")
SEEDS = range(400)


def _run(lines, **env):
    names = dict(env)
    exec("\n".join(lines), {"__builtins__": {"len": len, "list": list}}, names)   # noqa: S102
    return names


def _check_shelf(r):
    got = []
    names = _run(r["lines"], pull=got.append)
    shelf = names["shelf"]
    opened = shelf[got[0]] if isinstance(got[0], int) else got[0]
    assert opened == "ghost"
    assert shelf.index("ghost") == r["answer"]


def _check_catalogue(r):
    label = r["labels"][r["answer"]].strip("'")
    if r["form"] == "value":
        codes = r["codes"]
        value = re.search(r"holds '([^']+)'", r["lines"][-1]).group(1)
        assert codes[label] == value
        return
    got = []
    _run(r["lines"], open=got.append)
    # open(codes[key]) hands over the card (the value); open(list(codes)[i]) names the drawer itself
    expected = label if r["form"] == "keys_index" else r["codes"][label]
    assert got[-1] == expected


def _check_vault(r, satchel):
    fed = []

    class Vault:
        def feed(self, item):
            fed.append(item)

    names = _run(r["lines"][1:], satchel=list(satchel), vault=Vault())
    assert fed[-1] == satchel[r["answer"]]


@pytest.mark.parametrize("difficulty", DIFFS)
def test_every_request_is_answerable_and_unambiguous(difficulty):
    for seed in SEEDS:
        rng = random.Random(seed)
        r0 = R.shelf_request(rng, difficulty)
        _check_shelf(r0)
        r1 = R.catalogue_request(rng, difficulty)
        _check_catalogue(r1)
        satchel = ["badge", "dossier", r1["take"]]
        r2 = R.vault_request(rng, satchel, difficulty)
        _check_vault(r2, satchel)
        for r in (r0, r1, r2):
            assert len(set(r["labels"])) == len(r["labels"])
            assert 0 <= r["answer"] < len(r["labels"])
            assert r["hint"] and r["walk"] and r["explain"]
            assert set(r["reasons"]) == set(range(len(r["labels"]))) - {r["answer"]}


@pytest.mark.parametrize("stage", [0, 1, 2])
def test_difficulties_never_share_a_form(stage):
    easy, medium, hard = (set(R.forms_for(stage, d)) for d in DIFFS)
    assert not (easy & medium) and not (easy & hard) and not (medium & hard)
    assert min(len(easy), len(medium), len(hard)) >= 3


@pytest.mark.parametrize("stage", [0, 1, 2])
@pytest.mark.parametrize("difficulty", DIFFS)
def test_every_form_in_a_tier_actually_appears(stage, difficulty):
    seen = set()
    for seed in range(600):
        rng = random.Random(seed)
        satchel = ["badge", "dossier", "B-7"]
        seen.add(R.make_request(stage, rng, satchel, difficulty)["form"])
    assert seen == set(R.forms_for(stage, difficulty))


def test_a_request_only_uses_forms_of_its_own_difficulty():
    for difficulty in DIFFS:
        for seed in range(100):
            rng = random.Random(seed)
            for stage in (0, 1, 2):
                r = R.make_request(stage, rng, ["badge", "dossier", "B-7"], difficulty)
                assert r["form"] in R.forms_for(stage, difficulty)
                assert r["difficulty"] == difficulty


def test_unknown_difficulty_falls_back_to_medium():
    r = R.shelf_request(random.Random(1), "nonsense")
    assert r["difficulty"] == "medium"


def test_a_wrong_pick_explains_itself():
    r = R.shelf_request(random.Random(3), "easy")
    wrong = (r["answer"] + 1) % len(r["labels"])
    assert R.why_wrong(r, wrong) == r["reasons"][wrong]


def test_feedback_lines_fit_the_message_line():
    from levels.floor4_archive import MESSAGE_CHARS
    for difficulty in DIFFS:
        for seed in range(150):
            rng = random.Random(seed)
            for stage in (0, 1, 2):
                r = R.make_request(stage, rng, ["badge", "dossier", "B-7"], difficulty)
                assert len("Wrong again. " + r["walk"]) <= MESSAGE_CHARS
                assert all(len("Wrong. " + t) <= MESSAGE_CHARS for t in r["reasons"].values())


def test_case_and_value_mistakes_get_their_own_reasons():
    seen = set()
    for seed in range(300):
        r = R.catalogue_request(random.Random(seed), "easy")
        seen.update(r["reasons"].values())
    assert any("case-sensitive" in t for t in seen)
    assert any("VALUE" in t for t in seen)


# --- the floor itself: feedback after a wrong answer, easy timeout ---------------------
def _floor(difficulty="medium", hints=True, seed=1):
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    from tests.test_floor4_archive import make_level
    return make_level(hints=hints, difficulty=difficulty, seed=seed)


def _wrong_pick(level):
    return next(i for i in range(len(level.request["labels"])) if i != level.request["answer"])


def _press(level, player, index):
    import pygame
    from levels import archive_decor as A
    player.rect.center = A.stand_zone(level.stage, index).center
    level.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))


def test_first_miss_gives_the_reason_second_works_it_through():
    level, game, player = _floor()
    request = level.request
    pick = _wrong_pick(level)
    _press(level, player, pick)
    assert level.message.startswith("Wrong.") and request["reasons"][pick] in level.message
    assert len(level.message) <= 108
    _press(level, player, pick)
    assert level.message.startswith("Wrong again.") and request["walk"] in level.message
    assert game.security.level == 30                 # both misses were charged as before


def test_the_miss_count_restarts_on_the_next_slip_and_after_a_timeout():
    level, game, player = _floor()
    pick = _wrong_pick(level)
    _press(level, player, pick)
    assert level.misses == 1
    level.time_left = 0.01
    for _ in range(40):                          # the clock is held while the feedback is read
        level.update(0.25)
        if level.misses == 0:
            break
    assert level.misses == 0
    pick = _wrong_pick(level)
    _press(level, player, pick)
    assert "Wrong again" not in level.message
    _press(level, player, level.request["answer"])
    assert level.misses == 0 and level.stage == 1


def test_with_hints_off_a_miss_gives_no_reason():
    level, _, player = _floor(hints=False)
    _press(level, player, _wrong_pick(level))
    assert "Read the slip again" in level.message and "Off by one" not in level.message


def test_easy_timeouts_cost_a_little_less_security_than_medium_and_hard():
    from levels.floor4_archive import EASY_TIMEOUT_SECURITY, TIMEOUT_SECURITY
    for difficulty, cost in (("easy", EASY_TIMEOUT_SECURITY), ("medium", TIMEOUT_SECURITY),
                             ("hard", TIMEOUT_SECURITY)):
        level, game, _ = _floor(difficulty)
        level.time_left = 0.01
        level.update(0.05)
        assert game.security.level == cost
    assert EASY_TIMEOUT_SECURITY < TIMEOUT_SECURITY
