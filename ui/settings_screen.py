"""The settings panel: music volume, effects volume, mute.

It is drawn over whatever is behind it (the menu, or the paused game) and
takes all input while open.  Keys: UP/DOWN choose a row, LEFT/RIGHT adjust,
M mutes, ESC closes.  The mouse works too: click or drag a slider, click the
sound chip or DONE.  Changes apply at once through `on_change`.
"""

import pygame

from systems.settings import STEP, clamp, step
from ui import theme
from ui.kit import blit_centered, draw_chip, draw_panel
from ui.fonts import ui_font

ROW_MUSIC, ROW_SFX, ROW_SOUND = 0, 1, 2
ROW_COUNT = 3
PANEL_SIZE = (540, 360)
TRACK_HEIGHT = 12


class SettingsScreen:
    def __init__(self, settings, on_change=None, size=(960, 640)):
        self.settings = settings
        self.on_change = on_change
        self.size = size
        self.selected = ROW_MUSIC
        self.closed = True
        self._dragging = None
        self.dim = pygame.Surface(size, pygame.SRCALPHA)
        self.dim.fill((4, 6, 14, 190))
        self.title_font = ui_font(56, bold=True)
        self.label_font = ui_font(28)
        self.small_font = ui_font(22)
        self.chip_font = ui_font(26)
        self.panel = pygame.Rect((0, 0), PANEL_SIZE)
        self.panel.center = (size[0] // 2, size[1] // 2)

    # --- geometry (also used by the tests) -----------------------------------
    def row_y(self, row):
        return self.panel.y + 100 + row * 62

    def track_rect(self, row):
        return pygame.Rect(self.panel.x + 190, self.row_y(row) - TRACK_HEIGHT // 2,
                           250, TRACK_HEIGHT)

    def sound_chip(self):
        chip = pygame.Rect(0, 0, 160, 34)
        chip.midleft = (self.panel.x + 190, self.row_y(ROW_SOUND))
        return chip

    def done_chip(self):
        chip = pygame.Rect(0, 0, 160, 40)
        chip.midbottom = (self.panel.centerx, self.panel.bottom - 42)
        return chip

    def value_at(self, x, row):
        track = self.track_rect(row)
        return clamp(round((x - track.x) / track.width, 2))

    # --- state ---------------------------------------------------------------
    def open(self):
        self.closed = False
        self.selected = ROW_MUSIC
        self._dragging = None

    def close(self):
        self.closed = True
        self._dragging = None
        self.settings.save()

    def value(self, row):
        return self.settings.music if row == ROW_MUSIC else self.settings.sfx

    def _set(self, row, value):
        before = self.value(row)
        if row == ROW_MUSIC:
            self.settings.set_music(value)
        else:
            self.settings.set_sfx(value)
        if self.value(row) != before:
            self._changed("music" if row == ROW_MUSIC else "sfx")

    def _toggle_mute(self):
        self.settings.toggle_muted()
        self._changed("mute")

    def _changed(self, kind):
        if self.on_change:
            self.on_change(kind)

    # --- input -----------------------------------------------------------------
    def handle_event(self, event):
        """Returns True: while open, the panel consumes every event."""
        if self.closed:
            return False
        if event.type == pygame.KEYDOWN:
            self._key(event.key)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._press(event.pos)
        elif event.type == pygame.MOUSEMOTION and self._dragging is not None:
            self._set(self._dragging, self.value_at(event.pos[0], self._dragging))
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = None
        return True

    def _key(self, key):
        if key == pygame.K_ESCAPE:
            self.close()
        elif key == pygame.K_UP:
            self.selected = (self.selected - 1) % ROW_COUNT
        elif key == pygame.K_DOWN:
            self.selected = (self.selected + 1) % ROW_COUNT
        elif key == pygame.K_m:
            self._toggle_mute()
        elif key in (pygame.K_LEFT, pygame.K_RIGHT):
            direction = 1 if key == pygame.K_RIGHT else -1
            if self.selected == ROW_SOUND:
                self._toggle_mute()
            else:
                self._set(self.selected, step(self.value(self.selected), direction * STEP))
        elif key in (pygame.K_RETURN, pygame.K_SPACE, pygame.K_KP_ENTER):
            if self.selected == ROW_SOUND:
                self._toggle_mute()
            else:
                self.close()

    def _press(self, pos):
        for row in (ROW_MUSIC, ROW_SFX):
            if self.track_rect(row).inflate(16, 28).collidepoint(pos):
                self.selected = row
                self._dragging = row
                self._set(row, self.value_at(pos[0], row))
                return
        if self.sound_chip().collidepoint(pos):
            self.selected = ROW_SOUND
            self._toggle_mute()
        elif self.done_chip().collidepoint(pos):
            self.close()

    # --- drawing ---------------------------------------------------------------
    def draw(self, surface, tick=0):
        if self.closed:
            return
        surface.blit(self.dim, (0, 0))
        panel = draw_panel(surface, self.panel, fill=theme.mix(theme.INK, theme.NAVY, 0.7),
                           border=theme.SKY)
        blit_centered(surface, self.title_font.render("SETTINGS", True, theme.PAPER),
                      (panel.centerx, panel.y + 42))
        muted = self.settings.muted
        for row, (name, colour) in enumerate((("MUSIC", theme.TEAL), ("EFFECTS", theme.SKY),
                                              ("SOUND", theme.GOLD))):
            y = self.row_y(row)
            active = row == self.selected
            label = self.label_font.render(name, True, theme.PAPER if active else theme.MIST)
            surface.blit(label, (panel.x + 52, y - label.get_height() // 2))
            if active:
                pygame.draw.polygon(surface, theme.GOLD, [(panel.x + 30, y - 8),
                                                          (panel.x + 30, y + 8),
                                                          (panel.x + 40, y)])
            if row == ROW_SOUND:
                draw_chip(surface, self.sound_chip(), "MUTED" if muted else "ON",
                          self.chip_font, fg=theme.CORAL if muted else theme.TEAL,
                          border=theme.CORAL if muted else theme.TEAL, filled=muted)
                continue
            self._draw_slider(surface, row, colour if not muted else theme.SLATE, active)

        draw_chip(surface, self.done_chip(), "DONE", self.chip_font, fg=theme.PAPER,
                  border=theme.SLATE)
        blit_centered(surface, self.small_font.render(
            "UP/DOWN choose   LEFT/RIGHT adjust   M mute   ESC close", True, theme.MIST),
            (panel.centerx, panel.bottom - 20))

    def _draw_slider(self, surface, row, colour, active):
        track = self.track_rect(row)
        pygame.draw.rect(surface, theme.mix(theme.NAVY, theme.INK, 0.4), track, border_radius=6)
        value = self.value(row)
        fill = pygame.Rect(track.x, track.y, int(track.width * value), track.height)
        if fill.width:
            pygame.draw.rect(surface, colour, fill, border_radius=6)
        knob = (track.x + int(track.width * value), track.centery)
        pygame.draw.circle(surface, theme.PAPER if active else theme.MIST, knob, 10 if active else 8)
        pygame.draw.circle(surface, colour, knob, 10 if active else 8, 2)
        text = self.small_font.render(f"{round(value * 100)}%", True, theme.PAPER)
        surface.blit(text, (track.right + 14, track.centery - text.get_height() // 2))
