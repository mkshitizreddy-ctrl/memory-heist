"""Floor 1 extras: the sweeping camera beam, hidden visitor chips, bell and vending machine."""

import math
import os
import random
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.player import Player
from levels import floor1_lobby as f1
from levels import lobby_extras as X
from levels.floor1_lobby import FloorOneLobby
from systems.scoring import ScoreTracker
from systems.security import SecurityMeter
from ui import theme


@pytest.fixture(autouse=True)
def display_init():
    pygame.init()
    pygame.display.set_mode((960, 640))


def make_level(seed=1, coop=False):
    p1 = Player(100, 100)
    p2 = Player(150, 100) if coop else None
    game = SimpleNamespace(score=ScoreTracker(), security=SecurityMeter(),
                           hints=SimpleNamespace(enabled=True), coop=coop, player2=p2,
                           difficulty={"security_penalty_multiplier": 1.0})
    return FloorOneLobby(player=p1, game=game, seed=seed), game, p1


def press_e(level):
    level.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e))


def into_beam(level, player, t=0.0, dist=200):
    """Put the player on the beam's centre line at time t and set the level clock."""
    level.time = t
    a = level.beam.angle(t)
    ox, oy = level.beam.origin
    player.rect.center = (int(ox + math.cos(a) * dist), int(oy + math.sin(a) * dist))


def hold_still_in_beam(level, player, seconds, t=0.0, dist=200):
    """Stay on the moving beam's line for `seconds`, in 1/60 s steps."""
    for _ in range(round(seconds * 60)):
        into_beam(level, player, level.time if level.time else t, dist)
        level.update(1 / 60)


# --- the beam ------------------------------------------------------------
def test_beam_points_straight_down_at_the_start_and_swings_both_ways():
    b = X.SweepBeam((100, 100))
    assert b.angle(0) == pytest.approx(math.pi / 2)
    assert b.angle(b.period / 4) == pytest.approx(math.pi / 2 + b.swing)
    assert b.angle(3 * b.period / 4) == pytest.approx(math.pi / 2 - b.swing)
    assert b.angle(b.period) == pytest.approx(math.pi / 2)


def test_beam_contains_points_on_its_line_and_not_outside_range_or_angle():
    b = X.SweepBeam((100, 100))
    assert b.contains((100, 300), 0)                       # straight down, in range
    assert not b.contains((100, 100 + b.length + 5), 0)    # too far
    assert b.contains((100, 100 + b.length - 5), 0)
    assert not b.contains((100, 100), 0)                   # the camera itself
    assert not b.contains((100, 20), 0)                    # behind it
    off = b.half_angle + 0.05
    assert not b.contains((100 + 200 * math.sin(off), 100 + 200 * math.cos(off)), 0)
    inside = b.half_angle - 0.05
    assert b.contains((100 + 200 * math.sin(inside), 100 + 200 * math.cos(inside)), 0)
    assert not b.contains((100 + 200 * math.sin(inside), 100 + 200 * math.cos(inside)),
                          b.period / 4)                    # the beam has swung away


def test_beam_polygon_is_a_wedge_from_the_camera():
    b = X.SweepBeam((100, 100))
    poly = b.polygon(0)
    assert poly[0] == (100, 100) and len(poly) == 3
    for x, y in poly[1:]:
        assert math.hypot(x - 100, y - 100) == pytest.approx(b.length)


# --- spotting ------------------------------------------------------------
def test_watch_spots_after_spot_time_in_the_beam_and_not_before():
    w = X.Watch(X.SweepBeam((100, 100)))
    pt = {"p": (100, 300)}
    assert w.update(X.SPOT_TIME - 0.05, 0, pt) is None
    assert w.update(0.1, 0, pt) == "p"
    assert w.spots == 1


def test_leaving_the_beam_resets_the_exposure():
    w = X.Watch(X.SweepBeam((100, 100)))
    w.update(X.SPOT_TIME - 0.05, 0, {"p": (100, 300)})
    w.update(0.1, 0, {"p": (700, 300)})                    # stepped out
    assert w.exposure["p"] == 0
    assert w.update(X.SPOT_TIME - 0.05, 0, {"p": (100, 300)}) is None


def test_watch_waits_out_the_cooldown_and_stops_after_max_spots():
    w = X.Watch(X.SweepBeam((100, 100)))
    pt, away = {"p": (100, 300)}, {"p": (700, 300)}
    assert w.update(X.SPOT_TIME, 0, pt) == "p"
    assert w.update(X.SPOT_COOLDOWN - 0.5, 0, pt) is None   # still cooling down, however long they stand
    assert w.update(0.4, 0, away) is None                   # leaving resets the exposure
    assert w.update(0.2, 0, pt) is None                     # cooldown over, exposure restarts from zero
    assert w.update(X.SPOT_TIME, 0, pt) == "p"
    for _ in range(10):
        w.update(X.SPOT_COOLDOWN, 0, away)
        w.update(X.SPOT_TIME, 0, pt)
    assert w.spots == X.MAX_SPOTS
    w.update(X.SPOT_COOLDOWN, 0, away)
    assert w.update(X.SPOT_TIME * 3, 0, pt) is None


def test_exposure_does_not_build_up_while_the_camera_cools_down():
    w = X.Watch(X.SweepBeam((100, 100)))
    pt = {"p": (100, 300)}
    assert w.update(X.SPOT_TIME, 0, pt) == "p"
    assert w.update(X.SPOT_COOLDOWN - 0.01, 0, pt) is None
    assert w.exposure["p"] == 0
    assert w.update(0.02, 0, pt) is None                     # cooldown over, but a fresh start
    assert w.update(X.SPOT_TIME - 0.05, 0, pt) is None
    assert w.update(0.1, 0, pt) == "p"


def test_danger_rises_in_the_beam_and_is_zero_outside_or_cooling_down():
    w = X.Watch(X.SweepBeam((100, 100)))
    assert w.danger() == 0
    w.update(X.SPOT_TIME / 2, 0, {"p": (100, 300)})
    assert w.danger() == pytest.approx(0.5)
    w.update(X.SPOT_TIME, 0, {"p": (100, 300)})            # spotted: cooling down
    assert w.danger() == 0


def test_danger_stops_at_one_once_the_camera_has_given_up():
    w = X.Watch(X.SweepBeam((100, 100)))
    w.spots = X.MAX_SPOTS
    w.update(5.0, 0, {"p": (100, 300)})
    assert w.danger() == 1.0


def test_two_players_are_tracked_separately():
    w = X.Watch(X.SweepBeam((100, 100)))
    w.update(0.3, 0, {"a": (100, 300), "b": (700, 300)})
    assert w.exposure["a"] == pytest.approx(0.3) and w.exposure["b"] == 0


def test_being_spotted_costs_score_and_never_security():
    level, game, p = make_level()
    game.score.add(50)
    shakes = []
    level.shake.add = lambda amount: shakes.append(amount)
    hold_still_in_beam(level, p, X.SPOT_TIME + 0.2)
    assert shakes == [0.3]
    assert game.score.get_score() == 50 - X.SPOT_PENALTY
    assert game.security.level == 0 and game.security.max_level == 100
    assert "spotted" in level.message.lower()


def test_walking_across_the_beam_quickly_is_safe():
    level, game, p = make_level()
    game.score.add(50)
    level.time = 0.0
    ox, oy = level.beam.origin
    for i in range(30):                                    # 0.5 s sprint through the wedge
        p.rect.center = (int(ox - 80 + i * 6), int(oy + 200))
        level.update(1 / 60)
    assert game.score.get_score() == 50


def test_no_more_spotting_once_the_floor_is_done():
    level, game, p = make_level()
    game.score.add(50)
    level.complete = True
    hold_still_in_beam(level, p, 1.5)
    assert game.score.get_score() == 50


# --- visitor chips -------------------------------------------------------
def test_every_possible_chip_spot_is_open_floor():
    level, _, _ = make_level()
    for spot in X.CHIP_SPOTS:
        assert not level._spot_blocked(spot), spot
        assert not level.room_map.blocked(pygame.Rect(spot[0] * 32 + 7, spot[1] * 32 + 7, 18, 18))


def test_three_distinct_chips_are_hidden_and_the_layout_follows_the_seed():
    level, _, _ = make_level(seed=5)
    assert len(level.chips) == X.CHIPS_HIDDEN
    assert len({c.rect.center for c in level.chips}) == X.CHIPS_HIDDEN
    again, _, _ = make_level(seed=5)
    assert [c.rect.center for c in again.chips] == [c.rect.center for c in level.chips]
    layouts = {tuple(c.rect.center for c in make_level(seed=s)[0].chips) for s in range(12)}
    assert len(layouts) > 1


def test_chips_do_not_change_where_the_crates_start():
    level, _, _ = make_level(seed=3)
    rng = random.Random(3)
    spots = list(f1.CRATE_SPOTS)
    rng.shuffle(spots)
    values = [c.value for c in level.crates]
    assert values == [v for v in f1.pick_crates("medium", rng)]
    assert [c.home.topleft for c in level.crates] == [(c * 32 + 2, r * 32 + 2) for c, r in spots[:6]]


def test_walking_over_a_chip_takes_it_and_scores():
    level, game, p = make_level()
    chip = level.chips[0]
    p.rect.center = chip.rect.center
    level.update(0.016)
    assert chip.taken and level.chips_found == 1
    assert game.score.get_score() == X.CHIP_POINTS
    assert "1/3" in level.message
    level.update(0.016)
    assert game.score.get_score() == X.CHIP_POINTS         # taken once only


def test_the_last_chip_pays_the_bonus():
    level, game, p = make_level()
    for chip in level.chips:
        p.rect.center = chip.rect.center
        level.update(0.016)
    assert level.chips_found == 3
    assert game.score.get_score() == 3 * X.CHIP_POINTS + X.CHIP_BONUS
    assert "all" in level.message.lower()


def test_either_player_can_take_a_chip_in_coop():
    level, game, p1 = make_level(coop=True)
    p2 = game.player2
    p2.rect.center = level.chips[1].rect.center
    p1.rect.center = (40, 400)
    level.update(0.016)
    assert level.chips[1].taken and not level.chips[0].taken


# --- bell and vending machine -------------------------------------------
def test_e_by_the_desk_rings_the_bell_and_the_receptionist_answers():
    level, _, p = make_level()
    for c in level.crates:
        c.rect.topleft = (40, 120)                         # no crate near the desk
    p.rect.midtop = (level.desk.centerx, level.desk.bottom + 2)
    press_e(level)
    assert level.receptionist.speech and level._bell_rings == 1
    first = level.receptionist.speech
    press_e(level)
    assert level._bell_rings == 2 and level.receptionist.speech != first


def test_vending_machine_pays_once_then_is_sold_out():
    level, game, p = make_level()
    for c in level.crates:
        c.rect.topleft = (40, 120)
    p.rect.midright = (level.vending.left - 2, level.vending.centery)
    press_e(level)
    assert game.score.get_score() == X.VENDING_POINTS and level.vending_used
    assert level.message == X.VENDING_LINE
    press_e(level)
    assert game.score.get_score() == X.VENDING_POINTS
    assert level.message == X.VENDING_EMPTY


def test_a_crate_in_reach_wins_over_the_props():
    level, game, p = make_level()
    crate = level.crates[0]
    crate.rect.midtop = (level.desk.centerx, level.desk.bottom + 6)
    p.rect.midtop = (level.desk.centerx, level.desk.bottom + 2)
    press_e(level)
    assert level.carried.get(id(p)) is crate and level._bell_rings == 0


def test_e_in_an_empty_corner_does_nothing():
    level, game, p = make_level()
    for c in level.crates:
        c.rect.topleft = (300, 400)
    p.rect.center = (60, 130)
    before = level.message
    press_e(level)
    assert not level.carried and level._bell_rings == 0 and not level.vending_used
    assert level.message == before


# --- drawing -------------------------------------------------------------
def test_beam_and_chips_draw_and_the_beam_reddens_with_danger():
    calm = X.draw_beam(pygame.Surface((960, 640), pygame.SRCALPHA), X.SweepBeam((480, 80)), 0, 0)
    hot = X.draw_beam(pygame.Surface((960, 640), pygame.SRCALPHA), X.SweepBeam((480, 80)), 0, 1)
    a, b = calm.get_at((480, 200)), hot.get_at((480, 200))
    assert a.a > 0 and b.a > a.a and b.r > a.r and b.g < a.g
    assert calm.get_at((20, 600)).a == 0
    surf = pygame.Surface((100, 100))
    surf.fill((0, 0, 0))
    X.draw_chip(surf, X.Chip((1, 1)), 0.0)
    assert any(surf.get_at((x, y))[:3] != (0, 0, 0) for x in range(100) for y in range(100))


def test_render_shows_chips_counter_and_survives_a_full_frame_loop():
    level, game, p = make_level()
    surf = pygame.Surface((960, 640))
    level.render(surf)
    level.chips_found = 2
    level.render(surf)
    into_beam(level, p)
    for _ in range(60):
        level.update(1 / 60)
        level.render(surf)
    level.complete = True
    level.render(surf)


def _beam_pixel(level):
    ox, oy = level.beam.origin
    return int(ox), int(oy + 220)


def test_the_beam_disappears_once_the_floor_is_done():
    level, _, _ = make_level()
    level.time = 0.0
    surf, done = pygame.Surface((960, 640)), pygame.Surface((960, 640))
    level.render(surf)
    level.complete = True
    level.render(done)
    assert surf.get_at(_beam_pixel(level)) != done.get_at(_beam_pixel(level))


def test_a_taken_chip_is_no_longer_drawn():
    level, _, _ = make_level()
    chip = level.chips[0]
    before, after = pygame.Surface((960, 640)), pygame.Surface((960, 640))
    level.render(before)
    chip.taken = True
    level.render(after)
    assert before.get_at(chip.rect.center) != after.get_at(chip.rect.center)


# --- the NovaCorp look and sound on Floor 1 --------------------------------
class Recorder:
    def __init__(self):
        self.played = []

    def play(self, name):
        self.played.append(name)


def with_audio(level, game):
    game.audio = Recorder()
    return game.audio.played


def test_cabinets_and_cooler_are_solid_and_inside_the_room():
    level, _, _ = make_level()
    room = pygame.Rect(0, 0, 960, 640)
    for rect in level.cabinets + [level.cooler]:
        assert level.room_map.blocked(rect) and room.contains(rect)
        assert rect in level.props
    assert len(level.cabinets) == 2


def test_the_exit_and_every_crate_spot_stay_reachable_around_the_new_furniture():
    level, _, _ = make_level()
    tile = 32
    blocked = lambda c, r: level.room_map.blocked(pygame.Rect(c * tile + 4, r * tile + 4, 24, 24))
    start = (3, 4)
    seen, todo = {start}, [start]
    while todo:
        c, r = todo.pop()
        for nc, nr in ((c + 1, r), (c - 1, r), (c, r + 1), (c, r - 1)):
            if (nc, nr) not in seen and 0 <= nc < 30 and 0 <= nr < 20 and not blocked(nc, nr):
                seen.add((nc, nr))
                todo.append((nc, nr))
    for col, row in f1.CRATE_SPOTS + list(X.CHIP_SPOTS):
        assert (col, row) in seen, (col, row)
    assert (27, 10) in seen                                # in front of the exit door


def test_the_pa_chimes_once_when_it_makes_an_announcement():
    level, game, _ = make_level()
    played = with_audio(level, game)
    for _ in range(int(level.pa.FIRST_AT * 60) - 5):
        level.update(1 / 60)
    assert "chime" not in played
    for _ in range(10):
        level.update(1 / 60)
    assert played.count("chime") == 1 and level.pa.caption in f1.PA_LINES
    for _ in range(120):
        level.update(1 / 60)
    assert played.count("chime") == 1


def test_the_caption_is_drawn_only_while_the_pa_speaks():
    level, _, _ = make_level()
    quiet, loud = pygame.Surface((960, 640)), pygame.Surface((960, 640))
    level.render(quiet)
    level.pa.update(level.pa.FIRST_AT)
    level.pa.update(1.0)
    level.render(loud)
    area = pygame.Rect(f1.PA_CAPTION, (150, 18))
    assert pygame.image.tostring(quiet.subsurface(area), "RGB") != pygame.image.tostring(loud.subsurface(area), "RGB")


def test_each_prop_and_hazard_plays_its_own_sound():
    level, game, p = make_level()
    played = with_audio(level, game)
    for c in level.crates:
        c.rect.topleft = (40, 120)
    p.rect.midtop = (level.desk.centerx, level.desk.bottom + 2)
    press_e(level)
    p.rect.midright = (level.vending.left - 2, level.vending.centery)
    press_e(level)
    p.rect.center = level.chips[0].rect.center
    level.update(0.016)
    hold_still_in_beam(level, p, X.SPOT_TIME + 0.2)
    for name in ("bell", "vending", "chip", "alarm"):
        assert name in played, name
    assert "click" not in played and "wrong" not in played


def test_the_background_is_graded_and_has_posters_on_the_left_wall():
    level, _, _ = make_level()
    calls = []
    import levels.novacorp_style as nc
    real = nc.grade
    nc.grade = lambda *a, **k: calls.append(1) or real(*a, **k)
    try:
        level._background = None
        level.render(pygame.Surface((960, 640)))
    finally:
        nc.grade = real
    assert calls == [1]
    poster = level._background.get_at((30, 10 * 32 + 20))[:3]
    assert poster[0] > poster[2] + 15                       # a red-brown card, not wall grey


# --- the reception phone ------------------------------------------------------------
def test_the_phone_rings_on_schedule_then_gets_answered():
    phone = X.Phone()
    assert phone.update(X.PHONE_FIRST_AT - 0.1) is None and not phone.is_ringing
    assert phone.update(0.2) == "ring" and phone.is_ringing
    seen = []
    for _ in range(int(X.RING_TIME / 0.1) + 5):
        seen.append(phone.update(0.1))
    assert "answer" in seen and not phone.is_ringing
    assert phone.calls == 1


def test_the_phone_rings_a_second_time_halfway_through():
    phone = X.Phone()
    phone.update(X.PHONE_FIRST_AT)
    events = [phone.update(0.1) for _ in range(int(X.RING_TIME / 0.1) + 3)]
    assert events.count("ring") == 1                     # the start was returned above, the midpoint here
    assert events.index("ring") * 0.1 == pytest.approx(X.RING_TIME / 2, abs=0.2)


def test_the_phone_rings_again_later_and_lines_cycle():
    phone = X.Phone()
    lines = []
    t = 0.0
    while len(lines) < len(X.CALL_LINES) + 1 and t < 600:
        event = phone.update(0.1)
        t += 0.1
        if event == "answer":
            lines.append(phone.line())
    assert lines[:len(X.CALL_LINES)] == list(X.CALL_LINES)
    assert lines[len(X.CALL_LINES)] == X.CALL_LINES[0]
    assert all(len(line) <= 30 for line in X.CALL_LINES)


def test_the_phone_is_drawn_and_shows_ring_arcs_only_while_ringing():
    desk = pygame.Rect(384, 480, 192, 32)
    quiet, loud = pygame.Surface((640, 640)), pygame.Surface((640, 640))
    X.draw_phone(quiet, desk, False, 0.0)
    X.draw_phone(loud, desk, True, 0.0)
    blank = pygame.Surface((640, 640))
    assert pygame.image.tobytes(quiet, "RGB") != pygame.image.tobytes(blank, "RGB")
    assert pygame.image.tobytes(quiet, "RGB") != pygame.image.tobytes(loud, "RGB")


def test_the_receptionist_takes_the_call_in_the_real_level():
    level, game, p1 = make_level()
    sounds = []
    level._sfx = sounds.append
    level.phone.clock = 0.05
    level._update_extras(0.1)
    assert sounds == ["phone"] and level.phone.is_ringing
    for _ in range(40):
        level._update_extras(0.1)
    assert level.phone.calls == 1
    assert level.receptionist.speech == X.CALL_LINES[0]


def test_a_visitor_badge_is_drawn_as_a_card_with_a_teal_stripe_and_a_clip():
    surf = pygame.Surface((80, 80))
    surf.fill((20, 20, 30))
    chip = X.Chip((1, 1))
    chip.rect.center = (40, 40)
    X.draw_chip(surf, chip, 0.0)
    colours = {tuple(surf.get_at((x, y)))[:3] for x in range(28, 52) for y in range(26, 54)}
    assert tuple(theme.PAPER)[:3] in colours             # the white card
    assert any(c[1] > 150 and c[2] > 150 and c[0] < 130 for c in colours)   # the teal stripe


# ---- purposeful props: manifests, cooler, banter ----------------------------------

def _lobby():
    from tests.test_floor1_lobby import make_level
    return make_level()[0]


def test_reading_a_manifest_shows_the_next_chute_rule():
    from levels import floor1_lobby as f1
    level = _lobby()
    level._read_manifest()
    assert level.message.endswith(f1.HINTS[f1.BIN_TYPES[0]])
    level._read_manifest()
    assert level.message.endswith(f1.HINTS[f1.BIN_TYPES[1]])


def test_manifests_are_sealed_when_hints_are_off():
    level = _lobby()
    level.game = type("G", (), {"hints": type("H", (), {"enabled": False})()})()
    level._read_manifest()
    from levels import lobby_extras as le
    assert level.message == le.MANIFEST_OFF


def test_guard_and_receptionist_banter_when_he_passes_her_desk():
    level = _lobby()
    level.guard.rect.center = level.receptionist.rect.center
    level._banter_wait = 0.0
    level._banter(0.1)
    assert level.guard.speech and level.receptionist.speech
    wait = level._banter_wait
    level._banter(0.1)
    assert level._banters == 1 and level._banter_wait < wait   # cooldown, no repeat
