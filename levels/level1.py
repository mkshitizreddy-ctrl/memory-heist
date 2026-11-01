"""
levels/level1.py
Owner: Member 2 - Paranthama Selvan

Level 1 - Security Gate

Topics: variables, data types, strings, integers, booleans.

Progression: 3 gates. Each gate draws one random question from the
level's question pool, filtered to that gate's room and the globally
selected Easy/Medium/Hard difficulty (same pattern as Level 3).

The wrong-answer path in _check_answer() is covered by
tests/test_level1_hints.py and must keep its exact message text and
game.security / game.score amounts.
"""

import json
import random
from pathlib import Path

import pygame

from levels.common import (BG, PANEL, GREEN, RED, YELLOW, WHITE, GREY,
                           ClickTracker, draw_button, draw_text)

GATES_PER_LEVEL = 3
POINTS_FALLBACK = 50

# Used only if data/puzzles.json is missing or unreadable.
FALLBACK_QUESTIONS = {
    1: [{"prompt": "What is the data type of agent_id = \"A-4471\"?",
         "options": ["int", "str", "bool"], "answer": "str",
         "hint": "It is text inside quotes.", "explanation": "Quoted text is a str.",
         "points": POINTS_FALLBACK, "difficulty": "medium", "room": 1}],
    2: [{"prompt": "clearance = 3. What is the data type of clearance?",
         "options": ["float", "str", "int"], "answer": "int",
         "hint": "It is a whole number with no quotes.", "explanation": "Whole numbers are int.",
         "points": POINTS_FALLBACK, "difficulty": "medium", "room": 2}],
    3: [{"prompt": "is_active = True. What is the data type of is_active?",
         "options": ["bool", "str", "int"], "answer": "bool",
         "hint": "Booleans are only True or False.", "explanation": "True/False values are bool.",
         "points": POINTS_FALLBACK, "difficulty": "medium", "room": 3}],
}


class Level1:
    """Security Gate: answer 3 randomized questions (one per gate) to unlock the vault."""

    def __init__(self, player=None, game=None):
        """Load the question pool, pick the first gate's question, and set up state."""
        self.player = player
        self.game = game

        self.complete = False
        self.gates_passed = 0
        self.message = "Read the question, then answer to open each gate."
        self.message_color = WHITE

        self.room_question_pools = self._load_questions()
        self.current_difficulty = self._get_selected_difficulty()

        # Difficulty-scaled per-question timer, same pattern as Level 3.
        self.base_time_limit = 25
        multiplier = self._get_timer_multiplier()
        self.time_limit = max(1, round(self.base_time_limit * multiplier))
        self.time_left = self.time_limit

        self.current_question = None
        self._load_question_for_gate(self.gates_passed + 1)

        self.clicks = ClickTracker()
        self.font = pygame.font.SysFont("consolas", 24)
        self.big = pygame.font.SysFont("consolas", 34, bold=True)

    # =========================================================
    # QUESTION LOADING (same pattern as levels/level3_loops.py)
    # =========================================================

    def _load_questions(self):
        """Load this level's questions from data/puzzles.json, grouped by room."""
        pools = {1: [], 2: [], 3: []}
        try:
            base_path = Path(__file__).resolve().parent.parent
            puzzle_path = base_path / "data" / "puzzles.json"
            with open(puzzle_path, "r", encoding="utf-8") as f:
                puzzles = json.load(f)
            for key, puzzle in puzzles.items():
                if not key.startswith("level1_gate_") or key == "level1_gate_code":
                    continue
                room = puzzle.get("room")
                if room in (1, 2, 3):
                    pools[room].append(puzzle)
        except (OSError, ValueError):
            pass

        if not any(pools.values()):
            pools = {k: list(v) for k, v in FALLBACK_QUESTIONS.items()}
        return pools

    def _get_selected_difficulty(self):
        """Safely read the game's global difficulty, same logic as Level 3."""
        difficulty = getattr(self.game, "difficulty", None)
        if isinstance(difficulty, dict):
            value = difficulty.get("name", difficulty.get("level"))
            if value is None:
                try:
                    from core.difficulty import DIFFICULTIES
                    value = next((k for k, preset in DIFFICULTIES.items()
                                  if preset == difficulty), None)
                except ImportError:
                    value = None
        else:
            value = difficulty

        if not isinstance(value, str):
            return "medium"
        value = value.lower().strip()
        return value if value in {"easy", "medium", "hard"} else "medium"

    def _get_timer_multiplier(self):
        """Read the global timer multiplier for the current difficulty, if available."""
        try:
            from core.difficulty import DIFFICULTIES
            return DIFFICULTIES.get(self.current_difficulty, {}).get("timer_multiplier", 1.0)
        except ImportError:
            return 1.0

    def _load_question_for_gate(self, gate_number):
        """Pick a random question for this gate, matching the global difficulty."""
        pool = self.room_question_pools.get(gate_number, [])
        filtered = [q for q in pool if q.get("difficulty", "medium") == self.current_difficulty]
        chosen_pool = filtered if filtered else pool
        if chosen_pool:
            self.current_question = random.choice(chosen_pool)
        else:
            self.current_question = FALLBACK_QUESTIONS[gate_number][0]

    # =========================================================
    # INPUT
    # =========================================================

    def _option_rects(self, count):
        """Return one clickable rect per answer option."""
        return [pygame.Rect(60, 400 + i * 62, 500, 50) for i in range(count)]

    def handle_event(self, event):
        """No keyboard interaction needed - this level is mouse-driven."""
        pass

    def update(self, dt):
        """Count down the per-question timer and handle mouse clicks on options."""
        if self.complete:
            return

        self.time_left -= dt
        if self.time_left <= 0:
            self.time_left = self.time_limit
            self.message = "TIME'S UP! Security increased. Try this gate again."
            self.message_color = RED
            if self.game:
                self.game.security.increase(25)
                self.game.score.penalize(15)
            return

        if not self.clicks.clicked():
            return
        pos = pygame.mouse.get_pos()
        question = self.current_question
        for i, rect in enumerate(self._option_rects(len(question["options"]))):
            if rect.collidepoint(pos):
                self._check_answer(question, question["options"][i])
                break

    # =========================================================
    # ANSWER CHECKING
    # Wrong-answer branch is covered by tests/test_level1_hints.py -
    # keep its message text and game.security/game.score amounts exact.
    # =========================================================

    def _check_answer(self, question, choice):
        """Open a gate on a correct answer, otherwise raise security and show hint."""
        if choice == question["answer"]:
            points = question.get("points", POINTS_FALLBACK)
            self.gates_passed += 1
            if self.game:
                self.game.score.add(points)          # points for correct answer
            if self.gates_passed >= GATES_PER_LEVEL:
                self.complete = True
                self.message = "ACCESS GRANTED - gate unlocked!"
                if self.game:
                    self.game.score.add(100)     # bonus for finishing the level
            else:
                self.message = f"Correct! Gate {self.gates_passed} open."
                self.time_left = self.time_limit
                self._load_question_for_gate(self.gates_passed + 1)
            self.message_color = GREEN
        else:
            if self.game and not self.game.hints.enabled:
                self.message = "Wrong. Hints are off on this difficulty."
            else:
                self.message = "Wrong. Hint: " + question.get("hint", "Try again.")
            self.message_color = RED
            if self.game:
                self.game.security.increase(20)  # raise security on wrong answer
                self.game.score.penalize(10)     # small score penalty

    # =========================================================
    # RENDER
    # =========================================================

    def render(self, surface):
        """Draw the question, options, gate progress, difficulty and timer."""
        surface.fill(BG)
        draw_text(surface, self.big, "LEVEL 1 - SECURITY GATE", (60, 30), YELLOW)
        draw_text(surface, self.font,
                  f"Gate {min(self.gates_passed + 1, GATES_PER_LEVEL)} of {GATES_PER_LEVEL}  |  "
                  f"Difficulty: {self.current_difficulty.upper()}  |  "
                  f"Time: {max(0, int(self.time_left))}s",
                  (60, 70), GREY)

        for i in range(GATES_PER_LEVEL):
            rect = pygame.Rect(620 + i * 65, 95, 50, 50)
            open_ = i < self.gates_passed
            pygame.draw.rect(surface, GREEN if open_ else RED, rect, border_radius=8)
            draw_text(surface, self.font, "OK" if open_ else "X", (rect.x + 12, rect.y + 13))
        draw_text(surface, self.font, "GATES", (620, 65), GREY)

        if not self.complete:
            q = self.current_question
            panel = pygame.Rect(60, 140, 840, 90)
            pygame.draw.rect(surface, PANEL, panel, border_radius=10)
            draw_text(surface, self.font, q["prompt"], (80, 170), WHITE)

            mouse = pygame.mouse.get_pos()
            for rect, option in zip(self._option_rects(len(q["options"])), q["options"]):
                draw_button(surface, self.font, rect, option, rect.collidepoint(mouse))
        else:
            draw_text(surface, self.big, "GATE OPEN", (60, 250), GREEN)

        draw_text(surface, self.font, self.message, (60, 590), self.message_color)

    def is_complete(self) -> bool:
        """Return True when every gate is open."""
        return self.complete
