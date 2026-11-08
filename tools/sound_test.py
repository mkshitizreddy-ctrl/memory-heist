"""Listen to every sound effect, one after another, with its name.

    python tools/sound_test.py            all effects
    python tools/sound_test.py bell zap   just these

Run it from the project folder. It needs a sound device; on a machine without
one it only prints the list.
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from systems.sfx import SAMPLE_RATE, SFX_NAMES, synth_sfx


def length_of(name):
    return synth_sfx(name).size / SAMPLE_RATE


def main(names=None, play=True, wait=time.sleep):
    names = list(names or SFX_NAMES)
    unknown = [n for n in names if n not in SFX_NAMES]
    if unknown:
        print("Unknown effect:", ", ".join(unknown), "- choose from:", ", ".join(SFX_NAMES))
        return 1
    audio = None
    if play:
        import pygame
        from systems.audio import Audio
        pygame.init()
        audio = Audio(ambient=False)
    for name in names:
        print(f"{name:12s} {length_of(name):.2f}s")
        if audio is not None:
            audio.play(name)
            wait(length_of(name) + 0.6)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
