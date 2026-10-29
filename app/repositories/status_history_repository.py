from __future__ import annotations

import sqlite3

from app.models.enums import Status
from app.models.status_change import StatusChange
from app.repositories.mappers import parse_datetime, user_from_row

_HISTORY_COLUMNS = """
    h.id, h.ticket_id, h.old_status, h.new_status, h.changed_at,
    u.id AS changed_by_id, u.username AS changed_by_username,
    u.full_name AS changed_by_full_name, u.role AS changed_by_role,
    u.created_at AS changed_by_created_at
"""

_HISTORY_FROM = """
    FROM status_history h
    JOIN users u ON u.id = h.changed_by_id
"""


def _history_from_row(row: sqlite3.Row) -> StatusChange:
    changed_at = parse_datetime(row["changed_at"])
    if changed_at is None:
        raise ValueError("Wpis historii bez daty zmiany.")
    return StatusChange(
        id=row["id"],
        ticket_id=row["ticket_id"],
        changed_by=user_from_row(row, prefix="changed_by_"),
        old_status=Status(row["old_status"]) if row["old_status"] else None,
        new_status=Status(row["new_status"]),
        changed_at=changed_at,
    )


class StatusHistoryRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(
        self,
        ticket_id: int,
        changed_by_id: int,
        old_status: Status | None,
        new_status: Status,
    ) -> None:
        self._connection.execute(
            """
            INSERT INTO status_history
                (ticket_id, changed_by_id, old_status, new_status)
            VALUES (?, ?, ?, ?)
            """,
            (
                ticket_id,
                changed_by_id,
                old_status.value if old_status else None,
                new_status.value,
            ),
        )

    def list_for_ticket(self, ticket_id: int) -> list[StatusChange]:
        rows = self._connection.execute(
            f"""
            SELECT {_HISTORY_COLUMNS}
            {_HISTORY_FROM}
            WHERE h.ticket_id = ?
            ORDER BY h.changed_at ASC, h.id ASC
            """,
            (ticket_id,),
        ).fetchall()
        return [_history_from_row(row) for row in rows]
