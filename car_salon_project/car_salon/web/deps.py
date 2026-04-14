"""Shared web-layer configuration and helpers."""

from __future__ import annotations

from pathlib import Path
from fastapi import Request
from fastapi.templating import Jinja2Templates

WEB_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))


def get_db_path(request: Request) -> Path:
    """Resolve the SQLite path configured on the FastAPI app."""

    return Path(request.app.state.db_path)
