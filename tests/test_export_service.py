from __future__ import annotations

import pytest

from app.errors import AuthorizationError
from app.models.enums import Status
from app.models.ticket import TicketFilter, TicketInput


def _ticket(services, anna, title="Problem"):
    return services.tickets.create(
        anna,
        TicketInput(
            title=title,
            description="Opis problemu jest wystarczająco długi.",
            priority="medium",
            channel="form",
        ),
    )


def test_empty_export_contains_header(services, marek):
    content = services.export.export_csv(marek, TicketFilter())
    assert content.startswith("\ufeffID;Tytuł;Priorytet;Status;Kanał;Autor;Technik")
    assert len(content.splitlines()) == 1


def test_export_respects_filters(services, anna, marek):
    _ticket(services, anna, "Zgłoszenie nowe")
    closed = _ticket(services, anna, "Zgłoszenie zamknięte")
    services.tickets.change_status(marek, closed.id, "closed")

    content = services.export.export_csv(
        marek,
        TicketFilter(status=Status.NEW),
    )
    assert "Zgłoszenie nowe" in content
    assert "Zgłoszenie zamknięte" not in content


def test_export_escapes_spreadsheet_formulas(services, anna, marek):
    _ticket(services, anna, "=SUM(A1)")
    content = services.export.export_csv(marek, TicketFilter())
    assert "'=SUM(A1)" in content


def test_user_cannot_export(services, anna):
    with pytest.raises(AuthorizationError):
        services.export.export_csv(anna, TicketFilter())
