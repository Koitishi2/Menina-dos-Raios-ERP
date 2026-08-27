import sqlite3


def _login(client, username="admin", password="admin123", company="raios"):
    response = client.post(
        "/api/auth/login",
        headers={"x-company": company},
        json={"username": username, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _headers(token, company="raios"):
    return {"x-token": token, "x-company": company}


def _create_user(client, token, username, role="Cliente"):
    response = client.post(
        "/api/users",
        headers=_headers(token),
        json={
            "username": username,
            "password": "SenhaTeste123!",
            "full_name": "Cliente Restrito",
            "role": role,
        },
    )
    assert response.status_code == 200, response.text
    return response.json()["id"]


def _insert_sales(db_path):
    rows = [
        ("uva-1", "NF", "2026-08-20", "Cliente A", "Uva Vitória", 2, 10, 20),
        ("uva-2", "AVULSO", "2026-08-21", "Cliente B", "Uva Vitória 250g", 3, 5, 15),
        ("mac-1", "NF", "2026-08-22", "Cliente C", "Macaxeira Chips", 4, 7, 28),
    ]
    conn = sqlite3.connect(db_path)
    try:
        conn.executemany(
            """INSERT INTO sales(
                   id,sale_type,sale_date,client,product,quantity,unit_price,total)
               VALUES(?,?,?,?,?,?,?,?)""",
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def test_cliente_seed_login_permissions_and_product_isolation(isolated_app):
    client = isolated_app.client
    admin = _login(client)
    _create_user(client, admin["token"], "cliente_rbac")
    _insert_sales(isolated_app.db_paths["estrada"])
    isolated_app.module.clear_sales_cache()

    login = _login(client, "cliente_rbac", "SenhaTeste123!", company="raios")
    assert login["role"] == "cliente"
    assert login["company"] == "estrada"
    headers = _headers(login["token"], "estrada")

    permissions = client.get("/api/auth/permissions", headers=headers)
    assert permissions.status_code == 200
    context = permissions.json()
    assert context["managed"] is True
    assert context["areas"] == {"menina_da_estrada": True}
    assert list(context["modules"]["menina_da_estrada"]) == ["produtos", "consolidado"]
    assert all(
        values == {
            "view": True,
            "create": False,
            "edit": False,
            "delete": False,
            "export": False,
            "import": False,
            "approve": False,
            "configure": False,
        }
        for values in context["modules"]["menina_da_estrada"].values()
    )
    assert {p["name"] for p in context["product_scope"]["products"]} == {
        "Uva Vitória",
        "Uva Vitória 250g",
    }

    sales = client.get("/api/sales", headers=headers)
    assert sales.status_code == 200
    assert {row["product"] for row in sales.json()} == {"Uva Vitória", "Uva Vitória 250g"}

    consolidated = client.get("/api/consolidado?year=2026", headers=headers)
    assert consolidated.status_code == 200
    assert {
        isolated_app.module.normalize_product_key(row["product"])
        for row in consolidated.json()
    } == {"UVA_VITORIA", "UVA_VITORIA_250G"}
    assert sum(row["total_val"] for row in consolidated.json()) == 35

    summary = client.get("/api/summary?year=2026", headers=headers)
    assert summary.status_code == 200
    assert sum(row["total_val"] for row in summary.json()) == 35
    assert sum(row["cnt"] for row in summary.json()) == 2

    hidden = client.get("/api/product-stats?product=Macaxeira%20Chips&year=2026", headers=headers)
    assert hidden.status_code == 404
    assert hidden.json()["detail"] == "Produto nao encontrado."

    uva_product = next(
        p
        for p in context["product_scope"]["products"]
        if isolated_app.module.normalize_product_key(p["name"]) == "UVA_VITORIA"
    )
    changed_scope = client.put(
        "/api/admin/roles/cliente",
        headers=_headers(admin["token"]),
        json={
            "name": "Cliente",
            "description": "Acesso restrito atualizado em teste.",
            "active": True,
            "product_scope_mode": "specific",
            "areas": {"menina_da_estrada": True},
            "modules": {
                "menina_da_estrada": {
                    "produtos": {"view": True},
                    "consolidado": {"view": True},
                }
            },
            "products": [{"product_id": uva_product["id"], "view": True}],
        },
    )
    assert changed_scope.status_code == 200
    refreshed_sales = client.get("/api/sales", headers=headers)
    assert refreshed_sales.status_code == 200
    assert {
        isolated_app.module.normalize_product_key(row["product"])
        for row in refreshed_sales.json()
    } == {"UVA_VITORIA"}

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    conn.row_factory = sqlite3.Row
    try:
        isolated_app.module.seed_rbac_defaults(conn)
        conn.commit()
        after_restart = isolated_app.module.role_context_from_db(conn, "cliente")
    finally:
        conn.close()
    assert [p["id"] for p in after_restart["product_scope"]["products"]] == [uva_product["id"]]


def test_cliente_is_default_deny_and_cannot_switch_area_or_write(isolated_app):
    client = isolated_app.client
    admin = _login(client)
    _create_user(client, admin["token"], "cliente_negado")
    login = _login(client, "cliente_negado", "SenhaTeste123!", company="estrada")
    token = login["token"]
    headers = _headers(token, "estrada")

    denied_requests = [
        client.post(
            "/api/sales",
            headers=headers,
            json={
                "sale_type": "NF",
                "sale_date": "2026-08-26",
                "product": "Uva Vitória",
                "quantity": 1,
                "unit_price": 1,
            },
        ),
        client.get("/api/projecao/producao", headers=headers),
        client.get("/api/users", headers=headers),
        client.post(
            "/api/auth/company-switch",
            headers=headers,
            json={"company": "raios"},
        ),
    ]
    assert [response.status_code for response in denied_requests] == [403, 403, 403, 403]
    assert all("permiss" in response.json()["detail"].lower() for response in denied_requests)


def test_admin_manages_roles_and_user_role_changes_apply_to_existing_session(isolated_app):
    client = isolated_app.client
    admin = _login(client)
    admin_headers = _headers(admin["token"])

    roles = client.get("/api/admin/roles", headers=admin_headers)
    assert roles.status_code == 200
    assert {role["key"] for role in roles.json()} >= {"admin", "cliente"}

    products = client.get("/api/admin/permission-products", headers=admin_headers)
    assert products.status_code == 200
    uva = next(row for row in products.json() if row["name"] == "Uva Vitória")
    body = {
        "key": "cliente_teste",
        "name": "Cliente de teste",
        "description": "Cargo temporário de caracterização.",
        "active": True,
        "product_scope_mode": "specific",
        "areas": {"menina_da_estrada": True},
        "modules": {
            "menina_da_estrada": {
                "produtos": {"view": False, "edit": True},
            }
        },
        "products": [{"product_id": uva["id"], "edit": True}],
    }
    created = client.post("/api/admin/roles", headers=admin_headers, json=body)
    assert created.status_code == 200, created.text

    role = client.get("/api/admin/roles/cliente_teste", headers=admin_headers)
    assert role.status_code == 200
    role_data = role.json()
    assert role_data["modules"]["menina_da_estrada"]["produtos"]["view"] is True
    assert role_data["modules"]["menina_da_estrada"]["produtos"]["edit"] is True
    assert role_data["product_scope"]["products"][0]["can_view"] == 1
    assert role_data["product_scope"]["products"][0]["can_edit"] == 1

    user_id = _create_user(client, admin["token"], "role_live", role="cliente_teste")
    live_login = _login(client, "role_live", "SenhaTeste123!", company="estrada")
    changed = client.put(
        f"/api/users/{user_id}",
        headers=admin_headers,
        json={"role": "cliente"},
    )
    assert changed.status_code == 200
    live_context = client.get(
        "/api/auth/permissions",
        headers=_headers(live_login["token"], "estrada"),
    )
    assert live_context.status_code == 200
    assert live_context.json()["role"]["key"] == "cliente"

    protected = client.delete("/api/admin/roles/cliente", headers=admin_headers)
    assert protected.status_code == 400
    linked = client.delete("/api/admin/roles/cliente_teste", headers=admin_headers)
    assert linked.status_code == 200


def test_admin_keeps_legacy_company_selection_and_full_access(isolated_app):
    login = _login(isolated_app.client, company="estrada")
    assert login["company"] == "estrada"
    permissions = isolated_app.client.get(
        "/api/auth/permissions",
        headers=_headers(login["token"], "estrada"),
    )
    assert permissions.status_code == 200
    context = permissions.json()
    assert context["role"]["key"] == "admin"
    assert all(context["areas"].values())
    assert context["product_scope"]["mode"] == "all"


def test_custom_role_actions_are_enforced_per_product(isolated_app):
    client = isolated_app.client
    admin = _login(client)
    admin_headers = _headers(admin["token"])
    products = client.get("/api/admin/permission-products", headers=admin_headers).json()
    uva = next(row for row in products if row["name"] == "Uva Vitória")
    role_body = {
        "key": "operador_uva",
        "name": "Operador Uva",
        "active": True,
        "product_scope_mode": "specific",
        "areas": {"menina_da_estrada": True},
        "modules": {
            "menina_da_estrada": {
                "consolidado": {"create": True},
            }
        },
        "products": [{"product_id": uva["id"], "create": True}],
    }
    response = client.post("/api/admin/roles", headers=admin_headers, json=role_body)
    assert response.status_code == 200, response.text
    _create_user(client, admin["token"], "operador_uva", role="operador_uva")
    login = _login(client, "operador_uva", "SenhaTeste123!", company="estrada")
    headers = _headers(login["token"], "estrada")

    allowed = client.post(
        "/api/sales",
        headers=headers,
        json={
            "sale_type": "NF",
            "sale_date": "2026-08-26",
            "product": "Uva Vitória",
            "quantity": 1,
            "unit_price": 12,
        },
    )
    assert allowed.status_code == 200, allowed.text
    denied = client.post(
        "/api/sales",
        headers=headers,
        json={
            "sale_type": "NF",
            "sale_date": "2026-08-26",
            "product": "Macaxeira Chips",
            "quantity": 1,
            "unit_price": 12,
        },
    )
    assert denied.status_code == 404
    assert denied.json()["detail"] == "Produto nao encontrado."

    conn = sqlite3.connect(isolated_app.db_paths["estrada"])
    try:
        products_saved = [row[0] for row in conn.execute("SELECT product FROM sales").fetchall()]
    finally:
        conn.close()
    assert [isolated_app.module.normalize_product_key(name) for name in products_saved] == ["UVA_VITORIA"]


def test_frontend_loads_backend_permissions_before_restricted_data(isolated_app):
    html = (isolated_app.temp_backend / "static" / "index.html").read_text(encoding="utf-8")
    assert 'id="cfg-cargos"' in html
    assert "/api/auth/permissions" in html
    assert "await loadPermissionsOnLogin();\n    showApp();" in html
    assert "function loadRestrictedApp()" in html
    assert "applyManagedActionUI" in html
    assert "rbac-product-search" in html
