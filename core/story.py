"""
core/story.py
Owner: Member 1 - Core Game System

All story text in one place: the cast and one "beat" per part of the run
(intro, each level, ending). Screens read from here, so changing the story
never means touching game code. Keep each line short enough for a card.
"""

HERO = "Ghost"
PARTNER = "Echo"
ANTAGONIST = "WARDEN"

STORY = {
    "intro": {
        "title": "THE MEMORY HEIST",
        "lines": [
            "NovaCorp's security AI, WARDEN, has locked the Master Memory chip",
            "away. It holds every secret the company ever erased.",
            "Ghost has until the building's sleep cycle ends.",
            "WARDEN reads logic, so Ghost must think like code.",
        ],
    },
    "level1": {
        "title": "LEVEL 1 - THE SECURITY GATE",
        "concept": "Data types",
        "lines": [
            "The gate checks what you are before it lets you in.",
            "Prove clearance 5 by naming the right data types.",
        ],
    },
    "level2": {
        "title": "LEVEL 2 - THE SECURITY GRID",
        "concept": "Operators",
        "lines": [
            "The grid only opens for the right operation.",
            "Combine the numbers to reach the code: 42.",
        ],
    },
    "level3": {
        "title": "LEVEL 3 - THE LASER LOOP",
        "concept": "Loops",
        "lines": [
            "The lasers sweep in cycles that never stop on their own.",
            "Understand the loop, then slip through the gaps.",
        ],
    },
    "level4": {
        "title": "LEVEL 4 - THE MEMORY VAULT",
        "concept": "Lists and dictionaries",
        "lines": [
            "The vault stores everything as keys and values.",
            "Collect the right items and look up the Memory Chip.",
        ],
    },
    "level5": {
        "title": "LEVEL 5 - THE CONTROL CENTER",
        "concept": "Functions and exceptions",
        "lines": [
            "WARDEN's functions run the whole building.",
            "Pass the right arguments and catch the errors it throws.",
        ],
    },
    "final_vault": {
        "title": "FINAL VAULT - WARDEN'S LAST STAND",
        "concept": "Everything combined",
        "lines": [
            "One door left, and WARDEN throws everything at you.",
            "Use all you have learned to open it.",
        ],
    },
    "outro": {
        "title": "MISSION COMPLETE",
        "lines": [
            "The Memory Chip is in Ghost's hand, and WARDEN goes quiet.",
            "Every erased secret is out. Master Memory acquired.",
        ],
    },
}


def beat_for(key):
    """Return the story beat for 'intro', 'outro' or a level name, else None."""
    return STORY.get(key)
