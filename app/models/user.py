from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

from app.models.enums import Role


@dataclass(frozen=True, slots=True)
class User:
    id: int
    username: str
    full_name: str
    role: Role
    created_at: datetime

    @property
    def is_technician(self) -> bool:
        return self.role is Role.TECHNICIAN


@dataclass(frozen=True, slots=True)
class Credentials:
    user: User
    password_hash: str = field(repr=False)
