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

PORTRAIT_SIZE = 96


class WinScreen:
    def __init__(self, leaderboard=None):
        self.title_font = pygame.font.Font(None, 68)
        self.subtitle_font = pygame.font.Font(None, 32)
        self.prompt_font = pygame.font.Font(None, 28)
        self.row_font = pygame.font.Font(None, 26)
        self.big_font = pygame.font.Font(None, 72)
        self.caption_font = pygame.font.Font(None, 20)
        self.leaderboard = leaderboard or Leaderboard()
        self.tick = 0
        self.begin(0, "Medium", False)

    def begin(self, score, difficulty, coop, breakdown=None):
        """Start a fresh win screen: ask for a name, then show the table."""
        self.score = score
        self.breakdown = breakdown
        self.difficulty = difficulty
        self.coop = coop
        self.name = ""
        self.entering = True
        self.rank = None

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
        return {"score": score, "table": table}

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
        blit_centered(surface, self.big_font.render(f"{score}", True, theme.GOLD),
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
            for position, entry in enumerate(self.leaderboard.top(5), start=1):
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


class LoseScreen:
    def __init__(self):
        self.title_font = pygame.font.Font(None, 68)
        self.subtitle_font = pygame.font.Font(None, 32)
        self.prompt_font = pygame.font.Font(None, 28)
        self.big_font = pygame.font.Font(None, 56)
        self.caption_font = pygame.font.Font(None, 20)
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

    def render(self, surface, score=0):
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
        blit_centered(surface, self.big_font.render(f"{score}", True, theme.PAPER),
                      (panel.centerx, panel.y + 68))

        tip = lay["tip"]
        blit_centered(surface, self.caption_font.render(
            "TIP: wrong answers raise security. Slow down and read the hints.",
            True, theme.MIST), tip.center)

        pulse = 140 + int(60 * abs((self.tick % 60) - 30) / 30)
        prompt = self.prompt_font.render(
            "R: retry   |   M: menu   |   ESC: quit",
            True, (pulse, 155, 165)
        )
        blit_centered(surface, prompt, (width // 2, height - 50))
