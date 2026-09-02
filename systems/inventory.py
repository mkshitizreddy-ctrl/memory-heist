"""
systems/inventory.py
Owner: Member 3 (used mainly by Level 4, but shared)

Player inventory backed by a list. Demonstrates append/remove/index
concepts directly through gameplay.
"""


class Inventory:
    def __init__(self, capacity=8):
        self.items = []
        self.capacity = capacity

    def add_item(self, item):
        if len(self.items) >= self.capacity:
            return False
        self.items.append(item)
        return True

    def remove_item(self, item):
        if item in self.items:
            self.items.remove(item)
            return True
        return False

    def has_item(self, item):
        return item in self.items
