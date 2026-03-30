import tempfile
import unittest
from pathlib import Path

from src.core.player_profiles import load_player_profiles, resolve_player_profile


class PlayerProfilesTestCase(unittest.TestCase):
    def test_load_player_profiles_reads_players_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_dir = Path(tmp_dir)
            config_dir.joinpath("players.json").write_text(
                '{"default": {"sprite": "player.png"}}',
                encoding="utf-8",
            )

            profiles = load_player_profiles(config_dir)

            self.assertEqual({"default": {"sprite": "player.png"}}, profiles)

    def test_resolve_player_profile_uses_selected_model_and_legacy_defaults(self) -> None:
        settings = {
            "player_speed": 260,
            "player_radius": 16,
            "player_health": 100,
            "player_sprite": "player.png",
            "player_model": "marine",
        }
        profiles = {
            "default": {"sprite": "player.png", "color": [126, 232, 180]},
            "marine": {"sprite": "players/marine.png", "color": [110, 210, 255]},
        }

        profile = resolve_player_profile(settings, profiles)

        self.assertEqual("marine", profile["name"])
        self.assertEqual("players/marine.png", profile["sprite"])
        self.assertEqual((110, 210, 255), profile["color"])
        self.assertEqual(260.0, profile["speed"])
        self.assertEqual(16, profile["radius"])
        self.assertEqual(100, profile["health"])

    def test_resolve_player_profile_falls_back_to_settings_when_profiles_missing(self) -> None:
        settings = {
            "player_speed": 245,
            "player_radius": 18,
            "player_health": 90,
            "player_sprite": "heroes/scout.png",
        }

        profile = resolve_player_profile(settings, {})

        self.assertEqual("default", profile["name"])
        self.assertEqual("heroes/scout.png", profile["sprite"])
        self.assertEqual((126, 232, 180), profile["color"])
        self.assertEqual(245.0, profile["speed"])
        self.assertEqual(18, profile["radius"])
        self.assertEqual(90, profile["health"])

    def test_default_profile_does_not_override_legacy_sprite_settings(self) -> None:
        settings = {
            "player_speed": 260,
            "player_radius": 16,
            "player_health": 100,
            "player_sprite": "heroes/custom.png",
            "player_model": "default",
        }
        profiles = {
            "default": {"sprite": "players/default.png", "color": [110, 210, 255]},
        }

        profile = resolve_player_profile(settings, profiles)

        self.assertEqual("default", profile["name"])
        self.assertEqual("heroes/custom.png", profile["sprite"])
        self.assertEqual((126, 232, 180), profile["color"])


if __name__ == "__main__":
    unittest.main()
