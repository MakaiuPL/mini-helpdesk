from __future__ import annotations

import logging

from app.errors import AuthorizationError, NotFoundError, ValidationError
from app.models.comment import Comment
from app.models.enums import Role
from app.models.user import User
from app.repositories.uow import UnitOfWork

logger = logging.getLogger(__name__)


class CommentService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def add(self, actor: User, ticket_id: int, body: str) -> Comment:
        if actor.role is not Role.TECHNICIAN:
            raise AuthorizationError("Komentarze może dodawać tylko technik.")

        ticket = self._uow.tickets.get_by_id(ticket_id)
        if ticket is None:
            raise NotFoundError("Nie znaleziono zgłoszenia.")

        body = body.strip()
        if not 1 <= len(body) <= 2000:
            raise ValidationError({"body": "Komentarz musi mieć od 1 do 2000 znaków."})

        with self._uow.transaction():
            comment_id = self._uow.comments.add(ticket_id, actor.id, body)

        comment = self._uow.comments.get_by_id(comment_id)
        if comment is None:
            raise NotFoundError("Nie znaleziono dodanego komentarza.")
        logger.info(
            "Dodano komentarz id=%s do zgłoszenia id=%s przez user_id=%s",
            comment.id,
            ticket_id,
            actor.id,
        )
        return comment
