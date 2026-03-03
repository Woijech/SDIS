"""Domain models for the car salon system."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional


class CarState(str, Enum):
    """Lifecycle state of a car in the salon."""

    NEW = "NEW"
    IN_STOCK = "IN_STOCK"
    RESERVED_FOR_TESTDRIVE = "RESERVED_FOR_TESTDRIVE"
    READY_FOR_SALE = "READY_FOR_SALE"
    SOLD = "SOLD"
    IN_SERVICE = "IN_SERVICE"


@dataclass(frozen=True)
class Car:
    id: int
    vin: str
    brand: str
    model: str
    year: int
    price: float
    state: CarState
    space_id: Optional[int]


@dataclass(frozen=True)
class Client:
    id: int
    full_name: str
    phone: str
    email: Optional[str]


@dataclass(frozen=True)
class Seller:
    id: int
    full_name: str


@dataclass(frozen=True)
class ShowroomSpace:
    id: int
    name: str
    capacity: int


@dataclass(frozen=True)
class Documentation:
    id: int
    car_id: int
    content: str
    created_at: datetime


@dataclass(frozen=True)
class TestDrive:
    id: int
    car_id: int
    client_id: int
    seller_id: int
    scheduled_at: datetime
    status: str  # SCHEDULED / COMPLETED / CANCELED
    notes: Optional[str]


@dataclass(frozen=True)
class Sale:
    id: int
    car_id: int
    client_id: int
    seller_id: int
    sold_at: datetime
    price: float


@dataclass(frozen=True)
class ServiceOrder:
    id: int
    car_id: int
    client_id: Optional[int]
    opened_at: datetime
    closed_at: Optional[datetime]
    description: str
    status: str  # OPEN / CLOSED
