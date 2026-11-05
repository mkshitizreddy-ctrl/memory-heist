"""
systems/voice_clips.py

Spoken lines as audio files. Every line the game can say aloud (the story cards
and the radio chatter) has a clip id made from who says it and what they say,
so a clip can never be matched to the wrong words: change a line and its old
clip simply stops being found, and the game falls back to the blips.

    clip_id(speaker, text)        "echo_3f9a1c07b2"
    clip_path(speaker, text)      assets/voice/echo_3f9a1c07b2.mp3
    all_clips()                   every (speaker, text) the game can speak

tools/generate_voice.py reads all_clips() and asks ElevenLabs for the missing
files. Pure Python, no pygame, so the tool can import it.
"""

import hashlib
import os

from core.comms import COMMS
from core.story import STORY

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLIP_DIR = os.path.join(ROOT, "assets", "voice")
EXTENSION = ".mp3"

NARRATOR = "narrator"

# speaker -> ElevenLabs voice and delivery. stability: lower is more expressive.
# The default cast are voices designed in the project's own ElevenLabs account
# (they work by API on the free plan); tools/generate_voice.py --premade swaps in
# the built-in voices that every account can use.
CAST = {
    "narrator": {"voice_id": "zuy9QksMe9IObHgZo0cI", "stability": 0.50},     # MH Narrator, refined baritone
    "echo": {"voice_id": "3xY1sHyNnTtPq7x2eTwI", "stability": 0.40},         # MH Echo, composed hacker
    "warden": {"voice_id": "1ne5MN31usMd2RP9CqhW", "stability": 0.65},       # MH WARDEN, velvet AI
}
PREMADE_CAST = {
    "narrator": {"voice_id": "JBFqnCBsd6RMkjVDRZzb", "stability": 0.50},     # George
    "echo": {"voice_id": "EXAVITQu4vr4xnSDxMaL", "stability": 0.40},         # Sarah
    "warden": {"voice_id": "onwK4e9ZLuTAKqWW03F9", "stability": 0.65},       # Daniel
}


def normalise(text):
    """Collapse whitespace so a re-wrapped line keeps its clip."""
    return " ".join(str(text).split())


def speaker_key(speaker):
    return str(speaker).strip().lower()


def clip_id(speaker, text):
    digest = hashlib.sha1(normalise(text).encode("utf-8")).hexdigest()[:10]
    return f"{speaker_key(speaker)}_{digest}"


def clip_path(speaker, text, folder=None):
    return os.path.join(folder or CLIP_DIR, clip_id(speaker, text) + EXTENSION)


def story_text(lines):
    """What a story card says aloud: its lines read as one passage."""
    return normalise(" ".join(lines))


def all_clips():
    """Every (speaker, text) the game can speak, narration first, no repeats."""
    clips = []
    seen = set()

    def add(speaker, text):
        key = (speaker_key(speaker), normalise(text))
        if key not in seen and key[1]:
            seen.add(key)
            clips.append(key)

    for beat in STORY.values():
        add(NARRATOR, story_text(beat["lines"]))
    for floor in COMMS.values():
        for speaker, lines in floor.values():
            for line in lines:
                add(speaker, line)
    return clips
