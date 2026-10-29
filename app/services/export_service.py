from __future__ import annotations

import csv
import io
import logging

from app.errors import AuthorizationError
from app.labels import channel_label, priority_label, status_label
from app.models.enums import Role
from app.models.ticket import Ticket, TicketFilter
from app.models.user import User
from app.repositories.uow import UnitOfWork

logger = logging.getLogger(__name__)

_HEADER = (
    "ID",
    "Tytuł",
    "Priorytet",
    "Status",
    "Kanał",
    "Autor",
    "Technik",
    "Utworzono",
    "Zamknięto",
)


def _csv_safe(value: object) -> str:
    text = "" if value is None else str(value)
    if text.startswith(("=", "+", "-", "@")):
        return f"'{text}"
    return text


def _row(ticket: Ticket) -> tuple[str, ...]:
    return (
        str(ticket.id),
        _csv_safe(ticket.title),
        priority_label(ticket.priority),
        status_label(ticket.status),
        channel_label(ticket.channel),
        _csv_safe(ticket.author.full_name),
        _csv_safe(ticket.assignee.full_name if ticket.assignee else ""),
        ticket.created_at.strftime("%Y-%m-%d %H:%M"),
        ticket.closed_at.strftime("%Y-%m-%d %H:%M") if ticket.closed_at else "",
    )


class ExportService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def export_csv(self, actor: User, filters: TicketFilter) -> str:
        if actor.role is not Role.TECHNICIAN:
            raise AuthorizationError("Eksport jest dostępny tylko dla technika.")

        tickets = self._uow.tickets.list_all(filters)
        output = io.StringIO()
        output.write("\ufeff")
        writer = csv.writer(output, delimiter=";", lineterminator="\r\n")
        writer.writerow(_HEADER)
        writer.writerows(_row(ticket) for ticket in tickets)
        logger.info(
            "Wyeksportowano %s zgłoszeń do CSV przez user_id=%s",
            len(tickets),
            actor.id,
        )
        return output.getvalue()
