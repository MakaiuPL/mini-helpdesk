from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.models.user import User


@dataclass(frozen=True, slots=True)
class Comment:
    id: int
    ticket_id: int
    author: User
    body: str
    created_at: datetime
