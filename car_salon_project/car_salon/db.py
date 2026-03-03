"""SQLite persistence layer.

The application stores its state in a single SQLite file.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path


SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS showroom_spaces (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT NOT NULL UNIQUE,
  capacity INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS cars (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  vin TEXT NOT NULL UNIQUE,
  brand TEXT NOT NULL,
  model TEXT NOT NULL,
  year INTEGER NOT NULL,
  price REAL NOT NULL,
  state TEXT NOT NULL,
  space_id INTEGER,
  FOREIGN KEY(space_id) REFERENCES showroom_spaces(id)
);

CREATE TABLE IF NOT EXISTS clients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name TEXT NOT NULL,
  phone TEXT NOT NULL,
  email TEXT
);

CREATE TABLE IF NOT EXISTS sellers (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  full_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS documentation (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  car_id INTEGER NOT NULL,
  content TEXT NOT NULL,
  created_at TEXT NOT NULL,
  FOREIGN KEY(car_id) REFERENCES cars(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS test_drives (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  car_id INTEGER NOT NULL,
  client_id INTEGER NOT NULL,
  seller_id INTEGER NOT NULL,
  scheduled_at TEXT NOT NULL,
  status TEXT NOT NULL,
  notes TEXT,
  FOREIGN KEY(car_id) REFERENCES cars(id),
  FOREIGN KEY(client_id) REFERENCES clients(id),
  FOREIGN KEY(seller_id) REFERENCES sellers(id)
);

CREATE TABLE IF NOT EXISTS sales (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  car_id INTEGER NOT NULL,
  client_id INTEGER NOT NULL,
  seller_id INTEGER NOT NULL,
  sold_at TEXT NOT NULL,
  price REAL NOT NULL,
  FOREIGN KEY(car_id) REFERENCES cars(id),
  FOREIGN KEY(client_id) REFERENCES clients(id),
  FOREIGN KEY(seller_id) REFERENCES sellers(id)
);

CREATE TABLE IF NOT EXISTS service_orders (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  car_id INTEGER NOT NULL,
  client_id INTEGER,
  opened_at TEXT NOT NULL,
  closed_at TEXT,
  description TEXT NOT NULL,
  status TEXT NOT NULL,
  FOREIGN KEY(car_id) REFERENCES cars(id),
  FOREIGN KEY(client_id) REFERENCES clients(id)
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    """Create a connection and ensure schema exists."""

    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    return conn

