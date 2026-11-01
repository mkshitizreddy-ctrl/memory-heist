"""Floor 1 - Reception Lobby: sort crates by Python type, open gates, leave."""

import os
import random
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from levels import floor1_lobby as f1
from levels.floor1_lobby import (BIN_TYPES, FloorOneLobby, display, layout_rows,
                                 pick_crates, type_name, with_article)
from core.player import Player
from systems.scoring import ScoreTracker
from systems.security import SecurityMeter


@pytest.fixture(autouse=True)
def display_init():
    pygame.init()
    pygame.display.set_mode((960, 640))


def make_game(hints=True, difficulty=None):
    return SimpleNamespace(
        score=ScoreTracker(), security=SecurityMeter(),
        hints=SimpleNamespace(enabled=hints), coop=False, player2=None,
        difficulty=difficulty or {"security_penalty_multiplier": 1.0})


def make_level(seed=1, **kw):
    game = make_game(**kw)
    player = Player(100, 100)
    level = FloorOneLobby(player=player, game=game, seed=seed)
    return level, game, player


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


def stand_by(player, rect):
    player.rect.midtop = (rect.centerx, rect.bottom + 2)


def carry(level, player, crate):
    stand_by(player, crate.rect)
    level.handle_event(key(pygame.K_e))
    assert level.carried.get(id(player)) is crate


def deliver(level, player, crate, bin_type):
    carry(level, player, crate)
    stand_by(player, level.bins[bin_type])
    level.update(0.016)                          # a frame passes while walking over
    level.handle_event(key(pygame.K_e))


def wrong_bin(crate):
    return next(t for t in BIN_TYPES if t != crate.answer)


# --- pure helpers --------------------------------------------------------
def test_type_name_is_pythons_own_answer():
    assert [type_name(v) for v in (42, "42", 3.14, 2.0, True, False, -7, "True")] == \
        ["int", "str", "float", "float", "bool", "bool", "int", "str"]


def test_display_keeps_string_quotes():
    assert display("hi") == '"hi"' and display(42) == "42" and display(True) == "True"


@pytest.mark.parametrize("difficulty", ["easy", "medium", "hard"])
def test_pick_crates_are_distinct_cover_all_types_and_are_valid(difficulty):
    for seed in range(40):
        vals = pick_crates(difficulty, random.Random(seed))
        assert len(vals) == 6
        assert len({(type(v), v) for v in vals}) == 6
        assert {type_name(v) for v in vals} == set(BIN_TYPES)


def test_pick_crates_deterministic_for_a_seed_and_varies_between_seeds():
    a = pick_crates("medium", random.Random(5))
    assert a == pick_crates("medium", random.Random(5))
    assert len({tuple(map(repr, pick_crates("medium", random.Random(s)))) for s in range(20)}) > 5


def test_traps_appear_only_on_harder_difficulties():
    def has_trap(d):
        for s in range(200):
            vals = pick_crates(d, random.Random(s))
            if "42" in vals or 2.0 in [v for v in vals if isinstance(v, float)]:
                return True
        return False
    assert not has_trap("easy")
    assert has_trap("medium") and has_trap("hard")


def test_layout_is_a_closed_room_with_an_exit_gap():
    rows = layout_rows()
    assert len(rows) == 20 and all(len(r) == 30 for r in rows)
    assert all(c == "#" for c in rows[0]) and all(c == "#" for c in rows[19])
    for y in f1.EXIT_ROWS:
        assert rows[y][29] == "." and rows[y][28] == "."
    assert rows[5][29] == "#"


# --- level setup ---------------------------------------------------------
def test_player_spawn_point_is_free_floor():
    level, _, player = make_level()
    assert not level.room_map.blocked(player.rect)


def test_crates_start_on_free_floor_and_do_not_overlap():
    for seed in range(30):
        level, _, _ = make_level(seed)
        for c in level.crates:
            assert not level.room_map.blocked(c.rect), (seed, c.value)
        rects = [c.rect for c in level.crates]
        for i, a in enumerate(rects):
            assert a.collidelist(rects[i + 1:]) == -1


def test_every_crate_can_be_reached_from_the_spawn():
    level, _, player = make_level()
    seen = {(player.rect.x // 8, player.rect.y // 8)}
    stack = [player.rect.topleft]
    reach = set(stack)
    probe = player.rect.copy()
    while stack:
        x, y = stack.pop()
        for dx, dy in ((8, 0), (-8, 0), (0, 8), (0, -8)):
            n = (x + dx, y + dy)
            if n in reach:
                continue
            probe.topleft = n
            if not level.room_map.blocked(probe):
                reach.add(n)
                stack.append(n)
    for c in level.crates:
        assert any(c.rect.inflate(60, 60).collidepoint(p[0] + 16, p[1] + 16) for p in reach), c.value


def test_walls_props_and_closed_door_block_movement():
    level, _, _ = make_level()
    assert level.room_map.blocked(pygame.Rect(0, 0, 32, 32))
    assert level.room_map.blocked(level.bins["int"])
    assert level.room_map.blocked(level.desk)
    assert level.room_map.blocked(level.door.copy().inflate(-4, -4))
    assert not level.room_map.blocked(pygame.Rect(6 * 32, 11 * 32, 32, 32))


# --- interaction ---------------------------------------------------------
def test_pick_up_needs_to_be_close():
    level, _, player = make_level()
    c = level.crates[0]
    player.rect.topleft = (64, 540)               # far corner, no crate in reach
    level.handle_event(key(pygame.K_e))
    assert level.carried == {}
    carry(level, player, c)
    assert c.carrier is player


def test_pick_up_takes_the_nearest_crate():
    level, _, player = make_level()
    a, b = level.crates[:2]
    b.rect.center = (a.rect.centerx + 40, a.rect.centery)
    player.rect.center = (a.rect.centerx + 4, a.rect.centery + 20)
    level.handle_event(key(pygame.K_e))
    assert level.carried[id(player)] is a


def test_correct_bin_scores_and_removes_the_crate():
    level, game, player = make_level()
    c = level.crates[0]
    deliver(level, player, c, c.answer)
    assert c.sorted and level.sorted_count == 1
    assert game.score.get_score() == f1.CRATE_POINTS
    assert game.security.level == 0 and level.carried == {}
    assert level.sparks


def test_wrong_bin_returns_crate_and_costs_security_and_score():
    level, game, player = make_level()
    game.score.add(100)
    c = level.crates[0]
    home = c.home.copy()
    deliver(level, player, c, wrong_bin(c))
    assert not c.sorted and c.rect == home and c.carrier is None
    assert game.security.level == 20 and game.score.get_score() == 90
    assert level.shake.trauma > 0
    assert "Not a" in level.message and f1.HINTS[c.answer] in level.message


def test_wrong_bin_message_respects_hints_off():
    level, _, player = make_level(hints=False)
    c = level.crates[0]
    deliver(level, player, c, wrong_bin(c))
    assert "Hints are off" in level.message and f1.HINTS[c.answer] not in level.message


def test_score_never_negative_on_wrong_answers():
    level, game, player = make_level()
    c = level.crates[0]
    deliver(level, player, c, wrong_bin(c))
    assert game.score.get_score() == 0


def test_put_down_away_from_bins_drops_the_crate_at_your_feet():
    level, _, player = make_level()
    c = level.crates[0]
    carry(level, player, c)
    player.rect.topleft = (7 * 32, 12 * 32)
    level.handle_event(key(pygame.K_e))
    assert level.carried == {} and c.carrier is None and not c.sorted
    assert not level.room_map.blocked(c.rect)
    assert c.rect.top >= player.rect.bottom - 2


def test_cannot_carry_two_crates_and_cannot_pick_up_sorted_ones():
    level, _, player = make_level()
    a, b = level.crates[:2]
    b.rect.center = a.rect.center
    carry(level, player, a)
    level.handle_event(key(pygame.K_e))          # second press with a crate in hand: puts down
    assert level.carried == {}
    a.sorted = True
    stand_by(player, a.rect)
    level.handle_event(key(pygame.K_e))
    assert level.carried.get(id(player)) is not a


# --- progression ---------------------------------------------------------
def sort_all(level, player, upto=6):
    for c in level.crates[:upto]:
        if not c.sorted:
            deliver(level, player, c, c.answer)


def test_gates_open_every_two_crates_and_exit_after_three():
    level, game, player = make_level()
    level.update(0.016)
    assert level.gates_passed == 0
    sort_all(level, player, 1)
    assert level.gates_passed == 0
    sort_all(level, player, 2)
    assert level.gates_passed == 1
    assert level.door_tween is None
    sort_all(level, player, 6)
    assert level.gates_passed == 3
    assert level.door_tween is not None
    assert game.score.get_score() == 6 * f1.CRATE_POINTS


def test_exit_door_blocks_until_open_then_walkable_and_completes():
    level, game, player = make_level()
    sort_all(level, player)
    assert level.room_map.blocked(level.door.copy().inflate(-4, -4))
    assert not level.is_complete()
    for _ in range(80):
        level.update(0.016)
    assert level.door_open == pytest.approx(1.0)
    assert not level.room_map.blocked(level.door.copy().inflate(-4, -4))
    before = game.score.get_score()
    player.rect.center = level.exit_zone.center
    level.update(0.016)
    assert level.is_complete()
    assert game.score.get_score() == before + f1.FINISH_BONUS


def test_standing_at_the_closed_exit_does_not_complete():
    level, _, player = make_level()
    player.rect.center = level.exit_zone.center
    level.update(0.016)
    assert not level.is_complete()


def test_input_ignored_after_completion():
    level, game, player = make_level()
    sort_all(level, player)
    for _ in range(80):
        level.update(0.016)
    player.rect.center = level.exit_zone.center
    level.update(0.016)
    score = game.score.get_score()
    level.handle_event(key(pygame.K_e))
    level.update(0.016)
    assert game.score.get_score() == score


def test_works_without_a_game_for_standalone_use():
    level = FloorOneLobby(player=Player(100, 100), game=None, seed=3)
    c = level.crates[0]
    deliver(level, level.player, c, wrong_bin(c))
    deliver(level, level.player, c, c.answer)
    assert c.sorted


def test_difficulty_picks_the_trap_pool():
    seen = set()
    for s in range(60):
        lvl, _, _ = make_level(s, difficulty={"security_penalty_multiplier": 1.5})
        seen |= {c.value for c in lvl.crates}
    assert "True" in seen or 1.0 in seen or 0 in seen


def test_coop_second_player_uses_right_shift():
    game = make_game()
    game.coop = True
    p1, p2 = Player(100, 100), Player(150, 100)
    game.player2 = p2
    level = FloorOneLobby(player=p1, game=game, seed=2)
    c = level.crates[0]
    stand_by(p2, c.rect)
    level.handle_event(key(pygame.K_e))
    assert level.carried == {}                    # E belongs to player 1 only
    level.handle_event(key(pygame.K_RSHIFT))
    assert level.carried[id(p2)] is c
    stand_by(p2, level.bins[c.answer])
    level.handle_event(key(pygame.K_RSHIFT))
    assert c.sorted


# --- drawing -------------------------------------------------------------
def test_render_fills_the_screen_and_changes_with_state():
    level, _, player = make_level()
    s = pygame.Surface((960, 640))
    level.render(s)
    assert s.get_size() == (960, 640)
    assert s.get_at((5, 600))[:3] != (0, 0, 0)
    before = pygame.image.tostring(s, "RGB")
    c = level.crates[0]
    deliver(level, player, c, c.answer)
    level.update(0.05)
    s2 = pygame.Surface((960, 640))
    level.render(s2)
    assert pygame.image.tostring(s2, "RGB") != before


def test_render_survives_a_full_playthrough_and_shake():
    level, game, player = make_level()
    s = pygame.Surface((960, 640))
    c = level.crates[0]
    deliver(level, player, c, wrong_bin(c))
    for _ in range(30):
        level.update(0.016)
        level.render(s)
    sort_all(level, player)
    for _ in range(100):
        level.update(0.016)
        level.render(s)


def test_each_bin_label_and_colour_is_distinct():
    assert len(set(f1.BIN_COLOURS.values())) == 4
    level, _, _ = make_level()
    assert set(level.bins) == set(BIN_TYPES)


def test_carried_crate_rides_above_the_players_head_and_moves_with_them():
    level, _, player = make_level()
    c = level.crates[0]
    carry(level, player, c)
    assert c.rect.midbottom == (player.rect.centerx, player.rect.top - 2)
    player.rect.x += 50
    level.update(0.016)
    assert c.rect.centerx == player.rect.centerx


def test_nothing_can_be_picked_up_after_the_floor_is_complete():
    level, _, player = make_level()
    level.complete = True
    c = level.crates[0]
    stand_by(player, c.rect)
    level.handle_event(key(pygame.K_e))
    assert level.carried == {}


def test_messages_use_the_right_article():
    assert [with_article(t) for t in BIN_TYPES] == ["an int", "a str", "a float", "a bool"]
    level, _, player = make_level()
    c = next(c for c in level.crates if c.answer == "int")
    deliver(level, player, c, "int")
    assert "is an int" in level.message
    c2 = next(c for c in level.crates if c.answer == "str")
    deliver(level, player, c2, "int")
    assert "Not an int" in level.message
