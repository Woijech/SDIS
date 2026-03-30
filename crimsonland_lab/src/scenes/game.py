from __future__ import annotations

import math
import random
from typing import TYPE_CHECKING

import pygame

from src.core.config_loader import load_json
from src.core.particle_effects import load_particle_effects, resolve_enemy_hit_text
from src.core.player_profiles import load_player_profiles, resolve_player_profile
from src.entities.effects import CircleEffect, FloatingTextEffect
from src.entities.enemy import Enemy, EnemyAction
from src.entities.pickup import WeaponPickup
from src.entities.player import Player
from src.entities.projectile import Projectile
from src.entities.weapon import Weapon
from src.logic.progression import (
    enemy_damage_multiplier,
    is_miniboss_wave,
    miniboss_theme,
    miniboss_health_multiplier,
    miniboss_score_multiplier,
)
from src.logic.weapon_math import calculate_spread_angles
from src.logic.waves import WaveController, build_wave_plans
from src.scenes.base import BaseScene

if TYPE_CHECKING:
    from src.app import App


class GameScene(BaseScene):
    """Main gameplay scene that owns combat, waves, and rendering."""

    def __init__(self, app: App) -> None:
        """Build the full runtime state for a new game session.

        Args:
            app: Running application instance.

        Returns:
            None.
        """
        super().__init__(app)
        self.bounds = pygame.Rect(0, 0, self.app.settings["screen_width"], self.app.settings["screen_height"])
        self.random = random.Random()

        self.weapon_data = load_json(self.app.base_dir / "config" / "weapons.json")
        self.enemy_data = load_json(self.app.base_dir / "config" / "enemies.json")
        self.particle_effects = load_particle_effects(self.app.base_dir / "config")
        self.player_profiles = load_player_profiles(self.app.base_dir / "config")
        self.wave_data = load_json(self.app.base_dir / "config" / "waves.json")["waves"]
        self.default_enemy_hit_text = resolve_enemy_hit_text(self.particle_effects.get("enemy_hit_text"))
        player_profile = resolve_player_profile(self.app.settings, self.player_profiles)

        self.weapon_order = list(self.weapon_data.keys())
        self.weapons = {
            name: Weapon.from_dict(name, data)
            for name, data in self.weapon_data.items()
        }
        self.current_weapon_name = self.weapon_order[0]

        self.player = Player(
            position=(self.bounds.centerx, self.bounds.centery),
            speed=player_profile["speed"],
            radius=max(1, int(round(player_profile["radius"] * self.app.settings.get("player_size_scale", 1.0)))),
            max_health=player_profile["health"],
            sprite_path=player_profile["sprite"],
            color=player_profile["color"],
            name=player_profile["name"],
        )

        self.wave_controller = WaveController(build_wave_plans(self.wave_data))
        self.wave_controller.start()

        self.enemies: list[Enemy] = []
        self.projectiles: list[Projectile] = []
        self.effects: list[CircleEffect | FloatingTextEffect] = []
        self.pickups: list[WeaponPickup] = []
        self.score = 0
        self.total_elapsed = 0.0

        self._wave_banner_duration = 1.6
        self._boss_banner_duration = 2.2
        self._pickup_banner_duration = 1.5
        self._wave_banner_timer = 1.7
        self._boss_banner_timer = 0.0
        self._pickup_banner_timer = 0.0
        self._pickup_banner_text = ""
        self._boss_banner_text = ""
        self._invulnerability_timer = 0.0
        self._screen_flash = 0.0
        self._spawned_boss_waves: set[int] = set()

        self._background_surface = self._build_background_surface()
        self._background_nodes = self._build_background_nodes()

    def on_enter(self) -> None:
        """Start gameplay music and play the first wave cue.

        Returns:
            None.
        """
        self.app.resources.play_music("game_music")
        self.app.resources.play_sound("wave_start")

    def current_weapon(self) -> Weapon:
        """Return the weapon currently selected by the player.

        Returns:
            Active ``Weapon`` instance used for firing and HUD rendering.
        """
        return self.weapons[self.current_weapon_name]

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle scene-level keyboard and mouse input.

        Args:
            event: Event received from the main loop.

        Returns:
            None.
        """
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.app.change_scene("menu")
            elif event.key == pygame.K_1:
                self.current_weapon_name = self.weapon_order[0]
            elif event.key == pygame.K_2 and len(self.weapon_order) >= 2:
                self.current_weapon_name = self.weapon_order[1]
            elif event.key == pygame.K_3 and len(self.weapon_order) >= 3:
                self.current_weapon_name = self.weapon_order[2]
            elif event.key == pygame.K_SPACE:
                self.fire_weapon()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.fire_weapon()

    def update(self, dt: float) -> None:
        """Advance gameplay systems for one frame.

        Args:
            dt: Frame delta time in seconds.

        Returns:
            None. The method may change the active scene when the run ends.
        """
        self.total_elapsed += dt
        self._wave_banner_timer = max(0.0, self._wave_banner_timer - dt)
        self._boss_banner_timer = max(0.0, self._boss_banner_timer - dt)
        self._pickup_banner_timer = max(0.0, self._pickup_banner_timer - dt)
        self._invulnerability_timer = max(0.0, self._invulnerability_timer - dt)
        self._screen_flash = max(0.0, self._screen_flash - dt)

        keys = pygame.key.get_pressed()
        self.player.update(dt, self.bounds, keys)

        for weapon in self.weapons.values():
            weapon.update(dt)

        if pygame.mouse.get_pressed()[0]:
            self.fire_weapon()

        for enemy_name in self.wave_controller.update(dt, len(self.enemies)):
            self.spawn_enemy(enemy_name)

        if self.wave_controller.wave_started_this_frame:
            self._wave_banner_timer = self._wave_banner_duration
            self.app.resources.play_sound("wave_start")
            self.spawn_miniboss_for_current_wave()

        enemy_projectiles: list[Projectile] = []
        enemy_actions: list[EnemyAction] = []
        for enemy in self.enemies:
            update_result = enemy.update(dt, self.player.position)
            if enemy.is_miniboss:
                enemy.position.x = max(self.bounds.left + enemy.radius, min(self.bounds.right - enemy.radius, enemy.position.x))
                enemy.position.y = max(self.bounds.top + enemy.radius, min(self.bounds.bottom - enemy.radius, enemy.position.y))
            enemy_projectiles.extend(update_result.projectiles)
            enemy_actions.extend(update_result.actions)
            if (enemy.position - self.player.position).length() < enemy.radius + self.player.radius:
                self.damage_player(enemy.contact_damage * dt)
        self.projectiles.extend(enemy_projectiles)
        for action in enemy_actions:
            self.handle_enemy_action(action)

        for projectile in self.projectiles:
            projectile.update(dt)

        for effect in self.effects:
            effect.update(dt)

        for pickup in self.pickups:
            pickup.update(dt)

        self.resolve_collisions()
        self.cleanup_objects()

        if self.player.is_dead:
            self.app.change_scene("game_over", score=self.score, survived_all_waves=False)
            return

        if self.wave_controller.finished and not self.enemies:
            self.app.change_scene("game_over", score=self.score, survived_all_waves=True)

    def damage_player(self, amount: float) -> None:
        """Apply damage to the player with a short invulnerability window.

        Args:
            amount: Damage value that should be applied.

        Returns:
            None.
        """
        if self._invulnerability_timer > 0:
            return
        self.player.take_damage(amount)
        self._invulnerability_timer = 0.18
        self._screen_flash = min(0.2, self._screen_flash + 0.1)
        self.effects.append(CircleEffect(self.player.position, (255, 94, 94), 0.22, 16, 44))

    def fire_weapon(self) -> None:
        """Fire the currently selected weapon toward the mouse cursor.

        Returns:
            None. The method exits early when the weapon is still on cooldown.
        """
        weapon = self.current_weapon()
        if not weapon.is_ready():
            return

        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        direction = mouse_pos - self.player.position
        if direction.length_squared() == 0:
            direction = pygame.Vector2(1, 0)
        aim_direction = direction.normalize()
        base_angle = math.atan2(direction.y, direction.x)
        muzzle_position = self.player.position + aim_direction * (self.player.radius + 10)

        for angle in calculate_spread_angles(base_angle, weapon.pellets, weapon.spread_degrees):
            velocity = pygame.Vector2(math.cos(angle), math.sin(angle)) * weapon.projectile_speed
            projectile = Projectile(
                position=muzzle_position,
                velocity=velocity,
                damage=weapon.damage,
                radius=weapon.projectile_radius,
                color=weapon.color,
                from_enemy=False,
                lifetime=1.35,
            )
            self.projectiles.append(projectile)

        weapon.trigger()
        self.effects.append(CircleEffect(muzzle_position, weapon.color, 0.14, 8, 32))
        self.effects.append(CircleEffect(self.player.position, self.boost_color(weapon.color, 0.22), 0.16, 12, 34))
        self.app.resources.play_sound(f"{weapon.name}_shoot", fallback="shoot")

    def spawn_enemy(self, enemy_name: str, *, is_miniboss: bool = False) -> Enemy:
        """Spawn an enemy at an automatically chosen edge position.

        Args:
            enemy_name: Enemy identifier from ``enemies.json``.
            is_miniboss: Whether the enemy should receive miniboss modifiers.

        Returns:
            Spawned ``Enemy`` instance.
        """
        return self.spawn_enemy_at(enemy_name, position=None, is_miniboss=is_miniboss)

    def spawn_enemy_at(
        self,
        enemy_name: str,
        *,
        position: tuple[float, float] | pygame.Vector2 | None,
        is_miniboss: bool = False,
    ) -> Enemy:
        """Spawn an enemy at a specific or automatically chosen position.

        Args:
            enemy_name: Enemy identifier from ``enemies.json``.
            position: Explicit spawn position. When ``None``, the enemy is
                spawned just outside the arena bounds.
            is_miniboss: Whether the enemy should receive miniboss modifiers.

        Returns:
            Spawned ``Enemy`` instance already added to ``self.enemies``.
        """
        enemy_size_scale = float(self.app.settings.get("enemy_size_scale", 1.0))
        if position is None:
            spawn_side = self.random.choice(["top", "bottom", "left", "right"])
            margin = max(34, int(round(34 * enemy_size_scale)))
            if spawn_side == "top":
                position = (self.random.randint(0, self.bounds.width), -margin)
            elif spawn_side == "bottom":
                position = (self.random.randint(0, self.bounds.width), self.bounds.height + margin)
            elif spawn_side == "left":
                position = (-margin, self.random.randint(0, self.bounds.height))
            else:
                position = (self.bounds.width + margin, self.random.randint(0, self.bounds.height))

        wave_number = max(1, self.wave_controller.current_wave_number)
        base_damage_multiplier = enemy_damage_multiplier(wave_number)
        health_multiplier = miniboss_health_multiplier(wave_number) if is_miniboss else 1.0
        score_multiplier = miniboss_score_multiplier(wave_number) if is_miniboss else 1.0
        speed_multiplier = 1.08 if is_miniboss else 1.0
        damage_multiplier = base_damage_multiplier * (1.16 if is_miniboss else 1.0)

        enemy = Enemy(
            enemy_name,
            position,
            self.enemy_data[enemy_name],
            size_multiplier=enemy_size_scale,
            wave_number=wave_number,
            health_multiplier=health_multiplier,
            damage_multiplier=damage_multiplier,
            speed_multiplier=speed_multiplier,
            score_multiplier=score_multiplier,
            is_miniboss=is_miniboss,
        )
        self.enemies.append(enemy)

        if is_miniboss:
            self.effects.append(CircleEffect(enemy.position, enemy.color, 0.42, enemy.radius, enemy.radius + 44))
            self._screen_flash = 0.16
        return enemy

    def spawn_miniboss_for_current_wave(self) -> None:
        """Spawn the wave miniboss if the current wave should have one.

        Returns:
            None.
        """
        wave_number = self.wave_controller.current_wave_number
        if not is_miniboss_wave(wave_number) or wave_number in self._spawned_boss_waves:
            return

        self._spawned_boss_waves.add(wave_number)
        boss_name = self.select_miniboss_name(wave_number)
        boss = self.spawn_enemy(boss_name, is_miniboss=True)
        self._boss_banner_timer = self._boss_banner_duration
        self._boss_banner_text = f"Mini-boss: {boss.boss_title}"
        self.app.resources.play_sound("miniboss_spawn")

    def select_miniboss_name(self, wave_number: int) -> str:
        """Choose the miniboss enemy type for a given wave.

        Args:
            wave_number: One-based wave number that is starting.

        Returns:
            Enemy identifier for the miniboss that should be spawned.
        """
        theme = miniboss_theme(wave_number)
        preferred = None if theme is None else theme.get("enemy")
        if preferred in self.enemy_data:
            return preferred

        current_wave = self.wave_controller.current_wave
        if current_wave is None or not current_wave.entries:
            return "tank"

        available = {entry.enemy for entry in current_wave.entries}
        return max(available, key=lambda name: self.enemy_data[name]["health"])

    def handle_enemy_action(self, action: EnemyAction) -> None:
        """Execute deferred actions emitted by enemy AI.

        Args:
            action: Action generated by an enemy during its update step.

        Returns:
            None.
        """
        if action.kind != "spawn_minions":
            return

        enemy_name = action.payload["enemy_name"]
        source_position = pygame.Vector2(action.payload["source_position"])
        count = max(1, int(action.payload.get("count", 1)))
        radius = float(action.payload.get("radius", 36.0))
        angle_offset = self.random.uniform(0.0, math.tau)
        for index in range(count):
            angle = angle_offset + (math.tau * index) / count
            spawn_pos = pygame.Vector2(
                source_position.x + math.cos(angle) * radius,
                source_position.y + math.sin(angle) * radius,
            )
            spawn_pos.x = max(24, min(self.bounds.width - 24, spawn_pos.x))
            spawn_pos.y = max(24, min(self.bounds.height - 24, spawn_pos.y))
            self.spawn_enemy_at(enemy_name, position=spawn_pos, is_miniboss=False)
            self.effects.append(CircleEffect(spawn_pos, self.enemy_data[enemy_name]["color"], 0.22, 10, 28))
        self._screen_flash = min(0.18, self._screen_flash + 0.06)

    def resolve_collisions(self) -> None:
        """Resolve projectile hits, contact damage, and pickup collection.

        Returns:
            None.
        """
        for projectile in list(self.projectiles):
            if projectile.from_enemy:
                if (projectile.position - self.player.position).length() <= projectile.radius + self.player.radius:
                    self.damage_player(projectile.damage)
                    projectile.lifetime = 0
                continue

            for enemy in list(self.enemies):
                if (projectile.position - enemy.position).length() <= projectile.radius + enemy.radius:
                    projectile.lifetime = 0
                    dead = enemy.take_damage(projectile.damage)
                    self.effects.append(CircleEffect(projectile.position, projectile.color, 0.14, 8, 24))
                    score_text = self.create_enemy_hit_score_text(enemy)
                    if score_text is not None:
                        self.effects.append(score_text)
                    if dead:
                        self.kill_enemy(enemy)
                    break

        for pickup in list(self.pickups):
            if (pickup.position - self.player.position).length() <= pickup.radius + self.player.radius:
                weapon = self.weapons[pickup.weapon_name]
                upgraded = weapon.upgrade()
                self.current_weapon_name = pickup.weapon_name
                pickup.lifetime = 0
                self.effects.append(CircleEffect(pickup.position, pickup.color, 0.34, 12, 44))
                self._pickup_banner_timer = self._pickup_banner_duration
                self._pickup_banner_text = (
                    f"{pickup.weapon_name.title()} -> LVL {weapon.level}"
                    if upgraded
                    else f"{pickup.weapon_name.title()} is MAXED"
                )
                self.app.resources.play_sound("weapon_level_up" if upgraded else "meme_fah", fallback="pickup")

    def kill_enemy(self, enemy: Enemy) -> None:
        """Remove a defeated enemy, award score, and maybe drop a pickup.

        Args:
            enemy: Enemy instance that has been defeated.

        Returns:
            None.
        """
        if enemy in self.enemies:
            self.enemies.remove(enemy)
        self.score += enemy.score_value
        self.effects.append(CircleEffect(enemy.position, enemy.color, 0.36, 16, 52))
        self.app.resources.play_sound("hit")

        drop_chance = 1.0 if enemy.is_miniboss else self.app.settings["weapon_drop_chance"]
        if self.random.random() < drop_chance:
            available = [name for name in self.weapon_order if name != self.current_weapon_name]
            if not available:
                available = list(self.weapon_order)
            weapon_name = self.random.choice(available)
            color = tuple(self.weapon_data[weapon_name]["color"])
            self.pickups.append(WeaponPickup(enemy.position, weapon_name, color))

    def cleanup_objects(self) -> None:
        """Discard expired or out-of-bounds temporary objects.

        Returns:
            None.
        """
        self.projectiles = [
            projectile
            for projectile in self.projectiles
            if projectile.alive and self.bounds.inflate(120, 120).collidepoint(projectile.position)
        ]
        self.effects = [effect for effect in self.effects if effect.alive]
        self.pickups = [pickup for pickup in self.pickups if pickup.alive]

    def _build_background_surface(self) -> pygame.Surface:
        """Pre-render the static gameplay background layer.

        Returns:
            Surface containing the non-animated portion of the arena backdrop.
        """
        surface = pygame.Surface(self.bounds.size)
        top_color = (7, 9, 14)
        bottom_color = (30, 11, 16)

        for y in range(0, self.bounds.height, 4):
            blend = y / max(1, self.bounds.height - 1)
            color = self.mix_color(top_color, bottom_color, blend)
            pygame.draw.rect(surface, color, (0, y, self.bounds.width, 4))

        for y in range(24, self.bounds.height, 56):
            stripe_color = self.mix_color((18, 24, 34), (42, 19, 24), y / self.bounds.height)
            pygame.draw.line(surface, stripe_color, (0, y), (self.bounds.width, y), 1)

        speck_palette = ((196, 92, 79), (76, 143, 214), (248, 208, 118))
        for _ in range(90):
            pos = (
                self.random.randint(0, self.bounds.width - 1),
                self.random.randint(0, self.bounds.height - 1),
            )
            color = self.random.choice(speck_palette)
            self.draw_glow(surface, pos, self.random.randint(8, 16), color, 28)

        return surface

    def _build_background_nodes(self) -> list[tuple[float, float, int, float, tuple[int, int, int]]]:
        """Generate animated background glow nodes.

        Returns:
            List of tuples describing glow position, radius, speed, and color.
        """
        palette = ((179, 76, 69), (88, 153, 216), (246, 184, 102))
        nodes: list[tuple[float, float, int, float, tuple[int, int, int]]] = []
        for _ in range(18):
            nodes.append(
                (
                    self.random.uniform(0, self.bounds.width),
                    self.random.uniform(0, self.bounds.height),
                    self.random.randint(44, 92),
                    self.random.uniform(0.18, 0.6),
                    self.random.choice(palette),
                )
            )
        return nodes

    def draw_background(self, surface: pygame.Surface) -> None:
        """Draw the animated arena background and screen flash overlays.

        Args:
            surface: Framebuffer surface used for the current frame.

        Returns:
            None.
        """
        surface.blit(self._background_surface, (0, 0))

        overlay = pygame.Surface(self.bounds.size, pygame.SRCALPHA)
        sweep = int((self.total_elapsed * 52) % 70)
        grid_gap = 70

        for x in range(-self.bounds.height, self.bounds.width + self.bounds.height, grid_gap):
            pygame.draw.line(
                overlay,
                (108, 136, 176, 18),
                (x + sweep, 0),
                (x - self.bounds.height + sweep, self.bounds.height),
                1,
            )

        for y in range(0, self.bounds.height, 72):
            pulse = 8 + int(5 * (0.5 + 0.5 * math.sin(self.total_elapsed * 1.4 + y * 0.05)))
            pygame.draw.line(overlay, (255, 255, 255, pulse), (0, y), (self.bounds.width, y), 1)

        for index, (x, y, radius, speed, color) in enumerate(self._background_nodes):
            phase = self.total_elapsed * speed + index * 0.7
            center = (
                int((x + math.sin(phase * 1.4) * 18) % self.bounds.width),
                int((y + math.cos(phase * 1.1) * 12) % self.bounds.height),
            )
            self.draw_glow(overlay, center, int(radius * (0.9 + 0.12 * math.sin(phase))), color, 36)

        if any(enemy.is_miniboss for enemy in self.enemies):
            self.draw_glow(overlay, self.bounds.center, 320, (214, 86, 74), 80)

        pygame.draw.rect(overlay, (255, 130, 96, 24), self.bounds, width=3, border_radius=8)
        surface.blit(overlay, (0, 0))

        if self._screen_flash > 0:
            alpha = int(90 * (self._screen_flash / 0.2))
            flash = pygame.Surface(self.bounds.size, pygame.SRCALPHA)
            flash.fill((255, 245, 220, alpha))
            surface.blit(flash, (0, 0))

    def draw_hud(self, surface: pygame.Surface) -> None:
        """Render the gameplay HUD with player, wave, and weapon status.

        Args:
            surface: Framebuffer surface used for the current frame.

        Returns:
            None.
        """
        width = surface.get_width()
        height = surface.get_height()
        weapon = self.current_weapon()
        hp_ratio = self.player.health / self.player.max_health
        alive_count = len(self.enemies)
        queued_count = self.wave_controller.remaining_to_spawn()
        wave_number = max(1, self.wave_controller.current_wave_number)
        damage_scale = enemy_damage_multiplier(wave_number)
        boss = next((enemy for enemy in self.enemies if enemy.is_miniboss), None)

        vitals_rect = pygame.Rect(18, 16, 292, 128)
        wave_rect = pygame.Rect(width // 2 - 180, 16, 360, 112)
        weapon_rect = pygame.Rect(width - 304, 16, 286, 156)
        controls_rect = pygame.Rect(18, height - 54, 420, 34)

        self.draw_panel(surface, vitals_rect, accent=(216, 93, 78))
        self.draw_panel(surface, wave_rect, accent=(102, 173, 242))
        self.draw_panel(surface, weapon_rect, accent=weapon.color)
        controls_panel = pygame.Surface(controls_rect.size, pygame.SRCALPHA)
        controls_panel_rect = controls_panel.get_rect()
        pygame.draw.rect(controls_panel, (9, 12, 18, 170), controls_panel_rect, border_radius=12)
        pygame.draw.rect(controls_panel, (255, 255, 255, 18), controls_panel_rect, width=1, border_radius=12)
        surface.blit(controls_panel, controls_rect.topleft)

        title_color = (250, 238, 220)
        muted_color = (172, 186, 205)
        surface.blit(self.app.small_font.render("PLAYER", True, muted_color), (vitals_rect.x + 18, vitals_rect.y + 14))
        surface.blit(self.app.hud_font.render(f"Score {self.score}", True, title_color), (vitals_rect.x + 18, vitals_rect.y + 36))
        surface.blit(
            self.app.small_font.render(f"Time {self.total_elapsed:05.1f}s", True, muted_color),
            (vitals_rect.x + 18, vitals_rect.y + 66),
        )

        bar_bg = pygame.Rect(vitals_rect.x + 18, vitals_rect.y + 94, vitals_rect.width - 36, 18)
        bar_fg = pygame.Rect(bar_bg.x, bar_bg.y, int(bar_bg.width * hp_ratio), bar_bg.height)
        pygame.draw.rect(surface, (55, 20, 24), bar_bg, border_radius=8)
        pygame.draw.rect(surface, (224, 92, 92), bar_fg, border_radius=8)
        pygame.draw.rect(surface, (248, 230, 219), bar_bg, width=2, border_radius=8)
        hp_label = self.app.small_font.render(
            f"HP {int(self.player.health)}/{self.player.max_health}",
            True,
            (247, 246, 244),
        )
        surface.blit(hp_label, (bar_bg.x + 10, bar_bg.y - 1))

        surface.blit(
            self.app.small_font.render("WAVE STATUS", True, muted_color),
            (wave_rect.x + 20, wave_rect.y + 14),
        )
        wave_title = self.app.hud_font.render(
            f"Wave {wave_number}/{self.wave_controller.total_waves}",
            True,
            (244, 244, 246),
        )
        surface.blit(wave_title, (wave_rect.x + 20, wave_rect.y + 36))
        surface.blit(
            self.app.small_font.render(f"On arena {alive_count}", True, (235, 198, 130)),
            (wave_rect.x + 20, wave_rect.y + 66),
        )
        surface.blit(
            self.app.small_font.render(f"Queued {queued_count}", True, muted_color),
            (wave_rect.x + 156, wave_rect.y + 66),
        )
        surface.blit(
            self.app.small_font.render(f"Enemy damage x{damage_scale:.2f}", True, (244, 134, 118)),
            (wave_rect.x + 20, wave_rect.y + 88),
        )

        surface.blit(
            self.app.small_font.render("WEAPON UPGRADE", True, muted_color),
            (weapon_rect.x + 18, weapon_rect.y + 14),
        )
        surface.blit(
            self.app.hud_font.render(self.current_weapon_name.title(), True, weapon.color),
            (weapon_rect.x + 18, weapon_rect.y + 36),
        )
        surface.blit(
            self.app.small_font.render(f"LVL {weapon.level}/{weapon.max_level}", True, (250, 244, 236)),
            (weapon_rect.x + 18, weapon_rect.y + 62),
        )

        chip_y = weapon_rect.y + 90
        for index in range(weapon.max_level):
            chip_rect = pygame.Rect(weapon_rect.x + 18 + index * 40, chip_y, 28, 10)
            chip_color = weapon.color if index < weapon.level else (58, 64, 76)
            pygame.draw.rect(surface, chip_color, chip_rect, border_radius=4)
            pygame.draw.rect(surface, (245, 245, 245), chip_rect, width=1, border_radius=4)

        stat_y = weapon_rect.y + 114
        fire_rate = 1.0 / weapon.cooldown if weapon.cooldown > 0 else 0.0
        stats = (
            f"DMG {weapon.damage}",
            f"RATE {fire_rate:.1f}/s",
            f"PEL {weapon.pellets}",
            f"SPD {int(weapon.projectile_speed)}",
        )
        for index, stat in enumerate(stats):
            column = index % 2
            row = index // 2
            pos = (weapon_rect.x + 18 + column * 122, stat_y + row * 24)
            surface.blit(self.app.small_font.render(stat, True, (238, 238, 241)), pos)

        controls = self.app.small_font.render(
            "WASD move  |  LMB fire  |  1/2/3 switch  |  ESC menu",
            True,
            (182, 193, 210),
        )
        surface.blit(controls, (controls_rect.x + 14, controls_rect.y + 7))

        top_row_bottom = max(vitals_rect.bottom, wave_rect.bottom, weapon_rect.bottom)
        wave_banner_y = top_row_bottom + 36
        boss_banner_y = wave_banner_y + 64

        if boss is not None:
            boss_rect = pygame.Rect(width - 304, 182, 286, 72)
            self.draw_panel(surface, boss_rect, accent=(255, 166, 112), fill=(28, 12, 16, 220))
            surface.blit(
                self.app.small_font.render("MINI-BOSS ACTIVE", True, (255, 197, 135)),
                (boss_rect.x + 18, boss_rect.y + 14),
            )
            boss_name = self.app.hud_font.render(boss.boss_title, True, (247, 244, 238))
            surface.blit(boss_name, (boss_rect.x + 18, boss_rect.y + 34))
            boss_hp = self.app.small_font.render(
                f"HP {int(boss.health)}/{boss.max_health}",
                True,
                (243, 224, 214),
            )
            surface.blit(boss_hp, (boss_rect.x + 156, boss_rect.y + 38))

        if self._wave_banner_timer > 0:
            self.draw_banner(
                surface,
                f"Wave {wave_number}",
                accent=(102, 173, 242),
                y=wave_banner_y,
                progress=self._wave_banner_timer / self._wave_banner_duration,
                width=300,
                center_x=340,
            )

        if self._boss_banner_timer > 0:
            self.draw_banner(
                surface,
                self._boss_banner_text,
                accent=(236, 147, 94),
                y=boss_banner_y,
                progress=self._boss_banner_timer / self._boss_banner_duration,
                width=390,
                center_x=350,
            )

        if self._pickup_banner_timer > 0:
            self.draw_banner(
                surface,
                self._pickup_banner_text,
                accent=weapon.color,
                y=height - 92,
                progress=self._pickup_banner_timer / self._pickup_banner_duration,
                width=360,
            )

    def draw_banner(
        self,
        surface: pygame.Surface,
        text: str,
        *,
        accent: tuple[int, int, int],
        y: int,
        progress: float,
        width: int,
        center_x: int | None = None,
    ) -> None:
        """Draw a temporary banner message on the screen.

        Args:
            surface: Surface that receives the banner.
            text: Banner text to display.
            accent: RGB accent color for the banner border.
            y: Vertical center position of the banner.
            progress: Remaining progress in the ``0..1`` range used for fade
                intensity.
            width: Banner width in pixels.
            center_x: Optional custom horizontal center position.

        Returns:
            None.
        """
        alpha = max(0, min(255, int(255 * progress)))
        banner = pygame.Surface((width, 58), pygame.SRCALPHA)
        rect = banner.get_rect()
        pygame.draw.rect(banner, (16, 20, 28, int(alpha * 0.9)), rect, border_radius=18)
        pygame.draw.rect(banner, (*accent, alpha), rect, width=2, border_radius=18)
        pygame.draw.line(banner, (255, 255, 255, int(alpha * 0.16)), (18, 14), (width - 18, 14), 2)
        label = self.app.default_font.render(text, True, (252, 248, 241))
        banner.blit(label, label.get_rect(center=rect.center))
        target_x = surface.get_width() // 2 if center_x is None else center_x
        surface.blit(banner, banner.get_rect(center=(target_x, y)))

    def draw_pickup(self, surface: pygame.Surface, pickup: WeaponPickup) -> None:
        """Render a floating weapon pickup.

        Args:
            surface: Framebuffer surface used for the current frame.
            pickup: Pickup instance that should be drawn.

        Returns:
            None.
        """
        center = pygame.Vector2(pickup.position.x, pickup.position.y + pickup.draw_offset)
        center_xy = (int(center.x), int(center.y))
        self.draw_glow(surface, center_xy, int((pickup.radius + 10) * pickup.pulse), pickup.color, 120)
        pygame.draw.circle(surface, (18, 22, 28), center_xy, pickup.radius + 6)

        points = []
        for index in range(4):
            angle = math.radians(pickup.rotation + 45 + index * 90)
            points.append(
                (
                    center.x + math.cos(angle) * pickup.radius,
                    center.y + math.sin(angle) * pickup.radius,
                )
            )
        pygame.draw.polygon(surface, pickup.color, points)
        pygame.draw.polygon(surface, (250, 248, 242), points, width=2)

        label = self.app.small_font.render("+1", True, (14, 18, 24))
        surface.blit(label, label.get_rect(center=center_xy))

    def draw_projectile(self, surface: pygame.Surface, projectile: Projectile) -> None:
        """Render a projectile trail and core sprite.

        Args:
            surface: Framebuffer surface used for the current frame.
            projectile: Projectile instance that should be drawn.

        Returns:
            None.
        """
        direction = projectile.velocity.normalize() if projectile.velocity.length_squared() > 0 else pygame.Vector2(1, 0)
        tail_length = 20 if not projectile.from_enemy else 15
        tail_start = projectile.position - direction * tail_length
        tail_color = self.mix_color(projectile.color, (255, 255, 255), 0.22)

        self.draw_glow(surface, projectile.position, projectile.radius * 5, projectile.color, 90)
        pygame.draw.line(surface, tail_color, tail_start, projectile.position, max(2, projectile.radius * 2))
        pygame.draw.circle(surface, projectile.color, projectile.position, projectile.radius)
        pygame.draw.circle(surface, (255, 255, 255), projectile.position, max(1, projectile.radius - 1))

    def create_enemy_hit_score_text(self, enemy: Enemy) -> FloatingTextEffect | None:
        """Create a floating hit-text effect for a damaged enemy.

        Args:
            enemy: Enemy that has just been hit.

        Returns:
            ``FloatingTextEffect`` instance when the configured chance succeeds,
            otherwise ``None``.
        """
        config = resolve_enemy_hit_text(self.default_enemy_hit_text | enemy.hit_text_config)
        text_options = config["text"]
        if not text_options or self.random.random() > config["chance"]:
            return None

        text = self.random.choice(text_options)
        text_surface = self.app.hud_font.render(text, True, config["color"])
        start_position = pygame.Vector2(enemy.position.x, enemy.position.y + config["offset_y"])
        velocity = pygame.Vector2(
            self.random.uniform(
                config["drift_x_min"],
                config["drift_x_max"],
            ),
            self.random.uniform(
                config["launch_y_min"],
                config["launch_y_max"],
            ),
        )
        return FloatingTextEffect(
            start_position,
            text_surface,
            velocity=velocity,
            gravity=config["gravity"],
            duration=config["lifetime"],
        )

    def get_enemy_sprite(self, enemy: Enemy) -> pygame.Surface | None:
        """Fetch a cached circular sprite for an enemy.

        Args:
            enemy: Enemy whose sprite should be loaded.

        Returns:
            Circular sprite surface, or ``None`` when no sprite is available.
        """
        return self.app.resources.get_round_sprite(enemy.sprite_path, enemy.radius * 2)

    def get_player_sprite(self) -> pygame.Surface | None:
        """Fetch a cached circular sprite for the active player profile.

        Returns:
            Circular sprite surface, or ``None`` when no sprite is available.
        """
        return self.app.resources.get_round_sprite(self.player.sprite_path, self.player.radius * 2)

    def draw_enemy(self, surface: pygame.Surface, enemy: Enemy) -> None:
        """Render an enemy with sprite fallback, aura, and health bar.

        Args:
            surface: Framebuffer surface used for the current frame.
            enemy: Enemy instance that should be drawn.

        Returns:
            None.
        """
        center = pygame.Vector2(enemy.position.x, enemy.position.y + math.sin(enemy.phase) * (2 if enemy.is_miniboss else 1))
        center_xy = (int(center.x), int(center.y))
        shadow = pygame.Surface((enemy.radius * 3, enemy.radius * 2), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 70), shadow.get_rect())
        surface.blit(shadow, (center.x - shadow.get_width() // 2, center.y + enemy.radius * 0.35))

        aura_radius = enemy.radius + (24 if enemy.is_miniboss else 14)
        aura_alpha = 130 if enemy.is_miniboss else 70
        self.draw_glow(surface, center_xy, aura_radius, enemy.color, aura_alpha)

        outer_color = self.mix_color(enemy.color, (10, 12, 16), 0.35)
        inner_color = self.boost_color(enemy.color, 0.18)
        sprite = self.get_enemy_sprite(enemy)
        if sprite is not None:
            pygame.draw.circle(surface, outer_color, center_xy, enemy.radius + 4)
            surface.blit(sprite, sprite.get_rect(center=center_xy))
            pygame.draw.circle(surface, inner_color, center_xy, enemy.radius, width=2)
        else:
            pygame.draw.circle(surface, outer_color, center_xy, enemy.radius + 4)
            pygame.draw.circle(surface, enemy.color, center_xy, enemy.radius)
            pygame.draw.circle(surface, inner_color, center_xy, max(5, enemy.radius - 5))

        if enemy.behavior == "keep_distance":
            pygame.draw.circle(surface, enemy.accent_color, center_xy, enemy.radius + 8, width=1)
        elif enemy.behavior == "kamikaze":
            pygame.draw.line(surface, (255, 236, 210), (center.x - 7, center.y - 7), (center.x + 7, center.y + 7), 2)
            pygame.draw.line(surface, (255, 236, 210), (center.x + 7, center.y - 7), (center.x - 7, center.y + 7), 2)
        elif enemy.name == "tank":
            pygame.draw.rect(surface, enemy.accent_color, pygame.Rect(center.x - 8, center.y - 4, 16, 8), width=2, border_radius=3)

        if enemy.is_miniboss:
            pygame.draw.circle(surface, (255, 221, 160), center_xy, enemy.radius + 8, width=2)
            if enemy.boss_pattern == "juggernaut":
                pygame.draw.line(surface, (255, 210, 150), (center.x - 10, center.y), (center.x + 10, center.y), 2)
            elif enemy.boss_pattern == "stormcaller":
                pygame.draw.arc(surface, (154, 218, 255), pygame.Rect(center.x - 14, center.y - 14, 28, 28), 0.3, 2.8, 2)
            elif enemy.boss_pattern == "reaper":
                pygame.draw.line(surface, (255, 206, 236), (center.x - 8, center.y - 8), (center.x + 8, center.y + 8), 2)
                pygame.draw.line(surface, (255, 206, 236), (center.x + 8, center.y - 8), (center.x - 8, center.y + 8), 2)
            elif enemy.boss_pattern == "overlord":
                pygame.draw.circle(surface, (255, 231, 166), center_xy, enemy.radius + 12, width=1)

        if sprite is None:
            to_player = self.player.position - enemy.position
            eye_direction = to_player.normalize() if to_player.length_squared() > 0 else pygame.Vector2(1, 0)
            eye_pos = enemy.position + eye_direction * enemy.radius * 0.34
            eye_radius = max(3, enemy.radius // 4)
            pygame.draw.circle(surface, (255, 244, 236), eye_pos, eye_radius)
            pygame.draw.circle(surface, (26, 18, 18), eye_pos, max(1, eye_radius // 2))

        bar_rect = pygame.Rect(center.x - enemy.radius, center.y - enemy.radius - 16, enemy.radius * 2, 6)
        fill_rect = pygame.Rect(bar_rect.x, bar_rect.y, int(bar_rect.width * enemy.health_ratio), bar_rect.height)
        pygame.draw.rect(surface, (60, 20, 24), bar_rect, border_radius=3)
        pygame.draw.rect(surface, (239, 105, 105), fill_rect, border_radius=3)
        if enemy.is_miniboss:
            pygame.draw.rect(surface, (255, 215, 152), bar_rect, width=1, border_radius=3)

    def draw_player(self, surface: pygame.Surface) -> None:
        """Render the player, equipped weapon barrel, and invulnerability aura.

        Args:
            surface: Framebuffer surface used for the current frame.

        Returns:
            None.
        """
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        aim = mouse_pos - self.player.position
        direction = aim.normalize() if aim.length_squared() > 0 else pygame.Vector2(1, 0)
        perp = pygame.Vector2(-direction.y, direction.x)
        center_xy = (int(self.player.position.x), int(self.player.position.y))
        aura_color = (255, 214, 120) if self._invulnerability_timer > 0 else self.current_weapon().color

        shadow = pygame.Surface((self.player.radius * 4, self.player.radius * 3), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow, (0, 0, 0, 78), shadow.get_rect())
        surface.blit(shadow, (self.player.position.x - shadow.get_width() // 2, self.player.position.y + self.player.radius * 0.4))

        self.draw_glow(surface, center_xy, self.player.radius + 22, aura_color, 110)
        sprite = self.get_player_sprite()
        if sprite is not None:
            outline_color = self.boost_color(self.current_weapon().color, 0.22)
            pygame.draw.circle(surface, (12, 16, 21), center_xy, self.player.radius + 6)
            surface.blit(sprite, sprite.get_rect(center=center_xy))
            pygame.draw.circle(surface, outline_color, center_xy, self.player.radius + 2, width=2)
            if self._invulnerability_timer > 0:
                pygame.draw.circle(surface, (255, 224, 124), center_xy, self.player.radius + 4, width=3)
        else:
            pygame.draw.circle(surface, (12, 16, 21), center_xy, self.player.radius + 6)

            body_color = self.player.color if self._invulnerability_timer <= 0 else (255, 224, 124)
            inner_color = self.boost_color(body_color, 0.18)
            pygame.draw.circle(surface, body_color, center_xy, self.player.radius + 1)
            pygame.draw.circle(surface, inner_color, center_xy, max(5, self.player.radius - 4))
            pygame.draw.circle(surface, (18, 22, 27), center_xy, max(4, self.player.radius - 9))

        barrel_base = self.player.position + direction * 6
        barrel_tip = self.player.position + direction * (self.player.radius + 16)
        barrel_points = [
            barrel_base + perp * 4,
            barrel_base - perp * 4,
            barrel_tip - perp * 2,
            barrel_tip + perp * 2,
        ]
        pygame.draw.polygon(surface, self.boost_color(self.current_weapon().color, 0.24), barrel_points)
        if sprite is None:
            pygame.draw.circle(surface, (247, 247, 247), center_xy, 4)

    def draw_crosshair(self, surface: pygame.Surface) -> None:
        """Render the weapon crosshair at the mouse position.

        Args:
            surface: Framebuffer surface used for the current frame.

        Returns:
            None.
        """
        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        if not self.bounds.collidepoint(mouse_pos):
            return

        weapon = self.current_weapon()
        radius = 10 + int(weapon.spread_degrees * 0.25) + max(0, weapon.pellets - 1) * 2
        pulse = 1 + int(2 * (0.5 + 0.5 * math.sin(self.total_elapsed * 7)))
        self.draw_glow(surface, mouse_pos, radius + 16, weapon.color, 70)
        pygame.draw.circle(surface, weapon.color, mouse_pos, radius + pulse, width=1)
        pygame.draw.circle(surface, (255, 245, 240), mouse_pos, 2)

        gap = radius + 5
        arm = radius + 11
        pygame.draw.line(surface, weapon.color, (mouse_pos.x, mouse_pos.y - arm), (mouse_pos.x, mouse_pos.y - gap), 2)
        pygame.draw.line(surface, weapon.color, (mouse_pos.x, mouse_pos.y + gap), (mouse_pos.x, mouse_pos.y + arm), 2)
        pygame.draw.line(surface, weapon.color, (mouse_pos.x - arm, mouse_pos.y), (mouse_pos.x - gap, mouse_pos.y), 2)
        pygame.draw.line(surface, weapon.color, (mouse_pos.x + gap, mouse_pos.y), (mouse_pos.x + arm, mouse_pos.y), 2)

    def render(self, surface: pygame.Surface) -> None:
        """Draw the complete gameplay frame in the correct visual order.

        Args:
            surface: Framebuffer surface used for the current frame.

        Returns:
            None.
        """
        self.draw_background(surface)

        for pickup in self.pickups:
            self.draw_pickup(surface, pickup)

        for projectile in self.projectiles:
            self.draw_projectile(surface, projectile)

        for enemy in self.enemies:
            self.draw_enemy(surface, enemy)

        self.draw_player(surface)

        for effect in self.effects:
            effect.draw(surface)

        self.draw_crosshair(surface)
        self.draw_hud(surface)
