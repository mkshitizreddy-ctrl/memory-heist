"""NPCs: sprites, patrol, noticing the player, speech, and drawing."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core import character
from core.npc import NOTICE_HYSTERESIS, NOTICE_RANGE, NPC
from core.npc_sprites import KINDS, make_npc_frames
from ui.fonts import ui_font
from ui.kit import draw_speech_bubble


@pytest.fixture(autouse=True)
def display():
    pygame.init()
    pygame.display.set_mode((64, 64))


def run(npc, seconds, fps=60):
    for _ in range(int(seconds * fps)):
        npc.update(1 / fps)


def pixels(surface):
    return pygame.image.tostring(surface, "RGBA")


# --- sprites -----------------------------------------------------------------

@pytest.mark.parametrize("kind", KINDS)
def test_every_kind_has_the_frames_characters_need(kind):
    frames = make_npc_frames(kind)
    assert len(frames["walk"]) == 4
    for image in [frames["idle"], *frames["walk"]]:
        assert image.get_size() == (32, 32)
    # the walk cycle really moves the legs
    assert pixels(frames["walk"][0]) != pixels(frames["walk"][2])


def test_the_people_look_different_from_each_other_and_from_the_heroes():
    from core.hero_sprites import make_hero_frames
    seen = {pixels(make_npc_frames(k)["idle"]) for k in KINDS}
    seen |= {pixels(make_hero_frames(h)["idle"]) for h in ("ghost", "echo")}
    assert len(seen) == len(KINDS) + 2


def test_receptionist_blinks_but_the_guard_in_sunglasses_does_not():
    rec = make_npc_frames("receptionist")
    assert pixels(rec["blink"]) != pixels(rec["idle"])
    assert "blink" not in make_npc_frames("guard")


def test_unknown_kind_is_refused():
    with pytest.raises(ValueError):
        make_npc_frames("janitor")


# --- patrol -----------------------------------------------------------------

def test_a_patrol_starts_at_its_first_waypoint():
    npc = NPC("guard", (500, 500), patrol=[(100, 200), (300, 200)])
    assert npc.rect.topleft == (100, 200)


def test_walks_toward_the_next_waypoint_at_its_speed():
    npc = NPC("guard", (0, 0), patrol=[(0, 0), (400, 0)], speed=100)
    run(npc, 1.0)
    assert 98 <= npc.rect.x <= 102
    assert npc.rect.y == 0
    assert npc.moving
    assert not npc.facing_left


def test_waits_at_each_end_then_turns_back():
    npc = NPC("guard", (0, 0), patrol=[(0, 0), (50, 0)], speed=100, pause=1.0)
    run(npc, 0.5)                       # arrives at x=50 exactly
    assert npc.rect.x == 50
    run(npc, 0.5)
    assert npc.rect.x == 50 and not npc.moving    # pausing
    run(npc, 0.4)
    assert npc.rect.x == 50                       # still pausing (0.9s of 1.0s)
    run(npc, 0.4)
    assert npc.rect.x < 50 and npc.facing_left    # walking back, facing left
    assert npc.moving


def test_three_point_route_goes_out_and_back_through_the_middle():
    npc = NPC("guard", (0, 0), patrol=[(0, 0), (100, 0), (100, 100)], speed=1000, pause=0.0)
    visited = []
    for _ in range(40):
        npc.update(0.1)
        if not visited or visited[-1] != npc.rect.topleft:
            visited.append(npc.rect.topleft)
    stops = [p for p in visited if p in {(0, 0), (100, 0), (100, 100)}]
    assert stops[:5] == [(100, 0), (100, 100), (100, 0), (0, 0), (100, 0)]


@pytest.mark.parametrize("dt", [0.61, 0.9, 2.0, 10.0])
def test_a_long_time_step_never_overshoots_a_waypoint(dt):
    """Even a step only slightly longer than needed must stop exactly on the point."""
    npc = NPC("guard", (0, 0), patrol=[(0, 0), (60, 0)], speed=100, pause=5.0)
    npc.update(dt)
    assert npc.rect.x == 60


def test_diagonal_movement_keeps_the_same_speed():
    npc = NPC("guard", (0, 0), patrol=[(0, 0), (300, 400)], speed=100)
    run(npc, 1.0)
    assert abs(((npc.rect.x ** 2 + npc.rect.y ** 2) ** 0.5) - 100) < 2


def test_a_stationary_npc_never_moves_but_keeps_breathing():
    npc = NPC("receptionist", (200, 300))
    run(npc, 3.0)
    assert npc.rect.topleft == (200, 300)
    assert not npc.moving
    assert npc.idle_time == pytest.approx(3.0, abs=0.05)


def test_walking_resets_the_idle_clock():
    npc = NPC("guard", (0, 0), patrol=[(0, 0), (400, 0)], speed=100)
    npc.idle_time = 2.0
    npc.update(0.1)
    assert npc.idle_time == 0.0 and npc.anim_time > 0


def test_negative_dt_is_ignored():
    npc = NPC("guard", (0, 0), patrol=[(0, 0), (400, 0)], speed=100)
    npc.update(-5.0)
    assert npc.rect.topleft == (0, 0)


# --- noticing and reacting ---------------------------------------------------

def test_notice_fires_once_as_the_player_arrives():
    npc = NPC("receptionist", (200, 200), facing_left=False)
    near = pygame.Rect(200 - 40, 200, 32, 32)
    assert npc.notice(near, "p1") is True
    assert npc.notice(near, "p1") is False        # not again while they stay


def test_notice_ignores_a_player_out_of_range():
    npc = NPC("receptionist", (200, 200))
    far = pygame.Rect(200 + NOTICE_RANGE + 60, 200, 32, 32)
    assert npc.notice(far, "p1") is False


def test_notice_fires_again_after_the_player_walks_away_and_returns():
    npc = NPC("receptionist", (200, 200))
    near = pygame.Rect(180, 200, 32, 32)
    far = pygame.Rect(200 + NOTICE_RANGE + NOTICE_HYSTERESIS + 40, 200, 32, 32)
    assert npc.notice(near, "p1")
    assert not npc.notice(far, "p1")
    assert npc.notice(near, "p1")


def test_hovering_at_the_edge_of_range_does_not_spam():
    npc = NPC("receptionist", (200, 200))
    inside = pygame.Rect(200 + NOTICE_RANGE - 4, 200, 32, 32)
    edge = pygame.Rect(200 + NOTICE_RANGE + NOTICE_HYSTERESIS // 2, 200, 32, 32)
    assert npc.notice(inside, "p1")
    assert not npc.notice(edge, "p1")
    assert not npc.notice(inside, "p1")


def test_two_players_are_noticed_separately():
    npc = NPC("receptionist", (200, 200))
    near = pygame.Rect(180, 200, 32, 32)
    assert npc.notice(near, "p1")
    assert npc.notice(near, "p2")


def test_noticing_turns_the_npc_toward_the_player():
    npc = NPC("receptionist", (200, 200), facing_left=False)
    npc.notice(pygame.Rect(120, 200, 32, 32), "p1")
    assert npc.facing_left
    npc.notice(pygame.Rect(280, 200, 32, 32), "p2")
    assert not npc.facing_left


def test_alert_stops_the_patrol_then_it_resumes():
    npc = NPC("guard", (0, 0), patrol=[(0, 0), (400, 0)], speed=100, pause=0.0)
    run(npc, 0.5)
    here = npc.rect.x
    npc.alert(pygame.Rect(-100, 0, 32, 32), 1.0)
    assert npc.facing_left
    run(npc, 0.9)
    assert npc.rect.x == here and not npc.moving
    run(npc, 0.5)
    assert npc.rect.x > here


# --- speech ------------------------------------------------------------------

def test_speech_shows_then_expires():
    npc = NPC("receptionist", (0, 0))
    npc.say("Hello", seconds=1.0)
    assert npc.speech == "Hello"
    run(npc, 0.9)
    assert npc.speech == "Hello"
    run(npc, 0.2)
    assert npc.speech is None


def test_a_new_line_replaces_the_old_one_and_restarts_the_timer():
    npc = NPC("receptionist", (0, 0))
    npc.say("One", seconds=1.0)
    run(npc, 0.8)
    npc.say("Two", seconds=1.0)
    run(npc, 0.5)
    assert npc.speech == "Two"


# --- drawing -----------------------------------------------------------------

def test_draw_matches_the_shared_character_pose():
    npc = NPC("receptionist", (100, 100))
    got = pygame.Surface((200, 200), pygame.SRCALPHA)
    npc.draw(got)
    image, lift = character.pose_for(npc.frames, npc.moving, npc.anim_time, npc.idle_time)
    want = pygame.Surface((200, 200), pygame.SRCALPHA)
    character.draw_character(want, npc.rect, image, lift, npc.facing_left)
    assert pixels(got) == pixels(want)


def test_speech_is_drawn_only_when_there_is_a_line_and_a_font():
    npc = NPC("receptionist", (100, 100))
    font = ui_font(20)

    def draw(speaking, with_font):
        npc.speech = "Hi there" if speaking else None
        surface = pygame.Surface((300, 200), pygame.SRCALPHA)
        npc.draw(surface, font if with_font else None)
        return pixels(surface)

    silent = draw(False, True)
    assert draw(True, False) == silent        # no font: no bubble
    assert draw(True, True) != silent         # bubble appears


def test_speech_bubble_sits_above_the_speaker_and_stays_on_screen():
    surface = pygame.Surface((300, 200), pygame.SRCALPHA)
    font = ui_font(20)
    anchor = pygame.Rect(140, 120, 32, 32)
    box = draw_speech_bubble(surface, font, "Welcome to NovaCorp.", anchor)
    assert box.bottom <= anchor.top
    corner = pygame.Rect(0, 4, 32, 32)         # speaker at the very top-left
    box = draw_speech_bubble(surface, font, "Welcome to NovaCorp.", corner)
    assert surface.get_rect().contains(box)


STAFF = ("cleaner", "engineer", "sysadmin", "curator")


def test_the_new_staff_are_faceless_and_never_blink():
    from core.npc_sprites import BLINK_COLOURS
    for kind in STAFF:
        assert kind in KINDS and BLINK_COLOURS[kind] == {}
        assert "blink" not in make_npc_frames(kind)


def test_the_new_staff_have_their_own_distinct_voices():
    from systems.voice import DEFAULT_VOICE, VOICES
    voices = [VOICES[k] for k in STAFF]
    assert len(set(voices)) == len(STAFF) and DEFAULT_VOICE not in voices
    assert len({VOICES[k] for k in VOICES}) == len(VOICES)
