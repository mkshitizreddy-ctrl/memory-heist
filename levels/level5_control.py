"""
levels/level5_control.py
Owner: Member 4 - Apporov Sahu

Level 5 - Control and Recovery Center

Topics:
- functions
- parameters
- arguments
- return values
- exception handling
- try/except
"""

import pygame


class Level5ControlCenter:
    """Controls the Level 5 function and exception-handling puzzle."""

    def __init__(self, game=None):
        self.game = game

        self.complete = False
        self.selected_option = None
        self.feedback = ""
        self.command = ""
        self.command_result = ""

        # Four concepts tested by this level.
        self.options = [
            "parameter",
            "argument",
            "return",
            "try/except",
        ]

        self.correct_options = {
            1: "parameter",
            2: "argument",
            3: "return",
            4: "try/except",
        }

        self.current_step = 1
        self.total_steps = 4

        self.room_x = 40
        self.room_y = 30
        self.room_width = 880
        self.room_height = 560

        # Terminal becomes available after all concepts are solved.
        self.terminal_unlocked = False

        # Number of successful concept answers.
        self.correct_answers = 0

        # Prevent repeatedly completing the level.
        self._completion_awarded = False

    
    # UPDATE
    def update(self, dt):
        """Update the Level 5 state."""
        if self.complete:
            return

    # RENDER
    def render(self, surface):
        """Draw the Level 5 Control and Recovery Center."""

        title_font = pygame.font.Font(None, 34)
        heading_font = pygame.font.Font(None, 27)
        text_font = pygame.font.Font(None, 23)
        code_font = pygame.font.Font(None, 22)
        option_font = pygame.font.Font(None, 22)
        feedback_font = pygame.font.Font(None, 22)
        input_font = pygame.font.Font(None, 25)


        # Room
        pygame.draw.rect(
            surface,
            (20, 28, 38),
            (
                self.room_x,
                self.room_y,
                self.room_width,
                self.room_height,
            ),
        )

        pygame.draw.rect(
            surface,
            (70, 150, 180),
            (
                self.room_x,
                self.room_y,
                self.room_width,
                self.room_height,
            ),
            3,
        )
        # Title
        title = title_font.render(
            "LEVEL 5 - CONTROL & RECOVERY CENTER",
            True,
            (255, 255, 255),
        )

        surface.blit(
            title,
            (self.room_x + 25, self.room_y + 15),
        )
        # Objective
        objective = text_font.render(
            "Repair the control system using Python functions.",
            True,
            (190, 205, 215),
        )

        surface.blit(
            objective,
            (self.room_x + 25, self.room_y + 58),
        )
        # Function panel
        panel_x = 70
        panel_y = 115
        panel_width = 500
        panel_height = 185

        pygame.draw.rect(
            surface,
            (8, 12, 20),
            (panel_x, panel_y, panel_width, panel_height),
        )

        pygame.draw.rect(
            surface,
            (65, 100, 135),
            (panel_x, panel_y, panel_width, panel_height),
            2,
        )

        heading = heading_font.render(
            "DAMAGED CONTROL FUNCTION",
            True,
            (80, 210, 255),
        )

        surface.blit(
            heading,
            (panel_x + 20, panel_y + 15),
        )

        code_lines = [
            "def unlock_vault(level):",
            "    if level < 5:",
            "        raise ValueError('Access denied')",
            "    return 'MASTER ACCESS'",
        ]

        code_y = panel_y + 52

        for line in code_lines:
            code_text = code_font.render(
                line,
                True,
                (110, 230, 255),
            )

            surface.blit(
                code_text,
                (panel_x + 20, code_y),
            )

            code_y += 25
        # Current task
        task_x = 600
        task_y = 115
        task_width = 270
        task_height = 185

        pygame.draw.rect(
            surface,
            (28, 34, 48),
            (task_x, task_y, task_width, task_height),
        )

        pygame.draw.rect(
            surface,
            (100, 110, 150),
            (task_x, task_y, task_width, task_height),
            2,
        )

        step_text = heading_font.render(
            f"STEP {self.current_step}/{self.total_steps}",
            True,
            (255, 220, 80),
        )

        surface.blit(
            step_text,
            (task_x + 20, task_y + 18),
        )

        task_messages = {
            1: "What receives a value?",
            2: "What is passed to a function?",
            3: "What sends a result back?",
            4: "What handles errors safely?",
        }

        if self.terminal_unlocked:
            task_message = "Concepts repaired. Test the terminal."
        else:
            task_message = task_messages.get(
                self.current_step,
                "Control system ready.",
            )

        message = text_font.render(
            task_message,
            True,
            (235, 235, 240),
        )

        surface.blit(
            message,
            (task_x + 20, task_y + 60),
        )

        # Answer options
        options_heading = heading_font.render(
            "SELECT ANSWER",
            True,
            (240, 240, 240),
        )

        surface.blit(
            options_heading,
            (70, 325),
        )

        option_y = 365

        for index, option in enumerate(self.options):
            color = (235, 235, 240)

            if self.selected_option == index + 1:
                if (
                    option
                    == self.correct_options.get(self.current_step)
                ):
                    color = (70, 230, 120)
                else:
                    color = (255, 100, 100)

            option_text = option_font.render(
                f"[{index + 1}] {option}",
                True,
                color,
            )

            surface.blit(
                option_text,
                (80, option_y),
            )

            option_y += 30

        # Terminal
        input_heading = heading_font.render(
            "CONTROL TERMINAL",
            True,
            (80, 210, 255),
        )

        surface.blit(
            input_heading,
            (500, 325),
        )

        terminal_color = (
            (80, 100, 125)
            if self.terminal_unlocked
            else (55, 60, 70)
        )

        pygame.draw.rect(
            surface,
            (5, 8, 14),
            (500, 365, 360, 42),
        )

        pygame.draw.rect(
            surface,
            terminal_color,
            (500, 365, 360, 42),
            2,
        )

        if self.terminal_unlocked:
            placeholder = "Enter access level..."
        else:
            placeholder = "LOCKED - repair concepts first"

        input_text = input_font.render(
            self.command if self.command else placeholder,
            True,
            (230, 230, 235),
        )

        surface.blit(
            input_text,
            (512, 374),
        )

        if self.terminal_unlocked:
            instruction_text = (
                "ENTER: submit | Correct access level: 5"
            )
        else:
            instruction_text = (
                "Solve all four concepts to unlock terminal."
            )

        instruction = text_font.render(
            instruction_text,
            True,
            (170, 180, 195),
        )

        surface.blit(
            instruction,
            (500, 420),
        )
        # Feedback
        if self.feedback:
            feedback_color = (
                (70, 230, 120)
                if self.complete
                else (255, 110, 100)
            )

            if self.feedback == "CORRECT!":
                feedback_color = (70, 230, 120)

            feedback = feedback_font.render(
                self.feedback,
                True,
                feedback_color,
            )

            feedback_rect = feedback.get_rect(
                center=(
                    self.room_x + self.room_width // 2,
                    485,
                )
            )

            surface.blit(
                feedback,
                feedback_rect,
            )
        # Terminal result
        if self.command_result:
            result = feedback_font.render(
                self.command_result,
                True,
                (90, 220, 255),
            )

            result_rect = result.get_rect(
                center=(
                    self.room_x + self.room_width // 2,
                    515,
                )
            )

            surface.blit(
                result,
                result_rect,
            )

        # Bottom instruction
        instruction_bottom = text_font.render(
            "1-4: choose concept | Type a number after terminal unlock",
            True,
            (155, 160, 175),
        )

        instruction_rect = instruction_bottom.get_rect(
            center=(
                self.room_x + self.room_width // 2,
                555,
            )
        )

        surface.blit(
            instruction_bottom,
            instruction_rect,
        )

    # EVENT HANDLING
    def handle_event(self, event):
        """Handle keyboard input for Level 5."""

        if event.type != pygame.KEYDOWN:
            return

        if self.complete:
            return

        # Answer selection
        option_keys = {
            pygame.K_1: 1,
            pygame.K_2: 2,
            pygame.K_3: 3,
            pygame.K_4: 4,
        }

        if event.key in option_keys:

            # Do not allow concept selection after concepts
            # have already been completed.
            if self.terminal_unlocked:
                self.feedback = (
                    "Concepts already repaired. "
                    "Use the terminal."
                )
                return

            selected = option_keys[event.key]
            self.selected_option = selected

            selected_text = self.options[selected - 1]
            correct_text = self.correct_options.get(
                self.current_step
            )

            if selected_text == correct_text:

                self.correct_answers += 1
                self.feedback = "CORRECT!"

                if self.game:
                    self.game.score.add(40)

                if self.current_step < self.total_steps:

                    self.current_step += 1
                    self.selected_option = None

                    self.feedback = (
                        f"Correct! "
                        f"Proceed to step {self.current_step}."
                    )

                else:

                    self.terminal_unlocked = True
                    self.selected_option = None

                    self.feedback = (
                        "ALL FUNCTION CONCEPTS RESTORED! "
                        "Terminal unlocked."
                    )

            else:

                self.feedback = (
                    "INCORRECT! Review the code and try again."
                )

                if self.game:
                    self.game.security.increase(20)
                    self.game.score.penalize(10)

            return
        # Terminal is locked until concepts are solved.
        if not self.terminal_unlocked:
            return

        # Backspace
        if event.key == pygame.K_BACKSPACE:
            self.command = self.command[:-1]
            return

        # Enter
        if event.key == pygame.K_RETURN:
            self._submit_terminal()
            return

        # Numeric input
        if event.unicode.isdigit():
            if len(self.command) < 3:
                self.command += event.unicode

    # TERMINAL
    def _submit_terminal(self):
        """Validate terminal input using exception handling."""

        if not self.terminal_unlocked:
            self.feedback = (
                "Terminal locked. Repair the function concepts first."
            )
            return

        if not self.command:
            self.feedback = "Enter an access level first."
            return

        try:
            level = int(self.command)

            result = self._unlock_vault(level)
            self.command_result = result

            if level >= 5:

                self.complete = True

                self.feedback = (
                    "CONTROL CENTER RESTORED! "
                    "Master Vault access granted."
                )

                if self.game and not self._completion_awarded:
                    self.game.score.add(50)
                    self.game.score.add(100)
                    self._completion_awarded = True

            else:

                self.feedback = (
                    "Access denied. "
                    "Security clearance must be 5 or higher."
                )

                if self.game:
                    self.game.security.increase(15)
                    self.game.score.penalize(5)

        except ValueError:

            self.command_result = (
                "ValueError caught: invalid integer input."
            )

            self.feedback = (
                "Exception handled safely with try/except."
            )

            if self.game:
                self.game.security.increase(10)

        finally:
            self.command = ""

    # FUNCTION DEMONSTRATION
    def _unlock_vault(self, level):
        """
        Demonstrate a function parameter, conditional,
        exception, and return value.
        """

        if level < 5:
            return "RETURN VALUE: ACCESS DENIED"

        return "RETURN VALUE: MASTER ACCESS"

    # COMPLETION
    def is_complete(self):
        """Return True when Level 5 has been completed."""
        return self.complete
