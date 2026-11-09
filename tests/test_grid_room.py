"""Floor 2 - the maintenance grid: geometry, the unchanged Level 2 rules, the room, the game."""

import os
from collections import deque
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.player import Player
from core.tilemap import TILE
from levels import snake_decor as G
from levels import level2_grid as L2
from levels.level2 import Level2
from levels.level2_grid import GridRoom
from systems.scoring import ScoreTracker
from systems.security import SecurityMeter
from ui import theme

E_KEY = pygame.K_e


@pytest.fixture(autouse=True)
def display_init():
    pygame.init()
    pygame.display.set_mode((960, 640))


def question(prompt="What does 6 * 7 evaluate to?", options=("42", "67", "13", "76"), answer="42",
             hint="* means multiply.", points=50):
    return {"prompt": prompt, "options": list(options), "answer": answer, "hint": hint,
            "points": points, "difficulty": "medium", "room": 1}


class FakeAudio:
    def __init__(self):
        self.played = []

    def play(self, name):
        self.played.append(name)


def make_room(hints=True, coop=False, seed=1):
    game = SimpleNamespace(score=ScoreTracker(), security=SecurityMeter(),
                           hints=SimpleNamespace(enabled=hints), coop=coop, player2=None,
                           difficulty={"name": "medium", "security_penalty_multiplier": 1.0},
                           audio=FakeAudio())
    game.score.add(100)
    player = Player(*G.SPAWNS[0])
    if coop:
        game.player2 = Player(*G.SPAWNS[1])
    room = GridRoom(player=player, game=game, seed=seed)
    return room, game, player


def set_pool(room, questions):
    """Make every gate draw from `questions` (one per gate, in order)."""
    room.room_question_pools = {1: [questions[0]], 2: [questions[1]], 3: [questions[2]]}
    room.current_difficulty = "medium"
    room._load_question_for_gate(1)


def press(room, key=E_KEY):
    room.handle_event(pygame.event.Event(pygame.KEYDOWN, key=key))


def stand_on(player, rect):
    player.rect.center = rect.center


def answer(room, player, label):
    index = room.current_question["options"].index(label)
    stand_on(player, room.pad_rects()[index])
    press(room)


QS = [question(), question("What does 5 > 3 evaluate to?", ("True", "False", "5"), "True", "Is 5 bigger?", 40),
      question("What does True and False evaluate to?", ("False", "True"), "False", "'and' needs both.", 60)]


def settle(room, seconds=3.0):
    for _ in range(int(seconds * 60)):
        room.update(1 / 60)


# --- geometry ---------------------------------------------------------------
def test_the_map_is_one_screen_of_three_corridors_joined_by_two_shafts():
    rows = G.layout_rows()
    assert len(rows) == 20 and all(len(r) == 30 for r in rows)
    assert set(rows[0]) == {"#"} and set(rows[G.WALL_ROWS - 1]) == {"#"} and set(rows[19]) == {"#"}
    for row in G.LANE_ROW:
        assert rows[row][2:28] == "," * 26                      # an unbroken lit lane in every corridor
    for sep, (lo, hi) in zip(G.SEPARATORS, G.SHAFTS):
        assert all(rows[sep][c] == ("," if lo <= c <= hi else "#") for c in range(30))   # a wall with one shaft
    for y in range(G.BANDS[2][0], G.BANDS[2][1] + 1):
        assert rows[y][28:] == ".."                            # the exit gap is at the end of corridor 3
    for y in list(range(G.BANDS[0][0], G.BANDS[0][1] + 1)) + list(range(G.BANDS[1][0], G.BANDS[1][1] + 1)):
        assert rows[y][0:2] == "##" and rows[y][28:] == "##"


def tile_free(room, col, row):
    return not room.room_map.blocked(pygame.Rect(col * TILE + 2, row * TILE + 2, 28, 28))


def reachable(room, start, goal):
    seen, queue = {start}, deque([start])
    while queue:
        c, r = queue.popleft()
        if (c, r) == goal:
            return True
        for nc, nr in ((c + 1, r), (c - 1, r), (c, r + 1), (c, r - 1)):
            if (nc, nr) not in seen and 0 <= nc < 30 and 0 <= nr < 20 and tile_free(room, nc, nr):
                seen.add((nc, nr))
                queue.append((nc, nr))
    return False


def test_the_gates_really_gate_the_way_through():
    room, _, _ = make_room()
    spawn = (3, 8)
    corridor2_east, corridor2_west = (26, 12), (3, 12)
    corridor3, exit_tile = (10, 16), (29, 16)
    assert tile_free(room, *spawn)
    assert not reachable(room, spawn, exit_tile)
    assert reachable(room, spawn, (22, 8))                    # corridor 1 is open to walk along
    assert not reachable(room, spawn, (26, 8))                # power gate 1 holds
    assert not reachable(room, spawn, corridor2_east)
    room.gate_blocks[0].size = (0, 0)
    assert reachable(room, spawn, (26, 8)) and reachable(room, spawn, corridor2_east)
    assert reachable(room, spawn, (8, 12)) and not reachable(room, spawn, corridor2_west)    # gate 2 holds
    assert not reachable(room, spawn, corridor3)
    room.gate_blocks[1].size = (0, 0)
    assert reachable(room, spawn, corridor2_west) and reachable(room, spawn, corridor3)
    assert not reachable(room, spawn, exit_tile)               # the exit shutter holds
    room.gate_blocks[2].size = (0, 0)
    assert reachable(room, spawn, exit_tile)


def test_every_corridor_has_its_pads_reachable_without_opening_anything_extra():
    room, _, _ = make_room()
    for gate in range(3):
        for count in (2, 3, 4):
            for pad in G.pad_rects(gate, count):
                col, row = pad.centerx // TILE, pad.centery // TILE
                assert tile_free(room, col, row), (gate, count, pad)
    room.gate_blocks[0].size = (0, 0)
    room.gate_blocks[1].size = (0, 0)
    assert reachable(room, (3, 8), (13, 16))                    # corridor 3's plates, once both gates are open


@pytest.mark.parametrize("count", [2, 3, 4])
def test_pads_are_centred_apart_and_inside_their_corridor(count):
    for gate, (first, last) in enumerate(G.BANDS):
        pads = G.pad_rects(gate, count)
        assert len(pads) == count
        corridor = pygame.Rect(2 * TILE, first * TILE, 26 * TILE, (last - first + 1) * TILE)
        assert all(corridor.contains(p) for p in pads)
        assert all(not a.colliderect(b) for i, a in enumerate(pads) for b in pads[i + 1:])
        assert abs((pads[0].left + pads[-1].right) / 2 - G.PAD_CENTRE_X[gate]) <= 1
        assert all(p.y == G.PAD_YS[gate] for p in pads)


def test_screens_hang_on_the_wall_clear_of_the_text_band_and_hud():
    for gate, (first, last) in enumerate(G.SCREEN_COLS):
        r = G.screen_rect(gate)
        assert r.top >= 96 and r.bottom <= G.WALL_ROWS * TILE
        assert r.left >= first * TILE and r.right <= (last + 1) * TILE
        assert r.width >= 224


def test_racks_desk_and_transformers_stand_on_the_floor_and_off_pads_lanes_and_spawn():
    props = G.rack_rects() + G.desk_rects() + G.transformer_rects()
    assert len(G.rack_rects()) == 2 and len(G.desk_rects()) == 1 and len(G.transformer_rects()) == 2
    pads = [p for gate in range(3) for p in G.pad_rects(gate, 4)]
    for p in props:
        assert p.top >= G.WALL_ROWS * TILE
        assert not any(p.colliderect(pad.inflate(8, 8)) for pad in pads)
    for spawn in G.SPAWNS:
        assert not any(pygame.Rect(spawn, (32, 32)).colliderect(p) for p in props)
    for lane_row in G.LANE_ROW:                                  # a player-wide path stays open beside every prop
        for p in props:
            if p.top <= lane_row * TILE < p.bottom:
                pytest.fail(f"{p} blocks lane row {lane_row}")


def test_spawns_are_free_floor_apart_from_each_other():
    room, _, _ = make_room()
    rects = [pygame.Rect(s, (32, 32)) for s in G.SPAWNS]
    assert all(not room.room_map.blocked(r) for r in rects)
    assert not rects[0].colliderect(rects[1])
    assert room.spawn_points == G.SPAWNS


# --- the rules: the same numbers as the old Level 2 ------------------------------
def test_it_is_a_level_2_underneath():
    room, _, _ = make_room()
    assert isinstance(room, Level2)
    assert room.gates_passed == 0 and not room.is_complete()
    assert room.time_limit == room.time_left
    assert room.current_question["options"]


def test_a_right_answer_scores_opens_the_gate_resets_the_clock_and_loads_the_next_question():
    room, game, player = make_room()
    set_pool(room, QS)
    room.time_left = 7.0
    before = game.score.get_score()
    answer(room, player, "42")
    assert game.score.get_score() == before + 50
    assert room.gates_passed == 1 and room.solved == [QS[0]]
    assert room.time_left == room.time_limit
    assert room.current_question is QS[1]
    assert room.message == "Relay 1 live. Power gate 1 open."
    assert room.message_tone == theme.TEAL
    assert game.security.level == 0
    assert "door" in game.audio.played


def test_a_wrong_answer_costs_security_and_score_and_shows_the_hint():
    room, game, player = make_room()
    set_pool(room, QS)
    before = game.score.get_score()
    answer(room, player, "67")
    assert game.security.level == 20
    assert game.score.get_score() == before - 10
    assert room.message == "Wrong. Hint: * means multiply."
    assert room.message_tone == theme.CORAL
    assert room.gates_passed == 0 and room.current_question is QS[0]
    assert room.shake.trauma > 0.3 and room.sparks
    assert room.pad_flash == {1: L2.FLASH_SECONDS}
    assert room.engineer.speech == L2.SCOLD


def test_with_hints_off_a_wrong_answer_says_so():
    room, _, player = make_room(hints=False)
    set_pool(room, QS)
    answer(room, player, "13")
    assert room.message == "Wrong. Hints are off on this difficulty."


def test_a_question_without_a_hint_falls_back_to_try_again():
    room, _, player = make_room()
    q = question()
    del q["hint"]
    set_pool(room, [q, QS[1], QS[2]])
    answer(room, player, "67")
    assert room.message == "Wrong. Hint: Try again."


def test_points_default_when_a_question_has_none():
    room, game, player = make_room()
    q = question()
    del q["points"]
    set_pool(room, [q, QS[1], QS[2]])
    before = game.score.get_score()
    answer(room, player, "42")
    assert game.score.get_score() == before + 50


def test_running_out_of_time_costs_security_and_score_and_resets_the_clock():
    room, game, _ = make_room()
    set_pool(room, QS)
    before = game.score.get_score()
    room.update(room.time_limit + 0.5)
    assert game.security.level == 25
    assert game.score.get_score() == before - 15
    assert room.message == "TIME'S UP! Security increased. Try this gate again."
    assert room.time_left == room.time_limit
    assert room.current_question is QS[0]


def test_the_clock_runs_only_while_a_question_is_open():
    room, game, player = make_room()
    set_pool(room, QS)
    room.update(2.0)
    assert room.time_left == pytest.approx(room.time_limit - 2.0)
    for label in ("42", "True", "False"):
        answer(room, player, label)
    assert room.gates_passed == 3
    frozen = room.time_left
    room.update(room.time_limit * 3)
    assert room.time_left == frozen and game.security.level == 0


def test_the_third_answer_opens_the_exit_but_you_must_walk_out_for_the_bonus():
    room, game, player = make_room()
    set_pool(room, QS)
    for label in ("42", "True", "False"):
        answer(room, player, label)
    assert room.gates_passed == 3 and not room.is_complete()
    assert room.message == "All relays live - the exit is open."
    before = game.score.get_score()
    settle(room, 4)
    assert not room.is_complete() and room.gate_blocks[2].size == (0, 0)
    player.rect.center = room.exit_zone.center
    room.update(1 / 60)
    assert room.is_complete()
    assert game.score.get_score() == before + 100
    assert room.message == "Grid powered - the way down is open!"
    assert room.engineer.speech == L2.FAREWELL


def test_standing_in_the_exit_does_nothing_while_the_door_is_shut():
    room, _, player = make_room()
    set_pool(room, QS)
    player.rect.center = room.exit_zone.center
    room.update(1 / 60)
    assert not room.is_complete()


def test_the_exit_counts_only_once_the_door_has_nearly_finished_opening():
    room, _, player = make_room()
    set_pool(room, QS)
    for label in ("42", "True", "False"):
        answer(room, player, label)
    player.rect.center = room.exit_zone.center
    room.update(1 / 60)
    assert 0 < room.gate_open[2] < 0.9 and not room.is_complete()
    settle(room, 2)
    assert room.is_complete()


def test_the_finish_bonus_is_paid_once():
    room, game, player = make_room()
    set_pool(room, QS)
    for label in ("42", "True", "False"):
        answer(room, player, label)
    settle(room, 4)
    player.rect.center = room.exit_zone.center
    room.update(1 / 60)
    score = game.score.get_score()
    room.update(1 / 60)
    room.update(1 / 60)
    assert game.score.get_score() == score


def test_gates_open_gradually_and_stop_blocking_only_when_open():
    room, _, player = make_room()
    set_pool(room, QS)
    answer(room, player, "42")
    room.update(1 / 60)
    assert 0 < room.gate_open[0] < 0.5 and room.gate_blocks[0].size == (TILE, 4 * TILE)
    settle(room, 3)
    assert room.gate_open[0] > 0.9 and room.gate_blocks[0].size == (0, 0)
    assert room.gate_open[1] == 0.0 and room.gate_blocks[1].size == (TILE, 3 * TILE)


def test_a_half_open_gate_still_blocks_the_way():
    room, _, player = make_room()
    set_pool(room, QS)
    answer(room, player, "42")
    while room.gate_open[0] < 0.6:
        room.update(1 / 60)
    assert room.gate_open[0] < 0.9 and room.gate_blocks[0].size == (TILE, 4 * TILE)
    assert not reachable(room, (3, 8), (26, 8))


# --- input ------------------------------------------------------------------
def test_pressing_off_a_pad_only_gives_a_nudge():
    room, game, player = make_room()
    set_pool(room, QS)
    player.rect.center = (5 * TILE, 11 * TILE)
    press(room)
    assert room.message == "Stand on a breaker, then press E."
    assert room.gates_passed == 0 and game.security.level == 0 and room.current_question is QS[0]


def test_other_keys_and_a_finished_level_ignore_input():
    room, game, player = make_room()
    set_pool(room, QS)
    stand_on(player, room.pad_rects()[0])
    press(room, pygame.K_SPACE)
    room.handle_event(pygame.event.Event(pygame.KEYUP, key=E_KEY))
    assert room.gates_passed == 0
    room.complete = True
    press(room)
    assert room.gates_passed == 0


def test_the_pad_zone_is_the_pad_plus_a_little_slack():
    room, _, player = make_room()
    set_pool(room, QS)
    pad = room.pad_rects()[3]                                  # the last pad has no neighbour on its right
    player.rect.center = (pad.right + 3, pad.centery)
    assert room.pad_at(player) == 3
    player.rect.center = (pad.right + 5, pad.centery)
    assert room.pad_at(player) is None
    pad = room.pad_rects()[2]
    player.rect.center = (pad.centerx, pad.top - 3)
    assert room.pad_at(player) == 2
    player.rect.center = (pad.centerx, pad.top - 5)
    assert room.pad_at(player) is None


def test_the_second_player_answers_with_right_shift_and_only_in_co_op():
    room, game, p1 = make_room(coop=True)
    set_pool(room, QS)
    stand_on(game.player2, room.pad_rects()[0])
    press(room, E_KEY)                                         # player 1 is not on a pad
    assert room.gates_passed == 0
    press(room, pygame.K_RSHIFT)
    assert room.gates_passed == 1
    solo, _, player = make_room(coop=False)
    set_pool(solo, QS)
    stand_on(player, solo.pad_rects()[0])
    press(solo, pygame.K_RSHIFT)
    assert solo.gates_passed == 0


def test_there_are_no_pads_once_every_gate_is_open():
    room, _, player = make_room()
    set_pool(room, QS)
    for label in ("42", "True", "False"):
        answer(room, player, label)
    assert room.pad_rects() == [] and room.pad_at(player) is None
    press(room)
    assert room.message == "All relays live - the exit is open."


def test_a_pad_only_belongs_to_the_active_chamber():
    room, _, player = make_room()
    set_pool(room, QS)
    next_pad = G.pad_rects(1, 3)[0]
    stand_on(player, next_pad)
    assert room.pad_at(player) is None


# --- the engineer -------------------------------------------------------------
def test_the_engineer_is_a_harmless_person_who_walks_a_route():
    room, _, _ = make_room()
    assert room.engineer.kind == "engineer" and room.npcs == [room.engineer]
    assert not any(room.engineer.rect.colliderect(p) for p in room.props)
    start = room.engineer.rect.center
    for _ in range(300):
        room.update(1 / 60)
    assert room.engineer.rect.center != start


def test_the_engineer_tips_off_a_passer_by_in_turn_but_not_again_while_they_linger():
    room, _, player = make_room()
    tips = []
    for visit in range(4):
        player.rect.center = (room.engineer.rect.centerx, room.engineer.rect.centery + 20)
        room.update(1 / 60)
        tips.append(room.engineer.speech)
        room.update(1 / 60)
        assert room.engineer.speech == tips[-1]
        player.rect.center = (30 * TILE, 2 * TILE)                  # leave, far enough to be forgotten
        room.update(1 / 60)
    assert tips[:3] == list(L2.ENGINEER_LINES) and tips[3] == L2.ENGINEER_LINES[0]


def test_the_engineer_praises_every_other_right_answer():
    room, _, player = make_room()
    set_pool(room, QS)
    answer(room, player, "42")
    assert room.engineer.speech == L2.PRAISE[0]
    room.engineer.speech = None
    answer(room, player, "True")
    assert room.engineer.speech is None
    answer(room, player, "False")                               # the last gate: no praise, the farewell comes later
    assert room.engineer.speech is None


# --- pads and flashes ---------------------------------------------------------------
def test_a_wrong_pad_flashes_then_calms_and_the_right_one_lingers_in_green():
    room, _, player = make_room()
    set_pool(room, QS)
    answer(room, player, "67")
    assert 1 in room.pad_flash
    room.update(L2.FLASH_SECONDS + 0.1)
    assert room.pad_flash == {}
    answer(room, player, "42")
    assert room.pad_flash == {} and room.done_pad[1] == "42"
    assert room.done_pad[0] == G.pad_rects(0, 4)[0]
    room.update(L2.DONE_PAD_SECONDS + 0.1)
    assert room.done_pad is None


# --- drawing ------------------------------------------------------------------------
def region_pixels(surface, rect):
    return [surface.get_at((x, y))[:3] for x in range(rect.left, rect.right, 3)
            for y in range(rect.top, rect.bottom, 3)]


def render(room):
    s = pygame.Surface((960, 640))
    room.render(s)
    return s


def test_screens_show_each_chambers_state():
    room, _, player = make_room()
    set_pool(room, QS)
    assert [room._screen_state(g) for g in range(3)] == ["active", "standby", "standby"]
    answer(room, player, "42")
    assert [room._screen_state(g) for g in range(3)] == ["accepted", "active", "standby"]
    for label in ("True", "False"):
        answer(room, player, label)
    assert [room._screen_state(g) for g in range(3)] == ["accepted"] * 3


def test_a_screen_looks_different_standby_active_and_accepted():
    surface = pygame.Surface((960, 640))
    rect = G.screen_rect(0)
    images = []
    for state in ("standby", "active", "accepted"):
        s = pygame.Surface((960, 640))
        s.fill(theme.INK)
        G.draw_screen(s, rect, 0, state, theme.ORANGE if hasattr(theme, "ORANGE") else (255, 140, 80),
                      prompt="What does 6 * 7 evaluate to?", answer="42", fraction=0.5, seconds=12)
        images.append(region_pixels(s, rect))
    assert images[0] != images[1] != images[2] and images[0] != images[2]


def test_the_timer_bar_shrinks_and_flashes_when_low():
    rect = G.screen_rect(0)
    def bar(fraction, t=0.0):
        s = pygame.Surface((960, 640))
        s.fill(theme.INK)
        G.draw_screen(s, rect, 0, "active", (255, 140, 80), prompt="x", fraction=fraction, seconds=3, time=t)
        y = rect.bottom - 10
        return sum(1 for x in range(rect.left + 8, rect.right - 8) if s.get_at((x, y))[:3] != theme.INK[:3]
                   and s.get_at((x, y))[:3] != theme.mix(theme.INK, theme.SLATE, 0.5))
    assert bar(1.0) > bar(0.5) > bar(0.1) > 0
    assert bar(0.1, 0.0) == bar(0.1, 0.3)


def test_the_screens_prompt_wraps_inside_the_screen_and_never_past_three_lines():
    rect = G.screen_rect(0)
    s = pygame.Surface((960, 640))
    s.fill(theme.INK)
    G.draw_screen(s, rect, 0, "active", (255, 140, 80), prompt="word " * 40, fraction=1.0, seconds=9)
    outside = pygame.Rect(rect.right + 1, rect.top, 20, rect.height)
    assert all(px == tuple(theme.INK[:3]) for px in region_pixels(s, outside))


@pytest.mark.parametrize("state", ["idle", "stand", "right", "wrong"])
def test_a_pad_draws_each_state_inside_its_rectangle_plus_glow(state):
    s = pygame.Surface((960, 640))
    s.fill((1, 2, 3))
    pad = G.pad_rects(0, 4)[0]
    G.draw_pad(s, pad, "3.75", state, (255, 140, 80), 0.0)
    outside = pad.inflate(24, 24)
    painted = [(x, y) for x in range(outside.left, outside.right) for y in range(outside.top, outside.bottom)
               if s.get_at((x, y))[:3] != (1, 2, 3)]
    assert painted and all(outside.collidepoint(p) for p in painted)


def test_pad_states_differ_and_a_long_label_still_fits():
    pad = G.pad_rects(0, 4)[0]
    def image(state, label="42"):
        s = pygame.Surface((960, 640))
        s.fill((1, 2, 3))
        G.draw_pad(s, pad, label, state, (255, 140, 80), 0.0)
        return region_pixels(s, pad)
    assert len({tuple(image(s)) for s in ("idle", "stand", "right", "wrong")}) == 4
    assert G.fit_font("3.75", pad.w - 8).size("3.75")[0] <= pad.w - 8
    assert G.fit_font("a" * 60, 30).size("a" * 60)[0] > 30                 # nothing fits: the smallest comes back
    assert G.fit_font("a" * 60, 30).get_height() <= G.fit_font("a", 999).get_height()


def test_the_room_renders_in_every_state_and_changes_over_time():
    room, game, player = make_room()
    set_pool(room, QS)
    first = render(room)
    settle(room, 1.5)
    second = render(room)
    assert region_pixels(first, pygame.Rect(0, 96, 960, 544)) != region_pixels(second, pygame.Rect(0, 96, 960, 544))
    answer(room, player, "67")
    render(room)
    for label in ("42", "True", "False"):
        answer(room, player, label)
    settle(room, 4)
    player.rect.center = room.exit_zone.center
    room.update(1 / 60)
    render(room)
    assert room.is_complete()


def test_the_background_is_built_once_and_the_title_is_on_the_wall():
    room, _, _ = make_room()
    render(room)
    built = room._background
    settle(room, 1)
    render(room)
    assert room._background is built
    title_band = pygame.Rect(64, 44, 340, 30)
    assert len(set(region_pixels(built, title_band))) > 3


def test_decoration_stays_off_the_text_band_and_the_lane():
    room, _, _ = make_room()
    room.message = ""
    render(room)
    band = pygame.Rect(64, 76, 700, 18)                                      # the message line's row
    assert len(set(region_pixels(room._background, band))) <= 6               # a quiet wall, nothing baked on it


# --- pure helpers -------------------------------------------------------------
def test_leds_are_deterministic_three_valued_and_not_all_alike():
    values = {G.led_state(t / 10, r, l) for t in range(300) for r in range(6) for l in range(6)}
    assert values == {0, 1, 2}
    assert G.led_state(3.3, 2, 4) == G.led_state(3.3, 2, 4)
    assert len({G.led_state(5.0, 1, l) for l in range(6)}) > 1
    assert len({G.led_state(5.0, r, 0) for r in range(6)}) > 1


def test_data_pulses_travel_the_line_and_wrap():
    pts = G.pulse_points(0.0, (0, 0), (100, 0), count=4)
    assert [round(p[0]) for p in pts] == [0, 25, 50, 75]
    later = G.pulse_points(G.PULSE_SECONDS / 2, (0, 0), (100, 0), count=4)
    assert [round(p[0]) for p in later] == [50, 75, 0, 25]
    assert G.pulse_points(G.PULSE_SECONDS, (0, 0), (100, 0), count=4) == pts or \
        [round(p[0]) for p in G.pulse_points(G.PULSE_SECONDS, (0, 0), (100, 0), count=4)] == [0, 25, 50, 75]
    down = G.pulse_points(0.0, (10, 0), (10, 80), count=2)
    assert [p[1] for p in down] == [0, 40] and all(p[0] == 10 for p in down)


def test_timer_fraction_is_clamped_and_safe():
    assert G.timer_fraction(10, 20) == 0.5
    assert G.timer_fraction(-3, 20) == 0.0 and G.timer_fraction(30, 20) == 1.0
    assert G.timer_fraction(5, 0) == 0.0


def test_the_gate_retracts_into_its_posts_and_the_shutter_slides_open():
    rect = G.GATE_RECTS[0]
    def bars(openness):
        s = pygame.Surface((960, 640))
        s.fill((1, 2, 3))
        G.draw_gate(s, rect, openness, 0.2)
        cx = rect.centerx
        return sum(1 for y in range(rect.top + 12, rect.bottom - 12)
                   if any(s.get_at((cx + dx, y))[:3] != (1, 2, 3) for dx in range(-14, 15)))
    assert bars(0.0) > bars(0.5) > bars(1.0) == 0
    door = G.GATE_RECTS[2]
    def plates(openness):
        s = pygame.Surface((960, 640))
        s.fill((1, 2, 3))
        G.draw_shutter(s, door, openness, theme.CORAL)
        return s.get_at(door.center)[:3]
    assert plates(0.0) != plates(1.0)


def test_ambience_animates_the_leds_pulses_and_dust():
    amb = G.Ambience(seed=1)
    def frame(t):
        a = G.Ambience(seed=1)
        a.update(t)
        s = pygame.Surface((960, 640))
        s.fill((1, 2, 3))
        a.draw(s, (255, 140, 80))
        return s
    rack = G.rack_rects()[0]
    assert region_pixels(frame(0.0), rack) != region_pixels(frame(1.7), rack)
    lane = pygame.Rect(64, G.LANE_ROW[0] * TILE, 832, TILE)
    assert region_pixels(frame(0.0), lane) != region_pixels(frame(2.0), lane)
    amb.update(-5)
    assert amb.time == 0.0


# --- the shared room plumbing -------------------------------------------------------
def test_the_clock_the_dust_and_the_steps_run_through_update_room():
    room, game, player = make_room()
    player.moving = True
    for _ in range(60):
        room.update(1 / 60)
    assert room.time == pytest.approx(1.0)
    assert room.dust and game.audio.played.count("step_metal") >= 2
    player.moving = False
    game.audio.played.clear()
    for _ in range(60):
        room.update(1 / 60)
    assert "step_metal" not in game.audio.played and room.dust == []


def test_sparks_fall_fade_and_disappear():
    room, _, _ = make_room()
    room.burst((100, 100), theme.TEAL, 10)
    assert len(room.sparks) == 10
    y0 = [s["y"] for s in room.sparks]
    room.update(0.1)
    assert [s["y"] for s in room.sparks] != y0
    room.update(1.0)
    assert room.sparks == []


def test_a_room_without_audio_or_a_game_still_works():
    room = GridRoom(player=Player(*G.SPAWNS[0]), game=None, seed=2)
    room.sfx("door")
    room.update(0.5)
    render(room)
    assert room.players() == [(room.player, E_KEY)]
    set_pool(room, QS)
    stand_on(room.player, room.pad_rects()[1])
    press(room)                                                            # wrong answer, no game to charge
    assert room.gates_passed == 0


def test_the_message_line_and_hint_are_drawn_on_the_wall():
    room, _, _ = make_room()
    room.say("A message to read.", theme.GOLD)
    s = render(room)
    assert len(set(region_pixels(s, pygame.Rect(64, 76, 280, 20)))) > 3
    assert len(set(region_pixels(s, pygame.Rect(740, 46, 160, 22)))) > 3


# --- inside the real game ------------------------------------------------------------
@pytest.fixture
def game():
    from core.game import Game
    g = Game()
    yield g
    g.music.stop()
    pygame.mixer.stop()
    pygame.mixer.set_reserved(0)


def test_the_real_game_uses_the_grid_room_unless_told_otherwise(monkeypatch):
    from core.game import Game
    monkeypatch.delenv("MEMORY_HEIST_OLD_LEVEL2", raising=False)
    g = Game()
    assert isinstance(g.level_manager.levels["level2"], GridRoom)
    g.music.stop()
    for value, cls in (("1", Level2), ("0", GridRoom), ("", GridRoom), ("yes", GridRoom)):
        monkeypatch.setenv("MEMORY_HEIST_OLD_LEVEL2", value)
        g = Game()
        assert type(g.level_manager.levels["level2"]) is cls, value
        g.music.stop()


def test_players_start_at_the_levels_spawn_points_or_the_default(game):
    from core.game import PLAYER2_START_POS, PLAYER_START_POS
    game.level_manager.current = SimpleNamespace(spawn_points=((200, 300), (260, 300)))
    game._reset_player_position()
    assert game.player.rect.topleft == (200, 300) and game.player2.rect.topleft == (260, 300)
    game.level_manager.current = SimpleNamespace()
    game._reset_player_position()
    assert game.player.rect.topleft == PLAYER_START_POS and game.player2.rect.topleft == PLAYER2_START_POS
    game.level_manager.current = None
    game._reset_player_position()
    assert game.player.rect.topleft == PLAYER_START_POS


def test_entering_level_2_in_the_real_game_puts_the_players_in_the_first_chamber(game):
    game.story_enabled = False
    game.level_manager.start("level2")
    game.state = "playing"
    game._last_level_name = "level1"
    game.update(1 / 60)
    assert game.player.rect.topleft == G.SPAWNS[0] and game.player2.rect.topleft == G.SPAWNS[1]
    assert game.level_manager.current_name == "level2"


def test_a_whole_run_through_floor_2_in_the_real_game_ends_on_floor_3(game):
    game.story_enabled = False
    game.level_manager.start("level2")
    game._last_level_name = "level2"
    game.state = "playing"
    room = game.level_manager.current
    set_pool(room, QS)
    game.score.add(100)
    for label in ("42", "True", "False"):
        answer(room, game.player, label)
        for _ in range(30):
            game.update(1 / 60)
    for _ in range(240):
        game.update(1 / 60)
        game.render()
    assert game.state == "playing" and game.level_manager.current_name == "level2"
    game.player.rect.center = room.exit_zone.center
    game.update(1 / 60)
    assert game.level_manager.current_name == "level3"


def test_radio_and_story_for_level_2_describe_the_room_not_the_old_screen():
    from core.comms import MAX_LINE, line_for
    from core.story import beat_for
    beat = beat_for("level2")
    text = " ".join([beat["title"], *beat["lines"]]).lower()
    assert "maintenance grid" in beat["title"].lower() and "breaker" in text and "screen" in text
    assert "42" not in text and "security grid" not in text and beat["concept"] == "Operators"
    speaker, line = line_for("level2", "enter")
    assert speaker == "Echo" and len(line) <= MAX_LINE and "relay" in line.lower() and "42" not in line


# --- polish: fitted prompts, signs, floor paint, chevrons ------------------------
def test_a_short_prompt_gets_the_big_font_on_at_most_two_lines():
    font, lines = G.fit_prompt("What does 15 // 4 evaluate to?", 216)
    assert font.get_height() > G.code_font(17).get_height()
    assert 1 <= len(lines) <= 2 and " ".join(lines) == "What does 15 // 4 evaluate to?"
    assert all(font.size(line)[0] <= 216 for line in lines)


def test_a_long_prompt_shrinks_then_is_cut_to_three_lines():
    long = "What does the expression (3 + 4) * 2 ** 2 - 10 // 3 evaluate to here?"
    font, lines = G.fit_prompt(long, 216)
    assert font.get_height() == G.code_font(17).get_height()
    assert len(lines) == 3
    huge, cut = G.fit_prompt("word " * 80, 216)
    assert len(cut) == 3 and all(huge.size(line)[0] <= 216 for line in cut)


def test_fit_prompt_handles_an_empty_prompt():
    assert G.fit_prompt("", 216)[1] in ([], [""])


def static_background(room):
    render(room)
    return room._background


def test_hazard_stripes_are_painted_under_the_two_gates_but_not_the_exit_or_plain_corridor():
    room, _, _ = make_room()
    bg = static_background(room)
    plain = pygame.Rect(9 * TILE, G.BANDS[0][0] * TILE + 6, TILE, 14)             # bare corridor floor, clear of props
    for rect in G.GATE_RECTS[:2]:
        cell = pygame.Rect(rect.x, rect.y + 6, rect.w, 20)
        assert len(set(region_pixels(bg, cell))) >= 2
        assert any(p[0] > 120 and p[2] < 90 for p in region_pixels(bg, cell))          # a warm stripe colour
    assert not any(p[0] > 120 and p[2] < 90 for p in region_pixels(bg, plain))


def test_there_is_an_exit_sign_above_the_door_and_a_label_on_each_corridor_floor():
    room, _, _ = make_room()
    bg = static_background(room)
    sign = pygame.Rect(28 * TILE + 4, G.SEPARATORS[1] * TILE + 3, 56, 26)
    wall = pygame.Rect(28 * TILE + 4, 20 * TILE - 22, 56, 14)                       # bare bottom wall
    assert len(set(region_pixels(bg, sign))) > len(set(region_pixels(bg, wall)))
    assert any(p[1] > 150 and p[0] < 120 for p in region_pixels(bg, sign))               # teal letters
    for gate, (_, last) in enumerate(G.BANDS):
        y = (last + 1) * TILE - 10
        label = pygame.Rect(G.PAD_CENTRE_X[gate] - 100, y - 8, 200, 16)
        assert len(set(region_pixels(bg, label))) > 4
        assert len(set(region_pixels(bg, pygame.Rect(G.PAD_CENTRE_X[gate] - 90, y - 8, 40, 16)))) > 2   # the long label, not just "RELAY"


def test_chevrons_show_only_once_the_exit_is_opening_and_they_move():
    def frame(openness, t):
        s = pygame.Surface((960, 640))
        s.fill((1, 2, 3))
        G.draw_chevrons(s, openness, t)
        return region_pixels(s, pygame.Rect(22 * TILE, G.BANDS[2][0] * TILE, 6 * TILE, 3 * TILE))
    blank = frame(0.0, 0.0)
    assert set(blank) == {(1, 2, 3)} and set(frame(0.4, 0.0)) == {(1, 2, 3)}
    assert set(frame(1.0, 0.0)) != {(1, 2, 3)}
    assert frame(1.0, 0.0) != frame(1.0, 0.2)
    assert frame(1.0, 0.0) == frame(1.0, 0.0)


def test_the_room_draws_chevrons_when_the_exit_has_opened():
    room, _, player = make_room()
    set_pool(room, QS)
    area = pygame.Rect(23 * TILE, G.LANE_ROW[2] * TILE + 4, 4 * 36, 24)          # only the chevrons live here
    before = region_pixels(render(room), area)
    for label in ("42", "True", "False"):
        answer(room, player, label)
    player.rect.center = (3 * TILE, 8 * TILE)
    settle(room, 3)
    first = region_pixels(render(room), area)
    settle(room, 0.1)
    assert first != before and first != region_pixels(render(room), area)


# --- live floor panels: read the expression, walk the False one ------------------------
def test_every_panel_expression_really_evaluates_the_way_its_pool_says():
    for corridor in range(3):
        assert all(G.evaluate(e) is True for e in G.TRUE_EXPRS[corridor]), corridor
        assert all(G.evaluate(e) is False for e in G.FALSE_EXPRS[corridor]), corridor


def test_each_corridor_has_one_panel_per_row_with_a_live_and_a_safe_way_for_any_seed():
    import random
    for seed in range(25):
        tiles = G.panel_tiles(random.Random(seed))
        for corridor, (first, last) in enumerate(G.BANDS):
            row = [t for t in tiles if t["corridor"] == corridor]
            assert [t["row"] for t in row] == list(range(first, last + 1))
            assert any(t["live"] for t in row) and any(not t["live"] for t in row)
            assert all(t["live"] == G.evaluate(t["expr"]) for t in row)       # live exactly when it is True
            assert len({t["expr"] for t in row}) == len(row)                    # no two rows alike
            assert all(t["rect"].width == G.PANEL_TILES_WIDE * TILE for t in row)


def test_panels_never_block_a_corridor_or_sit_on_props_or_pads():
    room, _, _ = make_room()
    for tile in room.panels:
        assert not any(tile["rect"].colliderect(p) for p in room.props)
        assert not any(tile["rect"].colliderect(pad.inflate(8, 8)) for pad in G.pad_rects(tile["corridor"], 4))
    room.gate_blocks[0].size = (0, 0)
    room.gate_blocks[1].size = (0, 0)
    assert reachable(room, (3, 8), (13, 16))                                          # floor panels are not walls


def _step_on(room, player, live):
    tile = next(t for t in room.panels if t["live"] == live)
    player.rect.center = tile["rect"].center
    return tile


def test_stepping_on_a_live_panel_zaps_for_score_only_and_then_waits():
    room, game, player = make_room()
    _step_on(room, player, True)
    score, security = game.score.get_score(), game.security.level
    room.update(1 / 60)
    assert game.score.get_score() == score - L2.PANEL_PENALTY
    assert game.security.level == security                      # hazards never touch security
    assert "zap" in game.audio.played and room.zaps == 1 and room.engineer.speech == L2.PANEL_LINE
    assert "True" in room.message and "live" in room.message
    for _ in range(30):
        room.update(1 / 60)
    assert room.zaps == 1                                         # the cooldown stops a second zap straight away


def test_a_safe_panel_does_nothing_and_is_marked_safe():
    room, game, player = make_room()
    tile = _step_on(room, player, False)
    score = game.score.get_score()
    room.update(1 / 60)
    assert room.zaps == 0 and game.score.get_score() == score and "zap" not in game.audio.played
    assert room.panel_state[room.panels.index(tile)] == "safe"


def test_the_panel_answer_never_changes_over_time():
    room, game, player = make_room()
    before = [(t["expr"], t["live"]) for t in room.panels]
    settle(room, 20)
    assert [(t["expr"], t["live"]) for t in room.panels] == before


def test_a_player_off_the_panels_is_never_zapped():
    room, game, player = make_room()
    player.rect.center = (3 * TILE, 8 * TILE)
    room.update(1 / 60)
    assert room.zaps == 0 and G.panel_under(room.panels, player.rect) is None


def test_the_second_player_is_zapped_on_their_own_clock():
    room, game, p1 = make_room(coop=True)
    live = next(t for t in room.panels if t["live"])
    p1.rect.center = live["rect"].center
    game.player2.rect.center = live["rect"].center
    room.update(1 / 60)
    assert room.zaps == 2


def test_a_tried_panel_remembers_what_it_was_and_a_zap_flashes_then_calms():
    room, game, player = make_room()
    tile = _step_on(room, player, True)
    index = room.panels.index(tile)
    room.update(1 / 60)
    assert room.panel_state[index] == "live" and index in room.panel_flash
    player.rect.center = (3 * TILE, 8 * TILE)
    settle(room, 1.0)
    assert index not in room.panel_flash and room.panel_state[index] == "live"


def test_panel_states_look_different_and_a_long_expression_stays_inside_its_panel():
    tile = {"rect": G.panel_tiles(__import__("random").Random(1))[0]["rect"], "expr": "True and False"}
    def frame(state):
        s = pygame.Surface((960, 640))
        s.fill((1, 2, 3))
        G.draw_floor_panel(s, tile, state, 0.3)
        return region_pixels(s, tile["rect"])
    assert len({tuple(frame(s)) for s in ("unknown", "safe", "live")}) == 3 and frame("live") == frame("live")
    s = pygame.Surface((960, 640))
    s.fill((1, 2, 3))
    G.draw_floor_panel(s, tile, "unknown", 0.0)
    outside = tile["rect"].inflate(40, 40)
    assert all(p == (1, 2, 3) for p in region_pixels(s, pygame.Rect(outside.x, outside.y, 20, outside.h)))


def test_the_breaker_clunks_and_boots_ring_on_steel():
    room, game, player = make_room()
    set_pool(room, QS)
    answer(room, player, "42")
    assert "switch" in game.audio.played and "door" in game.audio.played
    assert GridRoom.STEP_SOUND == "step_metal"
