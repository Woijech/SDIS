"""Domain-specific exceptions.

All custom exceptions inherit from :class:`CarSalonError`.
"""

from __future__ import annotations


class CarSalonError(Exception):
    """Base exception for the application."""


class NotFoundError(CarSalonError):
    """Raised when an entity is not found."""


class ValidationError(CarSalonError):
    """Raised when input data is invalid."""


class StateTransitionError(CarSalonError):
    """Raised when a state transition is not allowed."""
