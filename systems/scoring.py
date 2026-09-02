"""
systems/scoring.py
Owner: Member 5

Tracks score across the whole run. Hints and time penalties should
call into this rather than levels touching score directly, so all
scoring rules live in one place.
"""


class ScoreTracker:
    def __init__(self):
        self.score = 0

    def add(self, points):
        self.score += points

    def penalize(self, points):
        self.score = max(0, self.score - points)
