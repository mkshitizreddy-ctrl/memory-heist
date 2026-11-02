"""What the player did on one floor: points, time and mistakes.

The game takes a snapshot when a floor starts and another when it ends; the
difference is shown on the "floor cleared" panel of the next briefing card.
Pure functions, so they are easy to test.
"""

MAX_STARS = 3


def snapshot(score, time_remaining, mistakes):
    return {"score": int(score), "time": float(time_remaining), "mistakes": int(mistakes)}


def stars_for(mistakes):
    """Three stars for a clean floor, two for one mistake, one otherwise."""
    if mistakes <= 0:
        return 3
    if mistakes == 1:
        return 2
    return 1


def floor_summary(name, start, end):
    """The floor's result, or None when there is no starting snapshot."""
    if start is None or end is None:
        return None
    mistakes = max(0, end["mistakes"] - start["mistakes"])
    return {
        "name": name,
        "points": end["score"] - start["score"],
        "seconds": max(0, int(round(start["time"] - end["time"]))),
        "mistakes": mistakes,
        "stars": stars_for(mistakes),
    }


def format_duration(seconds):
    seconds = max(0, int(seconds))
    return f"{seconds // 60}:{seconds % 60:02d}"
