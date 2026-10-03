"""Shared drawing helpers and the reusable multi-room, multi-gate level engine."""
import pygame

from systems.questions import QuestionBank

BG = (12, 16, 28)
PANEL = (24, 32, 52)
GREEN = (60, 220, 120)
RED = (230, 80, 80)
YELLOW = (240, 200, 70)
WHITE = (235, 240, 250)
GREY = (120, 130, 150)
BLUE = (70, 120, 220)


def draw_text(surface, font, text, pos, color=WHITE):
    """Draw one line of text at pos (top-left)."""
    surface.blit(font.render(str(text), True, color), pos)


def wrap_text(font, text, max_width):
    """Split text into lines that each fit within max_width pixels for the given font."""
    words = text.split(" ")
    lines = []
    current = ""
    for word in words:
        trial = (current + " " + word).strip()
        if font.size(trial)[0] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def draw_button(surface, font, rect, text, hover=False, color=BLUE, disabled=False):
    """Draw a rectangular button with centered text."""
    if disabled:
        fill = (40, 44, 56)
    else:
        fill = tuple(min(255, c + 40) for c in color) if hover else color
    pygame.draw.rect(surface, fill, rect, border_radius=8)
    pygame.draw.rect(surface, WHITE, rect, 2, border_radius=8)
    label = font.render(str(text), True, GREY if disabled else WHITE)
    surface.blit(label, label.get_rect(center=rect.center))


class ClickTracker:
    """Detects a single left-click per press (no repeat while held)."""

    def __init__(self):
        """Start with the mouse button considered released."""
        self._was_down = False

    def clicked(self):
        """Return True only on the frame the left button goes down."""
        down = pygame.mouse.get_pressed()[0]
        result = down and not self._was_down
        self._was_down = down
        return result


class MultiGateLevel:
    """Generic multi-room, multi-gate level: N gates, each unlocked by a random question.

    Subclass this once per level and just set level_key/title (see level1.py, level2.py).
    Difficulty changes the number of hints and whether/how long a per-question timer runs.
    """

    GATES_PER_LEVEL = 3
    DIFFICULTY_SETTINGS = {
        "easy":   {"hints": 3, "time_limit": None},
        "medium": {"hints": 1, "time_limit": 45},
        "hard":   {"hints": 0, "time_limit": 25},
    }
    HINT_PENALTY = 20
    WRONG_PENALTY = 10

    @classmethod
    def _normalize_difficulty(cls, difficulty):
        """Lowercase/trim a difficulty string and fall back to medium if it's not recognized."""
        key = str(difficulty).strip().lower() if difficulty else "medium"
        return key if key in cls.DIFFICULTY_SETTINGS else "medium"

    def __init__(self, level_key, title, player=None, difficulty="medium"):
        """Set up the question bank, first room/gate, scoring, and difficulty-based rules."""
        self.level_key = level_key
        self.title = title
        self.player = player
        self.difficulty = self._normalize_difficulty(difficulty)
        self.bank = QuestionBank(level_key, self.difficulty)
        self.gates_passed = 0
        self.complete = False
        self.score = 0
        self.hints_left = self.DIFFICULTY_SETTINGS[self.difficulty]["hints"]
        self.time_limit = self.DIFFICULTY_SETTINGS[self.difficulty]["time_limit"]
        self.time_left = self.time_limit
        self.show_hint = False
        self.message = "Solve the challenge to open the gate."
        self.message_color = WHITE
        self.question = None
        self.clicks = ClickTracker()
        self.font = pygame.font.SysFont("consolas", 24)
        self.big = pygame.font.SysFont("consolas", 34, bold=True)
        self._next_question()

    def set_difficulty(self, difficulty):
        """Change difficulty mid-level, e.g. from a difficulty-select menu."""
        difficulty = self._normalize_difficulty(difficulty)
        self.difficulty = difficulty
        self.bank.set_difficulty(difficulty)
        self.hints_left = self.DIFFICULTY_SETTINGS[difficulty]["hints"]
        self.time_limit = self.DIFFICULTY_SETTINGS[difficulty]["time_limit"]
        self.time_left = self.time_limit

    def get_score(self):
        """Return the running score for this level (puzzle points minus hint/wrong penalties)."""
        return self.score

    def _next_question(self):
        """Pull the next random, non-repeating question and reset the per-question timer."""
        self.question = self.bank.next_question()
        self.time_left = self.time_limit
        self.show_hint = False

    def _question_lines(self):
        """Return the current question text wrapped to fit the panel width."""
        return wrap_text(self.font, self.question["question"], 840)

    def _options_top(self):
        """Return the y-position options start at, shifted down for extra question lines."""
        extra_lines = max(0, len(self._question_lines()) - 1)
        return 300 + extra_lines * 30

    def _option_rects(self, count):
        """Return one clickable rect per answer option."""
        top = self._options_top()
        return [pygame.Rect(60, top + i * 56, 560, 48) for i in range(count)]

    def _hint_rect(self):
        """Return the hint button rect, aligned with the first option row."""
        return pygame.Rect(650, self._options_top(), 170, 48)

    def update(self, dt):
        """Advance the timer (if any), and handle clicks on options and the hint button."""
        if self.complete:
            return
        if self.time_limit is not None:
            self.time_left -= dt
            if self.time_left <= 0:
                self.score = max(0, self.score - self.WRONG_PENALTY)
                self._wrong("Time's up! Try this gate again.")
                return
        if not self.clicks.clicked():
            return
        pos = pygame.mouse.get_pos()
        if self.hints_left > 0 and self._hint_rect().collidepoint(pos):
            self.show_hint = True
            self.hints_left -= 1
            self.score = max(0, self.score - self.HINT_PENALTY)
            return
        for i, rect in enumerate(self._option_rects(len(self.question["options"]))):
            if rect.collidepoint(pos):
                self._answer(self.question["options"][i])
                return

    def _answer(self, choice):
        """Check the chosen option against the question's answer."""
        if choice == self.question["answer"]:
            self.score += self.question.get("points", 0)
            explanation = self.question.get("explanation", "")
            self.gates_passed += 1
            if self.gates_passed >= self.GATES_PER_LEVEL:
                self.complete = True
                self.message = f"Correct! {explanation} {self.title}: ALL GATES OPEN! Score: {self.score}"
            else:
                opened = self.gates_passed
                self._next_question()
                self.message = f"Correct! {explanation} Gate {opened} open - entering room {opened + 1}."
            self.message_color = GREEN
        else:
            self.score = max(0, self.score - self.WRONG_PENALTY)
            self._wrong("Wrong answer - try again." if self.hints_left == 0
                        else "Wrong answer - try again, or use a hint.")

    def _wrong(self, text):
        """Show a failure message and reset the timer so the player can retry this gate."""
        self.message = text
        self.message_color = RED
        self.time_left = self.time_limit

    def render(self, surface):
        """Draw the room header, question, options, hint and gate progress."""
        surface.fill(BG)
        draw_text(surface, self.big, self.title.upper(), (60, 25), YELLOW)
        draw_text(surface, self.font,
                  f"Room {min(self.gates_passed + 1, self.GATES_PER_LEVEL)} of {self.GATES_PER_LEVEL}  |  "
                  f"Difficulty: {self.difficulty.upper()}  |  Score: {self.score}", (60, 65), GREY)

        for i in range(self.GATES_PER_LEVEL):
            rect = pygame.Rect(60 + i * 65, 95, 50, 50)
            opened = i < self.gates_passed
            pygame.draw.rect(surface, GREEN if opened else RED, rect, border_radius=8)
            draw_text(surface, self.font, "OK" if opened else "X", (rect.x + 12, rect.y + 13))

        if self.complete:
            draw_text(surface, self.big, "LEVEL COMPLETE", (60, 220), GREEN)
            for i, line in enumerate(wrap_text(self.font, self.message, 840)):
                draw_text(surface, self.font, line, (60, 560 + i * 28), self.message_color)
            return

        for i, line in enumerate(self._question_lines()):
            draw_text(surface, self.font, line, (60, 280 + i * 30), WHITE)
        if self.time_limit is not None:
            draw_text(surface, self.font, f"Time: {max(0, int(self.time_left))}s", (650, 280),
                      RED if self.time_left < 10 else WHITE)

        mouse = pygame.mouse.get_pos()
        options_bottom = self._options_top() + len(self.question["options"]) * 56
        for rect, option in zip(self._option_rects(len(self.question["options"])), self.question["options"]):
            draw_button(surface, self.font, rect, option, rect.collidepoint(mouse))

        if self.hints_left > 0:
            draw_button(surface, self.font, self._hint_rect(), f"HINT ({self.hints_left})",
                        self._hint_rect().collidepoint(mouse))
        if self.show_hint:
            draw_text(surface, self.font, "Hint: " + self.question.get("hint", ""),
                      (650, self._options_top() + 60), YELLOW)

        msg_top = max(560, options_bottom + 15)
        for i, line in enumerate(wrap_text(self.font, self.message, 840)):
            draw_text(surface, self.font, line, (60, msg_top + i * 26), self.message_color)

    def is_complete(self) -> bool:
        """Return True once every gate in this level is open."""
        return self.complete
