from __future__ import annotations

import logging

from app.errors import (
    AuthorizationError,
    ConflictError,
    NotFoundError,
    ValidationError,
)
from app.labels import status_label
from app.models.common import Page
from app.models.enums import Channel, Priority, Role, Status
from app.models.ticket import Ticket, TicketDetails, TicketFilter, TicketInput
from app.models.user import User
from app.repositories.uow import UnitOfWork

logger = logging.getLogger(__name__)

ALLOWED_TRANSITIONS: dict[Status, frozenset[Status]] = {
    Status.NEW: frozenset({Status.IN_PROGRESS, Status.CLOSED}),
    Status.IN_PROGRESS: frozenset({Status.WAITING, Status.CLOSED}),
    Status.WAITING: frozenset({Status.IN_PROGRESS, Status.CLOSED}),
    Status.CLOSED: frozenset({Status.IN_PROGRESS}),
}

_STATUS_ORDER = (Status.NEW, Status.IN_PROGRESS, Status.WAITING, Status.CLOSED)


def allowed_transitions(current: Status) -> list[Status]:
    """Zwraca dozwolone statusy docelowe w kolejności prezentacji."""
    allowed = ALLOWED_TRANSITIONS.get(current, frozenset())
    return [status for status in _STATUS_ORDER if status in allowed]


def _require_technician(actor: User) -> None:
    if actor.role is not Role.TECHNICIAN:
        raise AuthorizationError("Ta operacja jest dostępna tylko dla technika.")


def _parse_priority(value: str) -> Priority:
    try:
        return Priority(value)
    except ValueError as error:
        raise ValidationError({"priority": "Wybierz poprawny priorytet."}) from error


def _parse_channel(value: str) -> Channel:
    try:
        return Channel(value)
    except ValueError as error:
        raise ValidationError({"channel": "Wybierz poprawny kanał."}) from error


def _parse_status(value: str) -> Status:
    try:
        return Status(value)
    except ValueError as error:
        raise ValidationError({"status": "Wybierz poprawny status."}) from error


class TicketService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def create(self, actor: User, data: TicketInput) -> Ticket:
        if actor.role is not Role.USER:
            raise AuthorizationError("Zgłoszenia może tworzyć tylko użytkownik.")

        title = data.title.strip()
        description = data.description.strip()
        errors: dict[str, str] = {}

        if not 3 <= len(title) <= 120:
            errors["title"] = "Tytuł musi mieć od 3 do 120 znaków."
        if not 10 <= len(description) <= 5000:
            errors["description"] = "Opis musi mieć od 10 do 5000 znaków."

        priority = None
        channel = None
        try:
            priority = _parse_priority(data.priority)
        except ValidationError as error:
            errors.update(error.errors)
        try:
            channel = _parse_channel(data.channel)
        except ValidationError as error:
            errors.update(error.errors)

        if errors:
            raise ValidationError(errors)

        assert priority is not None and channel is not None
        with self._uow.transaction():
            ticket_id = self._uow.tickets.add(
                title=title,
                description=description,
                priority=priority,
                channel=channel,
                author_id=actor.id,
            )
            self._uow.history.add(
                ticket_id=ticket_id,
                changed_by_id=actor.id,
                old_status=None,
                new_status=Status.NEW,
            )

        ticket = self._uow.tickets.get_by_id(ticket_id)
        if ticket is None:
            raise NotFoundError("Nie znaleziono utworzonego zgłoszenia.")
        logger.info(
            "Utworzono zgłoszenie id=%s przez user_id=%s",
            ticket.id,
            actor.id,
        )
        return ticket

    def list(self, actor: User, filters: TicketFilter) -> Page[Ticket]:
        author_id = actor.id if actor.role is Role.USER else None
        return self._uow.tickets.list(filters, author_id=author_id)

    def get_details(self, actor: User, ticket_id: int) -> TicketDetails:
        ticket = self._uow.tickets.get_by_id(ticket_id)
        if ticket is None:
            raise NotFoundError("Nie znaleziono zgłoszenia.")
        if actor.role is Role.USER and not ticket.is_authored_by(actor):
            raise NotFoundError("Nie znaleziono zgłoszenia.")

        return TicketDetails(
            ticket=ticket,
            comments=self._uow.comments.list_for_ticket(ticket_id),
            history=self._uow.history.list_for_ticket(ticket_id),
        )

    def change_status(
        self,
        actor: User,
        ticket_id: int,
        new_status: str,
    ) -> Ticket:
        _require_technician(actor)
        target = _parse_status(new_status)
        ticket = self._uow.tickets.get_by_id(ticket_id)
        if ticket is None:
            raise NotFoundError("Nie znaleziono zgłoszenia.")
        if ticket.status is target:
            raise ConflictError("Zgłoszenie ma już wybrany status.")
        if target not in ALLOWED_TRANSITIONS[ticket.status]:
            raise ConflictError(
                "Nie można zmienić statusu z "
                f"„{status_label(ticket.status)}” na „{status_label(target)}”."
            )

        with self._uow.transaction():
            self._uow.tickets.update_status(ticket_id, target)
            self._uow.history.add(
                ticket_id=ticket_id,
                changed_by_id=actor.id,
                old_status=ticket.status,
                new_status=target,
            )

        updated = self._uow.tickets.get_by_id(ticket_id)
        if updated is None:
            raise NotFoundError("Nie znaleziono zgłoszenia.")
        logger.info(
            "Zmieniono status zgłoszenia id=%s z %s na %s przez user_id=%s",
            ticket_id,
            ticket.status.value,
            target.value,
            actor.id,
        )
        return updated

    def assign_to_self(self, actor: User, ticket_id: int) -> Ticket:
        _require_technician(actor)
        ticket = self._uow.tickets.get_by_id(ticket_id)
        if ticket is None:
            raise NotFoundError("Nie znaleziono zgłoszenia.")
        if ticket.is_assigned_to(actor):
            raise ConflictError("Zgłoszenie jest już przypisane do Ciebie.")

        with self._uow.transaction():
            self._uow.tickets.assign(ticket_id, actor.id)

        updated = self._uow.tickets.get_by_id(ticket_id)
        if updated is None:
            raise NotFoundError("Nie znaleziono zgłoszenia.")
        logger.info(
            "Przypisano zgłoszenie id=%s do user_id=%s",
            ticket_id,
            actor.id,
        )
        return updated
