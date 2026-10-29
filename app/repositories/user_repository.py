from __future__ import annotations

import sqlite3

from app.models.user import Credentials, User
from app.repositories.mappers import user_from_row


class UserRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def get_by_id(self, user_id: int) -> User | None:
        row = self._connection.execute(
            """
            SELECT id, username, full_name, role, created_at
            FROM users
            WHERE id = ?
            """,
            (user_id,),
        ).fetchone()
        return user_from_row(row) if row else None

    def get_credentials(self, username: str) -> Credentials | None:
        row = self._connection.execute(
            """
            SELECT id, username, full_name, role, created_at, password_hash
            FROM users
            WHERE username = ?
            """,
            (username,),
        ).fetchone()
        if row is None:
            return None
        return Credentials(user_from_row(row), row["password_hash"])
