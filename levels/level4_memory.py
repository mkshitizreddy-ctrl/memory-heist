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
        self.vault_data = {
            "required_item": "Vault Key",
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
        self.gates = [
            {
                "name": "Memory Access",
                "rect": pygame.Rect(280, 120, 125, 48),
                "unlocked": False,
                "question": "What does access[1] return?",
                "options": ["ID01", "ID02", "ID03", "Error"],
                "answer": 1,
                "topic": "LIST INDEXING"
            },
            {
                "name": "Credential Storage",
                "rect": pygame.Rect(485, 120, 145, 48),
                "unlocked": False,
                "question": "How do you access the value of key 'access'?",
                "options": [
                    "data.access",
                    "data['access']",
                    "data[access()]",
                    "data(0)"
                ],
                "answer": 1,
                "topic": "DICTIONARIES"
            },
            {
                "name": "Security Override",
                "rect": pygame.Rect(700, 120, 145, 48),
                "unlocked": False,
                "question": "What does inventory.append('Key') do?",
                "options": [
                    "Removes Key",
                    "Sorts inventory",
                    "Adds Key to the list",
                    "Clears inventory"
                ],
                "answer": 2,
                "topic": "LIST OPERATIONS"
            }
        ]

        self.active_gate = None
        self.hacking_active = False
        self.gate_feedback = ""

        # -------------------------
        # Companion recon drone
        # -------------------------
        start_x, start_y = (self.player.rect.center if self.player else (110, 130))
        self.drone_x = float(start_x - 34)
        self.drone_y = float(start_y - 38)
        self.drone_scan_message = "Drone ready. Press Q to scan."

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

        # Companion drone distraction: short effect with a cooldown.
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
        """Temporary movement test."""
        return []

    # =========================================================
    # UPDATE
    # =========================================================

    def update(self, dt):
        """Update the Memory Vault level."""
        if self.complete:
            return

        # Smoothly follow the player from a short distance behind.
        if self.player:
            target_x = self.player.rect.centerx - 34
            target_y = self.player.rect.centery - 38
            follow_speed = min(1.0, max(0.0, dt * 5.0))
            self.drone_x += (target_x - self.drone_x) * follow_speed
            self.drone_y += (target_y - self.drone_y) * follow_speed

        safe_dt = max(0.0, dt)
        self.drone_distraction_cooldown = max(
            0.0, self.drone_distraction_cooldown - safe_dt
        )
        self.drone_distraction_timer = max(
            0.0, self.drone_distraction_timer - safe_dt
        )
        self.security_drone_distracted = self.drone_distraction_timer > 0.0

        # Patrol pauses briefly while the enemy is distracted.
        if not self.security_drone_distracted:
            self.security_drone_x += (
                self.security_drone_direction * self.security_drone_speed * safe_dt
            )
            if self.security_drone_x >= self.security_drone_max_x:
                self.security_drone_x = self.security_drone_max_x
                self.security_drone_direction = -1
            elif self.security_drone_x <= self.security_drone_min_x:
                self.security_drone_x = self.security_drone_min_x
                self.security_drone_direction = 1

        # Detection and security gain are paused during the distraction window.
        self.security_alert_cooldown = max(
            0.0, self.security_alert_cooldown - safe_dt
        )
        self.security_drone_detecting = False
        if self.player and not self.security_drone_distracted:
            player_center = pygame.Vector2(self.player.rect.center)
            enemy_center = pygame.Vector2(
                self.security_drone_x, self.security_drone_y
            )
            distance = player_center.distance_to(enemy_center)
            self.security_drone_detecting = distance <= self.security_drone_detection_range

            if self.security_drone_detecting and self.security_alert_cooldown <= 0.0:
                if self.game:
                    self.game.security.increase(8)
                self.feedback = "Security drone detected you! Move away."
                self.security_alert_cooldown = 1.8

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
        

        # The shared game HUD already draws the level title and objective.
        # Avoid drawing a second title here, which previously overlapped the HUD.

        # =====================================================
        # GAME ROOM
        # =====================================================

        room_rect = self.room_bounds
        pygame.draw.rect(surface, (25, 30, 43), room_rect)
        pygame.draw.rect(surface, (80, 90, 115), room_rect, 2)

        room_text = small_font.render(
            "MEMORY VAULT STORAGE AREA",
            True,
            (120, 130, 150)
        )
        surface.blit(room_text, (65, 95))

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

            pygame.draw.rect(surface, (30, 42, 58), gate_rect)
            pygame.draw.rect(surface, gate_color, gate_rect, 2)

            gate_name = small_font.render(
                gate["name"], True, (235, 235, 240)
            )
            surface.blit(gate_name, (gate_rect.x + 5, gate_rect.y + 5))

            gate_status = small_font.render(
                gate_label, True, gate_color
            )
            surface.blit(gate_status, (gate_rect.x + 5, gate_rect.y + 27))

            if self.player and not gate["unlocked"]:
                if self.player.rect.inflate(70, 70).colliderect(gate_rect):
                    prompt = small_font.render(
                        "Press E to hack", True, (90, 230, 150)
                    )
                    surface.blit(prompt, (gate_rect.x, gate_rect.y - 18))

        gate_count = sum(1 for gate in self.gates if gate["unlocked"])
        gate_progress = small_font.render(
            f"Security Gates: {gate_count}/3 unlocked",
            True, (160, 210, 255)
        )
        surface.blit(gate_progress, (650, 95))

        # Hacking question overlay
        if self.hacking_active and self.active_gate is not None:
            panel = pygame.Rect(160, 175, 640, 190)
            pygame.draw.rect(surface, (18, 24, 38), panel)
            pygame.draw.rect(surface, (100, 170, 255), panel, 3)

            gate = self.gates[self.active_gate]
            question = heading_font.render(
                gate["question"], True, (245, 245, 250)
            )
            surface.blit(question, (panel.x + 20, panel.y + 18))

            for option_index, option in enumerate(gate["options"]):
                option_text = text_font.render(
                    f"{option_index + 1}. {option}",
                    True, (210, 220, 235)
                )
                surface.blit(
                    option_text,
                    (panel.x + 25, panel.y + 55 + option_index * 27)
                )

            hint = small_font.render(
                "Press 1-4 to answer | ESC to close",
                True, (100, 220, 170)
            )
            surface.blit(hint, (panel.x + 20, panel.bottom - 25))

        # =====================================================
        # COMPANION RECON DRONE
        # =====================================================

        drone_center = (int(self.drone_x), int(self.drone_y))
        pygame.draw.line(
            surface, (55, 170, 205),
            (drone_center[0] - 10, drone_center[1]),
            (drone_center[0] + 10, drone_center[1]), 3
        )
        pygame.draw.circle(surface, (35, 205, 245), drone_center, 10)
        pygame.draw.circle(surface, (190, 245, 255), drone_center, 4)
        pygame.draw.circle(surface, (70, 190, 220),
                           (drone_center[0] - 13, drone_center[1] - 5), 3)
        pygame.draw.circle(surface, (70, 190, 220),
                           (drone_center[0] + 13, drone_center[1] - 5), 3)

        drone_hint = small_font.render(
            "ALLY DRONE | Q: Scan | X: Distract",
            True, (90, 220, 245)
        )
        surface.blit(drone_hint, (room_rect.x + 12, room_rect.bottom - 24))

        if self.drone_distraction_timer > 0:
            drone_status_text = (
                f"Enemy distracted: {self.drone_distraction_timer:.1f}s"
            )
        elif self.drone_distraction_cooldown > 0:
            drone_status_text = (
                f"Distraction recharging: {self.drone_distraction_cooldown:.1f}s"
            )
        else:
            drone_status_text = "Distraction ready (X)"
        drone_status = small_font.render(
            drone_status_text, True, (110, 205, 255)
        )
        surface.blit(drone_status, (room_rect.x + 12, room_rect.bottom - 43))

        # Enemy security drone: orange body, red sensor eye.
        enemy_center = (int(self.security_drone_x), int(self.security_drone_y))
        if self.security_drone_distracted:
            enemy_color = (100, 190, 255)
        else:
            enemy_color = (
                (255, 85, 75)
                if self.security_drone_detecting
                else (230, 145, 65)
            )
        pygame.draw.line(
            surface, enemy_color,
            (enemy_center[0] - 13, enemy_center[1]),
            (enemy_center[0] + 13, enemy_center[1]), 4
        )
        pygame.draw.circle(surface, enemy_color, enemy_center, 11)
        pygame.draw.circle(surface, (255, 230, 190), enemy_center, 4)
        enemy_label = small_font.render(
            (
                "DISTRACTED"
                if self.security_drone_distracted
                else ("ALERT!" if self.security_drone_detecting else "SECURITY DRONE")
            ),
            True, enemy_color
        )
        surface.blit(enemy_label, (enemy_center[0] - 48, enemy_center[1] - 25))
        if self.security_drone_detecting and not self.security_drone_distracted:
            pygame.draw.line(
                surface, (220, 75, 75),
                enemy_center, self.player.rect.center, 2
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
            item_rect = pygame.Rect(position[0], position[1], 120, 55)

            pygame.draw.rect(surface, (35, 40, 55), item_rect)
            pygame.draw.rect(surface, item_colors[item], item_rect, 2)

            item_text = small_font.render(item, True, (235, 235, 240))
            item_text_rect = item_text.get_rect(center=item_rect.center)
            surface.blit(item_text, item_text_rect)

            # Interaction prompt
            if self.player:
                interaction_rect = self.player.rect.inflate(70, 70)
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
                    surface.blit(prompt, prompt_rect)

        # Drone scan result appears in the concept/feedback area below.

        # =====================================================
        # VAULT
        # =====================================================

        if self.complete:
            vault_color = (60, 220, 100)
            vault_label = "UNLOCKED"
        else:
            vault_color = (210, 130, 70)
            vault_label = "LOCKED"

        pygame.draw.rect(surface, (40, 30, 42), self.vault_rect)
        pygame.draw.rect(surface, vault_color, self.vault_rect, 3)

        vault_text = heading_font.render("VAULT", True, vault_color)
        vault_text_rect = vault_text.get_rect(
            center=(self.vault_rect.centerx, self.vault_rect.centery - 10)
        )
        surface.blit(vault_text, vault_text_rect)

        status_text = small_font.render(vault_label, True, (220, 220, 225))
        status_rect = status_text.get_rect(
            center=(self.vault_rect.centerx, self.vault_rect.centery + 18)
        )
        surface.blit(status_text, status_rect)

        # Vault interaction prompt
        if self.player and not self.complete:
            interaction_rect = self.player.rect.inflate(70, 70)
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
                surface.blit(prompt, prompt_rect)

        # =====================================================
        # INVENTORY
        # =====================================================

        inventory_rect = pygame.Rect(45, 395, 270, 195)
        pygame.draw.rect(surface, (29, 34, 48), inventory_rect)
        pygame.draw.rect(surface, (100, 80, 150), inventory_rect, 2)

        inventory_title = heading_font.render(
            "PLAYER INVENTORY",
            True,
            (190, 140, 255)
        )
        surface.blit(inventory_title, (65, 415))

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
                surface.blit(item_text, (65, y))
                y += 28
        else:
            empty_text = small_font.render(
                "Inventory empty.",
                True,
                (150, 155, 165)
            )
            surface.blit(empty_text, (65, 450))

        count_text = small_font.render(
            f"Items: {len(self.inventory.items)} / "
            f"{self.inventory.capacity}",
            True,
            (170, 175, 185)
        )
        surface.blit(count_text, (65, 555))

        # =====================================================
        # PYTHON CONCEPT
        # =====================================================

        concept_rect = pygame.Rect(335, 395, 580, 195)
        pygame.draw.rect(surface, (24, 31, 42), concept_rect)
        pygame.draw.rect(surface, (60, 150, 120), concept_rect, 2)

        concept_heading = heading_font.render(
            "PYTHON CONCEPT",
            True,
            (80, 220, 150)
        )
        surface.blit(concept_heading, (355, 415))

        concept_title = text_font.render(
            self.concept_title,
            True,
            (240, 240, 240)
        )
        surface.blit(concept_title, (355, 447))

        concept_text = small_font.render(
            self.concept_text,
            True,
            (190, 195, 205)
        )
        surface.blit(concept_text, (355, 475))

        concept_code = small_font.render(
            self.concept_code,
            True,
            (100, 210, 255)
        )
        surface.blit(concept_code, (355, 505))

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
            surface.blit(feedback, (355, 540))

        # =====================================================
        # CONTROLS
        # =====================================================

        controls = small_font.render(
            "WASD Move | E Interact | Q Scan | X Distract | 1-3 Select | ENTER Use",
            True,
            (175, 180, 190)
        )
        controls_rect = controls.get_rect(center=(625, 565))
        surface.blit(controls, controls_rect)

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
        # Answer an active hacking question
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
                self.answer_gate(answer_keys[event.key])
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
        """Hack nearby terminals, collect items, or interact with the vault."""
        interaction_rect = player.rect.inflate(70, 70)

        # Check hacking terminals first
        for index, gate in enumerate(self.gates):
            if not gate["unlocked"] and interaction_rect.colliderect(gate["rect"]):
                self.active_gate = index
                self.hacking_active = True
                self.feedback = f"Hacking: {gate['name']}"
                self.concept_title = gate["topic"]
                self.concept_text = "Answer the Python question to unlock this terminal."
                self.concept_code = "Choose the correct option (1-4)."
                return

        # Check items
        for item in self.available_items:
            if item in self.collected:
                continue

            position = self.item_data[item]["position"]
            item_rect = pygame.Rect(position[0], position[1], 120, 55)

            if interaction_rect.colliderect(item_rect):
                self.collect_item(item)
                return

        # Check vault
        if interaction_rect.colliderect(self.vault_rect):
            if not all(gate["unlocked"] for gate in self.gates):
                self.feedback = "Unlock all 3 security gates first."
                self.concept_title = "SECURITY GATES"
                self.concept_text = "The vault remains protected until every terminal is unlocked."
                self.concept_code = "all(gate['unlocked'] for gate in gates)"
                return

            if self.selected_index is not None:
                self.use_selected_item()
            else:
                self.feedback = "Select an inventory item first."
                self.concept_title = "INDEXING"
                self.concept_text = "Select an item by its position in the list."
                self.concept_code = "inventory[index]"

    # =========================================================
    # DRONE DISTRACTION
    # =========================================================

    def activate_drone_distraction(self):
        """Temporarily distract the security drone, subject to cooldown."""
        if self.drone_distraction_timer > 0:
            self.feedback = (
                f"Security drone is already distracted "
                f"({self.drone_distraction_timer:.1f}s left)."
            )
            return

        if self.drone_distraction_cooldown > 0:
            self.feedback = (
                f"Drone distraction recharging: "
                f"{self.drone_distraction_cooldown:.1f}s."
            )
            return

        self.drone_distraction_timer = self.drone_distraction_duration
        self.drone_distraction_cooldown = self.drone_distraction_cooldown_max
        self.security_drone_detecting = False
        self.feedback = "Security drone distracted! Move quickly."
        self.concept_title = "DRONE DISTRACTION"
        self.concept_text = "The enemy sensor is temporarily occupied."
        self.concept_code = "distraction_timer = 4 seconds"

    # =========================================================
    # DRONE SCAN
    # =========================================================

    def scan_with_drone(self):
        """Report the nearest uncollected item or locked terminal."""
        if not self.player:
            self.feedback = "Drone cannot locate the player."
            return

        player_center = pygame.Vector2(self.player.rect.center)
        targets = []

        for item in self.available_items:
            if item in self.collected:
                continue
            x, y = self.item_data[item]["position"]
            target_center = pygame.Vector2(x + 60, y + 27)
            targets.append((player_center.distance_to(target_center), item))

        for gate in self.gates:
            if gate["unlocked"]:
                continue
            targets.append((
                player_center.distance_to(pygame.Vector2(gate["rect"].center)),
                gate["name"] + " terminal"
            ))

        if not targets:
            self.drone_scan_message = "Scan complete: no remaining targets."
        else:
            distance, target_name = min(targets, key=lambda target: target[0])
            self.drone_scan_message = (
                f"Scan: {target_name} is the nearest target ({int(distance)} units)."
            )

        self.feedback = self.drone_scan_message
        self.concept_title = "DRONE RECON"
        self.concept_text = self.drone_scan_message
        self.concept_code = "nearest_target = min(targets)"

    # =========================================================
    # HACKING GATES
    # =========================================================

    def answer_gate(self, chosen_answer):
        """Check the selected answer for the active terminal."""
        if self.active_gate is None:
            return

        gate = self.gates[self.active_gate]

        if chosen_answer == gate["answer"]:
            gate["unlocked"] = True
            self.feedback = f"{gate['name']} unlocked!"
            self.gate_feedback = self.feedback
            self.concept_title = gate["topic"]
            self.concept_text = "Correct answer. This security terminal is now open."
            self.concept_code = "gate['unlocked'] = True"

            if self.game:
                self.game.score.add(40)
        else:
            self.feedback = "Incorrect answer. Security alert increased."
            self.concept_title = gate["topic"]
            self.concept_text = "Review the Python concept and try another terminal."
            self.concept_code = "Try again: choose option 1-4."

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
            self.feedback = f"{item} added to inventory."

            if self.game:
                self.game.score.add(30)   # points for collecting an item

            self.concept_title = "LISTS - ADDING ELEMENTS"
            self.concept_text = "append() adds an item to a Python list."
            self.concept_code = f'inventory.append("{item}")'
        else:
            self.feedback = "Inventory is full."

    # =========================================================
    # SELECT ITEM
    # =========================================================

    def select_item(self, index):
        """Select an inventory item using its index."""
        if index >= len(self.inventory.items):
            self.feedback = "That inventory slot is empty."
            self.concept_title = "INDEXING"
            self.concept_text = "An index must point to an existing item."
            self.concept_code = "inventory[index]"
            return

        self.selected_index = index
        item = self.inventory.items[index]
        self.feedback = f"Selected: {item}"
        self.concept_title = "INDEXING"
        self.concept_text = "Indexing accesses an item by its position."
        self.concept_code = f"inventory[{index}] -> {item}"

    # =========================================================
    # USE ITEM
    # =========================================================

    def use_selected_item(self):
        """Use the selected item on the vault."""
        if self.selected_index is None:
            self.feedback = "Select an inventory item first."
            return

        if self.selected_index >= len(self.inventory.items):
            self.selected_index = None
            return

        # List indexing
        item = self.inventory.items[self.selected_index]

        # Dictionary key-value pair
        required_item = self.vault_data["required_item"]

        # Check selected item
        if not all(gate["unlocked"] for gate in self.gates):
            self.feedback = "Unlock all 3 security gates before using the Vault Key."
            return

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

            if self.game:
                self.game.score.add(50)
                self.game.score.add(100)   # level completion bonus

            self.concept_title = "DICTIONARIES + REMOVE"
            self.concept_text = (
                "Key-value pairs store vault data. "
                "The used item was removed."
            )
            self.concept_code = 'vault_data["required_item"] -> "Vault Key"'
        else:
            self.feedback = f"{item} cannot unlock the vault."

            if self.game:
                self.game.security.increase(20)
                self.game.score.penalize(10)

            self.concept_title = "DICTIONARY - KEY VALUE"
            self.concept_text = "The vault checks its required_item value."
            self.concept_code = 'vault_data["required_item"]'

    # =========================================================
    # COMPLETION
    # =========================================================

    def is_complete(self):
        """Return True when the level is complete."""
        return self.complete
