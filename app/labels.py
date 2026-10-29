from __future__ import annotations

from datetime import datetime

from app.models.enums import Channel, Priority, Role, Status

STATUS_LABELS: dict[Status, str] = {
    Status.NEW: "nowe",
    Status.IN_PROGRESS: "w toku",
    Status.WAITING: "oczekuje",
    Status.CLOSED: "zamknięte",
}

PRIORITY_LABELS: dict[Priority, str] = {
    Priority.LOW: "niski",
    Priority.MEDIUM: "średni",
    Priority.HIGH: "wysoki",
    Priority.CRITICAL: "krytyczny",
}

CHANNEL_LABELS: dict[Channel, str] = {
    Channel.PHONE: "telefon",
    Channel.EMAIL: "e-mail",
    Channel.REMOTE: "zdalny pulpit",
    Channel.FORM: "formularz",
}

ROLE_LABELS: dict[Role, str] = {
    Role.USER: "użytkownik",
    Role.TECHNICIAN: "technik",
}


def _label(mapping: dict, value: object) -> str:
    return mapping.get(value, str(value))


def status_label(value: object) -> str:
    return _label(STATUS_LABELS, value)


def priority_label(value: object) -> str:
    return _label(PRIORITY_LABELS, value)


def channel_label(value: object) -> str:
    return _label(CHANNEL_LABELS, value)


def role_label(value: object) -> str:
    return _label(ROLE_LABELS, value)


def format_datetime(value: datetime | None) -> str:
    if value is None:
        return "—"
    return value.strftime("%Y-%m-%d %H:%M")


def format_hours(value: float | None) -> str:
    if value is None:
        return "brak danych"
    return f"{value:.1f} h".replace(".", ",")
