"""
levels/grid_requests.py
Owner: Member 2 - Paranthama (Floor 2's operators), generator by Member 1

Floor 2's relay questions, written fresh every run instead of drawn from a
fixed bank of 27.  Every question takes one real step of thinking, and the
three wrong breakers are the mistakes a beginner actually makes.

    Relay 1  ARITHMETIC   "What does 7 + 3 * 2 evaluate to?"   precedence, //, %, /, **
    Relay 2  COMPARISON   "Which x makes 3 < x <= 6 True?"     boundaries, chains, ==
    Relay 3  LOGIC        "Which x makes x < 3 or x > 7 False?" and / or / not, precedence

Answers come from Python itself (eval of the expression, or of the condition
for each candidate x), so they cannot be wrong; for the "which x" questions
exactly one breaker satisfies the question.  Pure data, no pygame.

A question: id, room, difficulty, prompt, options (4, short enough for a
breaker plate), answer, hint, explanation, points, and why_wrong: for each wrong
breaker, one line on why it is wrong (shown on Hard, where hints are off).
"""

import random
import zlib

POINTS = {"easy": 40, "medium": 50, "hard": 60}
MAX_LABEL = 5                     # characters that fit on a breaker plate


def _show(value):
    return repr(value) if isinstance(value, str) else str(value)


def _pack(room, difficulty, prompt, answer, wrong, hint, explanation, rng, why_wrong=None, fallback=None):
    options = [answer]
    for w in wrong:
        if w not in options and len(w) <= MAX_LABEL:
            options.append(w)
        if len(options) == 4:
            break
    try:
        base = float(answer)
    except ValueError:
        base = 0
    step = 1
    while len(options) < 4:                        # pad with near numbers if the mistakes ran out
        for guess in (int(base) + step, int(base) - step):
            if str(guess) not in options and len(options) < 4:
                options.append(str(guess))
        step += 1
    rng.shuffle(options)
    why_wrong = why_wrong or {}
    reasons = {}
    for option in options:
        if option == answer:
            continue
        reason = why_wrong.get(option) or (fallback(option) if fallback else None)
        if reason:
            reasons[option] = reason
    tag = zlib.crc32(prompt.encode()) & 0xFFFF
    return {"id": f"grid_r{room}_{difficulty}_{tag:04x}", "room": room, "difficulty": difficulty,
            "prompt": prompt, "options": options, "answer": answer, "hint": hint,
            "explanation": explanation, "points": POINTS[difficulty],
            "why_wrong": reasons}


# --- Relay 1: arithmetic ---------------------------------------------------------------
def _arith_forms(rng, difficulty):
    """(expression, [mistaken expressions or values], hint)."""
    a, b = rng.randint(2, 9), rng.randint(2, 6)
    c = rng.choice([n for n in range(2, 6) if n % b])          # never divides evenly: // and % matter
    forms = {
        "easy": [
            (f"{a} + {b} * {c}", [f"({a} + {b}) * {c}", f"{a} + {b} + {c}"],
             "* is worked out before +."),
            (f"{a * b + c} // {b}", [f"{a * b + c} / {b}", f"{a * b + c} % {b}"],
             "// divides and drops the remainder."),
            (f"{a * b + c} % {b}", [f"{a * b + c} // {b}", f"{b} - {a * b + c} % {b}"],
             "% gives the remainder after dividing."),
        ],
        "medium": [
            (f"{a * 2} / 2", [f"{a * 2} // 2 + 0.5", f"{a}"],
             "/ always gives a float, even when it divides exactly."),
            (f"({a} + {b}) % {c}", [f"{a} + {b} % {c}", f"({a} + {b}) // {c}"],
             "Brackets first, then %."),
            (f"{a + 10} - {b} * {c} + 1", [f"({a + 10} - {b}) * {c} + 1", f"{a + 10} - {b} * ({c} + 1)"],
             "* before - and +; then left to right."),
            (f"{b} ** 2 // {c}", [f"{b} ** (2 // {c})", f"{b} ** 2 / {c}"],
             "** first, then //."),
        ],
        "hard": [
            ("2 ** 3 ** 2", ["(2 ** 3) ** 2", "2 * 3 * 2"],
             "** groups from the right: 3 ** 2 first."),
            (f"-{2 * a + 1} // 2", [f"-({2 * a + 1} // 2)", f"-{2 * a + 1} / 2"],
             "// rounds down, towards minus infinity, not towards zero."),
            (f"{a + 12} - {b} - {c}", [f"{a + 12} - ({b} - {c})", f"{a + 12} - {b} + {c}"],
             "- works left to right."),
            (f"{a * 3 + 2} % {a} * 2 + 1", [f"{a * 3 + 2} % ({a} * 2) + 1", f"{a * 3 + 2} % {a} * (2 + 1)"],
             "% and * share a level: left to right, then +."),
        ],
    }
    return forms[difficulty]


def arithmetic(rng, difficulty):
    expr, mistakes, hint = rng.choice(_arith_forms(rng, difficulty))
    value = eval(expr)                                          # noqa: S307 - our own expression
    answer = _show(value)
    wrong, why = [], {}
    for m in mistakes:
        try:
            v = eval(m)                                         # noqa: S307
        except ZeroDivisionError:
            continue
        if isinstance(v, float) and not v.is_integer():
            v = round(v, 2)
        wrong.append(_show(v))
        why.setdefault(_show(v), f"{_show(v)} is what {m} gives.")
    if isinstance(value, float) and value.is_integer():
        wrong.insert(0, str(int(value)))                        # the classic: 4 instead of 4.0
        why[str(int(value))] = f"{int(value)} is an int, but / always gives a float."
    return _pack(1, difficulty, f"What does {expr} evaluate to?", answer, wrong, hint,
                 f"{expr} evaluates to {answer}.", rng, why_wrong=why,
                 fallback=lambda option: f"{expr} does not give {option}.")


# --- Relays 2 and 3: "which x makes it True / False?" -----------------------------------
def _which(rng, room, difficulty, cond, pool, want, hint):
    """One candidate from `pool` gives `want`; three give the opposite (boundaries first)."""
    hits = [x for x in pool if bool(eval(cond, {"x": x})) is want]       # noqa: S307
    miss = [x for x in pool if bool(eval(cond, {"x": x})) is not want]   # noqa: S307
    if not hits or len(miss) < 3:
        return None
    # the interesting answer sits at the edge: prefer hits right next to a miss
    edge = sorted(hits, key=lambda h: (min(abs(h - m) for m in miss), rng.random()))
    right = rng.choice(edge[:2])
    wrong = sorted(miss, key=lambda x: (abs(x - right), rng.random()))[:3]
    word = "True" if want else "False"
    explanation = f"x = {right}: {cond} is {word}; for {', '.join(map(str, wrong))} it is {not want}."
    return _pack(room, difficulty, f"Which x makes {cond} {word}?", str(right), [str(w) for w in wrong],
                 hint, explanation, rng,
                 fallback=lambda option: f"x = {option} makes {cond} {not want}.")


def comparison(rng, difficulty):
    for _ in range(50):
        k = rng.randint(3, 8)
        lo, hi = k - rng.randint(1, 2), k + rng.randint(1, 3)
        forms = {
            "easy": [(f"x > {k}", "> does not include the number itself."),
                     (f"x >= {k}", ">= includes the number itself."),
                     (f"x < {k}", "< does not include the number itself."),
                     (f"x == {k}", "== asks: are they equal?")],
            "medium": [(f"{lo} < x <= {hi}", "A chain is both tests at once: lo < x and x <= hi."),
                       (f"{lo} <= x < {hi}", "A chain is both tests at once: lo <= x and x < hi."),
                       (f"x != {k}", "!= means 'not equal'."),
                       (f"x * 2 >= {2 * k + 1}", "Work out x * 2 first, then compare.")],
            "hard": [(f"x // 2 == {k // 2}", "// first, then compare with ==."),
                     (f"x % 3 == {k % 3}", "% first: the remainder after dividing by 3."),
                     (f"{lo} < x != {k}", "The chain means lo < x and x != k."),
                     (f"x ** 2 > {k * k}", "Square x first, then compare.")],
        }
        cond, hint = rng.choice(forms[difficulty])
        want = not cond.startswith("x !=") if difficulty == "medium" else rng.random() < 0.75
        q = _which(rng, 2, difficulty, cond, list(range(0, 13)), want, hint)
        if q:
            return q
    raise RuntimeError("no comparison question")


def logic(rng, difficulty):
    for _ in range(50):
        a = rng.randint(2, 5)
        b = a + rng.randint(2, 4)
        forms = {
            "easy": [(f"x > {a} and x < {b}", "and: both sides must be True."),
                     (f"x < {a} or x > {b}", "or: one True side is enough."),
                     (f"not x > {a}", "not flips True and False.")],
            "medium": [(f"x % 2 == 0 and x > {a}", "and: x must be even AND above the number."),
                       (f"not (x > {a} and x < {b})", "Work out the brackets, then flip it with not."),
                       (f"x == {a} or x > {b}", "or: either test is enough.")],
            "hard": [(f"not x > {a} or x == {b}", "not binds tighter than or: (not x > a) or x == b."),
                     (f"x < {a} or x > {b} and x != {b + 2}", "and is worked out before or."),
                     (f"x > {a} and not x == {b}", "not applies only to x == b.")],
        }
        cond, hint = rng.choice(forms[difficulty])
        q = _which(rng, 3, difficulty, cond, list(range(0, 13)), rng.random() < 0.6, hint)
        if q:
            return q
    raise RuntimeError("no logic question")


RELAYS = {1: arithmetic, 2: comparison, 3: logic}


def make_question(relay, difficulty="medium", rng=None):
    rng = rng or random
    difficulty = difficulty if difficulty in POINTS else "medium"
    return RELAYS[relay](rng, difficulty)
