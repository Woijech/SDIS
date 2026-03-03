"""Application services (business logic).

Implements required operations: sale, test-drive, model info, service maintenance, preparation.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Dict, Optional

from .exceptions import StateTransitionError, ValidationError
from .models import Car, CarState
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


def _validate_non_empty(name: str, value: str) -> None:
    if not value.strip():
        raise ValidationError(f"{name} must be non-empty")


def _validate_price(value: float) -> None:
    if value <= 0:
        raise ValidationError("price must be > 0")


_ALLOWED_CAR_TRANSITIONS = {
    CarState.NEW: {CarState.IN_STOCK, CarState.READY_FOR_SALE},
    CarState.IN_STOCK: {CarState.RESERVED_FOR_TESTDRIVE, CarState.READY_FOR_SALE, CarState.IN_SERVICE},
    CarState.RESERVED_FOR_TESTDRIVE: {CarState.IN_STOCK, CarState.READY_FOR_SALE, CarState.IN_SERVICE},
    CarState.READY_FOR_SALE: {CarState.SOLD, CarState.RESERVED_FOR_TESTDRIVE, CarState.IN_SERVICE},
    CarState.IN_SERVICE: {CarState.IN_STOCK, CarState.READY_FOR_SALE},
    CarState.SOLD: set(),
}


class CarSalonService:
    """Facade for all user-visible operations."""

    def __init__(
        self,
        car_repo: CarRepository,
        client_repo: ClientRepository,
        seller_repo: SellerRepository,
        space_repo: ShowroomSpaceRepository,
        doc_repo: DocumentationRepository,
        testdrive_repo: TestDriveRepository,
        sale_repo: SaleRepository,
        service_repo: ServiceOrderRepository,
    ) -> None:
        self.cars = car_repo
        self.clients = client_repo
        self.sellers = seller_repo
        self.spaces = space_repo
        self.docs = doc_repo
        self.test_drives = testdrive_repo
        self.sales = sale_repo
        self.services = service_repo

    def provide_model_info(self, car_id: int) -> Dict[str, object]:
        car = self.cars.get(car_id)
        docs = self.docs.list_for_car(car_id)
        return {"car": asdict(car), "documentation": [asdict(d) for d in docs]}

    def add_documentation(self, car_id: int, content: str) -> int:
        _validate_non_empty("content", content)
        self.cars.get(car_id)
        doc = self.docs.add(car_id=car_id, content=content, created_at=datetime.now(timezone.utc))
        return doc.id

    def prepare_car_for_sale(self, car_id: int, note: str) -> Car:
        _validate_non_empty("note", note)
        car = self.cars.get(car_id)
        self._transition_car(car, CarState.READY_FOR_SALE)
        self.docs.add(
            car_id=car_id,
            content=f"PREP: {note}",
            created_at=datetime.now(timezone.utc),
        )
        return self.cars.get(car_id)

    def schedule_test_drive(
        self,
        car_id: int,
        client_id: int,
        seller_id: int,
        scheduled_at: datetime,
        notes: Optional[str] = None,
    ) -> int:
        self.cars.get(car_id)
        self.clients.get(client_id)
        self.sellers.get(seller_id)
        car = self.cars.get(car_id)
        if car.state == CarState.SOLD:
            raise StateTransitionError("Cannot schedule test drive for a sold car")
        if car.state != CarState.RESERVED_FOR_TESTDRIVE:
            self._transition_car(car, CarState.RESERVED_FOR_TESTDRIVE)
        td = self.test_drives.add(
            car_id=car_id,
            client_id=client_id,
            seller_id=seller_id,
            scheduled_at=scheduled_at,
            status="SCHEDULED",
            notes=notes,
        )
        return td.id

    def complete_test_drive(self, test_drive_id: int, notes: Optional[str]) -> None:
        td = self.test_drives.get(test_drive_id)
        if td.status != "SCHEDULED":
            raise StateTransitionError("Test drive is not in SCHEDULED status")
        self.test_drives.update_status(test_drive_id, "COMPLETED", notes)
        car = self.cars.get(td.car_id)
        if car.state == CarState.RESERVED_FOR_TESTDRIVE:
            self._transition_car(car, CarState.IN_STOCK)

    def sell_car(self, car_id: int, client_id: int, seller_id: int, price: Optional[float]) -> int:
        self.cars.get(car_id)
        self.clients.get(client_id)
        self.sellers.get(seller_id)
        car = self.cars.get(car_id)
        if car.state == CarState.SOLD:
            raise StateTransitionError("Car already sold")
        if car.state not in {CarState.READY_FOR_SALE, CarState.IN_STOCK}:
            raise StateTransitionError(
                f"Car must be READY_FOR_SALE or IN_STOCK to sell, current={car.state.value}"
            )
        final_price = car.price if price is None else price
        _validate_price(final_price)
        self._transition_car(car, CarState.SOLD)
        sale = self.sales.add(
            car_id=car_id,
            client_id=client_id,
            seller_id=seller_id,
            sold_at=datetime.now(timezone.utc),
            price=final_price,
        )
        self.docs.add(
            car_id=car_id,
            content=f"SALE: client_id={client_id}, seller_id={seller_id}, price={final_price}",
            created_at=datetime.now(timezone.utc),
        )
        return sale.id

    def open_service_order(self, car_id: int, description: str, client_id: Optional[int] = None) -> int:
        self.cars.get(car_id)
        if client_id is not None:
            self.clients.get(client_id)
        _validate_non_empty("description", description)
        car = self.cars.get(car_id)
        if car.state != CarState.IN_SERVICE:
            self._transition_car(car, CarState.IN_SERVICE)
        so = self.services.add(
            car_id=car_id,
            client_id=client_id,
            opened_at=datetime.now(timezone.utc),
            description=description,
            status="OPEN",
        )
        self.docs.add(
            car_id=car_id,
            content=f"SERVICE_OPEN: order_id={so.id}, desc={description}",
            created_at=datetime.now(timezone.utc),
        )
        return so.id

    def close_service_order(self, service_order_id: int) -> None:
        so = self.services.get(service_order_id)
        if so.status != "OPEN":
            raise StateTransitionError("Service order is not OPEN")
        self.services.close(service_order_id, datetime.now(timezone.utc))
        car = self.cars.get(so.car_id)
        docs = self.docs.list_for_car(so.car_id)
        prepared = any(d.content.startswith("PREP:") for d in docs)
        target = CarState.READY_FOR_SALE if prepared else CarState.IN_STOCK
        self._transition_car(car, target)
        self.docs.add(
            car_id=so.car_id,
            content=f"SERVICE_CLOSE: order_id={service_order_id}",
            created_at=datetime.now(timezone.utc),
        )

    def assign_car_to_space(self, car_id: int, space_id: Optional[int]) -> Car:
        self.cars.get(car_id)
        if space_id is None:
            return self.cars.assign_space(car_id, None)
        space = self.spaces.get(space_id)
        current = self.spaces.occupancy(space_id)
        if current >= space.capacity:
            raise ValidationError(
                f"Showroom space '{space.name}' is full ({current}/{space.capacity})"
            )
        return self.cars.assign_space(car_id, space_id)

    def receive_car_to_stock(self, car_id: int) -> Car:
        car = self.cars.get(car_id)
        self._transition_car(car, CarState.IN_STOCK)
        return self.cars.get(car_id)

    def _transition_car(self, car: Car, to_state: CarState) -> None:
        allowed = _ALLOWED_CAR_TRANSITIONS.get(car.state, set())
        if to_state not in allowed and car.state != to_state:
            raise StateTransitionError(
                f"Transition {car.state.value} -> {to_state.value} is not allowed"
            )
        self.cars.update_state(car.id, to_state)
