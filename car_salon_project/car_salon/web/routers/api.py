"""JSON API routes."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from car_salon.bootstrap import service_session
from car_salon.web.deps import get_db_path
from car_salon.web.serializers import serialize_car_info, serialize_state, to_serializable

router = APIRouter(prefix="/api", tags=["api"])


@router.get("/state")
async def api_state(request: Request) -> JSONResponse:
    """Return a JSON snapshot of the entire system state."""

    with service_session(get_db_path(request)) as service:
        payload = serialize_state(service)
    return JSONResponse(to_serializable(payload))


@router.get("/cars/{car_id}")
async def api_car_info(car_id: int, request: Request) -> JSONResponse:
    """Return JSON with one car and its documentation."""

    with service_session(get_db_path(request)) as service:
        payload = serialize_car_info(service, car_id)
    return JSONResponse(to_serializable(payload))
