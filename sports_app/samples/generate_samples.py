"""Генератор демонстрационных XML-файлов со спортсменами."""

from __future__ import annotations

import random
from pathlib import Path

from ..app.model.athlete import Athlete, RANK_VALUES, SQUAD_VALUES
from ..app.model.xml_io import save_athletes_dom_xml


FIRST = [
    "Иван", "Алексей", "Дмитрий", "Никита", "Максим", "Егор", "Андрей", "Сергей", "Павел", "Михаил",
    "Анна", "Мария", "Екатерина", "Ольга", "Дарья", "Полина", "Ксения", "Алина", "Виктория", "Елена",
]
LAST = [
    "Иванов", "Петров", "Сидоров", "Кузнецов", "Смирнов", "Попов", "Волков", "Соколов", "Лебедев", "Козлов",
    "Новикова", "Морозова", "Фёдорова", "Михайлова", "Павлова", "Семёнова", "Андреева", "Романова", "Макарова", "Зайцева",
]
PATR = [
    "Алексеевич", "Иванович", "Сергеевич", "Павлович", "Дмитриевич", "Андреевич",
    "Алексеевна", "Ивановна", "Сергеевна", "Павловна", "Дмитриевна", "Андреевна",
]

SPORT_POS = {
    "Футбол": ["вратарь", "защитник", "полузащитник", "нападающий"],
    "Баскетбол": ["разыгрывающий", "атакующий защитник", "лёгкий форвард", "тяжёлый форвард", "центровой"],
    "Хоккей": ["вратарь", "защитник", "нападающий"],
    "Теннис": ["одиночка", "пары"],
    "Плавание": ["вольный стиль", "баттерфляй", "на спине", "брасс", "комплекс"],
    "Бокс": ["лёгкий вес", "средний вес", "тяжёлый вес"],
    "Дзюдо": ["лёгкий вес", "средний вес", "тяжёлый вес"],
    "Волейбол": ["связующий", "доигровщик", "диагональный", "центральный", "либеро"],
    "Лёгкая атлетика": ["спринт", "средние дистанции", "прыжки", "метание"],
    "Гимнастика": ["спортивная", "художественная"],
    "Шахматы": ["классика", "рапид", "блиц"],
    "Биатлон": ["спринт", "преследование", "индивидуальная гонка", "эстафета"],
}


def make_name() -> str:
    """Генерирует псевдореалистичное ФИО."""
    return f"{random.choice(LAST)} {random.choice(FIRST)} {random.choice(PATR)}"


def generate(n: int, seed: int) -> list[Athlete]:
    """Генерирует `n` валидированных записей спортсменов."""
    random.seed(seed)
    sports = list(SPORT_POS.keys())

    res: list[Athlete] = []
    for _ in range(1, n + 1):
        sport = random.choice(sports)
        pos = random.choice(SPORT_POS[sport])
        a = Athlete(
            fio=make_name(),
            squad=random.choice(SQUAD_VALUES),
            position=pos,
            titles=random.randint(0, 25),
            sport=sport,
            rank=random.choice(RANK_VALUES),
        ).normalized()
        res.append(a)
    return res


def main() -> None:
    """Создаёт и сохраняет два XML-файла с тестовыми данными."""
    out_dir = Path(__file__).resolve().parent
    a = generate(55, seed=7)
    b = generate(60, seed=17)
    save_athletes_dom_xml(str(out_dir / "athletes_50_a.xml"), a)
    save_athletes_dom_xml(str(out_dir / "athletes_50_b.xml"), b)
    print("Generated:", out_dir / "athletes_50_a.xml", out_dir / "athletes_50_b.xml")


if __name__ == "__main__":
    main()
