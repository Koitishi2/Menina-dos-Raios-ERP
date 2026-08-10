import pytest
from datetime import date


FIXED_TODAY = date(2026, 8, 9)


def _fix_calendar_today(isolated_app, monkeypatch):
    class FixedDate:
        @classmethod
        def today(cls):
            return FIXED_TODAY

    monkeypatch.setitem(isolated_app.module._calendar_event_dict.__globals__, "date", FixedDate)


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


class _CalendarTrackedConnection:
    def __init__(self, inner, fail_select=False):
        self.inner = inner
        self.fail_select = fail_select
        self.close_calls = 0

    def execute(self, sql, *args, **kwargs):
        if self.fail_select and "SELECT * FROM app_calendar_events" in str(sql):
            raise RuntimeError("select calendario falhou passo 106")
        return self.inner.execute(sql, *args, **kwargs)

    def close(self):
        self.close_calls += 1
        return self.inner.close()

    def cleanup_inner(self):
        try:
            self.inner.close()
        except Exception:
            pass

    def __getattr__(self, name):
        return getattr(self.inner, name)


def _install_calendar_connection_spy(isolated_app, fail_select=False):
    original_get_app_notes_db = isolated_app.module.get_app_notes_db
    tracked = []

    def tracked_get_app_notes_db():
        conn = _CalendarTrackedConnection(
            original_get_app_notes_db(),
            fail_select=fail_select,
        )
        tracked.append(conn)
        return conn

    isolated_app.module.get_app_notes_db = tracked_get_app_notes_db
    return original_get_app_notes_db, tracked


def _restore_calendar_connection_spy(isolated_app, original_get_app_notes_db, tracked):
    isolated_app.module.get_app_notes_db = original_get_app_notes_db
    for conn in tracked:
        if conn.close_calls == 0:
            conn.cleanup_inner()


def _assert_calendar_write_after_restoring(isolated_app, title):
    token = _login(isolated_app.client)
    response = isolated_app.client.post(
        "/api/app-calendar",
        headers=_headers(token),
        json={"title": title, "due_date": "2099-05-10"},
    )
    assert response.status_code == 200, response.text


def test_calendar_event_dict_calcula_janela_com_data_controlada(isolated_app, monkeypatch):
    _fix_calendar_today(isolated_app, monkeypatch)
    event_dict = isolated_app.module._calendar_event_dict

    hoje = event_dict({
        "id": "hoje",
        "due_date": "2026-08-09",
        "status": "pending",
        "notify_days_before": 2,
    })
    assert hoje["days_left"] == 0
    assert hoje["in_reminder_window"] is True

    futuro_dentro = event_dict({
        "id": "futuro-dentro",
        "due_date": "2026-08-11",
        "status": "pending",
        "notify_days_before": 2,
    })
    assert futuro_dentro["days_left"] == 2
    assert futuro_dentro["in_reminder_window"] is True

    futuro_fora = event_dict({
        "id": "futuro-fora",
        "due_date": "2026-08-12",
        "status": "pending",
        "notify_days_before": 2,
    })
    assert futuro_fora["days_left"] == 3
    assert futuro_fora["in_reminder_window"] is False

    passado = event_dict({
        "id": "passado",
        "due_date": "2026-08-08",
        "status": "pending",
        "notify_days_before": 2,
    })
    assert passado["days_left"] == -1
    assert passado["in_reminder_window"] is False


def test_calendar_event_dict_status_e_campos_preservados(isolated_app, monkeypatch):
    _fix_calendar_today(isolated_app, monkeypatch)
    event_dict = isolated_app.module._calendar_event_dict

    completed = event_dict({
        "id": "completed",
        "title": "Evento concluido",
        "details": "Detalhe original",
        "due_date": "2026-08-09",
        "status": "completed",
        "notify_days_before": 2,
        "extra": "preservado",
    })
    assert completed["days_left"] == 0
    assert completed["in_reminder_window"] is False
    assert completed["title"] == "Evento concluido"
    assert completed["details"] == "Detalhe original"
    assert completed["extra"] == "preservado"

    status_vazio = event_dict({
        "id": "status-vazio",
        "due_date": "2026-08-09",
        "status": "",
        "notify_days_before": 2,
    })
    assert status_vazio["days_left"] == 0
    assert status_vazio["in_reminder_window"] is False

    status_ausente = event_dict({
        "id": "status-ausente",
        "due_date": "2026-08-09",
        "notify_days_before": 2,
    })
    assert status_ausente["days_left"] == 0
    assert status_ausente["in_reminder_window"] is False


def test_calendar_event_dict_datas_invalidas_e_notify_atual(isolated_app, monkeypatch):
    _fix_calendar_today(isolated_app, monkeypatch)
    event_dict = isolated_app.module._calendar_event_dict

    for due_date in (None, "", "2026-08-09T10:30:00"):
        result = event_dict({
            "id": f"due-{due_date}",
            "due_date": due_date,
            "status": "pending",
            "notify_days_before": 2,
        })
        assert result["days_left"] is None
        assert result["in_reminder_window"] is False

    notify_none = event_dict({
        "id": "notify-none",
        "due_date": "2026-08-11",
        "status": "pending",
        "notify_days_before": None,
    })
    assert notify_none["days_left"] == 2
    assert notify_none["in_reminder_window"] is True

    notify_vazio = event_dict({
        "id": "notify-vazio",
        "due_date": "2026-08-11",
        "status": "pending",
        "notify_days_before": "",
    })
    assert notify_vazio["days_left"] == 2
    assert notify_vazio["in_reminder_window"] is True

    notify_invalido = event_dict({
        "id": "notify-invalido",
        "due_date": "2026-08-09",
        "status": "pending",
        "notify_days_before": "x",
    })
    assert notify_invalido["days_left"] is None
    assert notify_invalido["in_reminder_window"] is False


def test_calendar_event_dict_tipos_de_row_atuais(isolated_app, monkeypatch):
    _fix_calendar_today(isolated_app, monkeypatch)
    event_dict = isolated_app.module._calendar_event_dict

    dict_comum = event_dict({
        "id": "dict",
        "due_date": "2026-08-09",
        "status": "pending",
        "notify_days_before": 2,
    })
    assert dict_comum["days_left"] == 0
    assert dict_comum["in_reminder_window"] is True

    pares = event_dict([
        ("id", "pares"),
        ("due_date", "2026-08-09"),
        ("status", "pending"),
        ("notify_days_before", 2),
    ])
    assert pares["days_left"] == 0
    assert pares["in_reminder_window"] is True

    with pytest.raises(TypeError):
        event_dict(None)


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


def test_list_app_calendar_closes_connection_when_auto_complete_fails(isolated_app):
    failure = RuntimeError("auto-complete calendario falhou passo 106")
    original_get_app_notes_db, tracked = _install_calendar_connection_spy(isolated_app)
    original_auto_complete = isolated_app.module._auto_complete_expired_calendar_events
    original_require_monteiro_calendar = isolated_app.module.require_monteiro_calendar
    isolated_app.module.require_monteiro_calendar = lambda x_token="": {"role": "admin"}

    def failing_auto_complete(conn):
        raise failure

    isolated_app.module._auto_complete_expired_calendar_events = failing_auto_complete
    try:
        with pytest.raises(RuntimeError) as exc:
            isolated_app.module.list_app_calendar(x_token="token")
    finally:
        isolated_app.module._auto_complete_expired_calendar_events = original_auto_complete
        isolated_app.module.require_monteiro_calendar = original_require_monteiro_calendar
        _restore_calendar_connection_spy(
            isolated_app,
            original_get_app_notes_db,
            tracked,
        )

    assert exc.value is failure
    assert len(tracked) == 1
    assert tracked[0].close_calls == 1
    _assert_calendar_write_after_restoring(isolated_app, "Escrita apos falha web")


def test_list_app_calendar_closes_connection_when_select_fails(isolated_app):
    original_get_app_notes_db, tracked = _install_calendar_connection_spy(
        isolated_app,
        fail_select=True,
    )
    original_require_monteiro_calendar = isolated_app.module.require_monteiro_calendar
    isolated_app.module.require_monteiro_calendar = lambda x_token="": {"role": "admin"}
    try:
        with pytest.raises(RuntimeError, match="select calendario falhou passo 106"):
            isolated_app.module.list_app_calendar(x_token="token")
    finally:
        isolated_app.module.require_monteiro_calendar = original_require_monteiro_calendar
        _restore_calendar_connection_spy(
            isolated_app,
            original_get_app_notes_db,
            tracked,
        )

    assert len(tracked) == 1
    assert tracked[0].close_calls == 1


def test_list_app_calendar_mobile_closes_connection_when_auto_complete_fails(isolated_app):
    failure = RuntimeError("auto-complete mobile calendario falhou passo 106")
    original_get_app_notes_db, tracked = _install_calendar_connection_spy(isolated_app)
    original_auto_complete = isolated_app.module._auto_complete_expired_calendar_events

    def failing_auto_complete(conn):
        raise failure

    isolated_app.module._auto_complete_expired_calendar_events = failing_auto_complete
    try:
        with pytest.raises(RuntimeError) as exc:
            isolated_app.module.list_app_calendar_mobile(
                x_app_token=isolated_app.module.APP_CALENDAR_TOKEN,
            )
    finally:
        isolated_app.module._auto_complete_expired_calendar_events = original_auto_complete
        _restore_calendar_connection_spy(
            isolated_app,
            original_get_app_notes_db,
            tracked,
        )

    assert exc.value is failure
    assert len(tracked) == 1
    assert tracked[0].close_calls == 1
    _assert_calendar_write_after_restoring(isolated_app, "Escrita apos falha mobile")


def test_list_app_calendar_mobile_closes_connection_when_select_fails(isolated_app):
    original_get_app_notes_db, tracked = _install_calendar_connection_spy(
        isolated_app,
        fail_select=True,
    )
    try:
        with pytest.raises(RuntimeError, match="select calendario falhou passo 106"):
            isolated_app.module.list_app_calendar_mobile(
                x_app_token=isolated_app.module.APP_CALENDAR_TOKEN,
            )
    finally:
        _restore_calendar_connection_spy(
            isolated_app,
            original_get_app_notes_db,
            tracked,
        )

    assert len(tracked) == 1
    assert tracked[0].close_calls == 1
