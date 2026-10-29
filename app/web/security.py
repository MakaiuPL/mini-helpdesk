from __future__ import annotations

from collections.abc import Callable
from functools import wraps

from flask import abort, g, redirect, session, url_for

from app.db import get_db
from app.models.enums import Role
from app.repositories.uow import UnitOfWork
from app.services import build_services


def init_request_context() -> None:
    """Przygotowuje repozytoria, serwisy i zalogowanego użytkownika."""
    g.uow = UnitOfWork(get_db())
    g.services = build_services(g.uow)

    user_id = session.get("user_id")
    g.user = g.uow.users.get_by_id(user_id) if user_id else None
    if user_id and g.user is None:
        session.clear()


def login_required[F: Callable](view: F) -> F:
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            return redirect(url_for("auth.login"))
        return view(*args, **kwargs)

    return wrapped  # type: ignore[return-value]


def role_required[F: Callable](role: Role) -> Callable[[F], F]:
    def decorator(view: F) -> F:
        @wraps(view)
        def wrapped(*args, **kwargs):
            if g.user is None:
                return redirect(url_for("auth.login"))
            if g.user.role is not role:
                abort(403)
            return view(*args, **kwargs)

        return wrapped  # type: ignore[return-value]

    return decorator
