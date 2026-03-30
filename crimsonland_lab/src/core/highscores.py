from __future__ import annotations

import json
import string
from pathlib import Path
from typing import Any, Mapping

DEFAULT_SCORE_NAME = "Player"
MAX_SCORE_NAME_LENGTH = 14
ALLOWED_SCORE_NAME_CHARACTERS = frozenset(string.ascii_letters + string.digits + " _-")


def sanitize_score_name(name: str, *, max_length: int = MAX_SCORE_NAME_LENGTH) -> str:
    """Normalize a score-table name to the project's ASCII-only format.

    Args:
        name: Raw name entered by the player or loaded from storage.
        max_length: Maximum number of characters that should be preserved.

    Returns:
        Sanitized player name that contains only English letters, digits,
        spaces, underscores, and hyphens. Falls back to ``"Player"`` when the
        input does not contain any allowed characters.
    """
    filtered = "".join(character for character in name if character in ALLOWED_SCORE_NAME_CHARACTERS)
    normalized = " ".join(filtered.split())
    return normalized[:max_length].strip() or DEFAULT_SCORE_NAME


def _normalize_score_entry(entry: Mapping[str, Any]) -> dict[str, Any]:
    """Convert a raw JSON score entry to a stable runtime representation.

    Args:
        entry: Mapping loaded from ``scores.json``.

    Returns:
        Normalized score dictionary with sanitized ``name``, integer ``score``,
        and string ``date`` fields.
    """
    return {
        "name": sanitize_score_name(str(entry.get("name", ""))),
        "score": int(entry.get("score", 0)),
        "date": str(entry.get("date", "---")),
    }


def load_scores(path: str | Path) -> list[dict[str, Any]]:
    """Load, sanitize, and sort high-score entries.

    Args:
        path: Relative or absolute path to the score JSON file.

    Returns:
        Top score entries sorted in descending order by score. Invalid items are
        ignored, and stored names are normalized to the project's single
        language/ASCII format.
    """
    file_path = Path(path)
    if not file_path.exists():
        return []
    with file_path.open("r", encoding="utf-8") as file:
        data = json.load(file)
    raw_scores = data.get("scores", [])
    if not isinstance(raw_scores, list):
        return []
    scores = [_normalize_score_entry(item) for item in raw_scores if isinstance(item, Mapping)]
    scores.sort(key=lambda item: item["score"], reverse=True)
    return scores[:10]


def save_scores(path: str | Path, scores: list[dict[str, Any]]) -> None:
    """Persist the current top-10 table to disk.

    Args:
        path: Relative or absolute output path for the score JSON file.
        scores: Runtime score entries that should be written.

    Returns:
        None. The function writes the sanitized top-10 list to disk.
    """
    file_path = Path(path)
    normalized_scores = [_normalize_score_entry(entry) for entry in scores[:10]]
    file_path.write_text(
        json.dumps({"scores": normalized_scores}, ensure_ascii=True, indent=2),
        encoding="utf-8",
    )


def insert_score(
    existing_scores: list[dict[str, Any]],
    name: str,
    score: int,
    achieved_at: str,
) -> tuple[list[dict[str, Any]], int]:
    """Insert a new score into an existing top-10 table.

    Args:
        existing_scores: Current score entries sorted or unsorted.
        name: Raw player name for the new entry.
        score: Achieved score value.
        achieved_at: Date string that will be stored with the score.

    Returns:
        A tuple containing the updated top-10 list and the zero-based position
        of the inserted record inside that updated list. When the score does not
        remain in the top 10, the returned position equals ``len(updated)``.
    """
    normalized_name = sanitize_score_name(name)
    updated = list(existing_scores)
    updated.append({"name": normalized_name, "score": int(score), "date": str(achieved_at)})
    updated.sort(key=lambda item: item["score"], reverse=True)
    updated = updated[:10]

    position = next(
        (
            index
            for index, item in enumerate(updated)
            if item["name"] == normalized_name and item["score"] == int(score)
        ),
        len(updated),
    )
    return updated, position
