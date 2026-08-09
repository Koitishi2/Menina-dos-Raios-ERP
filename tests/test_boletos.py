import json
import sqlite3
import uuid
from datetime import datetime, timedelta


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
