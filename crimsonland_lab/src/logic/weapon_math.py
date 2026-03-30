from __future__ import annotations

import math


def calculate_spread_angles(base_angle_radians: float, pellets: int, spread_degrees: float) -> list[float]:
    """Generate projectile angles for a multi-pellet shot.

    Args:
        base_angle_radians: Central aim angle in radians.
        pellets: Number of projectiles that should be fired.
        spread_degrees: Total spread cone width in degrees.

    Returns:
        List of projectile angles in radians, evenly distributed across the
        requested spread cone.
    """
    if pellets <= 1:
        return [base_angle_radians]

    spread_radians = math.radians(spread_degrees)
    half = spread_radians / 2
    step = spread_radians / (pellets - 1)
    return [base_angle_radians - half + step * index for index in range(pellets)]


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Clamp a numeric value to an inclusive range.

    Args:
        value: Input value to constrain.
        minimum: Lower inclusive bound.
        maximum: Upper inclusive bound.

    Returns:
        ``value`` limited to the interval ``[minimum, maximum]``.
    """
    return max(minimum, min(maximum, value))
