from __future__ import annotations

from werkzeug.security import check_password_hash

from app.errors import AuthenticationError, ValidationError
from app.models.user import User
from app.repositories.uow import UnitOfWork


class AuthService:
    def __init__(self, uow: UnitOfWork) -> None:
        self._uow = uow

    def authenticate(self, username: str, password: str) -> User:
        username = (username or "").strip()
        password = password or ""
        if not username or not password:
            raise ValidationError("Podaj nazwę użytkownika i hasło.")

        credentials = self._uow.users.get_credentials(username)
        if credentials is None or not check_password_hash(
            credentials.password_hash, password
        ):
            raise AuthenticationError("Nieprawidłowa nazwa użytkownika lub hasło.")
        return credentials.user
