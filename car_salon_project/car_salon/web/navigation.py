"""Navigation and redirect helpers for the web layer."""

from __future__ import annotations

from urllib.parse import urlencode

from fastapi import Request
from fastapi.responses import RedirectResponse


def redirect_to_dashboard(
    request: Request,
    *,
    message: str | None = None,
    error: str | None = None,
    car_id: int | None = None,
) -> RedirectResponse:
    """Redirect back to the main dashboard while preserving UI feedback."""

    params = {
        key: value
        for key, value in {
            "message": message,
            "error": error,
            "car_id": car_id,
        }.items()
        if value not in {None, ""}
    }
    url = str(request.url_for("dashboard"))
    if params:
        url += "?" + urlencode(params)
    return RedirectResponse(url=url, status_code=303)
