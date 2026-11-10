"""
ui/screens.py
Win screen, lose screen.
"""

import pygame

from levels.common import draw_glow_text, GREEN, RED
from core.hero_portrait import make_portrait
from systems.leaderboard import Leaderboard, MAX_NAME_LENGTH
from ui import theme
from ui.backdrop import draw_backdrop
from ui.kit import blit_centered, draw_chip, draw_panel
from ui.fonts import ui_font
from systems.achievements import BADGE_NAMES

PORTRAIT_SIZE = 96
BADGE_GAP = 8
COUNT_FRAMES = 45        # frames the final score takes to count up
TABLE_ROWS = 5


def shown_score(score, tick, frames=COUNT_FRAMES):
    """The score as displayed `tick` frames after the screen opened (ease-out count-up)."""
    if tick >= frames or score <= 0:
        return score
    progress = max(0, tick) / frames
    return int(score * (1 - (1 - progress) ** 3))


class WinScreen:
    def __init__(self, leaderboard=None):
        self.title_font = ui_font(68, bold=True)
        self.subtitle_font = ui_font(32)
        self.prompt_font = ui_font(28)
        self.row_font = ui_font(26)
        self.big_font = ui_font(72, bold=True)
        self.caption_font = ui_font(20)
        self.badge_font = ui_font(20)
        self.leaderboard = leaderboard or Leaderboard()
        self.tick = 0
        self.begin(0, "Medium", False)

    def begin(self, score, difficulty, coop, breakdown=None, badges=None):
        """Start a fresh win screen: ask for a name, then show the table."""
        self.score = score
        self.breakdown = breakdown
        self.badges = list(badges or [])        # [(badge id, is new this run)]
        self.difficulty = difficulty
        self.coop = coop
        self.name = ""
        self.entering = True
        self.rank = None
        self.tick = 0

    def skip_entry(self):
        """Leave name entry without saving a leaderboard entry."""
        self.entering = False

    def handle_event(self, event):
        """Type a name, then ENTER saves it to the leaderboard."""
        if event.type != pygame.KEYDOWN or not self.entering:
            return

        if event.key == pygame.K_RETURN:
            self.rank = self.leaderboard.add(
                self.name, self.score, self.difficulty, self.coop
            )
            self.entering = False
        elif event.key == pygame.K_BACKSPACE:
            self.name = self.name[:-1]
        elif (
            event.unicode
            and event.unicode.isprintable()
            and len(self.name) < MAX_NAME_LENGTH
        ):
            self.name += event.unicode

    def layout(self, width=960):
        cx = width // 2
        score = pygame.Rect(0, 0, 560, 118)
        score.midtop = (cx, 122)
        table = pygame.Rect(0, 0, 560, 254)
        table.midtop = (cx, score.bottom + 16)
        strip = pygame.Rect(0, 0, 900, 30)
        strip.midtop = (cx, table.bottom + 14)
        return {"score": score, "table": table, "badges": strip}

    def _draw_badges(self, surface, strip):
        """Chips for the badges this run earned; new ones are solid gold."""
        if not self.badges:
            return
        chips = []
        for badge_id, is_new in self.badges:
            text = BADGE_NAMES.get(badge_id, badge_id)
            if is_new:
                text = "NEW " + text
            chips.append((text, is_new, self.badge_font.size(text)[0] + 28))
        x = strip.centerx - (sum(w for _, _, w in chips) + BADGE_GAP * (len(chips) - 1)) // 2
        for text, is_new, w in chips:
            draw_chip(surface, pygame.Rect(x, strip.y, w, strip.height), text, self.badge_font,
                      fg=theme.GOLD, border=theme.GOLD, filled=is_new)
            x += w + BADGE_GAP

    def render(self, surface, score=0):
        self.tick += 1
        width = surface.get_width()
        height = surface.get_height()
        lay = self.layout(width)

        draw_backdrop(surface, self.tick, theme.TEAL)

        draw_glow_text(surface, self.title_font, "YOU ESCAPED!",
                        (width // 2, 66), color=GREEN)
        surface.blit(make_portrait("ghost", PORTRAIT_SIZE, self.tick), (width // 2 - 380, 22))
        echo = make_portrait("echo", PORTRAIT_SIZE, self.tick + 15)
        if not self.coop:
            echo = echo.copy()
            echo.set_alpha(70)
        surface.blit(echo, (width // 2 + 380 - PORTRAIT_SIZE, 22))

        # Score panel
        panel = draw_panel(surface, lay["score"], fill=theme.mix(theme.INK, theme.NAVY, 0.6),
                           border=theme.TEAL)
        blit_centered(surface, self.caption_font.render("FINAL SCORE", True, theme.MIST),
                      (panel.centerx, panel.y + 18))
        blit_centered(surface, self.big_font.render(f"{shown_score(score, self.tick)}", True, theme.GOLD),
                      (panel.centerx, panel.y + 56))
        if self.breakdown:
            parts = self.breakdown
            detail = self.row_font.render(
                f"Base {parts['base']}  +  Time bonus {parts['time_bonus']}"
                f"  x{parts['multiplier']:g}",
                True, theme.MIST,
            )
            blit_centered(surface, detail, (panel.centerx, panel.bottom - 18))
        else:
            blit_centered(surface, self.subtitle_font.render(
                "Master Memory acquired. Mission complete.", True, theme.MIST),
                (panel.centerx, panel.bottom - 18))

        self._draw_badges(surface, lay["badges"])

        pulse = 140 + int(60 * abs((self.tick % 60) - 30) / 30)
        table = draw_panel(surface, lay["table"], fill=theme.mix(theme.INK, theme.NAVY, 0.6),
                           border=theme.SLATE)

        if self.entering:
            blit_centered(surface, self.prompt_font.render(
                "Enter your name for the leaderboard:", True, theme.SKY),
                (table.centerx, table.y + 56))
            box = pygame.Rect(0, 0, 360, 52)
            box.center = (table.centerx, table.y + 125)
            pygame.draw.rect(surface, theme.INK, box, border_radius=10)
            pygame.draw.rect(surface, theme.GOLD, box, width=2, border_radius=10)
            cursor = "_" if (self.tick // 30) % 2 == 0 else " "
            blit_centered(surface, self.subtitle_font.render(self.name + cursor, True, theme.GOLD),
                          box.center)
            hint = self.prompt_font.render(
                "Press ENTER to save   |   ESC to skip",
                True, (pulse, pulse, pulse + 10)
            )
            blit_centered(surface, hint, (table.centerx, table.bottom - 40))
        else:
            blit_centered(surface, self.caption_font.render("TOP SCORES", True, theme.SKY),
                          (table.centerx, table.y + 22))
            y = table.y + 48
            left = table.x + 28
            entries = list(self.leaderboard.top(TABLE_ROWS))
            for position in range(len(entries) + 1, TABLE_ROWS + 1):     # empty slots stay visible
                slot_y = table.y + 48 + (position - 1) * 38
                surface.blit(self.row_font.render(f"{position}.", True, theme.SLATE), (left, slot_y))
                surface.blit(self.row_font.render("- - -", True, theme.SLATE), (left + 40, slot_y))
            for position, entry in enumerate(entries, start=1):
                tag = " (co-op)" if entry.get("coop") else ""
                mine = position == self.rank
                color = theme.GOLD if mine else theme.PAPER
                if mine:
                    band = pygame.Rect(table.x + 12, y - 4, table.width - 24, 34)
                    pygame.draw.rect(surface, theme.mix(theme.INK, theme.GOLD, 0.22), band,
                                     border_radius=8)
                surface.blit(self.row_font.render(f"{position}.", True, color), (left, y))
                surface.blit(self.row_font.render(entry["name"], True, color), (left + 40, y))
                score_img = self.row_font.render(str(entry["score"]), True, color)
                surface.blit(score_img, (left + 300 - score_img.get_width(), y))
                extra = f"{entry.get('difficulty', '')}{tag}"
                surface.blit(self.row_font.render(extra, True, theme.MIST if not mine else color),
                             (left + 330, y))
                y += 38

            prompt = self.prompt_font.render(
                "R: play again   |   M: menu   |   ESC: quit",
                True, (pulse, pulse, pulse + 10)
            )
            blit_centered(surface, prompt, (width // 2, height - 50))


LOSE_TIPS = {
    "level1": "TIP: read the value, then pick the chute. int, str, float or bool.",
    "level2": "TIP: step onto the breaker, read the relay, then throw it. Panels marked False zap.",
    "level3": "TIP: lanes warn before they fire. Read the loop, then cross.",
    "level4": "TIP: a dictionary looks things up by key, not by position.",
    "level5": "TIP: check which arguments the function gets and what it returns.",
    "final_vault": "TIP: every earlier floor shows up here. Take your time.",
}
LOSE_TIP_DEFAULT = "TIP: wrong answers raise security. Slow down and read the hints."


def lose_tip(level_name):
    """The tip for the floor where the run ended, or the general one."""
    return LOSE_TIPS.get(level_name, LOSE_TIP_DEFAULT)


class LoseScreen:
    def __init__(self):
        self.title_font = ui_font(68, bold=True)
        self.subtitle_font = ui_font(32)
        self.prompt_font = ui_font(28)
        self.big_font = ui_font(56, bold=True)
        self.caption_font = ui_font(20)
        self.tick = 0

    def layout(self, width=960):
        cx = width // 2
        eye = pygame.Rect(0, 0, 130, 130)
        eye.midtop = (cx, 40)
        score = pygame.Rect(0, 0, 360, 110)
        score.midtop = (cx, 332)
        tip = pygame.Rect(0, 0, 620, 44)
        tip.midtop = (cx, score.bottom + 22)
        return {"eye": eye, "score": score, "tip": tip}

    def render(self, surface, score=0, level=None):
        self.tick += 1
        width = surface.get_width()
        height = surface.get_height()
        lay = self.layout(width)

        draw_backdrop(surface, self.tick, theme.CORAL)

        # WARDEN's eye, alert, with a slow red pulse behind it
        eye = lay["eye"]
        glow = pygame.Surface((eye.width * 2, eye.height * 2), pygame.SRCALPHA)
        strength = 40 + int(30 * abs((self.tick % 90) - 45) / 45)
        pygame.draw.circle(glow, (255, 70, 70, strength), glow.get_rect().center, eye.width // 2 + 20)
        surface.blit(glow, glow.get_rect(center=eye.center))
        surface.blit(make_portrait("warden", eye.width, self.tick, alert=True), eye)

        draw_glow_text(surface, self.title_font, "LOCKDOWN",
                        (width // 2, 224), color=RED, glow_color=(60, 15, 15))
        blit_centered(surface, self.subtitle_font.render("MISSION FAILED", True, (220, 140, 140)),
                      (width // 2, 280))

        panel = draw_panel(surface, lay["score"], fill=theme.mix(theme.INK, theme.CORAL, 0.15),
                           border=theme.CORAL)
        blit_centered(surface, self.caption_font.render("SCORE", True, theme.MIST),
                      (panel.centerx, panel.y + 24))
        blit_centered(surface, self.big_font.render(f"{shown_score(score, self.tick)}", True, theme.PAPER),
                      (panel.centerx, panel.y + 68))

        tip = lay["tip"]
        blit_centered(surface, self.caption_font.render(
            lose_tip(level), True, theme.MIST), tip.center)

        pulse = 140 + int(60 * abs((self.tick % 60) - 30) / 30)
        prompt = self.prompt_font.render(
            "R: retry   |   M: menu   |   ESC: quit",
            True, (pulse, 155, 165)
        )
        blit_centered(surface, prompt, (width // 2, height - 50))
