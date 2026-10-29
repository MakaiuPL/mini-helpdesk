from __future__ import annotations

from app.errors import AuthorizationError
from app.models.enums import Priority, Role, Status
from app.models.stats import DashboardStats
from app.models.user import User
from app.repositories.uow import UnitOfWork


class DashboardService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def stats(self, actor: User) -> DashboardStats:
        if actor.role is not Role.TECHNICIAN:
            raise AuthorizationError("Panel jest dostępny tylko dla technika.")

        status_counts = self._uow.tickets.count_by_status()
        priority_counts = self._uow.tickets.count_by_priority()
        return DashboardStats(
            by_status={status: status_counts.get(status, 0) for status in Status},
            by_priority={
                priority: priority_counts.get(priority, 0) for priority in Priority
            },
            total=self._uow.tickets.count_total(),
            avg_close_hours=self._uow.tickets.average_close_hours(),
        )
