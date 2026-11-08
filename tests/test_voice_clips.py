"""Recorded voice lines: clip ids, the clip catalogue, playback and the story/radio hooks."""

import os
from types import SimpleNamespace

import pygame
import pytest

from core.comms import COMMS
from core.story import STORY
from systems import voice_clips as vc
from systems.voice import VoiceEvents, VoicePlayer


# --- ids and catalogue ---------------------------------------------------------------
def test_a_clip_id_is_stable_and_names_the_speaker():
    assert vc.clip_id("Echo", "Stay low.") == vc.clip_id("echo", "Stay low.")
    assert vc.clip_id("echo", "Stay low.").startswith("echo_")
    assert len(vc.clip_id("echo", "Stay low.").split("_")[1]) == 10


def test_ids_differ_by_speaker_and_by_words():
    assert vc.clip_id("echo", "Stay low.") != vc.clip_id("warden", "Stay low.")
    assert vc.clip_id("echo", "Stay low.") != vc.clip_id("echo", "Stay low!")


def test_rewrapping_a_line_keeps_its_clip():
    assert vc.clip_id("echo", "Stay   low.\n") == vc.clip_id("echo", " Stay low.")


def test_clip_path_uses_the_folder_and_mp3():
    path = vc.clip_path("echo", "Stay low.", "somewhere")
    assert os.path.dirname(path) == "somewhere" and path.endswith(".mp3")
    assert vc.clip_path("echo", "Stay low.").startswith(vc.CLIP_DIR)


def test_story_text_joins_lines_with_single_spaces():
    assert vc.story_text(["One.", "Two.  ", "Three."]) == "One. Two. Three."


def test_the_catalogue_has_every_story_beat_and_radio_line_once():
    clips = vc.all_clips()
    assert len(clips) == len(set(clips))
    for beat in STORY.values():
        assert (vc.NARRATOR, vc.story_text(beat["lines"])) in clips
    for floor in COMMS.values():
        for speaker, lines in floor.values():
            for line in lines:
                assert (speaker.lower(), line) in clips
    story = len(STORY)
    radio = sum(len(lines) for floor in COMMS.values() for _, lines in floor.values())
    assert len(clips) == story + radio


def test_every_speaker_in_the_catalogue_has_a_voice_in_both_casts():
    speakers = {speaker for speaker, _ in vc.all_clips()}
    assert speakers == {"narrator", "echo", "warden"}
    for cast in (vc.CAST, vc.PREMADE_CAST):
        assert speakers <= set(cast)
        for voice in cast.values():
            assert voice["voice_id"] and 0 <= voice["stability"] <= 1


def test_clip_ids_in_the_catalogue_are_all_distinct():
    ids = [vc.clip_id(s, t) for s, t in vc.all_clips()]
    assert len(ids) == len(set(ids))


# --- player ----------------------------------------------------------------------------
class FakeChannel:
    def __init__(self):
        self.busy, self.stopped = True, False

    def get_busy(self):
        return self.busy

    def stop(self):
        self.stopped, self.busy = True, False


class FakeSound:
    created = []

    def __init__(self, path):
        self.path, self.volume, self.channels = path, None, []
        FakeSound.created.append(path)

    def set_volume(self, v):
        self.volume = v

    def play(self):
        channel = FakeChannel()
        self.channels.append(channel)
        return channel


@pytest.fixture
def folder(tmp_path):
    return str(tmp_path)


@pytest.fixture
def player(folder, monkeypatch):
    FakeSound.created = []
    monkeypatch.setattr(pygame.mixer, "Sound", FakeSound)
    audio = SimpleNamespace(enabled=True, mixer_ready=True, sfx_volume=0.9, voice_volume=0.5, sounds={}, play=lambda n: None)
    return VoicePlayer(audio, clip_dir=folder)


def make_clip(folder, speaker, text):
    path = vc.clip_path(speaker, text, folder)
    open(path, "wb").write(b"x")
    return path


def test_no_file_means_no_recording(player):
    assert player.speak_clip("t", "echo", "Stay low.") is False
    assert not player.speaking("t")


def test_an_existing_clip_plays_at_the_voice_volume_not_the_effects_volume(player, folder):
    make_clip(folder, "echo", "Stay low.")
    assert player.speak_clip("t", "Echo", "Stay low.") is True
    assert player.speaking("t") and player.speaking()
    sound = player._loaded[vc.clip_path("echo", "Stay low.", folder)]
    assert sound.volume == 0.5


def test_voice_volume_zero_turns_recordings_and_blips_off(player, folder):
    make_clip(folder, "echo", "Stay low.")
    player.audio.voice_volume = 0.0
    assert player.speak_clip("t", "echo", "Stay low.") is False
    assert player.speak("t", "echo", "Stay low.", 20) is False
    assert not player.speaking()


def test_a_player_whose_audio_has_no_voice_volume_plays_at_full(player, folder):
    make_clip(folder, "echo", "Stay low.")
    del player.audio.voice_volume
    assert player.speak_clip("t", "echo", "Stay low.") is True
    assert player._loaded[vc.clip_path("echo", "Stay low.", folder)].volume == 1.0


def test_muted_sound_plays_nothing(player, folder):
    make_clip(folder, "echo", "Stay low.")
    player.audio.enabled = False
    assert player.speak_clip("t", "echo", "Stay low.") is False


def test_no_mixer_means_no_recording(player, folder):
    make_clip(folder, "echo", "Stay low.")
    player.audio.mixer_ready = False
    assert player.speak_clip("t", "echo", "Stay low.") is False


def test_an_unreadable_file_falls_back_and_is_only_tried_once(player, folder, monkeypatch):
    make_clip(folder, "echo", "Stay low.")

    def broken(path):
        FakeSound.created.append(path)
        raise pygame.error("bad file")

    monkeypatch.setattr(pygame.mixer, "Sound", broken)
    assert player.speak_clip("t", "echo", "Stay low.") is False
    assert player.speak_clip("t", "echo", "Stay low.") is False
    assert len(FakeSound.created) == 1


def test_stopping_a_track_stops_its_recording(player, folder):
    make_clip(folder, "echo", "Stay low.")
    player.speak_clip("t", "echo", "Stay low.")
    sound = player._loaded[vc.clip_path("echo", "Stay low.", folder)]
    player.stop("t")
    assert sound.channels[0].stopped and not player.speaking("t")


def test_stopping_everything_stops_every_recording(player, folder):
    make_clip(folder, "echo", "A.")
    make_clip(folder, "warden", "B.")
    player.speak_clip("one", "echo", "A.")
    player.speak_clip("two", "warden", "B.")
    player.stop()
    assert not player.speaking()
    assert all(s.channels[0].stopped for s in player._loaded.values())


def test_a_new_line_on_a_track_replaces_the_old_recording(player, folder):
    make_clip(folder, "echo", "A.")
    make_clip(folder, "echo", "B.")
    player.speak_clip("t", "echo", "A.")
    first = player._loaded[vc.clip_path("echo", "A.", folder)]
    player.speak_clip("t", "echo", "B.")
    assert first.channels[0].stopped and player.speaking("t")


def test_a_finished_recording_is_forgotten(player, folder):
    make_clip(folder, "echo", "A.")
    player.speak_clip("t", "echo", "A.")
    player._loaded[vc.clip_path("echo", "A.", folder)].channels[0].busy = False
    player.update(0.016)
    assert not player.speaking("t")


def test_a_recording_replaces_blips_on_the_same_track(player, folder):
    make_clip(folder, "echo", "A.")
    player._tracks["t"] = object()
    player.speak_clip("t", "echo", "A.")
    assert "t" not in player._tracks


# --- hooks in VoiceEvents -----------------------------------------------------------------
class Recorder:
    def __init__(self, clips=True):
        self.calls, self.clips = [], clips

    def speak(self, track, speaker, text, cps):
        self.calls.append(("speak", track, speaker, text))

    def speak_clip(self, track, speaker, text):
        self.calls.append(("clip", track, speaker, text))
        return self.clips

    def stop(self, track=None):
        self.calls.append(("stop", track))

    def kinds(self):
        return [c[0] for c in self.calls if c[0] != "stop"]


class Box:
    def __init__(self, text):
        self.typer = type("T", (), {"text": text, "cps": 55.0})()


class Card:
    CHARS_PER_SECOND = 45

    def __init__(self, lines, warden=False, serial=1):
        self.lines, self.warden, self.serial = lines, warden, serial
        self.done = self.typing_done = False


def test_a_radio_line_uses_its_recording_and_skips_the_blips():
    rec = Recorder(clips=True)
    VoiceEvents(rec).observe("playing", comms=("Echo", Box("Stay low.")))
    assert rec.kinds() == ["clip"] and rec.calls[0][2:] == ("Echo", "Stay low.")


def test_a_radio_line_without_a_recording_falls_back_to_blips():
    rec = Recorder(clips=False)
    VoiceEvents(rec).observe("playing", comms=("Echo", Box("Stay low.")))
    assert rec.kinds() == ["clip", "speak"]


def test_a_player_without_recordings_support_still_blips():
    class Old:
        def __init__(self):
            self.spoken = []

        def speak(self, track, speaker, text, cps):
            self.spoken.append(text)

        def stop(self, track=None):
            pass

    old = Old()
    VoiceEvents(old).observe("playing", comms=("Echo", Box("Stay low.")))
    assert old.spoken == ["Stay low."]


def test_a_story_card_is_narrated_with_the_joined_lines():
    rec = Recorder(clips=True)
    VoiceEvents(rec).observe("intro", card=Card(["One.", "Two."]))
    assert rec.calls[0] == ("clip", "story", "narrator", "One. Two.")
    assert "speak" not in rec.kinds()


def test_narration_keeps_playing_after_the_typing_is_skipped_until_the_card_is_left():
    rec = Recorder(clips=True)
    ev = VoiceEvents(rec)
    card = Card(["One.", "Two."])
    ev.observe("intro", card=card)
    card.typing_done = True
    rec.calls.clear()
    ev.observe("intro", card=card)
    assert ("stop", "story") not in rec.calls
    card.done = True
    ev.observe("intro", card=card)
    assert ("stop", "story") in rec.calls


def test_leaving_the_story_state_stops_the_narration():
    rec = Recorder(clips=True)
    ev = VoiceEvents(rec)
    ev.observe("briefing", card=Card(["One."]))
    rec.calls.clear()
    ev.observe("playing", card=Card(["One."]))
    assert ("stop", "story") in rec.calls


def test_a_card_without_narration_blips_and_stops_when_typing_is_skipped():
    rec = Recorder(clips=False)
    ev = VoiceEvents(rec)
    card = Card(["One.", "Two."], warden=True)
    ev.observe("intro", card=card)
    assert rec.kinds() == ["clip", "speak"] and rec.calls[1][2] == "warden"
    card.typing_done = True
    rec.calls.clear()
    ev.observe("intro", card=card)
    assert ("stop", "story") in rec.calls


def test_a_new_card_is_narrated_again():
    rec = Recorder(clips=True)
    ev = VoiceEvents(rec)
    ev.observe("briefing", card=Card(["One."], serial=1))
    ev.observe("briefing", card=Card(["Two."], serial=2))
    assert [c[3] for c in rec.calls if c[0] == "clip"] == ["One.", "Two."]
