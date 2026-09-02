"""
systems/security.py
Owner: Member 5

Security meter that rises on wrong actions. Triggers lockdown
(lose condition) if it hits max.
"""


class SecurityMeter:
    def __init__(self, max_level=100):
        self.level = 0
        self.max_level = max_level

    def increase(self, amount):
        self.level = min(self.max_level, self.level + amount)

    def is_lockdown(self):
        return self.level >= self.max_level
