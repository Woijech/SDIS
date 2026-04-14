"""Helpers for parsing and validating HTML form submissions."""

from __future__ import annotations

from typing import Any
from urllib.parse import parse_qs

from fastapi import Request

from car_salon.exceptions import ValidationError


async def read_form_data(request: Request) -> dict[str, str]:
    """Parse a standard URL-encoded form body without multipart dependencies."""

    body = (await request.body()).decode("utf-8")
    parsed = parse_qs(body, keep_blank_values=True)
    return {
        key: values[-1] if values else ""
        for key, values in parsed.items()
    }


def get_required_text(form: dict[str, Any], field_name: str, label: str) -> str:
    """Read a required string field from submitted form data."""

    value = str(form.get(field_name, "")).strip()
    if not value:
        raise ValidationError(f"Поле '{label}' обязательно")
    return value


def get_optional_text(form: dict[str, Any], field_name: str) -> str | None:
    """Read an optional string field from submitted form data."""

    value = str(form.get(field_name, "")).strip()
    return value or None


def get_required_int(form: dict[str, Any], field_name: str, label: str) -> int:
    """Read a required integer field from submitted form data."""

    raw_value = get_required_text(form, field_name, label)
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValidationError(f"Поле '{label}' должно быть целым числом") from exc


def get_optional_int(form: dict[str, Any], field_name: str, label: str) -> int | None:
    """Read an optional integer field from submitted form data."""

    raw_value = get_optional_text(form, field_name)
    if raw_value is None:
        return None
    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValidationError(f"Поле '{label}' должно быть целым числом") from exc


def get_required_float(form: dict[str, Any], field_name: str, label: str) -> float:
    """Read a required float field from submitted form data."""

    raw_value = get_required_text(form, field_name, label)
    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValidationError(f"Поле '{label}' должно быть числом") from exc


def get_optional_float(form: dict[str, Any], field_name: str, label: str) -> float | None:
    """Read an optional float field from submitted form data."""

    raw_value = get_optional_text(form, field_name)
    if raw_value is None:
        return None
    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValidationError(f"Поле '{label}' должно быть числом") from exc
