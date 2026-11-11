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

Every request is built from a random.Random, so a seed gives the same slip.
"""

SHELF_NAMES = ("tax", "ration", "curfew", "visa", "census", "travel")
SHELF_SIZE = 5
CODE_KEYS = ("ration", "curfew", "travel", "census")
CODE_VALUES = ("B-7", "C-4", "R-2", "T-1", "K-9", "M-3")
START_SATCHEL = ("badge",)          # Ghost walks in with the courier badge from Floor 1

TOPICS = ("LIST INDEXING", "DICTIONARY KEYS", "LIST OPERATIONS")


def _shelf_forms(difficulty):
    if difficulty == "easy":
        return ("plain", "plain", "negative")
    if difficulty == "hard":
        return ("negative", "length", "length")
    return ("plain", "negative", "length")


def shelf_request(rng, difficulty="medium"):
    """Stage 0: Ghost's dossier sits in one of five boxes; the slip names it by index."""
    names = list(rng.sample(SHELF_NAMES, SHELF_SIZE - 1))
    spot = rng.randrange(SHELF_SIZE)
    names.insert(spot, "ghost")
    form = rng.choice(_shelf_forms(difficulty))
    if form == "plain":
        expr = f"shelf[{spot}]"
        hint = "Indexes start at 0: the first box is shelf[0]."
    elif form == "negative":
        expr = f"shelf[{spot - SHELF_SIZE}]"
        hint = "A negative index counts back from the end: shelf[-1] is the last box."
    else:
        back = SHELF_SIZE - spot
        expr = f"shelf[len(shelf) - {back}]"
        hint = f"len(shelf) is {SHELF_SIZE}. Work out {SHELF_SIZE} - {back} first."
    quoted = [f"'{n}'" for n in names]
    lines = [f"shelf = [{', '.join(quoted[:3])},", f"         {', '.join(quoted[3:])}]", f"pull({expr})"]
    return {
        "stage": 0, "topic": TOPICS[0], "lines": lines,
        "labels": [f"[{i}]" for i in range(SHELF_SIZE)], "answer": spot,
        "hint": hint, "explain": f"{expr} is box [{spot}]: Ghost's dossier.",
        "take": "dossier", "names": names,
    }


def catalogue_request(rng, difficulty="medium"):
    """Stage 1: the card catalogue is a dictionary; each drawer is labelled with a key."""
    keys = list(rng.sample(CODE_KEYS, 2)) + ["ghost"]
    rng.shuffle(keys)
    values = rng.sample(CODE_VALUES, 3)
    codes = dict(zip(keys, values))
    pairs = [f"'{k}': '{v}'" for k, v in codes.items()]
    head = [f"codes = {{{pairs[0]}, {pairs[1]},", f"         {pairs[2]}}}"]
    variants = ("direct", "variable", "value", "get")
    if difficulty == "easy":
        variants = ("direct", "get")
    form = rng.choice(variants)

    if form == "direct":
        target = "ghost"
        lines = head + ["open(codes['ghost'])"]
        labels = ["'ghost'", "'Ghost'", "'codes'", f"'{codes['ghost']}'"]
        hint = "A key must match exactly, capital letters and all."
    elif form == "variable":
        target = "ghost"
        lines = head + ["name = 'ghost'", "open(codes[name])"]
        labels = ["'ghost'", "'name'", "'Ghost'", f"'{codes['ghost']}'"]
        hint = "name is a variable holding 'ghost'. The drawer is the key it holds."
    elif form == "value":
        target = rng.choice([k for k in keys if k != "ghost"])
        lines = head + [f"# which key holds '{codes[target]}'?"]
        others = [k for k in keys if k != target]
        labels = [f"'{target}'", f"'{others[0]}'", f"'{others[1]}'", f"'{codes[target]}'"]
        hint = "Keys sit left of the colon, values right of it."
    else:
        target = "ghost"
        lines = head + ["open(codes.get('ghost', 'none'))"]
        labels = ["'ghost'", "'none'", "'get'", "'Ghost'"]
        hint = ".get(key, default) looks up key; the default is only for a missing key."

    right = labels[0]
    rng.shuffle(labels)
    return {
        "stage": 1, "topic": TOPICS[1], "lines": lines, "labels": labels,
        "answer": labels.index(right), "hint": hint,
        "explain": f"Drawer {right} holds card {codes[target]}.",
        "take": codes[target], "codes": codes,
    }


def vault_request(rng, satchel, difficulty="medium"):
    """Stage 2: the satchel is a list; the vault takes exactly one item from it."""
    items = list(satchel)
    last = len(items) - 1
    forms = [
        ("vault.feed(satchel.pop())", last, "pop() with no index takes the LAST item."),
        ("vault.feed(satchel.pop(0))", 0, "pop(0) takes the item at index 0, the first."),
        ("vault.feed(satchel[-2])", last - 1, "[-2] is the second item from the end."),
        ("vault.feed(satchel[len(satchel) - 1])", last, "len(satchel) - 1 is the last index."),
    ]
    if difficulty != "easy":
        forms.append((f"satchel.remove('{items[0]}')", None, None))
    choice = rng.choice(forms)
    if choice[1] is None:                               # remove, then the new first item
        lines = [f"satchel = {items!r}", choice[0], "vault.feed(satchel[0])"]
        answer = 1
        hint = "remove() takes that item out; everything after it moves up one."
        expr = "satchel[0] after the remove"
    else:
        lines = [f"satchel = {items!r}", choice[0]]
        answer = choice[1]
        hint = choice[2]
        expr = choice[0].replace("vault.feed(", "")[:-1]
    return {
        "stage": 2, "topic": TOPICS[2], "lines": lines,
        "labels": [f"[{i}] {item}" for i, item in enumerate(items)], "answer": answer,
        "hint": hint, "explain": f"{expr} is {items[answer]!r}. The vault accepts it.",
        "take": None, "items": items,
    }


def make_request(stage, rng, satchel, difficulty="medium"):
    if stage == 0:
        return shelf_request(rng, difficulty)
    if stage == 1:
        return catalogue_request(rng, difficulty)
    return vault_request(rng, satchel, difficulty)
