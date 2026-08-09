import json
import sqlite3
import uuid
from datetime import datetime


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
            f"Usuario {role} Configuracoes",
            role,
        ),
    )
    conn.commit()
    conn.close()
    return user_id


def _fetch_all(db_path, sql, args=()):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in conn.execute(sql, args).fetchall()]
    finally:
        conn.close()


def _fetch_one(db_path, sql, args=()):
    rows = _fetch_all(db_path, sql, args)
    return rows[0] if rows else None


def _table_exists(db_path, table):
    return _fetch_one(
        db_path,
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ) is not None


def _table_columns(db_path, table):
    return [row["name"] for row in _fetch_all(db_path, f"PRAGMA table_info({table})")]


def _table_count(db_path, table):
    if not _table_exists(db_path, table):
        return None
    return _fetch_one(db_path, f"SELECT COUNT(*) AS total FROM {table}")["total"]


def test_expand_tab_keys_current_aliases_duplicates_and_order(isolated_app):
    expand_tab_keys = isolated_app.module._expand_tab_keys

    assert expand_tab_keys([]) == []
    assert expand_tab_keys(None) == []
    assert expand_tab_keys(["notas"]) == ["notas", "pendentes"]
    assert expand_tab_keys(["pendentes"]) == ["pendentes", "notas"]
    assert expand_tab_keys(["clientes"]) == ["clientes"]
    assert expand_tab_keys(["notas", "clientes"]) == ["notas", "pendentes", "clientes"]
    assert expand_tab_keys(["notas", "notas", "pendentes"]) == ["notas", "pendentes"]
    assert expand_tab_keys(["clientes", "clientes", "notas"]) == ["clientes", "notas", "pendentes"]
    assert expand_tab_keys(("notas", "clientes")) == ["notas", "pendentes", "clientes"]

    from_set = expand_tab_keys({"notas", "clientes"})
    assert isinstance(from_set, list)
    assert set(from_set) == {"notas", "pendentes", "clientes"}
    assert len(from_set) == 3


def test_expand_tab_keys_current_string_type_spacing_case_and_return_independence(isolated_app):
    expand_tab_keys = isolated_app.module._expand_tab_keys
    aliases_before = {
        key: list(value)
        for key, value in isolated_app.module.TAB_PERMISSION_ALIASES.items()
    }

    assert expand_tab_keys("notas") == ["n", "o", "t", "a", "s"]
    assert expand_tab_keys("") == []
    assert expand_tab_keys(" notas ") == [" ", "n", "o", "t", "a", "s"]
    assert expand_tab_keys([" notas "]) == [" notas "]
    assert expand_tab_keys(["NOTAS"]) == ["NOTAS"]
    assert expand_tab_keys([None]) == [None]

    result = expand_tab_keys(["notas"])
    result.append("mutado")
    assert result == ["notas", "pendentes", "mutado"]
    assert isolated_app.module.TAB_PERMISSION_ALIASES == aliases_before


def test_config_prices_history_audit_and_permissions(isolated_app):
    admin_token = _login(isolated_app.client)
    _create_temp_user(isolated_app, "editor_config_precos", "editor123", "editor")
    _create_temp_user(isolated_app, "viewer_config_precos", "viewer123", "viewer")
    editor_token = _login(isolated_app.client, "editor_config_precos", "editor123")
    viewer_token = _login(isolated_app.client, "viewer_config_precos", "viewer123")

    unauth = isolated_app.client.get("/api/prices")
    assert unauth.status_code == 401

    initial = isolated_app.client.get("/api/prices", headers=_headers(admin_token))
    assert initial.status_code == 200
    assert isinstance(initial.json(), list)

    product_key = f"CFG_PRICE_{uuid.uuid4().hex[:8]}".upper()
    created = isolated_app.client.post(
        "/api/prices",
        headers=_headers(editor_token),
        json={
            "key": product_key,
            "label": "Produto Config Preco",
            "price": 12.5,
            "price_min": 10,
            "price_max": 15,
            "is_variable": True,
        },
    )
    assert created.status_code == 200
    assert created.json() == {"ok": True}

    price_row = _fetch_one(
        isolated_app.db_paths["raios"],
        "SELECT key,label,price,price_min,price_max,is_variable FROM product_prices WHERE key=?",
        (product_key,),
    )
    assert price_row == {
        "key": product_key,
        "label": "Produto Config Preco",
        "price": 12.5,
        "price_min": 10.0,
        "price_max": 15.0,
        "is_variable": 1,
    }

    update_price = isolated_app.client.put(
        "/api/prices",
        headers=_headers(editor_token),
        json={"key": product_key, "price": 13.75, "price_min": 11, "price_max": 16},
    )
    assert update_price.status_code == 200
    assert update_price.json() == {"ok": True}

    updated_price_row = _fetch_one(
        isolated_app.db_paths["raios"],
        "SELECT price,price_min,price_max FROM product_prices WHERE key=?",
        (product_key,),
    )
    assert updated_price_row == {"price": 13.75, "price_min": 11.0, "price_max": 16.0}

    update_history_row = _fetch_one(
        isolated_app.db_paths["raios"],
        "SELECT price,note,changed_by FROM price_history WHERE key=? AND price=?",
        (product_key, 13.75),
    )
    assert update_history_row == {
        "price": 13.75,
        "note": "Alterado via painel",
        "changed_by": "editor_config_precos",
    }

    price_change_audit = _fetch_one(
        isolated_app.db_paths["raios"],
        "SELECT action,old_value,new_value FROM audit_log WHERE product_key=? AND action='PRICE_CHANGE'",
        (product_key,),
    )
    assert price_change_audit == {
        "action": "PRICE_CHANGE",
        "old_value": "12.5",
        "new_value": "13.75",
    }

    rename = isolated_app.client.put(
        "/api/prices/label",
        headers=_headers(editor_token),
        json={"key": product_key, "label": "Produto Config Preco Editado"},
    )
    assert rename.status_code == 200
    assert rename.json() == {"ok": True}

    add_history = isolated_app.client.post(
        "/api/prices/history",
        headers=_headers(editor_token),
        json={
            "key": product_key,
            "price": 14.25,
            "effective_date": "2026-08-08",
            "note": "historico temporario",
        },
    )
    assert add_history.status_code == 200
    assert add_history.json() == {"ok": True}

    price_after_history = _fetch_one(
        isolated_app.db_paths["raios"],
        "SELECT price FROM product_prices WHERE key=?",
        (product_key,),
    )
    assert price_after_history == {"price": 14.25}

    history = isolated_app.client.get(
        f"/api/prices/history?key={product_key}",
        headers=_headers(admin_token),
    )
    assert history.status_code == 200
    history_rows = history.json()
    history_dates = [row["effective_date"] for row in history_rows]
    assert history_dates == sorted(history_dates, reverse=True)
    assert [(row["effective_date"], row["price"]) for row in history_rows] == [
        (datetime.now().strftime("%Y-%m-%d"), 13.75),
        ("2026-08-08", 14.25),
    ]
    assert history_rows[0]["changed_by"] == "editor_config_precos"

    audit = isolated_app.client.get("/api/audit-log", headers=_headers(admin_token))
    assert audit.status_code == 200
    audit_actions = [row["action"] for row in audit.json() if row["product_key"] == product_key]
    assert {"ADD_PRODUCT", "PRICE_CHANGE", "PRICE_HISTORY", "RENAME_PRODUCT"} <= set(audit_actions)

    viewer_read = isolated_app.client.get("/api/prices", headers=_headers(viewer_token))
    assert viewer_read.status_code == 200
    viewer_write = isolated_app.client.put(
        "/api/prices",
        headers=_headers(viewer_token),
        json={"key": product_key, "price": 99},
    )
    assert viewer_write.status_code == 403

    deleted = isolated_app.client.delete(
        f"/api/prices/{product_key}",
        headers=_headers(editor_token),
    )
    assert deleted.status_code == 200
    assert deleted.json() == {"ok": True, "deleted": True}
    assert _fetch_one(
        isolated_app.db_paths["raios"],
        "SELECT key FROM product_prices WHERE key=?",
        (product_key,),
    ) is None


def test_config_drivers_and_vehicles_crud_permissions(isolated_app):
    admin_token = _login(isolated_app.client)
    _create_temp_user(isolated_app, "editor_config_frota", "editor123", "editor")
    _create_temp_user(isolated_app, "viewer_config_frota", "viewer123", "viewer")
    editor_token = _login(isolated_app.client, "editor_config_frota", "editor123")
    viewer_token = _login(isolated_app.client, "viewer_config_frota", "viewer123")

    driver_name = f"EntregadorCfg{uuid.uuid4().hex[:6]}"
    created_driver = isolated_app.client.post(
        "/api/drivers",
        headers=_headers(editor_token),
        json={"name": driver_name},
    )
    assert created_driver.status_code == 200
    assert created_driver.json() == {"ok": True, "driver": driver_name}

    duplicate_driver = isolated_app.client.post(
        "/api/drivers",
        headers=_headers(editor_token),
        json={"name": driver_name.lower()},
    )
    assert duplicate_driver.status_code == 200
    assert duplicate_driver.json()["driver"] == driver_name.lower()

    listed_drivers = isolated_app.client.get("/api/drivers/list", headers=_headers(admin_token))
    assert listed_drivers.status_code == 200
    assert any(row["delivery_person"] == driver_name.lower() for row in listed_drivers.json())

    renamed = isolated_app.client.post(
        "/api/drivers/rename",
        headers=_headers(editor_token),
        json={"old_name": driver_name.lower(), "new_name": f"{driver_name}Novo"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["updated"] == 0

    removed = isolated_app.client.delete(
        f"/api/drivers/{driver_name}Novo",
        headers=_headers(editor_token),
    )
    assert removed.status_code == 200
    assert removed.json()["driver"] == f"{driver_name}Novo"

    vehicle = isolated_app.client.post(
        "/api/vehicles",
        headers=_headers(editor_token),
        json={
            "name": "Carro Config",
            "plate": "abc-1234",
            "driver": f"{driver_name}Novo",
            "notes": "veiculo temporario",
        },
    )
    assert vehicle.status_code == 200
    assert vehicle.json() == {"ok": True}
    vehicle_row = _fetch_one(
        isolated_app.db_paths["raios"],
        "SELECT id,name,plate,driver,notes FROM vehicles WHERE name='Carro Config'",
    )
    assert vehicle_row["plate"] == "ABC-1234"

    listed_vehicles = isolated_app.client.get("/api/vehicles", headers=_headers(viewer_token))
    assert listed_vehicles.status_code == 200
    assert any(row["id"] == vehicle_row["id"] for row in listed_vehicles.json())

    viewer_create_vehicle = isolated_app.client.post(
        "/api/vehicles",
        headers=_headers(viewer_token),
        json={"name": "Viewer Carro", "plate": "vwv-0001"},
    )
    assert viewer_create_vehicle.status_code == 403

    updated_vehicle = isolated_app.client.put(
        f"/api/vehicles/{vehicle_row['id']}",
        headers=_headers(editor_token),
        json={"name": "Carro Config Editado", "plate": "xyz-9876", "notes": "editado"},
    )
    assert updated_vehicle.status_code == 200
    assert updated_vehicle.json() == {"ok": True}
    after_update = _fetch_one(
        isolated_app.db_paths["raios"],
        "SELECT name,plate,notes FROM vehicles WHERE id=?",
        (vehicle_row["id"],),
    )
    assert after_update == {
        "name": "Carro Config Editado",
        "plate": "XYZ-9876",
        "notes": "editado",
    }

    deleted_vehicle = isolated_app.client.delete(
        f"/api/vehicles/{vehicle_row['id']}",
        headers=_headers(editor_token),
    )
    assert deleted_vehicle.status_code == 200
    assert deleted_vehicle.json() == {"ok": True}


def test_config_users_are_admin_only_and_use_control_database(isolated_app):
    admin_token = _login(isolated_app.client)
    _create_temp_user(isolated_app, "viewer_config_users", "viewer123", "viewer")
    viewer_token = _login(isolated_app.client, "viewer_config_users", "viewer123")

    auth_db_paths = {
        "raios": str(isolated_app.db_paths["raios"]),
        "estrada": str(isolated_app.db_paths["estrada"]),
    }
    users_before = {
        company: {
            "path": auth_db_paths[company],
            "users_exists": _table_exists(isolated_app.db_paths[company], "users"),
            "users_count": _table_count(isolated_app.db_paths[company], "users"),
            "columns": _table_columns(isolated_app.db_paths[company], "users")
            if _table_exists(isolated_app.db_paths[company], "users")
            else [],
            "admin_count": _table_count(isolated_app.db_paths[company], "users")
            and _fetch_one(
                isolated_app.db_paths[company],
                "SELECT COUNT(*) AS total FROM users WHERE username='admin'",
            )["total"],
        }
        for company in ("raios", "estrada")
    }

    unauth = isolated_app.client.get("/api/users")
    assert unauth.status_code == 401
    viewer_list = isolated_app.client.get("/api/users", headers=_headers(viewer_token))
    assert viewer_list.status_code == 403

    username = f"editor_cfg_{uuid.uuid4().hex[:8]}"
    created = isolated_app.client.post(
        "/api/users",
        headers=_headers(admin_token, "estrada"),
        json={
            "username": username,
            "password": "editor123",
            "full_name": "Editor Config Criado",
            "role": "editor",
        },
    )
    assert created.status_code == 200
    user_id = created.json()["id"]

    users_raios = isolated_app.client.get("/api/users", headers=_headers(admin_token, "raios"))
    users_estrada = isolated_app.client.get("/api/users", headers=_headers(admin_token, "estrada"))
    assert users_raios.status_code == 200
    assert users_estrada.status_code == 200
    assert any(row["id"] == user_id for row in users_raios.json())
    # PENDENCIA: confirmar se usuarios/permissoes devem ser compartilhados ou isolados por empresa.
    # O app inicializa a tabela users nos dois bancos temporarios, mas login e /api/users usam get_control_db().
    assert any(row["id"] == user_id for row in users_estrada.json())
    assert isolated_app.module.get_control_db().execute("PRAGMA database_list").fetchone()[2] == auth_db_paths["raios"]
    assert users_before["raios"]["path"] != users_before["estrada"]["path"]
    assert users_before["raios"]["users_exists"] is True
    assert users_before["estrada"]["users_exists"] is True
    assert users_before["raios"]["columns"] == users_before["estrada"]["columns"]
    assert users_before["raios"]["admin_count"] == 1
    assert users_before["estrada"]["admin_count"] == 0
    assert _fetch_one(
        isolated_app.db_paths["raios"],
        "SELECT COUNT(*) AS total FROM users WHERE id=?",
        (user_id,),
    )["total"] == 1
    assert _fetch_one(
        isolated_app.db_paths["estrada"],
        "SELECT COUNT(*) AS total FROM users WHERE id=?",
        (user_id,),
    )["total"] == 0

    updated = isolated_app.client.put(
        f"/api/users/{user_id}",
        headers=_headers(admin_token),
        json={"full_name": "Editor Config Editado", "role": "viewer", "active": 1},
    )
    assert updated.status_code == 200
    assert updated.json() == {"ok": True}

    deleted = isolated_app.client.delete(
        f"/api/users/{user_id}",
        headers=_headers(admin_token),
    )
    assert deleted.status_code == 200
    assert deleted.json() == {"ok": True}


def test_config_tab_permissions_tab_order_and_monteiro_settings(isolated_app):
    admin_token = _login(isolated_app.client)
    _create_temp_user(isolated_app, "viewer_config_settings", "viewer123", "viewer")
    viewer_token = _login(isolated_app.client, "viewer_config_settings", "viewer123")

    default_permissions = isolated_app.client.get(
        "/api/settings/tab-permissions",
        headers=_headers(viewer_token),
    )
    assert default_permissions.status_code == 200
    assert "viewer" in default_permissions.json()

    saved_permissions = {
        "viewer": ["consolidado"],
        "editor": ["config", "cfg_precos"],
        "admin": ["config", "cfg_precos", "cfg_registro"],
    }
    put_permissions = isolated_app.client.put(
        "/api/settings/tab-permissions",
        headers=_headers(admin_token),
        json=saved_permissions,
    )
    assert put_permissions.status_code == 200
    assert put_permissions.json() == {"ok": True, "saved": saved_permissions}

    get_permissions = isolated_app.client.get(
        "/api/settings/tab-permissions",
        headers=_headers(admin_token),
    )
    assert get_permissions.status_code == 200
    assert get_permissions.json() == saved_permissions

    replacement_permissions = {
        "viewer": ["clientes"],
        "editor": ["config", "cfg_precos", "cfg_sebrae"],
        "admin": ["config", "cfg_precos", "cfg_registro", "cfg_importar"],
    }
    replace_permissions = isolated_app.client.put(
        "/api/settings/tab-permissions",
        headers=_headers(admin_token),
        json=replacement_permissions,
    )
    assert replace_permissions.status_code == 200
    assert replace_permissions.json() == {"ok": True, "saved": replacement_permissions}

    replaced_permissions = isolated_app.client.get(
        "/api/settings/tab-permissions",
        headers=_headers(admin_token),
    )
    assert replaced_permissions.status_code == 200
    assert replaced_permissions.json() == replacement_permissions
    assert replaced_permissions.json() != saved_permissions

    viewer_put_permissions = isolated_app.client.put(
        "/api/settings/tab-permissions",
        headers=_headers(viewer_token),
        json=replacement_permissions,
    )
    assert viewer_put_permissions.status_code == 403

    initial_order = isolated_app.client.get("/api/settings/tab-order", headers=_headers(admin_token))
    assert initial_order.status_code == 200
    assert initial_order.json() is None

    order = ["consolidado", "produtos", "config"]
    save_order = isolated_app.client.post(
        "/api/settings/tab-order",
        headers=_headers(admin_token),
        json=order,
    )
    assert save_order.status_code == 200
    assert save_order.json() == {"ok": True, "saved": order}

    saved_order = isolated_app.client.get("/api/settings/tab-order", headers=_headers(admin_token))
    assert saved_order.status_code == 200
    assert saved_order.json() == order

    replacement_order = ["clientes", "boletos", "config", "produtos"]
    replace_order = isolated_app.client.put(
        "/api/settings/tab-order",
        headers=_headers(admin_token),
        json=replacement_order,
    )
    assert replace_order.status_code == 200
    assert replace_order.json() == {"ok": True, "saved": replacement_order}

    replaced_order = isolated_app.client.get("/api/settings/tab-order", headers=_headers(admin_token))
    assert replaced_order.status_code == 200
    assert replaced_order.json() == replacement_order
    assert replaced_order.json() != order

    invalid_order = isolated_app.client.put(
        "/api/settings/tab-order",
        headers=_headers(admin_token),
        json={"ordem": order},
    )
    assert invalid_order.status_code == 400
    preserved_order = isolated_app.client.get("/api/settings/tab-order", headers=_headers(admin_token))
    assert preserved_order.status_code == 200
    assert preserved_order.json() == replacement_order

    payment_default = isolated_app.client.get(
        "/api/settings/monteiro-payment-permission",
        headers=_headers(admin_token),
    )
    assert payment_default.status_code == 200
    assert payment_default.json() == {"roles": ["admin"]}

    set_payment = isolated_app.client.put(
        "/api/settings/monteiro-payment-permission",
        headers=_headers(admin_token),
        json={"roles": ["admin", "editor"]},
    )
    assert set_payment.status_code == 200
    assert set_payment.json() == {"ok": True}

    calendar_default = isolated_app.client.get(
        "/api/settings/monteiro-calendar-permission",
        headers=_headers(admin_token),
    )
    assert calendar_default.status_code == 200
    assert calendar_default.json() == {"roles": ["admin"]}

    set_calendar = isolated_app.client.put(
        "/api/settings/monteiro-calendar-permission",
        headers=_headers(admin_token),
        json={"roles": ["viewer"]},
    )
    assert set_calendar.status_code == 200
    assert set_calendar.json() == {"ok": True, "roles": ["admin", "viewer"]}

    viewer_set_calendar = isolated_app.client.put(
        "/api/settings/monteiro-calendar-permission",
        headers=_headers(viewer_token),
        json={"roles": ["admin", "viewer"]},
    )
    assert viewer_set_calendar.status_code == 403


def test_config_data_isolation_by_company_for_prices_drivers_vehicles_and_settings(isolated_app):
    token = _login(isolated_app.client)
    price_key = f"CFG_ISO_{uuid.uuid4().hex[:8]}".upper()

    raios_price = isolated_app.client.post(
        "/api/prices",
        headers=_headers(token, "raios"),
        json={"key": price_key, "label": "Produto Isolado Raios", "price": 21},
    )
    estrada_price = isolated_app.client.post(
        "/api/prices",
        headers=_headers(token, "estrada"),
        json={"key": price_key, "label": "Produto Isolado Estrada", "price": 31},
    )
    assert raios_price.status_code == 200
    assert estrada_price.status_code == 200
    assert _fetch_one(
        isolated_app.db_paths["raios"],
        "SELECT label,price FROM product_prices WHERE key=?",
        (price_key,),
    ) == {"label": "Produto Isolado Raios", "price": 21.0}
    assert _fetch_one(
        isolated_app.db_paths["estrada"],
        "SELECT label,price FROM product_prices WHERE key=?",
        (price_key,),
    ) == {"label": "Produto Isolado Estrada", "price": 31.0}

    isolated_app.client.post(
        "/api/drivers",
        headers=_headers(token, "raios"),
        json={"name": "Motorista Raios Config"},
    )
    isolated_app.client.post(
        "/api/drivers",
        headers=_headers(token, "estrada"),
        json={"name": "Motorista Estrada Config"},
    )
    raios_drivers = isolated_app.client.get("/api/drivers/list", headers=_headers(token, "raios"))
    estrada_drivers = isolated_app.client.get("/api/drivers/list", headers=_headers(token, "estrada"))
    assert any(row["delivery_person"] == "Motorista Raios Config" for row in raios_drivers.json())
    assert all(row["delivery_person"] != "Motorista Estrada Config" for row in raios_drivers.json())
    assert any(row["delivery_person"] == "Motorista Estrada Config" for row in estrada_drivers.json())

    isolated_app.client.post(
        "/api/vehicles",
        headers=_headers(token, "raios"),
        json={"name": "Veiculo Raios Config", "plate": "RAI-1111"},
    )
    isolated_app.client.post(
        "/api/vehicles",
        headers=_headers(token, "estrada"),
        json={"name": "Veiculo Estrada Config", "plate": "EST-2222"},
    )
    raios_vehicles = isolated_app.client.get("/api/vehicles", headers=_headers(token, "raios"))
    estrada_vehicles = isolated_app.client.get("/api/vehicles", headers=_headers(token, "estrada"))
    assert [row["name"] for row in raios_vehicles.json()] == ["Veiculo Raios Config"]
    assert [row["name"] for row in estrada_vehicles.json()] == ["Veiculo Estrada Config"]

    isolated_app.client.put(
        "/api/settings/monteiro-payment-permission",
        headers=_headers(token, "raios"),
        json={"roles": ["admin", "editor"]},
    )
    isolated_app.client.put(
        "/api/settings/monteiro-payment-permission",
        headers=_headers(token, "estrada"),
        json={"roles": ["admin", "viewer"]},
    )
    assert isolated_app.client.get(
        "/api/settings/monteiro-payment-permission",
        headers=_headers(token, "raios"),
    ).json() == {"roles": ["admin", "editor"]}
    assert isolated_app.client.get(
        "/api/settings/monteiro-payment-permission",
        headers=_headers(token, "estrada"),
    ).json() == {"roles": ["admin", "viewer"]}
