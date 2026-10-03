"""Level 1 - Security Gate (2.0): 3 gated rooms, randomized variables/data-type questions."""
from levels.common import MultiGateLevel


class Level1(MultiGateLevel):
    """Security Gate: variables and data types, across 3 gated rooms."""

    def __init__(self, player=None, difficulty="medium"):
        """Set up as a 3-gate Level 1 using the level1 question pool."""
        super().__init__("level1", "Level 1 - Security Gate", player=player, difficulty=difficulty)
