"""
Memory Heist - Entry point
Run this file to start the game: python main.py
"""

import sys

import pygame

from core.display import enable_dpi_awareness
from core.game import Game


def main():
    enable_dpi_awareness()  # before the window opens, so text stays sharp
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
