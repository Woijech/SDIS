import unittest

from src.logic.progression import (
    enemy_damage_multiplier,
    is_miniboss_wave,
    miniboss_theme,
    miniboss_health_multiplier,
    miniboss_score_multiplier,
)


class ProgressionTestCase(unittest.TestCase):
    def test_enemy_damage_multiplier_grows_each_wave(self) -> None:
        self.assertEqual(enemy_damage_multiplier(1), 1.0)
        self.assertGreater(enemy_damage_multiplier(6), enemy_damage_multiplier(3))
        self.assertGreater(enemy_damage_multiplier(20), enemy_damage_multiplier(10))

    def test_miniboss_waves_trigger_every_fifth_wave(self) -> None:
        self.assertFalse(is_miniboss_wave(4))
        self.assertTrue(is_miniboss_wave(5))
        self.assertTrue(is_miniboss_wave(20))

    def test_miniboss_scaling_increases_over_time(self) -> None:
        self.assertGreater(miniboss_health_multiplier(20), miniboss_health_multiplier(5))
        self.assertGreater(miniboss_score_multiplier(20), miniboss_score_multiplier(5))

    def test_miniboss_themes_are_unique_for_key_waves(self) -> None:
        self.assertEqual("juggernaut", miniboss_theme(5)["pattern"])
        self.assertEqual("boss_juggernaut", miniboss_theme(5)["enemy"])
        self.assertEqual("stormcaller", miniboss_theme(10)["pattern"])
        self.assertEqual("boss_stormcaller", miniboss_theme(10)["enemy"])
        self.assertEqual("reaper", miniboss_theme(15)["pattern"])
        self.assertEqual("boss_reaper", miniboss_theme(15)["enemy"])
        self.assertEqual("overlord", miniboss_theme(20)["pattern"])
        self.assertEqual("boss_overlord", miniboss_theme(20)["enemy"])


if __name__ == "__main__":
    unittest.main()
