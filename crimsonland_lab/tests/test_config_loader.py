import json
import tempfile
import unittest
from pathlib import Path

from src.core.config_loader import load_json


class ConfigLoaderTestCase(unittest.TestCase):
    def test_load_json_reads_dictionary(self) -> None:
        with tempfile.TemporaryDirectory() as tmp_dir:
            path = Path(tmp_dir) / "sample.json"
            payload = {"answer": 42, "title": "demo"}
            path.write_text(json.dumps(payload), encoding="utf-8")

            loaded = load_json(path)

            self.assertEqual(payload, loaded)


if __name__ == "__main__":
    unittest.main()
