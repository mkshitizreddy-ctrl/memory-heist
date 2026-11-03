"""
systems/voice.py
Owner: Member 1 - Core Game System

Speech without a voice actor: every speaker gets a short synthesized "blip"
that plays in time with the text as it appears, the way old adventure games
do it.  Each speaker has a pitch, a timbre and a rhythm of their own, so the
receptionist, the guard, ECHO and WARDEN are told apart with eyes closed.

    blip_schedule(text, cps, voice)    pure: when to blip, and at which pitch
    synth_blip(speaker, step)          pure: the waveform of one blip
    VoicePlayer(audio)                 plays schedules, one stream per track
    VoiceEvents(player)                watches the game, so no level has to

Blips go through Audio.play, so they follow the effects slider and the mute
switch.  Like SoundEvents, VoiceEvents is handed a snapshot once a frame.
"""

from collections import namedtuple

import pygame

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:                                   # the game still runs, silently
    NUMPY_AVAILABLE = False

SAMPLE_RATE = 44100

# base: pitch in Hz of step 0.  every: one blip per this many letters of a word.
# glide: end pitch / start pitch within one blip.  gain: peak level, below the
# sound effects because blips come thick and fast.
Voice = namedtuple("Voice", "base wave ms every glide gain")

VOICES = {
    "receptionist": Voice(330.0, "tri", 70, 2, 1.04, 0.30),     # warm, bright, chatty
    "guard": Voice(110.0, "square", 85, 3, 0.92, 0.26),         # low, blunt, slow
    "echo": Voice(520.0, "bell", 55, 2, 1.00, 0.28),            # clean, digital, quick
    "warden": Voice(82.0, "saw", 90, 3, 0.96, 0.26),            # harsh machine growl
    "ghost": Voice(240.0, "breath", 80, 2, 0.90, 0.24),         # airy, falling
}
DEFAULT_VOICE = Voice(220.0, "tri", 70, 2, 1.0, 0.26)

STEP_SEMITONES = (0, 2, 4, 7, 9, 12)        # a pentatonic ladder: any order sounds musical
STEPS = len(STEP_SEMITONES)
MIN_GAP = 0.045                             # seconds between blips; faster would smear
LATE_LIMIT = 0.12                           # a blip later than this (lag spike) is dropped
NPC_CPS = 20.0                              # a bubble appears at once; it "talks" this fast


def voice_key(speaker):
    return str(speaker).strip().lower()


def voice_for(speaker):
    return VOICES.get(voice_key(speaker), DEFAULT_VOICE)


def sound_name(speaker, step):
    return f"voice:{voice_key(speaker)}:{step}"


def _step_for(char, word_index):
    return (ord(char.lower()) * 5 + word_index) % STEPS


def blip_schedule(text, cps, voice):
    """List of (seconds, pitch step) for a line typed at `cps` characters/second.

    Each word opens with a blip and gets another every `voice.every` letters, so
    the rhythm follows the words.  Spaces and punctuation are silent; a question
    ends on the highest step, as a voice would rise.
    """
    if cps <= 0 or not text:
        return []
    events = []
    run, word, last = 0, 0, -MIN_GAP
    for i, ch in enumerate(text):
        if not ch.isalnum():
            if run:
                word += 1
            run = 0
            continue
        fire = run % voice.every == 0
        run += 1
        t = (i + 1) / cps
        if fire and t - last >= MIN_GAP:
            events.append((t, _step_for(ch, word)))
            last = t
    if events and text.rstrip().endswith("?"):
        events[-1] = (events[-1][0], STEPS - 1)
    return events


def _oscillator(kind, phase, rng):
    if kind == "tri":
        return (2.0 / np.pi) * np.arcsin(np.sin(phase))
    if kind == "square":                              # softened so it is not shrill
        wave = np.sign(np.sin(phase))
        return np.convolve(wave, np.ones(8) / 8, mode="same")
    if kind == "bell":
        return (np.sin(phase) + 0.45 * np.sin(2 * phase) + 0.2 * np.sin(3.01 * phase)) / 1.65
    if kind == "saw":
        saw = 2.0 * ((phase / (2 * np.pi)) % 1.0) - 1.0
        return np.convolve(saw, np.ones(4) / 4, mode="same")
    if kind == "breath":
        hiss = np.convolve(rng.uniform(-1, 1, phase.size), np.ones(6) / 6, mode="same")
        return 0.6 * np.sin(phase) + 0.5 * hiss
    raise KeyError(kind)


def synth_blip(speaker, step=0):
    """Float mono waveform in [-1, 1] for one blip of `speaker` at pitch `step`."""
    voice = voice_for(speaker)
    step = int(step) % STEPS
    n = int(SAMPLE_RATE * voice.ms / 1000)
    t = np.arange(n) / SAMPLE_RATE
    start = voice.base * 2.0 ** (STEP_SEMITONES[step] / 12.0)
    freq = np.linspace(start, start * voice.glide, n)
    phase = 2 * np.pi * np.cumsum(freq) / SAMPLE_RATE
    rng = np.random.default_rng(sum(map(ord, voice_key(speaker))) * 10 + step)
    wave = _oscillator(voice.wave, phase, rng)
    attack = max(1, int(SAMPLE_RATE * 0.004))
    envelope = np.exp(-3.4 * t / (voice.ms / 1000.0))               # gentle decay
    envelope[:attack] *= np.linspace(0.0, 1.0, attack)
    tail = max(1, int(SAMPLE_RATE * 0.008))
    envelope[-tail:] *= np.linspace(1.0, 0.0, tail)
    wave = wave * envelope
    peak = float(np.max(np.abs(wave))) or 1.0
    return wave / peak * voice.gain


class _Track:
    def __init__(self, speaker, events):
        self.speaker = speaker
        self.events = list(events)
        self.clock = 0.0


class VoicePlayer:
    """Plays blip schedules.  Each named track is one speaking voice at a time."""

    def __init__(self, audio):
        self.audio = audio
        self._tracks = {}

    # --- control ----------------------------------------------------------
    def speak(self, track, speaker, text, cps):
        """Start (or replace) `track`, blipping as `text` is typed at `cps`."""
        events = blip_schedule(text, cps, voice_for(speaker))
        if not events or not self._ensure(speaker):
            self._tracks.pop(track, None)
            return False
        self._tracks[track] = _Track(speaker, events)
        return True

    def stop(self, track=None):
        if track is None:
            self._tracks.clear()
        else:
            self._tracks.pop(track, None)

    def speaking(self, track=None):
        return bool(self._tracks) if track is None else track in self._tracks

    def update(self, dt):
        for name in list(self._tracks):
            track = self._tracks[name]
            track.clock += max(0.0, dt)
            due = None
            while track.events and track.events[0][0] <= track.clock:
                due = track.events.pop(0)
            if due is not None and track.clock - due[0] <= LATE_LIMIT:
                self.audio.play(sound_name(track.speaker, due[1]))
            if not track.events:
                del self._tracks[name]

    # --- sounds -----------------------------------------------------------
    def _ensure(self, speaker):
        """Build this speaker's blips the first time they talk."""
        if not (NUMPY_AVAILABLE and getattr(self.audio, "mixer_ready", False)):
            return False
        try:
            for step in range(STEPS):
                name = sound_name(speaker, step)
                if name not in self.audio.sounds:
                    pcm = (np.clip(synth_blip(speaker, step), -1.0, 1.0) * 32767).astype(np.int16)
                    stereo = np.ascontiguousarray(np.column_stack((pcm, pcm)))
                    self.audio.sounds[name] = pygame.sndarray.make_sound(stereo)
            return True
        except (pygame.error, ValueError):
            return False


class VoiceEvents:
    """Watches the game once a frame and starts the right voice.

      a radio line (ECHO / WARDEN / Ghost) appears  -> that voice, at its typing speed
      an NPC says something                        -> that NPC's voice
      a story card starts typing                   -> WARDEN on its cards, else ECHO
      the line / card ends, is skipped, or the run leaves play -> silence
    """

    def __init__(self, player):
        self.player = player
        self._comms = None
        self._said = {}
        self._serial = None

    def observe(self, state, comms=None, npcs=(), card=None):
        playing = state == "playing"

        # Radio line: (speaker, box) where box.typer has .text and .cps.
        if not playing or comms is None:
            if self._comms is not None:
                self._comms = None
                self.player.stop("comms")
        elif comms is not self._comms:
            self._comms = comms
            speaker, box = comms
            self.player.speak("comms", speaker, box.typer.text, box.typer.cps)

        # NPC speech: each NPC counts its lines in `said`.
        self._said = {n: s for n, s in self._said.items() if n in npcs}
        for npc in npcs:
            track = f"npc:{id(npc)}"
            if not playing:
                self.player.stop(track)
                self._said[npc] = npc.said          # do not replay on return
            elif npc.said != self._said.get(npc, 0):
                self._said[npc] = npc.said
                if npc.speech:
                    self.player.speak(track, npc.kind, npc.speech, NPC_CPS)

        # Story card text.
        typing = (card is not None and state in ("intro", "briefing", "outro")
                  and not card.done and not card.typing_done)
        if not typing:
            self.player.stop("story")
        elif card.serial != self._serial:
            self._serial = card.serial
            speaker = "warden" if card.warden else "echo"
            self.player.speak("story", speaker, "".join(card.lines), card.CHARS_PER_SECOND)
