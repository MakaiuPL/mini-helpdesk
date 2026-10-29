from __future__ import annotations

import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db() -> sqlite3.Connection:
    """Zwraca połączenie SQLite przypisane do bieżącego requestu."""
    if "db" not in g:
        database = current_app.config["DATABASE"]
        if database != ":memory:":
            Path(database).parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(database)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        if database != ":memory:":
            connection.execute("PRAGMA journal_mode = WAL")
        g.db = connection
    return g.db


def close_db(exception: BaseException | None = None) -> None:
    """Zamyka połączenie po zakończeniu requestu."""
    connection = g.pop("db", None)
    if connection is not None:
        connection.close()


def init_db() -> bool:
    """Tworzy bazę ze schema.sql, jeśli jeszcze nie istnieje."""
    connection = get_db()
    exists = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'users'"
    ).fetchone()
    if exists:
        return False

    schema_path = Path(current_app.root_path).parent / "schema.sql"
    connection.executescript(schema_path.read_text(encoding="utf-8"))
    connection.commit()
    return True
