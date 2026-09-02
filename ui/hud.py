"""
ui/hud.py
Owner: Member 5

Heads-up display: score, lives, timer, security meter.
Reads from systems/scoring.py, systems/security.py, systems/timer.py
- does not own game state itself.
"""


class HUD:
    def render(self, surface, score, lives, security_level, time_left=None):
        pass
