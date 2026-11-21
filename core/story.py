"""
core/story.py
Owner: Member 1 - Core Game System

All story text in one place: the cast and one "beat" per part of the run
(intro, each level, ending). A level's "memory" is the fragment of Ghost's past
that floor gives back; it shows in gold on the next card, under its text.
Screens read from here, so changing the story
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
            "NovaCorp's tower never sleeps. Its security AI, WARDEN, sees everything.",
            "When NovaCorp wants someone forgotten, WARDEN erases them.",
            "Ghost was erased six years ago. No name. No file. No past.",
            "Tonight Ghost goes down into the tower for the Master Memory chip.",
        ],
    },
    "level1": {
        "warden": True,
        "memory": "A lobby. Rain on the glass. Someone handing me coffee, saying my name.",
        "title": "FLOOR 1 - THE RECEPTION LOBBY",
        "concept": "Data types",
        "lines": [
            "Front door, courier vest, a fake parcel. The intake belt is jammed.",
            "NovaCorp sorts everything by type, even people.",
            "File each parcel in the chute for its type to earn the lift stamp.",
        ],
    },
    "level2": {
        "warden": True,
        "memory": "I wired this grid. My handwriting is on the breaker labels.",
        "title": "FLOOR 2 - THE MAINTENANCE GRID",
        "concept": "Operators",
        "lines": [
            "The stamp worked. The service lift drops Ghost into the power grid.",
            "Cut main power and the cameras below fall back to a backup loop.",
            "Read each relay's screen, stand on the breaker that answers it, press E.",
        ],
    },
    "level3": {
        "warden": True,
        "memory": "I walked these beams once. Same cycle, every night, for a year.",
        "title": "FLOOR 3 - THE NIGHT PATROL",
        "concept": "Loops",
        "lines": [
            "The grid is down. The security wing runs on its backup loop.",
            "Lasers cycle, a sentry sweeps, the reactor core pulses. It all repeats.",
            "Read each room's cycle, cross when it allows, answer at the gate.",
        ],
    },
    "level4": {
        "warden": True,
        "memory": "Name: REDACTED. Team: WARDEN logic. Status: erased. By: self.",
        "title": "FLOOR 4 - THE RECORDS ARCHIVE",
        "concept": "Lists and dictionaries",
        "lines": [
            "A night-shift badge says courier. The archivist will send slips.",
            "NovaCorp keeps a file on every citizen. Echo: \"G... yours is too.\"",
            "Fill each slip: a list index, a dictionary key, a list method.",
        ],
    },
    "level5": {
        "warden": True,
        "memory": "I wrote the function that told WARDEN to erase. I wrote it for me.",
        "title": "FLOOR 5 - THE SERVER HALL",
        "concept": "Functions and exceptions",
        "lines": [
            "Your file says access level 7. WARDEN's console wants one.",
            "Every rack here is a function WARDEN calls. One of them erases people.",
            "Pass the right arguments, catch its errors, shut the routine down.",
        ],
    },
    "final_vault": {
        "warden": True,
        "memory": "I asked to forget. WARDEN couldn't. So it remembered for me.",
        "title": "FINAL VAULT - WARDEN'S CORE",
        "concept": "Everything combined",
        "lines": [
            "Six locks ring WARDEN's core, one for every floor you crossed.",
            "Behind them is every memory WARDEN ever took. Including yours.",
            "Open them all, take the Master Memory chip, and get out.",
        ],
    },
    "outro": {
        "title": "MISSION COMPLETE",
        "lines": [
            "WARDEN: \"...Take it, then. Everything I ever erased.\"",
            "Ghost: \"I asked you to forget me. You remembered instead.\"",
            "The chip uploads. Forty years of names come back at once.",
            "Echo, quietly: \"Welcome back, Ash.\" And the tower finally sleeps.",
        ],
    },
}


def memory_for(level):
    """The memory fragment a cleared level gives back, or None."""
    return STORY.get(level, {}).get("memory")


def beat_for(key):
    """Return the story beat for 'intro', 'outro' or a level name, else None."""
    return STORY.get(key)
