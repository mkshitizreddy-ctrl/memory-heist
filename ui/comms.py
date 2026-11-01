"""
ui/comms.py
Owner: Member 1 - Core Game System

CommsFeed shows the radio lines from core.comms while a level is playing.
Like SoundEvents it watches the game state once a frame, so levels never
call it. Non-blocking: lines appear, type out, hold, then give way to the next.
"""

import pygame

from core.comms import DANGER_RATIO, line_for
from core.easing import Tween, ease_out_back
from core.hero_portrait import make_portrait
from ui import theme
from ui.kit import DialogueBox, draw_panel

SPEAKER_STYLE = {
    "Echo": (theme.TEAL, "echo"),
    "WARDEN": (theme.CORAL, "warden"),
    "Ghost": (theme.GOLD, "ghost"),
}
HOLD_SECONDS = 3.0
MISTAKE_COOLDOWN = 5.0
QUEUE_LIMIT = 2
PORTRAIT = 32
TOAST_HEIGHT = 40
TOAST_WIDTH = 700
TOAST_ALPHA = 235
SLIDE_SECONDS = 0.25


class CommsFeed:
    def __init__(self, hold=HOLD_SECONDS, cooldown=MISTAKE_COOLDOWN):
        self.hold = hold
        self.cooldown = cooldown
        self.queue = []
        self.current = None
        self.held = 0.0
        self.slide = None
        self._previous = None
        self._mistakes = {}
        self._progress = {}
        self._danger_done = set()
        self._cooldown_left = 0.0
        self._tick = 0

    # --- events -----------------------------------------------------------
    def say(self, speaker, text, force=False):
        if not force and len(self.queue) >= QUEUE_LIMIT:
            return False
        style = SPEAKER_STYLE.get(speaker, (theme.MIST, None))
        self.queue.append((speaker, DialogueBox(speaker, text, accent=style[0], cps=55.0)))
        return True

    def _trigger(self, level, moment, counters=None, force=False):
        count = counters.get(level, 0) if counters is not None else 0
        found = line_for(level, moment, count)
        if found and self.say(found[0], found[1], force=force) and counters is not None:
            counters[level] = count + 1

    def clear(self):
        self.queue = []
        self.current = None
        self.held = 0.0
        self.slide = None

    def observe(self, state, level, security, security_max, gates=0):
        """Compare this frame with the last and queue what changed."""
        now = (state, level, security, gates)
        previous, self._previous = self._previous, now
        if state != "playing":
            self.clear()
            return
        if previous is None or previous[0] != "playing" or previous[1] != level:
            if previous is None or previous[1] != level:
                self._danger_done.discard(level)
                self._mistakes.pop(level, None)
                self._progress.pop(level, None)
            self.clear()
            self._trigger(level, "enter", force=True)
            return
        _, _, old_security, old_gates = previous
        if gates > old_gates:
            self._trigger(level, "progress", self._progress)
        if security > old_security:
            ratio = security / security_max if security_max > 0 else 0.0
            if ratio >= DANGER_RATIO and level not in self._danger_done:
                self._danger_done.add(level)
                self._trigger(level, "danger", force=True)
            elif self._cooldown_left <= 0:
                self._cooldown_left = self.cooldown
                self._trigger(level, "mistake", self._mistakes)

    # --- per-frame --------------------------------------------------------
    def update(self, dt):
        dt = max(0.0, dt)
        self._tick += 1
        self._cooldown_left = max(0.0, self._cooldown_left - dt)
        self._next()
        if self.current is None:
            return
        box = self.current[1]
        box.update(dt)
        if self.slide is not None:
            self.slide.update(dt)
        if box.typer.done:
            self.held += dt
            if self.held >= self.hold:
                self.current = None
                self._next()                 # no empty frame between lines

    def _next(self):
        if self.current is None and self.queue:
            self.current = self.queue.pop(0)
            self.held = 0.0
            self.slide = Tween(0.0, 1.0, SLIDE_SECONDS, ease_out_back)

    # --- drawing ----------------------------------------------------------
    def draw(self, surface, font, name_font=None, rect=None):
        """Slim one-line toast along the bottom edge.

        Legacy levels use the whole screen, so the toast stays small and
        semi-transparent. A level that reserves a strip can pass its own `rect`.
        """
        if self.current is None:
            return
        speaker, box = self.current
        w, h = surface.get_size()
        rect = pygame.Rect(rect) if rect else pygame.Rect(
            16, h - TOAST_HEIGHT - 8, min(TOAST_WIDTH, w - 32), TOAST_HEIGHT)
        progress = self.slide.value if self.slide is not None else 1.0
        rect.y += int((1.0 - min(1.0, progress)) * 30)
        accent = box.accent

        toast = pygame.Surface(rect.size, pygame.SRCALPHA)
        draw_panel(toast, toast.get_rect(), border=accent, shadow=False)
        name_font = name_font or font
        name = name_font.render(speaker.upper() + ":", True, accent)
        toast.blit(name, (theme.PAD, (rect.h - name.get_height()) // 2))
        _, portrait_name = SPEAKER_STYLE.get(speaker, (None, None))
        right = rect.w - theme.PAD // 2
        if portrait_name:
            img = make_portrait(portrait_name, PORTRAIT, tick=self._tick,
                                alert=(speaker == "WARDEN"))
            toast.blit(img, (rect.w - PORTRAIT - theme.PAD // 2, (rect.h - PORTRAIT) // 2))
            right = rect.w - PORTRAIT - theme.PAD
        text = font.render(box.typer.visible, True, theme.PAPER)
        x = theme.PAD + name.get_width() + 8
        clip = pygame.Rect(0, 0, max(0, right - x), rect.h)
        toast.blit(text, (x, (rect.h - text.get_height()) // 2), clip)
        toast.set_alpha(TOAST_ALPHA)
        surface.blit(toast, rect)
