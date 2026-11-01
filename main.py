"""
Memory Heist - Entry point
Run this file to start the game: python main.py
"""

import sys

import pygame

from core.game import Game


def main():
    game = Game()
    game.run()
    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
