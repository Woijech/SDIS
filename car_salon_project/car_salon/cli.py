from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from .db import connect
from .exceptions import CarSalonError, ValidationError
from .models import CarState
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


def _parse_dt(value: str) -> datetime:
    """Parse datetime in ISO format: YYYY-MM-DDTHH:MM or YYYY-MM-DD HH:MM."""
    v = value.strip().replace(" ", "T")
    try:
        # allow missing seconds
        if len(v) == 16:
            v = v + ":00"
        return datetime.fromisoformat(v)
    except ValueError as exc:
        raise ValidationError(
            "Неверный формат даты/времени. Используйте YYYY-MM-DD HH:MM"
        ) from exc


def _build_service(db_path: Path) -> CarSalonService:
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


def _print(obj: Any) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, default=str))


def cmd_add_car(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    car = service.cars.add(
        vin=args.vin,
        brand=args.brand,
        model=args.model,
        year=args.year,
        price=args.price,
    )
    _print({"created": car.__dict__})


def cmd_list_cars(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    state: Optional[CarState] = CarState(args.state) if args.state else None
    cars = service.cars.list(state=state)
    _print([c.__dict__ for c in cars])


def cmd_add_client(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    client = service.clients.add(args.name, args.phone, args.email)
    _print({"created": client.__dict__})


def cmd_list_clients(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    _print([c.__dict__ for c in service.clients.list()])


def cmd_add_seller(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    seller = service.sellers.add(args.name)
    _print({"created": seller.__dict__})


def cmd_list_sellers(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    _print([s.__dict__ for s in service.sellers.list()])


def cmd_add_space(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    space = service.spaces.add(args.name, args.capacity)
    _print({"created": space.__dict__})


def cmd_list_spaces(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    spaces = []
    for s in service.spaces.list():
        spaces.append({**s.__dict__, "occupancy": service.spaces.occupancy(s.id)})
    _print(spaces)


def cmd_assign_space(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    space_id = None if args.space_id == 0 else args.space_id
    car = service.assign_car_to_space(args.car_id, space_id)
    _print({"updated": car.__dict__})


def cmd_receive_stock(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    car = service.receive_car_to_stock(args.car_id)
    _print({"updated": car.__dict__})


def cmd_add_doc(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    doc_id = service.add_documentation(args.car_id, args.content)
    _print({"doc_id": doc_id})


def cmd_car_info(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    _print(service.provide_model_info(args.car_id))


def cmd_prepare_car(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    car = service.prepare_car_for_sale(args.car_id, args.note)
    _print({"updated": car.__dict__})


def cmd_testdrive_schedule(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    scheduled_at = _parse_dt(args.at)
    td_id = service.schedule_test_drive(
        car_id=args.car_id,
        client_id=args.client_id,
        seller_id=args.seller_id,
        scheduled_at=scheduled_at,
        notes=args.notes,
    )
    _print({"test_drive_id": td_id})


def cmd_testdrive_complete(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    service.complete_test_drive(args.test_drive_id, args.notes)
    _print({"ok": True})


def cmd_list_testdrives(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    tds = service.test_drives.list(status=args.status)
    _print([t.__dict__ for t in tds])


def cmd_sell(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    sale_id = service.sell_car(
        car_id=args.car_id,
        client_id=args.client_id,
        seller_id=args.seller_id,
        price=args.price,
    )
    _print({"sale_id": sale_id})


def cmd_list_sales(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    _print([s.__dict__ for s in service.sales.list()])


def cmd_service_open(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    order_id = service.open_service_order(
        car_id=args.car_id, description=args.description, client_id=args.client_id
    )
    _print({"service_order_id": order_id})


def cmd_service_close(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    service.close_service_order(args.service_order_id)
    _print({"ok": True})


def cmd_list_services(args: argparse.Namespace) -> None:
    service = _build_service(args.db)
    orders = service.services.list(status=args.status)
    _print([o.__dict__ for o in orders])


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="car_salon",
        description="Модель салона автомобилей (вариант 52) — CLI.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Путь к SQLite базе данных (по умолчанию: {DEFAULT_DB_PATH})",
    )

    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("add-car", help="Добавить автомобиль")
    p.add_argument("--vin", required=True)
    p.add_argument("--brand", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--year", type=int, required=True)
    p.add_argument("--price", type=float, required=True)
    p.set_defaults(func=cmd_add_car)

    p = sub.add_parser("list-cars", help="Список автомобилей")
    p.add_argument("--state", choices=[s.value for s in CarState], default=None)
    p.set_defaults(func=cmd_list_cars)

    p = sub.add_parser("add-client", help="Добавить клиента")
    p.add_argument("--name", required=True)
    p.add_argument("--phone", required=True)
    p.add_argument("--email", default=None)
    p.set_defaults(func=cmd_add_client)

    p = sub.add_parser("list-clients", help="Список клиентов")
    p.set_defaults(func=cmd_list_clients)

    p = sub.add_parser("add-seller", help="Добавить продавца")
    p.add_argument("--name", required=True)
    p.set_defaults(func=cmd_add_seller)

    p = sub.add_parser("list-sellers", help="Список продавцов")
    p.set_defaults(func=cmd_list_sellers)

    p = sub.add_parser("add-space", help="Добавить выставочное пространство")
    p.add_argument("--name", required=True)
    p.add_argument("--capacity", type=int, required=True)
    p.set_defaults(func=cmd_add_space)

    p = sub.add_parser("list-spaces", help="Список выставочных пространств")
    p.set_defaults(func=cmd_list_spaces)

    p = sub.add_parser("assign-space", help="Назначить авто в выставочное пространство (0 чтобы снять)")
    p.add_argument("car_id", type=int)
    p.add_argument("space_id", type=int)
    p.set_defaults(func=cmd_assign_space)

    p = sub.add_parser("receive-stock", help="Перевести авто в IN_STOCK")
    p.add_argument("car_id", type=int)
    p.set_defaults(func=cmd_receive_stock)

    p = sub.add_parser("add-doc", help="Добавить запись документации для авто")
    p.add_argument("car_id", type=int)
    p.add_argument("--content", required=True)
    p.set_defaults(func=cmd_add_doc)

    p = sub.add_parser("car-info", help="Информация о модели и документации")
    p.add_argument("car_id", type=int)
    p.set_defaults(func=cmd_car_info)

    p = sub.add_parser("prepare-car", help="Подготовка авто к продаже (READY_FOR_SALE)")
    p.add_argument("car_id", type=int)
    p.add_argument("--note", required=True)
    p.set_defaults(func=cmd_prepare_car)

    p = sub.add_parser("testdrive-schedule", help="Запланировать тест-драйв")
    p.add_argument("car_id", type=int)
    p.add_argument("client_id", type=int)
    p.add_argument("seller_id", type=int)
    p.add_argument("--at", required=True, help="YYYY-MM-DD HH:MM")
    p.add_argument("--notes", default=None)
    p.set_defaults(func=cmd_testdrive_schedule)

    p = sub.add_parser("testdrive-complete", help="Завершить тест-драйв")
    p.add_argument("test_drive_id", type=int)
    p.add_argument("--notes", default=None)
    p.set_defaults(func=cmd_testdrive_complete)

    p = sub.add_parser("list-testdrives", help="Список тест-драйвов")
    p.add_argument("--status", default=None, choices=["SCHEDULED", "COMPLETED", "CANCELED"])
    p.set_defaults(func=cmd_list_testdrives)

    p = sub.add_parser("sell", help="Продать автомобиль")
    p.add_argument("car_id", type=int)
    p.add_argument("client_id", type=int)
    p.add_argument("seller_id", type=int)
    p.add_argument("--price", type=float, default=None)
    p.set_defaults(func=cmd_sell)

    p = sub.add_parser("list-sales", help="Список продаж")
    p.set_defaults(func=cmd_list_sales)

    p = sub.add_parser("service-open", help="Открыть сервисный заказ")
    p.add_argument("car_id", type=int)
    p.add_argument("--description", required=True)
    p.add_argument("--client-id", type=int, default=None)
    p.set_defaults(func=cmd_service_open)

    p = sub.add_parser("service-close", help="Закрыть сервисный заказ")
    p.add_argument("service_order_id", type=int)
    p.set_defaults(func=cmd_service_close)

    p = sub.add_parser("list-services", help="Список сервисных заказов")
    p.add_argument("--status", default=None, choices=["OPEN", "CLOSED"])
    p.set_defaults(func=cmd_list_services)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        args.func(args)
        return 0
    except CarSalonError as exc:
        print(f"Ошибка: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
