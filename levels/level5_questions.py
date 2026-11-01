"""
levels/level5_questions.py

Question pool and code listing for Level 5 - Control & Recovery Center.

Level 5 is a corridor of three gates:

    Gate 1 - PARAMETERS   (parameters and arguments)   2 questions
    Gate 2 - RETURN       (return values)               2 questions
    Gate 3 - EXCEPTIONS   (raise, try/except)           1 question + terminal

Each gate has a pool larger than the number of questions asked, so every
run is a little different. Answer options are shuffled when a question is
loaded, so the correct answer is not always in the same slot.
"""

from dataclasses import dataclass


# The program shown on screen. Each question highlights the line(s) it is
# about, so the player connects the concept to real code.
CODE_LINES = (
    'def unlock_vault(level):',                # 0
    '    if level < 5:',                       # 1
    '        raise ValueError("Access denied")',  # 2
    '    return "MASTER ACCESS"',              # 3
    '',                                        # 4
    'try:',                                    # 5
    '    result = unlock_vault(int(entry))',   # 6
    '    print(result)',                       # 7
    'except ValueError as err:',               # 8
    '    print("Caught:", err)',               # 9
)

# Lines highlighted while the player uses the terminal (the try/except part).
TERMINAL_LINES = (5, 6, 7, 8, 9)


@dataclass(frozen=True)
class Question:
    """One multiple-choice question."""

    prompt: str
    answer: str
    distractors: tuple          # exactly three wrong options
    explanation: str            # shown after a correct answer
    hint: str                   # shown when the player presses H
    highlight: tuple = ()       # indexes into CODE_LINES


GATES = (
    {
        "name": "PARAMETERS",
        "label": "GATE 1",
        "color": (80, 200, 255),
        "count": 2,
    },
    {
        "name": "RETURN",
        "label": "GATE 2",
        "color": (255, 200, 80),
        "count": 2,
    },
    {
        "name": "EXCEPTIONS",
        "label": "GATE 3",
        "color": (190, 130, 255),
        "count": 1,
    },
)


QUESTION_POOL = (
    # ---------------- Gate 1: parameters and arguments ----------------
    (
        Question(
            prompt="In def unlock_vault(level):, what is level?",
            answer="parameter",
            distractors=("argument", "return value", "exception"),
            explanation=(
                "A parameter is the variable named in the function "
                "definition."
            ),
            hint="It is written inside the parentheses after def.",
            highlight=(0,),
        ),
        Question(
            prompt="In unlock_vault(int(entry)), what is int(entry)?",
            answer="argument",
            distractors=("parameter", "return value", "exception"),
            explanation=(
                "An argument is the value passed in when the function "
                "is called."
            ),
            hint="It is the value written inside the call's parentheses.",
            highlight=(6,),
        ),
        Question(
            prompt="Which keyword starts a function definition?",
            answer="def",
            distractors=("func", "define", "function"),
            explanation="Python functions are created with the def keyword.",
            hint="It is the very first word on the first line of the code.",
            highlight=(0,),
        ),
        Question(
            prompt="You call unlock_vault(7). What value does level hold?",
            answer="7",
            distractors=("5", "0", "entry"),
            explanation=(
                "The argument 7 is copied into the parameter level."
            ),
            hint="The argument becomes the parameter's value.",
            highlight=(0, 6),
        ),
    ),
    # ---------------- Gate 2: return values ----------------
    (
        Question(
            prompt="Which keyword sends a result back to the caller?",
            answer="return",
            distractors=("print", "send", "exit"),
            explanation=(
                "return hands a value back to the code that called "
                "the function."
            ),
            hint="Look at the line that gives back MASTER ACCESS.",
            highlight=(3,),
        ),
        Question(
            prompt="What does unlock_vault(7) return?",
            answer="MASTER ACCESS",
            distractors=("ACCESS DENIED", "7", "None"),
            explanation=(
                "7 is not below 5, so the raise is skipped and the "
                "return line runs."
            ),
            hint="Check the if-test first: is 7 less than 5?",
            highlight=(1, 3),
        ),
        Question(
            prompt="What does a function return if it has no return line?",
            answer="None",
            distractors=("0", "False", "an error"),
            explanation=(
                "Without a return statement Python returns None."
            ),
            hint="Python still gives back a special 'nothing' value.",
        ),
        Question(
            prompt="After return runs, what happens to the rest of the "
                   "function?",
            answer="It is skipped",
            distractors=("It still runs", "It runs twice", "It raises an error"),
            explanation=(
                "return ends the function immediately; later lines "
                "never run."
            ),
            hint="return leaves the function straight away.",
            highlight=(3,),
        ),
    ),
    # ---------------- Gate 3: exceptions ----------------
    (
        Question(
            prompt="Which structure catches a ValueError safely?",
            answer="try/except",
            distractors=("if/else", "for/while", "def/return"),
            explanation=(
                "Code that might fail goes in try; the error is "
                "handled in except."
            ),
            hint="Look at the bottom half of the code listing.",
            highlight=(5, 8),
        ),
        Question(
            prompt="Which keyword creates an error on purpose?",
            answer="raise",
            distractors=("return", "catch", "throw"),
            explanation=(
                "raise starts an exception, here a ValueError."
            ),
            hint="It is the word before ValueError in the function.",
            highlight=(2,),
        ),
        Question(
            prompt="In except ValueError as err, what does err hold?",
            answer="the exception object",
            distractors=("the return value", "the argument", "a parameter"),
            explanation=(
                "err is the caught exception; printing it shows its "
                "message."
            ),
            hint="It is what was raised, including its message.",
            highlight=(8, 9),
        ),
    ),
)


def validate_pool():
    """Raise AssertionError if the pool is malformed (used by tests)."""
    assert len(QUESTION_POOL) == len(GATES)
    for gate, pool in zip(GATES, QUESTION_POOL):
        assert len(pool) >= gate["count"]
        for q in pool:
            assert len(q.distractors) == 3
            assert q.answer not in q.distractors
            assert len(set(q.distractors)) == 3
            assert q.explanation and q.hint
            assert all(0 <= i < len(CODE_LINES) for i in q.highlight)