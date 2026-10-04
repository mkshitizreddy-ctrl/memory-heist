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
