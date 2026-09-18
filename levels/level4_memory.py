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

from systems.inventory import Inventory


class Level4MemoryVault:
    """Controls the Memory Vault level."""

    def __init__(self, player=None):

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
                "position": (180, 230)
            },
            "Access Card": {
                "position": (430, 320)
            },
            "Vault Key": {
                "position": (650, 210)
            }
        }

        # -------------------------
        # Vault dictionary
        # -------------------------
        self.vault_data = {
            "required_item": "Vault Key",
            "vault_code": "42",
            "status": "LOCKED"
        }

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

    def get_obstacles(self):
        """Return objects that block player movement."""

        return [self.vault_rect]

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, dt):
        """Update the Memory Vault level."""

        if self.complete:
            return

    # =========================================================
    # RENDER
    # =========================================================

    def render(self, surface):
        """Draw the Memory Vault room and interface."""

        # -------------------------
        # Fonts
        # -------------------------
        title_font = pygame.font.Font(None, 34)
        heading_font = pygame.font.Font(None, 25)
        text_font = pygame.font.Font(None, 21)
        small_font = pygame.font.Font(None, 18)

        # -------------------------
        # Background
        # -------------------------
        surface.fill((15, 18, 30))

        # =====================================================
        # TITLE
        # =====================================================

        title = title_font.render(
            "LEVEL 4 - THE MEMORY VAULT",
            True,
            (255, 255, 255)
        )

        surface.blit(title, (45, 18))

        objective = small_font.render(
            "Explore the vault, collect memory items, and unlock the door.",
            True,
            (190, 195, 205)
        )

        surface.blit(objective, (45, 52))

        # =====================================================
        # GAME ROOM
        # =====================================================

        room_rect = pygame.Rect(
            45,
            80,
            870,
            300
        )

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

                interaction_rect = self.player.rect.inflate(
                    70,
                    70
                )

                if interaction_rect.colliderect(item_rect):

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

        # Vault interaction prompt
        if self.player and not self.complete:

            interaction_rect = self.player.rect.inflate(
                70,
                70
            )

            if interaction_rect.colliderect(self.vault_rect):

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

            for index, item in enumerate(self.inventory.items):

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

        count_text = small_font.render(
            f"Items: {len(self.inventory.items)} / "
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
            "WASD: Move   E: Interact   1/2/3: Select   ENTER: Use",
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
        # World interaction
        # -------------------------

        if event.key == pygame.K_e:

            if self.player:
                self.interact(self.player)

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
        """Collect nearby items or interact with the vault."""

        interaction_rect = player.rect.inflate(
            70,
            70
        )

        # Check items
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

            if interaction_rect.colliderect(item_rect):

                self.collect_item(item)
                return

        # Check vault
        if interaction_rect.colliderect(self.vault_rect):

            if self.selected_index is not None:

                self.use_selected_item()

            else:

                self.feedback = (
                    "Select an inventory item first."
                )

                self.concept_title = "INDEXING"

                self.concept_text = (
                    "Select an item by its position in the list."
                )

                self.concept_code = (
                    "inventory[index]"
                )

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

            self.feedback = "Inventory is full."

    # =========================================================
    # SELECT ITEM
    # =========================================================

    def select_item(self, index):
        """Select an inventory item using its index."""

        if index >= len(self.inventory.items):

            self.feedback = (
                "That inventory slot is empty."
            )

            self.concept_title = "INDEXING"

            self.concept_text = (
                "An index must point to an existing item."
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

        self.concept_title = "INDEXING"

        self.concept_text = (
            "Indexing accesses an item by its position."
        )

        self.concept_code = (
            f"inventory[{index}] -> {item}"
        )

    # =========================================================
    # USE ITEM
    # =========================================================

    def use_selected_item(self):
        """Use the selected item on the vault."""

        if self.selected_index is None:

            self.feedback = (
                "Select an inventory item first."
            )

            return

        if self.selected_index >= len(self.inventory.items):

            self.selected_index = None
            return

        # List indexing
        item = self.inventory.items[self.selected_index]

        # Dictionary key-value pair
        required_item = self.vault_data["required_item"]

        # Check selected item
        if item == required_item:

            # Remove used item
            self.inventory.remove_item(item)

            # Update dictionary value
            self.vault_data["status"] = "UNLOCKED"

            self.complete = True
            self.selected_index = None

            self.feedback = (
                "Correct! Vault Key used. "
                "Memory Vault unlocked!"
            )

            self.concept_title = (
                "DICTIONARIES + REMOVE"
            )

            self.concept_text = (
                "Key-value pairs store vault data. "
                "The used item was removed."
            )

            self.concept_code = (
                'vault_data["required_item"] -> "Vault Key"'
            )

        else:

            self.feedback = (
                f"{item} cannot unlock the vault."
            )

            self.concept_title = (
                "DICTIONARY - KEY VALUE"
            )

            self.concept_text = (
                "The vault checks its required_item value."
            )

            self.concept_code = (
                'vault_data["required_item"]'
            )

    # =========================================================
    # COMPLETION
    # =========================================================

    def is_complete(self):
        """Return True when the level is complete."""

        return self.complete