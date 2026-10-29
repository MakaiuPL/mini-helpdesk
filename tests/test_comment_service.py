from __future__ import annotations

import pytest

from app.errors import AuthorizationError, NotFoundError, ValidationError
from app.models.ticket import TicketInput


def _ticket(services, anna, title="Problem z kontem"):
    return services.tickets.create(
        anna,
        TicketInput(
            title=title,
            description="Opis problemu jest wystarczająco długi.",
            priority="medium",
            channel="form",
        ),
    )


def test_technician_can_add_comment(services, anna, marek):
    ticket = _ticket(services, anna)
    comment = services.comments.add(marek, ticket.id, "Sprawdzam logi systemowe.")

    assert comment.body == "Sprawdzam logi systemowe."
    assert comment.author.id == marek.id
    details = services.tickets.get_details(marek, ticket.id)
    assert len(details.comments) == 1


def test_user_cannot_add_comment(services, anna):
    ticket = _ticket(services, anna)
    with pytest.raises(AuthorizationError):
        services.comments.add(anna, ticket.id, "Komentarz użytkownika")


def test_empty_comment_is_rejected(services, anna, marek):
    ticket = _ticket(services, anna)
    with pytest.raises(ValidationError):
        services.comments.add(marek, ticket.id, "   ")


def test_comment_to_missing_ticket_is_rejected(services, marek):
    with pytest.raises(NotFoundError):
        services.comments.add(marek, 9999, "Treść komentarza")
