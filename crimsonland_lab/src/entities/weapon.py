from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class Weapon:
    """Weapon definition plus mutable progression state."""

    name: str
    base_damage: int
    base_cooldown: float
    base_projectile_speed: float
    base_pellets: int
    base_spread_degrees: float
    color: tuple[int, int, int]
    projectile_radius: int = 4
    max_level: int = 6
    level: int = 1

    _timer: float = 0.0

    def update(self, dt: float) -> None:
        """Advance the internal cooldown timer.

        Args:
            dt: Frame delta time in seconds.

        Returns:
            None.
        """
        self._timer = max(0.0, self._timer - dt)

    def is_ready(self) -> bool:
        """Check whether the weapon can fire right now.

        Returns:
            ``True`` when the cooldown timer reached zero.
        """
        return self._timer <= 0.0

    def trigger(self) -> None:
        """Start the cooldown after a shot has been fired.

        Returns:
            None.
        """
        self._timer = self.cooldown

    @property
    def damage(self) -> int:
        """Return the current damage per projectile.

        Returns:
            Damage value after applying the current weapon level bonuses.
        """
        return max(1, int(round(self.base_damage * (1 + 0.22 * (self.level - 1)))))

    @property
    def cooldown(self) -> float:
        """Return the current delay between shots.

        Returns:
            Cooldown in seconds after applying level-based reductions.
        """
        return max(0.05, self.base_cooldown * (0.93 ** (self.level - 1)))

    @property
    def projectile_speed(self) -> float:
        """Return the current projectile speed.

        Returns:
            Projectile speed in pixels per second.
        """
        return self.base_projectile_speed * (1 + 0.04 * (self.level - 1))

    @property
    def pellets(self) -> int:
        """Return how many projectiles are fired per shot.

        Returns:
            Pellet count after applying weapon-specific upgrade rules.
        """
        if self.base_pellets > 1:
            return self.base_pellets + (self.level - 1) // 2
        if self.name == "rifle" and self.level >= 4:
            return 2
        if self.name == "pistol" and self.level >= 5:
            return 2
        return self.base_pellets

    @property
    def spread_degrees(self) -> float:
        """Return the current total spread cone width.

        Returns:
            Spread angle in degrees for the current weapon level.
        """
        if self.base_pellets > 1:
            return self.base_spread_degrees + (self.level - 1) * 1.8
        if self.pellets > 1:
            return 6.0 + (self.level - 1) * 0.6
        return max(0.0, self.base_spread_degrees * (0.9 ** (self.level - 1)))

    def upgrade(self) -> bool:
        """Increase weapon level if it has not reached the cap yet.

        Returns:
            ``True`` when the level was increased, otherwise ``False``.
        """
        if self.level >= self.max_level:
            return False
        self.level += 1
        return True

    @classmethod
    def from_dict(cls, name: str, data: dict) -> "Weapon":
        """Build a weapon instance from JSON configuration data.

        Args:
            name: Weapon identifier used by the game.
            data: Raw weapon configuration dictionary.

        Returns:
            Fully initialized ``Weapon`` instance.
        """
        return cls(
            name=name,
            base_damage=int(data["damage"]),
            base_cooldown=float(data["cooldown"]),
            base_projectile_speed=float(data["projectile_speed"]),
            base_pellets=int(data["pellets"]),
            base_spread_degrees=float(data["spread_degrees"]),
            color=tuple(data["color"]),
            projectile_radius=int(data.get("projectile_radius", 4)),
        )
