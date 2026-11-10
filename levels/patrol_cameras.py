"""
levels/patrol_cameras.py
Owner: Member 5 (UI)

Floor 3, Room 2 - the camera gallery.  The wall board shows

    while camera.on:
        sweep()
    camera.on = False      # <- the gate opening runs this line

and the room does exactly that: ceiling cameras sweep sight cones across the
floor until the room's question is answered, which switches them off.  Stand in
a cone long enough and you are spotted (score only).  Pure logic and drawing;
Level 3 asks which cone has the player and when the cameras are on.
"""

import math

import pygame

GRACE = 2.0                       # cameras look away for this long after entering or a hit
DETECT = 0.6                      # seconds inside a cone before it counts as seen
CONE_LENGTH = 330
MOUNT_Y = 152                     # the wall's foot, in screen space

# difficulty -> (cones, half angle in degrees, swing speed multiplier)
SETTINGS = {"easy": (2, 18, 0.8), "medium": (3, 20, 1.0), "hard": (3, 23, 1.25)}

# x of the mount, swing amplitude (degrees), period (seconds), phase (radians)
CAMERAS = (
    (330, 38, 5.2, 0.0),
    (610, 34, 4.4, math.pi),
    (770, 28, 3.8, math.pi / 2),
)

SAFE = (255, 235, 140)
SEEN = (255, 60, 60)


class CameraBank:
    def __init__(self, difficulty="medium"):
        count, half, speed = SETTINGS.get(difficulty, SETTINGS["medium"])
        self.half = half
        self.speed = speed
        self.cameras = CAMERAS[:count] if count < 3 else CAMERAS
        self.clock = 0.0
        self.on = True
        self.dwell = 0.0
        self.seen_by = None

    # ---- geometry -------------------------------------------------------

    def angle(self, index):
        """Direction of camera `index` in degrees; 90 is straight down."""
        x, amplitude, period, phase = self.cameras[index]
        return 90 + amplitude * math.sin(self.clock * self.speed * 2 * math.pi / period + phase)

    def mount(self, index):
        return (self.cameras[index][0], MOUNT_Y)

    def cone(self, index):
        """The cone's triangle (three screen points)."""
        mx, my = self.mount(index)
        a = self.angle(index)
        points = [(mx, my)]
        for edge in (-self.half, self.half):
            r = math.radians(a + edge)
            points.append((mx + CONE_LENGTH * math.cos(r), my + CONE_LENGTH * math.sin(r)))
        return points

    def inside(self, index, point):
        mx, my = self.mount(index)
        dx, dy = point[0] - mx, point[1] - my
        if dy <= 0 or math.hypot(dx, dy) > CONE_LENGTH:
            return False
        diff = abs(math.degrees(math.atan2(dy, dx)) - self.angle(index))
        return diff <= self.half

    def watching(self):
        return self.on and self.clock >= GRACE

    def camera_seeing(self, rects):
        """Index of the first camera whose cone holds any of the rects, or None."""
        for index in range(len(self.cameras)):
            for rect in rects:
                points = (rect.center, rect.topleft, rect.topright, rect.bottomleft, rect.bottomright)
                if any(self.inside(index, p) for p in points):
                    return index
        return None

    # ---- time -----------------------------------------------------------

    def update(self, dt, rects):
        """Advance the sweep.  Returns the camera index when somebody is spotted."""
        self.clock += max(0.0, dt)

        if not self.watching():
            self.dwell, self.seen_by = 0.0, None
            return None

        seen = self.camera_seeing(rects)
        self.seen_by = seen

        if seen is None:
            self.dwell = max(0.0, self.dwell - dt * 2)
            return None

        self.dwell += dt
        if self.dwell >= DETECT:
            self.dwell = 0.0
            return seen
        return None

    def rearm(self):
        self.clock = 0.0
        self.dwell, self.seen_by = 0.0, None

    def switch_off(self):
        self.on = False
        self.dwell, self.seen_by = 0.0, None

    def light_rects(self, origin):
        """(rect, phase) pieces for the room lighting, in room-local coordinates."""
        if not self.on:
            return []
        pieces = []
        for index in range(len(self.cameras)):
            phase = "active" if self.seen_by == index else "warning"
            mx, my = self.mount(index)
            r = math.radians(self.angle(index))
            for d in (110, 230):
                cx, cy = mx + d * math.cos(r) - origin[0], my + d * math.sin(r) - origin[1]
                pieces.append((pygame.Rect(int(cx) - 20, int(cy) - 20, 40, 40), phase))
        return pieces

    # ---- drawing --------------------------------------------------------

    def draw(self, surface, t):
        for index in range(len(self.cameras)):
            if self.on:
                self._draw_cone(surface, index, t)
            self._draw_camera(surface, index, t)

    def _draw_cone(self, surface, index, t):
        points = self.cone(index)
        xs, ys = [p[0] for p in points], [p[1] for p in points]
        box = pygame.Rect(int(min(xs)) - 2, int(min(ys)) - 2, int(max(xs) - min(xs)) + 4, int(max(ys) - min(ys)) + 4)
        box = box.clip(pygame.Rect(40, 152, 880, 330))
        if box.width <= 0 or box.height <= 0:
            return
        local = [(p[0] - box.x, p[1] - box.y) for p in points]

        seen = self.seen_by == index
        colour = SEEN if seen else SAFE
        layer = pygame.Surface(box.size, pygame.SRCALPHA)
        pygame.draw.polygon(layer, (*colour, 70 if seen else 42), local)

        # scan rings: the cone reads as a beam, not a flat triangle
        mx, my = local[0]
        for k in range(1, 6):
            reach = (k * 56 + (t * 40) % 56) % CONE_LENGTH
            a0, a1 = self.angle(index) - self.half, self.angle(index) + self.half
            arc = [(mx + reach * math.cos(math.radians(a0 + (a1 - a0) * s / 8)),
                    my + reach * math.sin(math.radians(a0 + (a1 - a0) * s / 8))) for s in range(9)]
            pygame.draw.lines(layer, (*colour, 90), False, arc, 1)

        edge = (*colour, 230 if seen else 170)
        dash = 0 if seen else 1                                   # tracking edges are solid, idle ones dashed
        for a, b in ((local[0], local[1]), (local[0], local[2])):
            if dash:
                for s in range(0, 20, 2):
                    p0 = (a[0] + (b[0] - a[0]) * s / 20, a[1] + (b[1] - a[1]) * s / 20)
                    p1 = (a[0] + (b[0] - a[0]) * (s + 1) / 20, a[1] + (b[1] - a[1]) * (s + 1) / 20)
                    pygame.draw.line(layer, edge, p0, p1, 2)
            else:
                pygame.draw.line(layer, edge, a, b, 3)
        surface.blit(layer, box.topleft)

    def _draw_camera(self, surface, index, t):
        mx, my = self.mount(index)
        pygame.draw.rect(surface, (38, 34, 62), (mx - 12, my - 8, 24, 10), border_radius=3)
        pygame.draw.rect(surface, (80, 62, 135), (mx - 12, my - 8, 24, 10), 1, border_radius=3)
        r = math.radians(self.angle(index) if self.on else 90)
        tip = (mx + 14 * math.cos(r), my + 14 * math.sin(r))
        pygame.draw.line(surface, (150, 150, 168), (mx, my), tip, 6)
        seen = self.on and self.seen_by == index
        lens = SEEN if seen else ((255, 190, 60) if self.on else (95, 95, 110))
        pygame.draw.circle(surface, lens, (int(tip[0]), int(tip[1])), 4)
        if self.on and int(t * 2) % 2 == 0:
            pygame.draw.circle(surface, SEEN, (mx - 8, my - 3), 2)      # REC
