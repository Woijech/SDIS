from __future__ import annotations

import pygame


class Projectile:
    """Moving damaging object fired by the player or enemies."""

    def __init__(
        self,
        position: pygame.Vector2,
        velocity: pygame.Vector2,
        damage: int,
        radius: int,
        color: tuple[int, int, int],
        from_enemy: bool = False,
        lifetime: float = 1.6,
    ) -> None:
        """Create a projectile with its current motion state.

        Args:
            position: Initial projectile position.
            velocity: Projectile velocity in pixels per second.
            damage: Damage dealt on collision.
            radius: Collision and render radius.
            color: RGB color used for drawing.
            from_enemy: Whether the projectile was fired by an enemy.
            lifetime: Maximum lifetime in seconds.

        Returns:
            None.
        """
        self.position = pygame.Vector2(position)
        self.velocity = pygame.Vector2(velocity)
        self.damage = damage
        self.radius = radius
        self.color = color
        self.from_enemy = from_enemy
        self.lifetime = lifetime

    def update(self, dt: float) -> None:
        """Advance projectile motion and lifetime.

        Args:
            dt: Frame delta time in seconds.

        Returns:
            None.
        """
        self.position += self.velocity * dt
        self.lifetime -= dt

    @property
    def alive(self) -> bool:
        """Tell whether the projectile should stay active.

        Returns:
            ``True`` while the projectile lifetime is above zero.
        """
        return self.lifetime > 0
