"""
ui/screens.py
Win screen, lose screen.
"""

import pygame

from levels.common import draw_cyber_background, draw_glow_text, GREEN, RED
from systems.leaderboard import Leaderboard, MAX_NAME_LENGTH


class WinScreen:
    def __init__(self, leaderboard=None):
        self.title_font = pygame.font.Font(None, 68)
        self.subtitle_font = pygame.font.Font(None, 32)
        self.prompt_font = pygame.font.Font(None, 28)
        self.row_font = pygame.font.Font(None, 26)
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

    def render(self, surface, score=0):
        self.tick += 1
        width = surface.get_width()
        height = surface.get_height()

        draw_cyber_background(surface, self.tick)

        draw_glow_text(surface, self.title_font, "YOU ESCAPED!",
                        (width // 2, 100), color=GREEN)

        subtitle = self.subtitle_font.render(
            "Master Memory acquired. Mission complete.",
            True, (180, 200, 190)
        )
        surface.blit(subtitle, (width // 2 - subtitle.get_width() // 2, 160))

        score_text = self.subtitle_font.render(f"Final Score: {score}", True, (200, 220, 255))
        surface.blit(score_text, (width // 2 - score_text.get_width() // 2, 205))

        if self.breakdown:
            parts = self.breakdown
            detail = self.row_font.render(
                f"Base {parts['base']}  +  Time bonus {parts['time_bonus']}"
                f"  x{parts['multiplier']:g}",
                True, (150, 165, 190),
            )
            surface.blit(detail, (width // 2 - detail.get_width() // 2, 240))

        pulse = 140 + int(60 * abs((self.tick % 60) - 30) / 30)

        if self.entering:
            ask = self.prompt_font.render("Enter your name for the leaderboard:", True, (140, 200, 255))
            surface.blit(ask, (width // 2 - ask.get_width() // 2, 290))

            cursor = "_" if (self.tick // 30) % 2 == 0 else " "
            name_text = self.subtitle_font.render(self.name + cursor, True, (255, 230, 150))
            surface.blit(name_text, (width // 2 - name_text.get_width() // 2, 335))

            hint = self.prompt_font.render(
                "Press ENTER to save   |   ESC to skip",
                True, (pulse, pulse, pulse + 10)
            )
            surface.blit(hint, (width // 2 - hint.get_width() // 2, 395))
        else:
            heading = self.prompt_font.render("TOP SCORES", True, (140, 200, 255))
            surface.blit(heading, (width // 2 - heading.get_width() // 2, 278))

            y = 312
            for position, entry in enumerate(self.leaderboard.top(5), start=1):
                tag = " (co-op)" if entry.get("coop") else ""
                mine = position == self.rank
                color = (255, 230, 150) if mine else (200, 205, 215)
                left = width // 2 - 230
                surface.blit(self.row_font.render(f"{position}.", True, color), (left, y))
                surface.blit(self.row_font.render(entry["name"], True, color), (left + 36, y))
                score_img = self.row_font.render(str(entry["score"]), True, color)
                surface.blit(score_img, (left + 290 - score_img.get_width(), y))
                extra = f"{entry.get('difficulty', '')}{tag}"
                surface.blit(self.row_font.render(extra, True, color), (left + 310, y))
                y += 30

            prompt = self.prompt_font.render(
                "R: play again   |   M: menu   |   ESC: quit",
                True, (pulse, pulse, pulse + 10)
            )
            surface.blit(prompt, (width // 2 - prompt.get_width() // 2, height - 70))


class LoseScreen:
    def __init__(self):
        self.title_font = pygame.font.Font(None, 68)
        self.subtitle_font = pygame.font.Font(None, 32)
        self.prompt_font = pygame.font.Font(None, 28)
        self.tick = 0

    def render(self, surface, score=0):
        self.tick += 1
        width = surface.get_width()
        height = surface.get_height()

        draw_cyber_background(surface, self.tick)

        draw_glow_text(surface, self.title_font, "LOCKDOWN",
                        (width // 2, 180), color=RED, glow_color=(60, 15, 15))

        subtitle = self.subtitle_font.render("MISSION FAILED", True, (200, 130, 130))
        surface.blit(subtitle, (width // 2 - subtitle.get_width() // 2, 250))

        score_text = self.subtitle_font.render(f"Score: {score}", True, (180, 180, 190))
        surface.blit(score_text, (width // 2 - score_text.get_width() // 2, 310))

        pulse = 140 + int(60 * abs((self.tick % 60) - 30) / 30)
        prompt = self.prompt_font.render(
            "R: retry   |   M: menu   |   ESC: quit",
            True, (pulse, 155, 165)
        )
        surface.blit(prompt, (width // 2 - prompt.get_width() // 2, height - 80))