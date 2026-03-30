from __future__ import annotations

import math

import pygame


class WeaponPickup:
    """Temporary pickup that upgrades a weapon when collected."""

    def __init__(self, position: tuple[float, float], weapon_name: str, color: tuple[int, int, int]) -> None:
        """Create a floating weapon pickup.

        Args:
            position: Spawn position in world coordinates.
            weapon_name: Identifier of the weapon that will be upgraded.
            color: RGB color used for drawing the pickup.

        Returns:
            None.
        """
        self.position = pygame.Vector2(position)
        self.weapon_name = weapon_name
        self.color = color
        self.radius = 13
        self.lifetime = 9.5
        self._phase = 0.0
        self._rotation = 0.0

    def update(self, dt: float) -> None:
        """Advance pickup timers and idle animation phases.

        Args:
            dt: Frame delta time in seconds.

        Returns:
            None.
        """
        self.lifetime -= dt
        self._phase += dt * 4
        self._rotation += dt * 135

    @property
    def alive(self) -> bool:
        """Tell whether the pickup should remain in the world.

        Returns:
            ``True`` while the pickup lifetime is above zero.
        """
        return self.lifetime > 0

    @property
    def draw_offset(self) -> float:
        """Compute the vertical bobbing offset for rendering.

        Returns:
            Vertical offset in pixels produced by the idle animation.
        """
        return math.sin(self._phase) * 4

    @property
    def pulse(self) -> float:
        """Compute the current glow pulse multiplier.

        Returns:
            Scale factor used to animate pickup glow intensity.
        """
        return 0.82 + 0.18 * (math.sin(self._phase * 1.6) + 1.0)

    @property
    def rotation(self) -> float:
        """Return the current diamond rotation angle.

        Returns:
            Rotation angle in degrees.
        """
        return self._rotation
