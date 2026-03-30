from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any

import pygame

from src.entities.projectile import Projectile
from src.logic.progression import miniboss_theme


@dataclass(slots=True)
class EnemyAction:
    """Deferred gameplay action emitted by an enemy update."""

    kind: str
    payload: dict[str, Any]


@dataclass(slots=True)
class EnemyUpdateResult:
    """Collection of projectiles and actions produced during one update."""

    projectiles: list[Projectile]
    actions: list[EnemyAction]


class Enemy:
    """Runtime enemy instance with AI, combat, and miniboss behavior."""

    def __init__(
        self,
        name: str,
        position: tuple[float, float],
        data: dict[str, Any],
        *,
        size_multiplier: float = 1.0,
        wave_number: int = 1,
        health_multiplier: float = 1.0,
        damage_multiplier: float = 1.0,
        speed_multiplier: float = 1.0,
        score_multiplier: float = 1.0,
        is_miniboss: bool = False,
    ) -> None:
        """Create an enemy from configuration data and wave modifiers.

        Args:
            name: Enemy identifier from the configuration.
            position: Initial spawn position in world coordinates.
            data: Raw enemy configuration dictionary.
            size_multiplier: Global size scaling applied to the base radius.
            wave_number: Current one-based wave number.
            health_multiplier: Extra multiplier applied to health.
            damage_multiplier: Extra multiplier applied to contact and ranged
                damage.
            speed_multiplier: Extra multiplier applied to movement speed.
            score_multiplier: Extra multiplier applied to score reward.
            is_miniboss: Whether the enemy should use miniboss visuals and
                attack patterns.

        Returns:
            None.
        """
        self.name = name
        self.position = pygame.Vector2(position)
        self.wave_number = wave_number
        self.is_miniboss = is_miniboss
        theme = miniboss_theme(wave_number) if is_miniboss else None
        self.base_color = tuple(data["color"])
        self.color = self._boost_color(self.base_color, 0.24 if is_miniboss else 0.08)
        self.accent_color = self._boost_color(self.color, 0.26)
        self.sprite_path = data.get("sprite", f"enemies/{name}.png") or None
        title_value = data.get("title")
        self.title = title_value.strip() if isinstance(title_value, str) and title_value.strip() else name.replace("_", " ").title()
        hit_text = data.get("hit_text", {})
        self.hit_text_config = hit_text if isinstance(hit_text, dict) else {}
        self.boss_pattern = theme["pattern"] if theme is not None else None
        self.boss_title = self.title
        health_value = data["health"]
        speed_value = data["speed"]
        radius_value = data["radius"]
        contact_damage_value = data["contact_damage"]
        score_value = data["score"]
        preferred_distance_value = data.get("preferred_distance", 220)
        shoot_cooldown_value = data.get("shoot_cooldown", 1.2)
        ranged_damage_value = data.get("ranged_damage", 8)
        ranged_speed_value = data.get("ranged_speed", 280)

        self.max_health = max(1, int(round(float(health_value) * health_multiplier)))
        self.health = float(self.max_health)
        self.speed = float(speed_value) * speed_multiplier
        base_radius = float(radius_value) * size_multiplier
        self.radius = max(8, int(round(base_radius * (1.35 if is_miniboss else 1.0))))
        damage_boost = 1.12 if is_miniboss else 1.0
        self.contact_damage = float(contact_damage_value) * damage_multiplier * damage_boost
        self.score_value = max(1, int(round(float(score_value) * score_multiplier)))
        self.behavior = data["behavior"]

        self.preferred_distance = float(preferred_distance_value) + (28 if is_miniboss else 0)
        self.shoot_cooldown = float(shoot_cooldown_value) / (1.15 if is_miniboss else 1.0)
        self.ranged_damage = max(1, int(round(float(ranged_damage_value) * damage_multiplier * damage_boost)))
        self.ranged_speed = float(ranged_speed_value)
        self.phase = random.uniform(0.0, math.tau)
        self._shot_timer = random.uniform(0.1, self.shoot_cooldown)
        self._boss_attack_timer = random.uniform(1.1, 2.2) if is_miniboss else 0.0
        self._boss_secondary_timer = random.uniform(2.5, 4.0) if is_miniboss else 0.0
        self._dash_timer = 0.0
        self._dash_velocity = pygame.Vector2()

    def update(self, dt: float, player_position: pygame.Vector2) -> EnemyUpdateResult:
        """Advance AI, movement, and attacks for one frame.

        Args:
            dt: Frame delta time in seconds.
            player_position: Current player position used for steering and
                attacks.

        Returns:
            ``EnemyUpdateResult`` with newly fired projectiles and deferred
            actions requested by the enemy.
        """
        projectiles: list[Projectile] = []
        actions: list[EnemyAction] = []
        to_player = player_position - self.position
        distance = max(1.0, to_player.length())
        direction = to_player.normalize() if to_player.length_squared() > 0 else pygame.Vector2(1, 0)
        self.phase += dt * (2.3 if self.is_miniboss else 1.4)
        if self._dash_timer > 0:
            self._dash_timer = max(0.0, self._dash_timer - dt)
            self.position += self._dash_velocity * dt
            return EnemyUpdateResult(projectiles, actions)

        if self.behavior == "wander":
            direction = pygame.Vector2(random.uniform(-1, 1), random.uniform(-1, 1))
            if direction.length_squared() > 0:
                self.position += direction.normalize() * (self.speed * 0.35) * dt
        elif self.behavior == "keep_distance":
            if distance > self.preferred_distance + 20:
                self.position += direction * self.speed * dt
            elif distance < self.preferred_distance - 20:
                self.position -= direction * self.speed * dt
            self._shot_timer -= dt
            if self._shot_timer <= 0:
                velocity = direction * self.ranged_speed
                projectiles.append(
                    Projectile(
                        position=self.position,
                        velocity=velocity,
                        damage=self.ranged_damage,
                        radius=5,
                        color=self.accent_color,
                        from_enemy=True,
                        lifetime=2.4,
                    )
                )
                self._shot_timer = self.shoot_cooldown
        elif self.behavior == "kamikaze":
            speed_boost = 1.28 if self.is_miniboss and self.boss_pattern == "reaper" and self.health_ratio < 0.5 else 1.1
            self.position += direction * (self.speed * speed_boost) * dt
        else:
            self.position += direction * self.speed * dt

        if self.is_miniboss:
            extra_projectiles, extra_actions = self._update_miniboss_pattern(dt, player_position, direction, distance)
            projectiles.extend(extra_projectiles)
            actions.extend(extra_actions)

        return EnemyUpdateResult(projectiles, actions)

    def take_damage(self, amount: float) -> bool:
        """Apply incoming damage to the enemy.

        Args:
            amount: Damage that should be subtracted from current health.

        Returns:
            ``True`` when the enemy died after taking the damage, otherwise
            ``False``.
        """
        self.health -= amount
        return self.health <= 0

    @property
    def health_ratio(self) -> float:
        """Return current health as a ``0..1`` fraction of maximum health.

        Returns:
            Clamped health ratio used by the UI and miniboss logic.
        """
        if self.max_health <= 0:
            return 0.0
        return max(0.0, self.health / self.max_health)

    @staticmethod
    def _boost_color(color: tuple[int, int, int], amount: float) -> tuple[int, int, int]:
        """Brighten a base RGB color toward white.

        Args:
            color: Source RGB color.
            amount: Brightening factor.

        Returns:
            Brightened RGB color tuple.
        """
        return tuple(min(255, int(component + (255 - component) * amount)) for component in color)

    def _update_miniboss_pattern(
        self,
        dt: float,
        player_position: pygame.Vector2,
        direction: pygame.Vector2,
        distance: float,
    ) -> tuple[list[Projectile], list[EnemyAction]]:
        """Run the special attack logic used by miniboss enemies.

        Args:
            dt: Frame delta time in seconds.
            player_position: Current player position in world coordinates.
            direction: Normalized direction vector from the enemy to the player.
            distance: Current distance between the enemy and the player.

        Returns:
            Tuple containing projectiles fired this frame and deferred gameplay
            actions such as minion spawns.
        """
        projectiles: list[Projectile] = []
        actions: list[EnemyAction] = []
        self._boss_attack_timer -= dt
        self._boss_secondary_timer -= dt

        if self.boss_pattern == "juggernaut":
            if self._boss_attack_timer <= 0:
                self._boss_attack_timer = 3.0
                self._dash_velocity = direction * (self.speed * 2.8)
                self._dash_timer = 0.52
                projectiles.extend(self._radial_burst(8, speed=250, damage=self.ranged_damage + 3, radius=6))
        elif self.boss_pattern == "stormcaller":
            tangent = pygame.Vector2(-direction.y, direction.x)
            strafe_scale = 1 if math.sin(self.phase * 1.25) >= 0 else -1
            self.position += tangent * (self.speed * 0.42 * strafe_scale) * dt
            if self._boss_attack_timer <= 0:
                self._boss_attack_timer = 2.15
                projectiles.extend(self._radial_burst(10, speed=255, damage=self.ranged_damage, radius=5))
            if self._boss_secondary_timer <= 0:
                self._boss_secondary_timer = 1.45
                projectiles.extend(self._aimed_spread(direction, pellets=5, spread=0.52, speed=320, damage=self.ranged_damage + 2))
        elif self.boss_pattern == "reaper":
            if self._boss_attack_timer <= 0:
                self._boss_attack_timer = 3.35
                self._dash_velocity = direction * (self.speed * 3.2)
                self._dash_timer = 0.34
                projectiles.extend(self._aimed_spread(direction, pellets=6, spread=0.8, speed=260, damage=self.ranged_damage + 4))
            if self._boss_secondary_timer <= 0:
                self._boss_secondary_timer = 4.9
                actions.append(
                    EnemyAction(
                        "spawn_minions",
                        {
                            "enemy_name": "kamikaze",
                            "count": 2,
                            "source_position": pygame.Vector2(self.position),
                            "radius": self.radius + 34,
                        },
                    )
                )
        elif self.boss_pattern == "overlord":
            tangent = pygame.Vector2(-direction.y, direction.x)
            self.position += tangent * (self.speed * 0.28) * dt
            if self._boss_attack_timer <= 0:
                self._boss_attack_timer = 2.0
                projectiles.extend(self._radial_burst(12, speed=270, damage=self.ranged_damage + 3, radius=5))
                projectiles.extend(self._aimed_spread(direction, pellets=3, spread=0.32, speed=345, damage=self.ranged_damage + 4))
            if self._boss_secondary_timer <= 0:
                self._boss_secondary_timer = 5.2
                self._dash_velocity = direction * (self.speed * 2.1)
                self._dash_timer = 0.28
                actions.append(
                    EnemyAction(
                        "spawn_minions",
                        {
                            "enemy_name": "runner",
                            "count": 2,
                            "source_position": pygame.Vector2(self.position),
                            "radius": self.radius + 42,
                        },
                    )
                )
                actions.append(
                    EnemyAction(
                        "spawn_minions",
                        {
                            "enemy_name": "shooter",
                            "count": 1,
                            "source_position": pygame.Vector2(self.position),
                            "radius": self.radius + 54,
                        },
                    )
                )
        elif distance < self.preferred_distance * 0.72 and self._boss_attack_timer <= 0:
            self._boss_attack_timer = 2.6
            projectiles.extend(self._radial_burst(6, speed=220, damage=self.ranged_damage, radius=5))

        return projectiles, actions

    def _radial_burst(self, pellets: int, *, speed: float, damage: int, radius: int) -> list[Projectile]:
        """Create projectiles evenly distributed around the enemy.

        Args:
            pellets: Number of projectiles to spawn.
            speed: Projectile speed in pixels per second.
            damage: Damage dealt by each projectile.
            radius: Projectile collision radius.

        Returns:
            List of radial projectiles emitted from the enemy position.
        """
        projectiles: list[Projectile] = []
        for index in range(max(1, pellets)):
            angle = (math.tau * index) / max(1, pellets) + self.phase * 0.18
            velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
            projectiles.append(
                Projectile(
                    position=self.position,
                    velocity=velocity,
                    damage=damage,
                    radius=radius,
                    color=self.accent_color,
                    from_enemy=True,
                    lifetime=2.7,
                )
            )
        return projectiles

    def _aimed_spread(
        self,
        direction: pygame.Vector2,
        *,
        pellets: int,
        spread: float,
        speed: float,
        damage: int,
    ) -> list[Projectile]:
        """Create a forward-facing spread of enemy projectiles.

        Args:
            direction: Normalized aim direction toward the player.
            pellets: Number of projectiles to spawn.
            spread: Total angular spread in radians.
            speed: Projectile speed in pixels per second.
            damage: Damage dealt by each projectile.

        Returns:
            List of projectiles distributed across the requested spread cone.
        """
        projectiles: list[Projectile] = []
        base_angle = math.atan2(direction.y, direction.x)
        if pellets <= 1:
            angles = [base_angle]
        else:
            angles = [
                base_angle + spread * ((index / (pellets - 1)) - 0.5)
                for index in range(pellets)
            ]
        for angle in angles:
            velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * speed
            projectiles.append(
                Projectile(
                    position=self.position,
                    velocity=velocity,
                    damage=damage,
                    radius=5,
                    color=self.accent_color,
                    from_enemy=True,
                    lifetime=2.6,
                )
            )
        return projectiles
