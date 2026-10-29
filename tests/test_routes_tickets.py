from __future__ import annotations


def test_user_sees_only_own_tickets(client, login):
    login("anna", "anna1234")
    body = client.get("/tickets").get_data(as_text=True)
    assert "Nie działa drukarka w sali 204" in body
    assert "Nie mogę zalogować się do VPN" not in body


def test_technician_sees_all_tickets(client, login):
    login("marek", "marek1234")
    first_page = client.get("/tickets").get_data(as_text=True)
    second_page = client.get("/tickets?page=2").get_data(as_text=True)
    assert "Nie mogę zalogować się do VPN" in first_page
    assert "Podejrzenie phishingu w wiadomości" in first_page
    assert "Nie działa drukarka w sali 204" in second_page


def test_filter_by_status(client, login):
    login("marek", "marek1234")
    body = client.get("/tickets?status=closed").get_data(as_text=True)
    assert "Brak dostępu do folderu projektowego" in body
    assert "Nie działa drukarka w sali 204" not in body


def test_text_search(client, login):
    login("marek", "marek1234")
    body = client.get("/tickets?q=phishing").get_data(as_text=True)
    assert "Podejrzenie phishingu w wiadomości" in body
    assert "Nie działa drukarka w sali 204" not in body


def test_pagination_second_page(client, login):
    login("marek", "marek1234")
    body = client.get("/tickets?page=2").get_data(as_text=True)
    assert "Strona 2 z 2" in body
    assert "12 zgłoszeń" in body


def test_user_can_create_ticket(client, login, csrf_token):
    login("anna", "anna1234")
    token = csrf_token("/tickets/new")
    response = client.post(
        "/tickets",
        data={
            "title": "Nowy problem z kontem",
            "description": "Opis nowego problemu jest wystarczająco długi.",
            "priority": "high",
            "channel": "form",
            "csrf_token": token,
        },
        follow_redirects=True,
    )
    body = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "Nowy problem z kontem" in body
    assert "Zgłoszenie zostało utworzone." in body


def test_create_ticket_validation_error(client, login, csrf_token):
    login("anna", "anna1234")
    token = csrf_token("/tickets/new")
    response = client.post(
        "/tickets",
        data={
            "title": "ab",
            "description": "krótki",
            "priority": "high",
            "channel": "form",
            "csrf_token": token,
        },
    )
    body = response.get_data(as_text=True)
    assert response.status_code == 400
    assert "Tytuł musi mieć od 3 do 120 znaków." in body


def test_user_cannot_view_foreign_ticket(client, login):
    login("anna", "anna1234")
    assert client.get("/tickets/4").status_code == 404


def test_user_cannot_export_csv(client, login):
    login("anna", "anna1234")
    assert client.get("/tickets/export.csv").status_code == 403


def test_technician_can_export_csv(client, login):
    login("marek", "marek1234")
    response = client.get("/tickets/export.csv")
    assert response.status_code == 200
    assert response.data.startswith(b"\xef\xbb\xbf")
    assert "ID;Tytuł;Priorytet;Status;Kanał" in response.get_data(as_text=True)


def test_technician_changes_status(client, login, csrf_token):
    login("marek", "marek1234")
    token = csrf_token("/tickets/4")
    response = client.post(
        "/tickets/4/status",
        data={"status": "in_progress", "csrf_token": token},
        follow_redirects=True,
    )
    body = response.get_data(as_text=True)
    assert "Status został zmieniony." in body
    assert "w toku" in body


def test_invalid_status_transition_shows_error(client, login, csrf_token):
    login("marek", "marek1234")
    token = csrf_token("/tickets/4")
    response = client.post(
        "/tickets/4/status",
        data={"status": "waiting", "csrf_token": token},
        follow_redirects=True,
    )
    body = response.get_data(as_text=True)
    assert "Nie można zmienić statusu" in body


def test_technician_adds_comment(client, login, csrf_token):
    login("marek", "marek1234")
    token = csrf_token("/tickets/4")
    response = client.post(
        "/tickets/4/comments",
        data={"body": "Nowy komentarz testowy.", "csrf_token": token},
        follow_redirects=True,
    )
    body = response.get_data(as_text=True)
    assert "Komentarz został dodany." in body
    assert "Nowy komentarz testowy." in body


def test_technician_assigns_ticket_to_self(client, login, csrf_token):
    login("marek", "marek1234")
    token = csrf_token("/tickets/4")
    response = client.post(
        "/tickets/4/assign",
        data={"csrf_token": token},
        follow_redirects=True,
    )
    body = response.get_data(as_text=True)
    assert "Zgłoszenie zostało przypisane do Ciebie." in body
    assert "Marek Wiśniewski" in body


def test_user_cannot_change_status(client, login, csrf_token):
    login("anna", "anna1234")
    token = csrf_token("/tickets/1")
    response = client.post(
        "/tickets/1/status",
        data={"status": "closed", "csrf_token": token},
    )
    assert response.status_code == 403


def test_ticket_post_without_csrf_is_rejected(client, login):
    login("anna", "anna1234")
    response = client.post(
        "/tickets",
        data={
            "title": "Bez tokenu",
            "description": "Opis problemu jest wystarczająco długi.",
            "priority": "low",
            "channel": "form",
        },
    )
    assert response.status_code == 400
