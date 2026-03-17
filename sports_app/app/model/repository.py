"""SQLite-репозиторий с CRUD, поиском и удалением записей спортсменов."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Sequence
from contextlib import suppress
from pathlib import Path
from typing import Final

from .athlete import Athlete


class AthleteRepository:
    """Инкапсулирует доступ к таблице `athletes` и правилам поиска варианта."""

    _TABLE: Final[str] = "athletes"
    _SELECT_FIELDS: Final[str] = "fio, squad, position, titles, sport, rank"
    _ALLOWED_ORDER_BY: Final[set[str]] = {"fio COLLATE NOCASE"}

    def __init__(self, db_path: str):
        """Открывает соединение и гарантирует наличие схемы в файле БД."""
        self.db_path = db_path
        Path(os.path.dirname(db_path) or ".").mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def close(self) -> None:
        """Закрывает соединение с БД."""
        if self._conn is None:
            return
        with suppress(sqlite3.Error):
            self._conn.close()
        self._conn = None

    def _get_conn(self) -> sqlite3.Connection:
        if self._conn is None:
            raise RuntimeError("Соединение с БД уже закрыто")
        return self._conn

    def _ensure_schema(self) -> None:
        """Создаёт таблицу и индексы при первом запуске."""
        conn = self._get_conn()
        with conn:
            cur = conn.cursor()
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS athletes (
                    fio TEXT NOT NULL,
                    squad TEXT NOT NULL,
                    position TEXT NOT NULL,
                    titles INTEGER NOT NULL,
                    sport TEXT NOT NULL,
                    rank TEXT NOT NULL
                )
                """
            )
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_athletes_fio ON {self._TABLE} (fio COLLATE NOCASE)")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_athletes_sport ON {self._TABLE} (sport COLLATE NOCASE)")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_athletes_rank ON {self._TABLE} (rank COLLATE NOCASE)")
            cur.execute(f"CREATE INDEX IF NOT EXISTS idx_athletes_titles ON {self._TABLE} (titles)")

    def add(self, athlete: Athlete) -> Athlete:
        """Добавляет одну запись и возвращает её нормализованное представление."""
        normalized = athlete.normalized()
        conn = self._get_conn()
        with conn:
            conn.execute(
                f"""
                INSERT INTO {self._TABLE} (fio, squad, position, titles, sport, rank)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    normalized.fio,
                    normalized.squad,
                    normalized.position,
                    normalized.titles,
                    normalized.sport,
                    normalized.rank,
                ),
            )
        return normalized

    def replace_all(self, athletes: Sequence[Athlete]) -> None:
        """Заменяет содержимое таблицы переданным набором записей."""
        normalized = [athlete.normalized() for athlete in athletes]
        payload = [
            (
                athlete.fio,
                athlete.squad,
                athlete.position,
                athlete.titles,
                athlete.sport,
                athlete.rank,
            )
            for athlete in normalized
        ]
        conn = self._get_conn()
        with conn:
            cur = conn.cursor()
            cur.execute(f"DELETE FROM {self._TABLE}")
            cur.executemany(
                f"""
                INSERT INTO {self._TABLE} (fio, squad, position, titles, sport, rank)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                payload,
            )

    def list_page(self, page: int, page_size: int) -> tuple[list[Athlete], int]:
        """Возвращает страницу записей и общее число строк."""
        page = max(1, int(page))
        page_size = max(1, int(page_size))
        total = self._count(f"SELECT COUNT(*) FROM {self._TABLE}", ())
        offset = (page - 1) * page_size
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT {self._SELECT_FIELDS}
            FROM {self._TABLE}
            ORDER BY fio COLLATE NOCASE
            LIMIT ? OFFSET ?
            """,
            (page_size, offset),
        )
        rows = cur.fetchall()
        return [self._row_to_athlete(row) for row in rows], total

    def distinct_sports(self) -> list[str]:
        """Возвращает уникальные виды спорта в алфавитном порядке."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(f"SELECT DISTINCT sport FROM {self._TABLE} ORDER BY sport COLLATE NOCASE")
        return [row[0] for row in cur.fetchall() if row[0]]

    def distinct_ranks(self) -> list[str]:
        """Возвращает уникальные разряды в алфавитном порядке."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(f"SELECT DISTINCT rank FROM {self._TABLE} ORDER BY rank COLLATE NOCASE")
        return [row[0] for row in cur.fetchall() if row[0]]

    def search_fio_or_sport(
        self,
        fio_sub: str = "",
        sport: str = "",
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Athlete], int]:
        """Ищет записи по условию: ФИО содержит подстроку ИЛИ вид спорта равен значению."""
        fio_sub = (fio_sub or "").strip()
        sport = (sport or "").strip()
        where: list[str] = []
        params: list[object] = []
        if fio_sub:
            where.append(r"fio LIKE ? ESCAPE '\' COLLATE NOCASE")
            params.append(self._as_like_pattern(fio_sub))
        if sport:
            where.append("sport = ?")
            params.append(sport)
        if not where:
            return self.list_page(page, page_size)
        return self._select_page_with_or_filters(
            where=where,
            params=tuple(params),
            order_by="fio COLLATE NOCASE",
            page=page,
            page_size=page_size,
        )

    def search_titles_range(
        self,
        low: int,
        high: int,
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Athlete], int]:
        """Ищет записи в диапазоне титулов с сортировкой по ФИО."""
        low_i = int(low)
        high_i = int(high)
        if low_i > high_i:
            low_i, high_i = high_i, low_i
        base = f"FROM {self._TABLE} WHERE titles BETWEEN ? AND ?"
        params = (low_i, high_i)
        total = self._count(f"SELECT COUNT(*) {base}", params)
        page = max(1, int(page))
        page_size = max(1, int(page_size))
        offset = (page - 1) * page_size
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT {self._SELECT_FIELDS}
            {base}
            ORDER BY titles DESC, fio COLLATE NOCASE
            LIMIT ? OFFSET ?
            """,
            params + (page_size, offset),
        )
        return [self._row_to_athlete(row) for row in cur.fetchall()], total

    def search_fio_or_rank(
        self,
        fio_sub: str = "",
        rank: str = "",
        page: int = 1,
        page_size: int = 10,
    ) -> tuple[list[Athlete], int]:
        """Ищет записи по условию: ФИО содержит подстроку ИЛИ разряд равен значению."""
        fio_sub = (fio_sub or "").strip()
        rank = (rank or "").strip()
        where: list[str] = []
        params: list[object] = []
        if fio_sub:
            where.append(r"fio LIKE ? ESCAPE '\' COLLATE NOCASE")
            params.append(self._as_like_pattern(fio_sub))
        if rank:
            where.append("rank = ?")
            params.append(rank)
        if not where:
            return self.list_page(page, page_size)
        return self._select_page_with_or_filters(
            where=where,
            params=tuple(params),
            order_by="fio COLLATE NOCASE",
            page=page,
            page_size=page_size,
        )

    def delete_fio_or_sport(self, fio_sub: str = "", sport: str = "") -> int:
        """Удаляет записи по условию: ФИО содержит подстроку ИЛИ вид спорта равен значению."""
        fio_sub = (fio_sub or "").strip()
        sport = (sport or "").strip()
        where: list[str] = []
        params: list[object] = []
        if fio_sub:
            where.append(r"fio LIKE ? ESCAPE '\' COLLATE NOCASE")
            params.append(self._as_like_pattern(fio_sub))
        if sport:
            where.append("sport = ?")
            params.append(sport)
        if not where:
            return 0
        sql_where = self._build_or_where(where)
        conn = self._get_conn()
        with conn:
            cur = conn.cursor()
            cur.execute(f"DELETE FROM {self._TABLE} WHERE {sql_where}", tuple(params))
        return int(cur.rowcount or 0)

    def delete_titles_range(self, low: int, high: int) -> int:
        """Удаляет записи по диапазону титулов."""
        low_i = int(low)
        high_i = int(high)
        if low_i > high_i:
            low_i, high_i = high_i, low_i
        conn = self._get_conn()
        with conn:
            cur = conn.cursor()
            cur.execute(f"DELETE FROM {self._TABLE} WHERE titles BETWEEN ? AND ?", (low_i, high_i))
        return int(cur.rowcount or 0)

    def delete_fio_or_rank(self, fio_sub: str = "", rank: str = "") -> int:
        """Удаляет записи по условию: ФИО содержит подстроку ИЛИ разряд равен значению."""
        fio_sub = (fio_sub or "").strip()
        rank = (rank or "").strip()
        where: list[str] = []
        params: list[object] = []
        if fio_sub:
            where.append(r"fio LIKE ? ESCAPE '\' COLLATE NOCASE")
            params.append(self._as_like_pattern(fio_sub))
        if rank:
            where.append("rank = ?")
            params.append(rank)
        if not where:
            return 0
        sql_where = self._build_or_where(where)
        conn = self._get_conn()
        with conn:
            cur = conn.cursor()
            cur.execute(f"DELETE FROM {self._TABLE} WHERE {sql_where}", tuple(params))
        return int(cur.rowcount or 0)

    def list_all(self) -> list[Athlete]:
        """Возвращает весь набор записей для полного отображения и XML-экспорта."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT {self._SELECT_FIELDS}
            FROM {self._TABLE}
            ORDER BY fio COLLATE NOCASE
            """
        )
        return [self._row_to_athlete(row) for row in cur.fetchall()]

    def _count(self, sql: str, params: tuple[object, ...]) -> int:
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(sql, params)
        row = cur.fetchone()
        return 0 if row is None else int(row[0])

    @staticmethod
    def _as_like_pattern(value: str) -> str:
        escaped = value.replace("\\", "\\\\").replace("%", r"\%").replace("_", r"\_")
        return f"%{escaped}%"

    @staticmethod
    def _build_or_where(where: Sequence[str]) -> str:
        return " OR ".join(f"({item})" for item in where)

    def _select_page_with_or_filters(
        self,
        where: Sequence[str],
        params: tuple[object, ...],
        order_by: str,
        page: int,
        page_size: int,
    ) -> tuple[list[Athlete], int]:
        if order_by not in self._ALLOWED_ORDER_BY:
            raise ValueError("Недопустимое поле сортировки")
        base = f"FROM {self._TABLE} WHERE {self._build_or_where(where)}"
        total = self._count(f"SELECT COUNT(*) {base}", params)
        page = max(1, int(page))
        page_size = max(1, int(page_size))
        offset = (page - 1) * page_size
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            f"""
            SELECT {self._SELECT_FIELDS}
            {base}
            ORDER BY {order_by}
            LIMIT ? OFFSET ?
            """,
            params + (page_size, offset),
        )
        return [self._row_to_athlete(row) for row in cur.fetchall()], total

    @staticmethod
    def _row_to_athlete(row: sqlite3.Row) -> Athlete:
        return Athlete(
            fio=str(row["fio"]),
            squad=str(row["squad"]),
            position=str(row["position"]),
            titles=int(row["titles"]),
            sport=str(row["sport"]),
            rank=str(row["rank"]),
        )
