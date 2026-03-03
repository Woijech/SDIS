"""Repositories encapsulate all database access."""

from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import List, Optional

from .exceptions import NotFoundError
from .models import (
    Car,
    CarState,
    Client,
    Documentation,
    Sale,
    Seller,
    ServiceOrder,
    ShowroomSpace,
    TestDrive,
)


def _dt_to_str(dt: datetime) -> str:
    return dt.replace(microsecond=0).isoformat()


def _str_to_dt(value: str) -> datetime:
    return datetime.fromisoformat(value)


class CarRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(
        self,
        vin: str,
        brand: str,
        model: str,
        year: int,
        price: float,
        state: CarState = CarState.NEW,
        space_id: Optional[int] = None,
    ) -> Car:
        with self._conn:
            cur = self._conn.execute(
                """INSERT INTO cars(vin, brand, model, year, price, state, space_id)
                   VALUES(?,?,?,?,?,?,?)""",
                (vin, brand, model, year, price, state.value, space_id),
            )
        return self.get(int(cur.lastrowid))

    def get(self, car_id: int) -> Car:
        row = self._conn.execute("SELECT * FROM cars WHERE id=?", (car_id,)).fetchone()
        if row is None:
            raise NotFoundError(f"Car id={car_id} not found")
        return Car(
            id=int(row["id"]),
            vin=str(row["vin"]),
            brand=str(row["brand"]),
            model=str(row["model"]),
            year=int(row["year"]),
            price=float(row["price"]),
            state=CarState(str(row["state"])),
            space_id=int(row["space_id"]) if row["space_id"] is not None else None,
        )

    def by_vin(self, vin: str) -> Car:
        row = self._conn.execute("SELECT id FROM cars WHERE vin=?", (vin,)).fetchone()
        if row is None:
            raise NotFoundError(f"Car vin={vin} not found")
        return self.get(int(row["id"]))

    def list(self, state: Optional[CarState] = None) -> List[Car]:
        if state is None:
            rows = self._conn.execute("SELECT id FROM cars ORDER BY id").fetchall()
        else:
            rows = self._conn.execute(
                "SELECT id FROM cars WHERE state=? ORDER BY id", (state.value,)
            ).fetchall()
        return [self.get(int(r["id"])) for r in rows]

    def update_state(self, car_id: int, new_state: CarState) -> Car:
        with self._conn:
            self._conn.execute(
                "UPDATE cars SET state=? WHERE id=?", (new_state.value, car_id)
            )
        return self.get(car_id)

    def assign_space(self, car_id: int, space_id: Optional[int]) -> Car:
        with self._conn:
            self._conn.execute("UPDATE cars SET space_id=? WHERE id=?", (space_id, car_id))
        return self.get(car_id)


class ClientRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, full_name: str, phone: str, email: Optional[str]) -> Client:
        with self._conn:
            cur = self._conn.execute(
                "INSERT INTO clients(full_name, phone, email) VALUES(?,?,?)",
                (full_name, phone, email),
            )
        return self.get(int(cur.lastrowid))

    def get(self, client_id: int) -> Client:
        row = self._conn.execute(
            "SELECT * FROM clients WHERE id=?", (client_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError(f"Client id={client_id} not found")
        return Client(
            id=int(row["id"]),
            full_name=str(row["full_name"]),
            phone=str(row["phone"]),
            email=str(row["email"]) if row["email"] is not None else None,
        )

    def list(self) -> List[Client]:
        rows = self._conn.execute("SELECT id FROM clients ORDER BY id").fetchall()
        return [self.get(int(r["id"])) for r in rows]


class SellerRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, full_name: str) -> Seller:
        with self._conn:
            cur = self._conn.execute("INSERT INTO sellers(full_name) VALUES(?)", (full_name,))
        return self.get(int(cur.lastrowid))

    def get(self, seller_id: int) -> Seller:
        row = self._conn.execute(
            "SELECT * FROM sellers WHERE id=?", (seller_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError(f"Seller id={seller_id} not found")
        return Seller(id=int(row["id"]), full_name=str(row["full_name"]))

    def list(self) -> List[Seller]:
        rows = self._conn.execute("SELECT id FROM sellers ORDER BY id").fetchall()
        return [self.get(int(r["id"])) for r in rows]


class ShowroomSpaceRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, name: str, capacity: int) -> ShowroomSpace:
        with self._conn:
            cur = self._conn.execute(
                "INSERT INTO showroom_spaces(name, capacity) VALUES(?,?)", (name, capacity)
            )
        return self.get(int(cur.lastrowid))

    def get(self, space_id: int) -> ShowroomSpace:
        row = self._conn.execute(
            "SELECT * FROM showroom_spaces WHERE id=?", (space_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError(f"ShowroomSpace id={space_id} not found")
        return ShowroomSpace(
            id=int(row["id"]), name=str(row["name"]), capacity=int(row["capacity"])
        )

    def list(self) -> List[ShowroomSpace]:
        rows = self._conn.execute("SELECT id FROM showroom_spaces ORDER BY id").fetchall()
        return [self.get(int(r["id"])) for r in rows]

    def occupancy(self, space_id: int) -> int:
        row = self._conn.execute(
            "SELECT COUNT(*) AS c FROM cars WHERE space_id=?", (space_id,)
        ).fetchone()
        return int(row["c"]) if row is not None else 0


class DocumentationRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(self, car_id: int, content: str, created_at: datetime) -> Documentation:
        with self._conn:
            cur = self._conn.execute(
                "INSERT INTO documentation(car_id, content, created_at) VALUES(?,?,?)",
                (car_id, content, _dt_to_str(created_at)),
            )
        return self.get(int(cur.lastrowid))

    def get(self, doc_id: int) -> Documentation:
        row = self._conn.execute(
            "SELECT * FROM documentation WHERE id=?", (doc_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError(f"Documentation id={doc_id} not found")
        return Documentation(
            id=int(row["id"]),
            car_id=int(row["car_id"]),
            content=str(row["content"]),
            created_at=_str_to_dt(str(row["created_at"])),
        )

    def list_for_car(self, car_id: int) -> List[Documentation]:
        rows = self._conn.execute(
            "SELECT id FROM documentation WHERE car_id=? ORDER BY created_at", (car_id,)
        ).fetchall()
        return [self.get(int(r["id"])) for r in rows]


class TestDriveRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(
        self,
        car_id: int,
        client_id: int,
        seller_id: int,
        scheduled_at: datetime,
        status: str,
        notes: Optional[str],
    ) -> TestDrive:
        cur = self._conn.execute(
            """INSERT INTO test_drives(car_id, client_id, seller_id, scheduled_at, status, notes)
               VALUES(?,?,?,?,?,?)""",
            (car_id, client_id, seller_id, _dt_to_str(scheduled_at), status, notes),
        )
        return self.get(int(cur.lastrowid))

    def get(self, td_id: int) -> TestDrive:
        row = self._conn.execute(
            "SELECT * FROM test_drives WHERE id=?", (td_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError(f"TestDrive id={td_id} not found")
        return TestDrive(
            id=int(row["id"]),
            car_id=int(row["car_id"]),
            client_id=int(row["client_id"]),
            seller_id=int(row["seller_id"]),
            scheduled_at=_str_to_dt(str(row["scheduled_at"])),
            status=str(row["status"]),
            notes=str(row["notes"]) if row["notes"] is not None else None,
        )

    def update_status(self, td_id: int, status: str, notes: Optional[str]) -> TestDrive:
        with self._conn:
            self._conn.execute(
                "UPDATE test_drives SET status=?, notes=? WHERE id=?", (status, notes, td_id)
            )
        return self.get(td_id)

    def list(self, status: Optional[str] = None) -> List[TestDrive]:
        if status is None:
            rows = self._conn.execute("SELECT id FROM test_drives ORDER BY id").fetchall()
        else:
            rows = self._conn.execute(
                "SELECT id FROM test_drives WHERE status=? ORDER BY id", (status,)
            ).fetchall()
        return [self.get(int(r["id"])) for r in rows]


class SaleRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(
        self,
        car_id: int,
        client_id: int,
        seller_id: int,
        sold_at: datetime,
        price: float,
    ) -> Sale:
        with self._conn:
            cur = self._conn.execute(
                """INSERT INTO sales(car_id, client_id, seller_id, sold_at, price)
                   VALUES(?,?,?,?,?)""",
                (car_id, client_id, seller_id, _dt_to_str(sold_at), price),
            )
        return self.get(int(cur.lastrowid))

    def get(self, sale_id: int) -> Sale:
        row = self._conn.execute("SELECT * FROM sales WHERE id=?", (sale_id,)).fetchone()
        if row is None:
            raise NotFoundError(f"Sale id={sale_id} not found")
        return Sale(
            id=int(row["id"]),
            car_id=int(row["car_id"]),
            client_id=int(row["client_id"]),
            seller_id=int(row["seller_id"]),
            sold_at=_str_to_dt(str(row["sold_at"])),
            price=float(row["price"]),
        )

    def list(self) -> List[Sale]:
        rows = self._conn.execute("SELECT id FROM sales ORDER BY id").fetchall()
        return [self.get(int(r["id"])) for r in rows]


class ServiceOrderRepository:
    def __init__(self, conn: sqlite3.Connection) -> None:
        self._conn = conn

    def add(
        self,
        car_id: int,
        client_id: Optional[int],
        opened_at: datetime,
        description: str,
        status: str,
    ) -> ServiceOrder:
        with self._conn:
            cur = self._conn.execute(
                """INSERT INTO service_orders(car_id, client_id, opened_at, closed_at, description, status)
                   VALUES(?,?,?,?,?,?)""",
                (car_id, client_id, _dt_to_str(opened_at), None, description, status),
            )
        return self.get(int(cur.lastrowid))

    def get(self, so_id: int) -> ServiceOrder:
        row = self._conn.execute(
            "SELECT * FROM service_orders WHERE id=?", (so_id,)
        ).fetchone()
        if row is None:
            raise NotFoundError(f"ServiceOrder id={so_id} not found")
        return ServiceOrder(
            id=int(row["id"]),
            car_id=int(row["car_id"]),
            client_id=int(row["client_id"]) if row["client_id"] is not None else None,
            opened_at=_str_to_dt(str(row["opened_at"])),
            closed_at=_str_to_dt(str(row["closed_at"])) if row["closed_at"] else None,
            description=str(row["description"]),
            status=str(row["status"]),
        )

    def close(self, so_id: int, closed_at: datetime) -> ServiceOrder:
        with self._conn:
            self._conn.execute(
                "UPDATE service_orders SET status='CLOSED', closed_at=? WHERE id=?",
                (_dt_to_str(closed_at), so_id),
            )
        return self.get(so_id)

    def list(self, status: Optional[str] = None) -> List[ServiceOrder]:
        if status is None:
            rows = self._conn.execute("SELECT id FROM service_orders ORDER BY id").fetchall()
        else:
            rows = self._conn.execute(
                "SELECT id FROM service_orders WHERE status=? ORDER BY id", (status,)
            ).fetchall()
        return [self.get(int(r["id"])) for r in rows]
