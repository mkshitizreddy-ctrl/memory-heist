"""Room 3 visual polish (drawing only). Rooms 1 and 2 must be untouched."""

import importlib.util
import os
import random
from pathlib import Path
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.difficulty import get_difficulty
from levels.level3_loops import Level3LaserLoop
from systems.scoring import ScoreTracker

ROOT = Path(__file__).resolve().parent.parent
BASELINE = ROOT / "backups" / "level3_loops.before-claude-visuals.py"


def make_level(room, cls=Level3LaserLoop):
    pygame.font.init()
    random.seed(1234)
    game = SimpleNamespace(
        difficulty=get_difficulty("medium"),
        score=ScoreTracker(),
        security=SimpleNamespace(increase=lambda amount: None),
    )
    level = cls(game=game)
    level.current_checkpoint = room
    level.current_question_number = room - 1
    level.setup_room_hazards()
    level.load_current_question()
    return level


def shot(level):
    surface = pygame.Surface((960, 640))
    level.render(surface)
    return surface


def test_phase_colours_follow_rules():
    level = make_level(3)
    assert level._r3_phase_colour("warning") == level.R3_YELLOW
    assert level._r3_phase_colour("active") == level.R3_RED
    assert level._r3_phase_colour("off") == level.R3_CYAN


@pytest.mark.parametrize("state", ["closed", "opening", "tracking", "warning",
                                   "locking", "active", "retracting", "cooldown"])
def test_every_emitter_state_renders(state):
    level = make_level(3)
    emitter = level.emitters[0]
    emitter["state"] = state
    emitter["timer"] = 0.1
    emitter["target"] = (650, 330)
    shot(level)


def test_rendering_never_changes_hazard_state():
    a, b = make_level(3), make_level(3)
    for _ in range(600):
        a.update(1 / 60)
        b.update(1 / 60)
        shot(a)
    assert [a.laser_phase(i) for i in range(len(a.lasers))] == \
           [b.laser_phase(i) for i in range(len(b.lasers))]
    assert [e["state"] for e in a.emitters] == [e["state"] for e in b.emitters]
    assert a.time_left == pytest.approx(b.time_left)


def test_gate3_vault_states_render():
    level = make_level(3)
    rect = tuple(level.gate3.rect)
    shot(level)
    level.gate1.state = level.gate2.state = "open"
    level.unlock_current_gate()
    for _ in range(20):
        level._update_visual_effects(1 / 60)
        level.gate3.update(1 / 60)
        shot(level)
    for _ in range(300):
        level._update_visual_effects(1 / 60)
        level.gate3.update(1 / 60)
    assert level.gate3.is_open()
    shot(level)
    assert tuple(level.gate3.rect) == rect


@pytest.mark.skipif(not BASELINE.exists(), reason="baseline backup not present")
@pytest.mark.parametrize("room", [1, 2])
def test_rooms_1_and_2_render_pixel_identical(room):
    """Rooms 1 and 2 keep the pre-polish look.

    Room 2 now also draws the team's camera bank (a deliberate integration
    addition), so there the comparison is made with that one layer removed;
    test_room_2_camera_layer_is_the_only_difference proves the layer is real.
    """
    spec = importlib.util.spec_from_file_location("l3_baseline", BASELINE)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    images = []
    for cls in (base.Level3LaserLoop, Level3LaserLoop):
        level = make_level(room, cls)
        if cls is Level3LaserLoop:
            level.camera_bank = None          # Room 2's cameras are added art
        for _ in range(90):
            level.update(1 / 60)
        images.append(pygame.image.tostring(shot(level), "RGB"))
    assert images[0] == images[1]


@pytest.mark.skipif(not BASELINE.exists(), reason="baseline backup not present")
def test_room_2_camera_layer_is_the_only_difference():
    spec = importlib.util.spec_from_file_location("l3_baseline", BASELINE)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    old = make_level(2, base.Level3LaserLoop)
    new = make_level(2)
    assert new.camera_bank is not None
    for level in (old, new):
        for _ in range(90):
            level.update(1 / 60)
    assert pygame.image.tostring(shot(old), "RGB") != pygame.image.tostring(shot(new), "RGB")
    new.camera_bank = None
    assert pygame.image.tostring(shot(old), "RGB") == pygame.image.tostring(shot(new), "RGB")
