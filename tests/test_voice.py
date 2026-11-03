"""Speaker voices: blip schedules, synthesis, playback and the game hooks."""

import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import numpy as np
import pygame
import pytest

from core.game import Game
from core.npc import NPC
from systems import voice as V
from systems.audio import Audio
from systems.voice import (DEFAULT_VOICE, LATE_LIMIT, MIN_GAP, NPC_CPS, SAMPLE_RATE, STEPS,
                           VOICES, VoiceEvents, VoicePlayer, blip_schedule, sound_name,
                           synth_blip, voice_for)

SPEAKERS = sorted(VOICES)


@pytest.fixture(autouse=True)
def pygame_up():
    pygame.init()
    yield
    pygame.mixer.stop()
    pygame.mixer.set_reserved(0)


def crossings(wave):
    return int(np.sum(np.abs(np.diff(np.sign(wave))) > 0))


# --- schedule ---------------------------------------------------------------
PLAIN = V.Voice(300.0, "tri", 60, 2, 1.0, 0.3)


def test_nothing_to_say_means_no_blips():
    assert blip_schedule("", 40, PLAIN) == []
    assert blip_schedule("   ...  ", 40, PLAIN) == []
    assert blip_schedule("hello", 0, PLAIN) == []
    assert blip_schedule("hello", -5, PLAIN) == []


def test_blips_land_when_their_letter_appears():
    # "ab": a is char 0 (visible at 1/cps) and fires; b is the 2nd letter and does not (every=2).
    assert [t for t, _ in blip_schedule("ab", 10, PLAIN)] == [pytest.approx(0.1)]
    # "abc": a and c fire; c is char 2, visible at 3/cps.
    assert [t for t, _ in blip_schedule("abc", 10, PLAIN)] == [pytest.approx(0.1), pytest.approx(0.3)]


def test_every_word_opens_with_a_blip_and_spaces_are_silent():
    times = [t for t, _ in blip_schedule("a b c", 10, V.Voice(300.0, "tri", 60, 5, 1.0, 0.3))]
    assert times == [pytest.approx(0.1), pytest.approx(0.3), pytest.approx(0.5)]
    # No blip is ever timed for a space or punctuation mark.
    text = "go, now! ok."
    silent = {(i + 1) / 10 for i, ch in enumerate(text) if not ch.isalnum()}
    for t, _ in blip_schedule(text, 10, V.Voice(300.0, "tri", 60, 1, 1.0, 0.3)):
        assert not any(abs(t - s) < 1e-9 for s in silent)


def test_a_slower_voice_blips_less_often():
    text = "the quick brown fox jumps over the lazy dog"
    chatty = len(blip_schedule(text, 40, V.Voice(300.0, "tri", 60, 1, 1.0, 0.3)))
    slow = len(blip_schedule(text, 40, V.Voice(300.0, "tri", 60, 4, 1.0, 0.3)))
    assert chatty > slow > 0


def test_blips_are_never_closer_than_the_minimum_gap():
    fast = blip_schedule("abcdefghijklmnopqrstuvwxyz " * 4, 400, V.Voice(300.0, "tri", 60, 1, 1.0, 0.3))
    times = [t for t, _ in fast]
    assert len(times) > 3
    assert all(b - a >= MIN_GAP - 1e-9 for a, b in zip(times, times[1:]))


def test_steps_stay_on_the_ladder_and_schedules_are_deterministic():
    text = "Intruder on the third floor? Do not panic."
    a, b = blip_schedule(text, 55, PLAIN), blip_schedule(text, 55, PLAIN)
    assert a == b
    assert all(0 <= step < STEPS for _, step in a)
    assert len({step for _, step in a}) > 2            # intonation, not a drone


def test_a_question_ends_on_its_highest_step():
    asked = blip_schedule("are you ready?", 30, PLAIN)
    stated = blip_schedule("are you ready.", 30, PLAIN)
    assert asked[-1][1] == STEPS - 1
    assert asked[:-1] == stated[:-1]
    assert [t for t, _ in asked] == [t for t, _ in stated]


# --- synthesis --------------------------------------------------------------
@pytest.mark.parametrize("speaker", SPEAKERS)
@pytest.mark.parametrize("step", [0, STEPS - 1])
def test_blip_is_bounded_short_quiet_at_the_edges_and_deterministic(speaker, step):
    wave = synth_blip(speaker, step)
    assert wave.ndim == 1 and np.all(np.isfinite(wave))
    assert 0.03 <= wave.size / SAMPLE_RATE <= 0.11
    assert float(np.max(np.abs(wave))) == pytest.approx(VOICES[speaker].gain, abs=0.01)
    assert abs(wave[0]) < 0.02 and abs(wave[-1]) < 0.02          # no clicks
    assert np.array_equal(wave, synth_blip(speaker, step))


def test_blips_sit_below_the_sound_effects():
    from systems.sfx import SFX_VOLUME
    assert max(v.gain for v in VOICES.values()) < max(SFX_VOLUME.values())


def test_every_speaker_sounds_different():
    waves = {s: synth_blip(s, 0) for s in SPEAKERS}
    for i, a in enumerate(SPEAKERS):
        for b in SPEAKERS[i + 1:]:
            n = min(waves[a].size, waves[b].size)
            assert not np.allclose(waves[a][:n], waves[b][:n]), (a, b)


def test_pitch_rises_with_the_step_and_the_guard_is_lower_than_the_receptionist():
    rising = [crossings(synth_blip("receptionist", s)) for s in range(STEPS)]
    assert rising == sorted(rising) and rising[-1] > rising[0]
    # The long envelope tail makes comparing counts per second fair.
    def rate(speaker):
        w = synth_blip(speaker, 0)
        return crossings(w) / (w.size / SAMPLE_RATE)
    assert rate("warden") < rate("guard") < rate("receptionist") < rate("echo")


def test_ghost_voice_is_breathy_and_the_step_changes_its_noise():
    assert not np.array_equal(synth_blip("ghost", 0), synth_blip("ghost", 1))


def test_unknown_oscillator_is_an_error():
    with pytest.raises(KeyError):
        V._oscillator("kazoo", np.zeros(10), np.random.default_rng(0))


def test_voice_lookup_ignores_case_and_falls_back_to_a_default():
    assert voice_for("Echo") is VOICES["echo"] is voice_for(" ECHO ")
    assert voice_for("WARDEN") is VOICES["warden"]
    assert voice_for("Nobody") is DEFAULT_VOICE
    assert sound_name("Echo", 3) == "voice:echo:3"
    assert synth_blip("Nobody", 2).size > 0


# --- player -----------------------------------------------------------------
class FakeSound:
    def __init__(self):
        self.plays = 0
        self.volume = 1.0

    def get_volume(self):
        return self.volume

    def set_volume(self, v):
        self.volume = v

    def play(self):
        self.plays += 1


@pytest.fixture
def audio():
    a = Audio(ambient=False)
    yield a
    pygame.mixer.stop()


@pytest.fixture
def spy(audio, monkeypatch):
    """The real Audio, recording which sound names it was asked to play."""
    played = []
    monkeypatch.setattr(audio, "play", lambda name: played.append(name))
    return played


def run(player, seconds, fps=60):
    for _ in range(int(seconds * fps)):
        player.update(1 / fps)


def test_speaking_builds_the_speakers_blips_once(audio, spy):
    p = VoicePlayer(audio)
    assert p.speak("a", "guard", "move along", 20)
    names = [sound_name("guard", s) for s in range(STEPS)]
    assert all(n in audio.sounds for n in names)
    assert not any(n.startswith("voice:echo") for n in audio.sounds)       # only on demand
    first = audio.sounds[names[0]]
    p.speak("a", "guard", "again", 20)
    assert audio.sounds[names[0]] is first


def test_blips_play_at_their_scheduled_times(audio, spy):
    p = VoicePlayer(audio)
    expected = blip_schedule("hello there", 20, voice_for("guard"))
    p.speak("a", "guard", "hello there", 20)
    step, clock = 1 / 137, 0.0          # no frame lands exactly on a blip time
    for _ in range(1000):                                                  # bounded: never hang
        if not p.speaking("a"):
            break
        p.update(step)
        clock += step
        due = [e for e in expected if e[0] <= clock + 1e-9]
        assert spy == [sound_name("guard", s) for _, s in due]             # none early, none late
    assert not p.speaking("a")                                             # finished and removed
    assert len(spy) == len(expected) > 2


def test_a_lag_spike_plays_one_blip_not_a_burst(audio, spy):
    p = VoicePlayer(audio)
    events = blip_schedule("a long enough line to blip many times", 20, voice_for("echo"))
    p.speak("a", "echo", "a long enough line to blip many times", 20)
    p.update(events[3][0] + 0.001)                     # one huge frame covering four blips
    assert len(spy) == 1 and spy[0] == sound_name("echo", events[3][1])


def test_a_blip_that_is_far_too_late_is_dropped(audio, spy):
    p = VoicePlayer(audio)
    p.speak("a", "echo", "hi", 20)
    first = blip_schedule("hi", 20, voice_for("echo"))[0][0]
    p.update(first + LATE_LIMIT + 0.05)
    assert spy == []


def test_stop_silences_and_negative_time_is_ignored(audio, spy):
    p = VoicePlayer(audio)
    p.speak("a", "echo", "hello world", 20)
    p.speak("b", "guard", "hello world", 20)
    p.update(-1.0)
    assert p._tracks["a"].clock == 0.0
    p.stop("a")
    assert p.speaking("b") and not p.speaking("a")
    p.stop()
    assert not p.speaking()
    run(p, 2.0)
    assert spy == []


def test_a_new_line_on_a_track_replaces_the_old_one(audio, spy):
    p = VoicePlayer(audio)
    p.speak("a", "guard", "a very long first line indeed", 20)
    run(p, 0.2)
    spy.clear()
    p.speak("a", "echo", "ok", 20)
    run(p, 3.0)
    assert spy and all(n.startswith("voice:echo") for n in spy)


def test_tracks_talk_at_the_same_time(audio, spy):
    p = VoicePlayer(audio)
    p.speak("radio", "echo", "ping", 20)
    p.speak("npc", "guard", "halt", 20)
    run(p, 1.0)
    assert any(n.startswith("voice:echo") for n in spy)
    assert any(n.startswith("voice:guard") for n in spy)


def test_nothing_to_voice_means_not_speaking(audio, spy):
    p = VoicePlayer(audio)
    p.speak("a", "echo", "hello", 20)
    assert p.speak("a", "echo", "...", 20) is False
    assert not p.speaking("a")                                             # stale line removed


def test_no_mixer_means_silence_not_a_crash():
    dead = Audio.__new__(Audio)
    dead.mixer_ready, dead.enabled, dead.sounds = False, False, {}
    p = VoicePlayer(dead)
    assert p.speak("a", "echo", "hello there", 20) is False
    p.update(1.0)


def test_a_failing_mixer_is_survived(audio, monkeypatch):
    def boom(_):
        raise pygame.error("no device")
    monkeypatch.setattr(pygame.sndarray, "make_sound", boom)
    assert VoicePlayer(audio).speak("a", "echo", "hello there", 20) is False


def test_without_numpy_the_player_is_silent(audio, monkeypatch):
    monkeypatch.setattr(V, "NUMPY_AVAILABLE", False)
    assert VoicePlayer(audio).speak("a", "echo", "hello there", 20) is False


def test_blips_follow_the_effects_volume_and_the_mute_switch(audio):
    p = VoicePlayer(audio)
    p.speak("a", "guard", "ok", 20)
    fake = FakeSound()
    audio.sounds.update({sound_name("guard", s): fake for s in range(STEPS)})
    audio.sfx_volume = 0.5
    p.update(0.06)
    assert fake.plays == 1 and fake.volume == pytest.approx(0.5)
    p.speak("a", "guard", "ok", 20)
    audio.enabled = False                                                  # muted
    p.update(0.06)
    assert fake.plays == 1


# --- VoiceEvents ------------------------------------------------------------
class Recorder:
    def __init__(self):
        self.calls = []

    def speak(self, track, speaker, text, cps):
        self.calls.append(("speak", track, speaker, text, cps))

    def stop(self, track=None):
        self.calls.append(("stop", track))

    def spoken(self):
        return [c for c in self.calls if c[0] == "speak"]


class Box:
    def __init__(self, text, cps=55.0):
        self.typer = type("T", (), {"text": text, "cps": cps})()


class Card:
    CHARS_PER_SECOND = 45

    def __init__(self, lines, warden=False, serial=1):
        self.lines, self.warden, self.serial = lines, warden, serial
        self.done = self.typing_done = False


def test_a_radio_line_is_voiced_once_in_the_speakers_voice():
    rec = Recorder()
    ev = VoiceEvents(rec)
    line = ("Echo", Box("Stay low.", 55.0))
    for _ in range(5):
        ev.observe("playing", comms=line)
    assert rec.spoken() == [("speak", "comms", "Echo", "Stay low.", 55.0)]
    ev.observe("playing", comms=("WARDEN", Box("Halt.")))
    assert rec.spoken()[-1][2:4] == ("WARDEN", "Halt.")
    assert len(rec.spoken()) == 2


def test_a_radio_line_that_ends_or_a_run_that_leaves_play_goes_quiet():
    rec = Recorder()
    ev = VoiceEvents(rec)
    ev.observe("playing", comms=("Echo", Box("Hi there.")))
    ev.observe("playing", comms=None)
    assert ("stop", "comms") in rec.calls
    rec.calls.clear()
    ev.observe("playing", comms=("Echo", Box("Again.")))
    ev.observe("lose", comms=("Echo", Box("Again.")))
    assert ("stop", "comms") in rec.calls and len(rec.spoken()) == 1
    ev.observe("playing", comms=None)
    assert rec.calls.count(("stop", "comms")) == 1                         # no repeated stops


def test_the_same_line_object_is_not_re_voiced_after_leaving_and_returning():
    rec = Recorder()
    ev = VoiceEvents(rec)
    line = ("Echo", Box("Quiet now."))
    ev.observe("playing", comms=line)
    ev.observe("menu", comms=line)
    ev.observe("playing", comms=line)
    assert len(rec.spoken()) == 2             # returning to play restarts the line, as comms does


def test_an_npc_speaks_each_time_it_says_something_even_the_same_words():
    rec = Recorder()
    ev = VoiceEvents(rec)
    guard = NPC("guard", (100, 100))
    ev.observe("playing", npcs=[guard])
    assert rec.spoken() == []
    guard.say("Move along.")
    ev.observe("playing", npcs=[guard])
    ev.observe("playing", npcs=[guard])
    assert rec.spoken() == [("speak", f"npc:{id(guard)}", "guard", "Move along.", NPC_CPS)]
    guard.say("Move along.")
    ev.observe("playing", npcs=[guard])
    assert len(rec.spoken()) == 2


def test_two_npcs_have_their_own_tracks_and_voices():
    rec = Recorder()
    ev = VoiceEvents(rec)
    guard, clerk = NPC("guard", (0, 0)), NPC("receptionist", (50, 0))
    guard.say("Hmm.")
    clerk.say("Welcome!")
    ev.observe("playing", npcs=[guard, clerk])
    tracks = {c[1]: c[2] for c in rec.spoken()}
    assert tracks == {f"npc:{id(guard)}": "guard", f"npc:{id(clerk)}": "receptionist"}


def test_npc_speech_while_away_from_play_is_not_replayed_on_return():
    rec = Recorder()
    ev = VoiceEvents(rec)
    guard = NPC("guard", (0, 0))
    ev.observe("playing", npcs=[guard])
    guard.say("Hey.")
    ev.observe("pause_menu_or_win", npcs=[guard])
    ev.observe("playing", npcs=[guard])
    assert rec.spoken() == []
    assert ("stop", f"npc:{id(guard)}") in rec.calls


def test_a_story_card_is_voiced_once_by_echo_or_by_warden():
    rec = Recorder()
    ev = VoiceEvents(rec)
    card = Card(["Line one.", "Line two."], serial=1)
    for _ in range(4):
        ev.observe("briefing", card=card)
    assert rec.spoken() == [("speak", "story", "echo", "Line one.Line two.", 45)]
    ev.observe("briefing", card=Card(["Halt."], warden=True, serial=2))
    assert rec.spoken()[-1][2] == "warden"


def test_a_skipped_or_finished_card_falls_silent_and_does_not_restart():
    rec = Recorder()
    ev = VoiceEvents(rec)
    card = Card(["Hello there."], serial=7)
    ev.observe("intro", card=card)
    card.typing_done = True                                # first key: finish typing
    ev.observe("intro", card=card)
    assert ("stop", "story") in rec.calls
    card.typing_done = False                               # (cannot happen; guards against a restart)
    ev.observe("intro", card=card)
    assert len(rec.spoken()) == 1
    other = Card(["Hello there."], serial=8)
    other.done = True
    ev.observe("intro", card=other)
    assert len(rec.spoken()) == 1


def test_a_card_is_silent_outside_the_story_states():
    rec = Recorder()
    ev = VoiceEvents(rec)
    ev.observe("playing", card=Card(["Hello."]))
    ev.observe("menu", card=Card(["Hello."]))
    assert rec.spoken() == []


# --- the real game ----------------------------------------------------------
@pytest.fixture
def game():
    g = Game()
    yield g
    g.music.stop()
    pygame.mixer.stop()
    pygame.mixer.set_reserved(0)


def frames(g, n):
    for _ in range(n):
        g.update(1 / 60)
        g.render()


def test_radio_lines_are_voiced_in_the_real_game(game):
    game.state = "playing"
    game.level_manager.current_name = "level2"
    game._last_level_name = "level2"
    frames(game, 5)
    assert game.comms.current is not None
    assert game.voice.speaking("comms")
    game.state = "lose"
    frames(game, 2)
    assert not game.voice.speaking("comms")


def test_voices_wait_while_paused(game):
    game.state = "playing"
    game.level_manager.current_name = "level2"
    game._last_level_name = "level2"
    frames(game, 5)
    game.paused = True
    clock = game.voice._tracks["comms"].clock
    frames(game, 30)
    assert game.voice._tracks["comms"].clock == clock


def test_a_story_card_is_voiced_in_the_real_game(game):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN, unicode=""))
    game.handle_events()
    assert game.state == "intro"
    frames(game, 2)
    assert game.voice.speaking("story")
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE, unicode=" "))
    game.handle_events()                                   # first key finishes the typing
    frames(game, 2)
    assert not game.voice.speaking("story")


def test_floor_one_npcs_are_voiced_in_the_real_game(monkeypatch):
    monkeypatch.setenv("MEMORY_HEIST_NEW_FLOOR1", "1")
    g = Game()
    try:
        g.story_enabled = False
        g.level_manager.start("level1")
        g._last_level_name = "level1"
        g.state = "playing"
        frames(g, 5)
        npc = g.level_manager.current.guard
        npc.say("Move along.")
        frames(g, 2)
        assert g.voice.speaking(f"npc:{id(npc)}")
    finally:
        g.music.stop()
        pygame.mixer.stop()
        pygame.mixer.set_reserved(0)


def test_each_new_story_card_is_voiced_again(game):
    for key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_SPACE):     # menu, finish typing, leave
        pygame.event.clear()
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key, unicode=" "))
        game.handle_events()
        frames(game, 2)
    assert game.state == "briefing"
    assert game.voice.speaking("story")
