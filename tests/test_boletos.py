import json
import sqlite3
import uuid
from datetime import datetime, timedelta

import pytest


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


def _sale_payload(**overrides):
    payload = {
        "sale_type": "NF",
        "sale_date": "2026-08-05",
        "sale_time": "08:00",
        "client": "Cliente Boleto Padrao",
        "product": "Produto Boleto",
        "nf_number": "BOL-001",
        "quantity": 1,
        "unit_price": 100,
        "total": 100,
        "notes": "venda temporaria para boleto",
        "delivery_person": "Lucas",
        "plate": "BOL-0001",
        "source": "manual",
    }
    payload.update(overrides)
    return payload


def _create_sale(test_client, token, company="raios", **overrides):
    response = test_client.post(
        "/api/sales",
        headers=_headers(token, company),
        json=_sale_payload(**overrides),
    )
    assert response.status_code == 200
    return response.json()


def _list_boletos(test_client, token, company="raios", query=""):
    response = test_client.get(
        f"/api/boletos{query}",
        headers=_headers(token, company),
    )
    assert response.status_code == 200
    return response.json()


def _update_boleto(test_client, token, boleto_id, company="raios", **body):
    response = test_client.put(
        f"/api/boletos/{boleto_id}",
        headers=_headers(token, company),
        json=body,
    )
    assert response.status_code == 200
    return response.json()


def _read_boleto(db_path, boleto_id):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute("SELECT * FROM boletos WHERE id=?", (boleto_id,)).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _write_boleto_probe(db_path, boleto_id, value):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("UPDATE boletos SET notes=? WHERE id=?", (value, boleto_id))
        conn.commit()
    finally:
        conn.close()


class _TrackedBoletoConnection:
    def __init__(self, path, state, fail_execute=False, fail_commit=False):
        self._conn = sqlite3.connect(path)
        self._conn.row_factory = sqlite3.Row
        self._state = state
        self._fail_execute = fail_execute
        self._fail_commit = fail_commit
        state["open"] += 1

    def execute(self, sql, params=()):
        if sql.startswith("UPDATE boletos SET"):
            self._state["update_executes"] += 1
            if self._fail_execute:
                raise sqlite3.OperationalError("falha controlada no update boleto")
        return self._conn.execute(sql, params)

    def commit(self):
        self._state["commits"] += 1
        if self._fail_commit:
            raise sqlite3.OperationalError("falha controlada no commit boleto")
        return self._conn.commit()

    def rollback(self):
        self._state["rollbacks"] += 1
        return self._conn.rollback()

    def close(self):
        self._state["closes"] += 1
        self._state["open"] -= 1
        return self._conn.close()


def _install_boleto_update_spy(monkeypatch, isolated_app, fail_execute=False, fail_commit=False):
    state = {"open": 0, "update_executes": 0, "commits": 0, "rollbacks": 0, "closes": 0}

    def tracked_get_db(company=None):
        assert company in (None, "raios")
        return _TrackedBoletoConnection(
            isolated_app.db_paths["raios"],
            state,
            fail_execute=fail_execute,
            fail_commit=fail_commit,
        )

    monkeypatch.setattr(isolated_app.module, "get_db", tracked_get_db)
    monkeypatch.setattr(isolated_app.module, "require_editor", lambda token: {"username": "editor", "role": "editor"})
    return state


def _seed_boleto_sales(test_client, token, company="raios"):
    fixtures = [
        {
            "client": "Cliente Boleto Pendente",
            "nf_number": "BOL-PENDENTE",
            "sale_date": "2026-08-01",
            "total": 100,
            "unit_price": 100,
        },
        {
            "client": "Cliente Boleto Pago",
            "nf_number": "BOL-PAGO",
            "sale_date": "2026-08-02",
            "total": 200,
            "unit_price": 200,
        },
        {
            "client": "Cliente Boleto Vencido",
            "nf_number": "BOL-VENCIDO",
            "sale_date": "2026-08-03",
            "total": 300,
            "unit_price": 300,
        },
        {
            "client": "Cliente Boleto Hoje",
            "nf_number": "BOL-HOJE",
            "sale_date": "2026-08-04",
            "total": 400,
            "unit_price": 400,
        },
    ]
    for item in fixtures:
        _create_sale(test_client, token, company=company, **item)
    rows = _list_boletos(test_client, token, company, "?year=2026&month=8")
    return {row["client"]: row for row in rows}


def test_update_boleto_transaction_success_persists_commit_close_and_route_contract(isolated_app, monkeypatch):
    token = _login(isolated_app.client)
    boleto = _seed_boleto_sales(isolated_app.client, token)["Cliente Boleto Pendente"]

    response = isolated_app.client.put(
        f"/api/boletos/{boleto['id']}",
        headers=_headers(token),
        json={
            "due_date": "2026-08-30",
            "status": "pago",
            "paid_date": "2026-08-31",
            "notes": "pago pela rota",
            "total_val": 123.45,
        },
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}
    persisted = _read_boleto(isolated_app.db_paths["raios"], boleto["id"])
    assert persisted["due_date"] == "2026-08-30"
    assert persisted["status"] == "pago"
    assert persisted["paid_date"] == "2026-08-31"
    assert persisted["notes"] == "pago pela rota"
    assert persisted["total_val"] == 123.45

    state = _install_boleto_update_spy(monkeypatch, isolated_app)
    result = isolated_app.module.update_boleto(
        boleto["id"],
        {
            "due_date": "2026-09-01",
            "status": "pendente",
            "paid_date": "",
            "notes": "volta pelo spy",
            "total_val": 222.22,
        },
        x_token="token",
    )

    assert result == {"ok": True}
    assert state == {"open": 0, "update_executes": 1, "commits": 1, "rollbacks": 0, "closes": 1}
    persisted = _read_boleto(isolated_app.db_paths["raios"], boleto["id"])
    assert persisted["due_date"] == "2026-09-01"
    assert persisted["status"] == "pendente"
    assert persisted["paid_date"] == ""
    assert persisted["notes"] == "volta pelo spy"
    assert persisted["total_val"] == 222.22


def test_update_boleto_rolls_back_closes_and_preserves_data_when_execute_fails(isolated_app, monkeypatch):
    token = _login(isolated_app.client)
    boleto = _seed_boleto_sales(isolated_app.client, token)["Cliente Boleto Pendente"]
    original = _read_boleto(isolated_app.db_paths["raios"], boleto["id"])
    state = _install_boleto_update_spy(monkeypatch, isolated_app, fail_execute=True)

    with pytest.raises(sqlite3.OperationalError, match="falha controlada no update boleto"):
        isolated_app.module.update_boleto(
            boleto["id"],
            {"status": "pago", "paid_date": "2026-08-31", "total_val": 999.99},
            x_token="token",
        )

    assert state == {"open": 0, "update_executes": 1, "commits": 0, "rollbacks": 1, "closes": 1}
    assert _read_boleto(isolated_app.db_paths["raios"], boleto["id"]) == original
    _write_boleto_probe(isolated_app.db_paths["raios"], boleto["id"], "probe apos execute")
    assert _read_boleto(isolated_app.db_paths["raios"], boleto["id"])["notes"] == "probe apos execute"


def test_update_boleto_rolls_back_closes_and_preserves_data_when_commit_fails(isolated_app, monkeypatch):
    token = _login(isolated_app.client)
    boleto = _seed_boleto_sales(isolated_app.client, token)["Cliente Boleto Pendente"]
    original = _read_boleto(isolated_app.db_paths["raios"], boleto["id"])
    state = _install_boleto_update_spy(monkeypatch, isolated_app, fail_commit=True)

    with pytest.raises(sqlite3.OperationalError, match="falha controlada no commit boleto"):
        isolated_app.module.update_boleto(
            boleto["id"],
            {"status": "pago", "paid_date": "2026-08-31", "total_val": 999.99},
            x_token="token",
        )

    assert state == {"open": 0, "update_executes": 1, "commits": 1, "rollbacks": 1, "closes": 1}
    assert _read_boleto(isolated_app.db_paths["raios"], boleto["id"]) == original
    _write_boleto_probe(isolated_app.db_paths["raios"], boleto["id"], "probe apos commit")
    assert _read_boleto(isolated_app.db_paths["raios"], boleto["id"])["notes"] == "probe apos commit"


def test_update_boleto_preserves_missing_id_success_contract(isolated_app):
    token = _login(isolated_app.client)

    response = isolated_app.client.put(
        "/api/boletos/boleto-inexistente-passo-120",
        headers=_headers(token),
        json={"status": "pago", "paid_date": "2026-08-31"},
    )

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def test_update_boleto_auth_failure_happens_before_opening_connection(isolated_app, monkeypatch):
    opened = []

    def forbidden_require_editor(token):
        raise isolated_app.module.HTTPException(403, "bloqueado antes do banco")

    def forbidden_get_db(company=None):
        opened.append(company)
        raise AssertionError("get_db nao deveria ser chamado")

    monkeypatch.setattr(isolated_app.module, "require_editor", forbidden_require_editor)
    monkeypatch.setattr(isolated_app.module, "get_db", forbidden_get_db)

    with pytest.raises(isolated_app.module.HTTPException) as excinfo:
        isolated_app.module.update_boleto(
            "boleto-qualquer",
            {"status": "pago"},
            x_token="token-invalido",
        )

    assert excinfo.value.status_code == 403
    assert excinfo.value.detail == "bloqueado antes do banco"
    assert opened == []


def test_boletos_list_filters_summary_paid_and_items(isolated_app):
    token = _login(isolated_app.client)
    today = datetime.now().date()
    boleto_by_client = _seed_boleto_sales(isolated_app.client, token)

    assert set(boleto_by_client) == {
        "Cliente Boleto Pendente",
        "Cliente Boleto Pago",
        "Cliente Boleto Vencido",
        "Cliente Boleto Hoje",
    }
    assert boleto_by_client["Cliente Boleto Pendente"]["status"] == "pendente"
    assert boleto_by_client["Cliente Boleto Pendente"]["due_date"] is None
    assert boleto_by_client["Cliente Boleto Pendente"]["item_count"] == 1
    assert boleto_by_client["Cliente Boleto Pendente"]["total_val"] == 100

    _update_boleto(
        isolated_app.client,
        token,
        boleto_by_client["Cliente Boleto Pago"]["id"],
        status="pago",
        paid_date=today.strftime("%Y-%m-%d"),
        due_date=(today - timedelta(days=5)).strftime("%Y-%m-%d"),
        notes="pago no teste",
    )
    _update_boleto(
        isolated_app.client,
        token,
        boleto_by_client["Cliente Boleto Vencido"]["id"],
        due_date=(today - timedelta(days=1)).strftime("%Y-%m-%d"),
    )
    _update_boleto(
        isolated_app.client,
        token,
        boleto_by_client["Cliente Boleto Hoje"]["id"],
        due_date=today.strftime("%Y-%m-%d"),
    )

    all_rows = _list_boletos(isolated_app.client, token, query="?year=2026&month=8")
    assert len(all_rows) == 4

    pending_rows = _list_boletos(
        isolated_app.client,
        token,
        query="?year=2026&month=8&status=pendente",
    )
    assert {row["client"] for row in pending_rows} == {
        "Cliente Boleto Pendente",
        "Cliente Boleto Vencido",
        "Cliente Boleto Hoje",
    }

    paid_rows = _list_boletos(
        isolated_app.client,
        token,
        query="?year=2026&month=8&status=pago",
    )
    assert [row["client"] for row in paid_rows] == ["Cliente Boleto Pago"]
    assert paid_rows[0]["paid_date"] == today.strftime("%Y-%m-%d")

    search_rows = _list_boletos(
        isolated_app.client,
        token,
        query="?year=2026&month=8&search=Vencido",
    )
    assert [row["client"] for row in search_rows] == ["Cliente Boleto Vencido"]
    assert search_rows[0]["is_overdue"] is True

    due_today_rows = [
        row for row in all_rows if row["client"] == "Cliente Boleto Hoje"
    ]
    assert due_today_rows[0]["is_due_today"] is True

    summary = isolated_app.client.get(
        "/api/boletos/summary",
        headers=_headers(token),
    )
    assert summary.status_code == 200
    assert summary.json() == {
        "total_pendente": 800,
        "total_pago": 200,
        "total_pago_mes": 200,
        "vencidos": 1,
        "vence_hoje": 1,
    }

    paid = isolated_app.client.get(
        "/api/boletos/paid",
        headers=_headers(token),
    )
    assert paid.status_code == 200
    paid_body = paid.json()
    assert len(paid_body) == 1
    assert paid_body[0]["month"] == today.strftime("%Y-%m")
    assert paid_body[0]["total"] == 200
    assert paid_body[0]["count"] == 1
    assert paid_body[0]["boletos"][0]["client"] == "Cliente Boleto Pago"

    items = isolated_app.client.get(
        f"/api/boletos/{boleto_by_client['Cliente Boleto Pago']['id']}/items",
        headers=_headers(token),
    )
    assert items.status_code == 200
    assert [row["nf_number"] for row in items.json()] == ["BOL-PAGO"]


def test_boletos_period_year_month_and_clients_config(isolated_app):
    token = _login(isolated_app.client)
    _create_sale(
        isolated_app.client,
        token,
        client="Cliente Boleto Agosto",
        nf_number="BOL-AGO",
        sale_date="2026-08-10",
        total=111,
        unit_price=111,
    )
    _create_sale(
        isolated_app.client,
        token,
        client="Cliente Boleto Setembro",
        nf_number="BOL-SET",
        sale_date="2026-09-10",
        total=222,
        unit_price=222,
    )

    august = _list_boletos(isolated_app.client, token, query="?year=2026&month=8")
    assert [row["client"] for row in august] == ["Cliente Boleto Agosto"]

    whole_year = _list_boletos(isolated_app.client, token, query="?year=2026")
    assert {row["client"] for row in whole_year} == {
        "Cliente Boleto Agosto",
        "Cliente Boleto Setembro",
    }

    config_before = isolated_app.client.get(
        "/api/boletos/clients-config",
        headers=_headers(token),
    )
    assert config_before.status_code == 200
    assert config_before.json()["configured"] is False
    assert {row["name"] for row in config_before.json()["clients"]} == {
        "Cliente Boleto Agosto",
        "Cliente Boleto Setembro",
    }

    config_update = isolated_app.client.put(
        "/api/boletos/clients-config",
        headers=_headers(token),
        json={"enabled": ["Cliente Boleto Setembro"]},
    )
    assert config_update.status_code == 200
    assert config_update.json() == {"ok": True}

    config_after = isolated_app.client.get(
        "/api/boletos/clients-config",
        headers=_headers(token),
    )
    assert config_after.status_code == 200
    assert config_after.json()["configured"] is True
    assert {
        row["name"]: row["enabled"] for row in config_after.json()["clients"]
    } == {
        "Cliente Boleto Agosto": False,
        "Cliente Boleto Setembro": True,
    }

    filtered = _list_boletos(isolated_app.client, token, query="?year=2026")
    assert [row["client"] for row in filtered] == ["Cliente Boleto Setembro"]


def test_boletos_authentication_and_role_permissions(isolated_app):
    token = _login(isolated_app.client)
    boleto = _seed_boleto_sales(isolated_app.client, token)["Cliente Boleto Pendente"]

    without_token = isolated_app.client.get("/api/boletos")
    assert without_token.status_code == 401

    update_without_token = isolated_app.client.put(
        f"/api/boletos/{boleto['id']}",
        json={"status": "pago"},
    )
    assert update_without_token.status_code == 401

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    viewer_id = str(uuid.uuid4())
    editor_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO users(id, username, password_hash, full_name, role, active) VALUES(?,?,?,?,?,1)",
        (
            viewer_id,
            "viewer_boletos",
            isolated_app.module.hash_password("viewer123"),
            "Viewer Boletos",
            "viewer",
        ),
    )
    conn.execute(
        "INSERT INTO users(id, username, password_hash, full_name, role, active) VALUES(?,?,?,?,?,1)",
        (
            editor_id,
            "editor_boletos",
            isolated_app.module.hash_password("editor123"),
            "Editor Boletos",
            "editor",
        ),
    )
    conn.execute(
        "INSERT OR REPLACE INTO settings(key,value) VALUES('tab_permissions',?)",
        (json.dumps({"viewer": [], "editor": [], "admin": []}),),
    )
    conn.commit()
    conn.close()

    viewer_token = _login(isolated_app.client, "viewer_boletos", "viewer123")
    editor_token = _login(isolated_app.client, "editor_boletos", "editor123")

    viewer_read = isolated_app.client.get(
        "/api/boletos?year=2026&month=8",
        headers=_headers(viewer_token),
    )
    assert viewer_read.status_code == 200

    viewer_update = isolated_app.client.put(
        f"/api/boletos/{boleto['id']}",
        headers=_headers(viewer_token),
        json={"status": "pago"},
    )
    assert viewer_update.status_code == 403

    editor_update = isolated_app.client.put(
        f"/api/boletos/{boleto['id']}",
        headers=_headers(editor_token),
        json={"status": "pago", "paid_date": "2026-08-20"},
    )
    assert editor_update.status_code == 200
    assert editor_update.json() == {"ok": True}

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    conn.execute(
        "INSERT OR REPLACE INTO settings(key,value) VALUES('tab_permissions',?)",
        (json.dumps({"viewer": ["produtos"], "editor": [], "admin": []}),),
    )
    conn.commit()
    conn.close()

    restrictive_read = isolated_app.client.get(
        "/api/boletos?year=2026&month=8",
        headers=_headers(viewer_token),
    )
    assert restrictive_read.status_code == 200


def test_boletos_are_isolated_by_x_company(isolated_app):
    token = _login(isolated_app.client)

    _create_sale(
        isolated_app.client,
        token,
        company="raios",
        client="Cliente Boleto Raios",
        nf_number="BOL-RAIOS",
        total=123,
        unit_price=123,
    )
    _create_sale(
        isolated_app.client,
        token,
        company="estrada",
        client="Cliente Boleto Estrada",
        nf_number="BOL-ESTRADA",
        total=456,
        unit_price=456,
    )

    raios_rows = _list_boletos(
        isolated_app.client,
        token,
        company="raios",
        query="?year=2026&month=8",
    )
    assert [row["client"] for row in raios_rows] == ["Cliente Boleto Raios"]

    estrada_rows = _list_boletos(
        isolated_app.client,
        token,
        company="estrada",
        query="?year=2026&month=8",
    )
    assert [row["client"] for row in estrada_rows] == ["Cliente Boleto Estrada"]
