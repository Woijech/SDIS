"""Serialization helpers for JSON API responses."""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from enum import Enum
from typing import Any

from car_salon.services import CarSalonService


def to_serializable(value: Any) -> Any:
    """Convert domain objects to JSON-friendly structures."""

    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [to_serializable(item) for item in value]
    if isinstance(value, dict):
        return {key: to_serializable(item) for key, item in value.items()}
    return value


def serialize_state(service: CarSalonService) -> dict[str, Any]:
    """Build a full JSON snapshot of the current system state."""

    return {
        "cars": [asdict(car) for car in service.cars.list()],
        "clients": [asdict(client) for client in service.clients.list()],
        "sellers": [asdict(seller) for seller in service.sellers.list()],
        "spaces": [
            {
                **asdict(space),
                "occupancy": service.spaces.occupancy(space.id),
            }
            for space in service.spaces.list()
        ],
        "test_drives": [asdict(item) for item in service.test_drives.list()],
        "sales": [asdict(item) for item in service.sales.list()],
        "service_orders": [asdict(item) for item in service.services.list()],
    }


def serialize_car_info(service: CarSalonService, car_id: int) -> dict[str, Any]:
    """Build JSON payload with one car and its documentation."""

    return service.provide_model_info(car_id)
