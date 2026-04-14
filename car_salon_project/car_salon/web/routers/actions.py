"""Form action routes for mutating dashboard operations."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

from car_salon.bootstrap import parse_datetime_input
from car_salon.bootstrap import service_session
from car_salon.exceptions import CarSalonError
from car_salon.web.deps import get_db_path
from car_salon.web.forms import (
    get_optional_float,
    get_optional_int,
    get_optional_text,
    get_required_float,
    get_required_int,
    get_required_text,
    read_form_data,
)
from car_salon.web.navigation import redirect_to_dashboard

router = APIRouter(tags=["actions"])


@router.post("/cars/create")
async def create_car(request: Request) -> RedirectResponse:
    """Create a new car from dashboard form data."""

    try:
        form = await read_form_data(request)
        with service_session(get_db_path(request)) as service:
            car = service.cars.add(
                vin=get_required_text(form, "vin", "VIN"),
                brand=get_required_text(form, "brand", "Марка"),
                model=get_required_text(form, "model", "Модель"),
                year=get_required_int(form, "year", "Год"),
                price=get_required_float(form, "price", "Цена"),
            )
        return redirect_to_dashboard(
            request,
            message=f"Автомобиль #{car.id} успешно добавлен",
            car_id=car.id,
        )
    except CarSalonError as exc:
        return redirect_to_dashboard(request, error=str(exc))


@router.post("/clients/create")
async def create_client(request: Request) -> RedirectResponse:
    """Create a new client from dashboard form data."""

    try:
        form = await read_form_data(request)
        with service_session(get_db_path(request)) as service:
            client = service.clients.add(
                get_required_text(form, "full_name", "ФИО"),
                get_required_text(form, "phone", "Телефон"),
                get_optional_text(form, "email"),
            )
        return redirect_to_dashboard(request, message=f"Клиент #{client.id} добавлен")
    except CarSalonError as exc:
        return redirect_to_dashboard(request, error=str(exc))


@router.post("/sellers/create")
async def create_seller(request: Request) -> RedirectResponse:
    """Create a new seller from dashboard form data."""

    try:
        form = await read_form_data(request)
        with service_session(get_db_path(request)) as service:
            seller = service.sellers.add(
                get_required_text(form, "full_name", "ФИО продавца")
            )
        return redirect_to_dashboard(request, message=f"Продавец #{seller.id} добавлен")
    except CarSalonError as exc:
        return redirect_to_dashboard(request, error=str(exc))


@router.post("/spaces/create")
async def create_space(request: Request) -> RedirectResponse:
    """Create a new showroom space from dashboard form data."""

    try:
        form = await read_form_data(request)
        with service_session(get_db_path(request)) as service:
            space = service.spaces.add(
                get_required_text(form, "name", "Название места"),
                get_required_int(form, "capacity", "Вместимость"),
            )
        return redirect_to_dashboard(request, message=f"Место #{space.id} добавлено")
    except CarSalonError as exc:
        return redirect_to_dashboard(request, error=str(exc))


@router.post("/cars/receive-stock")
async def receive_stock(request: Request) -> RedirectResponse:
    """Move a car to IN_STOCK."""

    car_id: int | None = None
    try:
        form = await read_form_data(request)
        car_id = get_required_int(form, "car_id", "Автомобиль")
        with service_session(get_db_path(request)) as service:
            service.receive_car_to_stock(car_id)
        return redirect_to_dashboard(
            request,
            message=f"Автомобиль #{car_id} переведен в IN_STOCK",
            car_id=car_id,
        )
    except CarSalonError as exc:
        return redirect_to_dashboard(request, error=str(exc), car_id=car_id)


@router.post("/cars/assign-space")
async def assign_space(request: Request) -> RedirectResponse:
    """Assign or clear a showroom space for a car."""

    car_id: int | None = None
    try:
        form = await read_form_data(request)
        car_id = get_required_int(form, "car_id", "Автомобиль")
        raw_space_id = get_optional_int(form, "space_id", "Место")
        space_id = None if raw_space_id in {None, 0} else raw_space_id
        with service_session(get_db_path(request)) as service:
            service.assign_car_to_space(car_id, space_id)
        action_text = "снят с места" if space_id is None else f"назначен на место #{space_id}"
        return redirect_to_dashboard(
            request,
            message=f"Автомобиль #{car_id} {action_text}",
            car_id=car_id,
        )
    except CarSalonError as exc:
        return redirect_to_dashboard(request, error=str(exc), car_id=car_id)


@router.post("/cars/prepare")
async def prepare_car(request: Request) -> RedirectResponse:
    """Prepare a car for sale."""

    car_id: int | None = None
    try:
        form = await read_form_data(request)
        car_id = get_required_int(form, "car_id", "Автомобиль")
        with service_session(get_db_path(request)) as service:
            service.prepare_car_for_sale(
                car_id,
                get_required_text(form, "note", "Заметка"),
            )
        return redirect_to_dashboard(
            request,
            message=f"Автомобиль #{car_id} подготовлен к продаже",
            car_id=car_id,
        )
    except CarSalonError as exc:
        return redirect_to_dashboard(request, error=str(exc), car_id=car_id)


@router.post("/cars/add-doc")
async def add_documentation(request: Request) -> RedirectResponse:
    """Add a documentation record for a car."""

    car_id: int | None = None
    try:
        form = await read_form_data(request)
        car_id = get_required_int(form, "car_id", "Автомобиль")
        with service_session(get_db_path(request)) as service:
            service.add_documentation(
                car_id,
                get_required_text(form, "content", "Документация"),
            )
        return redirect_to_dashboard(
            request,
            message=f"Документация для автомобиля #{car_id} добавлена",
            car_id=car_id,
        )
    except CarSalonError as exc:
        return redirect_to_dashboard(request, error=str(exc), car_id=car_id)


@router.post("/test-drives/schedule")
async def schedule_test_drive(request: Request) -> RedirectResponse:
    """Schedule a test drive."""

    car_id: int | None = None
    try:
        form = await read_form_data(request)
        car_id = get_required_int(form, "car_id", "Автомобиль")
        with service_session(get_db_path(request)) as service:
            test_drive_id = service.schedule_test_drive(
                car_id=car_id,
                client_id=get_required_int(form, "client_id", "Клиент"),
                seller_id=get_required_int(form, "seller_id", "Продавец"),
                scheduled_at=parse_datetime_input(
                    get_required_text(form, "scheduled_at", "Дата и время")
                ),
                notes=get_optional_text(form, "notes"),
            )
        return redirect_to_dashboard(
            request,
            message=f"Тест-драйв #{test_drive_id} назначен",
            car_id=car_id,
        )
    except CarSalonError as exc:
        return redirect_to_dashboard(request, error=str(exc), car_id=car_id)


@router.post("/test-drives/complete")
async def complete_test_drive(request: Request) -> RedirectResponse:
    """Complete a scheduled test drive."""

    try:
        form = await read_form_data(request)
        test_drive_id = get_required_int(form, "test_drive_id", "ID тест-драйва")
        with service_session(get_db_path(request)) as service:
            service.complete_test_drive(test_drive_id, get_optional_text(form, "notes"))
        return redirect_to_dashboard(
            request,
            message=f"Тест-драйв #{test_drive_id} завершен",
        )
    except CarSalonError as exc:
        return redirect_to_dashboard(request, error=str(exc))


@router.post("/sales/create")
async def create_sale(request: Request) -> RedirectResponse:
    """Create a sale from dashboard form data."""

    car_id: int | None = None
    try:
        form = await read_form_data(request)
        car_id = get_required_int(form, "car_id", "Автомобиль")
        with service_session(get_db_path(request)) as service:
            sale_id = service.sell_car(
                car_id=car_id,
                client_id=get_required_int(form, "client_id", "Клиент"),
                seller_id=get_required_int(form, "seller_id", "Продавец"),
                price=get_optional_float(form, "price", "Цена продажи"),
            )
        return redirect_to_dashboard(
            request,
            message=f"Продажа #{sale_id} оформлена",
            car_id=car_id,
        )
    except CarSalonError as exc:
        return redirect_to_dashboard(request, error=str(exc), car_id=car_id)


@router.post("/services/open")
async def open_service_order(request: Request) -> RedirectResponse:
    """Open a service order."""

    car_id: int | None = None
    try:
        form = await read_form_data(request)
        car_id = get_required_int(form, "car_id", "Автомобиль")
        with service_session(get_db_path(request)) as service:
            order_id = service.open_service_order(
                car_id=car_id,
                description=get_required_text(form, "description", "Описание"),
                client_id=get_optional_int(form, "client_id", "Клиент"),
            )
        return redirect_to_dashboard(
            request,
            message=f"Сервисный заказ #{order_id} открыт",
            car_id=car_id,
        )
    except CarSalonError as exc:
        return redirect_to_dashboard(request, error=str(exc), car_id=car_id)


@router.post("/services/close")
async def close_service_order(request: Request) -> RedirectResponse:
    """Close an existing service order."""

    try:
        form = await read_form_data(request)
        order_id = get_required_int(form, "service_order_id", "ID сервисного заказа")
        with service_session(get_db_path(request)) as service:
            service.close_service_order(order_id)
        return redirect_to_dashboard(
            request,
            message=f"Сервисный заказ #{order_id} закрыт",
        )
    except CarSalonError as exc:
        return redirect_to_dashboard(request, error=str(exc))
