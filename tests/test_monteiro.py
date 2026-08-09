import sqlite3
import uuid

from fastapi.testclient import TestClient


PENDING_MONTEIRO_SCOPE_DECISION = (
    "PENDENCIA: decidir se o modulo Monteiro deve ser compartilhado ou isolado por empresa."
)


MONTEIRO_SCOPE_MATRIX = [
    {
        "rota": "/api/monteiro/products",
        "metodo": "GET",
        "banco_tabela": "bm_monteiro.db: paladar_products",
        "empresa_header": "x-company ignorado; middleware forca raios",
        "isolamento_real": "compartilhado no escopo raios",
        "risco": "medio",
    },
    {
        "rota": "/api/monteiro/products",
        "metodo": "POST",
        "banco_tabela": "bm_monteiro.db: paladar_products",
        "empresa_header": "x-company ignorado; middleware forca raios",
        "isolamento_real": "compartilhado no escopo raios",
        "risco": "medio",
    },
    {
        "rota": "/api/monteiro/sales",
        "metodo": "GET/POST",
        "banco_tabela": "bm_monteiro.db: paladar_sales",
        "empresa_header": "x-company ignorado; middleware forca raios",
        "isolamento_real": "compartilhado no escopo raios",
        "risco": "alto",
    },
    {
        "rota": "/api/monteiro/summary",
        "metodo": "GET",
        "banco_tabela": "bm_monteiro.db: paladar_sales",
        "empresa_header": "x-company ignorado; middleware forca raios",
        "isolamento_real": "compartilhado no escopo raios",
        "risco": "alto",
    },
    {
        "rota": "/api/monteiro/clients/list",
        "metodo": "GET",
        "banco_tabela": "bm_monteiro.db: paladar_sales",
        "empresa_header": "x-company ignorado; middleware forca raios",
        "isolamento_real": "compartilhado no escopo raios",
        "risco": "medio",
    },
    {
        "rota": "/api/monteiro/clients/summary",
        "metodo": "GET",
        "banco_tabela": "bm_monteiro.db: paladar_sales",
        "empresa_header": "x-company ignorado; middleware forca raios",
        "isolamento_real": "compartilhado no escopo raios",
        "risco": "medio",
    },
    {
        "rota": "/api/monteiro/payments",
        "metodo": "GET/POST",
        "banco_tabela": "bm_monteiro.db: monteiro_payments",
        "empresa_header": "x-company ignorado; middleware forca raios",
        "isolamento_real": "compartilhado no escopo raios",
        "risco": "alto",
    },
    {
        "rota": "/api/monteiro/payments/summary",
        "metodo": "GET",
        "banco_tabela": "bm_monteiro.db: paladar_sales + monteiro_payments",
        "empresa_header": "x-company ignorado; middleware forca raios",
        "isolamento_real": "compartilhado no escopo raios",
        "risco": "alto",
    },
    {
        "rota": "/api/monteiro/payments/report",
        "metodo": "GET",
        "banco_tabela": "bm_monteiro.db: paladar_sales + monteiro_payments",
        "empresa_header": "x-company ignorado; middleware forca raios",
        "isolamento_real": "compartilhado no escopo raios",
        "risco": "alto",
    },
]


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


def _create_temp_user(isolated_app, username, password, role):
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    user_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO users(id, username, password_hash, full_name, role, active) VALUES(?,?,?,?,?,1)",
        (
            user_id,
            username,
            isolated_app.module.hash_password(password),
            f"Usuario {role} Monteiro",
            role,
        ),
    )
    conn.commit()
    conn.close()
    return user_id


def _product_payload(name=None, price=12.5, **overrides):
    payload = {
        "name": name or f"Produto Monteiro {uuid.uuid4().hex[:8]}",
        "suggested_price": price,
    }
    payload.update(overrides)
    return payload


def _sale_payload(client="Cliente Monteiro Padrao", nf_number=None, **overrides):
    token = uuid.uuid4().hex[:6]
    payload = {
        "saledate": "2026-06-05",
        "client": client,
        "nf_number": nf_number or f"MON-{token}",
        "driver": "Lucas",
        "vehicle": "Carro Monteiro",
        "plate": "MON-0001",
        "notes": "venda monteiro temporaria",
        "items": [
            {
                "product": "Produto Monteiro A",
                "quantity": 2,
                "unitprice": 100,
                "total": 200,
                "notes": "item A",
            },
            {
                "product": "Produto Monteiro B",
                "quantity": 1,
                "unitprice": 150,
                "total": 150,
                "notes": "item B",
            },
        ],
    }
    payload.update(overrides)
    return payload


def _payment_payload(client="Cliente Monteiro Padrao", amount=100, **overrides):
    payload = {
        "client": client,
        "payment_date": "2026-06-20",
        "amount": amount,
        "month": "06",
        "year": "2026",
        "payment_type": "repasse",
        "notes": "pagamento monteiro temporario",
    }
    payload.update(overrides)
    return payload


def _post_product(test_client, token, company="raios", **overrides):
    response = test_client.post(
        "/api/monteiro/products",
        headers=_headers(token, company),
        json=_product_payload(**overrides),
    )
    assert response.status_code == 200
    return response.json()


def _post_sale(test_client, token, company="raios", **overrides):
    response = test_client.post(
        "/api/monteiro/sales",
        headers=_headers(token, company),
        json=_sale_payload(**overrides),
    )
    assert response.status_code == 200
    return response.json()


def _post_paladar_sale(test_client, token, company="raios", **overrides):
    response = test_client.post(
        "/api/paladar/sales",
        headers=_headers(token, company),
        json=_sale_payload(**overrides),
    )
    assert response.status_code == 200
    return response.json()


def _post_payment(test_client, token, company="raios", **overrides):
    response = test_client.post(
        "/api/monteiro/payments",
        headers=_headers(token, company),
        json=_payment_payload(**overrides),
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    return response


def _table_count(db_path, table):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
    finally:
        conn.close()


def test_monteiro_scope_matrix_documents_current_forced_raios_behavior():
    assert PENDING_MONTEIRO_SCOPE_DECISION.startswith("PENDENCIA")
    assert MONTEIRO_SCOPE_MATRIX
    for item in MONTEIRO_SCOPE_MATRIX:
        assert item["rota"].startswith("/api/monteiro/")
        assert "forca raios" in item["empresa_header"]
        assert item["isolamento_real"] == "compartilhado no escopo raios"
        assert item["risco"] in {"medio", "alto"}


def test_monteiro_products_crud_and_forced_raios_scope(isolated_app):
    token = _login(isolated_app.client)

    created_raios = _post_product(
        isolated_app.client,
        token,
        company="raios",
        name="Produto Monteiro Raios",
        price=10.5,
    )
    created_estrada_header = _post_product(
        isolated_app.client,
        token,
        company="estrada",
        name="Produto Monteiro Estrada Header",
        price=22,
    )

    assert created_raios["suggested_price"] == 10.5
    assert created_estrada_header["suggested_price"] == 22
    assert _table_count(isolated_app.db_paths["raios"], "paladar_products") >= 2
    assert _table_count(isolated_app.db_paths["estrada"], "paladar_products") == 0

    listed_raios = isolated_app.client.get(
        "/api/monteiro/products?active=all&search=Produto Monteiro",
        headers=_headers(token, "raios"),
    )
    listed_estrada_header = isolated_app.client.get(
        "/api/monteiro/products?active=all&search=Produto Monteiro",
        headers=_headers(token, "estrada"),
    )
    assert listed_raios.status_code == 200
    assert listed_estrada_header.status_code == 200
    assert {row["name"] for row in listed_raios.json()} == {
        "Produto Monteiro Raios",
        "Produto Monteiro Estrada Header",
    }
    assert listed_estrada_header.json() == listed_raios.json()

    updated = isolated_app.client.put(
        f"/api/monteiro/products/{created_raios['id']}",
        headers=_headers(token),
        json={"name": "Produto Monteiro Raios Editado", "suggested_price": 11.75, "active": 0},
    )
    assert updated.status_code == 200
    assert updated.json() == {"message": "ok"}

    inactive_list = isolated_app.client.get(
        "/api/monteiro/products?active=all&search=Raios Editado",
        headers=_headers(token),
    )
    assert inactive_list.status_code == 200
    assert inactive_list.json()[0]["active"] == 0
    assert inactive_list.json()[0]["suggested_price"] == 11.75

    deleted = isolated_app.client.delete(
        f"/api/monteiro/products/{created_estrada_header['id']}",
        headers=_headers(token),
    )
    assert deleted.status_code == 200
    assert deleted.json() == {"ok": True}


def test_paladar_sales_route_uses_same_multi_item_flow_as_monteiro(isolated_app):
    token = _login(isolated_app.client)

    created = _post_paladar_sale(
        isolated_app.client,
        token,
        client="Cliente Paladar Direto",
        nf_number="PAL-DIR-001",
        items=[
            {
                "product": "Produto Paladar Direto A",
                "quantity": 4,
                "unitprice": 10,
                "total": 40,
                "notes": "item paladar A",
            },
            {
                "product": "Produto Paladar Direto B",
                "quantity": 2,
                "unitprice": 15,
                "total": 30,
                "notes": "item paladar B",
            },
        ],
    )

    assert len(created["ids"]) == 2
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT sale_group,client,nf_number,product,quantity,unitprice,total "
            "FROM paladar_sales WHERE nf_number=? ORDER BY id",
            ("PAL-DIR-001",),
        ).fetchall()
    finally:
        conn.close()
    assert len(rows) == 2
    assert {row["sale_group"] for row in rows} == {created["group"]}
    assert [row["product"] for row in rows] == [
        "Produto Paladar Direto A",
        "Produto Paladar Direto B",
    ]
    assert sum(row["total"] for row in rows) == 70


def test_monteiro_sale_invalid_later_item_rolls_back_and_allows_next_write(isolated_app):
    token = _login(isolated_app.client)
    payload = _sale_payload(
        client="Cliente Monteiro Falha Item",
        nf_number="MON-FALHA-ITEM",
        items=[
            {
                "product": "Produto Valido Antes Da Falha",
                "quantity": 1,
                "unitprice": 20,
                "total": 20,
                "notes": "primeiro item valido",
            },
            {
                "product": "Produto Invalido Depois",
                "quantity": "quantidade-invalida",
                "unitprice": 30,
                "total": 30,
                "notes": "segundo item invalido",
            },
        ],
    )

    with TestClient(isolated_app.module.app, raise_server_exceptions=False) as client:
        failed = client.post(
            "/api/monteiro/sales",
            headers=_headers(token),
            json=payload,
        )
    assert failed.status_code == 500

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        partial_count = conn.execute(
            "SELECT COUNT(*) FROM paladar_sales WHERE nf_number=?",
            ("MON-FALHA-ITEM",),
        ).fetchone()[0]
    finally:
        conn.close()
    assert partial_count == 0

    created_after_error = _post_sale(
        isolated_app.client,
        token,
        client="Cliente Monteiro Pos Falha",
        nf_number="MON-POS-FALHA",
        items=[
            {
                "product": "Produto Pos Falha",
                "quantity": 1,
                "unitprice": 12,
                "total": 12,
                "notes": "escrita posterior",
            }
        ],
    )
    assert len(created_after_error["ids"]) == 1


def test_monteiro_sales_grouping_filters_summary_clients_and_forced_scope(isolated_app):
    token = _login(isolated_app.client)
    client_name = "Cliente Monteiro Agrupado"

    created = _post_sale(
        isolated_app.client,
        token,
        company="raios",
        client=client_name,
        nf_number="MON-AGR-001",
    )
    created_other_header = _post_sale(
        isolated_app.client,
        token,
        company="estrada",
        client="Cliente Monteiro Estrada Header",
        nf_number="MON-AGR-002",
        items=[
            {
                "product": "Produto Monteiro C",
                "quantity": 3,
                "unitprice": 50,
                "total": 150,
                "notes": "item C",
            }
        ],
    )

    assert len(created["ids"]) == 2
    assert len(created_other_header["ids"]) == 1
    assert _table_count(isolated_app.db_paths["raios"], "paladar_sales") == 3
    assert _table_count(isolated_app.db_paths["estrada"], "paladar_sales") == 0

    listed = isolated_app.client.get(
        "/api/monteiro/sales?month=6&year=2026&client=Cliente Monteiro Agrupado",
        headers=_headers(token, "raios"),
    )
    assert listed.status_code == 200
    rows = listed.json()
    assert len(rows) == 1
    assert rows[0]["sale_group"] == created["group"]
    assert rows[0]["client"] == client_name
    assert rows[0]["nf_number"] == "MON-AGR-001"
    assert rows[0]["driver"] == "Lucas"
    assert rows[0]["plate"] == "MON-0001"
    assert rows[0]["total_group"] == 350
    assert len(rows[0]["items"]) == 2

    listed_with_estrada_header = isolated_app.client.get(
        "/api/monteiro/sales?month=6&year=2026&client=Cliente Monteiro Agrupado",
        headers=_headers(token, "estrada"),
    )
    assert listed_with_estrada_header.status_code == 200
    assert listed_with_estrada_header.json() == rows

    by_product = isolated_app.client.get(
        "/api/monteiro/sales?month=6&year=2026&product=Produto Monteiro B",
        headers=_headers(token),
    )
    assert by_product.status_code == 200
    assert len(by_product.json()) == 1
    assert by_product.json()[0]["sale_group"] == created["group"]

    by_nf = isolated_app.client.get(
        "/api/monteiro/sales?month=6&year=2026&nf_number=MON-AGR-002",
        headers=_headers(token),
    )
    assert by_nf.status_code == 200
    assert by_nf.json()[0]["client"] == "Cliente Monteiro Estrada Header"

    summary = isolated_app.client.get(
        "/api/monteiro/summary?month=6&year=2026",
        headers=_headers(token, "estrada"),
    )
    assert summary.status_code == 200
    summary_json = summary.json()
    assert summary_json["total_receita"] == 500
    assert summary_json["total_vendas"] == 2
    assert summary_json["ticket_medio"] == 250
    assert summary_json["dias_produtivos"] == 1
    assert summary_json["melhor_dia"]["date"] == "2026-06-05"
    assert {row["product"] for row in summary_json["por_produto"]} >= {
        "Produto Monteiro A",
        "Produto Monteiro B",
        "Produto Monteiro C",
    }

    clients_list = isolated_app.client.get(
        "/api/monteiro/clients/list?month=6&year=2026",
        headers=_headers(token, "estrada"),
    )
    assert clients_list.status_code == 200
    assert clients_list.json() == ["Cliente Monteiro Agrupado", "Cliente Monteiro Estrada Header"]

    clients_summary = isolated_app.client.get(
        "/api/monteiro/clients/summary?month=6&year=2026&client_filter=Agrupado",
        headers=_headers(token),
    )
    assert clients_summary.status_code == 200
    clients_summary_json = clients_summary.json()
    assert clients_summary_json["total_vendido"] == 350
    assert clients_summary_json["total_clientes"] == 1
    assert clients_summary_json["cliente_lider"]["client"] == client_name

    clients_history = isolated_app.client.get(
        "/api/monteiro/clients/history?month=6&year=2026&client_filter=Agrupado",
        headers=_headers(token),
    )
    assert clients_history.status_code == 200
    assert clients_history.json() == [
        {"mes": "2026-06", "num_vendas": 1, "qty_total": 3, "total": 350}
    ]


def test_monteiro_payments_report_uses_paladar_sales_and_monteiro_payments(isolated_app):
    token = _login(isolated_app.client)
    client_name = "Cliente Monteiro Relatorio"

    _post_sale(
        isolated_app.client,
        token,
        client=client_name,
        nf_number="MON-PAY-001",
        items=[
            {
                "product": "Produto Monteiro Relatorio",
                "quantity": 5,
                "unitprice": 100,
                "total": 500,
                "notes": "venda para relatorio de pagamento",
            }
        ],
    )
    _post_payment(isolated_app.client, token, client=client_name, amount=200)
    _post_payment(
        isolated_app.client,
        token,
        company="estrada",
        client=client_name,
        amount=300,
        payment_date="2026-06-25",
    )

    payments = isolated_app.client.get(
        f"/api/monteiro/payments?client={client_name}&month=6&year=2026",
        headers=_headers(token, "estrada"),
    )
    assert payments.status_code == 200
    assert [row["amount"] for row in payments.json()] == [300, 200]

    summary = isolated_app.client.get(
        f"/api/monteiro/payments/summary?client={client_name}&month=6&year=2026",
        headers=_headers(token, "estrada"),
    )
    assert summary.status_code == 200
    assert summary.json() == {
        "total_vendido": 500.0,
        "num_notas": 1,
        "total_pago": 500.0,
        "num_pagamentos": 2,
        "ultimo_pagamento": "2026-06-25",
        "saldo": 0.0,
    }

    report = isolated_app.client.get(
        f"/api/monteiro/payments/report?client={client_name}&month=6&year=2026",
        headers=_headers(token),
    )
    assert report.status_code == 200
    report_json = report.json()
    assert report_json["client"] == client_name
    assert report_json["period"] == "06/2026"
    assert report_json["total_vendas"] == 500
    assert report_json["total_pago"] == 500
    assert report_json["saldo"] == 0
    assert len(report_json["vendas"]) == 1
    assert report_json["vendas"][0]["total"] == 500
    assert report_json["vendas"][0]["qty"] == 5
    assert report_json["vendas"][0]["nf_number"] == "MON-PAY-001"
    assert len(report_json["pagamentos"]) == 2
    assert [row["amount"] for row in report_json["pagamentos"]] == [200, 300]
    assert [row["tipo"] for row in report_json["extrato"]] == [
        "nota",
        "total_notas",
        "pagamento",
        "pagamento",
    ]
    assert [row["valor"] for row in report_json["extrato"]] == [500, 500, -200, -300]


def test_monteiro_auth_permissions_and_current_role_behavior(isolated_app):
    admin_token = _login(isolated_app.client)
    _create_temp_user(isolated_app, "editor_monteiro", "editor123", "editor")
    _create_temp_user(isolated_app, "viewer_monteiro", "viewer123", "viewer")
    editor_token = _login(isolated_app.client, "editor_monteiro", "editor123")
    viewer_token = _login(isolated_app.client, "viewer_monteiro", "viewer123")

    endpoints = [
        "/api/monteiro/products",
        "/api/monteiro/sales",
        "/api/monteiro/summary",
        "/api/monteiro/clients/list",
        "/api/monteiro/payments",
    ]
    for endpoint in endpoints:
        response = isolated_app.client.get(endpoint)
        assert response.status_code == 401

    viewer_get_products = isolated_app.client.get(
        "/api/monteiro/products",
        headers=_headers(viewer_token),
    )
    viewer_get_sales = isolated_app.client.get(
        "/api/monteiro/sales",
        headers=_headers(viewer_token),
    )
    assert viewer_get_products.status_code == 200
    assert viewer_get_sales.status_code == 200

    viewer_create_product = isolated_app.client.post(
        "/api/monteiro/products",
        headers=_headers(viewer_token),
        json=_product_payload(name="Produto Viewer Bloqueado"),
    )
    viewer_create_sale = isolated_app.client.post(
        "/api/monteiro/sales",
        headers=_headers(viewer_token),
        json=_sale_payload(client="Cliente Viewer Bloqueado"),
    )
    viewer_create_payment = isolated_app.client.post(
        "/api/monteiro/payments",
        headers=_headers(viewer_token),
        json=_payment_payload(client="Cliente Viewer Bloqueado"),
    )
    assert viewer_create_product.status_code == 403
    assert viewer_create_sale.status_code == 403
    assert viewer_create_payment.status_code == 403

    editor_create_product = isolated_app.client.post(
        "/api/monteiro/products",
        headers=_headers(editor_token),
        json=_product_payload(name="Produto Editor Permitido"),
    )
    editor_create_sale = isolated_app.client.post(
        "/api/monteiro/sales",
        headers=_headers(editor_token),
        json=_sale_payload(client="Cliente Editor Permitido", nf_number="MON-EDIT-001"),
    )
    editor_create_payment_default = isolated_app.client.post(
        "/api/monteiro/payments",
        headers=_headers(editor_token),
        json=_payment_payload(client="Cliente Editor Bloqueado"),
    )
    assert editor_create_product.status_code == 200
    assert editor_create_sale.status_code == 200
    assert editor_create_payment_default.status_code == 403

    payment_permission = isolated_app.client.put(
        "/api/settings/monteiro-payment-permission",
        headers=_headers(admin_token),
        json={"roles": ["admin", "editor"]},
    )
    assert payment_permission.status_code == 200

    editor_create_payment_allowed = isolated_app.client.post(
        "/api/monteiro/payments",
        headers=_headers(editor_token),
        json=_payment_payload(client="Cliente Editor Permitido", amount=50),
    )
    assert editor_create_payment_allowed.status_code == 200

    invalid_token = isolated_app.client.get(
        "/api/monteiro/summary",
        headers=_headers("token-invalido"),
    )
    assert invalid_token.status_code == 401


def test_monteiro_routes_force_raios_and_do_not_provide_x_company_isolation(isolated_app):
    token = _login(isolated_app.client)

    _post_sale(
        isolated_app.client,
        token,
        company="raios",
        client="Cliente Escopo Raios",
        nf_number="MON-SCOPE-R",
        items=[
            {
                "product": "Produto Escopo Raios",
                "quantity": 1,
                "unitprice": 100,
                "total": 100,
                "notes": "",
            }
        ],
    )
    _post_sale(
        isolated_app.client,
        token,
        company="estrada",
        client="Cliente Escopo Estrada Header",
        nf_number="MON-SCOPE-E",
        items=[
            {
                "product": "Produto Escopo Estrada Header",
                "quantity": 1,
                "unitprice": 200,
                "total": 200,
                "notes": "",
            }
        ],
    )
    _post_payment(isolated_app.client, token, company="raios", client="Cliente Escopo Raios", amount=25)
    _post_payment(
        isolated_app.client,
        token,
        company="estrada",
        client="Cliente Escopo Estrada Header",
        amount=75,
    )

    raios_sales = isolated_app.client.get(
        "/api/monteiro/sales?month=6&year=2026",
        headers=_headers(token, "raios"),
    )
    estrada_sales = isolated_app.client.get(
        "/api/monteiro/sales?month=6&year=2026",
        headers=_headers(token, "estrada"),
    )
    assert raios_sales.status_code == 200
    assert estrada_sales.status_code == 200
    assert estrada_sales.json() == raios_sales.json()
    assert {row["client"] for row in raios_sales.json()} == {
        "Cliente Escopo Raios",
        "Cliente Escopo Estrada Header",
    }

    raios_payments = isolated_app.client.get(
        "/api/monteiro/payments?month=6&year=2026",
        headers=_headers(token, "raios"),
    )
    estrada_payments = isolated_app.client.get(
        "/api/monteiro/payments?month=6&year=2026",
        headers=_headers(token, "estrada"),
    )
    assert raios_payments.status_code == 200
    assert estrada_payments.status_code == 200
    assert estrada_payments.json() == raios_payments.json()
    assert {row["client"] for row in raios_payments.json()} == {
        "Cliente Escopo Raios",
        "Cliente Escopo Estrada Header",
    }

    assert _table_count(isolated_app.db_paths["raios"], "paladar_sales") == 2
    assert _table_count(isolated_app.db_paths["raios"], "monteiro_payments") == 2
    assert _table_count(isolated_app.db_paths["estrada"], "paladar_sales") == 0
    assert _table_count(isolated_app.db_paths["estrada"], "monteiro_payments") == 0

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        payment_columns = [
            row[1] for row in conn.execute("PRAGMA table_info(monteiro_payments)").fetchall()
        ]
    finally:
        conn.close()
    assert "company" not in payment_columns
    assert PENDING_MONTEIRO_SCOPE_DECISION
