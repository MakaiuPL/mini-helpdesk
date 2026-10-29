from __future__ import annotations

import pytest

from app.errors import AuthorizationError, ConflictError, NotFoundError, ValidationError
from app.models.enums import Status
from app.models.ticket import TicketFilter, TicketInput
from app.services.ticket_service import allowed_transitions


def _input(
    title="Problem z kontem", description="Opis problemu jest wystarczająco długi."
):
    return TicketInput(
        title=title,
        description=description,
        priority="high",
        channel="form",
    )


def test_create_ticket_starts_as_new_and_records_history(services, anna):
    ticket = services.tickets.create(anna, _input())

    assert ticket.status is Status.NEW
    assert ticket.author.id == anna.id
    details = services.tickets.get_details(anna, ticket.id)
    assert len(details.history) == 1
    assert details.history[0].old_status is None
    assert details.history[0].new_status is Status.NEW


@pytest.mark.parametrize(
    "data",
    [
        TicketInput("ab", "Opis problemu jest wystarczająco długi.", "low", "form"),
        TicketInput("Poprawny tytuł", "krótki", "low", "form"),
        TicketInput(
            "Poprawny tytuł", "Opis problemu jest wystarczająco długi.", "pilny", "form"
        ),
        TicketInput(
            "Poprawny tytuł", "Opis problemu jest wystarczająco długi.", "low", "sms"
        ),
    ],
)
def test_create_ticket_validates_input(services, anna, data):
    with pytest.raises(ValidationError):
        services.tickets.create(anna, data)


def test_technician_cannot_create_ticket(services, marek):
    with pytest.raises(AuthorizationError):
        services.tickets.create(marek, _input())


def test_user_cannot_read_foreign_ticket(services, anna, piotr):
    ticket = services.tickets.create(piotr, _input())
    with pytest.raises(NotFoundError):
        services.tickets.get_details(anna, ticket.id)


def test_user_list_is_limited_to_own_tickets(services, anna, piotr):
    services.tickets.create(anna, _input("Zgłoszenie Anny"))
    services.tickets.create(piotr, _input("Zgłoszenie Piotra"))

    page = services.tickets.list(anna, TicketFilter())
    assert page.total == 1
    assert page.items[0].title == "Zgłoszenie Anny"


def test_status_change_records_history_and_closes_ticket(services, anna, marek):
    ticket = services.tickets.create(anna, _input())

    in_progress = services.tickets.change_status(marek, ticket.id, "in_progress")
    assert in_progress.status is Status.IN_PROGRESS

    closed = services.tickets.change_status(marek, ticket.id, "closed")
    assert closed.status is Status.CLOSED
    assert closed.closed_at is not None

    details = services.tickets.get_details(marek, ticket.id)
    assert len(details.history) == 3
    assert details.history[-1].new_status is Status.CLOSED


def test_reopening_ticket_clears_closed_at(services, anna, marek):
    ticket = services.tickets.create(anna, _input())
    services.tickets.change_status(marek, ticket.id, "closed")

    reopened = services.tickets.change_status(marek, ticket.id, "in_progress")
    assert reopened.closed_at is None


def test_invalid_status_transition_is_rejected(services, anna, marek):
    ticket = services.tickets.create(anna, _input())
    with pytest.raises(ConflictError):
        services.tickets.change_status(marek, ticket.id, "waiting")


def test_same_status_is_rejected(services, anna, marek):
    ticket = services.tickets.create(anna, _input())
    with pytest.raises(ConflictError):
        services.tickets.change_status(marek, ticket.id, "new")


def test_assign_to_self_and_takeover(services, anna, marek, ewa):
    ticket = services.tickets.create(anna, _input())

    assigned = services.tickets.assign_to_self(marek, ticket.id)
    assert assigned.assignee is not None
    assert assigned.assignee.id == marek.id

    with pytest.raises(ConflictError):
        services.tickets.assign_to_self(marek, ticket.id)

    taken_over = services.tickets.assign_to_self(ewa, ticket.id)
    assert taken_over.assignee is not None
    assert taken_over.assignee.id == ewa.id


def test_user_cannot_change_status_or_assign(services, anna):
    ticket = services.tickets.create(anna, _input())
    with pytest.raises(AuthorizationError):
        services.tickets.change_status(anna, ticket.id, "in_progress")
    with pytest.raises(AuthorizationError):
        services.tickets.assign_to_self(anna, ticket.id)


def test_allowed_transitions_are_ordered():
    assert allowed_transitions(Status.NEW) == [Status.IN_PROGRESS, Status.CLOSED]
    assert allowed_transitions(Status.CLOSED) == [Status.IN_PROGRESS]
