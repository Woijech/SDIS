from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.config_loader import load_json

DEFAULT_PLAYER_COLOR = (126, 232, 180)


def load_player_profiles(config_dir: Path) -> dict[str, dict[str, Any]]:
    """Load optional player profile definitions from ``players.json``.

    Args:
        config_dir: Directory that contains the configuration files.

    Returns:
        Mapping of profile names to raw profile dictionaries. Returns an empty
        mapping when the file is missing.

    Raises:
        ValueError: If the JSON payload is not an object.
    """
    profiles_path = config_dir / "players.json"
    if not profiles_path.is_file():
        return {}

    raw_profiles = load_json(profiles_path)
    if not isinstance(raw_profiles, dict):
        raise ValueError("players.json must contain a JSON object with player profiles")

    return raw_profiles


def resolve_player_profile(
    settings: dict[str, Any],
    player_profiles: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    """Resolve the effective player profile for the current run.

    Args:
        settings: Global settings loaded from ``settings.json``.
        player_profiles: Optional profile mapping loaded from
            ``players.json``.

    Returns:
        Normalized player profile dictionary containing the selected name,
        movement stats, health, sprite path, and color.

    Raises:
        ValueError: If the selected profile exists but is not a JSON object.
    """
    selected_name = str(settings.get("player_model", "") or "").strip()
    legacy_profile = {
        "speed": settings["player_speed"],
        "radius": settings["player_radius"],
        "health": settings["player_health"],
        "sprite": settings.get("player_sprite", "player.png") or None,
        "color": settings.get("player_color", DEFAULT_PLAYER_COLOR),
    }

    if not player_profiles:
        return _normalize_player_profile(selected_name or "default", legacy_profile)

    if selected_name and selected_name in player_profiles:
        profile_name = selected_name
    elif "default" in player_profiles:
        profile_name = "default"
    else:
        profile_name = next(iter(player_profiles))

    profile_data = player_profiles[profile_name]
    if not isinstance(profile_data, dict):
        raise ValueError(f"Player profile '{profile_name}' must be a JSON object")

    # Let explicit profile values override legacy settings while still using
    # settings.json as a fallback for any omitted fields.
    merged_profile = legacy_profile | profile_data
    return _normalize_player_profile(profile_name, merged_profile)


def _normalize_player_profile(name: str, data: dict[str, Any]) -> dict[str, Any]:
    """Coerce raw profile data to the shape used by the game runtime.

    Args:
        name: Profile identifier that should be exposed in the runtime state.
        data: Raw profile values combined from legacy settings and profile data.

    Returns:
        Dictionary with normalized numeric values, bounded color channels, and a
        cleaned sprite path.
    """
    raw_color = data.get("color", DEFAULT_PLAYER_COLOR)
    if not isinstance(raw_color, (list, tuple)) or len(raw_color) != 3:
        raw_color = DEFAULT_PLAYER_COLOR

    sprite_path = data.get("sprite")
    if isinstance(sprite_path, str):
        normalized_sprite = sprite_path.replace("\\", "/").strip("/") or None
    else:
        normalized_sprite = None

    return {
        "name": name,
        "speed": float(data["speed"]),
        "radius": int(data["radius"]),
        "health": int(data["health"]),
        "sprite": normalized_sprite,
        "color": tuple(max(0, min(255, int(component))) for component in raw_color),
    }
