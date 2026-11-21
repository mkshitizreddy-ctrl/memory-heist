"""
levels/laser_requests.py
Owner: Member 3 - Yashovardhan (Floor 3's loops)

Floor 3's door questions are about the loop the room is really running.

Each room gets one request: a few lines of Python for the LOOP LOGIC board and
a question about them.  The room then does exactly what the code says:

    Room 1  for pad in range(...): light(pad)    the safe pads that shield you
    Room 2  cam = ...; while cam < ...:          the cameras that sweep
    Room 3  for pulse in range(...): overload()  the pulses before the core vents

The answer is worked out by running the code, so the board, the room and the
answer can never disagree.  Pure data: no pygame, so the tests can check every
answer by running the code again.

A request: id, room, difficulty, code (lines), question, options (4), answer,
hint, explanation, points, fires (pads / cameras / one pulse per overload).
"""

import random

from levels import patrol_requests
from levels.patrol_requests import POINTS, _fmt, _number, _options, _pack, _subsets

PADS = 3                     # Room 1's safe pads, numbered 0, 1, 2 on the floor
MAX_LINES = 4                # the LOOP LOGIC board shows at most four lines


def run(code):
    """Run the board's code; return what light()/sweep() got, one entry per overload()."""
    fired = []
    names = {
        "light": fired.append,
        "sweep": fired.append,
        "overload": lambda: fired.append(len(fired)),
        "vent": lambda: None,
    }
    exec("\n".join(code), names)              # noqa: S102 - our own generated code
    return fired, names


def _which_pads(rng, fired, near):
    answer = _fmt(sorted(fired))
    return answer, _options(rng, answer, [_fmt(sorted(set(c))) for c in near if c], _subsets(PADS))


# --- Room 1: for and range light the safe pads -------------------------------------------
def _room1(rng, difficulty):
    if difficulty == "easy":
        start, stop = rng.choice([(0, 2), (1, 3), (0, 3), (2, 3)])
        args = f"{stop}" if start == 0 else f"{start}, {stop}"
        hint = "range(a, b) starts at a and stops before b; range(b) starts at 0."
        near = [range(start, stop + 1), range(start + 1, stop + 1), range(0, stop), range(start, stop - 1)]
        key = f"range_{start}_{stop}"
    elif difficulty == "medium":
        start, stop, step = rng.choice([(0, 3, 2), (1, 3, 1), (2, -1, -2), (0, 2, 1)])
        args = f"{start}, {stop}, {step}"
        hint = "The third number is the step; the stop value itself never comes out."
        near = [range(start, stop + (1 if step > 0 else -1), step), range(0, PADS),
                range(start + 1, PADS), [start]]
        key = f"step_{start}_{stop}_{step}"
    else:
        kind = rng.choice(["continue", "break", "odd"])
        if kind == "odd":
            code = ["for pad in range(3):", "    if pad % 2 == 1:", "        continue", "    light(pad)"]
            hint = "pad % 2 == 1 is True for odd pads; continue skips them."
            k = 1
        else:
            k = rng.randrange(1, PADS) if kind == "break" else rng.randrange(PADS)
            code = ["for pad in range(3):", f"    if pad == {k}:", f"        {kind}", "    light(pad)"]
            hint = ("break leaves the loop at once; nothing after it runs." if kind == "break"
                    else "continue skips the rest of this pass, then the loop goes on.")
        fired, _ = run(code)
        near = [range(PADS), [v for v in range(PADS) if v != k], range(k), range(k + 1), [1], [0, 2]]
        answer, options = _which_pads(rng, fired, [list(r) for r in near])
        return _pack(1, difficulty, f"{kind}_{k}", code, "The board's loop: which safe pads are lit?",
                     answer, options, hint,
                     f"Only pads {_fmt(fired)} reach light(pad); the others give no cover.", fired)
    code = [f"for pad in range({args}):", "    light(pad)"]
    fired, _ = run(code)
    answer, options = _which_pads(rng, fired, [[v for v in r if 0 <= v < PADS] for r in near])
    return _pack(1, difficulty, key, code, "The board's loop: which safe pads are lit?",
                 answer, options, hint,
                 f"pad takes {_fmt(fired)}, so only those pads shield you.", fired)


# --- Room 2: the team's while-loop cameras (levels/patrol_requests.py) ---------------------
def _room2(rng, difficulty):
    return patrol_requests.make_request(2, difficulty, rng)


# --- Room 3: the core overloads, then vents when its loop ends ----------------------------
def _room3(rng, difficulty):
    if difficulty == "easy":
        args = rng.choice(["1", "2", "1, 3"])
        code = [f"for pulse in range({args}):", "    overload()", "vent()"]
        hint = "Count the values range() gives: one overload() for each."
    elif difficulty == "medium":
        code = rng.choice([
            ["for pulse in range(0, 4, 2):", "    overload()", "vent()"],
            ["for pulse in range(3, 1, -1):", "    overload()", "vent()"],
            ["pulse = 1", "while pulse < 2:", "    overload()", "    pulse += 1"],
            ["pulse = 0", "while pulse < 3:", "    overload()", "    pulse += 2"],
        ])
        hint = "Write down each value the loop variable takes; each one is a pulse."
    else:
        code = rng.choice([
            ["pulse = 0", "while True:", "    overload(); pulse += 1", "    if pulse == 2: break"],
            ["pulse = 3", "while pulse > 0:", "    overload()", "    pulse -= 2"],
            ["for pulse in range(4):", "    if pulse % 2: continue", "    overload()", "vent()"],
            ["for pulse in range(5):", "    if pulse == 1: break", "    overload()", "vent()"],
        ])
        hint = "Trace the loop by hand: break ends it, continue skips one overload()."
    fired, _ = run(code)
    count = len(fired)
    answer, options = _number(rng, count, [count - 1, count + 1, count + 2], 0, 4)
    return _pack(3, difficulty, f"vent_{count}", code,
                 "The core vents when its loop ends. How many overload pulses first?",
                 answer, options, hint,
                 f"overload() runs {count} time{'s' if count != 1 else ''}; then the core vents "
                 "and is safe to cross.", fired)


ROOMS = {1: _room1, 2: _room2, 3: _room3}


def make_request(room, difficulty="medium", rng=None):
    rng = rng or random
    difficulty = difficulty if difficulty in POINTS else "medium"
    return ROOMS[room](rng, difficulty)
