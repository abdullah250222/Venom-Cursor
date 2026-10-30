import math
import random
import pygame

from .config import MOUSE_INFLUENCE, DOT_COLOR
from .utils import distance

class Particle:
    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.x = random.uniform(0, width)
        self.y = random.uniform(0, height)

        self.vx = random.uniform(-22, 22)
        self.vy = random.uniform(-22, 22)

        self.radius = random.choice([1, 1, 2, 2, 3])
        self.phase = random.uniform(0, math.tau)

    @property
    def pos(self):
        return self.x, self.y

    def update(self, dt, mouse):
        self.phase += dt * random.uniform(0.25, 0.65)

        self.vx += math.sin(self.phase) * 5.0 * dt
        self.vy += math.cos(self.phase * 0.83) * 5.0 * dt

        # Mouse attraction
        dx = mouse[0] - self.x
        dy = mouse[1] - self.y
        d = math.hypot(dx, dy)

        if 8 < d < MOUSE_INFLUENCE:
            force = (1.0 - d / MOUSE_INFLUENCE) * 42.0

            self.vx += (dx / d) * force * dt
            self.vy += (dy / d) * force * dt

        # Damping
        self.vx *= 0.992
        self.vy *= 0.992


        speed = math.hypot(self.vx, self.vy)

        if speed > 52:
            self.vx = self.vx / speed * 52
            self.vy = self.vy / speed * 52

        self.x += self.vx * dt
        self.y += self.vy * dt

        if self.x < -5:
            self.x = self.width + 5
        elif self.x > self.width + 5:
            self.x = -5

        if self.y < -5:
            self.y = self.height + 5
        elif self.y > self.height + 5:
            self.y = -5


def draw_particles(surface, particles, mouse, show_dots=True):
    if not show_dots:
        return

    for particle in particles:
        d = distance(particle.pos, mouse)

        if d < 180:
            color = DOT_COLOR
        else:
            color = (75, 91, 108)

        radius = particle.radius

        if d < 85:
            radius += 1

        pygame.draw.circle(
            surface,
            color,
            (int(particle.x), int(particle.y)),
            radius
        )