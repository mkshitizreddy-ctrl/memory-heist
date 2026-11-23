"""Floor 2: relay questions are generated, correct, and every breaker is a real mistake."""

import random
import re

import pytest

from levels.grid_requests import MAX_LABEL, POINTS, make_question

DIFFS = ("easy", "medium", "hard")


def _value(text):
    return repr(eval(text))


@pytest.mark.parametrize("relay", (1, 2, 3))
@pytest.mark.parametrize("difficulty", DIFFS)
def test_answers_are_what_python_says(relay, difficulty):
    rng = random.Random(relay * 7 + len(difficulty))
    for _ in range(300):
        q = make_question(relay, difficulty, rng)
        assert len(q["options"]) == 4 and len(set(q["options"])) == 4 and q["answer"] in q["options"]
        assert all(len(o) <= MAX_LABEL for o in q["options"])
        assert q["points"] == POINTS[difficulty] and q["room"] == relay and q["hint"]
        if relay == 1:
            expr = re.match(r"What does (.+) evaluate to\?", q["prompt"]).group(1)
            assert q["answer"] == _value(expr)
        else:
            cond, word = re.match(r"Which x makes (.+) (True|False)\?", q["prompt"]).groups()
            want = word == "True"
            matching = [o for o in q["options"] if bool(eval(cond, {"x": int(o)})) is want]
            assert matching == [q["answer"]], q            # exactly one breaker answers it


@pytest.mark.parametrize("relay", (1, 2, 3))
@pytest.mark.parametrize("difficulty", DIFFS)
def test_runs_vary(relay, difficulty):
    rng = random.Random(3)
    assert len({make_question(relay, difficulty, rng)["prompt"] for _ in range(60)}) >= 4


def test_arithmetic_offers_the_classic_mistakes():
    rng = random.Random(0)
    seen = {}
    for _ in range(400):
        q = make_question(1, "hard", rng)
        seen[q["prompt"]] = q["options"]
    tower = seen.get("What does 2 ** 3 ** 2 evaluate to?")
    assert tower and "512" in tower and "64" in tower
    medium = [make_question(1, "medium", rng) for _ in range(400)]
    floats = [q for q in medium if q["answer"].endswith(".0")]
    assert floats and all(q["answer"][:-2] in q["options"] for q in floats)   # 4.0 next to 4


def test_the_grid_room_plays_generated_questions():
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame
    from types import SimpleNamespace
    pygame.init()
    pygame.display.set_mode((960, 640))
    from levels.level2_grid import GridRoom
    from systems.scoring import ScoreTracker
    from systems.security import SecurityMeter

    game = SimpleNamespace(score=ScoreTracker(), security=SecurityMeter(), hints=SimpleNamespace(enabled=True),
                           coop=False, player2=None, difficulty={"name": "hard"}, audio=None)
    room = GridRoom(game=game, seed=2)
    assert room.current_question["id"].startswith("grid_r1_hard")


@pytest.mark.parametrize("relay", (1, 2, 3))
@pytest.mark.parametrize("difficulty", DIFFS)
def test_every_wrong_breaker_has_a_true_reason(relay, difficulty):
    """Hard mode shows why_wrong instead of a hint, so every reason must be what Python says."""
    rng = random.Random(relay * 11 + len(difficulty))
    for _ in range(300):
        q = make_question(relay, difficulty, rng)
        wrong = [o for o in q["options"] if o != q["answer"]]
        assert set(q["why_wrong"]) == set(wrong), q
        for option, reason in q["why_wrong"].items():
            if relay == 1:
                expr = re.match(r"What does (.+) evaluate to\?", q["prompt"]).group(1)
                m = re.fullmatch(r"(\S+) is what (.+) gives\.", reason)
                if m:
                    value = eval(m.group(2))
                    if isinstance(value, float) and not value.is_integer():
                        value = round(value, 2)
                    assert m.group(1) == option and repr(value) == option, reason
                elif reason.endswith("but / always gives a float."):
                    assert q["answer"] == option + ".0", reason
                else:
                    assert reason == f"{expr} does not give {option}." and _value(expr) != option
            else:
                cond, word = re.match(r"Which x makes (.+) (True|False)\?", q["prompt"]).groups()
                actual = bool(eval(cond, {"x": int(option)}))
                assert reason == f"x = {option} makes {cond} {actual}.", reason
                assert str(actual) != word


def test_floor2_wall_lines_fit_the_wall():
    """Right-answer and Hard wrong-answer lines must fit on one line of the wall band."""
    import os
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    import pygame
    pygame.init()
    from core.game import SCREEN_WIDTH
    from core.tilemap import TILE
    from ui.fonts import ui_font
    font = ui_font(22)
    room_for_text = SCREEN_WIDTH - 4 * TILE
    rng = random.Random(5)
    longest = ""
    for relay in (1, 2, 3):
        for difficulty in DIFFS:
            for _ in range(200):
                q = make_question(relay, difficulty, rng)
                lines = [f"Relay {relay} live. {q['hint']}", f"All relays live. {q['hint']}"]
                lines += [f"Wrong: {r}" for r in q["why_wrong"].values()]
                longest = max(lines + [longest], key=lambda t: font.size(t)[0])
    assert font.size(longest)[0] <= room_for_text, longest
