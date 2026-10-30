# Each whole second left on the run timer is worth this many points.
POINTS_PER_SECOND_LEFT = 1


def final_score(base, seconds_left, multiplier):
    """Combine the run score, time left and difficulty into the final score.

    total = round((base + whole seconds left * POINTS_PER_SECOND_LEFT) * multiplier)
    """
    whole_seconds = max(0, int(seconds_left or 0))
    time_bonus = whole_seconds * POINTS_PER_SECOND_LEFT
    return {
        "base": base,
        "time_bonus": time_bonus,
        "multiplier": multiplier,
        "total": round((base + time_bonus) * multiplier),
    }


class ScoreTracker:
    def __init__(self):
        self.score = 0

    def add(self, points: int):
        self.score += points

    def penalize(self, points: int):
        self.score = max(0, self.score - points)

    def get_score(self) -> int:
        return self.score

    def reset(self):
        self.score = 0
