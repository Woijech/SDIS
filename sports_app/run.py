"""Точка входа приложения Sports App."""

from __future__ import annotations

import os
from pathlib import Path

from app.controller.controller import AppController


def main() -> None:
    """Создаёт контроллер с БД по умолчанию и запускает GUI."""
    base = Path(__file__).resolve().parent
    db_path = str(base / "data" / "app.db")
    Path(os.path.dirname(db_path)).mkdir(parents=True, exist_ok=True)

    controller = AppController(db_path=db_path)
    controller.run()


if __name__ == "__main__":
    main()
