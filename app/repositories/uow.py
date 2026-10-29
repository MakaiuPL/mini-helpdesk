from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from app.repositories.comment_repository import CommentRepository
from app.repositories.status_history_repository import StatusHistoryRepository
from app.repositories.ticket_repository import TicketRepository
from app.repositories.user_repository import UserRepository


class UnitOfWork:
    """Wspólne połączenie i transakcje dla zestawu repozytoriów."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        self.connection = connection
        self.users = UserRepository(connection)
        self.tickets = TicketRepository(connection)
        self.comments = CommentRepository(connection)
        self.history = StatusHistoryRepository(connection)

    @contextmanager
    def transaction(self) -> Iterator[UnitOfWork]:
        try:
            yield self
            self.connection.commit()
        except Exception:
            self.connection.rollback()
            raise
