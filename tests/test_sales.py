import json
import sqlite3
import uuid


def _login(client, username="admin", password="admin123", company="raios"):
    response = client.post(
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
        "sale_time": "08:15",
        "client": "Cliente Teste Vendas",
        "product": "Produto Teste Alpha",
        "nf_number": "NF-TST-001",
        "quantity": 2,
        "unit_price": 10,
        "notes": "observacao teste vendas",
        "delivery_person": "Lucas",
        "plate": "TST-0001",
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


def test_sales_create_read_update_and_delete_on_temp_db(isolated_app):
    token = _login(isolated_app.client)

    created = _create_sale(isolated_app.client, token)
    assert created["id"]
    assert created["sale_type"] == "NF"
    assert created["client"] == "Cliente Teste Vendas"
    assert created["total"] == 20
    assert created["created_by"] == "admin"

    listed = isolated_app.client.get(
        "/api/sales?search=NF-TST-001",
        headers=_headers(token),
    )
    assert listed.status_code == 200
    rows = listed.json()
    assert [r["id"] for r in rows] == [created["id"]]

    update = isolated_app.client.put(
        f"/api/sales/{created['id']}",
        headers=_headers(token),
        json={"quantity": 3, "unit_price": 11, "total": 33, "notes": "editado"},
    )
    assert update.status_code == 200
    assert update.json() == {"ok": True}

    after_update = isolated_app.client.get(
        "/api/sales?search=NF-TST-001",
        headers=_headers(token),
    ).json()[0]
    assert after_update["quantity"] == 3
    assert after_update["unit_price"] == 11
    assert after_update["total"] == 33
    assert after_update["notes"] == "editado"

    deleted = isolated_app.client.delete(
        f"/api/sales/{created['id']}",
        headers=_headers(token),
    )
    assert deleted.status_code == 200
    assert deleted.json() == {"ok": True}

    after_delete = isolated_app.client.get(
        "/api/sales?search=NF-TST-001",
        headers=_headers(token),
    )
    assert after_delete.status_code == 200
    assert after_delete.json() == []


def test_sales_filters_type_month_year_search_and_limit(isolated_app):
    token = _login(isolated_app.client)
    fixtures = [
        {
            "sale_type": "NF",
            "sale_date": "2026-08-10",
            "sale_time": "09:00",
            "client": "Cliente Filtro NF",
            "product": "Produto Filtro NF",
            "nf_number": "NF-FILTRO-001",
            "plate": "ABC-1111",
        },
        {
            "sale_type": "PR",
            "sale_date": "2026-08-11",
            "sale_time": "10:00",
            "client": "Cliente Filtro PR",
            "product": "Produto Filtro PR",
            "nf_number": "PR-FILTRO-001",
            "plate": "ABC-2222",
        },
        {
            "sale_type": "AVULSO",
            "sale_date": "2026-07-12",
            "sale_time": "11:00",
            "client": "Cliente Filtro Avulso",
            "product": "Produto Filtro Avulso",
            "nf_number": "AV-FILTRO-001",
            "plate": "ABC-3333",
        },
        {
            "sale_type": "AVARIA",
            "sale_date": "2026-08-13",
            "sale_time": "12:00",
            "client": "Cliente Filtro Avaria",
            "product": "Produto Filtro Avaria",
            "nf_number": "AVR-FILTRO-001",
            "plate": "PLACA-BUSCA-4444",
        },
    ]
    created = [_create_sale(isolated_app.client, token, **item) for item in fixtures]

    by_type = isolated_app.client.get("/api/sales?sale_type=PR", headers=_headers(token))
    assert by_type.status_code == 200
    assert [row["sale_type"] for row in by_type.json()] == ["PR"]

    by_month_year = isolated_app.client.get(
        "/api/sales?month=8&year=2026",
        headers=_headers(token),
    )
    assert by_month_year.status_code == 200
    assert {row["id"] for row in by_month_year.json()} == {
        created[0]["id"],
        created[1]["id"],
        created[3]["id"],
    }

    search = isolated_app.client.get(
        "/api/sales?search=PLACA-BUSCA",
        headers=_headers(token),
    )
    assert search.status_code == 200
    assert [row["id"] for row in search.json()] == [created[3]["id"]]

    limited = isolated_app.client.get("/api/sales?limit=2", headers=_headers(token))
    assert limited.status_code == 200
    assert len(limited.json()) == 2


def test_sales_requires_authentication(isolated_app):
    read_without_token = isolated_app.client.get("/api/sales")
    assert read_without_token.status_code == 401

    create_without_token = isolated_app.client.post("/api/sales", json=_sale_payload())
    assert create_without_token.status_code == 401


def test_sales_characterizes_viewer_permission_behavior(isolated_app):
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    user_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO users(id, username, password_hash, full_name, role, active) VALUES(?,?,?,?,?,1)",
        (
            user_id,
            "viewer_sem_vendas",
            isolated_app.module.hash_password("viewer123"),
            "Viewer Sem Vendas",
            "viewer",
        ),
    )
    conn.execute(
        "INSERT OR REPLACE INTO settings(key,value) VALUES('tab_permissions',?)",
        (json.dumps({"viewer": [], "editor": [], "admin": []}),),
    )
    conn.commit()
    conn.close()

    viewer_token = _login(isolated_app.client, "viewer_sem_vendas", "viewer123")

    empty_permissions_read = isolated_app.client.get(
        "/api/sales",
        headers=_headers(viewer_token),
    )
    assert empty_permissions_read.status_code == 200

    empty_permissions_create = isolated_app.client.post(
        "/api/sales",
        headers=_headers(viewer_token),
        json=_sale_payload(),
    )
    assert empty_permissions_create.status_code == 403

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    conn.execute(
        "INSERT OR REPLACE INTO settings(key,value) VALUES('tab_permissions',?)",
        (json.dumps({"viewer": ["produtos"], "editor": [], "admin": []}),),
    )
    conn.commit()
    conn.close()

    restrictive_read = isolated_app.client.get(
        "/api/sales",
        headers=_headers(viewer_token),
    )
    assert restrictive_read.status_code == 403


def test_sales_are_isolated_by_x_company(isolated_app):
    token = _login(isolated_app.client)

    raios_sale = _create_sale(
        isolated_app.client,
        token,
        company="raios",
        client="Cliente Isolado Raios",
        nf_number="ISO-RAIOS-001",
    )
    estrada_sale = _create_sale(
        isolated_app.client,
        token,
        company="estrada",
        client="Cliente Isolado Estrada",
        nf_number="ISO-ESTRADA-001",
    )

    raios_rows = isolated_app.client.get(
        "/api/sales?search=ISO-",
        headers=_headers(token, "raios"),
    )
    assert raios_rows.status_code == 200
    assert [row["id"] for row in raios_rows.json()] == [raios_sale["id"]]

    estrada_rows = isolated_app.client.get(
        "/api/sales?search=ISO-",
        headers=_headers(token, "estrada"),
    )
    assert estrada_rows.status_code == 200
    assert [row["id"] for row in estrada_rows.json()] == [estrada_sale["id"]]
