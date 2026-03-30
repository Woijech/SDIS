from __future__ import annotations

from pathlib import Path
from typing import Any

from src.core.config_loader import load_json


def load_particle_effects(config_dir: Path) -> dict[str, Any]:
    """Load optional particle effect overrides from ``particles.json``.

    Args:
        config_dir: Directory that contains the configuration files.

    Returns:
        Particle effect configuration mapping. Returns an empty dictionary when
        the file does not exist.

    Raises:
        ValueError: If the JSON payload is not an object.
    """
    particles_path = config_dir / "particles.json"
    if not particles_path.is_file():
        return {}

    payload = load_json(particles_path)
    if not isinstance(payload, dict):
        raise ValueError("particles.json must contain a JSON object")
    return payload


DEFAULT_ENEMY_HIT_TEXT = {
    "text": None,
    "color": (92, 186, 255),
    "chance": 0.35,
    "lifetime": 0.55,
    "gravity": 420.0,
    "drift_x_min": -65.0,
    "drift_x_max": 65.0,
    "launch_y_min": -105.0,
    "launch_y_max": -50.0,
    "offset_y": -8.0,
}


def resolve_enemy_hit_text(base_config: dict[str, Any] | None) -> dict[str, Any]:
    """Normalize enemy hit-text configuration with safe defaults.

    Args:
        base_config: Optional effect overrides loaded from configuration.

    Returns:
        Dictionary containing normalized hit-text fields used by the effect
        system, including text options, color, spawn chance, movement values,
        and lifetime.
    """
    config = DEFAULT_ENEMY_HIT_TEXT.copy()
    if isinstance(base_config, dict):
        config |= {key: value for key, value in base_config.items() if value is not None}

    raw_text = config.get("text")
    if isinstance(raw_text, str):
        stripped = raw_text.strip()
        text = [stripped] if stripped else None
    elif isinstance(raw_text, list):
        normalized = [item.strip() for item in raw_text if isinstance(item, str) and item.strip()]
        text = normalized or None
    else:
        text = None

    raw_color = config.get("color", DEFAULT_ENEMY_HIT_TEXT["color"])
    if not isinstance(raw_color, (list, tuple)) or len(raw_color) != 3:
        raw_color = DEFAULT_ENEMY_HIT_TEXT["color"]

    chance = max(0.0, min(1.0, float(config.get("chance", DEFAULT_ENEMY_HIT_TEXT["chance"]))))
    lifetime = max(0.05, float(config.get("lifetime", DEFAULT_ENEMY_HIT_TEXT["lifetime"])))
    gravity = float(config.get("gravity", DEFAULT_ENEMY_HIT_TEXT["gravity"]))
    drift_x_min = float(config.get("drift_x_min", DEFAULT_ENEMY_HIT_TEXT["drift_x_min"]))
    drift_x_max = max(drift_x_min, float(config.get("drift_x_max", DEFAULT_ENEMY_HIT_TEXT["drift_x_max"])))
    launch_y_min = float(config.get("launch_y_min", DEFAULT_ENEMY_HIT_TEXT["launch_y_min"]))
    launch_y_max = max(launch_y_min, float(config.get("launch_y_max", DEFAULT_ENEMY_HIT_TEXT["launch_y_max"])))
    offset_y = float(config.get("offset_y", DEFAULT_ENEMY_HIT_TEXT["offset_y"]))

    return {
        "text": text,
        "color": tuple(max(0, min(255, int(component))) for component in raw_color),
        "chance": chance,
        "lifetime": lifetime,
        "gravity": gravity,
        "drift_x_min": drift_x_min,
        "drift_x_max": drift_x_max,
        "launch_y_min": launch_y_min,
        "launch_y_max": launch_y_max,
        "offset_y": offset_y,
    }
