"""
core/game.py
Owner: Member 1 - Core Game System
...
"""
import sys
import pygame
from core.player import Player

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 640
FPS = 60
TITLE = "Memory Heist"
BG_COLOR = (10, 12, 20)


class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.state = "menu"
        self.player = Player(100, 100)
        self.wall = pygame.Rect(400, 200, 160, 40)          # ← ADD THIS

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000
            self.handle_events()
            self.update(dt)
            self.render()
        pygame.quit()
        sys.exit()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.running = False

    def update(self, dt):
        keys = pygame.key.get_pressed()
        old_rect = self.player.rect.copy()                  # ← ADD THIS
        self.player.handle_input(keys, dt)
        if self.player.rect.colliderect(self.wall):          # ← ADD THIS
            self.player.rect = old_rect                       # ← ADD THIS

    def render(self):
        self.screen.fill(BG_COLOR)
        pygame.draw.rect(self.screen, (150, 60, 60), self.wall)  # ← ADD THIS
        self.player.draw(self.screen)
        pygame.display.flip()

    def change_state(self, new_state: str):
        self.state = new_state