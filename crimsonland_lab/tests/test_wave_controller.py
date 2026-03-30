import unittest

from src.logic.waves import WaveController, build_wave_plans


class WaveControllerTestCase(unittest.TestCase):
    def setUp(self) -> None:
        raw = [
            {
                "number": 1,
                "clear_delay": 1.0,
                "entries": [
                    {"enemy": "walker", "count": 2, "interval": 0.5},
                    {"enemy": "runner", "count": 1, "interval": 0.2},
                ],
            },
            {
                "number": 2,
                "clear_delay": 1.0,
                "entries": [
                    {"enemy": "tank", "count": 1, "interval": 0.1},
                ],
            },
        ]
        self.controller = WaveController(build_wave_plans(raw))
        self.controller.start()

    def test_spawns_all_enemies_in_first_wave(self) -> None:
        spawned = []
        spawned.extend(self.controller.update(0.0, 0))
        spawned.extend(self.controller.update(0.5, 1))
        spawned.extend(self.controller.update(0.5, 2))

        self.assertEqual(spawned, ["walker", "walker", "runner"])
        self.assertTrue(self.controller.waiting_for_clear)

    def test_advances_to_next_wave_after_clear_delay(self) -> None:
        self.controller.update(0.0, 0)
        self.controller.update(0.5, 1)
        self.controller.update(0.5, 1)
        self.controller.update(0.1, 0)
        self.controller.update(1.0, 0)

        self.assertEqual(self.controller.current_wave_number, 2)
        self.assertTrue(self.controller.wave_started_this_frame)


if __name__ == "__main__":
    unittest.main()
