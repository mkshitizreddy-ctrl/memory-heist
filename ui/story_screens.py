"""
ui/story_screens.py
Owner: Member 1 - Core Game System

The story card: a title, the hero portrait(s) and a few lines of text that
type themselves out. The first key press finishes the typing, the next one
leaves the card; ESC skips it. Used for the intro now, and for the level
briefings and the ending later.
"""

import pygame

from core.hero_portrait import make_portrait
from levels.common import draw_cyber_background, draw_glow_text, GREEN

PORTRAIT_SIZE = 128


class StoryScreen:
    CHARS_PER_SECOND = 45

    def __init__(self):
        self.title_font = pygame.font.Font(None, 52)
        self.body_font = pygame.font.Font(None, 30)
        self.concept_font = pygame.font.Font(None, 26)
        self.hint_font = pygame.font.Font(None, 26)
        self.tick = 0
        self.begin({"title": "", "lines": []})

    def begin(self, beat, coop=False):
        """Start a card from a story beat; coop shows both thieves."""
        self.title = beat["title"]
        self.lines = list(beat["lines"])
        self.concept = beat.get("concept")
        self.coop = coop
        self.done = False
        self.typing_done = self._total() == 0
        self._clock = 0.0

    def _total(self):
        return sum(len(line) for line in self.lines)

    def _revealed(self):
        return min(self._total(), int(self._clock))

    def update(self, dt):
        """Advance the typewriter."""
        if self.done or self.typing_done:
            return
        self._clock += dt * self.CHARS_PER_SECOND
        if self._revealed() >= self._total():
            self.typing_done = True

    def visible_lines(self):
        """The lines typed so far, the last one possibly partial."""
        remaining = self._revealed()
        shown = []
        for line in self.lines:
            if remaining <= 0:
                break
            shown.append(line[:remaining])
            remaining -= len(line)
        return shown

    def handle_event(self, event):
        """First key finishes the typing; the next key leaves the card."""
        if event.type != pygame.KEYDOWN:
            return
        if not self.typing_done:
            self.typing_done = True
            self._clock = float(self._total())
        else:
            self.done = True

    def skip(self):
        self.done = True

    def render(self, surface):
        self.tick += 1
        width, height = surface.get_size()
        draw_cyber_background(surface, self.tick)

        draw_glow_text(surface, self.title_font, self.title, (width // 2, 60), color=GREEN)

        # Hero portrait(s) under the title.
        top = 105
        if self.coop:
            ghost = make_portrait("ghost", PORTRAIT_SIZE, self.tick)
            echo = make_portrait("echo", PORTRAIT_SIZE, self.tick + 15)
            surface.blit(ghost, (width // 2 - 40 - PORTRAIT_SIZE, top))
            surface.blit(echo, (width // 2 + 40, top))
        else:
            ghost = make_portrait("ghost", PORTRAIT_SIZE, self.tick)
            surface.blit(ghost, (width // 2 - PORTRAIT_SIZE // 2, top))

        # Centre the whole block by its longest line, and type left-aligned
        # inside it, so the text does not shift sideways as it appears.
        block = max((self.body_font.size(line)[0] for line in self.lines), default=0)
        left = width // 2 - block // 2
        y = 270
        for line in self.visible_lines():
            image = self.body_font.render(line, True, (205, 215, 230))
            surface.blit(image, (left, y))
            y += 36

        if self.concept:
            tag = self.concept_font.render(f"You will learn: {self.concept}", True, (140, 200, 255))
            surface.blit(tag, (width // 2 - tag.get_width() // 2, height - 120))

        pulse = 140 + int(60 * abs((self.tick % 60) - 30) / 30)
        text = (
            "Press any key to continue   |   ESC to skip"
            if self.typing_done
            else "Press any key to show all   |   ESC to skip"
        )
        hint = self.hint_font.render(text, True, (pulse, pulse, pulse + 10))
        surface.blit(hint, (width // 2 - hint.get_width() // 2, height - 70))
