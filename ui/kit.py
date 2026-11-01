"""
ui/kit.py
Owner: Member 1 - Core Game System

Shared UI building blocks so every screen and level looks like the same game:
a flat rounded panel, a Button with hover/press feedback, a typewriter, and a
DialogueBox for WARDEN / Echo / Ghost lines. All colour comes from ui.theme.
"""

import pygame

from core.easing import Tween, ease_out_back
from ui import theme

SHADOW_OFFSET = 4
SHADOW_ALPHA = 90
HOVER_SCALE = 1.04
PRESS_SCALE = 0.96
POP_SECONDS = 0.15


def draw_panel(surface, rect, fill=theme.NAVY, border=theme.SLATE,
               radius=theme.RADIUS, shadow=True):
    """Flat rounded panel with a 2px border and an optional soft drop shadow."""
    rect = pygame.Rect(rect)
    if shadow:
        sh = pygame.Surface(rect.size, pygame.SRCALPHA)
        pygame.draw.rect(sh, (0, 0, 0, SHADOW_ALPHA), sh.get_rect(), border_radius=radius)
        surface.blit(sh, rect.move(SHADOW_OFFSET, SHADOW_OFFSET))
    pygame.draw.rect(surface, fill, rect, border_radius=radius)
    pygame.draw.rect(surface, border, rect, width=theme.BORDER, border_radius=radius)
    return rect


def wrap_text(text, font, max_width):
    """Greedy word wrap; honours explicit newlines; never drops text."""
    lines = []
    for paragraph in text.split("\n"):
        words = paragraph.split(" ")
        line = ""
        for word in words:
            trial = word if not line else line + " " + word
            if font.size(trial)[0] <= max_width or not line:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
    return lines


class Typewriter:
    """Reveals text at `cps` characters per second."""

    def __init__(self, text, cps=45.0):
        self.text = text
        self.cps = cps
        self.time = 0.0

    def update(self, dt):
        self.time += max(0.0, dt)

    @property
    def count(self):
        return min(len(self.text), int(self.time * self.cps))

    @property
    def visible(self):
        return self.text[:self.count]

    @property
    def done(self):
        return self.count >= len(self.text)

    def skip(self):
        self.time = len(self.text) / self.cps if self.cps > 0 else 0.0


class Button:
    """Flat button. Pops on hover, squashes on press, greys out when disabled."""

    def __init__(self, rect, label, font, accent=theme.SKY, enabled=True):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.font = font
        self.accent = accent
        self.enabled = enabled
        self.hover = False
        self.pressed = False
        self.scale = 1.0
        self._tween = None

    def _target(self):
        if not self.enabled:
            return 1.0
        if self.pressed:
            return PRESS_SCALE
        return HOVER_SCALE if self.hover else 1.0

    def _retarget(self):
        target = self._target()
        if abs(target - self.scale) > 1e-6 and (self._tween is None or self._tween.end != target):
            self._tween = Tween(self.scale, target, POP_SECONDS, ease_out_back)

    def handle_event(self, event):
        """Return True when the button was clicked (released over it)."""
        if not self.enabled:
            self.hover = self.pressed = False
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.pressed = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            clicked = self.pressed and self.rect.collidepoint(event.pos)
            self.pressed = False
            self._retarget()
            return clicked
        self._retarget()
        return False

    def update(self, dt):
        self._retarget()
        if self._tween is not None:
            self.scale = self._tween.update(dt)
            if self._tween.done:
                self._tween = None

    def draw(self, surface):
        r = self.rect.copy()
        r.size = (int(r.w * self.scale), int(r.h * self.scale))
        r.center = self.rect.center
        if not self.enabled:
            fill, border, text = theme.NAVY, theme.SLATE, theme.SLATE
        elif self.hover or self.pressed:
            fill, border, text = theme.mix(theme.NAVY, self.accent, 0.35), self.accent, theme.PAPER
        else:
            fill, border, text = theme.NAVY, self.accent, theme.PAPER
        draw_panel(surface, r, fill=fill, border=border, shadow=self.enabled)
        img = self.font.render(self.label, True, text)
        surface.blit(img, img.get_rect(center=r.center))


class DialogueBox:
    """Speaker name + typewriter text in a panel. Click/key: skip, then advance."""

    def __init__(self, speaker, text, accent=theme.GOLD, cps=45.0):
        self.speaker = speaker
        self.accent = accent
        self.typer = Typewriter(text, cps)

    def update(self, dt):
        self.typer.update(dt)

    def advance(self):
        """First call completes the line; returns True once it was already complete."""
        if self.typer.done:
            return True
        self.typer.skip()
        return False

    def draw(self, surface, rect, font, name_font=None):
        rect = pygame.Rect(rect)
        draw_panel(surface, rect, border=self.accent)
        name_font = name_font or font
        name = name_font.render(self.speaker.upper(), True, self.accent)
        surface.blit(name, (rect.x + theme.PAD, rect.y + theme.PAD))
        y = rect.y + theme.PAD * 2 + name.get_height()
        lines = wrap_text(self.typer.visible, font, rect.w - theme.PAD * 2)
        for line in lines:
            if y + font.get_linesize() > rect.bottom - theme.PAD // 2:
                break
            surface.blit(font.render(line, True, theme.PAPER), (rect.x + theme.PAD, y))
            y += font.get_linesize()
