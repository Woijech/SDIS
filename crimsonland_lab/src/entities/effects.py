from __future__ import annotations

import pygame


class CircleEffect:
    """Expanding ring effect used for impacts, pickups, and flashes."""

    def __init__(
        self,
        position: tuple[float, float] | pygame.Vector2,
        color: tuple[int, int, int],
        duration: float,
        start_radius: int,
        end_radius: int,
    ) -> None:
        """Create a circular effect that expands over time.

        Args:
            position: World position where the effect starts.
            color: RGB color of the ring.
            duration: Total lifetime in seconds.
            start_radius: Radius used at the beginning of the effect.
            end_radius: Radius reached when the effect expires.

        Returns:
            None.
        """
        self.position = pygame.Vector2(position)
        self.color = color
        self.duration = duration
        self.remaining = duration
        self.start_radius = start_radius
        self.end_radius = end_radius

    def update(self, dt: float) -> None:
        """Advance the effect lifetime.

        Args:
            dt: Frame delta time in seconds.

        Returns:
            None.
        """
        self.remaining -= dt

    @property
    def alive(self) -> bool:
        """Tell whether the effect should stay in the scene.

        Returns:
            ``True`` while the remaining lifetime is above zero.
        """
        return self.remaining > 0

    def draw(self, surface: pygame.Surface) -> None:
        """Render the expanding ring on the target surface.

        Args:
            surface: Surface that receives the visual effect.

        Returns:
            None.
        """
        progress = 1.0 - max(0.0, self.remaining) / self.duration
        radius = int(self.start_radius + (self.end_radius - self.start_radius) * progress)
        alpha = max(0, min(255, int(255 * (1 - progress))))

        overlay = pygame.Surface((radius * 2 + 4, radius * 2 + 4), pygame.SRCALPHA)
        pygame.draw.circle(overlay, (*self.color, alpha), (radius + 2, radius + 2), radius, width=3)
        surface.blit(overlay, (self.position.x - radius - 2, self.position.y - radius - 2))


class FloatingTextEffect:
    """Floating text sprite affected by velocity and gravity."""

    def __init__(
        self,
        position: tuple[float, float] | pygame.Vector2,
        surface: pygame.Surface,
        *,
        velocity: tuple[float, float] | pygame.Vector2,
        gravity: float,
        duration: float,
    ) -> None:
        """Create a floating text effect.

        Args:
            position: Initial position of the text center.
            surface: Pre-rendered text surface to display.
            velocity: Initial velocity vector in pixels per second.
            gravity: Downward acceleration applied every frame.
            duration: Total lifetime in seconds.

        Returns:
            None.
        """
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(velocity)
        self.gravity = gravity
        self.duration = duration
        self.remaining = duration
        self.surface = surface

    def update(self, dt: float) -> None:
        """Advance position and lifetime for the text effect.

        Args:
            dt: Frame delta time in seconds.

        Returns:
            None.
        """
        self.remaining -= dt
        self.velocity.y += self.gravity * dt
        self.position += self.velocity * dt

    @property
    def alive(self) -> bool:
        """Tell whether the text should stay active.

        Returns:
            ``True`` while the remaining lifetime is above zero.
        """
        return self.remaining > 0

    def draw(self, surface: pygame.Surface) -> None:
        """Render the text with fade-out applied.

        Args:
            surface: Surface that receives the visual effect.

        Returns:
            None.
        """
        if self.remaining <= 0:
            return

        progress = 1.0 - max(0.0, self.remaining) / self.duration
        alpha = max(0, min(255, int(255 * (1.0 - progress))))
        text_surface = self.surface.copy()
        text_surface.set_alpha(alpha)
        surface.blit(text_surface, text_surface.get_rect(center=(self.position.x, self.position.y)))
