"""
levels/server_requests.py
Owner: Member 1 - Core Game System (Floor 5 rebuilt on the shared kit)

The three machine jobs on Floor 5, as plain data.  Every machine in WARDEN's
server hall is a function; its def is stencilled on the casing.

    stage 0  ARGUMENTS    which value lands in a parameter: patch the cable to that port
    stage 1  RETURN       what the call returns: route the conveyor to that bay
    stage 2  EXCEPTIONS   which error the risky line raises: pull that except breaker

Each request is a dict:
    stage, topic
    machine   the def on the machine's casing (lines)
    lines     the job ticket on the wall (lines)
    labels    what is written on each port, bay or breaker (the answers)
    answer    index of the right label
    hint      shown when the player asks for a hint (H)
    explain   said when the right one is chosen
    code      Python the tests run to prove the answer (never shown)
"""

TOPICS = ("ARGUMENTS", "RETURN VALUES", "EXCEPTIONS")
ERRORS = {
    "ValueError": ("level = int('abc')", "int() cannot turn 'abc' into a number: ValueError."),
    "ZeroDivisionError": ("load = 10 / 0", "Dividing by zero raises ZeroDivisionError."),
    "KeyError": ("temp = sensors['core']", "sensors has no key 'core': KeyError."),
    "IndexError": ("fan = fans[5]", "fans has 3 items; index 5 is out of range: IndexError."),
    "TypeError": ("heat = 'hot' + 1", "A str and an int cannot be added: TypeError."),
}
SETUP = {"KeyError": "sensors = {'fan': 2}", "IndexError": "fans = [1, 2, 3]"}


def _shuffle(rng, labels, right):
    labels = list(labels)
    rng.shuffle(labels)
    return labels, labels.index(right)


def argument_request(rng, difficulty="medium"):
    floor, door = rng.sample(range(1, 9), 2)
    forms = ("positional", "keyword", "default")
    if difficulty == "easy":
        forms = ("positional", "positional", "keyword")
    form = rng.choice(forms)
    if form == "positional":
        machine = ["def route(floor, door):", "    lift.go(floor, door)"]
        call = f"route({floor}, {door})"
        ask = rng.choice(("floor", "door"))
        right = floor if ask == "floor" else door
        other = door if ask == "floor" else floor
        hint = "Positional arguments fill the parameters in order: first to floor, second to door."
    elif form == "keyword":
        machine = ["def route(floor, door):", "    lift.go(floor, door)"]
        call = f"route(door={door}, floor={floor})"
        ask = rng.choice(("floor", "door"))
        right = floor if ask == "floor" else door
        other = door if ask == "floor" else floor
        hint = "Keyword arguments match by name, whatever order they are written in."
    else:
        default = rng.choice([x for x in range(1, 9) if x != floor])
        machine = [f"def route(floor, door={default}):", "    lift.go(floor, door)"]
        call = f"route({floor})"
        ask = "door"
        right, other = default, floor
        hint = "A parameter with a default keeps it when the call leaves that argument out."
    labels, answer = _shuffle(rng, [str(right), str(other), f"'{ask}'", "None"], str(right))
    return {
        "stage": 0, "topic": TOPICS[0], "machine": machine,
        "lines": [call, f"# which value lands in {ask}?"],
        "labels": labels, "answer": answer, "hint": hint,
        "explain": f"In {call}, {ask} is {right}. Cable patched.",
        "code": "\n".join(machine).replace("lift.go(floor, door)", f"return {ask}") + f"\nresult = {call}",
        "value": right,
    }


def return_request(rng, difficulty="medium"):
    x = rng.randint(3, 6)
    forms = ["double", "tag", "log", "early", "clamp"]
    if difficulty == "easy":
        forms = ["double", "log", "tag"]
    form = rng.choice(forms)
    if form == "double":
        machine = ["def press(x):", "    return x * 2"]
        right, wrong = str(x * 2), [str(x), f"'{x}{x}'", "None"]
        hint = "return hands back x * 2 to whoever called press."
    elif form == "tag":
        machine = ["def press(x):", "    return str(x) * 2"]
        right, wrong = f"'{x}{x}'", [str(x * 2), str(x), "None"]
        hint = "str(x) is text. Text times 2 repeats it."
    elif form == "log":
        machine = ["def press(x):", "    print(x * 2)"]
        right, wrong = "None", [str(x * 2), f"'{x}{x}'", str(x)]
        hint = "print shows a value but does not return it. No return means None."
    elif form == "early":
        machine = ["def press(x):", "    return x + x", "    return 0"]
        right, wrong = str(x + x), ["0", str(x), "None"]
        hint = "The first return ends the function. Lines after it never run."
    else:
        x = rng.randint(7, 9)
        machine = ["def press(x):", "    if x > 5:", "        return 5", "    return x"]
        right, wrong = "5", [str(x), "None", "'5'"]
        hint = "x is bigger than 5, so the if branch returns first."
    call = f"press({x})"
    labels, answer = _shuffle(rng, [right] + wrong, right)
    return {
        "stage": 1, "topic": TOPICS[1], "machine": machine,
        "lines": [f"out = {call}", "# which bay gets out?"],
        "labels": labels, "answer": answer, "hint": hint,
        "explain": f"{call} returns {right}. Conveyor routed.",
        "code": "\n".join(machine).replace("print(", "_print(") + f"\nresult = {call}",
        "value": right,
    }


def exception_request(rng, difficulty="medium"):
    names = list(ERRORS)
    if difficulty == "easy":
        names = ["ValueError", "ZeroDivisionError", "KeyError", "IndexError"]
    right = rng.choice(names)
    line, why = ERRORS[right]
    decoys = rng.sample([n for n in ERRORS if n != right], 3)
    labels, answer = _shuffle(rng, [right] + decoys, right)
    setup = [SETUP[right]] if right in SETUP else []
    lines = setup + ["try:", f"    {line}", "except ________:", "    reactor.cool()"]
    return {
        "stage": 2, "topic": TOPICS[2], "machine": ["def run():", "    reactor.heat()", "    # risky line below"],
        "lines": lines, "labels": labels, "answer": answer,
        "hint": "Read the risky line in the try block: what goes wrong when it runs?",
        "explain": why + " Breaker pulled, reactor cooling.",
        "code": "\n".join(setup + [line]),
        "value": right,
    }


def make_request(stage, rng, difficulty="medium"):
    return (argument_request, return_request, exception_request)[stage](rng, difficulty)
