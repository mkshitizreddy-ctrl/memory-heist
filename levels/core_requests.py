"""
levels/core_requests.py
Owner: Member 1 - Core Game System (the Final Vault rebuilt as WARDEN's Core)

The six locks around WARDEN's core, one for every floor of the run.  Each lock
shows a few lines of Python; the three plates in front of it carry candidate
answers.  Stand on the right plate and press E.

    0 DATA TYPES     (Floor 1)   what type(...) gives
    1 OPERATORS      (Floor 2)   what an expression evaluates to
    2 LOOPS          (Floor 3)   what a loop leaves behind
    3 LISTS & DICTS  (Floor 4)   what an index or key looks up
    4 FUNCTIONS      (Floor 5)   what a call returns
    5 EXCEPTIONS     (Floor 5)   which error a line raises

Each lock is a dict: lock, topic, floor, lines, labels (3), answer, hint,
explain, and code + kind, which the tests run to prove the answer:
    kind "type"   eval(code) -> type name           kind "value"  exec(code) -> result
    kind "raise"  exec(code) raises that error name
"""

TOPICS = ("DATA TYPES", "OPERATORS", "LOOPS", "LISTS & DICTS", "FUNCTIONS", "EXCEPTIONS")
FLOORS = ("Floor 1 - Reception", "Floor 2 - Maintenance Grid", "Floor 3 - Night Patrol",
          "Floor 4 - Records Archive", "Floor 5 - Server Hall", "Floor 5 - Server Hall")
LOCKS = len(TOPICS)


def _pack(rng, lock, lines, right, wrong, hint, explain, code, kind):
    labels = [right] + list(wrong)
    rng.shuffle(labels)
    return {"lock": lock, "topic": TOPICS[lock], "floor": FLOORS[lock], "lines": lines,
            "labels": labels, "answer": labels.index(right), "hint": hint, "explain": explain,
            "code": code, "kind": kind}


def data_type_lock(rng):
    value, name = rng.choice((("3.0", "float"), ("'42'", "str"), ("42", "int"), ("True", "bool"),
                              ("[4, 2]", "list"), ("{'id': 7}", "dict")))
    wrong = rng.sample([n for n in ("int", "float", "str", "bool", "list", "dict") if n != name], 2)
    return _pack(rng, 0, [f"clearance = {value}", "type(clearance)  # ?"], name, wrong,
                 "Quotes make a str, a dot makes a float, square brackets a list, braces a dict.",
                 f"{value} is a {name}.", f"type({value})", "type")


def operator_lock(rng):
    a, b = rng.randint(7, 13), rng.randint(2, 4)
    forms = ((f"{a} // {b} + 1", a // b + 1), (f"{a} % {b} * 2", a % b * 2),
             (f"2 ** {b} - {b}", 2 ** b - b), (f"({a} > {b}) and ({b} > {a})", (a > b) and (b > a)))
    expr, value = rng.choice(forms)
    if isinstance(value, bool):
        right, wrong = repr(value), [repr(not value), "None"]
    else:
        right = str(value)
        wrong = [str(v) for v in (value + 1, value - 1 if value > 0 else value + 2)]
    return _pack(rng, 1, [f"power = {expr}", "# power is?"], right, wrong,
                 "// drops the fraction, % is the remainder, ** is a power; brackets first.",
                 f"{expr} is {right}.", f"result = {expr}", "value")


def loop_lock(rng):
    n = rng.randint(3, 5)
    forms = (
        ([f"total = 0", f"for i in range({n}):", "    total += i"], "total", sum(range(n))),
        ([f"count = 0", f"while count < {n * 2}:", "    count += 2"], "count", n * 2),
        ([f"laps = 0", f"for lane in range(1, {n}):", "    laps += 1"], "laps", n - 1),
    )
    lines, name, value = rng.choice(forms)
    wrong = [str(value + 1), str(value - 1 if value > 1 else value + 2)]
    return _pack(rng, 2, lines + [f"# {name} is?"], str(value), wrong,
                 "range(n) stops before n; a while loop stops as soon as its test is False.",
                 f"The loop leaves {name} = {value}.", "\n".join(lines) + f"\nresult = {name}", "value")


def collection_lock(rng):
    forms = (
        (["files = ['tax', 'visa', 'ghost']", "files[-1]  # ?"], "'ghost'", ["'tax'", "'visa'"],
         "files[-1]", "Index -1 is the last item."),
        (["files = ['tax', 'visa', 'ghost']", "files[1]  # ?"], "'visa'", ["'tax'", "'ghost'"],
         "files[1]", "Indexes start at 0, so [1] is the second item."),
        (["codes = {'ghost': 'B-7', 'warden': 'X-0'}", "codes['warden']  # ?"], "'X-0'", ["'B-7'", "'warden'"],
         "codes['warden']", "A key looks up its value."),
        (["codes = {'ghost': 'B-7'}", "codes['echo'] = 'E-2'", "len(codes)  # ?"], "2", ["1", "3"],
         "len(codes)", "Assigning a new key adds an entry."),
    )
    lines, right, wrong, expr, hint = rng.choice(forms)
    setup = "\n".join(line.split("  #")[0] for line in lines[:-1])
    return _pack(rng, 3, lines, right, wrong, hint, f"{expr} is {right}.",
                 setup + f"\nresult = {expr}", "value")


def function_lock(rng):
    x = rng.randint(2, 5)
    forms = (
        (["def boost(x):", "    return x * 3", f"boost({x})  # ?"], str(x * 3), [str(x + 3), "None"],
         "return hands the value back to the caller."),
        (["def boost(x, step=2):", "    return x + step", f"boost({x})  # ?"], str(x + 2), [str(x), "None"],
         "A default fills in a parameter the call leaves out."),
        (["def boost(x):", "    print(x * 3)", f"boost({x})  # ?"], "None", [str(x * 3), str(x)],
         "print shows a value; without return the call gives None."),
    )
    lines, right, wrong, hint = rng.choice(forms)
    code = "\n".join(lines[:-1]).replace("print(", "_print(") + f"\nresult = boost({x})"
    return _pack(rng, 4, lines, right, wrong, hint, f"boost({x}) returns {right}.", code, "value")


def exception_lock(rng):
    line, name = rng.choice((("int('7a')", "ValueError"), ("{}['key']", "KeyError"), ("10 / 0", "ZeroDivisionError"),
                             ("[1, 2][5]", "IndexError"), ("'id' + 7", "TypeError")))
    wrong = rng.sample([n for n in ("ValueError", "KeyError", "ZeroDivisionError", "IndexError", "TypeError")
                        if n != name], 2)
    return _pack(rng, 5, ["try:", f"    {line}", "except ____:  # ?"], name, wrong,
                 "Ask what goes wrong when the line runs: bad text, missing key, divide by zero, bad index, mixed types.",
                 f"{line} raises {name}.", line, "raise")


MAKERS = (data_type_lock, operator_lock, loop_lock, collection_lock, function_lock, exception_lock)


def make_lock(lock, rng):
    return MAKERS[lock](rng)
