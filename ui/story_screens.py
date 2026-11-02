"""
ui/story_screens.py
Owner: Member 1 - Core Game System

The story card: a title, the hero portrait(s) and a few lines of text that
type themselves out. The first key press finishes the typing, the next one
leaves the card; ESC skips it. Used for the intro now, and for the level
briefings and the ending later.
"""

import math

import pygame

from core.hero_portrait import make_portrait
from ui.cutscene_fx import (
    DataStreams,
    draw_glitch,
    draw_scanlines,
    open_flicker,
    periodic_glitch,
)
from levels.common import draw_cyber_background, draw_glow_text, GREEN, GREY
from core.floor_stats import MAX_STARS, format_duration
from ui import theme
from ui.kit import blit_centered, draw_panel

PORTRAIT_SIZE = 128
WARDEN_SIZE = 110
WARDEN_RED = (255, 70, 70)


class StoryScreen:
    CHARS_PER_SECOND = 45

    def __init__(self):
        self.title_font = pygame.font.Font(None, 52)
        self.body_font = pygame.font.Font(None, 30)
        self.concept_font = pygame.font.Font(None, 26)
        self.hint_font = pygame.font.Font(None, 26)
        self.map_font = pygame.font.Font(None, 24)
        self.label_font = pygame.font.Font(None, 24)
        self.stat_font = pygame.font.Font(None, 22)
        self.tick = 0
        self.age = 0.0
        self.streams = DataStreams(960, 640)
        self.begin({"title": "", "lines": []})

    def begin(self, beat, coop=False, progress=None, cleared=None):
        """Start a card from a story beat; coop shows both thieves.

        progress is (current level index, number of levels) and adds the
        route map; leave it out for cards that are not about a level.
        """
        self.progress = progress
        self.cleared = cleared      # summary of the floor just finished, or None
        self.title = beat["title"]
        self.lines = list(beat["lines"])
        self.concept = beat.get("concept")
        self.warden = bool(beat.get("warden", False))
        self.coop = coop
        self.done = False
        self.typing_done = self._total() == 0
        self._clock = 0.0
        self.age = 0.0

    def _total(self):
        return sum(len(line) for line in self.lines)

    def _revealed(self):
        return min(self._total(), int(self._clock))

    def update(self, dt):
        """Advance the typewriter, the card clock and the background streams."""
        self.age += dt
        self.streams.update(dt)
        if self.done or self.typing_done:
            return
        self._clock += dt * self.CHARS_PER_SECOND
        if self._revealed() >= self._total():
            self.typing_done = True

    def flicker(self):
        """1.0 just after the card opens, fading to 0 (drives the glitch)."""
        return open_flicker(self.age)

    def warden_alert(self):
        """WARDEN's eye is alert only while its card is still typing."""
        return self.warden and not self.typing_done

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

    def _draw_route_map(self, surface, y):
        """Draw one node per level: done = green, current = pulsing, next = grey."""
        current, total = self.progress
        width = surface.get_width()
        spacing = 90
        left = width // 2 - (total - 1) * spacing // 2
        centers = [(left + i * spacing, y) for i in range(total)]
        cyan = (0, 230, 255)

        for i in range(total - 1):
            done = i < current
            pygame.draw.line(
                surface, GREEN if done else (50, 60, 80),
                centers[i], centers[i + 1], 4,
            )

        pulse = 0.5 + 0.5 * math.sin(self.tick * 0.12)
        for i, center in enumerate(centers):
            label = "F" if i == total - 1 else str(i + 1)
            if i < current:
                pygame.draw.circle(surface, GREEN, center, 17)
                ink = (10, 30, 20)
            elif i == current:
                pygame.draw.circle(surface, (10, 30, 40), center, 17)
                pygame.draw.circle(surface, cyan, center, int(19 + 3 * pulse), 3)
                ink = cyan
            else:
                pygame.draw.circle(surface, (24, 30, 46), center, 17)
                pygame.draw.circle(surface, GREY, center, 17, 2)
                ink = GREY
            image = self.map_font.render(label, True, ink)
            surface.blit(image, image.get_rect(center=center))

    CLEARED_RECT = pygame.Rect(40, 105, 250, 150)

    @staticmethod
    def star_points(centre, radius):
        """Ten points of a five-pointed star, point up."""
        cx, cy = centre
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            r = radius if i % 2 == 0 else radius * 0.42
            pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
        return pts

    def _draw_cleared(self, surface):
        """A compact panel for the floor just finished: stars, points, time, mistakes."""
        info = self.cleared
        palette = theme.floor_palette(info["name"])
        accent = palette["accent"]
        rect = draw_panel(surface, self.CLEARED_RECT,
                          fill=theme.mix(theme.INK, theme.NAVY, 0.6), border=accent)
        blit_centered(surface, self.label_font.render("FLOOR CLEARED", True, accent),
                      (rect.centerx, rect.y + 16))
        blit_centered(surface, self.stat_font.render(palette["name"].upper(), True, theme.MIST),
                      (rect.centerx, rect.y + 34))
        for i in range(MAX_STARS):
            centre = (rect.centerx + (i - 1) * 36, rect.y + 62)
            pts = self.star_points(centre, 14)
            if i < info["stars"]:
                pygame.draw.polygon(surface, theme.GOLD, pts)
            else:
                pygame.draw.polygon(surface, theme.SLATE, pts, 2)
        sign = "+" if info["points"] >= 0 else ""
        rows = [("POINTS", f"{sign}{info['points']}", theme.SKY),
                ("TIME", format_duration(info["seconds"]), theme.GOLD),
                ("MISTAKES", str(info["mistakes"]),
                 theme.TEAL if info["mistakes"] == 0 else theme.CORAL)]
        y = rect.y + 88
        for caption, value, colour in rows:
            surface.blit(self.stat_font.render(caption, True, theme.MIST), (rect.x + 18, y))
            val = self.stat_font.render(value, True, colour)
            surface.blit(val, (rect.right - 18 - val.get_width(), y))
            y += 19

    def render(self, surface):
        self.tick += 1
        width, height = surface.get_size()
        draw_cyber_background(surface, self.tick)
        if self.streams.width != width or self.streams.height != height:
            self.streams = DataStreams(width, height)
        self.streams.draw(surface)

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

        if self.cleared:
            self._draw_cleared(surface)

        # WARDEN watches from the top-right corner on every card but the ending.
        if self.warden:
            eye = make_portrait("warden", WARDEN_SIZE, self.tick, alert=self.warden_alert())
            corner = (width - WARDEN_SIZE - 40, top + 5)
            surface.blit(eye, corner)
            name = self.label_font.render("WARDEN", True, WARDEN_RED)
            surface.blit(name, (corner[0] + WARDEN_SIZE // 2 - name.get_width() // 2, corner[1] + WARDEN_SIZE + 2))

        # Centre the whole block by its longest line, and type left-aligned
        # inside it, so the text does not shift sideways as it appears.
        block = max((self.body_font.size(line)[0] for line in self.lines), default=0)
        left = width // 2 - block // 2
        y = 270
        for line in self.visible_lines():
            image = self.body_font.render(line, True, (205, 215, 230))
            surface.blit(image, (left, y))
            y += 36

        if self.progress:
            self._draw_route_map(surface, 470)

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

        # Screen effects go last so they cover the whole card.
        draw_scanlines(surface, self.tick)
        glitch = max(self.flicker(), periodic_glitch(self.tick) if self.warden else 0.0)
        draw_glitch(surface, self.tick, glitch)
