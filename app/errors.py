from __future__ import annotations


class AppError(Exception):
    """Bazowy wyjątek domenowy."""


class ValidationError(AppError):
    """Niepoprawne dane wejściowe."""

    def __init__(self, errors: dict[str, str] | str) -> None:
        if isinstance(errors, str):
            errors = {"_": errors}
        self.errors = errors
        super().__init__("; ".join(errors.values()))

    @property
    def message(self) -> str:
        return next(iter(self.errors.values()), "Nieprawidłowe dane.")


class AuthenticationError(AppError):
    """Nieudane uwierzytelnienie."""


class AuthorizationError(AppError):
    """Brak uprawnień do wykonania operacji."""


class NotFoundError(AppError):
    """Rekord nie istnieje lub nie jest widoczny dla użytkownika."""


class ConflictError(AppError):
    """Operacja jest sprzeczna z aktualnym stanem danych."""
