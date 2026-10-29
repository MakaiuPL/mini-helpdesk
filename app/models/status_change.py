from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.models.enums import Status
from app.models.user import User


@dataclass(frozen=True, slots=True)
class StatusChange:
    id: int
    ticket_id: int
    changed_by: User
    old_status: Status | None
    new_status: Status
    changed_at: datetime
