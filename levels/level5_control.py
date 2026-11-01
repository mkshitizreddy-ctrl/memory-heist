"""
levels/level5_control.py
Owner: Member 4 - Apporov Sahu

Level 5 - Control and Recovery Center

The player guides a drone down a corridor of THREE GATES. Each gate is
opened by answering questions about one topic:

    Gate 1 - PARAMETERS : parameters and arguments   (2 questions)
    Gate 2 - RETURN     : return values              (2 questions)
    Gate 3 - EXCEPTIONS : raise, try/except          (1 question,
                          then the control terminal)

The terminal at Gate 3 runs real try/except code: typing letters causes a
genuine ValueError from int(), typing a number below 5 makes
unlock_vault() raise, and both are caught and explained.

Controls
    1-4        choose an answer
    H / TAB    reveal a hint (costs points; disabled on Hard)
    TAB        hint while using the terminal (letters are typed there)
    ENTER      submit the terminal command
    BACKSPACE  edit the terminal command
"""

import random

import pygame

from entities.gate import Gate
from levels.level5_questions import (
    CODE_LINES,
    GATES,
    QUESTION_POOL,
    TERMINAL_LINES,
)

# ---------------------------------------------------------------------
# Scoring and penalties
# ---------------------------------------------------------------------
POINTS_PER_QUESTION = 40
POINTS_TERMINAL = 50
POINTS_COMPLETION_BONUS = 100

WRONG_SECURITY = 20            # scaled by difficulty in game.security
WRONG_SCORE_PENALTY = 10
INVALID_INPUT_SECURITY = 5     # typed something that is not an integer
DENIED_SECURITY = 15           # typed an integer below 5
DENIED_SCORE_PENALTY = 5

HINT_PENALTY = 10
HINT_PENALTY_HARD = 15

REQUIRED_LEVEL = 5
MAX_COMMAND_LENGTH = 8
FINISH_DELAY = 1.6             # seconds to show the finished corridor

TERMINAL_HINT = (
    "Read the if-statement in unlock_vault: the level must not be below 5."
)

# ---------------------------------------------------------------------
# Layout (screen is 960x640; the HUD bar occupies the top ~45px)
# ---------------------------------------------------------------------
ROOM = pygame.Rect(30, 52, 900, 560)
CORRIDOR = pygame.Rect(60, 118, 840, 96)
CODE_PANEL = pygame.Rect(60, 228, 450, 270)
RIGHT_PANEL = pygame.Rect(525, 228, 375, 270)
MESSAGE_TOP = 506
HELP_Y = 590

GATE_XS = (330, 560, 790)
TOKEN_START_X = 100
TOKEN_VAULT_X = 872
TOKEN_Y = 164

# Colors
C_ROOM = (14, 20, 30)
C_GRID = (22, 31, 44)
C_PANEL = (9, 13, 21)
C_BORDER = (60, 110, 140)
C_TEXT = (225, 232, 240)
C_MUTED = (140, 152, 168)
C_GOOD = (80, 230, 130)
C_BAD = (255, 105, 100)
C_HINT = (255, 214, 90)
C_CYAN = (90, 215, 255)


class AccessDenied(ValueError):
    """Raised by unlock_vault when the level is too low.

    It is a ValueError subclass, so the single `except ValueError` shown
    in the on-screen code catches it, while the level can still tell an
    "access denied" error apart from a bad-input error.
    """


class Level5ControlCenter:
    """Three-gate function and exception-handling puzzle."""

    def __init__(self, game=None, seed=None, finish_delay=FINISH_DELAY):
        self.game = game
        self._rng = random.Random(seed)
        self._finish_delay = finish_delay

        # Public state
        self.complete = False
        self.feedback = ""
        self.feedback_good = False
        self.explanation = ""
        self.hint_text = ""
        self.command = ""
        self.command_result = ""
        self.selected_option = None
        self.terminal_unlocked = False

        # Progress: 5 questions + 1 terminal challenge
        self.total_questions = sum(g["count"] for g in GATES)
        self.total_steps = self.total_questions + 1
        self.current_step = 1
        self._steps_done = 0

        # Gate / question state
        self.gate_index = 0
        self.question_index = 0
        self.phase = "questions"     # "questions" | "terminal" | "done"
        self.gate_questions = self._pick_questions()
        self.question = None
        self.options = []
        self.correct_option = 0
        self.eliminated = set()
        self.hint_used = False

        self._completion_awarded = False
        self._finish_timer = 0.0

        # Animated gates and drone
        self.gates = [
            Gate(x - 9, CORRIDOR.y + 8, width=18, height=CORRIDOR.height - 16)
            for x in GATE_XS
        ]
        self._token_x = float(TOKEN_START_X)
        self._t = 0.0
        self._fonts = None

        self._load_question()

    # -----------------------------------------------------------------
    # Setup helpers
    # -----------------------------------------------------------------
    def _pick_questions(self):
        """Choose this run's questions for each gate from the pools."""
        return [
            self._rng.sample(list(pool), gate["count"])
            for gate, pool in zip(GATES, QUESTION_POOL)
        ]

    def _load_question(self):
        """Load the current question and shuffle its options."""
        self.question = self.gate_questions[self.gate_index][
            self.question_index
        ]
        options = [self.question.answer, *self.question.distractors]
        self._rng.shuffle(options)
        self.options = options
        self.correct_option = options.index(self.question.answer)
        self.eliminated = set()
        self.selected_option = None
        self.hint_used = False
        self.hint_text = ""

    # -----------------------------------------------------------------
    # Difficulty / hint helpers
    # -----------------------------------------------------------------
    def _difficulty_name(self):
        difficulty = getattr(self.game, "difficulty", None)
        if isinstance(difficulty, dict):
            return str(difficulty.get("label", "medium")).lower()
        if isinstance(difficulty, str):
            return difficulty.lower()
        return "medium"

    def hint_penalty(self):
        """Points deducted for using a hint (higher on Hard)."""
        if self._difficulty_name() == "hard":
            return HINT_PENALTY_HARD
        return HINT_PENALTY

    def _hints_enabled(self):
        hints = getattr(self.game, "hints", None)
        if hints is None:
            return True
        return bool(getattr(hints, "enabled", True))

    # -----------------------------------------------------------------
    # Update
    # -----------------------------------------------------------------
    def update(self, dt):
        """Advance gate animations, the drone and the finish timer."""
        self._t += dt

        for gate in self.gates:
            gate.update(dt)

        # Glide the drone toward its target position.
        target = self._token_target()
        self._token_x += (target - self._token_x) * min(1.0, dt * 4.0)

        if self.complete and self._finish_timer > 0:
            self._finish_timer = max(0.0, self._finish_timer - dt)

    def _token_target(self):
        if self.phase == "done":
            return TOKEN_VAULT_X
        return GATE_XS[self.gate_index] - 34

    # -----------------------------------------------------------------
    # Events
    # -----------------------------------------------------------------
    def handle_event(self, event):
        """Handle keyboard input for Level 5."""
        if event.type != pygame.KEYDOWN or self.complete:
            return

        if self.phase == "questions":
            self._handle_question_key(event)
        elif self.phase == "terminal":
            self._handle_terminal_key(event)

    def _handle_question_key(self, event):
        if event.key in (pygame.K_h, pygame.K_TAB):
            self._use_hint(self.question.hint)
            return

        answer_keys = {
            pygame.K_1: 0,
            pygame.K_2: 1,
            pygame.K_3: 2,
            pygame.K_4: 3,
        }
        if event.key in answer_keys:
            self._answer(answer_keys[event.key])

    def _handle_terminal_key(self, event):
        if event.key == pygame.K_TAB:
            self._use_hint(TERMINAL_HINT)
            return

        if event.key == pygame.K_BACKSPACE:
            self.command = self.command[:-1]
            return

        if event.key == pygame.K_RETURN:
            self._submit_terminal()
            return

        char = getattr(event, "unicode", "")
        if (
            char
            and char.isascii()
            and (char.isalnum() or char == "-")
            and len(self.command) < MAX_COMMAND_LENGTH
        ):
            self.command += char

    # -----------------------------------------------------------------
    # Hints
    # -----------------------------------------------------------------
    def _use_hint(self, text):
        if not self._hints_enabled():
            self.feedback = "Hints are disabled on Hard."
            self.feedback_good = False
            return

        if not self.hint_used:
            self.hint_used = True
            self.feedback = (
                f"Hint revealed. This step is worth "
                f"{self.hint_penalty()} fewer points."
            )
            self.feedback_good = True

        self.hint_text = f"HINT: {text}"

    def _award(self, base):
        """Add points, reduced by the hint penalty if a hint was used."""
        earned = base
        if self.hint_used:
            earned = max(0, base - self.hint_penalty())
        if self.game:
            self.game.score.add(earned)
        return earned

    # -----------------------------------------------------------------
    # Questions
    # -----------------------------------------------------------------
    def _answer(self, index):
        if index in self.eliminated:
            return

        self.selected_option = index

        if index != self.correct_option:
            self.eliminated.add(index)
            self.feedback = "INCORRECT - that option is eliminated. Try again."
            self.feedback_good = False
            self.explanation = ""
            if self.game:
                self.game.security.increase(WRONG_SECURITY)
                self.game.score.penalize(WRONG_SCORE_PENALTY)
            return

        earned = self._award(POINTS_PER_QUESTION)
        self.feedback = f"CORRECT! +{earned} points."
        self.feedback_good = True
        self.explanation = self.question.explanation
        self._finish_step()

        gate_questions = self.gate_questions[self.gate_index]
        if self.question_index + 1 < len(gate_questions):
            self.question_index += 1
            self._load_question()
            return

        # Last question of this gate.
        if self.gate_index + 1 < len(GATES):
            self.gates[self.gate_index].unlock()
            self.gate_index += 1
            self.question_index = 0
            self.feedback += f" {GATES[self.gate_index - 1]['label']} OPEN!"
            self._load_question()
        else:
            # Gate 3: questions done, now the terminal challenge.
            self.phase = "terminal"
            self.terminal_unlocked = True
            self.selected_option = None
            self.hint_used = False
            self.hint_text = ""
            self.feedback += " Terminal unlocked."

    def _finish_step(self):
        self._steps_done += 1
        self.current_step = min(self._steps_done + 1, self.total_steps)

    # -----------------------------------------------------------------
    # Terminal (real try/except)
    # -----------------------------------------------------------------
    def _submit_terminal(self):
        """Run the on-screen try/except code with the typed entry."""
        entry = self.command.strip()
        if not entry:
            self.feedback = "Type an access level first."
            self.feedback_good = False
            return

        try:
            result = self._unlock_vault(int(entry))
        except ValueError as err:
            self._handle_terminal_error(err)
        else:
            self._terminal_success(result)
        finally:
            self.command = ""

    def _handle_terminal_error(self, err):
        """Explain which ValueError was caught and apply its penalty."""
        message = str(err)
        if len(message) > 60:
            message = message[:57] + "..."
        self.command_result = f"Caught: {message}"
        self.feedback_good = False
        self.explanation = ""

        if isinstance(err, AccessDenied):
            self.feedback = (
                "Access denied - unlock_vault raised a ValueError and "
                "except caught it."
            )
            if self.game:
                self.game.security.increase(DENIED_SECURITY)
                self.game.score.penalize(DENIED_SCORE_PENALTY)
        else:
            self.feedback = (
                "int() could not convert that text - ValueError caught "
                "safely by except."
            )
            if self.game:
                self.game.security.increase(INVALID_INPUT_SECURITY)

    def _terminal_success(self, result):
        self.command_result = result
        self.feedback = "CONTROL CENTER RESTORED! Master Vault access granted."
        self.feedback_good = True
        self.explanation = (
            "No error was raised, so the except block was skipped."
        )

        if not self._completion_awarded:
            self._award(POINTS_TERMINAL)
            if self.game:
                self.game.score.add(POINTS_COMPLETION_BONUS)
            self._completion_awarded = True

        self._finish_step()
        self.gates[-1].unlock()
        self.phase = "done"
        self.complete = True
        self._finish_timer = self._finish_delay

    def _unlock_vault(self, level):
        """The function shown on screen: raises if the level is too low."""
        if level < REQUIRED_LEVEL:
            raise AccessDenied("Access denied")
        return "MASTER ACCESS"

    # -----------------------------------------------------------------
    # Completion
    # -----------------------------------------------------------------
    def is_complete(self):
        """True once the level is solved and the finish animation ended."""
        return self.complete and self._finish_timer <= 0

    # =================================================================
    # RENDERING
    # =================================================================
    def _get_fonts(self):
        if self._fonts is None:
            if not pygame.font.get_init():
                pygame.font.init()
            mono = self._fit_mono_font()
            self._fonts = {
                "title": pygame.font.Font(None, 34),
                "heading": pygame.font.Font(None, 26),
                "text": pygame.font.Font(None, 24),
                "small": pygame.font.Font(None, 20),
                "big": pygame.font.Font(None, 40),
                "mono": mono,
            }
        return self._fonts

    @staticmethod
    def _fit_mono_font():
        """Largest monospace font (up to 18pt) whose longest code line
        fits inside the code panel."""
        longest = max(CODE_LINES, key=len)
        available = CODE_PANEL.width - 46 - 20
        font = None
        for size in range(18, 11, -1):
            font = pygame.font.SysFont(
                "consolas,couriernew,dejavusansmono,monospace", size
            )
            if font.size(longest)[0] <= available:
                break
        return font

    @staticmethod
    def _wrap(font, text, max_width):
        """Split text into lines no wider than max_width pixels."""
        lines, current = [], ""
        for word in text.split():
            trial = f"{current} {word}".strip()
            if font.size(trial)[0] <= max_width or not current:
                current = trial
            else:
                lines.append(current)
                current = word
        if current:
            lines.append(current)
        return lines

    @staticmethod
    def _text(surface, font, text, color, pos, center=False):
        image = font.render(text, True, color)
        rect = image.get_rect()
        if center:
            rect.center = pos
        else:
            rect.topleft = pos
        surface.blit(image, rect)
        return rect

    def _gate_color(self, index):
        return GATES[index]["color"]

    def render(self, surface):
        """Draw the Level 5 Control and Recovery Center."""
        fonts = self._get_fonts()

        self._draw_room(surface, fonts)
        self._draw_progress(surface, fonts)
        self._draw_corridor(surface, fonts)
        self._draw_code_panel(surface, fonts)

        if self.phase == "questions":
            self._draw_question_panel(surface, fonts)
        elif self.phase == "terminal":
            self._draw_terminal_panel(surface, fonts)
        else:
            self._draw_done_panel(surface, fonts)

        self._draw_messages(surface, fonts)
        self._draw_help(surface, fonts)

    # ---- room, title and progress ----------------------------------
    def _draw_room(self, surface, fonts):
        pygame.draw.rect(surface, C_ROOM, ROOM, border_radius=10)

        for x in range(ROOM.x + 40, ROOM.right, 40):
            pygame.draw.line(surface, C_GRID, (x, ROOM.y + 4), (x, ROOM.bottom - 4))
        for y in range(ROOM.y + 40, ROOM.bottom, 40):
            pygame.draw.line(surface, C_GRID, (ROOM.x + 4, y), (ROOM.right - 4, y))

        pygame.draw.rect(surface, C_BORDER, ROOM, 3, border_radius=10)

        self._text(
            surface, fonts["title"],
            "LEVEL 5 - CONTROL & RECOVERY CENTER", (255, 255, 255),
            (ROOM.x + 24, ROOM.y + 12),
        )
        self._text(
            surface, fonts["text"],
            "Open three gates with functions and exception handling.",
            C_MUTED, (ROOM.x + 24, ROOM.y + 44),
        )

    def _draw_progress(self, surface, fonts):
        """Segmented progress bar, one segment per step."""
        seg_w, seg_h, gap = 30, 10, 5
        total = self.total_steps
        width = total * seg_w + (total - 1) * gap
        x0 = ROOM.right - 24 - width
        y0 = ROOM.y + 22

        for i in range(total):
            rect = pygame.Rect(x0 + i * (seg_w + gap), y0, seg_w, seg_h)
            if i < self._steps_done:
                color = C_GOOD
            elif i == self._steps_done and not self.complete:
                color = C_CYAN
            else:
                color = (45, 55, 70)
            pygame.draw.rect(surface, color, rect, border_radius=3)

        label = f"STEP {min(self.current_step, total)}/{total}"
        image = fonts["small"].render(label, True, C_MUTED)
        surface.blit(image, (x0 + width - image.get_width(), y0 + 18))

    # ---- corridor with three gates ----------------------------------
    def _draw_corridor(self, surface, fonts):
        pygame.draw.rect(surface, (7, 10, 17), CORRIDOR, border_radius=8)
        pygame.draw.rect(surface, C_BORDER, CORRIDOR, 2, border_radius=8)

        # Dashed floor line
        floor_y = TOKEN_Y + 24
        for x in range(CORRIDOR.x + 14, CORRIDOR.right - 14, 18):
            pygame.draw.line(surface, (40, 55, 72), (x, floor_y), (x + 9, floor_y), 2)

        self._text(surface, fonts["small"], "START", C_MUTED,
                   (CORRIDOR.x + 14, CORRIDOR.y + 8))
        self._text(surface, fonts["small"], "VAULT",
                   C_GOOD if self.phase == "done" else C_MUTED,
                   (CORRIDOR.right - 52, CORRIDOR.y + 8))

        for i, gate in enumerate(self.gates):
            color = self._gate_color(i)
            x = GATE_XS[i]

            # Gate frame (top and bottom brackets)
            frame_color = C_GOOD if gate.state == "open" else color
            pygame.draw.rect(
                surface, frame_color,
                (x - 16, CORRIDOR.y + 2, 32, 6), border_radius=2,
            )
            pygame.draw.rect(
                surface, frame_color,
                (x - 16, CORRIDOR.bottom - 8, 32, 6), border_radius=2,
            )

            gate.draw(surface)

            if gate.state == "open":
                name_color = C_GOOD
            elif i == self.gate_index and not self.complete:
                name_color = color
            else:
                name_color = C_MUTED

            label = fonts["small"].render(
                f"{GATES[i]['label']}  {GATES[i]['name']}", True, name_color
            )
            surface.blit(label, (x - 22 - label.get_width(), CORRIDOR.y + 12))

        self._draw_drone(surface)

    def _draw_drone(self, surface):
        """The glowing drone that travels through the gates."""
        x, y = int(self._token_x), TOKEN_Y
        pulse = 3 + int(2 * (1 + pygame.math.Vector2(1, 0).rotate(self._t * 240).x))

        glow = pygame.Surface((70, 70), pygame.SRCALPHA)
        pygame.draw.circle(glow, (*C_CYAN, 50), (35, 35), 16 + pulse)
        surface.blit(glow, (x - 35, y - 35))

        pygame.draw.circle(surface, (20, 40, 55), (x, y), 13)
        pygame.draw.circle(surface, C_CYAN, (x, y), 13, 2)
        pygame.draw.circle(surface, (255, 255, 255), (x, y), 4)

    # ---- code panel --------------------------------------------------
    def _highlighted_lines(self):
        if self.phase == "questions" and self.question:
            return set(self.question.highlight)
        if self.phase == "terminal":
            return set(TERMINAL_LINES)
        return set()

    def _draw_code_panel(self, surface, fonts):
        panel = CODE_PANEL
        pygame.draw.rect(surface, C_PANEL, panel, border_radius=8)
        pygame.draw.rect(surface, C_BORDER, panel, 2, border_radius=8)

        self._text(surface, fonts["heading"], "CONTROL PROGRAM", C_CYAN,
                   (panel.x + 16, panel.y + 12))

        highlighted = self._highlighted_lines()
        line_h = 21
        top = panel.y + 44

        for i, line in enumerate(CODE_LINES):
            y = top + i * line_h
            if i in highlighted:
                bar = pygame.Rect(panel.x + 8, y - 2, panel.width - 16, line_h)
                pygame.draw.rect(surface, (30, 66, 92), bar, border_radius=4)
                pygame.draw.rect(surface, C_CYAN, (bar.x, bar.y, 3, bar.height))

            self._text(surface, fonts["mono"], f"{i + 1:>2}", (90, 105, 125),
                       (panel.x + 16, y))
            self._text(
                surface, fonts["mono"], line,
                (170, 235, 255) if i in highlighted else (130, 190, 215),
                (panel.x + 46, y),
            )

    # ---- right panel: questions -------------------------------------
    def _draw_question_panel(self, surface, fonts):
        panel = RIGHT_PANEL
        color = self._gate_color(self.gate_index)
        pygame.draw.rect(surface, C_PANEL, panel, border_radius=8)
        pygame.draw.rect(surface, color, panel, 2, border_radius=8)

        gate = GATES[self.gate_index]
        self._text(surface, fonts["heading"],
                   f"{gate['label']} - {gate['name']}", color,
                   (panel.x + 16, panel.y + 12))

        count = len(self.gate_questions[self.gate_index])
        q_label = f"Q {self.question_index + 1}/{count}"
        image = fonts["small"].render(q_label, True, C_MUTED)
        surface.blit(image, (panel.right - 16 - image.get_width(), panel.y + 16))

        y = panel.y + 46
        for line in self._wrap(fonts["text"], self.question.prompt,
                               panel.width - 32)[:3]:
            self._text(surface, fonts["text"], line, C_TEXT, (panel.x + 16, y))
            y += 24

        y += 8
        for i, option in enumerate(self.options):
            row = pygame.Rect(panel.x + 14, y, panel.width - 28, 29)

            if i in self.eliminated:
                bg, fg, border = (40, 18, 22), (150, 90, 90), (110, 50, 55)
            elif self.selected_option == i and i == self.correct_option:
                bg, fg, border = (16, 50, 32), C_GOOD, C_GOOD
            else:
                bg, fg, border = (18, 26, 38), C_TEXT, (55, 75, 100)

            pygame.draw.rect(surface, bg, row, border_radius=6)
            pygame.draw.rect(surface, border, row, 1, border_radius=6)
            self._text(surface, fonts["text"], f"[{i + 1}]", color,
                       (row.x + 10, row.y + 6))
            self._text(surface, fonts["text"], option, fg,
                       (row.x + 52, row.y + 6))
            if i in self.eliminated:
                mid = row.y + row.height // 2
                width = fonts["text"].size(option)[0]
                pygame.draw.line(surface, fg, (row.x + 52, mid),
                                 (row.x + 52 + width, mid), 2)
            y += 33

    # ---- right panel: terminal --------------------------------------
    def _draw_terminal_panel(self, surface, fonts):
        panel = RIGHT_PANEL
        color = self._gate_color(2)
        pygame.draw.rect(surface, C_PANEL, panel, border_radius=8)
        pygame.draw.rect(surface, color, panel, 2, border_radius=8)

        self._text(surface, fonts["heading"], "GATE 3 - CONTROL TERMINAL",
                   color, (panel.x + 16, panel.y + 12))

        y = panel.y + 46
        for line in self._wrap(
            fonts["text"],
            "Type an access level for the vault door, then press ENTER.",
            panel.width - 32,
        ):
            self._text(surface, fonts["text"], line, C_TEXT, (panel.x + 16, y))
            y += 24

        box = pygame.Rect(panel.x + 14, panel.y + 112, panel.width - 28, 44)
        pygame.draw.rect(surface, (5, 8, 14), box, border_radius=6)
        pygame.draw.rect(surface, (90, 120, 150), box, 2, border_radius=6)

        cursor = "_" if int(self._t * 2) % 2 == 0 else " "
        self._text(surface, fonts["mono"], f"entry = {self.command}{cursor}",
                   (230, 235, 240), (box.x + 12, box.y + 13))

        self._text(surface, fonts["small"], "OUTPUT", C_MUTED,
                   (panel.x + 16, panel.y + 172))
        y = panel.y + 192
        if self.command_result:
            for line in self._wrap(fonts["mono"], self.command_result,
                                   panel.width - 32)[:3]:
                self._text(surface, fonts["mono"], line, C_CYAN,
                           (panel.x + 16, y))
                y += 21

    # ---- right panel: finished --------------------------------------
    def _draw_done_panel(self, surface, fonts):
        panel = RIGHT_PANEL
        pygame.draw.rect(surface, (10, 26, 20), panel, border_radius=8)
        pygame.draw.rect(surface, C_GOOD, panel, 2, border_radius=8)

        cx = panel.centerx
        self._text(surface, fonts["big"], "VAULT ACCESS", C_GOOD,
                   (cx, panel.y + 70), center=True)
        self._text(surface, fonts["big"], "GRANTED", C_GOOD,
                   (cx, panel.y + 108), center=True)
        self._text(surface, fonts["text"], "All 3 gates are open.", C_TEXT,
                   (cx, panel.y + 160), center=True)
        self._text(surface, fonts["text"], self.command_result, C_CYAN,
                   (cx, panel.y + 190), center=True)

    # ---- feedback and help ------------------------------------------
    def _draw_messages(self, surface, fonts):
        y = MESSAGE_TOP
        max_width = ROOM.width - 60
        x = ROOM.x + 30
        limit = HELP_Y - 18

        entries = (
            (self.feedback, C_GOOD if self.feedback_good else C_BAD),
            (self.hint_text, C_HINT),
            (self.explanation, C_MUTED),
        )
        for text, color in entries:
            if not text:
                continue
            for line in self._wrap(fonts["text"], text, max_width):
                if y > limit:
                    return
                self._text(surface, fonts["text"], line, color, (x, y))
                y += 22

    def _draw_help(self, surface, fonts):
        if self.phase == "questions":
            text = (
                f"1-4: answer   |   H: hint (-{self.hint_penalty()} pts)"
            )
        elif self.phase == "terminal":
            text = (
                "Type your entry   |   ENTER: run   |   "
                f"TAB: hint (-{self.hint_penalty()} pts)"
            )
        else:
            text = "Heading to the Final Vault..."

        self._text(surface, fonts["small"], text, (155, 162, 178),
                   (ROOM.centerx, HELP_Y), center=True)