"""
tests/test_level3_visuals.py

Phase 1 presentation guards for Level 3: the question panel always fits
under the lowest rail with its footer above y=585, answer text is never
truncated, the gate animation is driven by render-side time only, and
rendering never changes gameplay state.
"""

import json
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

PUZZLES = json.loads(
    (Path(__file__).resolve().parent.parent / "data" / "puzzles.json")
    .read_text(encoding="utf-8")
)
QUESTIONS = {
    key: value
    for key, value in PUZZLES.items()
    if key.startswith("level3_loop_")
}


def make_level(room, question_id, difficulty="medium"):
    pygame.font.init()
    random.seed(1)

    game = SimpleNamespace(
        difficulty=get_difficulty(difficulty),
        score=ScoreTracker(),
        security=SimpleNamespace(increase=lambda amount: None),
    )

    level = Level3LaserLoop(game=game)
    level.room_map.current_name = f"level3_room{room}"
    level.current_question_number = room - 1
    level.setup_room_hazards()
    level.selected_questions[room - 1] = QUESTIONS[question_id]
    level.load_current_question()

    return level


@pytest.mark.parametrize("question_id", sorted(QUESTIONS))
def test_question_panel_fits_and_footer_is_above_585(question_id):
    question = QUESTIONS[question_id]
    level = make_level(question["room"], question_id)

    layout = level._bottom_layout()
    panel = layout["panel"]

    assert panel.bottom == level.PANEL_BOTTOM
    assert panel.height <= layout["available"]
    assert panel.top >= level._lowest_rail_bottom() + 6

    footer = layout["foot_font"].render("Progress: 0/3 gates/challenges", True, (255, 255, 255))
    footer_bottom = layout["foot_y"] + footer.get_bounding_rect().bottom

    assert footer_bottom <= 585

    for button in layout["buttons"]:
        assert panel.contains(button)

    for first, second in zip(layout["buttons"], layout["buttons"][1:]):
        assert not first.colliderect(second)


@pytest.mark.parametrize("question_id", sorted(QUESTIONS))
def test_answer_text_is_reconstructed_exactly_from_button_lines(question_id):
    question = QUESTIONS[question_id]
    level = make_level(question["room"], question_id)
    lines = level._bottom_layout()["button_lines"]

    assert len(lines) == len(level.options)

    for option, button_lines in zip(level.options, lines):
        assert option == " ".join(option.split())       # no hidden double spaces
        assert " ".join(button_lines) == option          # nothing lost, nothing added
        assert "..." not in " ".join(button_lines) or "..." in option


def test_gate_progress_is_render_side_and_eased(monkeypatch):
    level = make_level(1, "level3_loop_1")
    clock = {"t": 100.0}
    monkeypatch.setattr(level, "_seconds", lambda: clock["t"])

    assert level._gate_progress(level.gate1) == 0.0

    level.gate1.unlock()
    assert level._gate_progress(level.gate1) == 0.0     # animation just started

    clock["t"] += 0.3
    middle = level._gate_progress(level.gate1)
    clock["t"] += 1.0
    finished = level._gate_progress(level.gate1)

    assert 0.0 < middle < 1.0
    assert finished == 1.0
    assert level.gate1.state == "unlocking"              # gameplay state untouched


def test_render_does_not_change_gameplay_state():
    level = make_level(2, "level3_loop_7", "hard")
    surface = pygame.Surface((960, 640))

    def snapshot():
        return (
            level.feedback,
            level.time_left,
            level.robot_x,
            level.robot_alert,
            [laser["x"] for laser in level.lasers],
            level.gate2.state,
            level.game.score.get_score(),
        )

    before = snapshot()

    for _ in range(3):
        level.render(surface)

    assert snapshot() == before


@pytest.mark.parametrize("room", (1, 2, 3))
def test_laser_labels_stay_out_of_the_robot_band(room):
    question_id = next(
        key for key, value in QUESTIONS.items() if value["room"] == room
    )
    level = make_level(room, question_id)

    band = pygame.Rect(90, 154, 800, 62)

    for rect in level._laser_label_rects():
        assert not rect.colliderect(band)


def test_gate_sparks_do_not_touch_private_gate_state_or_global_random():
    source = (
        Path(__file__).resolve().parent.parent / "levels" / "level3_loops.py"
    ).read_text(encoding="utf-8")

    assert "_particles" not in source

    level = make_level(1, "level3_loop_1")
    surface = pygame.Surface((960, 640))
    level.render(surface)
    level.gate1.unlock()
    state = random.getstate()

    for _ in range(4):
        level.render(surface)

    assert random.getstate() == state
    assert level._vis_state()["sparks"]


@pytest.mark.parametrize("room", (1, 2, 3))
def test_drawn_beam_matches_collision_box(room):
    question_id = next(
        key for key, value in QUESTIONS.items() if value["room"] == room
    )
    level = make_level(room, question_id)
    level.robot_x = 700
    level.laser_phase = lambda index: "active"      # beam drawn at full strength

    for index, laser in enumerate(level.lasers):
        laser["x"] = 200.0 + 111 * index

    surface = pygame.Surface((960, 640))
    surface.fill((0, 0, 0))
    level._draw_rails(surface)          # before the room lighting tints the beam

    for laser, collision in ((l, seg) for l in level.lasers for seg in level.beam_segments(l)):
        strip = pygame.Rect(
            collision.left, collision.top - 4, collision.width, collision.height + 8
        )
        red = [
            (x, y)
            for x in range(strip.left, strip.right, 5)
            for y in range(strip.top, strip.bottom)
            if tuple(surface.get_at((x, y)))[:3] == (255, 45, 45)
        ]

        assert red
        assert min(y for _, y in red) == collision.top
        assert max(y for _, y in red) == collision.bottom - 1

        # The rail is centred on the beam (8 px of housing each side).
        rail_top = laser["y"] - level.RAIL_TOP_PAD
        rail_bottom = rail_top + level.RAIL_HEIGHT

        assert collision.top - rail_top == rail_bottom - collision.bottom == 8


@pytest.mark.parametrize("room", (1, 2, 3))
def test_exit_marker_never_meets_the_robot_band(room):
    question_id = next(
        key for key, value in QUESTIONS.items() if value["room"] == room
    )
    level = make_level(room, question_id)
    gate = (level.gate1, level.gate2, level.gate3)[room - 1]
    marker = pygame.Rect(gate.rect.centerx - 11, 134, 60, 18)

    for x in range(level.robot_left_boundary, level.robot_right_boundary + 1, 5):
        robot = pygame.Rect(x, 154, level.robot_width, 62)   # antenna to wheels

        assert not marker.colliderect(robot)


# ---------------------------------------------------------------------------
# Final-review geometry checks
# ---------------------------------------------------------------------------

class _Spy(pygame.Surface):
    """Surface that records every blit so text positions can be checked."""

    log = []

    def blit(self, source, dest, *args, **kwargs):
        if not isinstance(dest, pygame.Rect):
            dest = pygame.Rect(dest, source.get_size())

        _Spy.log.append((dest.copy(), source))

        return super().blit(source, dest, *args, **kwargs)


def rendered_text_rects(level):
    """Ink rectangles of every text blit (text surfaces are <= 26 px high)."""

    _Spy.log = []
    level.render(_Spy((960, 640)))
    rects = []

    for box, source in _Spy.log:
        width, height = source.get_size()

        if not 6 < height <= 26 or width > 860:
            continue

        ink = source.get_bounding_rect()

        if ink.width:
            rects.append(ink.move(box.topleft))

    return rects


def rail_bodies(level):
    return [
        pygame.Rect(
            level.track_x,
            laser["y"] - level.RAIL_TOP_PAD,
            level.track_width,
            level.RAIL_HEIGHT,
        )
        for laser in level.lasers
    ]


def rail_emitters(level):
    return [
        pygame.Rect(x, laser["y"] - level.RAIL_TOP_PAD - 3, 22, level.RAIL_HEIGHT + 6)
        for laser in level.lasers
        for x in (level.track_x - 22, level.track_x + level.track_width)
    ]


@pytest.mark.parametrize("question_id", sorted(QUESTIONS))
def test_question_and_hint_never_extend_beyond_the_panel(question_id):
    question = QUESTIONS[question_id]
    level = make_level(question["room"], question_id)
    level.show_hint = True
    level.hint_used = True
    level.feedback = "Hint revealed. Final score for this question is reduced by 15."

    layout = level._bottom_layout()
    panel = layout["panel"]
    room_width = panel.width - 24

    assert layout["question_font"].size(question["question"])[0] <= room_width
    assert layout["hint_font"].size(f"HINT: {question['hint']}")[0] <= room_width
    assert layout["hint_y"] is not None

    for state in (
        "Hint revealed. Final score for this question is reduced by 15.",
        f"CORRECT! +60 points. GATE 3 UNLOCKED! REACH THE FINAL EXIT.  {question['explanation']}",
    ):
        level.feedback = state

        for ink in rendered_text_rects(level):
            if ink.top >= panel.top:
                assert panel.contains(ink), (question_id, ink, panel)


@pytest.mark.parametrize("room", (1, 2, 3))
@pytest.mark.parametrize("difficulty", ("easy", "medium", "hard"))
@pytest.mark.parametrize("alert", (False, True))
def test_header_notice_and_patrol_board_text_stay_inside_their_areas(room, difficulty, alert):
    from levels import patrol_decor as P

    question_id = next(k for k, v in QUESTIONS.items() if v["room"] == room)
    level = make_level(room, question_id, difficulty)
    level.robot_alert = alert
    level.time_left = 20.0

    texts = rendered_text_rects(level)
    header_texts = [t for t in texts if P.HEADER.top <= t.top < P.HEADER.bottom]
    board_texts = [t for t in texts if P.BOARD.collidepoint(t.topleft)]
    notice_texts = [t for t in texts if P.NOTICE.collidepoint(t.topleft)]

    assert len(header_texts) >= 3 and len(board_texts) >= 4

    if alert:
        # The banner text is drawn inside its own surface: it must fit the lane.
        lane = P.BANNER_LANE
        for banner in ("LASER HIT! SCORE -10", "!! SECURITY ALERT - ROBOT DETECTION !!"):
            font = level._font(level.BODY_SIZE)

            if font.size(banner)[0] > lane.width - 16:
                font = level._font(24)

            assert font.size(banner)[0] <= lane.width - 16
    else:
        assert notice_texts

    for area, items in ((P.HEADER, header_texts), (P.BOARD, board_texts), (P.NOTICE, notice_texts)):
        for ink in items:
            assert area.contains(ink), (area, ink)

    for first in range(len(header_texts)):
        for second in range(first + 1, len(header_texts)):
            assert not header_texts[first].colliderect(header_texts[second])


@pytest.mark.parametrize("room", (1, 2, 3))
def test_each_room_has_its_own_baked_look(room):
    from levels import patrol_decor as P

    level = make_level(room, next(k for k, v in QUESTIONS.items() if v["room"] == room))
    look = P.build_room(room, (level.room_width, level.room_height))
    others = [P.build_room(r, (level.room_width, level.room_height)) for r in (1, 2, 3) if r != room]
    wall = pygame.Rect(0, 40, 400, 80)

    mine = pygame.image.tostring(look.subsurface(wall), "RGB")
    for other in others:
        assert mine != pygame.image.tostring(other.subsurface(wall), "RGB")


def test_the_patrol_board_lights_its_if_line_only_while_a_beam_is_live():
    from levels import patrol_decor as P

    surface = pygame.Surface((960, 640))
    P.draw_board(surface, False, False, 0.0)
    quiet = pygame.image.tostring(surface.subsurface(P.BOARD), "RGB")
    surface.fill((0, 0, 0))
    P.draw_board(surface, True, False, 0.0)
    live = pygame.image.tostring(surface.subsurface(P.BOARD), "RGB")
    assert quiet != live


@pytest.mark.parametrize("room", (1, 2, 3))
def test_laser_collisions_use_check_laser_collision_on_all_four_edges(room):
    question_id = next(k for k, v in QUESTIONS.items() if v["room"] == room)
    level = make_level(room, question_id)
    hits = []
    player = pygame.Rect(0, 0, 32, 32)
    level.laser_phase = lambda index: "active"      # only active beams can hit
    level.game = SimpleNamespace(
        player=SimpleNamespace(rect=player),
        security=SimpleNamespace(increase=lambda amount: (_ for _ in ()).throw(AssertionError("no security"))),
        score=SimpleNamespace(penalize=lambda amount: hits.append(amount)),
        coop=False,
    )

    for laser in level.lasers:
      for beam in level.beam_segments(laser):
        mid_x, mid_y = beam.centerx - 16, beam.centery - 16

        for edge in ("left", "right", "above", "below"):
            for inside in (0, 1):
                if edge == "left":
                    player.topleft = (beam.left - 32 + inside, mid_y)
                elif edge == "right":
                    player.topleft = (beam.right - inside, mid_y)
                elif edge == "above":
                    player.topleft = (mid_x, beam.top - 32 + inside)
                else:
                    player.topleft = (mid_x, beam.bottom - inside)

                level.laser_penalty_cooldown = 0.0
                hits.clear()
                level.check_laser_collision(0.0)

                assert bool(hits) == bool(inside), (room, edge, inside, tuple(beam))
                assert player.colliderect(beam) == bool(inside)

def test_night_guard_walks_greets_and_reacts_without_touching_the_rules():
    from levels import patrol_decor as P

    level = make_level(1, next(k for k, v in QUESTIONS.items() if v["room"] == 1))
    assert level.guard.kind == "night_guard"
    start = level.guard.rect.topleft
    seen = set()
    for _ in range(600):
        level._update_guard(1 / 30)
        seen.add(level.guard.rect.topleft)
    assert len(seen) > 1                 # he walks his lap
    level._guard_says(P.GUARD_HIT)
    assert level.guard.speech == P.GUARD_HIT
    for room in (1, 2, 3):                                    # every room has lines, none too wide for a bubble
        assert P.GUARD_GREETING[room] and P.GUARD_IDLE[room]


def test_the_guard_lap_stays_clear_of_every_rail_and_the_question_panel():
    from levels import patrol_decor as P

    for room in (1, 2, 3):
        level = make_level(room, next(k for k, v in QUESTIONS.items() if v["room"] == room))
        route = P.GUARD_ROUTES[room]
        lap = pygame.Rect(route[0][0], route[0][1], route[1][0] - route[0][0] + 32, 32)
        for rail in rail_bodies(level) + rail_emitters(level):
            assert not lap.colliderect(rail), (room, rail)
        assert lap.bottom < level._bottom_layout()["panel"].top
