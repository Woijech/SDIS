from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_json(path: str | Path) -> Any:
    """Load and decode a JSON document from disk.

    Args:
        path: Relative or absolute path to the JSON file.

    Returns:
        Parsed JSON payload. The exact type depends on the file contents.
    """
    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as file:
        return json.load(file)
