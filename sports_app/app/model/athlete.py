"""Доменная модель спортсмена и допустимые справочники значений."""

from __future__ import annotations

from dataclasses import dataclass


SQUAD_VALUES = ("основной", "запасной", "n/a")
RANK_VALUES = (
    "1-й юношеский",
    "2-й разряд",
    "3-й разряд",
    "кмс",
    "мастер спорта",
)


@dataclass(frozen=True)
class Athlete:
    """Иммутабельная запись спортсмена с методами нормализации и валидации."""

    fio: str
    squad: str
    position: str
    titles: int
    sport: str
    rank: str

    def normalized(self) -> "Athlete":
        """Возвращает нормализованную валидную копию с очищенными строками."""
        fio = (self.fio or "").strip()
        position = (self.position or "").strip()
        sport = (self.sport or "").strip()
        squad = (self.squad or "").strip() or "n/a"
        rank = (self.rank or "").strip()

        if not fio:
            raise ValueError("ФИО спортсмена обязательно")
        if not sport:
            raise ValueError("Вид спорта обязателен")
        if not rank:
            raise ValueError("Разряд обязателен")
        if squad not in SQUAD_VALUES:
            raise ValueError(f"Состав должен быть одним из: {', '.join(SQUAD_VALUES)}")

        try:
            titles = int(self.titles)
        except (TypeError, ValueError) as exc:
            raise ValueError("Титулы должны быть целым числом") from exc
        if titles < 0:
            raise ValueError("Титулы не могут быть отрицательными")

        return Athlete(
            fio=fio,
            squad=squad,
            position=position,
            titles=titles,
            sport=sport,
            rank=rank,
        )
