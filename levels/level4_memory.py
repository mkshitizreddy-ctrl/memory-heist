"""
levels/level4_memory.py
Owner: Member 3

Level 4 - The Memory Vault

Topics:
- lists
- dictionaries
- indexing
- adding/removing elements
- key-value pairs

The level uses systems/inventory.py for inventory operations.
"""

import pygame
import random

from entities.sprites import draw_drone
from systems.inventory import Inventory


class Level4MemoryVault:
    """Controls the Memory Vault level."""

    def __init__(self, player=None, game=None):
        self.game = game

        # -------------------------
        # Level state
        # -------------------------
        self.complete = False
        self.feedback = ""
        self.player = player

        # -------------------------
        # Inventory system
        # -------------------------
        self.inventory = Inventory()

        # -------------------------
        # Items available to collect
        # -------------------------
        self.available_items = [
            "Memory Chip",
            "Access Card",
            "Vault Key"
        ]

        # Items already collected
        self.collected = []

        # -------------------------
        # Item information
        # -------------------------
        self.item_data = {
            "Memory Chip": {
                "position": (130, 170)
            },
            "Access Card": {
                "position": (390, 285)
            },
            "Vault Key": {
                "position": (610, 160)
            }
        }

        # -------------------------
        # Vault dictionary
        # -------------------------
        # The Memory Chip is the actual item required
        # to unlock the Memory Vault.
        self.vault_data = {
            "required_item": "Memory Chip",
            "vault_code": "42",
            "status": "LOCKED"
        }

        # Playable area matches the room drawn in render().
        self.room_bounds = pygame.Rect(45, 80, 870, 300)

        # Vault position
        self.vault_rect = pygame.Rect(
            770,
            235,
            100,
            80
        )

        # Selected inventory index
        self.selected_index = None

        # -------------------------
        # Python hacking gates
        # -------------------------
        # Each terminal has a small question pool. A new question is
        # selected whenever the player opens that terminal.
        self.gates = [
            {
                "name": "Memory Access",
                "rect": pygame.Rect(280, 120, 125, 48),
                "unlocked": False,
                "questions": [
                    {
                        "question": (
                            "items = ['Chip', 'Card', 'Key'] | "
                            "What does items[1] return?"
                        ),
                        "options": [
                            "Card",
                            "Chip",
                            "Key",
                            "Error"
                        ],
                        "answer": 0,
                        "topic": "LIST INDEXING",
                        "correct_text": (
                            "Python indexing starts at 0, so index 1 is the second item."
                        ),
                        "correct_code": "items[1] -> 'Card'",
                        "wrong_text": (
                            "Remember: Python list indexes start at 0."
                        ),
                        "wrong_code": "items[0] = first item"
                    },
                    {
                        "question": (
                            "items = ['Chip', 'Card', 'Key'] | "
                            "What does items[0] return?"
                        ),
                        "options": [
                            "Chip",
                            "Card",
                            "Key",
                            "Error"
                        ],
                        "answer": 0,
                        "topic": "LIST INDEXING",
                        "correct_text": (
                            "Index 0 refers to the first item in a Python list."
                        ),
                        "correct_code": "items[0] -> 'Chip'",
                        "wrong_text": (
                            "The first list item is at index 0."
                        ),
                        "wrong_code": "items[0] = first item"
                    },
                    {
                        "question": (
                            "items = ['Chip', 'Card', 'Key'] | "
                            "What does items[-1] return?"
                        ),
                        "options": [
                            "Chip",
                            "Card",
                            "Key",
                            "Error"
                        ],
                        "answer": 2,
                        "topic": "LIST INDEXING",
                        "correct_text": (
                            "Index -1 refers to the last item in a Python list."
                        ),
                        "correct_code": "items[-1] -> 'Key'",
                        "wrong_text": (
                            "Negative indexing counts from the end of the list."
                        ),
                        "wrong_code": "items[-1] = last item"
                    },
                    {
                        "question": (
                            "items = ['Chip', 'Card', 'Key'] | "
                            "Which item is at index 2?"
                        ),
                        "options": [
                            "Chip",
                            "Card",
                            "Key",
                            "Error"
                        ],
                        "answer": 2,
                        "topic": "LIST INDEXING",
                        "correct_text": (
                            "Index 2 is the third position because indexing starts at 0."
                        ),
                        "correct_code": "items[2] -> 'Key'",
                        "wrong_text": (
                            "Count positions from 0: 0, 1, 2."
                        ),
                        "wrong_code": "items[2] = third item"
                    }
                ],
                "question": "",
                "options": [],
                "answer": 0,
                "topic": "LIST INDEXING"
            },
            {
                "name": "Credential Storage",
                "rect": pygame.Rect(485, 120, 145, 48),
                "unlocked": False,
                "questions": [
                    {
                        "question": "How do you access the value of key 'access'?",
                        "options": [
                            "data.access",
                            "data['access']",
                            "data[access()]",
                            "data(0)"
                        ],
                        "answer": 1,
                        "topic": "DICTIONARIES",
                        "correct_text": "Dictionaries use keys to access their values.",
                        "correct_code": "data['access']",
                        "wrong_text": "Use the key inside square brackets.",
                        "wrong_code": "data['key']"
                    },
                    {
                        "question": (
                            "data = {'access': 'Memory Chip'} | "
                            "What does data['access'] return?"
                        ),
                        "options": [
                            "access",
                            "Memory Chip",
                            "data",
                            "Error"
                        ],
                        "answer": 1,
                        "topic": "KEY-VALUE PAIRS",
                        "correct_text": "The key 'access' maps to the value 'Memory Chip'.",
                        "correct_code": "data['access'] -> 'Memory Chip'",
                        "wrong_text": "Square brackets use the key to retrieve its value.",
                        "wrong_code": "data['key'] -> value"
                    },
                    {
                        "question": "How do you add a new key 'code' with value 42?",
                        "options": [
                            "data['code'] = 42",
                            "data.add('code', 42)",
                            "data.append(42)",
                            "data[42] = 'code'"
                        ],
                        "answer": 0,
                        "topic": "DICTIONARIES",
                        "correct_text": "Assigning to a new key adds a key-value pair.",
                        "correct_code": "data['code'] = 42",
                        "wrong_text": "Dictionaries add entries by assigning a value to a key.",
                        "wrong_code": "data['new_key'] = value"
                    },
                    {
                        "question": "In a dictionary, what does a key identify?",
                        "options": [
                            "A value",
                            "A list index",
                            "A value's name",
                            "The whole program"
                        ],
                        "answer": 2,
                        "topic": "KEY-VALUE PAIRS",
                        "correct_text": "A key identifies the value stored in a dictionary entry.",
                        "correct_code": "key -> value",
                        "wrong_text": "Think of a dictionary as key-value pairs.",
                        "wrong_code": "data[key] -> value"
                    }
                ],
                "question": "",
                "options": [],
                "answer": 0,
                "topic": "DICTIONARIES"
            },
            {
                "name": "Security Override",
                "rect": pygame.Rect(700, 120, 145, 48),
                "unlocked": False,
                "questions": [
                    {
                        "question": "What does inventory.append('Key') do?",
                        "options": [
                            "Removes Key",
                            "Sorts inventory",
                            "Adds Key to the list",
                            "Clears inventory"
                        ],
                        "answer": 2,
                        "topic": "LIST OPERATIONS",
                        "correct_text": "append() adds a new item to a Python list.",
                        "correct_code": "inventory.append('Key')",
                        "wrong_text": "append() adds an item; it does not remove one.",
                        "wrong_code": "inventory.append('item')"
                    },
                    {
                        "question": "What does inventory.remove('Card') do?",
                        "options": [
                            "Adds Card",
                            "Removes Card",
                            "Sorts Card",
                            "Copies Card"
                        ],
                        "answer": 1,
                        "topic": "LIST OPERATIONS",
                        "correct_text": "remove() deletes the matching item from the list.",
                        "correct_code": "inventory.remove('Card')",
                        "wrong_text": "remove() is used to delete a matching item.",
                        "wrong_code": "list.remove(item)"
                    },
                    {
                        "question": "What does inventory.pop() normally do?",
                        "options": [
                            "Adds an item",
                            "Removes and returns an item",
                            "Sorts the list",
                            "Creates a dictionary"
                        ],
                        "answer": 1,
                        "topic": "LIST OPERATIONS",
                        "correct_text": "pop() removes and returns an item from a list.",
                        "correct_code": "inventory.pop()",
                        "wrong_text": "pop() removes an item; append() adds one.",
                        "wrong_code": "append() -> add | pop() -> remove"
                    },
                    {
                        "question": "What does len(inventory) tell you?",
                        "options": [
                            "Number of items",
                            "First item",
                            "Last item",
                            "Dictionary key"
                        ],
                        "answer": 0,
                        "topic": "LIST OPERATIONS",
                        "correct_text": "len() tells you how many items are in a list.",
                        "correct_code": "len(inventory) -> number of items",
                        "wrong_text": "len() counts the items; it does not select one.",
                        "wrong_code": "len(list) -> count"
                    }
                ],
                "question": "",
                "options": [],
                "answer": 0,
                "topic": "LIST OPERATIONS"
            }
        ]

        self.active_gate = None
        self.hacking_active = False
        self.gate_feedback = ""

        # -------------------------
        # Companion recon drone
        # -------------------------
        start_x, start_y = (
            self.player.rect.center
            if self.player
            else (110, 130)
        )

        self.drone_x = float(start_x - 34)
        self.drone_y = float(start_y - 38)

        self.drone_scan_message = (
            "Drone ready. Press Q to scan."
        )

        # -------------------------
        # Enemy security drone
        # -------------------------
        self.security_drone_x = 520.0
        self.security_drone_y = 340.0

        self.security_drone_min_x = 500.0
        self.security_drone_max_x = 790.0

        self.security_drone_direction = 1
        self.security_drone_speed = 85.0

        self.security_drone_detection_range = 115.0

        self.security_alert_cooldown = 0.0
        self.security_drone_detecting = False

        # -------------------------
        # Companion drone distraction
        # -------------------------
        self.drone_distraction_duration = 4.0
        self.drone_distraction_timer = 0.0

        self.drone_distraction_cooldown = 0.0
        self.drone_distraction_cooldown_max = 12.0

        self.security_drone_distracted = False

        # -------------------------
        # Python learning panel
        # -------------------------
        self.concept_title = "LISTS"

        self.concept_text = (
            "Your inventory is a Python list."
        )

        self.concept_code = (
            'inventory.append("item")'
        )

    # =========================================================
    # PLAYER
    # =========================================================

    def set_player(self, player):
        """Set the player used for level interaction."""
        self.player = player

    # =========================================================
    # COLLISION
    # =========================================================

    def get_bounds(self):
        """Return the playable room bounds."""
        return self.room_bounds

    def get_obstacles(self):
        """Return objects that block player movement."""
        return []

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, dt):
        """Update the Memory Vault level."""

        if self.complete:
            return

        # -----------------------------------------------------
        # Companion drone follows player
        # -----------------------------------------------------
        if self.player:
            target_x = self.player.rect.centerx - 34
            target_y = self.player.rect.centery - 38

            follow_speed = min(
                1.0,
                max(0.0, dt * 5.0)
            )

            self.drone_x += (
                target_x - self.drone_x
            ) * follow_speed

            self.drone_y += (
                target_y - self.drone_y
            ) * follow_speed

        safe_dt = max(0.0, dt)

        # -----------------------------------------------------
        # Drone distraction timers
        # -----------------------------------------------------
        self.drone_distraction_cooldown = max(
            0.0,
            self.drone_distraction_cooldown - safe_dt
        )

        self.drone_distraction_timer = max(
            0.0,
            self.drone_distraction_timer - safe_dt
        )

        self.security_drone_distracted = (
            self.drone_distraction_timer > 0.0
        )

        # -----------------------------------------------------
        # Security drone patrol
        # -----------------------------------------------------
        if not self.security_drone_distracted:
            self.security_drone_x += (
                self.security_drone_direction
                * self.security_drone_speed
                * safe_dt
            )

            if (
                self.security_drone_x
                >= self.security_drone_max_x
            ):
                self.security_drone_x = (
                    self.security_drone_max_x
                )
                self.security_drone_direction = -1

            elif (
                self.security_drone_x
                <= self.security_drone_min_x
            ):
                self.security_drone_x = (
                    self.security_drone_min_x
                )
                self.security_drone_direction = 1

        # -----------------------------------------------------
        # Security detection
        # -----------------------------------------------------
        self.security_alert_cooldown = max(
            0.0,
            self.security_alert_cooldown - safe_dt
        )

        self.security_drone_detecting = False

        if (
            self.player
            and not self.security_drone_distracted
        ):
            player_center = pygame.Vector2(
                self.player.rect.center
            )

            enemy_center = pygame.Vector2(
                self.security_drone_x,
                self.security_drone_y
            )

            distance = player_center.distance_to(
                enemy_center
            )

            self.security_drone_detecting = (
                distance
                <= self.security_drone_detection_range
            )

            if (
                self.security_drone_detecting
                and self.security_alert_cooldown <= 0.0
            ):
                if self.game:
                    self.game.security.increase(8)

                self.feedback = (
                    "Security drone detected you! "
                    "Move away."
                )

                self.security_alert_cooldown = 1.8

    # =========================================================
    # RENDER
    # =========================================================

    def _get_render_fonts(self):
        """Return this screen's fonts, creating them only once.

        pygame.font.Font() costs about 2 ms per call, so creating fonts
        inside render() used up most of a 16.7 ms frame.
        """
        if getattr(self, "_render_fonts", None) is None:
            self._render_fonts = (
                pygame.font.Font(None, 34),
                pygame.font.Font(None, 25),
                pygame.font.Font(None, 21),
                pygame.font.Font(None, 18),
            )
        return self._render_fonts

    def render(self, surface):
        """Draw the Memory Vault room and interface."""

        # -------------------------
        # Fonts
        # -------------------------
        (
            title_font,
            heading_font,
            text_font,
            small_font,
        ) = self._get_render_fonts()

        # =====================================================
        # GAME ROOM
        # =====================================================

        room_rect = self.room_bounds

        pygame.draw.rect(
            surface,
            (25, 30, 43),
            room_rect
        )

        pygame.draw.rect(
            surface,
            (80, 90, 115),
            room_rect,
            2
        )

        room_text = small_font.render(
            "MEMORY VAULT STORAGE AREA",
            True,
            (120, 130, 150)
        )

        surface.blit(
            room_text,
            (65, 95)
        )

        # =====================================================
        # HACKING TERMINALS
        # =====================================================

        for gate in self.gates:
            gate_rect = gate["rect"]

            if gate["unlocked"]:
                gate_color = (70, 220, 120)
                gate_label = "OPEN"
            else:
                gate_color = (100, 170, 255)
                gate_label = "LOCKED"

            pygame.draw.rect(
                surface,
                (30, 42, 58),
                gate_rect
            )

            pygame.draw.rect(
                surface,
                gate_color,
                gate_rect,
                2
            )

            gate_name = small_font.render(
                gate["name"],
                True,
                (235, 235, 240)
            )

            surface.blit(
                gate_name,
                (
                    gate_rect.x + 5,
                    gate_rect.y + 5
                )
            )

            gate_status = small_font.render(
                gate_label,
                True,
                gate_color
            )

            surface.blit(
                gate_status,
                (
                    gate_rect.x + 5,
                    gate_rect.y + 27
                )
            )

            if (
                self.player
                and not gate["unlocked"]
            ):
                if self.player.rect.inflate(
                    70,
                    70
                ).colliderect(gate_rect):

                    prompt = small_font.render(
                        "Press E to hack",
                        True,
                        (90, 230, 150)
                    )

                    surface.blit(
                        prompt,
                        (
                            gate_rect.x,
                            gate_rect.y - 18
                        )
                    )

        # Gate progress
        gate_count = sum(
            1
            for gate in self.gates
            if gate["unlocked"]
        )

        gate_progress = small_font.render(
            f"Security Gates: {gate_count}/3 unlocked",
            True,
            (160, 210, 255)
        )

        surface.blit(
            gate_progress,
            (650, 95)
        )

        # =====================================================
        # HACKING QUESTION OVERLAY
        # =====================================================

        if (
            self.hacking_active
            and self.active_gate is not None
        ):
            panel = pygame.Rect(
                120,
                145,
                720,
                230
            )

            pygame.draw.rect(
                surface,
                (18, 24, 38),
                panel
            )

            pygame.draw.rect(
                surface,
                (100, 170, 255),
                panel,
                3
            )

            gate = self.gates[self.active_gate]

            # Question
            question = heading_font.render(
                gate["question"],
                True,
                (245, 245, 250)
            )

            surface.blit(
                question,
                (
                    panel.x + 20,
                    panel.y + 18
                )
            )

            # Options
            for option_index, option in enumerate(
                gate["options"]
            ):
                option_text = text_font.render(
                    f"{option_index + 1}. {option}",
                    True,
                    (210, 220, 235)
                )

                surface.blit(
                    option_text,
                    (
                        panel.x + 25,
                        panel.y + 62
                        + option_index * 30
                    )
                )

            # Hint
            hint = small_font.render(
                "Press 1-4 to answer | ESC to close",
                True,
                (100, 220, 170)
            )

            surface.blit(
                hint,
                (
                    panel.x + 20,
                    panel.bottom - 25
                )
            )

        # =====================================================
        # COMPANION RECON DRONE
        # =====================================================

        drone_center = (
            int(self.drone_x),
            int(self.drone_y)
        )

        rotor_tick = pygame.time.get_ticks() // 90

        draw_drone(
            surface,
            drone_center,
            "ally",
            rotor_tick
        )

        drone_hint = small_font.render(
            "ALLY DRONE | Q: Scan | X: Distract",
            True,
            (90, 220, 245)
        )

        surface.blit(
            drone_hint,
            (
                room_rect.x + 12,
                room_rect.bottom - 24
            )
        )

        # Drone status
        if self.drone_distraction_timer > 0:
            drone_status_text = (
                f"Enemy distracted: "
                f"{self.drone_distraction_timer:.1f}s"
            )

        elif self.drone_distraction_cooldown > 0:
            drone_status_text = (
                f"Distraction recharging: "
                f"{self.drone_distraction_cooldown:.1f}s"
            )

        else:
            drone_status_text = (
                "Distraction ready (X)"
            )

        drone_status = small_font.render(
            drone_status_text,
            True,
            (110, 205, 255)
        )

        surface.blit(
            drone_status,
            (
                room_rect.x + 12,
                room_rect.bottom - 43
            )
        )

        # =====================================================
        # ENEMY SECURITY DRONE
        # =====================================================

        enemy_center = (
            int(self.security_drone_x),
            int(self.security_drone_y)
        )

        if self.security_drone_distracted:
            enemy_color = (100, 190, 255)
            enemy_kind = "enemy_distracted"

        elif self.security_drone_detecting:
            enemy_color = (255, 85, 75)
            enemy_kind = "enemy_alert"

        else:
            enemy_color = (230, 145, 65)
            enemy_kind = "enemy"

        draw_drone(
            surface,
            enemy_center,
            enemy_kind,
            rotor_tick
        )

        if self.security_drone_distracted:
            enemy_label_text = "DISTRACTED"

        elif self.security_drone_detecting:
            enemy_label_text = "ALERT!"

        else:
            enemy_label_text = "SECURITY DRONE"

        enemy_label = small_font.render(
            enemy_label_text,
            True,
            enemy_color
        )

        surface.blit(
            enemy_label,
            (
                enemy_center[0] - 48,
                enemy_center[1] - 25
            )
        )

        if (
            self.security_drone_detecting
            and not self.security_drone_distracted
            and self.player
        ):
            pygame.draw.line(
                surface,
                (220, 75, 75),
                enemy_center,
                self.player.rect.center,
                2
            )

        # =====================================================
        # ITEMS
        # =====================================================

        item_colors = {
            "Memory Chip": (70, 180, 220),
            "Access Card": (190, 150, 70),
            "Vault Key": (90, 210, 120)
        }

        for item in self.available_items:

            if item in self.collected:
                continue

            position = self.item_data[item]["position"]

            item_rect = pygame.Rect(
                position[0],
                position[1],
                120,
                55
            )

            pygame.draw.rect(
                surface,
                (35, 40, 55),
                item_rect
            )

            pygame.draw.rect(
                surface,
                item_colors[item],
                item_rect,
                2
            )

            item_text = small_font.render(
                item,
                True,
                (235, 235, 240)
            )

            item_text_rect = item_text.get_rect(
                center=item_rect.center
            )

            surface.blit(
                item_text,
                item_text_rect
            )

            # Interaction prompt
            if self.player:

                interaction_rect = (
                    self.player.rect.inflate(
                        70,
                        70
                    )
                )

                if interaction_rect.colliderect(
                    item_rect
                ):

                    prompt = small_font.render(
                        "Press E to collect",
                        True,
                        (90, 230, 150)
                    )

                    prompt_rect = prompt.get_rect(
                        centerx=item_rect.centerx,
                        bottom=item_rect.top - 15
                    )

                    surface.blit(
                        prompt,
                        prompt_rect
                    )

        # =====================================================
        # VAULT
        # =====================================================

        if self.complete:
            vault_color = (60, 220, 100)
            vault_label = "UNLOCKED"

        else:
            vault_color = (210, 130, 70)
            vault_label = "LOCKED"

        pygame.draw.rect(
            surface,
            (40, 30, 42),
            self.vault_rect
        )

        pygame.draw.rect(
            surface,
            vault_color,
            self.vault_rect,
            3
        )

        vault_text = heading_font.render(
            "VAULT",
            True,
            vault_color
        )

        vault_text_rect = vault_text.get_rect(
            center=(
                self.vault_rect.centerx,
                self.vault_rect.centery - 10
            )
        )

        surface.blit(
            vault_text,
            vault_text_rect
        )

        status_text = small_font.render(
            vault_label,
            True,
            (220, 220, 225)
        )

        status_rect = status_text.get_rect(
            center=(
                self.vault_rect.centerx,
                self.vault_rect.centery + 18
            )
        )

        surface.blit(
            status_text,
            status_rect
        )

        # Show the exact item required by the vault.
        required_text = small_font.render(
            f"Requires: {self.vault_data['required_item']}",
            True,
            (150, 205, 255)
        )

        required_rect = required_text.get_rect(
            centerx=self.vault_rect.centerx,
            top=self.vault_rect.bottom + 8
        )

        surface.blit(
            required_text,
            required_rect
        )

        # Vault interaction prompt
        if (
            self.player
            and not self.complete
        ):

            interaction_rect = (
                self.player.rect.inflate(
                    70,
                    70
                )
            )

            if interaction_rect.colliderect(
                self.vault_rect
            ):

                prompt = small_font.render(
                    "Press E to interact",
                    True,
                    (90, 230, 150)
                )

                prompt_rect = prompt.get_rect(
                    centerx=self.vault_rect.centerx,
                    bottom=self.vault_rect.top - 15
                )

                surface.blit(
                    prompt,
                    prompt_rect
                )

        # =====================================================
        # INVENTORY
        # =====================================================

        inventory_rect = pygame.Rect(
            45,
            395,
            270,
            195
        )

        pygame.draw.rect(
            surface,
            (29, 34, 48),
            inventory_rect
        )

        pygame.draw.rect(
            surface,
            (100, 80, 150),
            inventory_rect,
            2
        )

        inventory_title = heading_font.render(
            "PLAYER INVENTORY",
            True,
            (190, 140, 255)
        )

        surface.blit(
            inventory_title,
            (65, 415)
        )

        if self.inventory.items:

            y = 450

            for index, item in enumerate(
                self.inventory.items
            ):

                if self.selected_index == index:
                    item_color = (80, 230, 120)
                    prefix = "> "
                else:
                    item_color = (235, 235, 240)
                    prefix = "  "

                item_text = text_font.render(
                    f"{prefix}[{index + 1}] {item}",
                    True,
                    item_color
                )

                surface.blit(
                    item_text,
                    (65, y)
                )

                y += 28

        else:

            empty_text = small_font.render(
                "Inventory empty.",
                True,
                (150, 155, 165)
            )

            surface.blit(
                empty_text,
                (65, 450)
            )

        # Inventory count
        count_text = small_font.render(
            f"Slots used: {len(self.inventory.items)} / "
            f"{self.inventory.capacity}",
            True,
            (170, 175, 185)
        )

        surface.blit(
            count_text,
            (65, 555)
        )

        # =====================================================
        # PYTHON CONCEPT
        # =====================================================

        concept_rect = pygame.Rect(
            335,
            395,
            580,
            195
        )

        pygame.draw.rect(
            surface,
            (24, 31, 42),
            concept_rect
        )

        pygame.draw.rect(
            surface,
            (60, 150, 120),
            concept_rect,
            2
        )

        concept_heading = heading_font.render(
            "PYTHON CONCEPT",
            True,
            (80, 220, 150)
        )

        surface.blit(
            concept_heading,
            (355, 415)
        )

        concept_title = text_font.render(
            self.concept_title,
            True,
            (240, 240, 240)
        )

        surface.blit(
            concept_title,
            (355, 447)
        )

        concept_text = small_font.render(
            self.concept_text,
            True,
            (190, 195, 205)
        )

        surface.blit(
            concept_text,
            (355, 475)
        )

        concept_code = small_font.render(
            self.concept_code,
            True,
            (100, 210, 255)
        )

        surface.blit(
            concept_code,
            (355, 505)
        )

        # Feedback
        if self.feedback:

            if self.complete:
                feedback_color = (70, 230, 110)
            else:
                feedback_color = (255, 110, 100)

            feedback = small_font.render(
                self.feedback,
                True,
                feedback_color
            )

            surface.blit(
                feedback,
                (355, 540)
            )

        # =====================================================
        # CONTROLS
        # =====================================================

        controls = small_font.render(
            "WASD Move | E Interact | Q Scan | "
            "X Distract | 1-3 Select | ENTER Use",
            True,
            (175, 180, 190)
        )

        controls_rect = controls.get_rect(
            center=(625, 565)
        )

        surface.blit(
            controls,
            controls_rect
        )

    # =========================================================
    # EVENT HANDLING
    # =========================================================

    def handle_event(self, event):
        """Handle interaction and inventory controls."""

        if event.type != pygame.KEYDOWN:
            return

        if self.complete:
            return

        # -------------------------
        # Answer active hacking question
        # -------------------------
        if self.hacking_active:

            if event.key == pygame.K_ESCAPE:

                self.hacking_active = False
                self.active_gate = None
                self.feedback = "Hacking cancelled."

                return

            answer_keys = {
                pygame.K_1: 0,
                pygame.K_2: 1,
                pygame.K_3: 2,
                pygame.K_4: 3
            }

            if event.key in answer_keys:

                self.answer_gate(
                    answer_keys[event.key]
                )

            return

        # -------------------------
        # Companion drone distraction
        # -------------------------
        if event.key == pygame.K_x:

            self.activate_drone_distraction()

            return

        # -------------------------
        # Drone scan
        # -------------------------
        if event.key == pygame.K_q:

            self.scan_with_drone()

            return

        # -------------------------
        # World interaction
        # -------------------------
        if event.key == pygame.K_e:

            if self.player:
                self.interact(self.player)

        # Player 2 interaction
        elif event.key == pygame.K_RSHIFT:

            if (
                self.game
                and getattr(
                    self.game,
                    "coop",
                    False
                )
            ):
                self.interact(
                    self.game.player2
                )

        # -------------------------
        # Inventory selection
        # -------------------------
        elif event.key == pygame.K_1:

            self.select_item(0)

        elif event.key == pygame.K_2:

            self.select_item(1)

        elif event.key == pygame.K_3:

            self.select_item(2)

        # -------------------------
        # Use selected item
        # -------------------------
        elif event.key == pygame.K_RETURN:

            self.use_selected_item()

    # =========================================================
    # INTERACTION
    # =========================================================

    def interact(self, player):
        """
        Hack nearby terminals, collect items,
        or interact with the vault.
        """

        interaction_rect = player.rect.inflate(
            70,
            70
        )

        # -----------------------------------------------------
        # Check hacking terminals first
        # -----------------------------------------------------
        for index, gate in enumerate(
            self.gates
        ):

            if (
                not gate["unlocked"]
                and interaction_rect.colliderect(
                    gate["rect"]
                )
            ):

                # Pick a question from this terminal's pool.
                question_data = random.choice(
                    gate["questions"]
                )

                gate["question"] = question_data["question"]
                gate["options"] = question_data["options"]
                gate["answer"] = question_data["answer"]
                gate["topic"] = question_data["topic"]
                gate["correct_text"] = question_data["correct_text"]
                gate["correct_code"] = question_data["correct_code"]
                gate["wrong_text"] = question_data["wrong_text"]
                gate["wrong_code"] = question_data["wrong_code"]

                self.active_gate = index
                self.hacking_active = True

                self.feedback = (
                    f"Hacking: {gate['name']}"
                )

                self.concept_title = gate["topic"]

                self.concept_text = (
                    "Use the Python concept shown "
                    "in the question to unlock this terminal."
                )

                self.concept_code = (
                    "Choose the correct option (1-4)."
                )

                return

        # -----------------------------------------------------
        # Check items
        # -----------------------------------------------------
        for item in self.available_items:

            if item in self.collected:
                continue

            position = self.item_data[item]["position"]

            item_rect = pygame.Rect(
                position[0],
                position[1],
                120,
                55
            )

            if interaction_rect.colliderect(
                item_rect
            ):

                self.collect_item(item)

                return

        # -----------------------------------------------------
        # Check vault
        # -----------------------------------------------------
        if interaction_rect.colliderect(
            self.vault_rect
        ):

            # All security gates must be unlocked.
            if not all(
                gate["unlocked"]
                for gate in self.gates
            ):

                self.feedback = (
                    "Unlock all 3 security gates first."
                )

                self.concept_title = (
                    "SECURITY GATES"
                )

                self.concept_text = (
                    "The vault remains protected "
                    "until every terminal is unlocked."
                )

                self.concept_code = (
                    "all(gate['unlocked'] for gate in gates)"
                )

                return

            # If an item is selected, use it.
            if self.selected_index is not None:

                self.use_selected_item()

            else:

                self.feedback = (
                    "Select an inventory item first."
                )

                self.concept_title = "INDEXING"

                self.concept_text = (
                    "Select an item by its position "
                    "in the list."
                )

                self.concept_code = (
                    "inventory[index]"
                )

    # =========================================================
    # DRONE DISTRACTION
    # =========================================================

    def activate_drone_distraction(self):
        """Temporarily distract the security drone."""

        if self.drone_distraction_timer > 0:

            self.feedback = (
                "Security drone is already distracted "
                f"({self.drone_distraction_timer:.1f}s left)."
            )

            return

        if self.drone_distraction_cooldown > 0:

            self.feedback = (
                "Drone distraction recharging: "
                f"{self.drone_distraction_cooldown:.1f}s."
            )

            return

        self.drone_distraction_timer = (
            self.drone_distraction_duration
        )

        self.drone_distraction_cooldown = (
            self.drone_distraction_cooldown_max
        )

        self.security_drone_detecting = False

        self.feedback = (
            "Security drone distracted! Move quickly."
        )

        self.concept_title = (
            "DRONE DISTRACTION"
        )

        self.concept_text = (
            "The enemy sensor is temporarily occupied."
        )

        self.concept_code = (
            "distraction_timer = 4 seconds"
        )

    # =========================================================
    # DRONE SCAN
    # =========================================================

    def scan_with_drone(self):
        """Report the nearest uncollected item or terminal."""

        if not self.player:

            self.feedback = (
                "Drone cannot locate the player."
            )

            return

        player_center = pygame.Vector2(
            self.player.rect.center
        )

        targets = []

        # -----------------------------------------------------
        # Items
        # -----------------------------------------------------
        for item in self.available_items:

            if item in self.collected:
                continue

            x, y = self.item_data[item]["position"]

            target_center = pygame.Vector2(
                x + 60,
                y + 27
            )

            targets.append(
                (
                    player_center.distance_to(
                        target_center
                    ),
                    item
                )
            )

        # -----------------------------------------------------
        # Locked terminals
        # -----------------------------------------------------
        for gate in self.gates:

            if gate["unlocked"]:
                continue

            targets.append(
                (
                    player_center.distance_to(
                        pygame.Vector2(
                            gate["rect"].center
                        )
                    ),
                    gate["name"] + " terminal"
                )
            )

        # -----------------------------------------------------
        # Scan result
        # -----------------------------------------------------
        if not targets:

            self.drone_scan_message = (
                "Scan complete: no remaining targets."
            )

        else:

            distance, target_name = min(
                targets,
                key=lambda target: target[0]
            )

            self.drone_scan_message = (
                f"Scan: {target_name} is the nearest "
                f"target ({int(distance)} units)."
            )

        self.feedback = (
            self.drone_scan_message
        )

        self.concept_title = (
            "DRONE RECON"
        )

        self.concept_text = (
            self.drone_scan_message
        )

        self.concept_code = (
            "nearest_target = min(targets)"
        )

    # =========================================================
    # HACKING GATES
    # =========================================================

    def answer_gate(self, chosen_answer):
        """Check the selected answer for the active terminal."""

        if self.active_gate is None:
            return

        gate = self.gates[
            self.active_gate
        ]

        # -----------------------------------------------------
        # Correct answer
        # -----------------------------------------------------
        if chosen_answer == gate["answer"]:

            gate["unlocked"] = True

            self.feedback = (
                f"{gate['name']} unlocked!"
            )

            self.gate_feedback = (
                self.feedback
            )

            self.concept_title = (
                gate["topic"]
            )

            self.concept_text = gate.get(
                "correct_text",
                "Correct! Apply the Python concept shown above."
            )

            self.concept_code = gate.get(
                "correct_code",
                "Review the example in the question."
            )

            if self.game:
                self.game.score.add(40)

        # -----------------------------------------------------
        # Incorrect answer
        # -----------------------------------------------------
        else:

            self.feedback = (
                "Incorrect answer. Security alert increased."
            )

            self.concept_title = (
                gate["topic"]
            )

            self.concept_text = gate.get(
                "wrong_text",
                "Review the Python concept shown above and try again."
            )

            self.concept_code = gate.get(
                "wrong_code",
                "Review the example in the question."
            )

            if self.game:

                self.game.security.increase(15)
                self.game.score.penalize(10)

        self.hacking_active = False
        self.active_gate = None

    # =========================================================
    # COLLECT ITEM
    # =========================================================

    def collect_item(self, item):
        """Add an item to the inventory."""

        if item in self.collected:
            return

        if self.inventory.add_item(item):

            self.collected.append(item)

            self.feedback = (
                f"{item} added to inventory."
            )

            if self.game:
                self.game.score.add(30)

            # Explain list adding.
            self.concept_title = (
                "LISTS - ADDING ELEMENTS"
            )

            self.concept_text = (
                "append() adds an item to a Python list."
            )

            self.concept_code = (
                f'inventory.append("{item}")'
            )

        else:

            self.feedback = (
                "Inventory is full."
            )

    # =========================================================
    # SELECT ITEM
    # =========================================================

    def select_item(self, index):
        """
        Select an inventory item using its
        Python list index.
        """

        # Check whether the index exists.
        if index >= len(
            self.inventory.items
        ):

            self.feedback = (
                "That inventory slot is empty."
            )

            self.concept_title = (
                "INDEXING"
            )

            self.concept_text = (
                "An index must point to an "
                "existing item."
            )

            self.concept_code = (
                "inventory[index]"
            )

            return

        self.selected_index = index

        item = self.inventory.items[index]

        self.feedback = (
            f"Selected: {item}"
        )

        self.concept_title = (
            "INDEXING"
        )

        self.concept_text = (
            "Indexing gets an item from the inventory list. "
            "The vault dictionary tells us which item is required."
        )

        self.concept_code = (
            f"inventory[{index}] -> {item} | "
            'vault_data["required_item"] -> "Memory Chip"'
        )

    # =========================================================
    # USE ITEM
    # =========================================================

    def use_selected_item(self):
        """Use the selected item on the vault when the player is nearby."""

        # ENTER should only work when the player is actually near the vault.
        if not self.player:
            self.feedback = "Player is not available."
            return

        interaction_rect = self.player.rect.inflate(70, 70)

        if not interaction_rect.colliderect(self.vault_rect):
            self.feedback = "Move closer to the vault before using an item."
            return

        # No item selected.
        if self.selected_index is None:

            self.feedback = (
                "Select an inventory item first."
            )

            return

        # Make sure selected index still exists.
        if (
            self.selected_index
            >= len(self.inventory.items)
        ):

            self.selected_index = None

            return

        # -----------------------------------------------------
        # LIST INDEXING
        # -----------------------------------------------------
        #
        # Get the item from the list using its index.
        #
        item = self.inventory.items[
            self.selected_index
        ]

        # -----------------------------------------------------
        # DICTIONARY KEY-VALUE PAIR
        # -----------------------------------------------------
        #
        # The vault stores the required item
        # inside a dictionary.
        #
        required_item = self.vault_data[
            "required_item"
        ]

        # -----------------------------------------------------
        # Security gate requirement
        # -----------------------------------------------------
        if not all(
            gate["unlocked"]
            for gate in self.gates
        ):

            self.feedback = (
                "Unlock all 3 security gates "
                "before using the Memory Chip."
            )

            return

        # -----------------------------------------------------
        # Correct item
        # -----------------------------------------------------
        if item == required_item:

            # Remove the used item from the list.
            self.inventory.remove_item(item)

            # Update dictionary value.
            self.vault_data[
                "status"
            ] = "UNLOCKED"

            self.complete = True
            self.selected_index = None

            self.feedback = (
                "Correct! Memory Chip used. "
                "Memory Vault unlocked!"
            )

            if self.game:

                self.game.score.add(50)
                self.game.score.add(100)

            self.concept_title = (
                "DICTIONARIES + REMOVE"
            )

            self.concept_text = (
                "The dictionary tells us which item "
                "the vault requires. The used item "
                "is then removed from the list."
            )

            self.concept_code = (
                'vault_data["required_item"] '
                '-> "Memory Chip"'
            )

        # -----------------------------------------------------
        # Wrong item
        # -----------------------------------------------------
        else:

            self.feedback = (
                f"{item} cannot unlock the vault."
            )

            if self.game:

                self.game.security.increase(20)
                self.game.score.penalize(10)

            self.concept_title = (
                "DICTIONARY - KEY VALUE"
            )

            self.concept_text = (
                "The vault checks its required_item "
                "value before unlocking."
            )

            self.concept_code = (
                'vault_data["required_item"] '
                '-> "Memory Chip"'
            )

    # =========================================================
    # COMPLETION
    # =========================================================

    def is_complete(self):
        """Return True when the level is complete."""

        return self.complete