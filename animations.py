"""Animation primitives: bounce, shake, etc."""

import math
import random


class BounceAnimation:
    """Sinusoidal vertical bounce."""

    def __init__(self, amplitude=10):
        self.amplitude = amplitude
        self.phase = 0.0

    def update(self, dt):
        """Returns (dx, dy, done). dy is upward offset."""
        self.phase += dt * 0.012
        dy = abs(math.sin(self.phase)) * self.amplitude
        done = self.phase > math.pi * 3
        return 0, dy, done


class ShakeAnimation:
    """Random horizontal jitter."""

    def __init__(self, duration=500, jitter=5):
        self.remaining = duration
        self.jitter = jitter

    def update(self, dt):
        """Returns (dx, dy, done)."""
        self.remaining -= dt
        if self.remaining <= 0:
            return 0, 0, True
        dx = (random.random() - 0.5) * self.jitter
        return dx, 0, False


class GravityDrop:
    """Fall with gravity and bounce on landing."""

    def __init__(self, start_y, target_y):
        self.y = start_y
        self.target_y = target_y
        self.vy = 0
        self.gravity = 0.0015  # px/ms^2
        self.bounce_count = 0

    def update(self, dt):
        """Returns (y_position, done)."""
        self.vy += self.gravity * dt
        self.y -= self.vy * dt  # y decreases as we fall (screen coords: y=0 at bottom)

        if self.y <= self.target_y:
            self.y = self.target_y
            self.vy *= -0.5  # bounce with damping
            self.bounce_count += 1

        done = self.bounce_count >= 3 or (
            self.bounce_count > 0 and abs(self.vy) < 0.05
        )
        return self.y, done
