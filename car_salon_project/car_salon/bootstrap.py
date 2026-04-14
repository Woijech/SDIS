"""Shared application bootstrap helpers for CLI and web interfaces."""

from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from .db import connect
from .exceptions import ValidationError
from .repositories import (
    CarRepository,
    ClientRepository,
    DocumentationRepository,
    SaleRepository,
    SellerRepository,
    ServiceOrderRepository,
    ShowroomSpaceRepository,
    TestDriveRepository,
)
from .services import CarSalonService


DEFAULT_DB_PATH = Path("data") / "car_salon.db"


def parse_datetime_input(value: str) -> datetime:
    """Parse user-supplied datetime values accepted by CLI and web forms."""

    normalized = value.strip().replace(" ", "T")
    try:
        if len(normalized) == 16:
            normalized = normalized + ":00"
        return datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValidationError(
            "Invalid datetime format. Use YYYY-MM-DD HH:MM"
        ) from exc


def build_service(db_path: Path) -> CarSalonService:
    """Build a service instance for short-lived interfaces such as CLI."""

    conn = connect(db_path)
    return CarSalonService(
        car_repo=CarRepository(conn),
        client_repo=ClientRepository(conn),
        seller_repo=SellerRepository(conn),
        space_repo=ShowroomSpaceRepository(conn),
        doc_repo=DocumentationRepository(conn),
        testdrive_repo=TestDriveRepository(conn),
        sale_repo=SaleRepository(conn),
        service_repo=ServiceOrderRepository(conn),
    )


@contextmanager
def service_session(db_path: Path) -> Iterator[CarSalonService]:
    """Yield a service instance backed by a connection that is closed afterwards."""

    conn = connect(db_path)
    service = CarSalonService(
        car_repo=CarRepository(conn),
        client_repo=ClientRepository(conn),
        seller_repo=SellerRepository(conn),
        space_repo=ShowroomSpaceRepository(conn),
        doc_repo=DocumentationRepository(conn),
        testdrive_repo=TestDriveRepository(conn),
        sale_repo=SaleRepository(conn),
        service_repo=ServiceOrderRepository(conn),
    )
    try:
        yield service
    finally:
        conn.close()
