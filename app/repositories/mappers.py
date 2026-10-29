from __future__ import annotations

from datetime import datetime
from sqlite3 import Row

from app.models.enums import Role
from app.models.user import User


def parse_datetime(value: str | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromisoformat(value)


def user_from_row(row: Row, prefix: str = "") -> User:
    created_at = parse_datetime(row[f"{prefix}created_at"])
    if created_at is None:
        raise ValueError("Użytkownik bez daty utworzenia.")
    return User(
        id=row[f"{prefix}id"],
        username=row[f"{prefix}username"],
        full_name=row[f"{prefix}full_name"],
        role=Role(row[f"{prefix}role"]),
        created_at=created_at,
    )
