# Модель салона автомобилей 

Предметная область: торговля и обслуживание автомобилей.

Важные сущности (все реализованы в системе):

- **Автомобили** (`Car`, состояние `CarState`)
- **Клиент** (`Client`)
- **Продавец** (`Seller`)
- **Выставочное пространство** (`ShowroomSpace`)
- **Тест-драйв** (`TestDrive`)
- **Документация** (`Documentation`)
- Дополнительно для полноты операций: **Продажа** (`Sale`), **Сервисный заказ** (`ServiceOrder`)

## Требования и как они выполнены

- PEP8 + аннотации типов: код написан с типами и читаемыми именами.
- Исключения: все ошибочные ситуации оформлены через исключения из `car_salon.exceptions`.
- CLI: интерфейс командной строки — `python -m car_salon ...`.
- Сохранение состояния: SQLite база (`data/car_salon.db` по умолчанию).
- Документация Markdown: этот файл + UML в `docs/uml`.
- UML 2.x: исходники PlantUML для диаграммы классов и диаграммы состояний.
- Unit-тесты: папка `tests/` (запуск через `python -m unittest -v`).

## Быстрый старт

Требования: Python 3.10+ (рекомендуется 3.11).

### Запуск CLI

```bash
# из корня проекта
python -m car_salon --help
```

База данных по умолчанию: `data/car_salon.db` (создаётся автоматически).

Можно указать свою:

```bash
python -m car_salon --db ./my.db list-cars
```

## Примеры сценариев

### 1) Регистрация сущностей

```bash
python -m car_salon add-space --name "Зал A" --capacity 10
python -m car_salon add-seller --name "Иван Петров"
python -m car_salon add-client --name "Анна Смирнова" --phone "+33-6-00-00-00-00" --email "anna@example.com"

python -m car_salon add-car --vin "VIN001" --brand "Toyota" --model "Camry" --year 2022 --price 32000
python -m car_salon receive-stock 1
python -m car_salon assign-space 1 1
```

### 2) Подготовка к продаже + документация

```bash
python -m car_salon prepare-car 1 --note "Мойка, предпродажная диагностика"
python -m car_salon add-doc 1 --content "Комплектация: Premium, 2 ключа"
python -m car_salon car-info 1
```

### 3) Тест-драйв

```bash
python -m car_salon testdrive-schedule 1 1 1 --at "2026-02-20 15:00" --notes "Маршрут: город"
python -m car_salon list-testdrives --status SCHEDULED
python -m car_salon testdrive-complete 1 --notes "Клиент доволен"
```

### 4) Продажа

```bash
python -m car_salon sell 1 1 1 --price 31500
python -m car_salon list-sales
```

### 5) Сервисное обслуживание

```bash
python -m car_salon service-open 1 --description "Замена масла" --client-id 1
python -m car_salon list-services --status OPEN
python -m car_salon service-close 1
```

## UML

Исходники диаграмм находятся в `docs/uml/*.puml`.

Чтобы получить картинки, можно использовать PlantUML:

