from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from app.models.comment import Comment
from app.models.enums import Channel, Priority, Status
from app.models.status_change import StatusChange
from app.models.user import User


@dataclass(frozen=True, slots=True)
class Ticket:
    id: int
    title: str
    description: str
    priority: Priority
    status: Status
    channel: Channel
    author: User
    assignee: User | None
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None

    @property
    def is_closed(self) -> bool:
        return self.status is Status.CLOSED

    def is_authored_by(self, user: User) -> bool:
        return self.author.id == user.id

    def is_assigned_to(self, user: User) -> bool:
        return self.assignee is not None and self.assignee.id == user.id


@dataclass(frozen=True, slots=True)
class TicketInput:
    title: str
    description: str
    priority: str
    channel: str


@dataclass(frozen=True, slots=True)
class TicketFilter:
    status: Status | None = None
    priority: Priority | None = None
    channel: Channel | None = None
    query: str = ""
    page: int = 1
    per_page: int = 10


@dataclass(frozen=True, slots=True)
class TicketDetails:
    ticket: Ticket
    comments: list[Comment]
    history: list[StatusChange]
