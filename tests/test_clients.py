import json
import sqlite3
import uuid


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


def _client_payload(**overrides):
    payload = {
        "name": "Cliente Teste Cadastro",
        "cnpj": "12.345.678/0001-90",
        "cpf": "",
        "phone": "+55 95 99999-0000",
        "email": "cliente.teste@example.com",
        "address": "Rua de Teste, 123",
        "city": "Boa Vista",
        "notes": "observacao cliente temporario",
    }
    payload.update(overrides)
    return payload


def _sale_payload(**overrides):
    payload = {
        "sale_type": "NF",
        "sale_date": "2026-01-10",
        "sale_time": "08:00",
        "client": "Cliente Teste Relatorio",
        "product": "Produto Cliente Alpha",
        "nf_number": "CLI-001",
        "quantity": 10,
        "unit_price": 10,
        "notes": "venda de caracterizacao de cliente",
        "delivery_person": "Lucas",
        "plate": "CLI-0001",
        "source": "manual",
    }
    payload.update(overrides)
    return payload


def _create_client(test_client, token, company="raios", **overrides):
    response = test_client.post(
        "/api/clients",
        headers=_headers(token, company),
        json=_client_payload(**overrides),
    )
    assert response.status_code == 200
    return response.json()


def _create_sale(test_client, token, company="raios", **overrides):
    response = test_client.post(
        "/api/sales",
        headers=_headers(token, company),
        json=_sale_payload(**overrides),
    )
    assert response.status_code == 200
    return response.json()


def test_clients_list_search_create_update_and_soft_delete(isolated_app):
    token = _login(isolated_app.client)

    created = _create_client(isolated_app.client, token)
    assert created["id"]
    assert created["name"] == "Cliente Teste Cadastro"
    assert created["cnpj"] == "12345678000190"
    assert created["created_by"] == "admin"

    for term in ["Teste Cadastro", "12345678000190", "99999"]:
        response = isolated_app.client.get(
            f"/api/clients?search={term}",
            headers=_headers(token),
        )
        assert response.status_code == 200
        assert [row["id"] for row in response.json()] == [created["id"]]

    update = isolated_app.client.put(
        f"/api/clients/{created['id']}",
        headers=_headers(token),
        json={
            "name": "Cliente Teste Cadastro Editado",
            "cnpj": "98.765.432/0001-10",
            "phone": "+55 95 98888-0000",
            "email": "editado@example.com",
            "notes": "cliente editado",
        },
    )
    assert update.status_code == 200
    assert update.json() == {"ok": True}

    after_update = isolated_app.client.get(
        "/api/clients?search=Cadastro Editado",
        headers=_headers(token),
    )
    assert after_update.status_code == 200
    rows = after_update.json()
    assert len(rows) == 1
    assert rows[0]["id"] == created["id"]
    assert rows[0]["cnpj"] == "98765432000110"
    assert rows[0]["phone"] == "+55 95 98888-0000"

    deleted = isolated_app.client.delete(
        f"/api/clients/{created['id']}",
        headers=_headers(token),
    )
    assert deleted.status_code == 200
    assert deleted.json() == {"ok": True}

    after_delete = isolated_app.client.get(
        "/api/clients?search=Cadastro Editado",
        headers=_headers(token),
    )
    assert after_delete.status_code == 200
    assert after_delete.json() == []


def test_clients_without_sales_stats_and_monthly_report(isolated_app):
    token = _login(isolated_app.client)
    created = _create_client(
        isolated_app.client,
        token,
        name="Cliente Sem Vendas",
        cnpj="11.111.111/0001-11",
    )

    stats_response = isolated_app.client.get(
        f"/api/clients/{created['id']}/stats",
        headers=_headers(token),
    )
    assert stats_response.status_code == 200
    stats_body = stats_response.json()
    assert stats_body["client"]["id"] == created["id"]
    assert stats_body["stats"]["total_sales"] == 0
    assert stats_body["stats"]["total_value"] is None
    assert stats_body["stats"]["avg_ticket"] is None
    assert stats_body["stats"]["last_purchase"] is None
    assert stats_body["by_type"] == []
    assert stats_body["by_product"] == []
    assert stats_body["monthly"] == []

    report_response = isolated_app.client.get(
        f"/api/clients/{created['id']}/monthly-report?start_month=2026-01&end_month=2026-03",
        headers=_headers(token),
    )
    assert report_response.status_code == 200
    report_body = report_response.json()
    assert report_body["client"]["id"] == created["id"]
    assert report_body == {
        "client": report_body["client"],
        "start_month": "2026-01",
        "end_month": "2026-03",
        "summary": {
            "total_value": 0,
            "records": 0,
            "quantity": 0,
            "active_months": 0,
        },
        "monthly": [],
        "products": [],
        "sales": [],
    }
    assert "totals" not in report_body
    assert report_body["monthly"] == []
    assert report_body["products"] == []
    assert report_body["sales"] == []


def test_clients_stats_monthly_report_and_client_sales_multiple_months(isolated_app):
    token = _login(isolated_app.client)
    created = _create_client(
        isolated_app.client,
        token,
        name="Cliente Teste Relatorio",
        cnpj="22.222.222/0001-22",
    )
    sales = [
        _create_sale(
            isolated_app.client,
            token,
            sale_type="NF",
            sale_date="2026-01-10",
            sale_time="08:00",
            product="Produto Cliente Alpha",
            nf_number="CLI-001",
            quantity=10,
            unit_price=10,
        ),
        _create_sale(
            isolated_app.client,
            token,
            sale_type="PR",
            sale_date="2026-02-11",
            sale_time="09:00",
            product="Produto Cliente Beta",
            nf_number="CLI-002",
            quantity=20,
            unit_price=10,
        ),
        _create_sale(
            isolated_app.client,
            token,
            sale_type="AVULSO",
            sale_date="2026-03-12",
            sale_time="10:00",
            product="Produto Cliente Alpha",
            nf_number="CLI-003",
            quantity=5,
            unit_price=10,
        ),
        _create_sale(
            isolated_app.client,
            token,
            sale_type="AVARIA",
            sale_date="2026-02-15",
            sale_time="11:00",
            product="Produto Cliente Avaria",
            nf_number="CLI-AVARIA",
            quantity=9,
            unit_price=111,
        ),
    ]

    stats_response = isolated_app.client.get(
        f"/api/clients/{created['id']}/stats",
        headers=_headers(token),
    )
    assert stats_response.status_code == 200
    stats_body = stats_response.json()
    assert stats_body["stats"]["total_sales"] == 3
    assert stats_body["stats"]["total_value"] == 350
    assert stats_body["stats"]["avg_ticket"] == 350 / 3
    assert stats_body["stats"]["first_purchase"] == "2026-01-10"
    assert stats_body["stats"]["last_purchase"] == "2026-03-12"
    assert stats_body["stats"]["active_months"] == 3
    assert {row["sale_type"]: row["cnt"] for row in stats_body["by_type"]} == {
        "AVULSO": 1,
        "NF": 1,
        "PR": 1,
    }
    assert [row["month"] for row in stats_body["monthly"]] == [
        "2026-03",
        "2026-02",
        "2026-01",
    ]
    assert "Produto Cliente Avaria" not in {
        row["product"] for row in stats_body["by_product"]
    }

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    sales_count_before_invalid_range = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    conn.close()

    invalid_range = isolated_app.client.get(
        f"/api/clients/{created['id']}/monthly-report?start_month=2026-03&end_month=2026-01",
        headers=_headers(token),
    )
    assert invalid_range.status_code == 400
    assert "detail" in invalid_range.json()

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    sales_count_after_invalid_range = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    conn.close()
    assert sales_count_after_invalid_range == sales_count_before_invalid_range

    report_response = isolated_app.client.get(
        f"/api/clients/{created['id']}/monthly-report?start_month=2026-01&end_month=2026-03",
        headers=_headers(token),
    )
    assert report_response.status_code == 200
    report_body = report_response.json()
    assert report_body["start_month"] == "2026-01"
    assert report_body["end_month"] == "2026-03"
    assert report_body["summary"]["records"] == 3
    assert report_body["summary"]["active_months"] == 3
    assert report_body["summary"]["quantity"] == 35
    assert report_body["summary"]["total_value"] == 350
    assert [row["month"] for row in report_body["monthly"]] == [
        "2026-01",
        "2026-02",
        "2026-03",
    ]
    assert {row["product"] for row in report_body["products"]} == {
        "Produto Cliente Alpha",
        "Produto Cliente Beta",
    }
    assert {row["nf_number"] for row in report_body["sales"]} == {
        "CLI-001",
        "CLI-002",
        "CLI-003",
    }

    client_sales = isolated_app.client.get(
        f"/api/clients/{created['id']}/sales?limit=2",
        headers=_headers(token),
    )
    assert client_sales.status_code == 200
    assert [row["id"] for row in client_sales.json()] == [
        sales[2]["id"],
        sales[3]["id"],
    ]


def test_clients_authentication_and_role_permissions(isolated_app):
    read_without_token = isolated_app.client.get("/api/clients")
    assert read_without_token.status_code == 401

    create_without_token = isolated_app.client.post(
        "/api/clients",
        json=_client_payload(),
    )
    assert create_without_token.status_code == 401

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    viewer_id = str(uuid.uuid4())
    editor_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO users(id, username, password_hash, full_name, role, active) VALUES(?,?,?,?,?,1)",
        (
            viewer_id,
            "viewer_clientes",
            isolated_app.module.hash_password("viewer123"),
            "Viewer Clientes",
            "viewer",
        ),
    )
    conn.execute(
        "INSERT INTO users(id, username, password_hash, full_name, role, active) VALUES(?,?,?,?,?,1)",
        (
            editor_id,
            "editor_clientes",
            isolated_app.module.hash_password("editor123"),
            "Editor Clientes",
            "editor",
        ),
    )
    conn.execute(
        "INSERT OR REPLACE INTO settings(key,value) VALUES('tab_permissions',?)",
        (json.dumps({"viewer": [], "editor": [], "admin": []}),),
    )
    conn.commit()
    conn.close()

    viewer_token = _login(isolated_app.client, "viewer_clientes", "viewer123")
    editor_token = _login(isolated_app.client, "editor_clientes", "editor123")

    viewer_read = isolated_app.client.get(
        "/api/clients",
        headers=_headers(viewer_token),
    )
    assert viewer_read.status_code == 200

    viewer_create = isolated_app.client.post(
        "/api/clients",
        headers=_headers(viewer_token),
        json=_client_payload(name="Cliente Viewer Bloqueado"),
    )
    assert viewer_create.status_code == 403

    editor_create = isolated_app.client.post(
        "/api/clients",
        headers=_headers(editor_token),
        json=_client_payload(name="Cliente Editor Permitido"),
    )
    assert editor_create.status_code == 200
    assert editor_create.json()["created_by"] == "editor_clientes"

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    conn.execute(
        "INSERT OR REPLACE INTO settings(key,value) VALUES('tab_permissions',?)",
        (json.dumps({"viewer": ["produtos"], "editor": [], "admin": []}),),
    )
    conn.commit()
    conn.close()

    restrictive_read = isolated_app.client.get(
        "/api/clients",
        headers=_headers(viewer_token),
    )
    assert restrictive_read.status_code == 200


def test_clients_are_isolated_by_x_company(isolated_app):
    token = _login(isolated_app.client)

    raios_client = _create_client(
        isolated_app.client,
        token,
        company="raios",
        name="Cliente Isolado Raios",
        cnpj="33.333.333/0001-33",
    )
    estrada_client = _create_client(
        isolated_app.client,
        token,
        company="estrada",
        name="Cliente Isolado Estrada",
        cnpj="44.444.444/0001-44",
    )

    raios_rows = isolated_app.client.get(
        "/api/clients?search=Cliente Isolado",
        headers=_headers(token, "raios"),
    )
    assert raios_rows.status_code == 200
    assert [row["id"] for row in raios_rows.json()] == [raios_client["id"]]

    estrada_rows = isolated_app.client.get(
        "/api/clients?search=Cliente Isolado",
        headers=_headers(token, "estrada"),
    )
    assert estrada_rows.status_code == 200
    assert [row["id"] for row in estrada_rows.json()] == [estrada_client["id"]]
