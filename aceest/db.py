"""SQLite storage. Each request opens a short-lived connection."""
import sqlite3
from contextlib import contextmanager

from flask import current_app

SCHEMA = """
CREATE TABLE IF NOT EXISTS clients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    age INTEGER NOT NULL,
    height_cm REAL NOT NULL,
    weight_kg REAL NOT NULL,
    program TEXT NOT NULL,
    calories INTEGER NOT NULL,
    membership_end TEXT
);
CREATE TABLE IF NOT EXISTS progress (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    week TEXT NOT NULL,
    adherence INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS workouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    client_id INTEGER NOT NULL REFERENCES clients(id),
    date TEXT NOT NULL,
    workout_type TEXT NOT NULL,
    duration_min INTEGER NOT NULL,
    notes TEXT
);
"""


@contextmanager
def connect():
    conn = sqlite3.connect(current_app.config["DATABASE"])
    conn.row_factory = sqlite3.Row
    try:
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()
