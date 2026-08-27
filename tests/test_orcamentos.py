import sqlite3
import uuid

import pytest
from fastapi.testclient import TestClient


PDF_BLOCKED_REASON = (
    "BLOQUEADO: geracao/visualizacao de PDF de orcamento e feita no frontend por impressao do navegador; "
    "nao ha rota backend JSON/PDF propria para testar sem navegador."
)


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


def _create_temp_user(isolated_app, username, password, role, company="raios"):
    conn = sqlite3.connect(isolated_app.db_paths[company])
    user_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO users(id, username, password_hash, full_name, role, active) VALUES(?,?,?,?,?,1)",
        (
            user_id,
            username,
            isolated_app.module.hash_password(password),
            f"Usuario {role} Orcamentos {company}",
            role,
        ),
    )
    conn.commit()
    conn.close()
    return user_id


def _product_payload(name=None, **overrides):
    payload = {
        "name": name or f"Produto Orcamento {uuid.uuid4().hex[:8]}",
        "code": "ORC-001",
        "unit": "und",
        "default_price": 85,
        "description": "Produto temporario de orcamento",
    }
    payload.update(overrides)
    return payload


def _quote_payload(client_name="Cliente Orcamento Padrao", **overrides):
    payload = {
        "company_key": "estrada",
        "client_name": client_name,
        "attention": "Compras",
        "client_cnpj": "00.000.000/0001-00",
        "client_ie": "ISENTO",
        "client_phone": "5595999999999",
        "client_email": "cliente@example.test",
        "client_address": "Rua Teste, 123",
        "client_district": "Centro",
        "client_city": "Boa Vista",
        "client_state": "RR",
        "client_zip": "69300-000",
        "issue_date": "2026-07-17",
        "issue_time": "10:30:00",
        "validity_days": 7,
        "delivery_deadline": "A combinar",
        "payment_terms": "Boleto 15 dias",
        "observations": "Observacao temporaria",
        "discount": 15,
        "status": "emitido",
        "items": [
            {
                "product_id": None,
                "item_order": 1,
                "code": "ORC-001",
                "description": "Item Orcamento A",
                "quantity": 2,
                "unit": "und",
                "unit_price": 100,
                "discount": 10,
            },
            {
                "product_id": None,
                "item_order": 2,
                "code": "ORC-002",
                "description": "Item Orcamento B",
                "quantity": 1,
                "unit": "kg",
                "unit_price": 50,
                "discount": 0,
            },
        ],
    }
    payload.update(overrides)
    return payload


def _post_product(test_client, token, company="raios", **overrides):
    response = test_client.post(
        "/api/orcamentos/products",
        headers=_headers(token, company),
        json=_product_payload(**overrides),
    )
    assert response.status_code == 200
    return response.json()


def _post_quote(test_client, token, company="raios", **overrides):
    response = test_client.post(
        "/api/orcamentos",
        headers=_headers(token, company),
        json=_quote_payload(**overrides),
    )
    assert response.status_code == 200
    return response.json()


def _table_count(db_path, table):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()


def _quote_db_snapshot(db_path, quote_id):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        quote = conn.execute("SELECT * FROM quotes WHERE id=?", (quote_id,)).fetchone()
        items = conn.execute(
            "SELECT * FROM quote_items WHERE quote_id=? ORDER BY item_order, id",
            (quote_id,),
        ).fetchall()
        return {
            "quote": dict(quote) if quote else None,
            "items": [dict(row) for row in items],
        }
    finally:
        conn.close()


def _assert_db_accepts_write(db_path):
    conn = sqlite3.connect(db_path, timeout=0.5)
    try:
        conn.execute("BEGIN IMMEDIATE")
        conn.rollback()
    finally:
        conn.close()


def test_quote_companies_current_metadata_structure_and_values(isolated_app):
    quote_companies = isolated_app.module._quote_companies
    companies = quote_companies()

    assert isinstance(companies, dict)
    assert list(companies.keys()) == ["estrada", "raios"]

    expected_fields = {
        "key",
        "cnpj",
        "razao_social",
        "nome_fantasia",
        "endereco",
        "cep",
        "email",
        "whatsapp",
        "logo",
    }
    assert set(companies["estrada"]) == expected_fields
    assert set(companies["raios"]) == expected_fields
    assert companies["estrada"] == {
        "key": "estrada",
        "cnpj": "63.585.166/0001-37",
        "razao_social": "J. M. de Lima",
        "nome_fantasia": "Menina da Estrada",
        "endereco": "Rua Raimundo Alves de Souza, 205 - Jardim Tropical, Boa Vista - Roraima - Brasil",
        "cep": "69314-670",
        "email": "adrianoabreub@gmail.com",
        "whatsapp": "+55 (21) 98426-1686 / (95) 99123-3960",
        "logo": "/assets/menina-estrada-logo.png",
    }
    assert companies["raios"] == {
        "key": "raios",
        "cnpj": "45.783.879/0001-23",
        "razao_social": "Menina dos Raios LTDA",
        "nome_fantasia": "Menina dos Raios",
        "endereco": "Rua Raimundo Alves de Souza, 205 - Jardim Tropical, Boa Vista - Roraima - Brasil",
        "cep": "69314-670",
        "email": "meninadosraios@gmail.com",
        "whatsapp": "+55 (95) 99123-3960 / (21) 98426-1686",
        "logo": "/assets/menina-dos-raios-logo.png",
    }


def test_quote_companies_current_calls_return_independent_dicts(isolated_app):
    quote_companies = isolated_app.module._quote_companies

    first = quote_companies()
    second = quote_companies()
    assert first == second
    assert first is not second
    assert first["estrada"] is not second["estrada"]

    first["estrada"]["nome_fantasia"] = "Mutado"
    first["nova"] = {"key": "nova"}

    fresh = quote_companies()
    assert fresh["estrada"]["nome_fantasia"] == "Menina da Estrada"
    assert "nova" not in fresh


def test_quote_company_current_normalization_fallback_identity_and_type_errors(isolated_app):
    quote_company = isolated_app.module._quote_company
    quote_companies = isolated_app.module._quote_companies
    companies = quote_companies()

    selected_default = quote_company(None)
    assert isinstance(selected_default, dict)
    assert selected_default == companies["estrada"]
    assert selected_default is not companies["estrada"]

    assert quote_company("") == companies["estrada"]
    assert quote_company("estrada") == companies["estrada"]
    assert quote_company(" ESTRADA ") == companies["estrada"]
    assert quote_company("desconhecida") == companies["estrada"]
    assert quote_company("raios") == companies["raios"]
    assert quote_company(" RAIOS ") == companies["raios"]
    assert quote_company("RaIoS") == companies["raios"]
    assert quote_company([]) == companies["estrada"]

    selected_raios = quote_company("raios")
    selected_raios["nome_fantasia"] = "Mutado"
    assert quote_company("raios")["nome_fantasia"] == "Menina dos Raios"

    with pytest.raises(AttributeError):
        quote_company(123)
    with pytest.raises(AttributeError):
        quote_company(["raios"])


def test_quote_totals_core_current_empty_single_decimal_and_defaults():
    from backend.orcamentos import quote_totals_from_items

    assert quote_totals_from_items([]) == ([], 0.0, 0.0)
    assert quote_totals_from_items(None) == ([], 0.0, 0.0)

    normalized, subtotal, total = quote_totals_from_items(
        [
            {
                "quantity": 2,
                "unit_price": 100,
                "discount": 10,
                "description": "  Item unico  ",
                "unit": "kg",
                "extra": "preservado",
            }
        ],
        discount=15,
    )
    assert subtotal == 190.0
    assert total == 175.0
    assert isinstance(subtotal, float)
    assert isinstance(total, float)
    assert normalized == [
        {
            "quantity": 2.0,
            "unit_price": 100.0,
            "discount": 10.0,
            "description": "Item unico",
            "unit": "KG",
            "extra": "preservado",
            "item_order": 1,
            "subtotal": 190.0,
        }
    ]

    decimal_items, decimal_subtotal, decimal_total = quote_totals_from_items(
        [
            {"quantity": 1.5, "unit_price": 10.05, "discount": 0},
            {"quantity": 2.5, "unit_price": 2.4, "discount": 0},
        ],
        discount=1.2,
    )
    assert decimal_subtotal == 21.075000000000003
    assert decimal_total == 19.875000000000004
    assert decimal_items[0]["subtotal"] == 15.075000000000001

    manual_items, manual_subtotal, manual_total = quote_totals_from_items(
        [
            {
                "quantity": 1,
                "unit_price": 4,
                "discount": 2.5,
                "subtotal_override": "7.5",
            }
        ],
        discount=1,
    )
    assert manual_items[0]["subtotal"] == 7.5
    assert manual_subtotal == 7.5
    assert manual_total == 6.5

    default_items, default_subtotal, default_total = quote_totals_from_items([{}])
    assert default_subtotal == 0.0
    assert default_total == 0.0
    assert default_items == [
        {
            "item_order": 1,
            "quantity": 0.0,
            "unit_price": 0.0,
            "discount": 0.0,
            "subtotal": 0.0,
            "unit": "UND",
            "description": "",
        }
    ]


def test_quote_totals_core_current_numeric_strings_order_discounts_and_negative_values():
    from backend.orcamentos import quote_totals_from_items

    normalized, subtotal, total = quote_totals_from_items(
        [
            {
                "quantity": "2",
                "unit_price": "5.5",
                "discount": "1",
                "item_order": "7",
                "unit": "cx",
                "description": 123,
                "keep": {"original": True},
            },
            {
                "quantity": "1",
                "unit_price": "3",
                "discount": "0",
                "item_order": 0,
                "unit": "",
                "description": "  teste  ",
            },
        ],
        discount="2.5",
    )
    assert subtotal == 13.0
    assert total == 10.5
    assert normalized[0]["item_order"] == 7
    assert normalized[0]["quantity"] == 2.0
    assert normalized[0]["unit_price"] == 5.5
    assert normalized[0]["discount"] == 1.0
    assert normalized[0]["subtotal"] == 10.0
    assert normalized[0]["unit"] == "CX"
    assert normalized[0]["description"] == "123"
    assert normalized[0]["keep"] == {"original": True}
    assert normalized[1]["item_order"] == 2
    assert normalized[1]["unit"] == "UND"
    assert normalized[1]["description"] == "teste"

    larger_item_discount, item_discount_subtotal, item_discount_total = quote_totals_from_items(
        [{"quantity": 1, "unit_price": 10, "discount": 20}]
    )
    assert item_discount_subtotal == 0.0
    assert item_discount_total == 0.0
    assert larger_item_discount[0]["subtotal"] == 0

    assert quote_totals_from_items([{"quantity": 1, "unit_price": 10}], discount=99)[2] == 0
    assert quote_totals_from_items([{"quantity": 1, "unit_price": 10}], discount=-5)[2] == 10.0
    assert quote_totals_from_items([{"quantity": -2, "unit_price": 10}])[1:] == (0.0, 0.0)
    assert quote_totals_from_items([{"quantity": 2, "unit_price": -10}])[1:] == (0.0, 0.0)
    assert quote_totals_from_items([{"quantity": 2, "unit_price": 10, "discount": -5}])[1:] == (25.0, 25.0)


def test_quote_totals_core_current_exceptions():
    from backend.orcamentos import QuoteItemsLimitError, quote_totals_from_items

    with pytest.raises(QuoteItemsLimitError):
        quote_totals_from_items([{} for _ in range(21)])

    for payload in (
        [{"quantity": "abc"}],
        [{"unit_price": "abc"}],
        [{"discount": "abc"}],
        [{"item_order": "abc"}],
    ):
        with pytest.raises(ValueError):
            quote_totals_from_items(payload)

    with pytest.raises(ValueError):
        quote_totals_from_items([{"quantity": 1}], discount="abc")

    for invalid_items in ({"quantity": 1}, "texto"):
        with pytest.raises(AttributeError):
            quote_totals_from_items(invalid_items)


def test_quote_totals_current_empty_single_decimal_and_defaults(isolated_app):
    quote_totals = isolated_app.module._quote_totals

    assert quote_totals([]) == ([], 0.0, 0.0)
    assert quote_totals(None) == ([], 0.0, 0.0)

    normalized, subtotal, total = quote_totals(
        [
            {
                "quantity": 2,
                "unit_price": 100,
                "discount": 10,
                "description": "  Item unico  ",
                "unit": "kg",
                "extra": "preservado",
            }
        ],
        discount=15,
    )
    assert subtotal == 190.0
    assert total == 175.0
    assert isinstance(subtotal, float)
    assert isinstance(total, float)
    assert normalized == [
        {
            "quantity": 2.0,
            "unit_price": 100.0,
            "discount": 10.0,
            "description": "Item unico",
            "unit": "KG",
            "extra": "preservado",
            "item_order": 1,
            "subtotal": 190.0,
        }
    ]

    decimal_items, decimal_subtotal, decimal_total = quote_totals(
        [
            {"quantity": 1.5, "unit_price": 10.05, "discount": 0},
            {"quantity": 2.5, "unit_price": 2.4, "discount": 0},
        ],
        discount=1.2,
    )
    assert decimal_subtotal == 21.075000000000003
    assert decimal_total == 19.875000000000004
    assert decimal_items[0]["subtotal"] == 15.075000000000001

    default_items, default_subtotal, default_total = quote_totals([{}])
    assert default_subtotal == 0.0
    assert default_total == 0.0
    assert default_items == [
        {
            "item_order": 1,
            "quantity": 0.0,
            "unit_price": 0.0,
            "discount": 0.0,
            "subtotal": 0.0,
            "unit": "UND",
            "description": "",
        }
    ]


def test_quote_totals_current_numeric_strings_order_discounts_and_negative_values(isolated_app):
    quote_totals = isolated_app.module._quote_totals

    normalized, subtotal, total = quote_totals(
        [
            {
                "quantity": "2",
                "unit_price": "5.5",
                "discount": "1",
                "item_order": "7",
                "unit": "cx",
                "description": 123,
                "keep": {"original": True},
            },
            {
                "quantity": "1",
                "unit_price": "3",
                "discount": "0",
                "item_order": 0,
                "unit": "",
                "description": "  teste  ",
            },
        ],
        discount="2.5",
    )
    assert subtotal == 13.0
    assert total == 10.5
    assert normalized[0]["item_order"] == 7
    assert normalized[0]["quantity"] == 2.0
    assert normalized[0]["unit_price"] == 5.5
    assert normalized[0]["discount"] == 1.0
    assert normalized[0]["subtotal"] == 10.0
    assert normalized[0]["unit"] == "CX"
    assert normalized[0]["description"] == "123"
    assert normalized[0]["keep"] == {"original": True}
    assert normalized[1]["item_order"] == 2
    assert normalized[1]["unit"] == "UND"
    assert normalized[1]["description"] == "teste"

    larger_item_discount, item_discount_subtotal, item_discount_total = quote_totals(
        [{"quantity": 1, "unit_price": 10, "discount": 20}]
    )
    assert item_discount_subtotal == 0.0
    assert item_discount_total == 0.0
    assert larger_item_discount[0]["subtotal"] == 0

    assert quote_totals([{"quantity": 1, "unit_price": 10}], discount=99)[2] == 0
    assert quote_totals([{"quantity": 1, "unit_price": 10}], discount=-5)[2] == 10.0
    assert quote_totals([{"quantity": -2, "unit_price": 10}])[1:] == (0.0, 0.0)
    assert quote_totals([{"quantity": 2, "unit_price": -10}])[1:] == (0.0, 0.0)
    assert quote_totals([{"quantity": 2, "unit_price": 10, "discount": -5}])[1:] == (25.0, 25.0)


def test_quote_totals_current_exceptions(isolated_app):
    quote_totals = isolated_app.module._quote_totals

    with pytest.raises(isolated_app.module.HTTPException) as too_many:
        quote_totals([{} for _ in range(21)])
    assert too_many.value.status_code == 400
    assert too_many.value.detail == "O orÃ§amento permite no mÃ¡ximo 20 itens."

    for payload in (
        [{"quantity": "abc"}],
        [{"unit_price": "abc"}],
        [{"discount": "abc"}],
        [{"item_order": "abc"}],
    ):
        with pytest.raises(ValueError):
            quote_totals(payload)

    with pytest.raises(ValueError):
        quote_totals([{"quantity": 1}], discount="abc")

    for invalid_items in ({"quantity": 1}, "texto"):
        with pytest.raises(AttributeError):
            quote_totals(invalid_items)


def test_orcamentos_company_metadata_and_pdf_backend_route_status(isolated_app):
    token = _login(isolated_app.client)

    company = isolated_app.client.get("/api/orcamentos/company", headers=_headers(token))
    assert company.status_code == 200
    body = company.json()
    assert body["default"] == "estrada"
    assert {row["key"] for row in body["companies"]} >= {"raios", "estrada"}

    route_paths = {
        route.path
        for route in isolated_app.module.app.routes
        if getattr(route, "path", "").startswith("/api/orcamentos")
    }
    assert not any("pdf" in path.lower() for path in route_paths), PDF_BLOCKED_REASON


def test_orcamento_products_seed_raios_catalog_and_keep_estrada_separate(isolated_app):
    token = _login(isolated_app.client)

    raios = isolated_app.client.get(
        "/api/orcamentos/products?company_key=raios",
        headers=_headers(token, "raios"),
    )
    estrada = isolated_app.client.get(
        "/api/orcamentos/products?company_key=estrada",
        headers=_headers(token, "raios"),
    )

    assert raios.status_code == 200
    assert estrada.status_code == 200

    raios_names = {row["name"] for row in raios.json()}
    assert {
        "Ab\u00f3bora Jacar\u00e9",
        "Alho 250g",
        "Alho KG",
        "Macaxeira a V\u00e1cuo",
        "Macaxeira Chips",
        "Macaxeira com Casca (KG)",
        "Macaxeira Processada",
        "Macaxeira Sem V\u00e1cuo",
        "Massa de Macaxeira",
        "Pasta de Alho",
        "Pr\u00e9-Cozida",
        "Uva Vit\u00f3ria",
    }.issubset(raios_names)
    assert {row["name"] for row in estrada.json()}.isdisjoint(raios_names)

    macaxeira = next(row for row in raios.json() if row["name"] == "Macaxeira a V\u00e1cuo")
    assert macaxeira["code"] == "RAI-MAC-VAC"
    assert macaxeira["unit"] == "KG"
    assert macaxeira["default_price"] == 7.5
    assert macaxeira["active"] == 1


def test_orcamento_products_crud_search_soft_delete_and_company_isolation(isolated_app):
    raios_token = _login(isolated_app.client)
    _create_temp_user(isolated_app, "admin_orc_estrada", "admin123", "admin", company="estrada")
    estrada_token = _login(isolated_app.client, "admin_orc_estrada", "admin123", company="estrada")
    raios_count_before = _table_count(isolated_app.db_paths["raios"], "quote_products")
    estrada_count_before = _table_count(isolated_app.db_paths["estrada"], "quote_products")

    raios_product = _post_product(
        isolated_app.client,
        raios_token,
        company="raios",
        name="Produto Orcamento Raios",
        code="RAI-001",
        default_price=90,
    )
    estrada_product = _post_product(
        isolated_app.client,
        estrada_token,
        company="estrada",
        name="Produto Orcamento Estrada",
        code="EST-001",
        default_price=120,
    )

    assert raios_product["unit"] == "UND"
    assert estrada_product["unit"] == "UND"
    assert _table_count(isolated_app.db_paths["raios"], "quote_products") == raios_count_before + 1
    assert _table_count(isolated_app.db_paths["estrada"], "quote_products") == estrada_count_before + 1

    raios_list = isolated_app.client.get(
        "/api/orcamentos/products?search=Produto Orcamento",
        headers=_headers(raios_token, "raios"),
    )
    estrada_list = isolated_app.client.get(
        "/api/orcamentos/products?search=Produto Orcamento",
        headers=_headers(estrada_token, "estrada"),
    )
    assert raios_list.status_code == 200
    assert estrada_list.status_code == 200
    assert [row["name"] for row in raios_list.json()] == ["Produto Orcamento Raios"]
    assert [row["name"] for row in estrada_list.json()] == ["Produto Orcamento Estrada"]

    duplicate = isolated_app.client.post(
        "/api/orcamentos/products",
        headers=_headers(raios_token),
        json=_product_payload(name="Produto Orcamento Raios"),
    )
    assert duplicate.status_code == 400

    updated = isolated_app.client.put(
        f"/api/orcamentos/products/{raios_product['id']}",
        headers=_headers(raios_token),
        json=_product_payload(
            name="Produto Orcamento Raios Editado",
            code="RAI-002",
            unit="cx",
            default_price=95.5,
            description="Descricao editada",
            active=1,
        ),
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "Produto Orcamento Raios Editado"
    assert updated.json()["unit"] == "CX"
    assert updated.json()["default_price"] == 95.5

    deleted = isolated_app.client.delete(
        f"/api/orcamentos/products/{raios_product['id']}",
        headers=_headers(raios_token),
    )
    assert deleted.status_code == 200
    assert deleted.json() == {"ok": True}

    active_after_delete = isolated_app.client.get(
        "/api/orcamentos/products?search=Raios Editado",
        headers=_headers(raios_token),
    )
    all_after_delete = isolated_app.client.get(
        "/api/orcamentos/products?active=0&search=Raios Editado",
        headers=_headers(raios_token),
    )
    assert active_after_delete.status_code == 200
    assert active_after_delete.json() == []
    assert all_after_delete.status_code == 200
    assert all_after_delete.json()[0]["active"] == 0


def test_orcamentos_create_read_list_update_delete_and_calculations(isolated_app):
    token = _login(isolated_app.client)
    product = _post_product(
        isolated_app.client,
        token,
        name="Produto Orcamento Item",
        code="ITM-001",
        default_price=100,
    )

    created = _post_quote(
        isolated_app.client,
        token,
        client_name="Cliente Orcamento CRUD",
        items=[
            {
                "product_id": product["id"],
                "item_order": 1,
                "code": product["code"],
                "description": product["description"],
                "quantity": 2,
                "unit": product["unit"],
                "unit_price": 100,
                "discount": 10,
            },
            {
                "product_id": None,
                "item_order": 2,
                "code": "SERV-001",
                "description": "Servico avulso",
                "quantity": 1,
                "unit": "serv",
                "unit_price": 50,
                "discount": 0,
            },
        ],
        discount=15,
    )
    quote = created["quote"]
    items = created["items"]
    assert quote["quote_number"] == 1
    assert quote["created_by"] == "admin"
    assert quote["subtotal"] == 240
    assert quote["discount"] == 15
    assert quote["total"] == 225
    assert len(items) == 2
    assert items[0]["subtotal"] == 190
    assert items[0]["unit"] == "UND"
    assert items[1]["subtotal"] == 50
    assert items[1]["unit"] == "SERV"

    manual_created = _post_quote(
        isolated_app.client,
        token,
        client_name="Cliente Subtotal Manual",
        items=[
            {
                "product_id": None,
                "item_order": 1,
                "code": "MANUAL-001",
                "description": "Item com subtotal manual",
                "quantity": 1,
                "unit": "kg",
                "unit_price": 4,
                "discount": 2.5,
                "subtotal_override": 7.5,
            }
        ],
        discount=0,
    )
    assert manual_created["quote"]["subtotal"] == 7.5
    assert manual_created["quote"]["total"] == 7.5
    assert manual_created["items"][0]["subtotal"] == 7.5

    quote_id = quote["id"]
    fetched = isolated_app.client.get(f"/api/orcamentos/{quote_id}", headers=_headers(token))
    listed = isolated_app.client.get(
        "/api/orcamentos?search=Cliente Orcamento CRUD",
        headers=_headers(token),
    )
    assert fetched.status_code == 200
    assert fetched.json()["company"]["key"] == "estrada"
    assert fetched.json()["quote"]["id"] == quote_id
    assert listed.status_code == 200
    assert listed.json()[0]["id"] == quote_id
    assert listed.json()[0]["total"] == 225

    updated = isolated_app.client.put(
        f"/api/orcamentos/{quote_id}",
        headers=_headers(token),
        json=_quote_payload(
            client_name="Cliente Orcamento Editado",
            company_key="raios",
            issue_date="2026-07-18",
            issue_time="11:00:00",
            discount=20,
            status="rascunho",
            items=[
                {
                    "product_id": product["id"],
                    "item_order": 1,
                    "code": "ITM-EDIT",
                    "description": "Item editado",
                    "quantity": 3,
                    "unit": "cx",
                    "unit_price": 80,
                    "discount": 5,
                }
            ],
        ),
    )
    assert updated.status_code == 200
    updated_json = updated.json()
    assert updated_json["company"]["key"] == "raios"
    assert updated_json["quote"]["client_name"] == "Cliente Orcamento Editado"
    assert updated_json["quote"]["status"] == "rascunho"
    assert updated_json["quote"]["subtotal"] == 235
    assert updated_json["quote"]["discount"] == 20
    assert updated_json["quote"]["total"] == 215
    assert len(updated_json["items"]) == 1
    assert updated_json["items"][0]["unit"] == "CX"
    assert updated_json["items"][0]["subtotal"] == 235

    deleted = isolated_app.client.delete(f"/api/orcamentos/{quote_id}", headers=_headers(token))
    after_delete = isolated_app.client.get(f"/api/orcamentos/{quote_id}", headers=_headers(token))
    db_after_delete = _quote_db_snapshot(isolated_app.db_paths["raios"], quote_id)
    assert deleted.status_code == 200
    assert deleted.json() == {"ok": True}
    assert after_delete.status_code == 404
    assert db_after_delete == {"quote": None, "items": []}


def test_orcamentos_current_validation_for_empty_unknown_and_zero_quantity_items(isolated_app):
    token = _login(isolated_app.client)

    no_items = isolated_app.client.post(
        "/api/orcamentos",
        headers=_headers(token),
        json=_quote_payload(items=[]),
    )
    no_client = isolated_app.client.post(
        "/api/orcamentos",
        headers=_headers(token),
        json=_quote_payload(client_name=""),
    )
    assert no_items.status_code == 400
    assert no_client.status_code == 400

    zero_qty_and_large_discount = isolated_app.client.post(
        "/api/orcamentos",
        headers=_headers(token),
        json=_quote_payload(
            client_name="Cliente Orcamento Item Sem Produto",
            discount=10,
            items=[
                {
                    "product_id": None,
                    "item_order": 1,
                    "code": "ZERO",
                    "description": "Quantidade zero aceita atualmente",
                    "quantity": 0,
                    "unit": "und",
                    "unit_price": 100,
                    "discount": 0,
                },
                {
                    "product_id": None,
                    "item_order": 2,
                    "code": "NEG",
                    "description": "Desconto maior que linha zera subtotal",
                    "quantity": 1,
                    "unit": "und",
                    "unit_price": 5,
                    "discount": 50,
                },
            ],
        ),
    )
    assert zero_qty_and_large_discount.status_code == 200
    body = zero_qty_and_large_discount.json()
    assert body["quote"]["subtotal"] == 0
    assert body["quote"]["discount"] == 10
    assert body["quote"]["total"] == 0
    assert body["items"][0]["product_id"] is None
    assert body["items"][0]["quantity"] == 0
    assert body["items"][0]["subtotal"] == 0
    assert body["items"][1]["subtotal"] == 0

    quotes_before = _table_count(isolated_app.db_paths["raios"], "quotes")
    items_before = _table_count(isolated_app.db_paths["raios"], "quote_items")

    # PENDENCIA: a rota deve tratar product_id inexistente e retornar erro controlado, em vez de deixar IntegrityError escapar.
    with TestClient(isolated_app.module.app, raise_server_exceptions=False) as non_raising_client:
        unknown_product = non_raising_client.post(
            "/api/orcamentos",
            headers=_headers(token),
            json=_quote_payload(
                client_name="Cliente Orcamento Produto Inexistente",
                discount=10,
                items=[
                    {
                        "product_id": 999999,
                        "item_order": 1,
                        "code": "UNKNOWN",
                        "description": "Produto inexistente dispara erro interno atualmente",
                        "quantity": 1,
                        "unit": "und",
                        "unit_price": 100,
                        "discount": 0,
                    }
                ],
            ),
        )
    assert unknown_product.status_code == 500
    assert _table_count(isolated_app.db_paths["raios"], "quotes") == quotes_before
    assert _table_count(isolated_app.db_paths["raios"], "quote_items") == items_before

    valid_quote_after_error = isolated_app.client.get(
        f"/api/orcamentos/{body['quote']['id']}",
        headers=_headers(token),
    )
    assert valid_quote_after_error.status_code == 200
    assert valid_quote_after_error.json()["quote"]["total"] == 0

    quote_id = body["quote"]["id"]
    before_update_error = _quote_db_snapshot(isolated_app.db_paths["raios"], quote_id)

    # PENDENCIA: a rota deve tratar product_id inexistente no update e retornar erro controlado.
    # Comportamento atual preservado: HTTP 500, sem gravacao parcial e sem manter lock no SQLite.
    with TestClient(isolated_app.module.app, raise_server_exceptions=False) as non_raising_client:
        unknown_product_update = non_raising_client.put(
            f"/api/orcamentos/{quote_id}",
            headers=_headers(token),
            json=_quote_payload(
                client_name="Cliente Orcamento Update Produto Inexistente",
                discount=25,
                items=[
                    {
                        "product_id": 999999,
                        "item_order": 1,
                        "code": "UNKNOWN-UPD",
                        "description": "Produto inexistente no update dispara erro interno atualmente",
                        "quantity": 1,
                        "unit": "und",
                        "unit_price": 100,
                        "discount": 0,
                    }
                ],
            ),
        )
    assert unknown_product_update.status_code == 500
    assert _quote_db_snapshot(isolated_app.db_paths["raios"], quote_id) == before_update_error
    _assert_db_accepts_write(isolated_app.db_paths["raios"])

    valid_quote_after_update_error = isolated_app.client.get(
        f"/api/orcamentos/{quote_id}",
        headers=_headers(token),
    )
    assert valid_quote_after_update_error.status_code == 200
    assert valid_quote_after_update_error.json()["quote"]["total"] == 0

    with TestClient(isolated_app.module.app, raise_server_exceptions=False) as non_raising_client:
        missing_quote_update = non_raising_client.put(
            "/api/orcamentos/999999",
            headers=_headers(token),
            json=_quote_payload(client_name="Cliente Orcamento Inexistente"),
        )
    assert missing_quote_update.status_code == 500
    _assert_db_accepts_write(isolated_app.db_paths["raios"])
    assert len(valid_quote_after_error.json()["items"]) == 2


def test_orcamentos_auth_permissions_current_behavior(isolated_app):
    admin_token = _login(isolated_app.client)
    _create_temp_user(isolated_app, "editor_orcamentos", "editor123", "editor")
    _create_temp_user(isolated_app, "viewer_orcamentos", "viewer123", "viewer")
    editor_token = _login(isolated_app.client, "editor_orcamentos", "editor123")
    viewer_token = _login(isolated_app.client, "viewer_orcamentos", "viewer123")

    endpoints = [
        "/api/orcamentos/company",
        "/api/orcamentos/products",
        "/api/orcamentos",
    ]
    for endpoint in endpoints:
        response = isolated_app.client.get(endpoint)
        assert response.status_code == 401

    viewer_products = isolated_app.client.get(
        "/api/orcamentos/products",
        headers=_headers(viewer_token),
    )
    viewer_quotes = isolated_app.client.get(
        "/api/orcamentos",
        headers=_headers(viewer_token),
    )
    assert viewer_products.status_code == 200
    assert viewer_quotes.status_code == 200

    viewer_create_product = isolated_app.client.post(
        "/api/orcamentos/products",
        headers=_headers(viewer_token),
        json=_product_payload(name="Produto Viewer Orcamento"),
    )
    viewer_create_quote = isolated_app.client.post(
        "/api/orcamentos",
        headers=_headers(viewer_token),
        json=_quote_payload(client_name="Cliente Viewer Orcamento"),
    )
    assert viewer_create_product.status_code == 403
    assert viewer_create_quote.status_code == 403

    editor_product = isolated_app.client.post(
        "/api/orcamentos/products",
        headers=_headers(editor_token),
        json=_product_payload(name="Produto Editor Orcamento"),
    )
    editor_quote = isolated_app.client.post(
        "/api/orcamentos",
        headers=_headers(editor_token),
        json=_quote_payload(client_name="Cliente Editor Orcamento"),
    )
    assert editor_product.status_code == 200
    assert editor_quote.status_code == 200

    invalid_token = isolated_app.client.get(
        "/api/orcamentos",
        headers=_headers("token-invalido"),
    )
    assert invalid_token.status_code == 401

    admin_quote = isolated_app.client.post(
        "/api/orcamentos",
        headers=_headers(admin_token),
        json=_quote_payload(client_name="Cliente Admin Orcamento"),
    )
    assert admin_quote.status_code == 200


def test_orcamentos_are_isolated_by_x_company_current_behavior(isolated_app):
    raios_token = _login(isolated_app.client)
    _create_temp_user(isolated_app, "admin_orc_estrada_iso", "admin123", "admin", company="estrada")
    estrada_token = _login(
        isolated_app.client,
        "admin_orc_estrada_iso",
        "admin123",
        company="estrada",
    )

    raios_quote = _post_quote(
        isolated_app.client,
        raios_token,
        company="raios",
        client_name="Cliente Orcamento Raios Isolado",
    )
    estrada_quote = _post_quote(
        isolated_app.client,
        estrada_token,
        company="estrada",
        client_name="Cliente Orcamento Estrada Isolado",
    )

    assert raios_quote["quote"]["quote_number"] == 1
    assert estrada_quote["quote"]["quote_number"] == 1
    assert _table_count(isolated_app.db_paths["raios"], "quotes") == 1
    assert _table_count(isolated_app.db_paths["estrada"], "quotes") == 1

    raios_list = isolated_app.client.get(
        "/api/orcamentos",
        headers=_headers(raios_token, "raios"),
    )
    estrada_list = isolated_app.client.get(
        "/api/orcamentos",
        headers=_headers(estrada_token, "estrada"),
    )
    assert raios_list.status_code == 200
    assert estrada_list.status_code == 200
    assert [row["client_name"] for row in raios_list.json()] == ["Cliente Orcamento Raios Isolado"]
    assert [row["client_name"] for row in estrada_list.json()] == [
        "Cliente Orcamento Estrada Isolado"
    ]

    raios_cannot_read_estrada_id = isolated_app.client.get(
        f"/api/orcamentos/{estrada_quote['quote']['id']}",
        headers=_headers(raios_token, "raios"),
    )
    # Comportamento atual: IDs reiniciam por banco; o mesmo id pode existir em ambas as empresas.
    assert raios_cannot_read_estrada_id.status_code == 200
    assert (
        raios_cannot_read_estrada_id.json()["quote"]["client_name"]
        == "Cliente Orcamento Raios Isolado"
    )
