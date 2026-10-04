"""
systems/audio.py
Simple sound manager for Memory Heist.

Also generates a short, seamless ambient background loop in code
(no royalty-free music file was available to include), using numpy
to synthesize a few low sine tones with a slow volume swell.
"""

import os
import pygame

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class Audio:
    def __init__(self):
        try:
            pygame.mixer.init(frequency=44100, size=-16, channels=2)
            self.enabled = True
        except pygame.error as e:
            print("Audio init failed:", e)
            self.enabled = False
            self.sounds = {}
            return

        self.sounds = {}
        base = os.path.join("assets", "sounds")

        print("Looking for sounds in:", os.path.abspath(base))

        if not os.path.isdir(base):
            print("  → folder does not exist")
        else:
            files = os.listdir(base)
            print("  → files found:", files)

            for name in ("correct", "wrong", "unlock", "click"):
                loaded = False
                for ext in (".wav", ".ogg", ".mp3"):
                    path = os.path.join(base, name + ext)
                    if os.path.exists(path):
                        try:
                            self.sounds[name] = pygame.mixer.Sound(path)
                            print(f"  ✓ loaded {name}{ext}")
                            loaded = True
                            break
                        except pygame.error as e:
                            print(f"  ✗ failed to load {name}{ext}: {e}")
                if not loaded:
                    print(f"  ✗ could not load {name}")

        self.ambient_channel = None
        self._start_ambient()

    def _make_ambient_loop(self):
        """Synthesize a 4-second seamless ambient drone (no external file)."""
        sample_rate = 44100
        duration = 4.0
        t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

        wave = (
            0.15 * np.sin(2 * np.pi * 55 * t) +
            0.10 * np.sin(2 * np.pi * 110 * t) +
            0.05 * np.sin(2 * np.pi * 165 * t)
        )
        # Slow volume swell - 0.25 Hz completes exactly one cycle in 4s,
        # so the loop point matches up with no audible click.
        envelope = 0.85 + 0.15 * np.sin(2 * np.pi * 0.25 * t)
        wave = wave * envelope

        audio_data = (wave * 32767 * 0.25).astype(np.int16)
        stereo = np.column_stack((audio_data, audio_data))
        return pygame.sndarray.make_sound(stereo)

    def _start_ambient(self):
        """Generate and start looping the ambient background hum."""
        if not (self.enabled and NUMPY_AVAILABLE):
            return
        try:
            ambient_sound = self._make_ambient_loop()
            self.ambient_channel = ambient_sound.play(loops=-1)
        except pygame.error as e:
            print("Ambient audio failed to start:", e)

    def play(self, name: str):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def toggle(self):
        self.enabled = not self.enabled
        if self.ambient_channel:
            if self.enabled:
                self.ambient_channel.unpause()
            else:
                self.ambient_channel.pause()