import unittest

from src.core.particle_effects import resolve_enemy_hit_text


class ParticleEffectsTestCase(unittest.TestCase):
    def test_resolve_enemy_hit_text_uses_defaults(self) -> None:
        config = resolve_enemy_hit_text(None)

        self.assertIsNone(config["text"])
        self.assertEqual((92, 186, 255), config["color"])
        self.assertEqual(0.35, config["chance"])
        self.assertEqual(0.55, config["lifetime"])
        self.assertEqual(420.0, config["gravity"])

    def test_resolve_enemy_hit_text_normalizes_custom_values(self) -> None:
        config = resolve_enemy_hit_text(
            {
                "text": "SC",
                "color": [70, 160, 255],
                "chance": 0.6,
                "lifetime": 0.8,
                "gravity": 510,
                "drift_x_min": -40,
                "drift_x_max": 55,
                "launch_y_min": -90,
                "launch_y_max": -35,
                "offset_y": -10,
            }
        )

        self.assertEqual(["SC"], config["text"])
        self.assertEqual((70, 160, 255), config["color"])
        self.assertEqual(0.6, config["chance"])
        self.assertEqual(0.8, config["lifetime"])
        self.assertEqual(510.0, config["gravity"])
        self.assertEqual(-40.0, config["drift_x_min"])
        self.assertEqual(55.0, config["drift_x_max"])
        self.assertEqual(-90.0, config["launch_y_min"])
        self.assertEqual(-35.0, config["launch_y_max"])
        self.assertEqual(-10.0, config["offset_y"])

    def test_resolve_enemy_hit_text_ignores_null_overrides(self) -> None:
        config = resolve_enemy_hit_text(
            {
                "text": None,
                "color": None,
                "chance": None,
                "lifetime": None,
                "gravity": None,
            }
        )

        self.assertIsNone(config["text"])
        self.assertEqual((92, 186, 255), config["color"])
        self.assertEqual(0.35, config["chance"])
        self.assertEqual(0.55, config["lifetime"])
        self.assertEqual(420.0, config["gravity"])

    def test_resolve_enemy_hit_text_accepts_list_of_words(self) -> None:
        config = resolve_enemy_hit_text(
            {
                "text": ["SC", "CRIT", "", "  ", "HIT"],
            }
        )

        self.assertEqual(["SC", "CRIT", "HIT"], config["text"])


if __name__ == "__main__":
    unittest.main()
