# memory-heist-main\levels\final_vault.py
#-----------------------------------------

"""
Final Level - Master Vault
Owner: Member 4 - Apporov Sahu

Topics combined:
- variables
- data types
- arithmetic/comparison/logical operators
- conditionals
- loops
- lists
- dictionaries
- indexing
- functions
- parameters
- arguments
- return values
- exception handling

The player must complete a sequence of Python-based security
challenges to unlock the Master Vault.
"""

import pygame


class FinalVault:
    """Controls the final combined Python challenge."""

    def __init__(self):
        """Initialize the Master Vault puzzle."""

        self.complete = False
        self.stage = 1
        self.total_stages = 6

        self.selected_option = None
        self.feedback = ""

        self.command = ""
        self.command_result = ""

        self.options = []

        self.room_x = 40
        self.room_y = 30
        self.room_width = 880
        self.room_height = 560

        # Values used by the final challenge.
        self.agent_id = "MH-07"
        self.clearance_level = 5

        self.security_numbers = [6, 7]

        self.inventory = {
            "keycard": True,
            "access_code": 42,
            "master_key": False,
        }

        self.loop_counter = 0

    def update(self, dt):
        """Update the final vault state."""

        if self.complete:
            return

    def render(self, surface):
        """Draw the Master Vault and its current challenge."""

        title_font = pygame.font.Font(None, 36)
        heading_font = pygame.font.Font(None, 27)
        text_font = pygame.font.Font(None, 22)
        code_font = pygame.font.Font(None, 22)
        option_font = pygame.font.Font(None, 22)
        feedback_font = pygame.font.Font(None, 23)

        # -----------------------------------------------------
        # Room
        # -----------------------------------------------------

        pygame.draw.rect(
            surface,
            (18, 20, 30),
            (
                self.room_x,
                self.room_y,
                self.room_width,
                self.room_height,
            ),
        )

        border_color = (
            (60, 220, 110)
            if self.complete
            else (180, 80, 80)
        )

        pygame.draw.rect(
            surface,
            border_color,
            (
                self.room_x,
                self.room_y,
                self.room_width,
                self.room_height,
            ),
            3,
        )

        # -----------------------------------------------------
        # Title
        # -----------------------------------------------------

        title = title_font.render(
            "FINAL LEVEL - MASTER VAULT",
            True,
            (255, 255, 255),
        )

        surface.blit(
            title,
            (self.room_x + 25, self.room_y + 18),
        )

        progress = text_font.render(
            f"SECURITY CHALLENGE {self.stage}/{self.total_stages}",
            True,
            (255, 215, 80),
        )

        progress_rect = progress.get_rect(
            topright=(
                self.room_x + self.room_width - 25,
                self.room_y + 23,
            )
        )

        surface.blit(progress, progress_rect)

        # -----------------------------------------------------
        # Objective
        # -----------------------------------------------------

        objective = self._get_objective()

        objective_text = text_font.render(
            objective,
            True,
            (195, 205, 215),
        )

        surface.blit(
            objective_text,
            (70, 90),
        )

        # -----------------------------------------------------
        # Security data
        # -----------------------------------------------------

        data_panel = pygame.Rect(
            70,
            125,
            300,
            150,
        )

        pygame.draw.rect(
            surface,
            (8, 12, 20),
            data_panel,
        )

        pygame.draw.rect(
            surface,
            (70, 105, 140),
            data_panel,
            2,
        )

        data_heading = heading_font.render(
            "VAULT DATA",
            True,
            (80, 210, 255),
        )

        surface.blit(
            data_heading,
            (90, 142),
        )

        data_lines = [
            f"agent_id = '{self.agent_id}'",
            f"clearance = {self.clearance_level}",
            f"numbers = {self.security_numbers}",
            f"access_code = {self.inventory['access_code']}",
        ]

        y = 178

        for line in data_lines:

            rendered = code_font.render(
                line,
                True,
                (205, 220, 230),
            )

            surface.blit(
                rendered,
                (90, y),
            )

            y += 23

        # -----------------------------------------------------
        # Challenge panel
        # -----------------------------------------------------

        challenge_panel = pygame.Rect(
            400,
            125,
            470,
            150,
        )

        pygame.draw.rect(
            surface,
            (10, 14, 23),
            challenge_panel,
        )

        pygame.draw.rect(
            surface,
            (100, 110, 150),
            challenge_panel,
            2,
        )

        challenge_heading = heading_font.render(
            "MASTER VAULT CHALLENGE",
            True,
            (235, 235, 240),
        )

        surface.blit(
            challenge_heading,
            (420, 142),
        )

        challenge_lines = self._get_code_lines()

        y = 180

        for line in challenge_lines:

            rendered = code_font.render(
                line,
                True,
                (100, 225, 255),
            )

            surface.blit(
                rendered,
                (420, y),
            )

            y += 24

        # -----------------------------------------------------
        # Options
        # -----------------------------------------------------

        options_heading = heading_font.render(
            "SELECT THE CORRECT ACTION",
            True,
            (245, 245, 245),
        )

        surface.blit(
            options_heading,
            (70, 315),
        )

        self.options = self._get_options()

        option_y = 355

        for index, option in enumerate(self.options):

            color = (235, 235, 240)

            if self.selected_option == index + 1:

                if self._is_correct_option(index + 1):
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
                (85, option_y),
            )

            option_y += 32

        # -----------------------------------------------------
        # Terminal
        # -----------------------------------------------------

        terminal_heading = heading_font.render(
            "FINAL TERMINAL",
            True,
            (80, 210, 255),
        )

        surface.blit(
            terminal_heading,
            (500, 315),
        )

        pygame.draw.rect(
            surface,
            (5, 8, 14),
            (500, 355, 350, 42),
        )

        pygame.draw.rect(
            surface,
            (80, 100, 125),
            (500, 355, 350, 42),
            2,
        )

        input_text = text_font.render(
            self.command if self.command else "Enter final value...",
            True,
            (230, 230, 235),
        )

        surface.blit(
            input_text,
            (512, 365),
        )

        terminal_instruction = text_font.render(
            "Use the terminal when the challenge asks.",
            True,
            (165, 175, 190),
        )

        surface.blit(
            terminal_instruction,
            (500, 410),
        )

        # -----------------------------------------------------
        # Feedback
        # -----------------------------------------------------

        if self.feedback:

            color = (
                (70, 230, 120)
                if self.complete
                else (255, 110, 100)
            )

            feedback = feedback_font.render(
                self.feedback,
                True,
                color,
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

        # -----------------------------------------------------
        # Bottom instruction
        # -----------------------------------------------------

        instruction = text_font.render(
            "1-3: choose an answer | Type numbers when requested | ENTER",
            True,
            (155, 160, 175),
        )

        instruction_rect = instruction.get_rect(
            center=(
                self.room_x + self.room_width // 2,
                555,
            )
        )

        surface.blit(
            instruction,
            instruction_rect,
        )

    def handle_event(self, event):
        """Handle keyboard input for the Master Vault."""

        if event.type != pygame.KEYDOWN:
            return

        if self.complete:
            return

        # -----------------------------------------------------
        # Answer selection
        # -----------------------------------------------------

        option_keys = {
            pygame.K_1: 1,
            pygame.K_2: 2,
            pygame.K_3: 3,
        }

        if event.key in option_keys:

            selected = option_keys[event.key]

            self.selected_option = selected

            if self._is_correct_option(selected):

                self.feedback = "CORRECT!"

                if self.stage < self.total_stages:
                    self.stage += 1
                    self.selected_option = None
                    self.command = ""
                    self.command_result = ""

                else:
                    self.complete = True
                    self.feedback = (
                        "MASTER VAULT UNLOCKED! "
                        "ESCAPE SEQUENCE COMPLETE!"
                    )

            else:

                self.feedback = (
                    "INCORRECT! Review the Python concept "
                    "and try again."
                )

            return

        # -----------------------------------------------------
        # Backspace
        # -----------------------------------------------------

        if event.key == pygame.K_BACKSPACE:

            self.command = self.command[:-1]
            return

        # -----------------------------------------------------
        # Enter
        # -----------------------------------------------------

        if event.key == pygame.K_RETURN:

            self._submit_terminal()
            return

        # -----------------------------------------------------
        # Numeric input
        # -----------------------------------------------------

        if event.unicode.isdigit():

            if len(self.command) < 4:
                self.command += event.unicode

    def _get_objective(self):
        """Return the objective for the current challenge."""

        objectives = {
            1: "Use the correct data type for the clearance level.",
            2: "Choose the operator that generates the access code.",
            3: "Identify the Python loop control statement.",
            4: "Retrieve the correct value from the dictionary.",
            5: "Choose the correct function concept.",
            6: "Handle invalid input safely.",
        }

        return objectives.get(
            self.stage,
            "Complete the Master Vault challenge.",
        )

    def _get_code_lines(self):
        """Return code examples for the current challenge."""

        code = {
            1: [
                "clearance = 5",
                "required = 5",
                "access = clearance == required",
            ],
            2: [
                "a = 6",
                "b = 7",
                "security_code = a ? b",
            ],
            3: [
                "for number in range(10):",
                "    if number == 5:",
                "        ???",
            ],
            4: [
                "vault = {",
                "    'key': 42,",
                "    'status': 'locked'",
                "}",
            ],
            5: [
                "def authorize(level):",
                "    return level >= 5",
                "",
                "authorize(5)",
            ],
            6: [
                "try:",
                "    level = int(user_input)",
                "except ValueError:",
                "    ???",
            ],
        }

        return code.get(
            self.stage,
            [],
        )

    def _get_options(self):
        """Return answer options for the current challenge."""

        options = {
            1: [
                "Store clearance as an integer",
                "Store clearance as a list",
                "Store clearance as a dictionary",
            ],
            2: [
                "+",
                "*",
                "/",
            ],
            3: [
                "continue",
                "return",
                "break",
            ],
            4: [
                "vault['key']",
                "vault[0]",
                "vault.key",
            ],
            5: [
                "parameter",
                "argument",
                "return value",
            ],
            6: [
                "Ignore the error",
                "Use try/except",
                "Delete the function",
            ],
        }

        return options.get(
            self.stage,
            [],
        )

    def _is_correct_option(self, selected):
        """Return True if the selected answer is correct."""

        correct_answers = {
            1: 1,
            2: 2,
            3: 3,
            4: 1,
            5: 3,
            6: 2,
        }

        return selected == correct_answers.get(self.stage)

    def _submit_terminal(self):
        """Process terminal input and demonstrate exception handling."""

        if self.stage not in (1, 2, 4, 6):
            self.feedback = (
                "This challenge is solved using the answer panel."
            )
            return

        try:

            value = int(self.command)

            if self.stage == 1:

                if value == self.clearance_level:
                    self.command_result = (
                        "Integer accepted: clearance verified."
                    )
                else:
                    self.command_result = (
                        "Wrong clearance level."
                    )

            elif self.stage == 2:

                if value == 42:
                    self.command_result = (
                        "Security code verified: 42."
                    )
                else:
                    self.command_result = (
                        "Incorrect security code."
                    )

            elif self.stage == 4:

                if value == self.inventory["access_code"]:
                    self.command_result = (
                        "Dictionary lookup verified: 42."
                    )
                else:
                    self.command_result = (
                        "Incorrect vault value."
                    )

            elif self.stage == 6:

                if value == 5:
                    self.command_result = (
                        "Input recovered safely."
                    )
                else:
                    self.command_result = (
                        "Recovery rejected the invalid value."
                    )

        except ValueError:

            self.command_result = (
                "ValueError caught: invalid input handled safely."
            )

            if self.stage == 6:
                self.feedback = (
                    "EXCEPTION HANDLED! try/except recovery works."
                )

        self.command = ""

    def is_complete(self):
        """Return True when the Master Vault has been unlocked."""

        return self.complete