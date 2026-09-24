"""Level 1 - Security Gate: variables, data types, strings, integers, booleans."""
import pygame

from levels.common import (BG, PANEL, GREEN, RED, YELLOW, WHITE, GREY,
                           ClickTracker, draw_button, draw_text, load_level_data)

DEFAULT_DATA = {
    "agent": {"agent_id": "A-4471", "clearance": 3, "is_active": True, "codename": "Ghost"},
    "questions": [
        {"prompt": "What is the data type of agent_id?",
         "options": ["int", "str", "bool"], "answer": "str",
         "hint": "It is text inside quotes."},
        {"prompt": "What is the data type of clearance?",
         "options": ["float", "str", "int"], "answer": "int",
         "hint": "It is a whole number with no quotes."},
        {"prompt": "Which variable holds a boolean?",
         "options": ["codename", "is_active", "clearance"], "answer": "is_active",
         "hint": "Booleans are only True or False."},
        {"prompt": "What does type(codename) return?",
         "options": ["<class 'str'>", "<class 'int'>", "<class 'bool'>"],
         "answer": "<class 'str'>", "hint": "codename is written in quotes."},
    ],
}


class Level1:
    """Security Gate: answer questions about an agent record to open the locks."""

    def __init__(self, player=None, game=None):
        """Load puzzle data and set up level state."""
        self.player = player
        self.game = game
        data = load_level_data("level1", DEFAULT_DATA)
        self.agent = data.get("agent", DEFAULT_DATA["agent"])
        self.questions = data.get("questions", DEFAULT_DATA["questions"])
        self.index = 0
        self.complete = False
        self.message = "Read the agent record, then answer to open each lock."
        self.message_color = WHITE
        self.clicks = ClickTracker()
        self.font = pygame.font.SysFont("consolas", 24)
        self.big = pygame.font.SysFont("consolas", 36, bold=True)

    def _option_rects(self, count):
        """Return one clickable rect per answer option."""
        return [pygame.Rect(60, 400 + i * 62, 500, 50) for i in range(count)]

    def handle_event(self, event):
        """No keyboard interaction needed — this level is mouse-driven."""
        pass

    def update(self, dt):
        """Handle mouse clicks on answer options."""
        clicked = self.clicks.clicked()
        if self.complete or not clicked:
            return
        pos = pygame.mouse.get_pos()
        question = self.questions[self.index]
        for i, rect in enumerate(self._option_rects(len(question["options"]))):
            if rect.collidepoint(pos):
                self._check_answer(question, question["options"][i])
                break

    def _check_answer(self, question, choice):
        """Open a lock on a correct answer, otherwise raise security and show hint."""
        if choice == question["answer"]:
            self.index += 1
            if self.game:
                self.game.score.add(50)          # points for correct answer
            if self.index >= len(self.questions):
                self.complete = True
                self.message = "ACCESS GRANTED - gate unlocked!"
                if self.game:
                    self.game.score.add(100)     # bonus for finishing the level
            else:
                self.message = "Correct! Lock opened."
            self.message_color = GREEN
        else:
            self.message = "Wrong. Hint: " + question.get("hint", "Try again.")
            self.message_color = RED
            if self.game:
                self.game.security.increase(20)  # raise security on wrong answer
                self.game.score.penalize(10)     # small score penalty

    def render(self, surface):
        """Draw the agent record, question, options and lock indicators."""
        surface.fill(BG)
        draw_text(surface, self.big, "LEVEL 1 - SECURITY GATE", (60, 60), YELLOW)

        panel = pygame.Rect(60, 90, 840, 170)
        pygame.draw.rect(surface, PANEL, panel, border_radius=10)
        draw_text(surface, self.font, "# agent record", (80, 100), GREY)
        for i, (name, value) in enumerate(self.agent.items()):
            draw_text(surface, self.font, f"{name} = {value!r}", (80, 130 + i * 30), GREEN)

        # Locks
        for i in range(len(self.questions)):
            rect = pygame.Rect(620 + i * 65, 400, 50, 50)
            open_ = i < self.index
            pygame.draw.rect(surface, GREEN if open_ else RED, rect, border_radius=8)
            draw_text(surface, self.font, "OK" if open_ else "X", (rect.x + 12, rect.y + 13))
        draw_text(surface, self.font, "LOCKS", (620, 365), GREY)

        if not self.complete:
            q = self.questions[self.index]
            draw_text(surface, self.font, f"Q{self.index + 1}/{len(self.questions)}: {q['prompt']}",
                      (60, 300), WHITE)
            mouse = pygame.mouse.get_pos()
            for rect, option in zip(self._option_rects(len(q["options"])), q["options"]):
                draw_button(surface, self.font, rect, option, rect.collidepoint(mouse))
        else:
            draw_text(surface, self.big, "GATE OPEN", (60, 320), GREEN)

        draw_text(surface, self.font, self.message, (60, 590), self.message_color)

    def is_complete(self) -> bool:
        """Return True when every lock is open."""
        return self.complete
