from __future__ import annotations


def test_login_required_redirects_to_login(client):
    response = client.get("/tickets")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_login_success(login):
    response = login()
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Zgłoszenia" in body
    assert "Anna Kowalska" in body


def test_login_failure_shows_message(client, csrf_token):
    token = csrf_token("/login")
    response = client.post(
        "/login",
        data={
            "username": "anna",
            "password": "zle-haslo",
            "csrf_token": token,
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "Nieprawidłowa nazwa użytkownika lub hasło." in response.get_data(
        as_text=True
    )


def test_login_without_csrf_token_is_rejected(client):
    response = client.post(
        "/login",
        data={"username": "anna", "password": "anna1234"},
    )
    assert response.status_code == 400


def test_logout_clears_session(client, login, csrf_token):
    login()
    token = csrf_token("/tickets")
    response = client.post(
        "/logout",
        data={"csrf_token": token},
        follow_redirects=True,
    )
    body = response.get_data(as_text=True)
    assert "Zostałeś wylogowany." in body
    assert "Zaloguj się" in body


def test_user_cannot_open_dashboard(client, login):
    login("anna", "anna1234")
    assert client.get("/dashboard").status_code == 403


def test_technician_sees_dashboard(client, login):
    login("marek", "marek1234")
    response = client.get("/dashboard")
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Średni czas zamknięcia" in body
    assert "Według statusu" in body
