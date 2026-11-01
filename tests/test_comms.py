import math
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
import pytest

from core.comms import COMMS, DANGER_RATIO, MAX_LINE, MOMENTS, line_for
from core.level_manager import LEVEL_ORDER
from ui.comms import CommsFeed


@pytest.fixture(autouse=True)
def display():
    pygame.init()
    pygame.display.set_mode((960, 640))


def feed(**kw):
    return CommsFeed(**kw)


def texts(f):
    return [b.typer.text for _, b in f.queue]


def start(f, level="level1", sec=0, gates=0):
    f.observe("playing", level, sec, 10, gates)


# --- script data ---------------------------------------------------------
def test_every_floor_has_every_moment():
    for lvl in LEVEL_ORDER:
        for m in MOMENTS:
            assert line_for(lvl, m) is not None, (lvl, m)


def test_lines_fit_the_box_and_speakers_are_known():
    for lvl, moments in COMMS.items():
        for m, (speaker, lines) in moments.items():
            assert speaker in ("Echo", "WARDEN")
            assert lines
            assert all(0 < len(t) <= MAX_LINE + 12 for t in lines), (lvl, m)


def test_mistake_lines_cycle_and_unknown_is_none():
    first = line_for("level1", "mistake", 0)
    n = len(COMMS["level1"]["mistake"][1])
    assert line_for("level1", "mistake", n) == first
    assert line_for("level1", "mistake", 1) != first
    assert line_for("nope", "enter") is None
    assert line_for("level1", "nope") is None


# --- observer ------------------------------------------------------------
def test_entering_a_level_queues_echo_intro():
    f = feed()
    start(f)
    assert len(f.queue) == 1
    assert f.queue[0][0] == "Echo"


def test_nothing_queued_outside_play_and_queue_cleared_on_leave():
    f = feed()
    f.observe("menu", "level1", 0, 10)
    assert f.queue == []
    start(f)
    f.observe("briefing", "level1", 0, 10)
    assert f.queue == [] and f.current is None


def test_security_rise_queues_warden_mistake_with_cooldown():
    f = feed(cooldown=5.0)
    start(f)
    f.clear()
    f.observe("playing", "level1", 1, 10)
    assert [s for s, _ in f.queue] == ["WARDEN"]
    f.clear()
    f.observe("playing", "level1", 2, 10)
    assert f.queue == []                         # cooldown blocks the spam
    f.update(6.0)
    f.observe("playing", "level1", 3, 10)
    assert len(f.queue) == 1
    assert texts(f)[0] != line_for("level1", "mistake", 0)[1]   # next line in the cycle


def test_security_drop_or_same_is_silent():
    f = feed()
    start(f, sec=5)
    f.clear()
    f.observe("playing", "level1", 5, 10)
    f.observe("playing", "level1", 2, 10)
    assert f.queue == []


def test_gate_open_queues_echo_progress():
    f = feed()
    start(f)
    f.clear()
    f.observe("playing", "level1", 0, 10, gates=1)
    assert [s for s, _ in f.queue] == ["Echo"]


def test_danger_fires_once_per_level_even_during_cooldown():
    f = feed(cooldown=99)
    start(f)
    f.clear()
    f.observe("playing", "level1", 1, 10)         # starts the cooldown
    f.clear()
    ratio_sec = math.ceil(10 * DANGER_RATIO)
    f.observe("playing", "level1", ratio_sec, 10)
    assert [t for t in texts(f)] == [line_for("level1", "danger")[1]]
    f.clear()
    f.observe("playing", "level1", ratio_sec + 1, 10)
    assert line_for("level1", "danger")[1] not in texts(f)


def test_danger_rearms_for_a_new_level_and_on_retry():
    f = feed(cooldown=0)
    start(f, "level1")
    f.observe("playing", "level1", 8, 10)
    f.observe("playing", "level2", 0, 10)         # next level, no card
    assert texts(f) == [line_for("level2", "enter")[1]]
    f.observe("playing", "level2", 9, 10)
    assert line_for("level2", "danger")[1] in texts(f)


def test_queue_limit_drops_spam_but_keeps_forced_danger():
    f = feed(cooldown=0)
    start(f)
    for i in range(1, 5):
        f.observe("playing", "level1", i, 100)
    assert len(f.queue) <= 2
    f.observe("playing", "level1", 90, 100)
    assert line_for("level1", "danger")[1] in texts(f)


def test_security_max_zero_does_not_crash():
    f = feed()
    start(f)
    f.observe("playing", "level1", 1, 0)


# --- playback ------------------------------------------------------------
def test_line_types_holds_then_next_line_takes_over():
    f = feed(hold=1.0)
    start(f)
    f.say("WARDEN", "Short.")
    f.update(0.01)
    assert f.current[0] == "Echo"
    for _ in range(600):
        f.update(0.05)
        if f.current is None or f.current[0] == "WARDEN":
            break
    assert f.current is not None and f.current[0] == "WARDEN"
    for _ in range(600):
        f.update(0.05)
    assert f.current is None and f.queue == []


def test_hold_timer_does_not_start_until_typed():
    f = feed(hold=0.1)
    f.say("Echo", "x" * 200)
    f.update(0.05)
    assert not f.current[1].typer.done
    for _ in range(3):
        f.update(0.05)
    assert f.current is not None


def test_negative_dt_ignored():
    f = feed()
    f.say("Echo", "hi")
    f.update(-5)
    assert f.current is not None and f.held == 0


def test_draw_paints_box_and_portrait_only_when_active():
    font = pygame.font.Font(None, 22)
    f = feed()
    blank = pygame.Surface((960, 640)); blank.fill((0, 0, 0))
    s = blank.copy()
    f.draw(s, font)
    assert pygame.image.tostring(s, "RGB") == pygame.image.tostring(blank, "RGB")
    f.say("WARDEN", "Please stop.")
    for _ in range(40):
        f.update(0.02)
    f.draw(s, font)
    assert pygame.image.tostring(s, "RGB") != pygame.image.tostring(blank, "RGB")
    assert s.get_at((5, 5))[:3] == (0, 0, 0)       # nothing outside the box


def test_draw_unknown_speaker_has_no_portrait_but_still_draws():
    font = pygame.font.Font(None, 22)
    f = feed()
    f.say("Guard", "Halt.")
    f.update(0.5)
    s = pygame.Surface((960, 640)); s.fill((0, 0, 0))
    f.draw(s, font)
    assert pygame.image.tostring(s, "RGB") != pygame.image.tostring(pygame.Surface((960, 640)), "RGB")


def test_every_line_fits_the_compact_toast():
    from ui.comms import PORTRAIT, TOAST_WIDTH
    from ui import theme
    font = pygame.font.Font(None, 22)
    name_font = pygame.font.Font(None, 24)
    for lvl, moments in COMMS.items():
        for m, (speaker, lines) in moments.items():
            for text in lines:
                room = (TOAST_WIDTH - theme.PAD - PORTRAIT - theme.PAD
                        - name_font.size(speaker.upper() + ":")[0] - 8)
                assert font.size(text)[0] <= room, (lvl, m, text, font.size(text)[0], room)


def test_toast_stays_inside_its_rect_and_honours_a_custom_rect():
    font = pygame.font.Font(None, 22)
    f = feed()
    f.say("Echo", "Door is open. Keep moving.")
    for _ in range(60):
        f.update(0.02)
    s = pygame.Surface((960, 640)); s.fill((0, 0, 0))
    f.draw(s, font, rect=(100, 100, 400, 40))
    inside = s.subsurface((100, 100, 400, 40))
    assert pygame.image.tostring(inside, "RGB") != bytes(400 * 40 * 3)
    outside_top = s.subsurface((0, 0, 960, 99))
    assert pygame.image.tostring(outside_top, "RGB") == bytes(960 * 99 * 3)
    outside_bottom = s.subsurface((0, 150, 960, 490))
    assert pygame.image.tostring(outside_bottom, "RGB") == bytes(960 * 490 * 3)


def test_default_toast_is_slim_and_leaves_the_screen_above_it_untouched():
    font = pygame.font.Font(None, 22)
    f = feed()
    f.say("WARDEN", "Please stop.")
    for _ in range(60):
        f.update(0.02)
    s = pygame.Surface((960, 640)); s.fill((0, 0, 0))
    f.draw(s, font)
    above = s.subsurface((0, 0, 960, 640 - 60))
    assert pygame.image.tostring(above, "RGB") == bytes(960 * 580 * 3)
