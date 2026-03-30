from __future__ import annotations

MINIBOSS_THEMES = {
    5: {"enemy": "boss_juggernaut", "pattern": "juggernaut"},
    10: {"enemy": "boss_stormcaller", "pattern": "stormcaller"},
    15: {"enemy": "boss_reaper", "pattern": "reaper"},
    20: {"enemy": "boss_overlord", "pattern": "overlord"},
}


def enemy_damage_multiplier(wave_number: int) -> float:
    """Calculate how much enemy contact damage scales for a wave.

    Args:
        wave_number: One-based wave number currently being played.

    Returns:
        Damage multiplier applied to normal enemies on that wave.
    """
    if wave_number <= 1:
        return 1.0
    return 1.0 + 0.07 * (wave_number - 1)


def is_miniboss_wave(wave_number: int) -> bool:
    """Determine whether a wave should spawn a miniboss.

    Args:
        wave_number: One-based wave number currently being played.

    Returns:
        ``True`` when the wave is a positive multiple of five, otherwise
        ``False``.
    """
    return wave_number > 0 and wave_number % 5 == 0


def miniboss_health_multiplier(wave_number: int) -> float:
    """Calculate bonus health scaling for miniboss enemies.

    Args:
        wave_number: One-based wave number currently being played.

    Returns:
        Multiplier applied to miniboss health on the specified wave.
    """
    return 2.8 + 0.12 * wave_number


def miniboss_score_multiplier(wave_number: int) -> float:
    """Calculate score reward scaling for miniboss enemies.

    Args:
        wave_number: One-based wave number currently being played.

    Returns:
        Multiplier applied to the miniboss score reward.
    """
    return 3.0 + 0.05 * wave_number


def miniboss_theme(wave_number: int) -> dict[str, str] | None:
    """Return the miniboss theme assigned to a specific wave.

    Args:
        wave_number: One-based wave number currently being played.

    Returns:
        Copy of the configured miniboss theme for the wave, or ``None`` when
        the wave has no dedicated miniboss theme.
    """
    theme = MINIBOSS_THEMES.get(wave_number)
    if theme is None:
        return None
    return dict(theme)
