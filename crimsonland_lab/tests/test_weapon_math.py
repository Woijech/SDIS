import math
import unittest

from src.entities.weapon import Weapon
from src.logic.weapon_math import calculate_spread_angles


class WeaponMathTestCase(unittest.TestCase):
    def test_single_pellet_returns_base_angle(self) -> None:
        angles = calculate_spread_angles(1.0, 1, 25)
        self.assertEqual(angles, [1.0])

    def test_multiple_pellets_are_symmetric(self) -> None:
        angles = calculate_spread_angles(0.0, 5, 20)
        self.assertEqual(len(angles), 5)
        self.assertAlmostEqual(angles[0], -math.radians(10), places=5)
        self.assertAlmostEqual(angles[-1], math.radians(10), places=5)
        self.assertAlmostEqual(angles[2], 0.0, places=5)

    def test_weapon_upgrade_improves_core_stats(self) -> None:
        weapon = Weapon.from_dict(
            "rifle",
            {
                "damage": 9,
                "cooldown": 0.11,
                "projectile_speed": 860,
                "pellets": 1,
                "spread_degrees": 4,
                "color": [120, 214, 255],
            },
        )

        base_damage = weapon.damage
        base_cooldown = weapon.cooldown
        base_speed = weapon.projectile_speed

        weapon.upgrade()

        self.assertGreater(weapon.damage, base_damage)
        self.assertLess(weapon.cooldown, base_cooldown)
        self.assertGreater(weapon.projectile_speed, base_speed)

    def test_shotgun_gains_extra_pellets_after_several_upgrades(self) -> None:
        weapon = Weapon.from_dict(
            "shotgun",
            {
                "damage": 11,
                "cooldown": 0.72,
                "projectile_speed": 610,
                "pellets": 6,
                "spread_degrees": 24,
                "color": [255, 198, 112],
            },
        )

        weapon.upgrade()
        weapon.upgrade()

        self.assertGreater(weapon.pellets, 6)


if __name__ == "__main__":
    unittest.main()
