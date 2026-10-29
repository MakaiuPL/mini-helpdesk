from __future__ import annotations

import pytest

from app.errors import AuthenticationError, ValidationError


def test_login_success(services):
    user = services.auth.authenticate("anna", "anna1234")
    assert user.username == "anna"
    assert user.role.value == "user"


def test_login_is_case_insensitive_for_username(services):
    user = services.auth.authenticate("ANNA", "anna1234")
    assert user.id == 1


def test_login_rejects_wrong_password(services):
    with pytest.raises(AuthenticationError):
        services.auth.authenticate("anna", "zle-haslo")


def test_login_rejects_unknown_user_with_same_message(services):
    with pytest.raises(AuthenticationError) as unknown:
        services.auth.authenticate("nieznany", "anna1234")
    with pytest.raises(AuthenticationError) as wrong:
        services.auth.authenticate("anna", "zle-haslo")
    assert str(unknown.value) == str(wrong.value)


def test_login_requires_both_fields(services):
    with pytest.raises(ValidationError):
        services.auth.authenticate("", "")
