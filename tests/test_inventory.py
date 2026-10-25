
from systems.inventory import Inventory


def test_inventory_starts_empty():
    inventory = Inventory()

    assert inventory.items == []


def test_add_item():
    inventory = Inventory()

    result = inventory.add_item("key")

    assert result is True
    assert inventory.has_item("key") is True


def test_inventory_respects_capacity():
    inventory = Inventory(capacity=2)

    assert inventory.add_item("key") is True
    assert inventory.add_item("card") is True
    assert inventory.add_item("map") is False

    assert inventory.items == ["key", "card"]


def test_remove_existing_item():
    inventory = Inventory()
    inventory.add_item("key")

    result = inventory.remove_item("key")

    assert result is True
    assert inventory.has_item("key") is False


def test_remove_missing_item():
    inventory = Inventory()

    result = inventory.remove_item("key")

    assert result is False
    assert inventory.items == []


def test_inventory_can_hold_duplicate_items():
    inventory = Inventory()

    assert inventory.add_item("key") is True
    assert inventory.add_item("key") is True

    assert inventory.items == ["key", "key"]


def test_remove_item_removes_only_one_duplicate():
    inventory = Inventory()
    inventory.add_item("key")
    inventory.add_item("key")

    inventory.remove_item("key")

    assert inventory.items == ["key"]
