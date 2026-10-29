from __future__ import annotations

import sqlite3

from app.models.comment import Comment
from app.repositories.mappers import parse_datetime, user_from_row

_COMMENT_COLUMNS = """
    c.id, c.ticket_id, c.body, c.created_at,
    u.id AS author_id, u.username AS author_username,
    u.full_name AS author_full_name, u.role AS author_role,
    u.created_at AS author_created_at
"""

_COMMENT_FROM = """
    FROM comments c
    JOIN users u ON u.id = c.author_id
"""


def _comment_from_row(row: sqlite3.Row) -> Comment:
    created_at = parse_datetime(row["created_at"])
    if created_at is None:
        raise ValueError("Komentarz bez daty utworzenia.")
    return Comment(
        id=row["id"],
        ticket_id=row["ticket_id"],
        author=user_from_row(row, prefix="author_"),
        body=row["body"],
        created_at=created_at,
    )


class CommentRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(self, ticket_id: int, author_id: int, body: str) -> int:
        cursor = self._connection.execute(
            """
            INSERT INTO comments (ticket_id, author_id, body)
            VALUES (?, ?, ?)
            """,
            (ticket_id, author_id, body),
        )
        return int(cursor.lastrowid)

    def get_by_id(self, comment_id: int) -> Comment | None:
        row = self._connection.execute(
            f"SELECT {_COMMENT_COLUMNS} {_COMMENT_FROM} WHERE c.id = ?",
            (comment_id,),
        ).fetchone()
        return _comment_from_row(row) if row else None

    def list_for_ticket(self, ticket_id: int) -> list[Comment]:
        rows = self._connection.execute(
            f"""
            SELECT {_COMMENT_COLUMNS}
            {_COMMENT_FROM}
            WHERE c.ticket_id = ?
            ORDER BY c.created_at ASC, c.id ASC
            """,
            (ticket_id,),
        ).fetchall()
        return [_comment_from_row(row) for row in rows]
