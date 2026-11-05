"""
ui/menu.py
Owner: Member 5

Main menu and tutorial screen.
"""

import math

import pygame

from levels.common import draw_glow_text, GREEN
from core.difficulty import DIFFICULTIES
from core.hero_portrait import make_portrait
from ui import theme
from ui.backdrop import draw_backdrop
from ui.kit import blit_centered, draw_chip, draw_panel
from ui.fonts import ui_font

CONTROLS = [
    ("Levels 1, 2", "WASD to move, E to pick up, drop or answer"),
    ("Levels 3, 5, Final Vault", "1-4 keys - select an answer"),
    ("Levels 3, 4", "WASD to move, E to collect / interact"),
    ("Co-op (C)", "Player 2: arrow keys to move, Right Shift to interact"),
    ("Any time", "ESC to pause or quit, R to retry after a loss"),
]

DIFFICULTY_ORDER = ["easy", "medium", "hard"]
DIFFICULTY_TINT = {"easy": theme.TEAL, "medium": theme.GOLD, "hard": theme.CORAL}
PORTRAIT_SIZE = 96
ROW_HEIGHT = 30
SHIMMER_PERIOD = 300            # ticks between title shimmers
SHIMMER_SWEEP = 36              # ticks one shimmer takes to cross the title
ECHO_DIM, ECHO_FULL = 70, 255   # Echo's opacity with co-op off / on
ECHO_STEP = 12                  # opacity change per frame
FLASH_TICKS = 14                # how long a freshly chosen difficulty chip flashes


def approach(current, target, step):
    """Move `current` toward `target` by at most `step`, never overshooting."""
    if current < target:
        return min(target, current + step)
    return max(target, current - step)


def title_glow(tick):
    """0..1, slowly pulsing: how bright the title's glow is."""
    return 0.5 + 0.5 * math.sin(tick * 0.05)


def shimmer_progress(tick, period=SHIMMER_PERIOD, sweep=SHIMMER_SWEEP):
    """0..1 while a shimmer is crossing the title, None while it rests."""
    phase = tick % period
    if phase >= sweep:
        return None
    return phase / (sweep - 1)


def bob(tick, phase=0.0, amplitude=3):
    """A small whole-pixel up-and-down for the hero portraits."""
    return round(math.sin(tick * 0.06 + phase) * amplitude)


def difficulty_blurb(name):
    """One line saying what a difficulty changes, from the real preset numbers."""
    d = DIFFICULTIES.get(name, DIFFICULTIES["medium"])
    hints = "hints on" if d["hints_enabled"] else "hints off"
    return (f"timer x{d['timer_multiplier']:g}  |  {hints}  |  "
            f"security x{d['security_penalty_multiplier']:g}  |  score x{d['score_multiplier']:g}")


class MainMenu:
    def __init__(self):
        self.title_font = ui_font(64, bold=True)
        self.subtitle_font = ui_font(26)
        self.heading_font = ui_font(24)
        self.control_font = ui_font(22)
        self.prompt_font = ui_font(32)
        self.small_font = ui_font(18)
        self.tick = 0
        self.selected_difficulty = "medium"
        self.coop = False
        self.echo_alpha = ECHO_DIM
        self._flash = 0
        self.saved_text = None      # "Floor 3 - 450 pts" when a run can be continued

    def handle_event(self, event):
        """Let the player switch difficulty with 1/2/3 while at the menu."""
        if event.type != pygame.KEYDOWN:
            return
        chosen = {pygame.K_1: "easy", pygame.K_2: "medium", pygame.K_3: "hard"}.get(event.key)
        if chosen is not None:
            if chosen != self.selected_difficulty:
                self._flash = FLASH_TICKS
            self.selected_difficulty = chosen
        elif event.key == pygame.K_c:
            self.coop = not self.coop

    def layout(self, width=960):
        """Every block's rectangle, so nothing overlaps and tests can check it."""
        cx = width // 2
        panel = pygame.Rect(0, 0, 720, 36 + len(CONTROLS) * ROW_HEIGHT + 14)
        panel.midtop = (cx, 168)
        chips = []
        for i in range(3):
            chip = pygame.Rect(0, 0, 170, 34)
            chip.midtop = (cx + (i - 1) * 190, panel.bottom + 46)
            chips.append(chip)
        blurb = pygame.Rect(0, 0, 640, 22)
        blurb.midtop = (cx, chips[0].bottom + 6)
        coop = pygame.Rect(0, 0, 330, 34)
        coop.midtop = (cx, blurb.bottom + 8)
        start = pygame.Rect(0, 0, 340, 46)
        start.midtop = (cx, coop.bottom + 22)
        hint = pygame.Rect(0, 0, 420, 24)
        hint.midtop = (cx, start.bottom + 14)
        return {"panel": panel, "chips": chips, "blurb": blurb, "coop": coop, "start": start, "hint": hint,
                "heroes": [pygame.Rect(cx - 370, 30, PORTRAIT_SIZE, PORTRAIT_SIZE),
                           pygame.Rect(cx + 370 - PORTRAIT_SIZE, 30, PORTRAIT_SIZE, PORTRAIT_SIZE)]}

    def render(self, surface):
        self.tick += 1
        width = surface.get_width()
        lay = self.layout(width)

        draw_backdrop(surface, self.tick, theme.SKY)

        # Ghost always; Echo glows only when co-op is on
        ghost_rect, echo_rect = lay["heroes"]
        surface.blit(make_portrait("ghost", PORTRAIT_SIZE, self.tick), ghost_rect.move(0, bob(self.tick, 0.0)))
        echo = make_portrait("echo", PORTRAIT_SIZE, self.tick + 15)
        self.echo_alpha = approach(self.echo_alpha, ECHO_FULL if self.coop else ECHO_DIM, ECHO_STEP)
        if self.echo_alpha < ECHO_FULL:
            echo = echo.copy()
            echo.set_alpha(self.echo_alpha)
        surface.blit(echo, echo_rect.move(0, bob(self.tick, 2.0)))

        glow = theme.mix((20, 60, 40), (40, 140, 90), title_glow(self.tick))
        draw_glow_text(surface, self.title_font, "MEMORY HEIST",
                        (width // 2, 70), color=GREEN, glow_color=glow)
        self._draw_shimmer(surface, (width // 2, 70))
        subtitle = self.subtitle_font.render(
            "Escape the vault by solving 5 Python puzzles, then the Final Vault.",
            True, theme.MIST
        )
        blit_centered(surface, subtitle, (width // 2, 124))

        # How to play: a panel with a key chip per row
        panel = draw_panel(surface, lay["panel"], fill=theme.mix(theme.INK, theme.NAVY, 0.6),
                           border=theme.SLATE)
        blit_centered(surface, self.heading_font.render("HOW TO PLAY", True, theme.SKY),
                      (panel.centerx, panel.y + 20))
        y = panel.y + 36 + ROW_HEIGHT // 2
        for label, action in CONTROLS:
            tag = self.control_font.render(label, True, theme.GOLD)
            surface.blit(tag, (panel.x + 24, y - tag.get_height() // 2))
            line = self.control_font.render(action, True, theme.PAPER)
            surface.blit(line, (panel.x + 250, y - line.get_height() // 2))
            y += ROW_HEIGHT

        # Difficulty selector: three chips, the chosen one is solid
        blit_centered(surface, self.heading_font.render("DIFFICULTY (press 1/2/3)", True, theme.SKY),
                      (width // 2, lay["chips"][0].y - 16))
        flash = self._flash / FLASH_TICKS
        self._flash = max(0, self._flash - 1)
        for chip, key_num, name in zip(lay["chips"], ("1", "2", "3"), DIFFICULTY_ORDER):
            label = DIFFICULTIES[name]["label"]
            tint = DIFFICULTY_TINT[name]
            chosen = name == self.selected_difficulty
            draw_chip(surface, chip, f"[{key_num}] {label}", self.control_font,
                      fg=tint, border=theme.mix(tint, theme.PAPER, 0.6 * flash) if chosen else tint,
                      filled=chosen)
        blit_centered(surface, self.small_font.render(difficulty_blurb(self.selected_difficulty), True,
                                                      theme.MIST), lay["blurb"].center)

        mode = "ON (P2: arrow keys)" if self.coop else "OFF"
        draw_chip(surface, lay["coop"], f"CO-OP (press C): {mode}", self.control_font,
                  fg=theme.GOLD, border=theme.GOLD, filled=self.coop)

        # Start prompt: breathes
        pulse = 0.5 + 0.5 * abs((self.tick % 60) - 30) / 30
        start = lay["start"]
        pygame.draw.rect(surface, theme.mix(theme.INK, theme.TEAL, 0.25 + 0.2 * pulse), start,
                         border_radius=start.height // 2)
        pygame.draw.rect(surface, theme.mix(theme.TEAL, theme.PAPER, 0.4 * pulse), start,
                         width=2, border_radius=start.height // 2)
        blit_centered(surface, self.prompt_font.render("Press ENTER to start", True,
                                                       theme.mix(theme.TEAL, theme.PAPER, 0.6)),
                      start.center)
        self._draw_hint(surface, lay["hint"])

    def _draw_hint(self, surface, rect):
        """The key hints; with a saved run, a gold 'L: continue' leads the line."""
        rest = self.control_font.render("S: settings   |   F11: fullscreen", True, theme.MIST)
        if not self.saved_text:
            blit_centered(surface, rest, rect.center)
            return
        gold = self.control_font.render(f"L: continue ({self.saved_text})", True, theme.GOLD)
        gap = 22
        x = rect.centerx - (gold.get_width() + gap + rest.get_width()) // 2
        surface.blit(gold, (x, rect.centery - gold.get_height() // 2))
        surface.blit(rest, (x + gold.get_width() + gap, rect.centery - rest.get_height() // 2))

    def _draw_shimmer(self, surface, centre):
        """A bright diagonal band that sweeps across the title now and then."""
        progress = shimmer_progress(self.tick)
        if progress is None:
            return
        title = self.title_font.render("MEMORY HEIST", True, (255, 255, 255))
        w, h = title.get_size()
        band = pygame.Surface((w, h), pygame.SRCALPHA)
        x = int(progress * (w + 80)) - 40
        for i in range(-18, 19):
            alpha = int(170 * (1 - abs(i) / 18))
            pygame.draw.line(band, (255, 255, 255, alpha), (x + i + 10, 0), (x + i - 10, h))
        band.blit(title, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)     # keep only the lettering
        surface.blit(band, band.get_rect(center=centre))

    def handle_click(self, pos):
        pass
