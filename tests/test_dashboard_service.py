from __future__ import annotations

import pytest

from app.errors import AuthorizationError
from app.models.enums import Priority, Status
from app.models.ticket import TicketInput


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


def test_empty_dashboard(services, marek):
    stats = services.dashboard.stats(marek)
    assert stats.total == 0
    assert all(count == 0 for count in stats.by_status.values())
    assert all(count == 0 for count in stats.by_priority.values())
    assert stats.avg_close_hours is None


def test_dashboard_counts_and_average(services, anna, marek):
    first = _ticket(services, anna, "Pierwsze")
    _ticket(services, anna, "Drugie")
    services.tickets.change_status(marek, first.id, "closed")

    stats = services.dashboard.stats(marek)
    assert stats.total == 2
    assert stats.by_status[Status.NEW] == 1
    assert stats.by_status[Status.CLOSED] == 1
    assert stats.by_priority[Priority.MEDIUM] == 2
    assert stats.avg_close_hours is not None
    assert stats.avg_close_hours >= 0


def test_user_cannot_read_dashboard(services, anna):
    with pytest.raises(AuthorizationError):
        services.dashboard.stats(anna)
