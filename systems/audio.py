"""
systems/audio.py
Simple sound manager for Memory Heist.
"""

import os
import pygame


class Audio:
    def __init__(self):
        try:
            pygame.mixer.init()
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
            return

        # Show what files are actually present
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

    def play(self, name: str):
        if self.enabled and name in self.sounds:
            self.sounds[name].play()

    def toggle(self):
        self.enabled = not self.enabled