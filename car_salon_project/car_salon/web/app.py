"""FastAPI application factory for the web interface."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from car_salon.bootstrap import DEFAULT_DB_PATH

from .routers.actions import router as actions_router
from .routers.api import router as api_router
from .routers.dashboard import router as dashboard_router

WEB_DIR = Path(__file__).resolve().parent
DB_PATH_ENV_VAR = "CAR_SALON_DB_PATH"


def resolve_db_path() -> Path:
    """Resolve the database path for the module-level FastAPI app."""

    return Path(os.environ.get(DB_PATH_ENV_VAR, DEFAULT_DB_PATH))


def create_app(db_path: Path = DEFAULT_DB_PATH) -> FastAPI:
    """Create and configure the FastAPI application."""

    app = FastAPI(
        title="Car Salon Project",
        description="FastAPI web interface for the car salon laboratory project.",
        version="0.3.0",
    )
    app.state.db_path = str(db_path)

    app.mount(
        "/static",
        StaticFiles(directory=str(WEB_DIR / "static")),
        name="static",
    )

    app.include_router(dashboard_router)
    app.include_router(actions_router)
    app.include_router(api_router)
    return app

app = create_app(resolve_db_path())
