"""
levels/level5_control.py
Owner: Member 4

Level 5 - Control and Recovery Center
Topics: functions, parameters, arguments, return values, exception
handling (try/except)
"""

import pygame


class Level5ControlCenter:
    """Controls the Level 5 function and exception-handling puzzle."""

    def __init__(self, game=None):
        """Initialize the Level 5 puzzle state."""
        self.game = game

        self.complete = False
        self.selected_option = None
        self.feedback = ""

        self.command = ""
        self.command_result = ""

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

        self.input_active = False

    def update(self, dt):
        """Update the Level 5 puzzle state."""
        if self.complete:
            return

    def render(self, surface):
        """Draw the Level 5 Control and Recovery Center."""

        title_font = pygame.font.Font(None, 34)
        heading_font = pygame.font.Font(None, 27)
        text_font = pygame.font.Font(None, 23)
        code_font = pygame.font.Font(None, 23)
        option_font = pygame.font.Font(None, 22)
        feedback_font = pygame.font.Font(None, 22)
        input_font = pygame.font.Font(None, 25)

        # -----------------------------------------------------
        # Room
        # -----------------------------------------------------
        pygame.draw.rect(
            surface,
            (20, 28, 38),
            (self.room_x, self.room_y, self.room_width, self.room_height),
        )
        pygame.draw.rect(
            surface,
            (70, 150, 180),
            (self.room_x, self.room_y, self.room_width, self.room_height),
            3,
        )

        # -----------------------------------------------------
        # Title
        # -----------------------------------------------------
        title = title_font.render(
            "LEVEL 5 - CONTROL & RECOVERY CENTER",
            True,
            (255, 255, 255),
        )
        surface.blit(title, (self.room_x + 25, self.room_y + 50))

        # -----------------------------------------------------
        # Objective
        # -----------------------------------------------------
        objective = text_font.render(
            "Repair the control system using Python functions.",
            True,
            (190, 205, 215),
        )
        surface.blit(objective, (self.room_x + 25, self.room_y + 58))

        # -----------------------------------------------------
        # Function panel
        # -----------------------------------------------------
        panel_x = 70
        panel_y = 115
        panel_width = 500
        panel_height = 185

        pygame.draw.rect(surface, (8, 12, 20), (panel_x, panel_y, panel_width, panel_height))
        pygame.draw.rect(surface, (65, 100, 135), (panel_x, panel_y, panel_width, panel_height), 2)

        heading = heading_font.render("DAMAGED CONTROL FUNCTION", True, (80, 210, 255))
        surface.blit(heading, (panel_x + 20, panel_y + 15))

        code_lines = [
            "def unlock_vault(level):",
            "    if level < 5:",
            "        raise ValueError('Access denied')",
            "    return 'MASTER ACCESS'",
        ]

        code_y = panel_y + 52
        for line in code_lines:
            code_text = code_font.render(line, True, (110, 230, 255))
            surface.blit(code_text, (panel_x + 20, code_y))
            code_y += 25

        # -----------------------------------------------------
        # Current task
        # -----------------------------------------------------
        task_x = 600
        task_y = 115
        task_width = 270
        task_height = 185

        pygame.draw.rect(surface, (28, 34, 48), (task_x, task_y, task_width, task_height))
        pygame.draw.rect(surface, (100, 110, 150), (task_x, task_y, task_width, task_height), 2)

        step_text = heading_font.render(
            f"STEP {self.current_step}/{self.total_steps}",
            True,
            (255, 220, 80),
        )
        surface.blit(step_text, (task_x + 20, task_y + 18))

        task_messages = {
            1: "What receives a value?",
            2: "What is passed to a function?",
            3: "What sends a result back?",
            4: "What handles errors safely?",
        }

        task_message = task_messages.get(self.current_step, "Control system ready.")
        message = text_font.render(task_message, True, (235, 235, 240))
        surface.blit(message, (task_x + 20, task_y + 60))

        # -----------------------------------------------------
        # Answer options
        # -----------------------------------------------------
        options_heading = heading_font.render("SELECT ANSWER", True, (240, 240, 240))
        surface.blit(options_heading, (70, 325))

        option_y = 365
        for index, option in enumerate(self.options):
            color = (235, 235, 240)

            if self.selected_option == index + 1:
                if option == self.correct_options.get(self.current_step):
                    color = (70, 230, 120)
                else:
                    color = (255, 100, 100)

            option_text = option_font.render(f"[{index + 1}] {option}", True, color)
            surface.blit(option_text, (80, option_y))
            option_y += 30

        # -----------------------------------------------------
        # Command input
        # -----------------------------------------------------
        input_heading = heading_font.render("CONTROL TERMINAL", True, (80, 210, 255))
        surface.blit(input_heading, (500, 325))

        pygame.draw.rect(surface, (5, 8, 14), (500, 365, 360, 42))
        pygame.draw.rect(surface, (80, 100, 125), (500, 365, 360, 42), 2)

        input_text = input_font.render(
            self.command if self.command else "Enter access level...",
            True,
            (230, 230, 235),
        )
        surface.blit(input_text, (512, 374))

        instruction = text_font.render(
            "Press ENTER to submit. Use 5 as the access level.",
            True,
            (170, 180, 195),
        )
        surface.blit(instruction, (500, 420))

        # -----------------------------------------------------
        # Feedback
        # -----------------------------------------------------
        if self.feedback:
            feedback_color = (70, 230, 120) if self.complete else (255, 110, 100)
            feedback = feedback_font.render(self.feedback, True, feedback_color)
            feedback_rect = feedback.get_rect(
                center=(self.room_x + self.room_width // 2, 485)
            )
            surface.blit(feedback, feedback_rect)

        if self.command_result:
            result = feedback_font.render(self.command_result, True, (90, 220, 255))
            result_rect = result.get_rect(
                center=(self.room_x + self.room_width // 2, 515)
            )
            surface.blit(result, result_rect)

        instruction_bottom = text_font.render(
            "1-4: choose concept | Type a number: terminal input",
            True,
            (155, 160, 175),
        )
        instruction_rect = instruction_bottom.get_rect(
            center=(self.room_x + self.room_width // 2, 555)
        )
        surface.blit(instruction_bottom, instruction_rect)

    def handle_event(self, event):
        """Handle keyboard input for the Level 5 puzzle."""
        if event.type != pygame.KEYDOWN:
            return

        if self.complete:
            return

        # -----------------------------------------------------
        # Select answer
        # -----------------------------------------------------
        option_keys = {
            pygame.K_1: 1,
            pygame.K_2: 2,
            pygame.K_3: 3,
            pygame.K_4: 4,
        }

        if event.key in option_keys:
            selected = option_keys[event.key]
            self.selected_option = selected

            selected_text = self.options[selected - 1]
            correct_text = self.correct_options.get(self.current_step)

            if selected_text == correct_text:
                self.feedback = "CORRECT!"
                if self.game:
                    self.game.score.add(40)

                if self.current_step < self.total_steps:
                    self.current_step += 1
                    self.selected_option = None
                else:
                    self.feedback = (
                        "Function concepts repaired! "
                        "Now test the control terminal."
                    )
            else:
                self.feedback = (
                    f"INCORRECT! Try again. "
                    f"Step {self.current_step} needs "
                    f"{correct_text}."
                )
                if self.game:
                    self.game.security.increase(20)
                    self.game.score.penalize(10)
            return

        # -----------------------------------------------------
        # Terminal input
        # -----------------------------------------------------
        if event.key == pygame.K_BACKSPACE:
            self.command = self.command[:-1]
            return

        if event.key == pygame.K_RETURN:
            try:
                level = int(self.command)
                result = self._unlock_vault(level)
                self.command_result = result

                if level == 5 and self.current_step == self.total_steps:
                    self.complete = True
                    self.feedback = (
                        "CONTROL CENTER RESTORED! "
                        "Master Vault access granted."
                    )
                    if self.game:
                        self.game.score.add(50)
                        self.game.score.add(100)   # level completion bonus
                elif level < 5:
                    self.feedback = "Access denied (level too low)."
                    if self.game:
                        self.game.security.increase(15)
                        self.game.score.penalize(5)

            except ValueError:
                self.command_result = "ERROR: Enter an integer."
                self.feedback = "Exception handled with try/except."
                if self.game:
                    self.game.security.increase(10)

            self.command = ""
            return

        # -----------------------------------------------------
        # Numeric input
        # -----------------------------------------------------
        if event.unicode.isdigit():
            if len(self.command) < 3:
                self.command += event.unicode

    def _unlock_vault(self, level):
        """Return the access result for a supplied security level."""
        if level < 5:
            raise ValueError("Access denied")
        return "RETURN VALUE: MASTER ACCESS"

    def is_complete(self):
        """Return True when Level 5 has been completed."""
        return self.complete
