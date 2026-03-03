import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from car_salon.db import connect
from car_salon.exceptions import StateTransitionError, ValidationError
from car_salon.models import CarState
from car_salon.repositories import (
    CarRepository,
    ClientRepository,
    DocumentationRepository,
    SaleRepository,
    SellerRepository,
    ServiceOrderRepository,
    ShowroomSpaceRepository,
    TestDriveRepository,
)
from car_salon.services import CarSalonService


def build_service(db_path: Path) -> CarSalonService:
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


class WorkflowTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmpdir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.tmpdir.name) / "test.db"
        self.service = build_service(self.db_path)

        self.space = self.service.spaces.add("Space A", 1)
        self.seller = self.service.sellers.add("Seller One")
        self.client = self.service.clients.add("Client One", "+000", None)
        self.car = self.service.cars.add("VINX", "Brand", "Model", 2022, 10000.0)

    def tearDown(self) -> None:
        self.tmpdir.cleanup()

    def test_assign_space_capacity(self) -> None:
        car2 = self.service.cars.add("VINY", "B", "M", 2023, 11000.0)
        self.service.assign_car_to_space(self.car.id, self.space.id)
        with self.assertRaises(ValidationError):
            self.service.assign_car_to_space(car2.id, self.space.id)

    def test_prepare_and_sell(self) -> None:
        self.service.receive_car_to_stock(self.car.id)
        self.service.prepare_car_for_sale(self.car.id, "prep done")
        sale_id = self.service.sell_car(self.car.id, self.client.id, self.seller.id, None)
        self.assertGreater(sale_id, 0)

        sold_car = self.service.cars.get(self.car.id)
        self.assertEqual(sold_car.state, CarState.SOLD)

        with self.assertRaises(StateTransitionError):
            self.service.sell_car(self.car.id, self.client.id, self.seller.id, None)

    def test_test_drive_flow(self) -> None:
        self.service.receive_car_to_stock(self.car.id)
        when = datetime.now(timezone.utc) + timedelta(days=1)
        td_id = self.service.schedule_test_drive(
            self.car.id, self.client.id, self.seller.id, when, "note"
        )
        car = self.service.cars.get(self.car.id)
        self.assertEqual(car.state, CarState.RESERVED_FOR_TESTDRIVE)

        self.service.complete_test_drive(td_id, "ok")
        car = self.service.cars.get(self.car.id)
        self.assertEqual(car.state, CarState.IN_STOCK)

    def test_test_drive_persistence_between_sessions(self) -> None:
        self.service.receive_car_to_stock(self.car.id)
        when = datetime.now(timezone.utc) + timedelta(days=1)
        self.service.schedule_test_drive(self.car.id, self.client.id, self.seller.id, when, None)

        service2 = build_service(self.db_path)
        test_drives = service2.test_drives.list("SCHEDULED")
        self.assertEqual(len(test_drives), 1)
        self.assertEqual(test_drives[0].car_id, self.car.id)

    def test_service_order_flow(self) -> None:
        self.service.receive_car_to_stock(self.car.id)
        self.service.prepare_car_for_sale(self.car.id, "prep done")

        order_id = self.service.open_service_order(self.car.id, "Oil", self.client.id)
        car = self.service.cars.get(self.car.id)
        self.assertEqual(car.state, CarState.IN_SERVICE)

        self.service.close_service_order(order_id)
        car = self.service.cars.get(self.car.id)
        self.assertEqual(car.state, CarState.READY_FOR_SALE)

    def test_persistence_between_sessions(self) -> None:
        self.service.receive_car_to_stock(self.car.id)
        # New connection -> state should persist
        service2 = build_service(self.db_path)
        car2 = service2.cars.get(self.car.id)
        self.assertEqual(car2.state, CarState.IN_STOCK)


if __name__ == "__main__":
    unittest.main()
