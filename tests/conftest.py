from __future__ import annotations

import re
import sqlite3
from pathlib import Path

import pytest

from app import create_app
from app.db import init_db
from app.repositories.uow import UnitOfWork
from app.services import build_services

ROOT = Path(__file__).resolve().parent.parent
SCHEMA = (ROOT / "schema.sql").read_text(encoding="utf-8")


@pytest.fixture
def connection():
    database = sqlite3.connect(":memory:")
    database.row_factory = sqlite3.Row
    database.execute("PRAGMA foreign_keys = ON")
    database.executescript(SCHEMA)
    database.execute("DELETE FROM status_history")
    database.execute("DELETE FROM comments")
    database.execute("DELETE FROM tickets")
    database.commit()
    yield database
    database.close()


@pytest.fixture
def uow(connection):
    return UnitOfWork(connection)


@pytest.fixture
def services(uow):
    return build_services(uow)


@pytest.fixture
def anna(uow):
    return uow.users.get_by_id(1)


@pytest.fixture
def piotr(uow):
    return uow.users.get_by_id(2)


@pytest.fixture
def marek(uow):
    return uow.users.get_by_id(3)


@pytest.fixture
def ewa(uow):
    return uow.users.get_by_id(4)


@pytest.fixture
def app(tmp_path):
    database = tmp_path / "test.db"
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "DATABASE": str(database),
            "WTF_CSRF_ENABLED": True,
            "LOG_LEVEL": "WARNING",
        }
    )
    with application.app_context():
        init_db()
    yield application


@pytest.fixture
def client(app):
    return app.test_client()


def extract_csrf(html: str) -> str:
    match = re.search(r'name="csrf_token"[^>]*value="([^"]+)"', html)
    assert match is not None, "Brak tokenu CSRF w odpowiedzi."
    return match.group(1)


@pytest.fixture
def csrf_token(client):
    def _token(path: str = "/login") -> str:
        response = client.get(path)
        assert response.status_code == 200
        return extract_csrf(response.get_data(as_text=True))

    return _token


@pytest.fixture
def login(client, csrf_token):
    def _login(username: str = "anna", password: str = "anna1234"):
        token = csrf_token("/login")
        return client.post(
            "/login",
            data={
                "username": username,
                "password": password,
                "csrf_token": token,
            },
            follow_redirects=True,
        )

    return _login
