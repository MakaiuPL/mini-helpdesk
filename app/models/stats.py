from __future__ import annotations

from dataclasses import dataclass

from app.models.enums import Priority, Status


@dataclass(frozen=True, slots=True)
class DashboardStats:
    by_status: dict[Status, int]
    by_priority: dict[Priority, int]
    total: int
    avg_close_hours: float | None
