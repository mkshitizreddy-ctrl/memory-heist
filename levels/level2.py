"""Level 2 - Security Grid: arithmetic, comparison and logical operators."""
import ast
import operator

import pygame

from levels.common import (BG, PANEL, GREEN, RED, YELLOW, WHITE, GREY,
                           ClickTracker, draw_button, draw_text, load_level_data)

DEFAULT_DATA = {
    "puzzles": [
        {"type": "number", "goal": 42, "tiles": [6, 7, "*"],
         "prompt": "Build an expression that equals 42 (use every tile)."},
        {"type": "number", "goal": 19, "tiles": [4, 3, 5, "+", "*"],
         "prompt": "Make 19. Remember: * happens before +."},
        {"type": "bool", "tiles": [3, ">=", 2, "and", 5, "<", 9],
         "prompt": "clearance = 3. Build a condition that is True (use every tile)."},
        {"type": "bool", "tiles": [1, ">", 2, "or", 4, "==", 4],
         "prompt": "Build a condition that is True using 'or'."},
    ]
}

_BIN = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul}
_CMP = {ast.Gt: operator.gt, ast.Lt: operator.lt, ast.GtE: operator.ge,
        ast.LtE: operator.le, ast.Eq: operator.eq, ast.NotEq: operator.ne}


def safe_eval(expr):
    """Evaluate a tiny arithmetic/comparison/logic expression; None if invalid."""
    def ev(node):
        """Recursively evaluate a whitelisted AST node."""
        if isinstance(node, ast.Expression):
            return ev(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, bool)):
            return node.value
        if isinstance(node, ast.BinOp):
            return _BIN[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.BoolOp):
            values = [ev(v) for v in node.values]
            return all(values) if isinstance(node.op, ast.And) else any(values)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
            return not ev(node.operand)
        if isinstance(node, ast.Compare):
            left = ev(node.left)
            for op, comp in zip(node.ops, node.comparators):
                right = ev(comp)
                if not _CMP[type(op)](left, right):
                    return False
                left = right
            return True
        raise ValueError("not allowed")

    try:
        return ev(ast.parse(expr, mode="eval"))
    except (SyntaxError, ValueError, KeyError, TypeError):
        return None


class Level2:
    """Security Grid: click tiles to build an expression that matches the goal."""

    def __init__(self, player=None):
        """Load puzzle data and set up level state."""
        self.player = player
        data = load_level_data("level2", DEFAULT_DATA)
        self.puzzles = data.get("puzzles", DEFAULT_DATA["puzzles"])
        self.index = 0
        self.complete = False
        self.expr = []          # tile indices in the order clicked
        self.message = "Click tiles to build the expression, then press SUBMIT."
        self.message_color = WHITE
        self.clicks = ClickTracker()
        self.font = pygame.font.SysFont("consolas", 26)
        self.big = pygame.font.SysFont("consolas", 36, bold=True)

    def _tiles(self):
        """Return the current puzzle's tiles."""
        return self.puzzles[self.index]["tiles"]

    def _tile_rects(self):
        """Return one clickable rect per tile."""
        return [pygame.Rect(60 + i * 90, 300, 80, 60) for i in range(len(self._tiles()))]

    def _buttons(self):
        """Return the Undo / Clear / Submit button rects."""
        return {"UNDO": pygame.Rect(60, 470, 140, 55),
                "CLEAR": pygame.Rect(220, 470, 140, 55),
                "SUBMIT": pygame.Rect(380, 470, 180, 55)}

    def _expression_text(self):
        """Return the built expression as a string."""
        tiles = self._tiles()
        return " ".join(str(tiles[i]) for i in self.expr)

    def update(self, dt):
        """Handle clicks on tiles and buttons."""
        clicked = self.clicks.clicked()
        if self.complete or not clicked:
            return
        pos = pygame.mouse.get_pos()
        for i, rect in enumerate(self._tile_rects()):
            if rect.collidepoint(pos) and i not in self.expr:
                self.expr.append(i)
                return
        for name, rect in self._buttons().items():
            if rect.collidepoint(pos):
                if name == "UNDO" and self.expr:
                    self.expr.pop()
                elif name == "CLEAR":
                    self.expr.clear()
                elif name == "SUBMIT":
                    self._submit()
                return

    def _submit(self):
        """Check the expression against the current puzzle's goal."""
        puzzle = self.puzzles[self.index]
        if len(self.expr) != len(self._tiles()):
            self._fail("Use every tile before submitting.")
            return
        result = safe_eval(self._expression_text())
        if result is None:
            self._fail("Invalid expression - check the order of tiles.")
            return
        if puzzle["type"] == "number":
            ok = isinstance(result, int) and not isinstance(result, bool) and result == puzzle["goal"]
        else:
            ok = result is True
        if ok:
            self.index += 1
            self.expr = []
            if self.index >= len(self.puzzles):
                self.complete = True
                self.message = "SECURITY CODE ACCEPTED - grid unlocked!"
            else:
                self.message = "Correct! Next panel."
            self.message_color = GREEN
        else:
            self._fail(f"That evaluates to {result}. Try again.")

    def _fail(self, text):
        """Show an error message."""
        self.message = text
        self.message_color = RED

    def render(self, surface):
        """Draw the prompt, tiles, current expression and buttons."""
        surface.fill(BG)
        draw_text(surface, self.big, "LEVEL 2 - SECURITY GRID", (60, 30), YELLOW)
        if self.complete:
            draw_text(surface, self.big, "GRID UNLOCKED", (60, 200), GREEN)
            draw_text(surface, self.font, self.message, (60, 590), self.message_color)
            return

        puzzle = self.puzzles[self.index]
        draw_text(surface, self.font, f"Panel {self.index + 1}/{len(self.puzzles)}", (60, 100), GREY)
        draw_text(surface, self.font, puzzle["prompt"], (60, 140), WHITE)
        goal = f"GOAL: {puzzle['goal']}" if puzzle["type"] == "number" else "GOAL: True"
        draw_text(surface, self.big, goal, (60, 190), GREEN)

        pygame.draw.rect(surface, PANEL, pygame.Rect(60, 380, 840, 60), border_radius=8)
        draw_text(surface, self.font, self._expression_text() or "(empty)", (75, 395))

        mouse = pygame.mouse.get_pos()
        for i, (rect, tile) in enumerate(zip(self._tile_rects(), self._tiles())):
            draw_button(surface, self.font, rect, tile, rect.collidepoint(mouse),
                        disabled=i in self.expr)
        for name, rect in self._buttons().items():
            draw_button(surface, self.font, rect, name, rect.collidepoint(mouse))
        draw_text(surface, self.font, self.message, (60, 590), self.message_color)

    def is_complete(self) -> bool:
        """Return True when every panel has been solved."""
        return self.complete
