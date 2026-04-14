"""Presentation helpers that prepare HTML template context."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from car_salon.exceptions import CarSalonError
from car_salon.models import Car
from car_salon.services import CarSalonService


def format_price(value: float) -> str:
    """Format monetary values for the UI."""

    return f"${value:,.2f}"


def format_datetime(value: datetime | None) -> str:
    """Format datetimes for the UI tables."""

    if value is None:
        return "—"
    return value.strftime("%Y-%m-%d %H:%M")


def build_dashboard_context(
    service: CarSalonService,
    *,
    message: str | None = None,
    error: str | None = None,
    selected_car_id: int | None = None,
) -> dict[str, Any]:
    """Build template context for the main dashboard page."""

    cars = service.cars.list()
    clients = service.clients.list()
    sellers = service.sellers.list()
    test_drives = service.test_drives.list()
    sales = service.sales.list()
    service_orders = service.services.list()
    spaces = service.spaces.list()

    selected_car: Car | None = None
    selected_car_docs = []
    if selected_car_id is not None:
        try:
            selected_car = service.cars.get(selected_car_id)
            selected_car_docs = service.docs.list_for_car(selected_car_id)
        except CarSalonError:
            if error is None:
                error = f"Автомобиль id={selected_car_id} не найден"
    elif cars:
        selected_car = cars[0]
        selected_car_id = selected_car.id
        selected_car_docs = service.docs.list_for_car(selected_car.id)

    spaces_with_occupancy = [
        {
            "space": space,
            "occupancy": service.spaces.occupancy(space.id),
        }
        for space in spaces
    ]

    summary_cards = [
        {
            "title": "Автомобили",
            "value": len(cars),
            "hint": "Состояние автосалона",
        },
        {
            "title": "Клиенты",
            "value": len(clients),
            "hint": "Зарегистрированные клиенты",
        },
        {
            "title": "Продажи",
            "value": len(sales),
            "hint": "Оформленные сделки",
        },
        {
            "title": "Сервис",
            "value": len([order for order in service_orders if order.status == "OPEN"]),
            "hint": "Открытые заказы",
        },
    ]

    return {
        "page_title": "Car Salon FastAPI",
        "message": message,
        "error": error,
        "summary_cards": summary_cards,
        "cars": cars,
        "clients": clients,
        "sellers": sellers,
        "spaces": spaces_with_occupancy,
        "test_drives": test_drives,
        "sales": sales,
        "service_orders": service_orders,
        "selected_car": selected_car,
        "selected_car_docs": selected_car_docs,
        "selected_car_id": selected_car_id,
        "car_options": [
            {
                "id": car.id,
                "label": f"#{car.id} {car.brand} {car.model} ({car.state.value})",
            }
            for car in cars
        ],
        "client_options": [
            {
                "id": client.id,
                "label": f"#{client.id} {client.full_name}",
            }
            for client in clients
        ],
        "seller_options": [
            {
                "id": seller.id,
                "label": f"#{seller.id} {seller.full_name}",
            }
            for seller in sellers
        ],
        "space_options": [
            {
                "id": space.id,
                "label": f"#{space.id} {space.name}",
            }
            for space in spaces
        ],
        "format_price": format_price,
        "format_datetime": format_datetime,
    }
