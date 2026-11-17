"""
levels/patrol_requests.py
Owner: Member 3 - Yashovardhan (Floor 3's loops), generator by Member 1

Floor 3's door questions are about the loop the room is really running.

Each room gets one request: a few lines of Python for the PATROL LOOP board,
and a question about them.  The room then does exactly what the code says:

    Room 1  for lane in range(...):        the lane columns that fire
    Room 2  cam = ...; while cam < ...:    the cameras that sweep
    Room 3  while patrol(): for lane ...   the tripwire rows that fire

`fires` is worked out by running the code (with zap/sweep recording what they
are given), so the board, the room and the answer can never disagree.  The
generators are pure data: no pygame, so the tests can check every answer by
running it again.

A request: id, room, difficulty, code (lines), question, options (4), answer,
hint, explanation, points, fires (lane or camera numbers, in firing order).
"""

import random
import zlib

POINTS = {"easy": 40, "medium": 50, "hard": 60}
LANES = {1: 4, 2: None, 3: 3}                 # lanes in rooms 1 and 3; room 2 counts cameras
CAMERAS = {"easy": 2, "medium": 3, "hard": 3}  # matches patrol_cameras.SETTINGS


def run(code):
    """Run the board's code; return what zap()/sweep() were called with, in order, and the names."""
    fired = []
    patrols = iter([True])                    # the robot's `while patrol():` runs one patrol

    def patrol():
        return next(patrols, False)

    names = {"zap": fired.append, "sweep": fired.append, "patrol": patrol}
    exec("\n".join(code), names)              # noqa: S102 - our own generated code
    return fired, names


def _fmt(values):
    return ", ".join(str(v) for v in values) if values else "none"


def _options(rng, answer, candidates, pool):
    """The answer plus three different distractors, shuffled."""
    out = [answer]
    for c in candidates:
        if c not in out:
            out.append(c)
        if len(out) == 4:
            break
    pool = [p for p in pool if p not in out]
    rng.shuffle(pool)
    while len(out) < 4 and pool:
        out.append(pool.pop())
    rng.shuffle(out)
    return out


def _subsets(n):
    """Every non-empty ascending choice of lanes 0..n-1, as answer strings."""
    out = []
    for mask in range(1, 2 ** n):
        out.append(_fmt([i for i in range(n) if mask >> i & 1]))
    return out


def _which(rng, fired, n, near):
    answer = _fmt(sorted(fired))
    pool = _subsets(n) if n >= 3 else _subsets(n + 1)        # two cameras: still four choices
    return answer, _options(rng, answer, [_fmt(sorted(c)) for c in near if c], pool)


def _number(rng, value, near, low, high):
    answer = str(value)
    pool = [str(v) for v in range(low, high + 1)]
    return answer, _options(rng, answer, [str(v) for v in near], pool)


def _pack(room, difficulty, key, code, question, answer, options, hint, explain, fires, trace=None):
    tag = zlib.crc32("\n".join(code + [question]).encode()) & 0xFFFF
    return {
        "id": f"patrol_r{room}_{difficulty}_{key}_{tag:04x}", "room": room, "difficulty": difficulty,
        "code": code, "question": question, "options": options, "answer": answer,
        "hint": hint, "explanation": explain, "points": POINTS[difficulty],
        "fires": list(fires), "trace": list(trace) if trace else None,
    }


# --- Room 1: for and range --------------------------------------------------------------
def _room1(rng, difficulty):
    n = LANES[1]
    if difficulty == "easy":
        start, stop = rng.choice([(0, 4), (1, 4), (0, 3), (2, 4), (0, 2)])
        args = f"{stop}" if start == 0 else f"{start}, {stop}"
        code = [f"for lane in range({args}):", "    zap(lane)"]
        fired, _ = run(code)
        near = [range(start, stop + 1), range(start + 1, stop + 1), range(0, stop), range(start, stop - 1)]
        answer, options = _which(rng, fired, n, [[v for v in r if 0 <= v < n] for r in near])
        return _pack(1, difficulty, f"range_{start}_{stop}", code, "The board's loop: which lanes fire?",
                     answer, options, "range(a, b) starts at a and stops before b; range(b) starts at 0.",
                     f"lane takes {_fmt(fired)}, so those lanes fire.", fired)
    if difficulty == "medium":
        kind = rng.choice(["step", "step", "down"])
        if kind == "step":
            start = rng.choice([0, 1])
            code = [f"for lane in range({start}, 4, 2):", "    zap(lane)"]
            fired, _ = run(code)
            near = [range(start, 4), range(start + 1, 4, 2), range(start, 5, 2), [start]]
            answer, options = _which(rng, fired, n, [[v for v in r if 0 <= v < n] for r in near])
            return _pack(1, difficulty, f"step_{start}", code, "The board's loop: which lanes fire?",
                         answer, options, "The third number in range() is the step: how far lane jumps each time.",
                         f"lane starts at {start} and jumps by 2 while it is below 4: {_fmt(fired)}.", fired)
        top = rng.choice([3, 2])
        code = [f"for lane in range({top}, -1, -1):", "    zap(lane)"]
        fired, _ = run(code)
        answer, options = _number(rng, fired[0], [0, top + 1, top - 1], 0, 3)
        return _pack(1, difficulty, f"down_{top}", code, "The board's loop: which lane fires first?",
                     answer, options, "A step of -1 counts down; the first value is the start.",
                     f"range({top}, -1, -1) gives {_fmt(fired)}, so lane {fired[0]} fires first.", fired)
    kind = rng.choice(["continue", "break", "odd"])
    if kind == "continue":
        k = rng.randrange(n)
        code = ["for lane in range(4):", f"    if lane == {k}:", "        continue", "    zap(lane)"]
        hint = "continue skips the rest of this pass, then the loop goes on."
    elif kind == "break":
        k = rng.randrange(1, n)
        code = ["for lane in range(4):", f"    if lane == {k}:", "        break", "    zap(lane)"]
        hint = "break leaves the loop at once; nothing after it runs."
    else:
        k = 0
        code = ["for lane in range(4):", "    if lane % 2 == 0:", "        continue", "    zap(lane)"]
        hint = "lane % 2 == 0 is True for even lanes; continue skips them."
    fired, _ = run(code)
    near = [range(n), [v for v in range(n) if v != k], range(k), range(k + 1), [0, 2], [1, 3]]
    answer, options = _which(rng, fired, n, [list(r) for r in near])
    return _pack(1, difficulty, f"{kind}_{k}", code, "The board's loop: which lanes fire?",
                 answer, options, hint, f"Only lanes {_fmt(fired)} reach zap(lane).", fired)


# --- Room 2: while, a counter and the cameras ------------------------------------------
def _room2(rng, difficulty):
    count = CAMERAS[difficulty]
    if difficulty == "easy":
        start = rng.choice([0, 1])
        code = [f"cam = {start}", f"while cam < {count}:", "    sweep(cam)", "    cam += 1"]
        step_text = "1"
    elif difficulty == "medium":
        start, limit = rng.choice([(0, 3), (1, 3), (0, 2)])
        step = 2 if limit == 3 else 1
        code = [f"cam = {start}", f"while cam < {limit}:", "    sweep(cam)", f"    cam += {step}"]
        step_text = str(step)
    else:
        start = rng.choice([2, 1])
        code = [f"cam = {start}", "while cam >= 0:", "    sweep(cam)", "    cam -= 2"]
        step_text = "-2"
    fired, names = run(code)
    after = names["cam"]
    trace = fired + [after]               # the values cam takes at each check of the condition
    ask_after = difficulty != "easy" and rng.random() < 0.5
    if ask_after:
        answer, options = _number(rng, after, [after - 1, after + 1, fired[-1]], -2, 5)
        return _pack(2, difficulty, "after", code,
                     "The board's loop: what is cam when it stops?", answer, options,
                     "The loop checks its condition before each pass; it stops the first time it is False.",
                     f"cam goes {_fmt([start] + [v for v in fired[1:]] + [after])}; at {after} the condition is False.",
                     fired, trace)
    near = [range(count), [start], [v for v in range(count) if v not in fired], range(start, count)]
    answer, options = _which(rng, fired, count, [[v for v in r if 0 <= v < count] for r in near])
    return _pack(2, difficulty, f"which_{start}_{step_text}", code,
                 "The board's loop: which cameras sweep?", answer, options,
                 "Follow cam: check the while condition, sweep, then change cam.",
                 f"cam takes {_fmt(fired)} before the condition turns False, so those cameras sweep.", fired, trace)


# --- Room 3: a for loop nested in the robot's while -------------------------------------
def _room3(rng, difficulty):
    n = LANES[3]
    if difficulty == "easy":
        start = rng.choice([0, 1])
        args = "3" if start == 0 else "1, 3"
        code = ["while patrol():", f"    for lane in range({args}):", "        zap(lane)"]
        fired, _ = run(code)
        near = [range(n), range(start + 1, n), range(start, n - 1), range(1, 4)]
        answer, options = _which(rng, fired, n, [[v for v in r if 0 <= v < n] for r in near])
        return _pack(3, difficulty, f"range_{start}", code, "Each patrol: which rows fire?", answer, options,
                     "The inner for loop runs in full on every pass of the while loop.",
                     f"Each patrol runs lane = {_fmt(fired)}.", fired)
    if difficulty == "medium":
        if rng.random() < 0.5:
            code = ["while patrol():", "    for lane in range(2, -1, -1):", "        zap(lane)"]
            fired, _ = run(code)
            answer, options = _number(rng, fired[0], [0, 1, 3], 0, 3)
            return _pack(3, difficulty, "down", code, "Each patrol: which row fires first?", answer, options,
                         "range(2, -1, -1) counts down from 2.",
                         f"The rows fire in the order {_fmt(fired)}.", fired)
        code = ["while patrol():", "    for lane in range(0, 3, 2):", "        zap(lane)"]
        fired, _ = run(code)
        answer, options = _which(rng, fired, n, [[0, 1, 2], [0, 1], [1], [0]])
        return _pack(3, difficulty, "step", code, "Each patrol: which rows fire?", answer, options,
                     "The step is 2: lane jumps from 0 to 2.", f"lane takes {_fmt(fired)}.", fired)
    k = rng.randrange(n)
    word = rng.choice(["continue", "break"]) if k else "continue"
    code = ["while patrol():", "    for lane in range(3):", f"        if lane == {k}: {word}", "        zap(lane)"]
    fired, _ = run(code)
    near = [range(n), [v for v in range(n) if v != k], range(k), range(k + 1)]
    answer, options = _which(rng, fired, n, [list(r) for r in near])
    hint = ("break leaves only the inner for loop; the patrol goes on."
            if word == "break" else "continue skips this row and goes on to the next.")
    return _pack(3, difficulty, f"{word}_{k}", code, "Each patrol: which rows fire?", answer, options,
                 hint, f"Only rows {_fmt(fired)} reach zap(lane).", fired)


ROOMS = {1: _room1, 2: _room2, 3: _room3}


def make_request(room, difficulty="medium", rng=None):
    rng = rng or random
    difficulty = difficulty if difficulty in POINTS else "medium"
    return ROOMS[room](rng, difficulty)
