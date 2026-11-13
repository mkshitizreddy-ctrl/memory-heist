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
        "warden": True,
        "title": "THE MEMORY HEIST",
        "lines": [
            "NovaCorp's security AI, WARDEN, has locked the Master Memory chip",
            "away. It holds every secret the company ever erased.",
            "Ghost has until the building's sleep cycle ends.",
            "WARDEN reads logic, so Ghost must think like code.",
        ],
    },
    "level1": {
        "warden": True,
        "title": "LEVEL 1 - THE RECEPTION LOBBY",
        "concept": "Data types",
        "lines": [
            "The intake belt is jammed and parcels are piled on the floor.",
            "Ghost pulls on a courier vest. File each parcel in its chute for a stamp.",
        ],
    },
    "level2": {
        "warden": True,
        "title": "LEVEL 2 - THE MAINTENANCE GRID",
        "concept": "Operators",
        "lines": [
            "Power to the lower floors runs through three relay bays and wall screens.",
            "Stand on the breaker whose value makes it true and press E to throw it.",
        ],
    },
    "level3": {
        "warden": True,
        "title": "LEVEL 3 - THE NIGHT PATROL",
        "concept": "Loops",
        "lines": [
            "NovaCorp's night patrol is a loop: lanes fire, cameras sweep, a robot walks.",
            "Answer the loop question at each door. Move when the pattern allows.",
        ],
    },
    "level4": {
        "warden": True,
        "title": "LEVEL 4 - THE RECORDS ARCHIVE",
        "concept": "Lists and dictionaries",
        "lines": [
            "NovaCorp keeps a file on every citizen. Yours is down here.",
            "Fill the request slip: a list index, a dictionary key, a list method.",
        ],
    },
    "level5": {
        "warden": True,
        "title": "LEVEL 5 - THE SERVER HALL",
        "concept": "Functions and exceptions",
        "lines": [
            "WARDEN's functions run the whole building.",
            "Pass the right arguments and catch the errors it throws.",
        ],
    },
    "final_vault": {
        "warden": True,
        "title": "FINAL VAULT - WARDEN'S CORE",
        "concept": "Everything combined",
        "lines": [
            "Six locks ring WARDEN's core, one for every floor you crossed.",
            "Open them all, take the Master Memory chip, and get out.",
        ],
    },
    "outro": {
        "title": "MISSION COMPLETE",
        "lines": [
            "The Master Memory chip is in Ghost's hand, and WARDEN goes quiet.",
            "Every erased secret is out. Master Memory acquired.",
        ],
    },
}


def beat_for(key):
    """Return the story beat for 'intro', 'outro' or a level name, else None."""
    return STORY.get(key)
