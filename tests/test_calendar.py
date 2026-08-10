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
    def __init__(self, inner, fail_select=False, fail_execute_contains=None, fail_commit=False):
        self.inner = inner
        self.fail_select = fail_select
        self.fail_execute_contains = fail_execute_contains
        self.fail_commit = fail_commit
        self.close_calls = 0
        self.commit_calls = 0
        self.rollback_calls = 0

    def execute(self, sql, *args, **kwargs):
        if self.fail_select and "SELECT * FROM app_calendar_events" in str(sql):
            raise RuntimeError("select calendario falhou passo 106")
        if self.fail_execute_contains and self.fail_execute_contains in str(sql):
            raise RuntimeError("execute calendario falhou passo 108")
        return self.inner.execute(sql, *args, **kwargs)

    def commit(self):
        self.commit_calls += 1
        if self.fail_commit:
            raise RuntimeError("commit calendario falhou passo 108")
        return self.inner.commit()

    def rollback(self):
        self.rollback_calls += 1
        return self.inner.rollback()

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


def _install_calendar_connection_spy(
    isolated_app,
    fail_select=False,
    fail_execute_contains=None,
    fail_commit=False,
):
    original_get_app_notes_db = isolated_app.module.get_app_notes_db
    tracked = []

    def tracked_get_app_notes_db():
        conn = _CalendarTrackedConnection(
            original_get_app_notes_db(),
            fail_select=fail_select,
            fail_execute_contains=fail_execute_contains,
            fail_commit=fail_commit,
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


def _create_calendar_event_for_write_route(isolated_app, event_id="evento-passo-108"):
    conn = isolated_app.module.get_app_notes_db()
    try:
        conn.execute(
            """
            INSERT INTO app_calendar_events(
                id,title,details,due_date,notify_days_before,reminders_per_day,
                status,created_at,updated_at,completed_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (
                event_id,
                "Evento Original",
                "Detalhe Original",
                "2099-06-10",
                2,
                4,
                "pending",
                "2026-08-10T07:00:00",
                "2026-08-10T07:00:00",
                None,
            ),
        )
        conn.commit()
    finally:
        conn.close()
    return event_id


def _calendar_update_body(**overrides):
    body = {
        "title": "Evento Editado",
        "details": "Detalhe Editado",
        "due_date": "2099-07-10",
        "notify_days_before": 3,
        "reminders_per_day": 5,
        "status": "pending",
    }
    body.update(overrides)
    return body


def _install_calendar_permission_bypass(isolated_app):
    original_require = isolated_app.module.require_monteiro_calendar
    isolated_app.module.require_monteiro_calendar = lambda x_token="": {"role": "admin"}
    return original_require


def _restore_calendar_permission_bypass(isolated_app, original_require):
    isolated_app.module.require_monteiro_calendar = original_require


def _assert_single_close_and_rollback(tracked):
    assert len(tracked) == 1
    assert tracked[0].close_calls == 1
    assert tracked[0].rollback_calls == 1


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


def test_update_app_calendar_event_rolls_back_and_closes_when_execute_fails(isolated_app):
    event_id = _create_calendar_event_for_write_route(isolated_app)
    original_get_app_notes_db, tracked = _install_calendar_connection_spy(
        isolated_app,
        fail_execute_contains="UPDATE app_calendar_events SET title",
    )
    original_require = _install_calendar_permission_bypass(isolated_app)
    try:
        with pytest.raises(RuntimeError, match="execute calendario falhou passo 108"):
            isolated_app.module.update_app_calendar_event(
                event_id,
                _calendar_update_body(),
                x_token="token",
            )
    finally:
        _restore_calendar_permission_bypass(isolated_app, original_require)
        _restore_calendar_connection_spy(
            isolated_app,
            original_get_app_notes_db,
            tracked,
        )

    _assert_single_close_and_rollback(tracked)
    _assert_calendar_write_after_restoring(isolated_app, "Escrita apos update execute")


def test_update_app_calendar_event_rolls_back_and_closes_when_commit_fails(isolated_app):
    event_id = _create_calendar_event_for_write_route(isolated_app)
    original_get_app_notes_db, tracked = _install_calendar_connection_spy(
        isolated_app,
        fail_commit=True,
    )
    original_require = _install_calendar_permission_bypass(isolated_app)
    try:
        with pytest.raises(RuntimeError, match="commit calendario falhou passo 108"):
            isolated_app.module.update_app_calendar_event(
                event_id,
                _calendar_update_body(),
                x_token="token",
            )
    finally:
        _restore_calendar_permission_bypass(isolated_app, original_require)
        _restore_calendar_connection_spy(
            isolated_app,
            original_get_app_notes_db,
            tracked,
        )

    _assert_single_close_and_rollback(tracked)
    _assert_calendar_write_after_restoring(isolated_app, "Escrita apos update commit")


def test_update_app_calendar_event_rolls_back_and_closes_when_serialization_fails(isolated_app):
    event_id = _create_calendar_event_for_write_route(isolated_app)
    original_get_app_notes_db, tracked = _install_calendar_connection_spy(isolated_app)
    original_require = _install_calendar_permission_bypass(isolated_app)
    original_event_dict = isolated_app.module._calendar_event_dict

    def failing_event_dict(row):
        raise RuntimeError("serializacao calendario falhou passo 108")

    isolated_app.module._calendar_event_dict = failing_event_dict
    try:
        with pytest.raises(RuntimeError, match="serializacao calendario falhou passo 108"):
            isolated_app.module.update_app_calendar_event(
                event_id,
                _calendar_update_body(),
                x_token="token",
            )
    finally:
        isolated_app.module._calendar_event_dict = original_event_dict
        _restore_calendar_permission_bypass(isolated_app, original_require)
        _restore_calendar_connection_spy(
            isolated_app,
            original_get_app_notes_db,
            tracked,
        )

    _assert_single_close_and_rollback(tracked)
    _assert_calendar_write_after_restoring(isolated_app, "Escrita apos update serializacao")


def test_update_app_calendar_status_rolls_back_and_closes_when_execute_fails(isolated_app):
    event_id = _create_calendar_event_for_write_route(isolated_app)
    original_get_app_notes_db, tracked = _install_calendar_connection_spy(
        isolated_app,
        fail_execute_contains="UPDATE app_calendar_events SET status",
    )
    original_require = _install_calendar_permission_bypass(isolated_app)
    try:
        with pytest.raises(RuntimeError, match="execute calendario falhou passo 108"):
            isolated_app.module.update_app_calendar_status(
                event_id,
                {"status": "completed"},
                x_token="token",
            )
    finally:
        _restore_calendar_permission_bypass(isolated_app, original_require)
        _restore_calendar_connection_spy(
            isolated_app,
            original_get_app_notes_db,
            tracked,
        )

    _assert_single_close_and_rollback(tracked)
    _assert_calendar_write_after_restoring(isolated_app, "Escrita apos status execute")


def test_update_app_calendar_status_rolls_back_and_closes_when_commit_fails(isolated_app):
    event_id = _create_calendar_event_for_write_route(isolated_app)
    original_get_app_notes_db, tracked = _install_calendar_connection_spy(
        isolated_app,
        fail_commit=True,
    )
    original_require = _install_calendar_permission_bypass(isolated_app)
    try:
        with pytest.raises(RuntimeError, match="commit calendario falhou passo 108"):
            isolated_app.module.update_app_calendar_status(
                event_id,
                {"status": "completed"},
                x_token="token",
            )
    finally:
        _restore_calendar_permission_bypass(isolated_app, original_require)
        _restore_calendar_connection_spy(
            isolated_app,
            original_get_app_notes_db,
            tracked,
        )

    _assert_single_close_and_rollback(tracked)
    _assert_calendar_write_after_restoring(isolated_app, "Escrita apos status commit")


def test_delete_app_calendar_event_rolls_back_and_closes_when_execute_fails(isolated_app):
    event_id = _create_calendar_event_for_write_route(isolated_app)
    original_get_app_notes_db, tracked = _install_calendar_connection_spy(
        isolated_app,
        fail_execute_contains="DELETE FROM app_calendar_events",
    )
    original_require = _install_calendar_permission_bypass(isolated_app)
    try:
        with pytest.raises(RuntimeError, match="execute calendario falhou passo 108"):
            isolated_app.module.delete_app_calendar_event(event_id, x_token="token")
    finally:
        _restore_calendar_permission_bypass(isolated_app, original_require)
        _restore_calendar_connection_spy(
            isolated_app,
            original_get_app_notes_db,
            tracked,
        )

    _assert_single_close_and_rollback(tracked)
    _assert_calendar_write_after_restoring(isolated_app, "Escrita apos delete execute")


def test_delete_app_calendar_event_rolls_back_and_closes_when_commit_fails(isolated_app):
    event_id = _create_calendar_event_for_write_route(isolated_app)
    original_get_app_notes_db, tracked = _install_calendar_connection_spy(
        isolated_app,
        fail_commit=True,
    )
    original_require = _install_calendar_permission_bypass(isolated_app)
    try:
        with pytest.raises(RuntimeError, match="commit calendario falhou passo 108"):
            isolated_app.module.delete_app_calendar_event(event_id, x_token="token")
    finally:
        _restore_calendar_permission_bypass(isolated_app, original_require)
        _restore_calendar_connection_spy(
            isolated_app,
            original_get_app_notes_db,
            tracked,
        )

    _assert_single_close_and_rollback(tracked)
    _assert_calendar_write_after_restoring(isolated_app, "Escrita apos delete commit")
