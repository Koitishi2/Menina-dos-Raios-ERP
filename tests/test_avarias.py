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


def _sale_payload(**overrides):
    payload = {
        "sale_type": "NF",
        "sale_date": "2026-08-05",
        "sale_time": "08:00",
        "client": "Cliente Avaria",
        "product": "Produto Venda",
        "nf_number": "AVR-VENDA-001",
        "quantity": 1,
        "unit_price": 100,
        "total": 100,
        "notes": "venda temporaria para risco de avaria",
        "delivery_person": "Lucas",
        "plate": "AVR-0001",
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


def _parse_items_by_key(items):
    return {item["key"]: item for item in items}


def test_parse_avaria_text_valid_multiple_products_quantities_and_values(isolated_app):
    prices = {
        "MAC_VACUO": 7.5,
        "ALHO_250G": 12.0,
        "PRE_COZIDA": 10.0,
        "MAC_CHIPS": 10.0,
    }

    total, items = isolated_app.module.parse_avaria_text(
        "2 vacuo, 3 alho; 1 cozida - 4 mac chips",
        prices,
    )

    by_key = _parse_items_by_key(items)
    assert set(by_key) == {"MAC_VACUO", "ALHO_250G", "PRE_COZIDA", "MAC_CHIPS"}
    assert by_key["MAC_VACUO"]["qty"] == 2
    assert by_key["MAC_VACUO"]["price"] == 7.5
    assert by_key["MAC_VACUO"]["value"] == 15
    assert by_key["ALHO_250G"]["qty"] == 3
    assert by_key["ALHO_250G"]["value"] == 36
    assert by_key["PRE_COZIDA"]["qty"] == 1
    assert by_key["PRE_COZIDA"]["value"] == 10
    assert by_key["MAC_CHIPS"]["qty"] == 4
    assert by_key["MAC_CHIPS"]["value"] == 40
    assert total == 101


def test_parse_avaria_text_accented_and_mojibake_variants_current_behavior(isolated_app):
    prices = {
        "MAC_VACUO": 7.5,
        "PRE_COZIDA": 10.0,
        "ALHO_250G": 12.0,
    }

    accented_total, accented_items = isolated_app.module.parse_avaria_text(
        "2 vácuo, 1 pré cozida, 2 alhos",
        prices,
    )
    accented_by_key = _parse_items_by_key(accented_items)

    mojibake_total, mojibake_items = isolated_app.module.parse_avaria_text(
        "2 vÃ¡cuo, 1 prÃ© cozida",
        prices,
    )
    mojibake_by_key = _parse_items_by_key(mojibake_items)

    assert accented_by_key["MAC_VACUO"]["qty"] == 2
    assert accented_by_key["PRE_COZIDA"]["qty"] == 1
    assert accented_by_key["ALHO_250G"]["qty"] == 2
    assert accented_total == 49

    # Caracterizacao atual: mojibake de vacuo nao foi ampliado nesta fase.
    assert "MAC_VACUO" not in mojibake_by_key
    assert mojibake_by_key["PRE_COZIDA"]["qty"] == 1
    assert mojibake_total == 10


def test_parse_avaria_text_unknown_empty_and_incomplete_text(isolated_app):
    prices = {"MAC_VACUO": 7.5, "ALHO_250G": 12.0}

    assert isolated_app.module.parse_avaria_text("", prices) == (0.0, [])
    assert isolated_app.module.parse_avaria_text("0", prices) == (0.0, [])
    assert isolated_app.module.parse_avaria_text("nan", prices) == (0.0, [])
    assert isolated_app.module.parse_avaria_text("macaxeira sem numero", prices) == (0.0, [])
    assert isolated_app.module.parse_avaria_text("2 produto desconhecido", prices) == (0.0, [])


def test_avaria_parse_endpoint_and_missing_parse_preview_endpoint(isolated_app):
    token = _login(isolated_app.client)

    response = isolated_app.client.post(
        "/api/avaria/parse",
        headers=_headers(token),
        json={"text": "2 vacuo, 3 alho"},
    )
    assert response.status_code == 200
    body = response.json()
    by_key = _parse_items_by_key(body["items"])
    assert body["text"] == "2 vacuo, 3 alho"
    assert body["total"] == 51
    assert by_key["MAC_VACUO"]["qty"] == 2
    assert by_key["ALHO_250G"]["qty"] == 3

    no_token = isolated_app.client.post(
        "/api/avaria/parse",
        json={"text": "2 vacuo"},
    )
    assert no_token.status_code == 401

    preview = isolated_app.client.post(
        "/api/avaria/parse-preview",
        headers=_headers(token),
        json={"text": "2 vacuo"},
    )
    # Nao ha rota explicita parse-preview; o catch-all GET gera 405 para POST.
    assert preview.status_code == 405


def test_avarias_client_risk_summary_ranking_permissions_and_filter(isolated_app):
    token = _login(isolated_app.client)
    _create_sale(
        isolated_app.client,
        token,
        client="Cliente Risco Alto",
        sale_type="NF",
        product="Produto Venda",
        sale_date="2026-08-01",
        total=1000,
        unit_price=1000,
    )
    _create_sale(
        isolated_app.client,
        token,
        client="Cliente Risco Alto",
        sale_type="AVARIA",
        product="Macaxeira a Vácuo",
        sale_date="2026-08-02",
        quantity=-10,
        unit_price=7.5,
        total=-150,
    )
    _create_sale(
        isolated_app.client,
        token,
        client="Cliente Risco Baixo",
        sale_type="NF",
        product="Produto Venda",
        sale_date="2026-08-03",
        total=2000,
        unit_price=2000,
    )
    _create_sale(
        isolated_app.client,
        token,
        client="Cliente Risco Baixo",
        sale_type="AVARIA",
        product="Alho 250g",
        sale_date="2026-08-04",
        quantity=-1,
        unit_price=12,
        total=-50,
    )

    response = isolated_app.client.get(
        "/api/avarias/client-risk?year=2026&month=8",
        headers=_headers(token),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["summary"] == {
        "total_avaria": 200,
        "total_vendas": 3000,
        "taxa_geral": 6.67,
        "clientes_afetados": 2,
        "ocorrencias": 2,
    }
    assert [row["client"] for row in body["clients"]] == [
        "Cliente Risco Alto",
        "Cliente Risco Baixo",
    ]
    assert body["clients"][0]["avTotal"] == 150
    assert body["clients"][0]["saleTotal"] == 1000
    assert body["clients"][0]["rate"] == 15
    assert body["clients"][0]["levelLabel"] == "Alto risco"
    assert {row["month"] for row in body["trend"]} == {"08"}

    filtered = isolated_app.client.get(
        "/api/avarias/client-risk?year=2026&month=8&client=Cliente Risco Baixo",
        headers=_headers(token),
    )
    assert filtered.status_code == 200
    assert [row["client"] for row in filtered.json()["clients"]] == ["Cliente Risco Baixo"]

    no_token = isolated_app.client.get("/api/avarias/client-risk?year=2026&month=8")
    assert no_token.status_code == 401

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    viewer_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO users(id, username, password_hash, full_name, role, active) VALUES(?,?,?,?,?,1)",
        (
            viewer_id,
            "viewer_avarias",
            isolated_app.module.hash_password("viewer123"),
            "Viewer Avarias",
            "viewer",
        ),
    )
    conn.execute(
        "INSERT OR REPLACE INTO settings(key,value) VALUES('tab_permissions',?)",
        (json.dumps({"viewer": [], "editor": [], "admin": []}),),
    )
    conn.commit()
    conn.close()

    viewer_token = _login(isolated_app.client, "viewer_avarias", "viewer123")
    viewer_read = isolated_app.client.get(
        "/api/avarias/client-risk?year=2026&month=8",
        headers=_headers(viewer_token),
    )
    assert viewer_read.status_code == 200

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    conn.execute(
        "INSERT OR REPLACE INTO settings(key,value) VALUES('tab_permissions',?)",
        (json.dumps({"viewer": ["produtos"], "editor": [], "admin": []}),),
    )
    conn.commit()
    conn.close()

    restrictive_read = isolated_app.client.get(
        "/api/avarias/client-risk?year=2026&month=8",
        headers=_headers(viewer_token),
    )
    assert restrictive_read.status_code == 200


def test_avarias_client_risk_isolated_by_x_company(isolated_app):
    token = _login(isolated_app.client)
    _create_sale(
        isolated_app.client,
        token,
        company="raios",
        client="Cliente Avaria Raios",
        sale_type="NF",
        sale_date="2026-08-01",
        total=1000,
        unit_price=1000,
    )
    _create_sale(
        isolated_app.client,
        token,
        company="raios",
        client="Cliente Avaria Raios",
        sale_type="AVARIA",
        sale_date="2026-08-02",
        product="Alho 250g",
        quantity=-1,
        unit_price=12,
        total=-100,
    )
    _create_sale(
        isolated_app.client,
        token,
        company="estrada",
        client="Cliente Avaria Estrada",
        sale_type="NF",
        sale_date="2026-08-01",
        total=2000,
        unit_price=2000,
    )
    _create_sale(
        isolated_app.client,
        token,
        company="estrada",
        client="Cliente Avaria Estrada",
        sale_type="AVARIA",
        sale_date="2026-08-02",
        product="Alho 250g",
        quantity=-1,
        unit_price=12,
        total=-200,
    )

    raios = isolated_app.client.get(
        "/api/avarias/client-risk?year=2026&month=8",
        headers=_headers(token, "raios"),
    )
    assert raios.status_code == 200
    assert [row["client"] for row in raios.json()["clients"]] == ["Cliente Avaria Raios"]
    assert raios.json()["summary"]["total_avaria"] == 100

    estrada = isolated_app.client.get(
        "/api/avarias/client-risk?year=2026&month=8",
        headers=_headers(token, "estrada"),
    )
    assert estrada.status_code == 200
    assert [row["client"] for row in estrada.json()["clients"]] == ["Cliente Avaria Estrada"]
    assert estrada.json()["summary"]["total_avaria"] == 200
