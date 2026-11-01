"""
core/tilemap.py
Owner: Member 1 - Core Game System

Our own small tilemap + camera (pyscroll is GPL, so we do not depend on it).

A floor is authored as rows of ASCII characters, so a level designer can see
the layout in the source file:

    LAYOUT = [
        "##########",
        "#........#",
        "#..#..#..#",
        "##########",
    ]

`LEGEND` maps each character to a tile name; tiles named in SOLID block
movement. Tile art is drawn in code from the floor palette (ui.theme), so
the six floors share one style and only the colours change.
"""

import pygame

from ui import theme

TILE = 32

LEGEND = {
    "#": "wall",
    ".": "floor",
    ",": "floor_alt",
    " ": "void",
}
SOLID = frozenset({"wall", "void"})


class TileMap:
    def __init__(self, rows, legend=None, solid=SOLID, tile=TILE):
        if not rows:
            raise ValueError("map needs at least one row")
        width = max(len(r) for r in rows)
        legend = legend or LEGEND
        self.tile = tile
        self.solid_names = frozenset(solid)
        self.cols = width
        self.rows = len(rows)
        self.grid = []
        for y, row in enumerate(rows):
            line = []
            for x in range(width):
                ch = row[x] if x < len(row) else " "
                if ch not in legend:
                    raise ValueError(f"unknown tile {ch!r} at row {y}, col {x}")
                line.append(legend[ch])
            self.grid.append(line)

    @property
    def pixel_size(self):
        return self.cols * self.tile, self.rows * self.tile

    def in_bounds(self, tx, ty):
        return 0 <= tx < self.cols and 0 <= ty < self.rows

    def name_at(self, tx, ty):
        """Tile name; anything outside the map counts as void."""
        return self.grid[ty][tx] if self.in_bounds(tx, ty) else "void"

    def is_solid(self, tx, ty):
        return self.name_at(tx, ty) in self.solid_names

    def to_tile(self, px, py):
        return int(px // self.tile), int(py // self.tile)

    def tile_rect(self, tx, ty):
        return pygame.Rect(tx * self.tile, ty * self.tile, self.tile, self.tile)

    def collides(self, rect):
        """True if a world-space rect overlaps any solid tile."""
        x0, y0 = self.to_tile(rect.left, rect.top)
        x1, y1 = self.to_tile(rect.right - 1, rect.bottom - 1)
        return any(self.is_solid(x, y)
                   for y in range(y0, y1 + 1) for x in range(x0, x1 + 1))

    def move(self, rect, dx, dy):
        """Move a rect by (dx, dy), sliding along walls. Returns the new rect."""
        out = rect.copy()
        out.x += int(dx)
        if self.collides(out):
            out.x = rect.x
            step = 1 if dx > 0 else -1
            for _ in range(abs(int(dx))):
                out.x += step
                if self.collides(out):
                    out.x -= step
                    break
        start_y = out.y
        out.y += int(dy)
        if self.collides(out):
            out.y = start_y
            step = 1 if dy > 0 else -1
            for _ in range(abs(int(dy))):
                out.y += step
                if self.collides(out):
                    out.y -= step
                    break
        return out

    def visible_tiles(self, view_rect):
        """(tx, ty) pairs overlapping a world-space view rectangle."""
        x0, y0 = self.to_tile(max(0, view_rect.left), max(0, view_rect.top))
        x1, y1 = self.to_tile(view_rect.right - 1, view_rect.bottom - 1)
        x1, y1 = min(self.cols - 1, x1), min(self.rows - 1, y1)
        return [(x, y) for y in range(y0, y1 + 1) for x in range(x0, x1 + 1)]

    def render(self, surface, camera, tiles):
        """Draw only the tiles the camera can see. `tiles` = make_tiles(...)."""
        ox, oy = camera.offset()
        view = pygame.Rect(camera.x, camera.y, camera.view_w, camera.view_h)
        for tx, ty in self.visible_tiles(view):
            img = tiles.get(self.grid[ty][tx])
            if img is not None:
                surface.blit(img, (tx * self.tile - ox, ty * self.tile - oy))


class Camera:
    """Follows a target smoothly and never shows outside the world."""

    def __init__(self, view_w, view_h, world_w, world_h, smoothing=8.0):
        self.view_w, self.view_h = view_w, view_h
        self.world_w, self.world_h = world_w, world_h
        self.smoothing = smoothing
        self.x = 0.0
        self.y = 0.0
        self.shake = (0, 0)

    def _clamp_axis(self, value, view, world):
        if world <= view:                   # small world: centre it
            return (world - view) / 2
        return max(0.0, min(world - view, value))

    def _target(self, tx, ty):
        return (self._clamp_axis(tx - self.view_w / 2, self.view_w, self.world_w),
                self._clamp_axis(ty - self.view_h / 2, self.view_h, self.world_h))

    def snap(self, tx, ty):
        self.x, self.y = self._target(tx, ty)

    def follow(self, tx, ty, dt):
        goal_x, goal_y = self._target(tx, ty)
        k = 1.0 - pow(2.718281828, -self.smoothing * max(0.0, dt))
        self.x += (goal_x - self.x) * k
        self.y += (goal_y - self.y) * k

    def offset(self):
        """Integer draw offset, including shake. Pixel art must not blur."""
        return int(round(self.x)) - self.shake[0], int(round(self.y)) - self.shake[1]

    def world_to_screen(self, wx, wy):
        ox, oy = self.offset()
        return wx - ox, wy - oy

    def screen_to_world(self, sx, sy):
        ox, oy = self.offset()
        return sx + ox, sy + oy

    def is_visible(self, rect, margin=0):
        view = pygame.Rect(self.x, self.y, self.view_w, self.view_h).inflate(margin * 2, margin * 2)
        return view.colliderect(rect)


def make_tiles(level_name, tile=TILE):
    """Procedural tiles in the floor's colours (floor, floor_alt, wall, void)."""
    pal = theme.floor_palette(level_name)
    floor, accent = pal["floor"], pal["accent"]

    floor_img = pygame.Surface((tile, tile))
    floor_img.fill(floor)
    pygame.draw.rect(floor_img, theme.mix(floor, theme.INK, 0.25), (0, 0, tile, tile), 1)

    alt_img = floor_img.copy()
    alt_img.fill(theme.mix(floor, theme.PAPER, 0.06), (1, 1, tile - 2, tile - 2))

    wall_img = pygame.Surface((tile, tile))
    wall_img.fill(theme.mix(floor, theme.INK, 0.65))
    pygame.draw.rect(wall_img, theme.mix(floor, theme.INK, 0.4), (0, 0, tile, tile // 4))
    pygame.draw.rect(wall_img, theme.mix(accent, theme.INK, 0.35), (0, tile // 4, tile, 2))

    void_img = pygame.Surface((tile, tile))
    void_img.fill(theme.INK)

    return {"floor": floor_img, "floor_alt": alt_img, "wall": wall_img, "void": void_img}
