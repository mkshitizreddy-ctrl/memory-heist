"""
systems/timer.py
Owner: Member 5

Simple countdown timer used for timed challenges.
"""


class Timer:
    def __init__(self, seconds):
        self.remaining = seconds

    def update(self, dt):
        self.remaining = max(0, self.remaining - dt)

    def expired(self):
        return self.remaining <= 0
