from __future__ import annotations

import pygame

from src.logic.weapon_math import clamp


class Player:
    """Player-controlled survivor entity."""

    def __init__(
        self,
        position: tuple[float, float],
        speed: float,
        radius: int,
        max_health: int,
        sprite_path: str | None = None,
        color: tuple[int, int, int] = (126, 232, 180),
        name: str = "default",
    ) -> None:
        """Create the player entity.

        Args:
            position: Initial spawn position in world coordinates.
            speed: Movement speed in pixels per second.
            radius: Collision and rendering radius.
            max_health: Maximum amount of health points.
            sprite_path: Optional path to the player's sprite inside
                ``assets/images``.
            color: Fallback RGB color used when no sprite is available.
            name: Resolved player profile name.

        Returns:
            None.
        """
        self.name = name
        self.position = pygame.Vector2(position)
        self.speed = speed
        self.radius = radius
        self.max_health = max_health
        self.health = float(max_health)
        self.sprite_path = sprite_path
        self.color = color

    def update(self, dt: float, bounds: pygame.Rect, keys: pygame.key.ScancodeWrapper) -> None:
        """Move the player according to keyboard input and arena bounds.

        Args:
            dt: Frame delta time in seconds.
            bounds: Rectangle that defines the playable area.
            keys: Current keyboard state returned by
                ``pygame.key.get_pressed()``.

        Returns:
            None.
        """
        direction = pygame.Vector2(0, 0)
        if keys[pygame.K_w]:
            direction.y -= 1
        if keys[pygame.K_s]:
            direction.y += 1
        if keys[pygame.K_a]:
            direction.x -= 1
        if keys[pygame.K_d]:
            direction.x += 1

        if direction.length_squared() > 0:
            direction = direction.normalize()
            self.position += direction * self.speed * dt

        self.position.x = clamp(self.position.x, bounds.left + self.radius, bounds.right - self.radius)
        self.position.y = clamp(self.position.y, bounds.top + self.radius, bounds.bottom - self.radius)

    def take_damage(self, amount: float) -> None:
        """Reduce player health without letting it drop below zero.

        Args:
            amount: Damage value that should be applied.

        Returns:
            None.
        """
        self.health = max(0.0, self.health - amount)

    @property
    def is_dead(self) -> bool:
        """Report whether the player has no health left.

        Returns:
            ``True`` when the player's health reached zero.
        """
        return self.health <= 0
