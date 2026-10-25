"""
entities/particles.py
Owner: Member 1 - Core Game System

Small, short-lived spark particles for visual feedback (gate unlocks,
item pickups, etc). Self-contained — nothing else needs to know how
particles work internally.
"""

import random
import pygame

PARTICLE_LIFETIME = 0.5  # seconds
PARTICLE_COLOR = (120, 230, 160)


class ParticleBurst:
    def __init__(self, x, y, count=16):
        self.particles = []
        for _ in range(count):
            angle = random.uniform(0, 6.283)
            speed = random.uniform(60, 160)
            self.particles.append({
                "x": x, "y": y,
                "vx": speed * pygame.math.Vector2(1, 0).rotate_rad(angle).x,
                "vy": speed * pygame.math.Vector2(1, 0).rotate_rad(angle).y,
                "life": PARTICLE_LIFETIME,
            })

    def update(self, dt):
        for p in self.particles:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
        self.particles = [p for p in self.particles if p["life"] > 0]

    def is_done(self):
        return len(self.particles) == 0

    def draw(self, surface):
        for p in self.particles:
            alpha_ratio = max(0.0, p["life"] / PARTICLE_LIFETIME)
            radius = max(1, int(3 * alpha_ratio))
            pygame.draw.circle(surface, PARTICLE_COLOR, (int(p["x"]), int(p["y"])), radius)


class ParticleSystem:
    """Holds multiple active bursts so a level can fire-and-forget."""

    def __init__(self):
        self.bursts = []

    def spawn(self, x, y, count=16):
        self.bursts.append(ParticleBurst(x, y, count))

    def update(self, dt):
        for burst in self.bursts:
            burst.update(dt)
        self.bursts = [b for b in self.bursts if not b.is_done()]

    def draw(self, surface):
        for burst in self.bursts:
            burst.draw(surface)