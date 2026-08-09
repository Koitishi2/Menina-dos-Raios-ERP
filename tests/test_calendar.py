def _login(test_client, username="admin", password="admin123", company="raios"):
    response = test_client.post(
        "/api/auth/login",
        headers={"x-company": company},
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()["token"]


def _headers(token, company="raios"):
    return {"x-token": token, "x-company": company}


def _calendar_rows(isolated_app):
    conn = isolated_app.module.get_app_notes_db()
    try:
        return [
            dict(row)
            for row in conn.execute(
                "SELECT * FROM app_calendar_events ORDER BY due_date ASC, created_at ASC"
            ).fetchall()
        ]
    finally:
        conn.close()


def test_create_app_calendar_event_simple(isolated_app):
    token = _login(isolated_app.client)

    response = isolated_app.client.post(
        "/api/app-calendar",
        headers=_headers(token),
        json={
            "title": "Pagar fornecedor",
            "details": "Conferir boleto antes do vencimento",
            "due_date": "2099-01-15",
            "notify_days_before": 3,
            "reminders_per_day": 2,
            "status": "pending",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["created"] == 1
    assert len(payload["events"]) == 1
    event = payload["event"]
    assert event["title"] == "Pagar fornecedor"
    assert event["details"] == "Conferir boleto antes do vencimento"
    assert event["due_date"] == "2099-01-15"
    assert event["notify_days_before"] == 3
    assert event["reminders_per_day"] == 2
    assert event["status"] == "pending"

    rows = _calendar_rows(isolated_app)
    assert len(rows) == 1
    assert rows[0]["id"] == event["id"]

    listed = isolated_app.client.get(
        "/api/app-calendar?month=01&year=2099",
        headers=_headers(token),
    )
    assert listed.status_code == 200
    assert listed.json()["count"] == 1


def test_create_app_calendar_event_recorrente_preserva_datas_e_vinculos(isolated_app):
    token = _login(isolated_app.client)

    response = isolated_app.client.post(
        "/api/app-calendar",
        headers=_headers(token),
        json={
            "title": "Pagamento recorrente",
            "details": "Salario",
            "due_date": "2099-01-31",
            "notify_days_before": 2,
            "reminders_per_day": 4,
            "status": "pending",
            "recurring": True,
            "repeat_months": 3,
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["ok"] is True
    assert payload["created"] == 3
    assert [event["due_date"] for event in payload["events"]] == [
        "2099-01-31",
        "2099-02-28",
        "2099-03-31",
    ]
    assert [event["title"] for event in payload["events"]] == [
        "Pagamento recorrente",
        "Pagamento recorrente",
        "Pagamento recorrente",
    ]
    assert [event["details"] for event in payload["events"]] == [
        "Salario\n\nRecorrencia: 1/3",
        "Salario\n\nRecorrencia: 2/3",
        "Salario\n\nRecorrencia: 3/3",
    ]

    rows = _calendar_rows(isolated_app)
    assert len(rows) == 3
    assert [row["due_date"] for row in rows] == ["2099-01-31", "2099-02-28", "2099-03-31"]


def test_create_app_calendar_event_auth_e_validacao_atual(isolated_app):
    token = _login(isolated_app.client)

    sem_token = isolated_app.client.post(
        "/api/app-calendar",
        json={"title": "Sem token", "due_date": "2099-01-15"},
    )
    assert sem_token.status_code == 401

    titulo_vazio = isolated_app.client.post(
        "/api/app-calendar",
        headers=_headers(token),
        json={"title": "", "due_date": "2099-01-15"},
    )
    assert titulo_vazio.status_code == 400
    assert _calendar_rows(isolated_app) == []

    data_invalida = isolated_app.client.post(
        "/api/app-calendar",
        headers=_headers(token),
        json={"title": "Data invalida", "due_date": "31/01/2099"},
    )
    assert data_invalida.status_code == 400
    assert _calendar_rows(isolated_app) == []

    escrita_posterior = isolated_app.client.post(
        "/api/app-calendar",
        headers=_headers(token),
        json={"title": "Escrita posterior", "due_date": "2099-04-10"},
    )
    assert escrita_posterior.status_code == 200, escrita_posterior.text
    assert len(_calendar_rows(isolated_app)) == 1
