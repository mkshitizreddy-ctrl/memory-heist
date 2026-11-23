"""
levels/archive_requests.py
Owner: Member 1 - Core Game System (Floor 4 rebuilt on the shared kit)

The three archive requests on Floor 4, written as plain data so they can be
tested without a screen.  Each request is a dict:

    stage     0 list index (pull a shelf box), 1 dictionary key (open a drawer),
              2 list operation (feed a satchel item to the vault)
    topic     the concept, shown on the request board
    lines     the Python on the request slip
    labels    what is written on each box, drawer or tray (the answers)
    answer    index of the right label
    hint      shown when Echo's drone scans the slip (if hints are on)
    explain   one line said when the right one is chosen
    take      what goes into the satchel when it is right (None for the last request)
    walk      a short step-by-step working, shown after a second wrong answer (hints on)
    reasons   {label index: why that choice is wrong} for the common mistakes

Each difficulty has its OWN forms for every request (FORMS below): easy, medium
and hard never share a form, so a hard slip is never an easy slip in disguise.

Every request is built from a random.Random, so a seed gives the same slip.
"""

SHELF_NAMES = ("tax", "ration", "curfew", "visa", "census", "travel")
SHELF_SIZE = 5
CODE_KEYS = ("ration", "curfew", "travel", "census")
CODE_VALUES = ("B-7", "C-4", "R-2", "T-1", "K-9", "M-3")
START_SATCHEL = ("badge",)          # Ghost walks in with the courier badge from Floor 1

TOPICS = ("LIST INDEXING", "DICTIONARY KEYS", "LIST OPERATIONS", "LOOPS: THE VAULT DIAL")

# The forms each difficulty may use, per request.  No form appears in two tiers.
FORMS = {
    0: {"easy": ("plain", "negative", "index_call"),
        "medium": ("length", "slice", "step"),
        "hard": ("reverse", "slice_neg", "step_back")},
    1: {"easy": ("direct", "get", "in_check"),
        "medium": ("variable", "value", "lower"),
        "hard": ("get_missing", "update", "keys_index")},
    2: {"easy": ("pop", "pop0", "minus2"),
        "medium": ("len_last", "remove", "slice1"),
        "hard": ("reverse", "rotate", "insert_pop")},
    3: {"easy": ("sum", "range_len", "last"),
        "medium": ("range_sum", "while", "evens"),
        "hard": ("nested", "weighted", "comp")},
}


def forms_for(stage, difficulty):
    """The form names a request of `stage` may take at `difficulty`."""
    tiers = FORMS[stage]
    return tiers.get(difficulty, tiers["medium"])


def _tier(difficulty):
    return difficulty if difficulty in ("easy", "medium", "hard") else "medium"


# --- stage 0: the shelf (list indexing) ----------------------------------------------
def _shelf_expr(form, spot):
    """(expression naming box `spot`, hint, working) for a shelf form."""
    n = SHELF_SIZE
    if form == "plain":
        return (f"shelf[{spot}]", "Indexes start at 0: the first box is shelf[0].",
                f"Count from zero: {spot} steps along is box [{spot}].")
    if form == "negative":
        return (f"shelf[{spot - n}]", "A negative index counts back from the end: shelf[-1] is the last box.",
                f"Counting back from the end (-1 is the last box), {spot - n} lands on box [{spot}].")
    if form == "index_call":
        return ("shelf.index('ghost')", ".index(x) gives the position where x sits in the list.",
                f"'ghost' sits at position {spot}, so pull(shelf.index('ghost')) is box [{spot}].")
    if form == "length":
        back = n - spot
        return (f"shelf[len(shelf) - {back}]", f"len(shelf) is {n}. Work out {n} - {back} first.",
                f"len(shelf) is {n}; {n} - {back} = {spot}, so box [{spot}].")
    if form == "slice":
        a = max(0, spot - 1)
        b = min(n, spot + 2)
        k = spot - a
        return (f"shelf[{a}:{b}][{k}]",
                f"shelf[{a}:{b}] is a smaller list starting at box [{a}]; then take its item [{k}].",
                f"shelf[{a}:{b}] starts at box [{a}]; item [{k}] of it is box [{a + k}].")
    if form == "step":
        start = spot % 2
        k = spot // 2
        return (f"shelf[{start}::2][{k}]",
                f"shelf[{start}::2] takes every second box starting at [{start}]; then item [{k}] of that.",
                f"Every second box from [{start}] is {list(range(start, n, 2))}; item [{k}] is box [{spot}].")
    if form == "reverse":
        j = n - 1 - spot
        return (f"shelf[::-1][{j}]", "shelf[::-1] is the shelf reversed: its item [0] is the last box.",
                f"Reversed, item [{j}] is box [{n - 1 - j}] = [{spot}] of the original.")
    if form == "slice_neg":
        a = max(0, spot - 1) - n
        b = min(n, spot + 2) - n
        stop = f"{b}" if b != 0 else ""
        k = spot - (a + n)
        return (f"shelf[{a}:{stop}][{k}]", f"shelf[{a}:{stop}] counts both ends from the back. Find where it starts.",
                f"{a} is box [{a + n}], so item [{k}] of the slice is box [{spot}].")
    # step_back
    if spot % 2 == 0:
        return (f"shelf[::-2][{(n - 1 - spot) // 2}]", "shelf[::-2] takes every second box walking backwards from the end.",
                f"Backwards in twos from [4]: 4, 2, 0. Item [{(n - 1 - spot) // 2}] is box [{spot}].")
    return (f"shelf[-2::-2][{(n - 2 - spot) // 2}]", "shelf[-2::-2] starts at the second-last box and steps back by two.",
            f"Backwards in twos from [3]: 3, 1. Item [{(n - 2 - spot) // 2}] is box [{spot}].")


def shelf_request(rng, difficulty="medium"):
    """Stage 0: Ghost's dossier sits in one of five boxes; the slip names it by index."""
    difficulty = _tier(difficulty)
    names = list(rng.sample(SHELF_NAMES, SHELF_SIZE - 1))
    spot = rng.randrange(SHELF_SIZE)
    names.insert(spot, "ghost")
    form = rng.choice(forms_for(0, difficulty))
    expr, hint, walk = _shelf_expr(form, spot)
    quoted = [f"'{n}'" for n in names]
    lines = [f"shelf = [{', '.join(quoted[:3])},", f"         {', '.join(quoted[3:])}]", f"pull({expr})"]
    reasons = {}
    for i in range(SHELF_SIZE):
        if i == spot:
            continue
        if abs(i - spot) == 1:
            reasons[i] = "Off by one: the slip's index lands on the box next to this one. Indexes start at 0."
        else:
            reasons[i] = f"Box [{i}] holds '{names[i]}', not Ghost's dossier."
    return {
        "stage": 0, "topic": TOPICS[0], "lines": lines, "form": form, "difficulty": difficulty,
        "labels": [f"[{i}]" for i in range(SHELF_SIZE)], "answer": spot,
        "hint": hint, "walk": walk, "reasons": reasons,
        "explain": f"{expr} is box [{spot}]: Ghost's dossier.",
        "take": "dossier", "names": names,
    }


# --- stage 1: the card catalogue (dictionary keys) -----------------------------------
def catalogue_request(rng, difficulty="medium"):
    """Stage 1: the card catalogue is a dictionary; each drawer is labelled with a key."""
    difficulty = _tier(difficulty)
    keys = list(rng.sample(CODE_KEYS, 2)) + ["ghost"]
    rng.shuffle(keys)
    values = rng.sample(CODE_VALUES, 3)
    codes = dict(zip(keys, values))
    pairs = [f"'{k}': '{v}'" for k, v in codes.items()]
    head = [f"codes = {{{pairs[0]}, {pairs[1]},", f"         {pairs[2]}}}"]
    form = rng.choice(forms_for(1, difficulty))
    others_of = lambda t: [k for k in keys if k != t]          # noqa: E731
    reasons = {}

    def labelled(target, extras, value=None):
        value = codes[target] if value is None else value
        return [f"'{target}'"] + [f"'{e}'" for e in extras] + [f"'{value}'"]

    if form == "direct":
        target = "ghost"
        lines = head + ["open(codes['ghost'])"]
        labels = ["'ghost'", "'Ghost'", "'codes'", f"'{codes['ghost']}'"]
        hint = "A key must match exactly, capital letters and all."
        walk = "open(codes['ghost']) opens the drawer whose key is the text 'ghost', exactly."
    elif form == "get":
        target = "ghost"
        lines = head + ["open(codes.get('ghost', 'none'))"]
        labels = ["'ghost'", "'none'", "'get'", "'Ghost'"]
        hint = ".get(key, default) looks up key; the default is only for a missing key."
        walk = "'ghost' is a key, so .get finds it and the default 'none' is never used."
    elif form == "in_check":
        target = "ghost"
        lines = head + ["if 'ghost' in codes:", "    open(codes['ghost'])"]
        labels = ["'ghost'", "'in'", "'Ghost'", f"'{codes['ghost']}'"]
        hint = "'x' in codes asks whether x is a KEY. It is, so the next line runs."
        walk = "'ghost' in codes is True, so open(codes['ghost']) runs: drawer 'ghost'."
    elif form == "variable":
        target = "ghost"
        lines = head + ["name = 'ghost'", "open(codes[name])"]
        labels = ["'ghost'", "'name'", "'Ghost'", f"'{codes['ghost']}'"]
        hint = "name is a variable holding 'ghost'. The drawer is the key it holds."
        walk = "name holds 'ghost', so codes[name] is codes['ghost']: drawer 'ghost'."
    elif form == "value":
        target = rng.choice(others_of("ghost"))
        lines = head + [f"# which key holds '{codes[target]}'?"]
        others = others_of(target)
        labels = labelled(target, others[:2])
        hint = "Keys sit left of the colon, values right of it."
        walk = f"'{codes[target]}' is on the right of a colon, so the key is the text on its left: '{target}'."
    elif form == "lower":
        target = "ghost"
        lines = head + ["name = 'GHOST'.lower()", "open(codes[name])"]
        labels = ["'ghost'", "'GHOST'", "'name'", f"'{codes['ghost']}'"]
        hint = ".lower() turns every letter small: 'GHOST' becomes 'ghost'."
        walk = "'GHOST'.lower() is 'ghost', so codes[name] is codes['ghost']."
    elif form == "get_missing":
        target = "ghost"
        lines = head + ["key = codes.get('vault', 'ghost')", "open(codes[key])"]
        labels = ["'ghost'", "'vault'", "'none'", f"'{codes['ghost']}'"]
        hint = "There is no 'vault' key, so .get gives back its default: the second argument."
        walk = "'vault' is missing, so key becomes the default 'ghost'; codes[key] is drawer 'ghost'."
    elif form == "update":
        target = rng.choice(others_of("ghost"))
        lines = head + [f"codes['{target}'] = codes['ghost']", f"open(codes['{target}'])"]
        labels = [f"'{target}'", "'ghost'", "'codes'", f"'{codes['ghost']}'"]
        hint = "The first line overwrites that key's value. The drawer you open is the key on line 2."
        walk = f"Line 2 opens codes['{target}'], so the drawer is labelled '{target}'."
        codes = dict(codes)
        codes[target] = codes["ghost"]
    else:  # keys_index
        index = rng.randrange(3)
        target = keys[index]
        lines = head + [f"open(list(codes)[{index}])"]
        others = others_of(target)
        labels = labelled(target, others[:2])
        hint = "list(codes) is the list of keys, in the order they were written."
        walk = f"The keys in order are {keys}. Item [{index}] is '{target}'."

    right = labels[0]
    rng.shuffle(labels)
    answer = labels.index(right)
    for i, label in enumerate(labels):
        if i == answer:
            continue
        if label.strip("'").lower() == target and label.strip("'") != target:
            reasons[i] = "Keys are case-sensitive: capital letters make it a different key."
        elif label.strip("'") == codes.get(target):
            reasons[i] = "That is the card's VALUE. Drawers are labelled with keys."
        else:
            reasons[i] = f"That drawer is not the key the slip asks for ({right})."
    return {
        "stage": 1, "topic": TOPICS[1], "lines": lines, "labels": labels, "form": form,
        "difficulty": difficulty, "answer": answer, "hint": hint, "walk": walk, "reasons": reasons,
        "explain": f"Drawer {right} holds card {codes[target]}.",
        "take": codes[target], "codes": codes,
    }


# --- stage 2: the vault (list operations) --------------------------------------------
def _vault_form(form, items):
    """(lines after the satchel line, answer index, hint, expression, working)."""
    last = len(items) - 1
    first = items[0]
    if form == "pop":
        return (["vault.feed(satchel.pop())"], last, "pop() with no index takes the LAST item.",
                "satchel.pop()", f"pop() removes the last item, [{last}].")
    if form == "pop0":
        return (["vault.feed(satchel.pop(0))"], 0, "pop(0) takes the item at index 0, the first.",
                "satchel.pop(0)", "pop(0) removes the first item, [0].")
    if form == "minus2":
        return (["vault.feed(satchel[-2])"], last - 1, "[-2] is the second item from the end.",
                "satchel[-2]", f"-1 is [{last}], so -2 is [{last - 1}].")
    if form == "len_last":
        return (["vault.feed(satchel[len(satchel) - 1])"], last, "len(satchel) - 1 is the last index.",
                "satchel[len(satchel) - 1]", f"len is {len(items)}; {len(items)} - 1 = {last}.")
    if form == "remove":
        return ([f"satchel.remove('{first}')", "vault.feed(satchel[0])"], 1,
                "remove() takes that item out; everything after it moves up one.",
                "satchel[0] after the remove", f"'{first}' leaves, so the old [1] is now [0].")
    if form == "slice1":
        return (["vault.feed(satchel[1:][0])"], 1, "satchel[1:] is everything except the first item.",
                "satchel[1:][0]", "satchel[1:] starts at [1], so its item [0] is [1].")
    if form == "reverse":
        return (["vault.feed(satchel[::-1][0])"], last, "satchel[::-1] is the list reversed.",
                "satchel[::-1][0]", f"Reversed, the first item is the old last, [{last}].")
    if form == "rotate":
        return (["satchel.append(satchel.pop(0))", "vault.feed(satchel.pop(0))"], 1,
                "The first line moves the first item to the back. Then pop(0) takes the new first.",
                "satchel.pop(0) after the rotate", f"'{first}' goes to the back, so [1] is now first.")
    # insert_pop
    return (["satchel.insert(0, satchel.pop())", "vault.feed(satchel[0])"], last,
            "pop() takes the last item; insert(0, x) puts it at the front.",
            "satchel[0] after the insert", f"The last item, [{last}], moves to the front and is fed.")


def vault_request(rng, satchel, difficulty="medium"):
    """Stage 2: the satchel is a list; the vault takes exactly one item from it."""
    difficulty = _tier(difficulty)
    items = list(satchel)
    form = rng.choice(forms_for(2, difficulty))
    steps, answer, hint, expr, walk = _vault_form(form, items)
    lines = [f"satchel = {items!r}"] + steps
    reasons = {}
    for i, item in enumerate(items):
        if i != answer:
            reasons[i] = f"That is [{i}], '{item}'. Follow the list line by line: the vault is fed [{answer}]."
    return {
        "stage": 2, "topic": TOPICS[2], "lines": lines, "form": form, "difficulty": difficulty,
        "labels": [f"[{i}] {item}" for i, item in enumerate(items)], "answer": answer,
        "hint": hint, "walk": walk, "reasons": reasons,
        "explain": f"{expr} is {items[answer]!r}. The vault accepts it.",
        "take": None, "items": items,
    }


# --- stage 3: the vault dial (loops) ---------------------------------------------------
DIAL_TRAYS = 3


def _dial_form(form, rng):
    """(code lines, hint, working, the classic wrong answer) for a dial form.

    The slip's answer is worked out by running its own code, so it can never drift."""
    if form == "sum":
        a, b, c = rng.sample(range(2, 10), 3)
        return ([f"total = 0", f"for n in [{a}, {b}, {c}]:", "    total += n", "vault.dial(total)"],
                "total adds every number in the list, one pass per number.",
                f"{a} + {b} + {c}.", None)
    if form == "range_len":
        k = rng.randrange(4, 10)
        return (["steps = 0", f"for i in range({k}):", "    steps += 1", "vault.dial(steps)"],
                "range(k) runs the loop k times (it counts 0 up to k - 1).",
                f"range({k}) gives {k} passes, so steps ends at {k}.", k + 1)
    if form == "last":
        nums = rng.sample(range(2, 20), 4)
        return ([f"for n in {nums}:", "    last = n", "vault.dial(last)"],
                "last is overwritten on every pass, so the final pass wins.",
                f"The final pass sets last to {nums[-1]}.", nums[0])
    if form == "range_sum":
        a = rng.randrange(1, 4)
        b = a + rng.randrange(3, 6)
        return (["total = 0", f"for i in range({a}, {b}):", "    total += i", "vault.dial(total)"],
                f"range({a}, {b}) starts at {a} and stops BEFORE {b}.",
                f"It adds {', '.join(str(i) for i in range(a, b))}.", sum(range(a, b + 1)))
    if form == "while":
        step = rng.choice((2, 3, 4))
        limit = rng.randrange(10, 18)
        start = rng.randrange(0, 3)
        return ([f"n = {start}", f"while n < {limit}:", f"    n += {step}", "vault.dial(n)"],
                f"The loop stops once n is no longer below {limit}; n keeps the value it had then.",
                f"n counts up by {step}: it ends on the first value that is {limit} or more.", None)
    if form == "evens":
        nums = rng.sample(range(2, 15), 4)
        return (["total = 0", f"for n in {nums}:", "    if n % 2 == 0: total += n", "vault.dial(total)"],
                "n % 2 == 0 is true for even numbers only; odd numbers are skipped.",
                f"Only the even numbers are added: {[n for n in nums if n % 2 == 0]}.", sum(nums))
    if form == "nested":
        a, b = rng.randrange(2, 5), rng.randrange(2, 5)
        return (["count = 0", f"for i in range({a}):", f"    for j in range({b}): count += 1", "vault.dial(count)"],
                "The inner loop runs completely for every pass of the outer loop.",
                f"{a} outer passes x {b} inner passes = {a * b}.", a + b)
    if form == "weighted":
        a, step = rng.randrange(3, 6), rng.randrange(2, 5)
        return (["total = 0", f"for i in range({a}):", f"    total += i * {step}", "vault.dial(total)"],
                f"i takes the values 0 to {a - 1}; each is multiplied by {step} before it is added.",
                f"({' + '.join(str(i) for i in range(a))}) x {step}.", step * sum(range(1, a + 1)))
    nums = rng.sample(range(1, 12), 4)
    t = rng.randrange(3, 7)
    return ([f"nums = {nums}", f"code = sum([n * 2 for n in nums if n > {t}])", "vault.dial(code)"],
            f"The list keeps only numbers greater than {t}, doubles them, and sum() adds the result.",
            f"Numbers above {t}: {[n for n in nums if n > t]}; doubled and added.",
            sum(n * 2 for n in nums))


def dial_request(rng, difficulty="medium"):
    """Stage 3: the vault asks for its code; the code is what the slip's loop leaves in the dial."""
    difficulty = _tier(difficulty)
    form = rng.choice(forms_for(3, difficulty))
    for _ in range(50):
        lines, hint, walk, slip = _dial_form(form, rng)
        sent = []
        scope = {"__builtins__": {"range": range, "sum": sum},
                 "vault": type("V", (), {"dial": staticmethod(sent.append)})}
        exec("\n".join(lines), scope)                       # noqa: S102 - one namespace: works on every Python
        answer = sent[-1]
        if answer >= 1 and slip != answer:
            break
    pool = [v for v in (slip, answer + 1, answer - 1, answer + 2, answer - 2, answer * 2) if v and v >= 1 and v != answer]
    values = []
    for v in pool:
        if v not in values:
            values.append(v)
    values = values[:DIAL_TRAYS - 1] + [answer]
    right = str(answer)
    rng.shuffle(values)
    labels = [str(v) for v in values]
    reasons = {}
    for i, v in enumerate(values):
        if v == answer:
            continue
        if slip is not None and v == slip:
            reasons[i] = "The classic slip: check exactly where the loop starts and where it stops."
        elif abs(v - answer) == 1:
            reasons[i] = "Off by one. Trace the first and the last pass of the loop."
        else:
            reasons[i] = "Not what the loop leaves in the dial. Trace it pass by pass."
    return {
        "stage": 3, "topic": TOPICS[3], "lines": lines, "form": form, "difficulty": difficulty,
        "labels": labels, "answer": labels.index(right), "hint": hint, "walk": walk, "reasons": reasons,
        "explain": f"The loop leaves {answer} in the dial. The vault accepts it.",
        "take": None, "value": answer,
    }


def make_request(stage, rng, satchel, difficulty="medium"):
    if stage == 0:
        return shelf_request(rng, difficulty)
    if stage == 1:
        return catalogue_request(rng, difficulty)
    if stage == 2:
        return vault_request(rng, satchel, difficulty)
    return dial_request(rng, difficulty)


def why_wrong(request, index):
    """One line saying why picking `index` is wrong."""
    return request.get("reasons", {}).get(index, "That is not what the slip asks for.")
