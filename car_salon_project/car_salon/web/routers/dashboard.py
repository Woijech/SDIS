"""HTML dashboard routes."""

from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse

from car_salon.bootstrap import service_session
from car_salon.web.deps import get_db_path, templates
from car_salon.web.presenters import build_dashboard_context

router = APIRouter()


@router.get("/", response_class=HTMLResponse, name="dashboard")
async def dashboard(
    request: Request,
    message: str | None = None,
    error: str | None = None,
    car_id: int | None = None,
) -> HTMLResponse:
    """Render the main HTML dashboard."""

    with service_session(get_db_path(request)) as service:
        context = build_dashboard_context(
            service,
            message=message,
            error=error,
            selected_car_id=car_id,
        )
    context["request"] = request
    return templates.TemplateResponse(request, "dashboard.html", context)
