
import pytest

from core.level_manager import LevelManager, LEVEL_ORDER


class FakeLevel:
    def __init__(self, complete=False):
        self.complete = complete
        self.update_calls = []
        self.render_calls = []
        self.event_calls = []

    def update(self, dt):
        self.update_calls.append(dt)

    def render(self, surface):
        self.render_calls.append(surface)

    def handle_event(self, event):
        self.event_calls.append(event)

    def is_complete(self):
        return self.complete


class FakeGame:
    def __init__(self):
        self.state_changes = []

    def change_state(self, state):
        self.state_changes.append(state)


def make_manager():
    game = FakeGame()
    manager = LevelManager(game)

    for name in LEVEL_ORDER:
        manager.register(name, FakeLevel())

    return game, manager


def test_start_registered_level():
    _, manager = make_manager()

    manager.start("level1")

    assert manager.current_name == "level1"
    assert manager.current is manager.levels["level1"]


def test_start_unknown_level_raises_value_error():
    _, manager = make_manager()

    with pytest.raises(ValueError, match="Cannot start unknown level"):
        manager.start("unknown_level")


def test_update_forwards_delta_time_to_current_level():
    _, manager = make_manager()
    manager.start("level1")

    manager.update(0.25)

    assert manager.current.update_calls == [0.25]


def test_handle_event_forwards_to_current_level():
    _, manager = make_manager()
    manager.start("level1")
    event = object()

    manager.handle_event(event)

    assert manager.current.event_calls == [event]


def test_render_forwards_surface_to_current_level():
    _, manager = make_manager()
    manager.start("level1")
    surface = object()

    manager.render(surface)

    assert manager.current.render_calls == [surface]


def test_completed_level_advances_to_next_level():
    _, manager = make_manager()
    manager.start("level1")
    manager.current.complete = True

    manager.update(0.1)

    assert manager.current_name == "level2"


def test_final_level_completion_triggers_win_state():
    game, manager = make_manager()
    manager.start("final_vault")
    manager.current.complete = True

    manager.update(0.1)

    assert game.state_changes == ["win"]


def test_update_does_nothing_when_no_level_is_active():
    _, manager = make_manager()

    manager.update(0.1)

    assert manager.current is None
    assert manager.current_name is None


def test_level_order_contains_all_six_levels():
    assert len(LEVEL_ORDER) == 6
    assert LEVEL_ORDER == [
        "level1",
        "level2",
        "level3",
        "level4",
        "level5",
        "final_vault",
    ]
