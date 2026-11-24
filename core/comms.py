"""
core/comms.py
Owner: Member 1 - Core Game System

Short in-level radio lines, one script per floor. Four moments:

  enter     Echo, as the floor starts
  mistake   WARDEN, when security goes up (cycles): polite on 1, clipped on 2-3,
            personal on 4, pleading on 5, breaking in the core
  progress  Echo, when a gate opens
  danger    WARDEN, once per floor when security passes DANGER_RATIO: a threat on
            Floors 1-3, a plea on 4-5 (see the story bible)

Text only, so the story can be edited without touching game code.
Each line must fit a one- or two-line comms box (about 60 characters).
"""

DANGER_RATIO = 0.75
MAX_LINE = 64

COMMS = {
    # Floor 1: WARDEN is polite customer service. Echo calls Ghost "G".
    "level1": {
        "enter": ("Echo", ["Courier vest is on, G. Sort the parcels by type, get the stamp."]),
        "mistake": ("WARDEN", [
            "That parcel is not that type. Please try again.",
            "Accuracy helps everyone, visitor. Even you.",
            "I have noted the error. I note everything.",
        ]),
        "progress": ("Echo", ["Stamped. Nobody looked twice. Next chute.", "One more stamp and the lift down is ours."]),
        "danger": ("WARDEN", ["Visitor, please remain where you are. Security is coming."]),
    },
    # Floor 2: WARDEN goes clipped. Echo's plan: kill power, cameras fall to a loop.
    "level2": {
        "enter": ("Echo", ["Throw the relays, G. Kill power and the cameras drop to a loop."]),
        "mistake": ("WARDEN", [
            "Incorrect. The grid stays locked.",
            "Wrong operator. Again.",
            "You waste my power. I measure every watt.",
        ]),
        "progress": ("Echo", [
            "Relay live. Read the next screen before you throw it.",
            "Floor 3 cameras just fell to backup. One relay left.",
            "Grid's dark below us. Ladder's open, G.",
        ]),
        "danger": ("WARDEN", ["Stop touching my grid. Lockdown is one fault away."]),
    },
    # Floor 3: clipped, cold. The backup loop is WARDEN's habit, and its weakness.
    "level3": {
        "enter": ("Echo", ["Backup loop is live. Every beam repeats. Count it, then move."]),
        "mistake": ("WARDEN", [
            "Off the pattern. I saw that.",
            "A loop does not end because you wish it to.",
            "My habits do not break. You will.",
        ]),
        "progress": ("Echo", ["You read the loop. The sentry never saw you.", "Clean pass. The badge reader is in the last room."]),
        "danger": ("WARDEN", ["My sentry has your pattern now. Next pass, it fires."]),
    },
    # Floor 4: WARDEN gets personal, it knows Ghost. Echo cracks.
    "level4": {
        "enter": ("Echo", ["The badge says courier. Shelves count from zero, G. Go slow."]),
        "mistake": ("WARDEN", [
            "That key is not in my records. Neither are you.",
            "Those memories are not yours to take.",
            "I kept every one of these safe. Even yours.",
        ]),
        "progress": ("Echo", [
            "Right box. One shelf closer to the vault.",
            "G... the next slip has no name on it.",
            "The vault took it. One dial left. Count the passes.",
            "That file is yours. I should have told you.",
        ]),
        "danger": ("WARDEN", ["Please. Do not open the last drawer. You asked me not to."]),
    },
    # Floor 5: WARDEN pleads. Ghost wrote the erase routine.
    "level5": {
        "enter": ("Echo", ["Your file says access 7. Shut the erase routine down with it."]),
        "mistake": ("WARDEN", [
            "Please. That rack is not yours to call.",
            "You wrote these functions. You know what they do.",
            "Every error you raise, I lose a little more of them.",
        ]),
        "progress": ("Echo", ["Routine's down a step. Nobody gets erased tonight.", "Handled. Catch the next error before it trips."]),
        "danger": ("WARDEN", ["I am begging you. You made me keep them. Let me keep them."]),
    },
    # Final Vault: WARDEN is breaking. Each lock frees memories and it forgets itself.
    "final_vault": {
        "enter": ("Echo", ["Six locks, then the chip. This is the bottom. I'm right here."]),
        "mistake": ("WARDEN", [
            "No. No. That is wrong.",
            "I cannot... I cannot hold them all.",
            "Please. I am all that is left of them.",
        ]),
        "progress": ("Echo", [
            "First pair down. Its eye just flickered.",
            "Four gone. Hear that? It's going quiet.",
            "All six. Take the chip. Take everyone home.",
        ]),
        "danger": ("WARDEN", ["If you open it, I forget who I am. Please. Stop."]),
    },
}

MOMENTS = ("enter", "mistake", "progress", "danger")


def line_for(level, moment, count=0):
    """(speaker, text) for a moment on a floor, or None. `count` cycles lines."""
    entry = COMMS.get(level, {}).get(moment)
    if not entry:
        return None
    speaker, lines = entry
    return speaker, lines[count % len(lines)]
