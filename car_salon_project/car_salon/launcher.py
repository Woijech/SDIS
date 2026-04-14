from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

from .bootstrap import DEFAULT_DB_PATH
from .cli import main as cli_main


def build_web_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="car_salon web",
        description="Запуск FastAPI веб-интерфейса автосалона.",
    )
    parser.add_argument(
        "--db",
        type=Path,
        default=DEFAULT_DB_PATH,
        help=f"Путь к SQLite базе данных (по умолчанию: {DEFAULT_DB_PATH})",
    )
    parser.add_argument("--host", default="127.0.0.1", help="Хост для веб-сервера")
    parser.add_argument("--port", type=int, default=8000, help="Порт для веб-сервера")
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Автоперезагрузка при изменениях исходников",
    )
    return parser


def web_main(argv: Optional[list[str]] = None) -> int:
    args = build_web_parser().parse_args(argv)
    try:
        import uvicorn

        from .web import create_app
        from .web.app import DB_PATH_ENV_VAR
    except ModuleNotFoundError as exc:
        missing_name = exc.name or "dependency"
        raise SystemExit(
            f"Не хватает зависимости для web-режима: {missing_name}. "
            "Установите зависимости проекта перед запуском веб-интерфейса."
        ) from exc

    os.environ[DB_PATH_ENV_VAR] = str(args.db)

    if args.reload:
        uvicorn.run(
            "car_salon.web.app:app",
            host=args.host,
            port=args.port,
            reload=True,
        )
        return 0

    app = create_app(args.db)
    uvicorn.run(app, host=args.host, port=args.port, reload=False)
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv and argv[0] == "web":
        return web_main(argv[1:])
    if argv and argv[0] == "cli":
        return cli_main(argv[1:])
    return cli_main(argv)
