from enum import StrEnum


class Role(StrEnum):
    USER = "user"
    TECHNICIAN = "technician"


class Priority(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Status(StrEnum):
    NEW = "new"
    IN_PROGRESS = "in_progress"
    WAITING = "waiting"
    CLOSED = "closed"


class Channel(StrEnum):
    PHONE = "phone"
    EMAIL = "email"
    REMOTE = "remote"
    FORM = "form"
