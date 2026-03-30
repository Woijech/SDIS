import unittest

from src.core.highscores import insert_score, sanitize_score_name


class HighScoresTestCase(unittest.TestCase):
    def test_insert_score_keeps_descending_order(self) -> None:
        existing = [
            {"name": "AAA", "score": 100, "date": "2026-03-01"},
            {"name": "BBB", "score": 80, "date": "2026-03-01"},
        ]

        updated, position = insert_score(existing, "YOU", 90, "2026-03-10")

        self.assertEqual(position, 1)
        self.assertEqual(updated[0]["score"], 100)
        self.assertEqual(updated[1]["name"], "YOU")
        self.assertEqual(updated[2]["score"], 80)

    def test_insert_score_trims_to_top_ten(self) -> None:
        existing = [{"name": str(i), "score": 100 - i, "date": "2026-03-01"} for i in range(10)]

        updated, _ = insert_score(existing, "LOW", 1, "2026-03-11")

        self.assertEqual(len(updated), 10)
        self.assertNotIn("LOW", [item["name"] for item in updated])

    def test_sanitize_score_name_keeps_only_allowed_ascii_characters(self) -> None:
        self.assertEqual("Player", sanitize_score_name("ЖЖЖ"))
        self.assertEqual("Ace-1 _", sanitize_score_name("Ace-1 _"))


if __name__ == "__main__":
    unittest.main()
