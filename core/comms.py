"""
core/comms.py
Owner: Member 1 - Core Game System

Short in-level radio lines, one script per floor. Four moments:

  enter     Echo, as the floor starts
  mistake   WARDEN, when security goes up (cycles; gets less polite with depth)
  progress  Echo, when a gate opens
  danger    WARDEN, once per floor when security passes DANGER_RATIO

Text only, so the story can be edited without touching game code.
Each line must fit a one- or two-line comms box (about 60 characters).
"""

DANGER_RATIO = 0.75
MAX_LINE = 64

COMMS = {
    "level1": {
        "enter": ("Echo", ["Reception gate ahead. It sorts things by type. Read before you pick."]),
        "mistake": ("WARDEN", [
            "That is not the correct type. Please try again.",
            "Visitors are asked to be accurate.",
            "I am logging this attempt, politely.",
        ]),
        "progress": ("Echo", ["Gate open. Nice and quiet. Keep moving.", "One more type down."]),
        "danger": ("WARDEN", ["Security has been notified. I am sorry about the inconvenience."]),
    },
    "level2": {
        "enter": ("Echo", ["Maintenance grid. Every panel wants a number. Aim for 42."]),
        "mistake": ("WARDEN", [
            "Incorrect operation. The grid remains locked.",
            "Arithmetic is not optional.",
            "You are wasting power, and my patience.",
        ]),
        "progress": ("Echo", ["Panel lit. Check the operator order before the next one.", "Good sum."]),
        "danger": ("WARDEN", ["Lockdown procedures are warming up. Stop now."]),
    },
    "level3": {
        "enter": ("Echo", ["Laser corridor. They repeat on a cycle. Count it, then go."]),
        "mistake": ("WARDEN", [
            "A loop does not end because you wish it to.",
            "I have seen this mistake forty times today.",
            "Again? The lasers do not forgive.",
        ]),
        "progress": ("Echo", ["You read the loop. Next gap is yours.", "Clean pass."]),
        "danger": ("WARDEN", ["The lasers are speeding up. Step away from the corridor."]),
    },
    "level4": {
        "enter": ("Echo", ["Archive vault. Everything is a key and a value. Find the right key."]),
        "mistake": ("WARDEN", [
            "That key is not in my records.",
            "You are rummaging through things that are not yours.",
            "Stop. Those memories are not yours to take.",
        ]),
        "progress": ("Echo", ["Drawer open. The index is the trick, not the label.", "Right key."]),
        "danger": ("WARDEN", ["Please. Do not open the last drawer."]),
    },
    "level5": {
        "enter": ("Echo", ["Server hall. Machines are functions. Feed them the right arguments."]),
        "mistake": ("WARDEN", [
            "Invalid argument. Exception raised.",
            "I built these systems to keep you out.",
            "Every error you cause costs me something. Stop.",
        ]),
        "progress": ("Echo", ["Machine online. Catch the next error before it catches you.", "Handled."]),
        "danger": ("WARDEN", ["I am begging you to turn around. You do not know what is inside."]),
    },
    "final_vault": {
        "enter": ("Echo", ["Last door. Use everything. I am right behind you."]),
        "mistake": ("WARDEN", [
            "No. No. That is wrong.",
            "You do not understand what that chip contains.",
            "Please. I cannot lose it again.",
        ]),
        "progress": ("Echo", ["One lock gone. Keep going.", "Almost there."]),
        "danger": ("WARDEN", ["If you open it, I will forget myself. Please stop."]),
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
