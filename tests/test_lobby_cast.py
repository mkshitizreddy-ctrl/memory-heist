"""The lobby's people: where they stand, what they say, how they react."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

from types import SimpleNamespace

import pygame
import pytest

import levels.floor1_lobby as f1
from core.player import Player
from core.tilemap import TILE
from levels.floor1_lobby import BIN_TYPES, FloorOneLobby
from systems.scoring import ScoreTracker
from systems.security import SecurityMeter


@pytest.fixture(autouse=True)
def display_init():
    pygame.init()
    pygame.display.set_mode((960, 640))


def make_level(coop=False):
    game = SimpleNamespace(
        score=ScoreTracker(), security=SecurityMeter(), hints=SimpleNamespace(enabled=True),
        coop=coop, player2=None, difficulty={"security_penalty_multiplier": 1.0})
    player = Player(100, 100)
    if coop:
        game.player2 = Player(120, 100)
    return FloorOneLobby(player=player, game=game, seed=1), game, player


def key(k):
    return pygame.event.Event(pygame.KEYDOWN, key=k)


def go_to(player, npc, dx=-60, dy=0):
    player.rect.center = (npc.rect.centerx + dx, npc.rect.centery + dy)


def step(level, seconds=0.1, fps=60):
    for _ in range(int(seconds * fps)):
        level.update(1 / fps)


def deliver(level, player, crate, bin_type):
    player.rect.midtop = (crate.rect.centerx, crate.rect.bottom + 2)
    level.handle_event(key(pygame.K_e))
    player.rect.midtop = (level.bins[bin_type].centerx, level.bins[bin_type].bottom + 2)
    level.update(0.016)
    level.handle_event(key(pygame.K_e))


def far_from_everyone(level, player):
    player.rect.topleft = (100, 100)
    step(level, 0.1)
    for npc in level.npcs:
        npc.speech = None


# --- placement ---------------------------------------------------------------

def test_the_lobby_has_a_receptionist_a_guard_and_a_cleaner():
    level, _, _ = make_level()
    assert [n.kind for n in level.npcs] == ["receptionist", "guard", "cleaner"]


def test_the_receptionist_stands_behind_the_desk_on_open_floor():
    level, _, _ = make_level()
    r = level.receptionist.rect
    assert not level.room_map.blocked(r)
    assert r.top >= level.desk.bottom                      # south of the desk
    assert level.desk.left <= r.centerx <= level.desk.right


def test_the_whole_guard_patrol_is_clear_floor():
    level, _, _ = make_level()
    guard = level.guard
    points = f1.GUARD_ROUTE
    for (c1, r1), (c2, r2) in zip(points, points[1:] + points[:1]):
        for i in range(21):
            t = i / 20
            x = (c1 + (c2 - c1) * t) * TILE
            y = (r1 + (r2 - r1) * t) * TILE
            assert not level.room_map.blocked(pygame.Rect(round(x), round(y), 32, 32)), (x, y)
    assert guard.rect.topleft == (points[0][0] * TILE, points[0][1] * TILE)


def test_the_guard_does_not_start_on_the_player_spawn():
    level, _, player = make_level()
    assert not level.guard.rect.colliderect(pygame.Rect(100, 100, 32, 32))


def test_people_never_block_the_player():
    level, _, _ = make_level()
    npc_rects = [n.rect for n in level.npcs]
    assert not any(level.room_map.blocked(r) for r in npc_rects)
    probe = level.guard.rect.copy()
    assert not level.room_map.blocked(probe)               # NPCs are not in the collision map
    assert all(n.rect not in level.props for n in level.npcs)


# --- life --------------------------------------------------------------------

def test_the_guard_patrols_while_the_level_runs():
    level, _, _ = make_level()
    start = level.guard.rect.topleft
    step(level, 2.0)
    assert level.guard.rect.topleft != start


def test_the_receptionist_stays_put():
    level, _, _ = make_level()
    start = level.receptionist.rect.topleft
    step(level, 3.0)
    assert level.receptionist.rect.topleft == start


# --- reactions ---------------------------------------------------------------

def test_receptionist_greets_you_as_you_arrive_but_not_while_you_stand_there():
    level, _, player = make_level()
    go_to(player, level.receptionist, dy=-50)
    step(level, 0.05)
    assert level.receptionist.speech == f1.GREETINGS[0]
    level.receptionist.speech = None
    step(level, 0.5)
    assert level.receptionist.speech is None               # no repeat while you stay


def test_each_return_visit_gets_the_next_greeting():
    level, _, player = make_level()
    said = []
    for _ in range(len(f1.GREETINGS) + 1):
        go_to(player, level.receptionist, dy=-50)
        step(level, 0.05)
        said.append(level.receptionist.speech)
        far_from_everyone(level, player)
        step(level, 0.2)
    assert said == [f1.GREETINGS[i % len(f1.GREETINGS)] for i in range(len(said))]


def test_the_receptionist_turns_to_face_you():
    level, _, player = make_level()
    level.receptionist.facing_left = True
    player.rect.center = (level.receptionist.rect.centerx + 70, level.receptionist.rect.centery)
    step(level, 0.05)
    assert level.receptionist.facing_left is False


def test_the_guard_speaks_when_you_get_close():
    level, _, player = make_level()
    level.guard.speech = None
    player.rect.center = (level.guard.rect.centerx, level.guard.rect.centery - 50)
    step(level, 0.05)
    assert level.guard.speech in f1.GUARD_LINES


def test_a_wrong_answer_makes_the_guard_stop_and_scold():
    level, _, player = make_level()
    step(level, 0.5)                                       # guard is walking
    far_from_everyone(level, player)
    crate = level.crates[0]
    bad = next(t for t in BIN_TYPES if t != crate.answer)
    deliver(level, player, crate, bad)
    assert level.guard.speech == f1.SCOLD
    before = level.guard.rect.topleft
    step(level, 1.0)
    assert level.guard.rect.topleft == before              # held still, looking at you


def test_a_correct_answer_does_not_make_the_guard_scold():
    level, _, player = make_level()
    far_from_everyone(level, player)
    crate = level.crates[0]
    deliver(level, player, crate, crate.answer)
    assert level.guard.speech != f1.SCOLD


def test_the_receptionist_praises_every_other_correct_sort():
    level, _, player = make_level()
    praised = []
    for crate in level.crates[:4]:
        far_from_everyone(level, player)
        deliver(level, player, crate, crate.answer)
        praised.append(level.receptionist.speech in f1.PRAISE)
    assert praised == [True, False, True, False]


def test_the_receptionist_says_goodbye_when_the_floor_is_cleared():
    level, _, _ = make_level()
    level._finish()
    assert level.receptionist.speech == f1.FAREWELL


def test_nobody_changes_the_score_or_security_by_talking():
    level, game, player = make_level()
    go_to(player, level.receptionist, dy=-50)
    step(level, 1.0)
    go_to(player, level.guard, dx=0, dy=-50)
    step(level, 1.0)
    assert game.score.get_score() == 0 and game.security.level == 0


def test_player_two_is_noticed_separately_in_coop():
    level, _, p1 = make_level(coop=True)
    p2 = level.game.player2
    go_to(p1, level.receptionist, dy=-50)
    p2.rect.topleft = (100, 300)
    step(level, 0.05)
    assert level.receptionist.speech == f1.GREETINGS[0]
    level.receptionist.speech = None
    go_to(p2, level.receptionist, dx=60, dy=0)
    step(level, 0.05)
    assert level.receptionist.speech == f1.GREETINGS[1]


# --- drawing -----------------------------------------------------------------

def test_the_people_are_drawn_into_the_level():
    level, _, _ = make_level()
    with_people = pygame.Surface((960, 640))
    level.render(with_people)
    level.npcs = []
    without = pygame.Surface((960, 640))
    level.render(without)
    area = level.receptionist.rect.inflate(8, 8)
    assert pygame.image.tostring(with_people.subsurface(area), "RGB") != \
        pygame.image.tostring(without.subsurface(area), "RGB")


def test_a_speech_bubble_reaches_the_screen():
    level, _, _ = make_level()
    plain = pygame.Surface((960, 640))
    level.render(plain)
    level.receptionist.say("Hello there")
    spoken = pygame.Surface((960, 640))
    level.render(spoken)
    above = pygame.Rect(level.receptionist.rect.x - 40, level.receptionist.rect.y - 50, 120, 40)
    assert pygame.image.tostring(plain.subsurface(above), "RGB") != \
        pygame.image.tostring(spoken.subsurface(above), "RGB")


# --- the cleaner -------------------------------------------------------------

def test_the_whole_cleaner_route_is_clear_floor_and_starts_at_its_first_point():
    level, _, _ = make_level()
    points = f1.CLEANER_ROUTE
    for (c1, r1), (c2, r2) in zip(points, points[1:] + points[:1]):
        for i in range(21):
            t = i / 20
            x, y = (c1 + (c2 - c1) * t) * TILE, (r1 + (r2 - r1) * t) * TILE
            assert not level.room_map.blocked(pygame.Rect(round(x), round(y), 32, 32)), (x, y)
    assert level.cleaner.rect.topleft == (points[0][0] * TILE, points[0][1] * TILE)


def test_the_cleaner_mops_back_and_forth_slower_than_the_guard():
    level, _, _ = make_level()
    assert level.cleaner.speed < level.guard.speed
    xs = set()
    for _ in range(60 * 14):
        level.update(1 / 60)
        xs.add(level.cleaner.rect.x)
    lo, hi = f1.CLEANER_ROUTE[0][0] * TILE, f1.CLEANER_ROUTE[1][0] * TILE
    assert min(xs) == lo and max(xs) == hi


def test_the_cleaner_mutters_a_line_when_a_player_comes_close():
    level, _, player = make_level()
    player.rect.center = level.cleaner.rect.center
    level.update(0.016)
    assert level.cleaner.speech in f1.CLEANER_LINES
    first = level.cleaner.speech
    player.rect.center = (900, 120)
    for _ in range(120):
        level.update(1 / 60)
    player.rect.center = level.cleaner.rect.center
    level.update(0.016)
    assert level.cleaner.speech in f1.CLEANER_LINES and level.cleaner.speech != first


def test_the_cleaner_mops_a_long_straight_line_in_front_of_the_desk_side():
    level, _, _ = make_level()
    (c1, r1), (c2, r2) = f1.CLEANER_ROUTE
    assert r1 == r2 and c2 - c1 >= 5                       # a good long stretch of floor
    assert c2 * TILE + 32 <= level.desk.left               # stops short of the desk
