from __future__ import annotations

from app.models.enums import Channel, Priority, Status
from app.models.ticket import TicketFilter


def _add_ticket(
    uow,
    title="Problem z kontem",
    priority=Priority.MEDIUM,
    channel=Channel.FORM,
    author_id=1,
):
    return uow.tickets.add(
        title=title,
        description="Szczegółowy opis problemu zgłoszonego przez użytkownika.",
        priority=priority,
        channel=channel,
        author_id=author_id,
    )


def test_ticket_roundtrip_maps_enums_and_author(uow):
    ticket_id = _add_ticket(uow, priority=Priority.HIGH, channel=Channel.EMAIL)
    ticket = uow.tickets.get_by_id(ticket_id)
    assert ticket is not None
    assert ticket.priority is Priority.HIGH
    assert ticket.channel is Channel.EMAIL
    assert ticket.status is Status.NEW
    assert ticket.author.id == 1
    assert ticket.assignee is None


def test_filters_are_combined(uow):
    first = _add_ticket(
        uow, title="Awaria drukarki", priority=Priority.HIGH, channel=Channel.PHONE
    )
    _add_ticket(
        uow, title="Problem z pocztą", priority=Priority.LOW, channel=Channel.EMAIL
    )
    uow.tickets.update_status(first, Status.IN_PROGRESS)

    result = uow.tickets.list(
        TicketFilter(status=Status.IN_PROGRESS, priority=Priority.HIGH)
    )
    assert result.total == 1
    assert result.items[0].title == "Awaria drukarki"


def test_search_escapes_like_wildcards(uow):
    _add_ticket(uow, title="Błąd 100% na dysku")
    _add_ticket(uow, title="Błąd 1000 na dysku")

    result = uow.tickets.list(TicketFilter(query="100%"))
    assert result.total == 1
    assert "100%" in result.items[0].title


def test_pagination_returns_requested_page(uow):
    for index in range(5):
        _add_ticket(uow, title=f"Problem numer {index}")

    first = uow.tickets.list(TicketFilter(page=1, per_page=2))
    last = uow.tickets.list(TicketFilter(page=3, per_page=2))
    assert first.total == 5
    assert first.pages == 3
    assert len(first.items) == 2
    assert len(last.items) == 1


def test_pagination_is_defensive_for_invalid_values(uow):
    _add_ticket(uow, title="Problem numer 0")

    result = uow.tickets.list(TicketFilter(page=0, per_page=0))
    assert result.page == 1
    assert result.per_page == 1
    assert len(result.items) == 1


def test_user_scope_limits_results(uow):
    _add_ticket(uow, title="Zgłoszenie Anny", author_id=1)
    _add_ticket(uow, title="Zgłoszenie Piotra", author_id=2)

    result = uow.tickets.list(TicketFilter(), author_id=1)
    assert result.total == 1
    assert result.items[0].title == "Zgłoszenie Anny"


def test_comments_are_returned_chronologically(uow):
    ticket_id = _add_ticket(uow)
    uow.comments.add(ticket_id, 3, "Pierwszy komentarz")
    uow.comments.add(ticket_id, 4, "Drugi komentarz")

    comments = uow.comments.list_for_ticket(ticket_id)
    assert [comment.body for comment in comments] == [
        "Pierwszy komentarz",
        "Drugi komentarz",
    ]


def test_status_update_sets_and_clears_closed_at(uow):
    ticket_id = _add_ticket(uow)
    uow.tickets.update_status(ticket_id, Status.CLOSED)
    closed = uow.tickets.get_by_id(ticket_id)
    assert closed is not None
    assert closed.closed_at is not None

    uow.tickets.update_status(ticket_id, Status.IN_PROGRESS)
    reopened = uow.tickets.get_by_id(ticket_id)
    assert reopened is not None
    assert reopened.closed_at is None
