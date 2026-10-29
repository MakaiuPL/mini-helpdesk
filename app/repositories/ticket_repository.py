from __future__ import annotations

import sqlite3
from typing import Any

from app.models.common import Page
from app.models.enums import Channel, Priority, Status
from app.models.ticket import Ticket, TicketFilter
from app.repositories.mappers import parse_datetime, user_from_row

_TICKET_COLUMNS = """
    t.id, t.title, t.description, t.priority, t.status, t.channel,
    t.created_at, t.updated_at, t.closed_at,
    a.id AS author_id, a.username AS author_username,
    a.full_name AS author_full_name, a.role AS author_role,
    a.created_at AS author_created_at,
    s.id AS assignee_id, s.username AS assignee_username,
    s.full_name AS assignee_full_name, s.role AS assignee_role,
    s.created_at AS assignee_created_at
"""

_TICKET_FROM = """
    FROM tickets t
    JOIN users a ON a.id = t.author_id
    LEFT JOIN users s ON s.id = t.assignee_id
"""


def _escape_like(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _ticket_from_row(row: sqlite3.Row) -> Ticket:
    created_at = parse_datetime(row["created_at"])
    updated_at = parse_datetime(row["updated_at"])
    if created_at is None or updated_at is None:
        raise ValueError("Zgłoszenie bez daty utworzenia lub aktualizacji.")

    assignee = None
    if row["assignee_id"] is not None:
        assignee = user_from_row(row, prefix="assignee_")

    return Ticket(
        id=row["id"],
        title=row["title"],
        description=row["description"],
        priority=Priority(row["priority"]),
        status=Status(row["status"]),
        channel=Channel(row["channel"]),
        author=user_from_row(row, prefix="author_"),
        assignee=assignee,
        created_at=created_at,
        updated_at=updated_at,
        closed_at=parse_datetime(row["closed_at"]),
    )


class TicketRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def add(
        self,
        title: str,
        description: str,
        priority: Priority,
        channel: Channel,
        author_id: int,
    ) -> int:
        cursor = self._connection.execute(
            """
            INSERT INTO tickets
                (title, description, priority, status, channel, author_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                description,
                priority.value,
                Status.NEW.value,
                channel.value,
                author_id,
            ),
        )
        return int(cursor.lastrowid)

    def get_by_id(self, ticket_id: int) -> Ticket | None:
        row = self._connection.execute(
            f"SELECT {_TICKET_COLUMNS} {_TICKET_FROM} WHERE t.id = ?",
            (ticket_id,),
        ).fetchone()
        return _ticket_from_row(row) if row else None

    def list(
        self,
        filters: TicketFilter,
        author_id: int | None = None,
    ) -> Page[Ticket]:
        where, params = self._where(filters, author_id)
        total_row = self._connection.execute(
            f"SELECT COUNT(*) AS total FROM tickets t {where}",
            params,
        ).fetchone()
        total = int(total_row["total"]) if total_row else 0
        page = max(filters.page, 1)
        per_page = max(filters.per_page, 1)
        offset = (page - 1) * per_page
        rows = self._connection.execute(
            f"""
            SELECT {_TICKET_COLUMNS}
            {_TICKET_FROM}
            {where}
            ORDER BY t.created_at DESC, t.id DESC
            LIMIT ? OFFSET ?
            """,
            [*params, per_page, offset],
        ).fetchall()
        return Page(
            items=[_ticket_from_row(row) for row in rows],
            page=page,
            per_page=per_page,
            total=total,
        )

    def list_all(
        self,
        filters: TicketFilter,
        author_id: int | None = None,
    ) -> list[Ticket]:
        where, params = self._where(filters, author_id)
        rows = self._connection.execute(
            f"""
            SELECT {_TICKET_COLUMNS}
            {_TICKET_FROM}
            {where}
            ORDER BY t.created_at DESC, t.id DESC
            """,
            params,
        ).fetchall()
        return [_ticket_from_row(row) for row in rows]

    def update_status(self, ticket_id: int, status: Status) -> None:
        self._connection.execute(
            """
            UPDATE tickets
            SET status = ?,
                updated_at = CURRENT_TIMESTAMP,
                closed_at = CASE
                    WHEN ? = 'closed' THEN CURRENT_TIMESTAMP
                    ELSE NULL
                END
            WHERE id = ?
            """,
            (status.value, status.value, ticket_id),
        )

    def assign(self, ticket_id: int, technician_id: int) -> None:
        self._connection.execute(
            """
            UPDATE tickets
            SET assignee_id = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (technician_id, ticket_id),
        )

    def count_by_status(self) -> dict[Status, int]:
        rows = self._connection.execute(
            "SELECT status, COUNT(*) AS count FROM tickets GROUP BY status"
        ).fetchall()
        return {Status(row["status"]): int(row["count"]) for row in rows}

    def count_by_priority(self) -> dict[Priority, int]:
        rows = self._connection.execute(
            "SELECT priority, COUNT(*) AS count FROM tickets GROUP BY priority"
        ).fetchall()
        return {Priority(row["priority"]): int(row["count"]) for row in rows}

    def count_total(self) -> int:
        row = self._connection.execute(
            "SELECT COUNT(*) AS total FROM tickets"
        ).fetchone()
        return int(row["total"]) if row else 0

    def average_close_hours(self) -> float | None:
        row = self._connection.execute(
            """
            SELECT AVG((julianday(closed_at) - julianday(created_at)) * 24.0)
                   AS avg_hours
            FROM tickets
            WHERE status = 'closed' AND closed_at IS NOT NULL
            """
        ).fetchone()
        if row is None or row["avg_hours"] is None:
            return None
        return float(row["avg_hours"])

    def _where(
        self,
        filters: TicketFilter,
        author_id: int | None,
    ) -> tuple[str, list[Any]]:
        clauses: list[str] = []
        params: list[Any] = []

        if author_id is not None:
            clauses.append("t.author_id = ?")
            params.append(author_id)
        if filters.status is not None:
            clauses.append("t.status = ?")
            params.append(filters.status.value)
        if filters.priority is not None:
            clauses.append("t.priority = ?")
            params.append(filters.priority.value)
        if filters.channel is not None:
            clauses.append("t.channel = ?")
            params.append(filters.channel.value)
        if filters.query:
            pattern = f"%{_escape_like(filters.query)}%"
            clauses.append(
                "(t.title LIKE ? ESCAPE '\\' OR t.description LIKE ? ESCAPE '\\')"
            )
            params.extend([pattern, pattern])

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        return where, params
