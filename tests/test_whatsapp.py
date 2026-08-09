import json
import sqlite3
import uuid
from datetime import datetime
from datetime import date
from datetime import timedelta

from fastapi.testclient import TestClient


def _login(test_client, username="admin", password="admin123", company="raios"):
    response = test_client.post(
        "/api/auth/login",
        headers={"x-company": company},
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["token"]


def _headers(token, company="raios"):
    return {"x-token": token, "x-company": company}


def _add_contact(db_path, name, phone, active=1):
    contact_id = str(uuid.uuid4())
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO whatsapp_contacts(id,name,phone,active,created_by) VALUES(?,?,?,?,?)",
            (contact_id, name, phone, active, "teste"),
        )
        conn.commit()
    finally:
        conn.close()
    return contact_id


def _add_template(db_path, name="Motivacao Teste", content="Foco e constancia."):
    template_id = str(uuid.uuid4())
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            "INSERT INTO whatsapp_templates(id,name,category,content) VALUES(?,?,?,?)",
            (template_id, name, "motivacao", content),
        )
        conn.commit()
    finally:
        conn.close()
    return template_id


def _add_overdue_boleto(db_path, client="Cliente Boleto", total=120.0, due_date=None):
    boleto_id = str(uuid.uuid4())
    due = due_date or (date.today() - timedelta(days=1)).isoformat()
    sale_date = (date.today() - timedelta(days=10)).isoformat()
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """INSERT INTO boletos(id,client,sale_date,nf_number,total_val,due_date,status)
               VALUES(?,?,?,?,?,?,?)""",
            (boleto_id, client, sale_date, boleto_id[:6], total, due, "pendente"),
        )
        conn.commit()
    finally:
        conn.close()
    return boleto_id


def _set_config(db_path, key, value):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("INSERT OR REPLACE INTO whatsapp_config(key,value) VALUES(?,?)", (key, value))
        conn.commit()
    finally:
        conn.close()


def _get_config(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return {
            row["key"]: row["value"]
            for row in conn.execute("SELECT key,value FROM whatsapp_config").fetchall()
        }
    finally:
        conn.close()


def _fetch_logs(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return [
            dict(row)
            for row in conn.execute(
                "SELECT phone,contact,event_type,message,status,response FROM whatsapp_log ORDER BY phone"
            ).fetchall()
        ]
    finally:
        conn.close()


class _TrackedConnection:
    def __init__(self, conn, state, fail_log_insert=False):
        self._conn = conn
        self._state = state
        self._fail_log_insert = fail_log_insert
        self._closed = False
        state["open"] += 1

    def execute(self, sql, args=()):
        if self._fail_log_insert and "INSERT INTO whatsapp_log" in sql:
            raise sqlite3.OperationalError("falha controlada no log")
        return self._conn.execute(sql, args)

    def commit(self):
        return self._conn.commit()

    def rollback(self):
        self._state["rollbacks"] += 1
        return self._conn.rollback()

    def close(self):
        if not self._closed:
            self._closed = True
            self._state["closes"] += 1
            self._state["open"] -= 1
        return self._conn.close()

    def __getattr__(self, name):
        return getattr(self._conn, name)


def _install_tracked_db(monkeypatch, isolated_app, fail_log_insert=False):
    original_get_db = isolated_app.module.get_db
    state = {"open": 0, "closes": 0, "rollbacks": 0}

    def tracked_get_db(company=None):
        return _TrackedConnection(original_get_db(company), state, fail_log_insert=fail_log_insert)

    monkeypatch.setattr(isolated_app.module, "get_db", tracked_get_db)
    return state


def test_whatsapp_send_uses_active_contacts_without_open_sqlite_during_send(isolated_app, monkeypatch):
    token = _login(isolated_app.client)
    _add_contact(isolated_app.db_paths["raios"], "Contato Um", "559500000001", active=1)
    _add_contact(isolated_app.db_paths["raios"], "Contato Dois", "559500000002", active=1)
    _add_contact(isolated_app.db_paths["raios"], "Contato Inativo", "559500000003", active=0)
    state = _install_tracked_db(monkeypatch, isolated_app)
    calls = []

    def fake_wa_send(phone, message, cfg):
        assert state["open"] == 0
        calls.append((phone, message, cfg.get("provider")))
        return {"ok": True, "response": "sent"}

    monkeypatch.setattr(isolated_app.module, "wa_send", fake_wa_send)

    response = isolated_app.client.post(
        "/api/whatsapp/send",
        headers=_headers(token),
        json={"message": "Mensagem manual", "event_type": "manual"},
    )

    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert [item["phone"] for item in response.json()["results"]] == ["559500000001", "559500000002"]
    assert [call[0] for call in calls] == ["559500000001", "559500000002"]
    assert state["open"] == 0
    assert state["closes"] >= 2
    logs = _fetch_logs(isolated_app.db_paths["raios"])
    assert [(row["phone"], row["status"], row["event_type"]) for row in logs] == [
        ("559500000001", "sent", "manual"),
        ("559500000002", "sent", "manual"),
    ]


def test_whatsapp_send_respects_explicit_contact_selection_and_failed_provider_result(isolated_app, monkeypatch):
    token = _login(isolated_app.client)
    selected_id = _add_contact(isolated_app.db_paths["raios"], "Contato Selecionado", "559511111111", active=1)
    _add_contact(isolated_app.db_paths["raios"], "Contato Fora", "559522222222", active=1)
    state = _install_tracked_db(monkeypatch, isolated_app)

    def fake_wa_send(phone, message, cfg):
        assert state["open"] == 0
        return {"ok": False, "response": "401 unauthorized"}

    monkeypatch.setattr(isolated_app.module, "wa_send", fake_wa_send)

    response = isolated_app.client.post(
        "/api/whatsapp/send",
        headers=_headers(token),
        json={"contact_ids": [selected_id], "message": "Mensagem selecionada", "event_type": "teste"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] == 1
    assert payload["results"][0]["phone"] == "559511111111"
    assert payload["results"][0]["ok"] is False
    assert payload["results"][0]["hint"]
    logs = _fetch_logs(isolated_app.db_paths["raios"])
    assert len(logs) == 1
    assert logs[0]["phone"] == "559511111111"
    assert logs[0]["status"] == "error"
    assert json.loads(logs[0]["response"])["hint"]


def test_whatsapp_send_rolls_back_and_closes_when_log_persistence_fails(isolated_app, monkeypatch):
    token = _login(isolated_app.client)
    _add_contact(isolated_app.db_paths["raios"], "Contato Log Falha", "559533333333", active=1)
    state = _install_tracked_db(monkeypatch, isolated_app, fail_log_insert=True)
    sent = []

    def fake_wa_send(phone, message, cfg):
        assert state["open"] == 0
        sent.append(phone)
        return {"ok": True, "response": "sent"}

    monkeypatch.setattr(isolated_app.module, "wa_send", fake_wa_send)

    with TestClient(isolated_app.module.app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/whatsapp/send",
            headers=_headers(token),
            json={"message": "Mensagem com falha de log", "event_type": "manual"},
        )

    assert response.status_code == 500
    assert sent == ["559533333333"]
    assert state["rollbacks"] == 1
    assert state["open"] == 0
    assert _fetch_logs(isolated_app.db_paths["raios"]) == []

    # A escrita seguinte confirma que a conexao foi fechada e o banco nao ficou travado.
    _add_contact(isolated_app.db_paths["raios"], "Contato Depois", "559544444444", active=1)


def test_daily_motivation_send_now_separates_db_from_provider_and_logs_results(isolated_app, monkeypatch):
    token = _login(isolated_app.client)
    db_path = isolated_app.db_paths["raios"]
    _add_template(db_path, content="Atenda com energia.")
    _add_contact(db_path, "Contato A", "559566666661", active=1)
    _add_contact(db_path, "Contato B", "559566666662", active=1)
    monkeypatch.setattr(
        isolated_app.module,
        "_motivation_now",
        lambda: datetime.fromisoformat("2026-08-08T08:00:00-04:00"),
    )
    state = _install_tracked_db(monkeypatch, isolated_app)
    calls = []

    def fake_wa_send(phone, message, cfg):
        assert state["open"] == 0
        calls.append((phone, message))
        return {"ok": phone.endswith("1"), "response": "ok" if phone.endswith("1") else "falha"}

    monkeypatch.setattr(isolated_app.module, "wa_send", fake_wa_send)

    response = isolated_app.client.post(
        "/api/whatsapp/motivation-send-now",
        headers=_headers(token),
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["sent"] == 1
    assert payload["failed"] == 1
    assert payload["templates"] == 1
    assert payload["message"] == "Atenda com energia."
    assert [phone for phone, _message in calls] == ["559566666661", "559566666662"]
    assert all("Atenda com energia." in message for _phone, message in calls)
    assert state["open"] == 0

    cfg = _get_config(db_path)
    assert cfg["motivation_last_attempt"].startswith("2026-08-08T08:00:00")
    assert cfg["motivation_last_success"] == "2026-08-08"
    logs = _fetch_logs(db_path)
    motivation_logs = [row for row in logs if row["event_type"] == "motivacao"]
    assert [(row["phone"], row["status"]) for row in motivation_logs] == [
        ("559566666661", "sent"),
        ("559566666662", "error"),
    ]


def test_daily_motivation_force_false_respects_recent_attempt_without_send(isolated_app, monkeypatch):
    db_path = isolated_app.db_paths["raios"]
    _add_template(db_path)
    _add_contact(db_path, "Contato A", "559577777771", active=1)
    _set_config(db_path, "motivation_last_attempt", "2026-08-08T07:30:00-04:00")
    _set_config(db_path, "motivation_last_success", "")
    monkeypatch.setattr(
        isolated_app.module,
        "_motivation_now",
        lambda: datetime.fromisoformat("2026-08-08T08:00:00-04:00"),
    )
    state = _install_tracked_db(monkeypatch, isolated_app)
    sent = []

    def fake_wa_send(phone, message, cfg):
        sent.append(phone)
        return {"ok": True, "response": "ok"}

    monkeypatch.setattr(isolated_app.module, "wa_send", fake_wa_send)

    result = isolated_app.module.send_daily_motivation(force=False)

    assert result == {"ok": False, "reason": "retry_wait"}
    assert sent == []
    assert state["open"] == 0
    assert _get_config(db_path)["motivation_last_attempt"] == "2026-08-08T07:30:00-04:00"


def test_daily_motivation_without_contacts_preserves_current_no_contacts_result(isolated_app, monkeypatch):
    db_path = isolated_app.db_paths["raios"]
    _add_template(db_path)
    monkeypatch.setattr(
        isolated_app.module,
        "_motivation_now",
        lambda: datetime.fromisoformat("2026-08-08T08:00:00-04:00"),
    )
    state = _install_tracked_db(monkeypatch, isolated_app)

    def fake_wa_send(phone, message, cfg):
        raise AssertionError("nao deve enviar sem contatos")

    monkeypatch.setattr(isolated_app.module, "wa_send", fake_wa_send)

    result = isolated_app.module.send_daily_motivation(force=True)

    assert result == {"ok": False, "reason": "no_contacts", "count": 1}
    assert state["open"] == 0
    assert _get_config(db_path)["motivation_last_attempt"] == ""


def test_daily_motivation_rolls_back_and_closes_when_log_persistence_fails(isolated_app, monkeypatch):
    db_path = isolated_app.db_paths["raios"]
    _add_template(db_path, content="Persistir depois do envio.")
    _add_contact(db_path, "Contato Falha Log", "559588888881", active=1)
    monkeypatch.setattr(
        isolated_app.module,
        "_motivation_now",
        lambda: datetime.fromisoformat("2026-08-08T08:00:00-04:00"),
    )
    state = _install_tracked_db(monkeypatch, isolated_app, fail_log_insert=True)
    sent = []

    def fake_wa_send(phone, message, cfg):
        assert state["open"] == 0
        sent.append(phone)
        return {"ok": True, "response": "ok"}

    monkeypatch.setattr(isolated_app.module, "wa_send", fake_wa_send)

    with TestClient(isolated_app.module.app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/whatsapp/motivation-send-now",
            headers=_headers(_login(isolated_app.client)),
        )

    assert response.status_code == 500
    assert sent == ["559588888881"]
    assert state["rollbacks"] == 1
    assert state["open"] == 0
    assert _fetch_logs(db_path) == []
    cfg = _get_config(db_path)
    assert cfg["motivation_last_attempt"].startswith("2026-08-08T08:00:00")
    assert cfg["motivation_last_success"] == ""

    _add_contact(db_path, "Contato Depois", "559588888882", active=1)


def test_whatsapp_triggers_preview_does_not_send_or_log(isolated_app, monkeypatch):
    token = _login(isolated_app.client)
    db_path = isolated_app.db_paths["raios"]
    _add_overdue_boleto(db_path, client="Cliente Preview", total=150.0)
    _add_contact(db_path, "Contato Preview", "559599000001", active=1)
    state = _install_tracked_db(monkeypatch, isolated_app)
    sent = []

    def fake_wa_send(phone, message, cfg):
        sent.append(phone)
        return {"ok": True, "response": "ok"}

    monkeypatch.setattr(isolated_app.module, "wa_send", fake_wa_send)

    response = isolated_app.client.post(
        "/api/whatsapp/check-triggers",
        headers=_headers(token),
        json={"send": False},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["dry_run"] is True
    assert payload["sent"] is None
    assert payload["triggers_fired"] >= 1
    assert "boleto" in payload["details"]
    assert sent == []
    assert _fetch_logs(db_path) == []
    assert state["open"] == 0


def test_whatsapp_triggers_send_true_sends_without_open_sqlite_and_persists_logs(isolated_app, monkeypatch):
    token = _login(isolated_app.client)
    db_path = isolated_app.db_paths["raios"]
    _add_overdue_boleto(db_path, client="Cliente Envio", total=200.0)
    _add_contact(db_path, "Contato Um", "559599000011", active=1)
    _add_contact(db_path, "Contato Dois", "559599000012", active=1)
    state = _install_tracked_db(monkeypatch, isolated_app)
    calls = []

    def fake_wa_send(phone, message, cfg):
        assert state["open"] == 0
        calls.append((phone, message))
        return {"ok": phone.endswith("11"), "response": "ok" if phone.endswith("11") else "erro"}

    monkeypatch.setattr(isolated_app.module, "wa_send", fake_wa_send)

    response = isolated_app.client.post(
        "/api/whatsapp/check-triggers",
        headers=_headers(token),
        json={"send": True},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["dry_run"] is False
    assert payload["triggers_fired"] >= 1
    assert [item["phone"] for item in payload["sent"]] == ["559599000011", "559599000012"]
    assert [item["ok"] for item in payload["sent"]] == [True, False]
    assert [phone for phone, _message in calls] == ["559599000011", "559599000012"]
    assert all("Boletos Vencidos" in message for _phone, message in calls)
    assert state["open"] == 0
    logs = [row for row in _fetch_logs(db_path) if row["event_type"] == "boleto"]
    assert [(row["phone"], row["status"]) for row in logs] == [
        ("559599000011", "sent"),
        ("559599000012", "error"),
    ]


def test_whatsapp_triggers_rolls_back_and_closes_when_log_persistence_fails(isolated_app, monkeypatch):
    token = _login(isolated_app.client)
    db_path = isolated_app.db_paths["raios"]
    _add_overdue_boleto(db_path, client="Cliente Falha Log", total=300.0)
    _add_contact(db_path, "Contato Log Falha", "559599000021", active=1)
    state = _install_tracked_db(monkeypatch, isolated_app, fail_log_insert=True)
    sent = []

    def fake_wa_send(phone, message, cfg):
        assert state["open"] == 0
        sent.append(phone)
        return {"ok": True, "response": "ok"}

    monkeypatch.setattr(isolated_app.module, "wa_send", fake_wa_send)

    with TestClient(isolated_app.module.app, raise_server_exceptions=False) as client:
        response = client.post(
            "/api/whatsapp/check-triggers",
            headers=_headers(token),
            json={"send": True},
        )

    assert response.status_code == 500
    assert sent == ["559599000021"]
    assert state["rollbacks"] == 1
    assert state["open"] == 0
    assert _fetch_logs(db_path) == []

    _add_contact(db_path, "Contato Depois", "559599000022", active=1)
