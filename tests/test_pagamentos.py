import sqlite3
import sys
import types
import uuid
from datetime import datetime, timedelta
from json import JSONDecodeError

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
        "sale_date": "2026-06-05",
        "sale_time": "08:00",
        "client": "Cliente Pagamento Padrao",
        "product": "Produto Pagamento",
        "nf_number": "PAY-001",
        "quantity": 1,
        "unit_price": 100,
        "total": 100,
        "notes": "venda temporaria para pagamento",
        "delivery_person": "Lucas",
        "plate": "PAY-0001",
        "source": "manual",
    }
    payload.update(overrides)
    return payload


def _monteiro_sale_payload(**overrides):
    payload = {
        "saledate": "2026-06-05",
        "client": "Cliente Pagamento Padrao",
        "nf_number": "PAY-001",
        "driver": "Lucas",
        "vehicle": "Carro Teste",
        "plate": "PAY-0001",
        "items": [
            {
                "product": "Produto Pagamento",
                "quantity": 1,
                "unitprice": 100,
                "total": 100,
                "notes": "venda monteiro temporaria para pagamento",
            }
        ],
    }
    payload.update(overrides)
    return payload


def _payment_payload(**overrides):
    payload = {
        "client": "Cliente Pagamento Padrao",
        "payment_date": "2026-06-16",
        "amount": 100,
        "payment_type": "repasse",
        "notes": "pagamento temporario",
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


def _create_monteiro_sale(test_client, token, company="raios", **overrides):
    response = test_client.post(
        "/api/monteiro/sales",
        headers=_headers(token, company),
        json=_monteiro_sale_payload(**overrides),
    )
    assert response.status_code == 200
    return response.json()


def _create_payment(test_client, token, company="raios", **overrides):
    response = test_client.post(
        "/api/monteiro/payments",
        headers=_headers(token, company),
        json=_payment_payload(**overrides),
    )
    assert response.status_code == 200
    assert response.json() == {"ok": True}

    client_name = overrides.get("client", _payment_payload()["client"])
    month = overrides.get(
        "month",
        overrides.get("payment_date", _payment_payload()["payment_date"])[5:7],
    )
    year = overrides.get(
        "year",
        overrides.get("payment_date", _payment_payload()["payment_date"])[:4],
    )
    listed = test_client.get(
        f"/api/monteiro/payments?client={client_name}&month={month}&year={year}",
        headers=_headers(token, company),
    )
    assert listed.status_code == 200
    rows = listed.json()
    assert rows
    return rows[0]


def _create_temp_user(isolated_app, username, password, role):
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    user_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO users(id, username, password_hash, full_name, role, active) VALUES(?,?,?,?,?,1)",
        (
            user_id,
            username,
            isolated_app.module.hash_password(password),
            f"Usuario {role} Pagamentos",
            role,
        ),
    )
    conn.commit()
    conn.close()
    return user_id


def _set_payment_perm_value(isolated_app, value, company="raios"):
    conn = sqlite3.connect(isolated_app.db_paths[company])
    conn.execute(
        "INSERT OR REPLACE INTO settings(key,value) VALUES('monteiro_payment_perm',?)",
        (value,),
    )
    conn.commit()
    conn.close()


def _delete_payment_perm_value(isolated_app, company="raios"):
    conn = sqlite3.connect(isolated_app.db_paths[company])
    conn.execute("DELETE FROM settings WHERE key='monteiro_payment_perm'")
    conn.commit()
    conn.close()


def _payment_rows_count(isolated_app):
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    total = conn.execute("SELECT COUNT(*) FROM monteiro_payments").fetchone()[0]
    conn.close()
    return total


def _payment_row_by_id(isolated_app, payment_id):
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM monteiro_payments WHERE id=?", (payment_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def _assert_http_exception(exc_info, status_code, detail):
    assert exc_info.value.status_code == status_code
    assert exc_info.value.detail == detail


def test_check_payment_perm_current_auth_precedence_and_default_roles(isolated_app):
    check_payment_perm = isolated_app.module._check_payment_perm
    admin_token = _login(isolated_app.client)
    _create_temp_user(isolated_app, "editor_perm_default", "editor123", "editor")
    _create_temp_user(isolated_app, "viewer_perm_default", "viewer123", "viewer")
    editor_token = _login(isolated_app.client, "editor_perm_default", "editor123")
    viewer_token = _login(isolated_app.client, "viewer_perm_default", "viewer123")

    _delete_payment_perm_value(isolated_app)

    assert check_payment_perm(admin_token)["role"] == "admin"
    with pytest.raises(isolated_app.module.HTTPException) as editor_exc:
        check_payment_perm(editor_token)
    _assert_http_exception(
        editor_exc,
        403,
        "Seu perfil nÃ£o tem permissÃ£o para lanÃ§ar pagamentos.",
    )
    with pytest.raises(isolated_app.module.HTTPException) as viewer_exc:
        check_payment_perm(viewer_token)
    _assert_http_exception(
        viewer_exc,
        403,
        "Seu perfil nÃ£o tem permissÃ£o para lanÃ§ar pagamentos.",
    )

    _set_payment_perm_value(isolated_app, "{json-invalido")
    with pytest.raises(isolated_app.module.HTTPException) as invalid_token_exc:
        check_payment_perm("token-invalido")
    _assert_http_exception(
        invalid_token_exc,
        401,
        "SessÃ£o invÃ¡lida. FaÃ§a login novamente.",
    )
    with pytest.raises(isolated_app.module.HTTPException) as empty_token_exc:
        check_payment_perm("")
    _assert_http_exception(
        empty_token_exc,
        401,
        "SessÃ£o invÃ¡lida. FaÃ§a login novamente.",
    )

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    conn.execute("UPDATE sessions SET expires_at=datetime('now','-1 minute') WHERE token=?", (editor_token,))
    conn.commit()
    conn.close()
    with pytest.raises(isolated_app.module.HTTPException) as expired_exc:
        check_payment_perm(editor_token)
    _assert_http_exception(
        expired_exc,
        401,
        "SessÃ£o invÃ¡lida. FaÃ§a login novamente.",
    )


def test_check_payment_perm_current_config_value_contract(isolated_app):
    check_payment_perm = isolated_app.module._check_payment_perm
    admin_token = _login(isolated_app.client)
    _create_temp_user(isolated_app, "editor_perm_values", "editor123", "editor")
    _create_temp_user(isolated_app, "viewer_perm_values", "viewer123", "viewer")
    _create_temp_user(isolated_app, "custom_perm_values", "custom123", "custom")
    editor_token = _login(isolated_app.client, "editor_perm_values", "editor123")
    viewer_token = _login(isolated_app.client, "viewer_perm_values", "viewer123")
    custom_token = _login(isolated_app.client, "custom_perm_values", "custom123")

    _set_payment_perm_value(isolated_app, '["admin"]')
    assert check_payment_perm(admin_token)["role"] == "admin"
    with pytest.raises(isolated_app.module.HTTPException):
        check_payment_perm(editor_token)

    _set_payment_perm_value(isolated_app, '["admin", "editor"]')
    assert check_payment_perm(editor_token)["role"] == "editor"
    with pytest.raises(isolated_app.module.HTTPException):
        check_payment_perm(viewer_token)

    _set_payment_perm_value(isolated_app, '["viewer"]')
    assert check_payment_perm(viewer_token)["role"] == "viewer"
    with pytest.raises(isolated_app.module.HTTPException):
        check_payment_perm(admin_token)

    _set_payment_perm_value(isolated_app, '["custom"]')
    assert check_payment_perm(custom_token)["role"] == "custom"

    _set_payment_perm_value(isolated_app, '{"admin": true}')
    assert check_payment_perm(admin_token)["role"] == "admin"

    _set_payment_perm_value(isolated_app, '"admin"')
    assert check_payment_perm(admin_token)["role"] == "admin"

    _set_payment_perm_value(isolated_app, '["editor", 123]')
    assert check_payment_perm(editor_token)["role"] == "editor"
    with pytest.raises(isolated_app.module.HTTPException):
        check_payment_perm(custom_token)

    for raw in ("", "{json-invalido"):
        _set_payment_perm_value(isolated_app, raw)
        with pytest.raises(JSONDecodeError):
            check_payment_perm(admin_token)

    _set_payment_perm_value(isolated_app, "123")
    with pytest.raises(TypeError):
        check_payment_perm(admin_token)


def test_monteiro_payment_permission_consumers_block_before_writes(isolated_app):
    admin_token = _login(isolated_app.client)
    _create_temp_user(isolated_app, "editor_perm_routes", "editor123", "editor")
    _create_temp_user(isolated_app, "viewer_perm_routes", "viewer123", "viewer")
    editor_token = _login(isolated_app.client, "editor_perm_routes", "editor123")
    viewer_token = _login(isolated_app.client, "viewer_perm_routes", "viewer123")

    before_post = _payment_rows_count(isolated_app)
    viewer_post = isolated_app.client.post(
        "/api/monteiro/payments",
        headers=_headers(viewer_token),
        json=_payment_payload(client="Cliente Viewer Bloqueio Escrita"),
    )
    assert viewer_post.status_code == 403
    assert _payment_rows_count(isolated_app) == before_post

    editor_post = isolated_app.client.post(
        "/api/monteiro/payments",
        headers=_headers(editor_token),
        json=_payment_payload(client="Cliente Editor Bloqueio Escrita"),
    )
    assert editor_post.status_code == 403
    assert _payment_rows_count(isolated_app) == before_post

    _set_payment_perm_value(isolated_app, '["admin", "editor"]')
    editor_post_allowed = isolated_app.client.post(
        "/api/monteiro/payments",
        headers=_headers(editor_token),
        json=_payment_payload(client="Cliente Editor Escrita Permitida"),
    )
    assert editor_post_allowed.status_code == 200

    payment = _create_payment(
        isolated_app.client,
        admin_token,
        client="Cliente Permissao Original",
        amount=333,
    )
    _set_payment_perm_value(isolated_app, '["admin"]')

    blocked_update = isolated_app.client.put(
        f"/api/monteiro/payments/{payment['id']}",
        headers=_headers(editor_token),
        json=_payment_payload(client="Cliente Permissao Alterado", amount=444),
    )
    assert blocked_update.status_code == 403
    assert _payment_row_by_id(isolated_app, payment["id"])["client"] == "Cliente Permissao Original"

    viewer_update = isolated_app.client.put(
        f"/api/monteiro/payments/{payment['id']}",
        headers=_headers(viewer_token),
        json=_payment_payload(client="Cliente Viewer Alterado", amount=555),
    )
    assert viewer_update.status_code == 403
    assert _payment_row_by_id(isolated_app, payment["id"])["amount"] == 333

    admin_update = isolated_app.client.put(
        f"/api/monteiro/payments/{payment['id']}",
        headers=_headers(admin_token),
        json=_payment_payload(client="Cliente Admin Alterado", amount=444),
    )
    assert admin_update.status_code == 200
    assert _payment_row_by_id(isolated_app, payment["id"])["client"] == "Cliente Admin Alterado"

    blocked_delete = isolated_app.client.delete(
        f"/api/monteiro/payments/{payment['id']}",
        headers=_headers(editor_token),
    )
    assert blocked_delete.status_code == 403
    assert _payment_row_by_id(isolated_app, payment["id"]) is not None

    _set_payment_perm_value(isolated_app, '["admin", "editor"]')
    editor_delete = isolated_app.client.delete(
        f"/api/monteiro/payments/{payment['id']}",
        headers=_headers(editor_token),
    )
    assert editor_delete.status_code == 200
    assert _payment_row_by_id(isolated_app, payment["id"]) is None


def test_monteiro_payment_permission_current_scope_forces_raios(isolated_app):
    _create_temp_user(isolated_app, "viewer_perm_scope", "viewer123", "viewer")
    viewer_token = _login(isolated_app.client, "viewer_perm_scope", "viewer123", company="estrada")

    _delete_payment_perm_value(isolated_app, "raios")
    _set_payment_perm_value(isolated_app, '["admin", "viewer"]', company="estrada")

    blocked_by_raios_scope = isolated_app.client.post(
        "/api/monteiro/payments",
        headers=_headers(viewer_token, "estrada"),
        json=_payment_payload(client="Cliente Viewer Estrada Ignorada"),
    )
    assert blocked_by_raios_scope.status_code == 403

    _set_payment_perm_value(isolated_app, '["admin", "viewer"]', company="raios")
    allowed_by_raios_scope = isolated_app.client.post(
        "/api/monteiro/payments",
        headers=_headers(viewer_token, "estrada"),
        json=_payment_payload(client="Cliente Viewer Raios Forcado"),
    )
    assert allowed_by_raios_scope.status_code == 200
    assert _payment_rows_count(isolated_app) == 1


def _freeze_datetime_module(monkeypatch, frozen_now):
    class FrozenDateTime:
        @classmethod
        def now(cls):
            return frozen_now

    monkeypatch.setitem(
        sys.modules,
        "datetime",
        types.SimpleNamespace(datetime=FrozenDateTime, timedelta=timedelta),
    )


def test_pal_period_where_current_month_year_and_invalid_contract(isolated_app):
    pal_period_where = isolated_app.module._pal_period_where

    assert pal_period_where("mensal", "6", 2026) == (
        ["strftime('%m',saledate)=?", "strftime('%Y',saledate)=?"],
        ["06", "2026"],
    )
    assert pal_period_where("anual", "06", "2026") == (
        ["strftime('%m',saledate)=?", "strftime('%Y',saledate)=?"],
        ["06", "2026"],
    )
    assert pal_period_where(None, "", "") == ([], [])
    assert pal_period_where("desconhecido", " 6 ", "ano") == (
        ["strftime('%m',saledate)=?", "strftime('%Y',saledate)=?"],
        [" 6 ", "ano"],
    )
    assert pal_period_where("mensal", "13", None) == (
        ["strftime('%m',saledate)=?"],
        ["13"],
    )
    with pytest.raises(AttributeError):
        pal_period_where("mensal", 6, 2026)


@pytest.mark.parametrize(
    ("frozen_now", "expected_current", "expected_previous"),
    [
        (
            datetime(2026, 6, 1, 10, 30),
            ["2026-05-18", "2026-06-01"],
            ["2026-05-03", "2026-05-17"],
        ),
        (
            datetime(2026, 12, 31, 23, 59),
            ["2026-12-17", "2026-12-31"],
            ["2026-12-02", "2026-12-16"],
        ),
        (
            datetime(2027, 1, 1, 0, 1),
            ["2026-12-18", "2027-01-01"],
            ["2026-12-03", "2026-12-17"],
        ),
    ],
)
def test_pal_period_where_current_quinzenal_contract(
    isolated_app,
    monkeypatch,
    frozen_now,
    expected_current,
    expected_previous,
):
    _freeze_datetime_module(monkeypatch, frozen_now)
    pal_period_where = isolated_app.module._pal_period_where

    assert pal_period_where("quinzenal", "2", "2020") == (
        ["saledate >= ? AND saledate <= ?"],
        expected_current,
    )
    assert pal_period_where("quinzenal_prev", "2", "2020") == (
        ["saledate >= ? AND saledate <= ?"],
        expected_previous,
    )


def test_pay_period_map_current_mapping_and_invalid_contract(isolated_app):
    pay_period_map = isolated_app.module._pay_period_map

    assert pay_period_map("mensal", "6", 2026) == ("06", "2026")
    assert pay_period_map("anual", "06", "2026") == ("06", "2026")
    assert pay_period_map("quinzenal_prev", "4", 2026) == ("04", "2026")
    assert pay_period_map(None, "", "") == ("", "")
    assert pay_period_map("desconhecido", " 6 ", "ano") == (" 6 ", "ano")
    assert pay_period_map("mensal", "13", None) == ("13", "")
    with pytest.raises(AttributeError):
        pay_period_map("mensal", 6, 2026)


def test_pay_period_map_current_quinzenal_uses_backend_now(isolated_app, monkeypatch):
    _freeze_datetime_module(monkeypatch, datetime(2027, 1, 1, 0, 1))
    pay_period_map = isolated_app.module._pay_period_map

    assert pay_period_map("quinzenal", "6", "2026") == ("01", "2027")


def test_pagamentos_list_create_read_update_delete_and_filters(isolated_app):
    token = _login(isolated_app.client)

    first = _create_payment(
        isolated_app.client,
        token,
        client="Cliente Pagamento CRUD",
        payment_date="2026-06-16",
        amount=250.75,
        payment_type="repasse",
        notes="primeiro pagamento",
    )
    second = _create_payment(
        isolated_app.client,
        token,
        client="Cliente Pagamento CRUD",
        payment_date="2026-07-02",
        amount=99.25,
        payment_type="ajuste",
        notes="segundo pagamento",
    )

    assert first["client"] == "Cliente Pagamento CRUD"
    assert first["payment_date"] == "2026-06-16"
    assert first["amount"] == 250.75
    assert first["month"] == "06"
    assert first["year"] == "2026"
    assert first["payment_type"] == "repasse"
    assert first["notes"] == "primeiro pagamento"

    june = isolated_app.client.get(
        "/api/monteiro/payments?client=Cliente Pagamento CRUD&month=6&year=2026",
        headers=_headers(token),
    )
    assert june.status_code == 200
    assert [row["id"] for row in june.json()] == [first["id"]]

    july = isolated_app.client.get(
        "/api/monteiro/payments?client=Cliente Pagamento CRUD&period=mensal&month=7&year=2026",
        headers=_headers(token),
    )
    assert july.status_code == 200
    assert [row["id"] for row in july.json()] == [second["id"]]

    update = isolated_app.client.put(
        f"/api/monteiro/payments/{first['id']}",
        headers=_headers(token),
        json=_payment_payload(
            client="Cliente Pagamento CRUD Editado",
            payment_date="2026-08-03",
            amount=300.5,
            payment_type="acerto",
            notes="pagamento editado",
        ),
    )
    assert update.status_code == 200
    assert update.json() == {"ok": True}

    after_update = isolated_app.client.get(
        "/api/monteiro/payments?client=Cliente Pagamento CRUD Editado&month=8&year=2026",
        headers=_headers(token),
    )
    assert after_update.status_code == 200
    updated_rows = after_update.json()
    assert len(updated_rows) == 1
    assert updated_rows[0]["id"] == first["id"]
    assert updated_rows[0]["amount"] == 300.5
    assert updated_rows[0]["month"] == "08"
    assert updated_rows[0]["payment_type"] == "acerto"

    delete = isolated_app.client.delete(
        f"/api/monteiro/payments/{second['id']}",
        headers=_headers(token),
    )
    assert delete.status_code == 200
    assert delete.json() == {"ok": True}

    after_delete = isolated_app.client.get(
        "/api/monteiro/payments?client=Cliente Pagamento CRUD&month=7&year=2026",
        headers=_headers(token),
    )
    assert after_delete.status_code == 200
    assert after_delete.json() == []


def test_pagamentos_summary_report_partial_total_balance_and_multiple_payments(isolated_app):
    token = _login(isolated_app.client)
    client_name = "Cliente Pagamento Resumo"
    _create_monteiro_sale(
        isolated_app.client,
        token,
        client=client_name,
        saledate="2026-06-05",
        nf_number="PAY-RES-001",
        items=[
            {
                "product": "Produto Pagamento A",
                "quantity": 2,
                "unitprice": 100,
                "total": 200,
            }
        ],
    )
    _create_monteiro_sale(
        isolated_app.client,
        token,
        client=client_name,
        saledate="2026-06-16",
        nf_number="PAY-RES-002",
        items=[
            {
                "product": "Produto Pagamento B",
                "quantity": 3,
                "unitprice": 100,
                "total": 300,
            }
        ],
    )

    partial = _create_payment(
        isolated_app.client,
        token,
        client=client_name,
        payment_date="2026-06-20",
        amount=200,
        payment_type="parcial",
    )
    summary_partial = isolated_app.client.get(
        f"/api/monteiro/payments/summary?client={client_name}&month=6&year=2026",
        headers=_headers(token),
    )
    assert summary_partial.status_code == 200
    assert summary_partial.json() == {
        "total_vendido": 500,
        "num_notas": 2,
        "total_pago": 200,
        "num_pagamentos": 1,
        "ultimo_pagamento": "2026-06-20",
        "saldo": 300,
    }

    total = _create_payment(
        isolated_app.client,
        token,
        client=client_name,
        payment_date="2026-06-25",
        amount=300,
        payment_type="quitacao",
    )
    summary_total = isolated_app.client.get(
        f"/api/monteiro/payments/summary?client={client_name}&period=mensal&month=6&year=2026",
        headers=_headers(token),
    )
    assert summary_total.status_code == 200
    assert summary_total.json() == {
        "total_vendido": 500,
        "num_notas": 2,
        "total_pago": 500,
        "num_pagamentos": 2,
        "ultimo_pagamento": "2026-06-25",
        "saldo": 0,
    }

    report = isolated_app.client.get(
        f"/api/monteiro/payments/report?client={client_name}&month=6&year=2026",
        headers=_headers(token),
    )
    assert report.status_code == 200
    body = report.json()
    assert body["client"] == client_name
    assert body["period"] == "06/2026"
    assert body["total_vendas"] == 500
    assert body["total_pago"] == 500
    assert body["saldo"] == 0
    assert [row["nf_number"] for row in body["vendas"]] == [
        "PAY-RES-001",
        "PAY-RES-002",
    ]
    assert [row["id"] for row in body["pagamentos"]] == [partial["id"], total["id"]]
    assert body["extrato"] == [
        {
            "tipo": "nota",
            "data": "2026-06-05",
            "descricao": "NF PAY-RES-001",
            "valor": 200,
        },
        {
            "tipo": "nota",
            "data": "2026-06-16",
            "descricao": "NF PAY-RES-002",
            "valor": 300,
        },
        {
            "tipo": "total_notas",
            "data": "",
            "descricao": "Total das notas",
            "valor": 500,
        },
        {
            "tipo": "pagamento",
            "data": "2026-06-20",
            "descricao": "Pagamento: parcial",
            "valor": -200,
        },
        {
            "tipo": "pagamento",
            "data": "2026-06-25",
            "descricao": "Pagamento: quitacao",
            "valor": -300,
        },
    ]


def test_pagamentos_negative_balance_when_payment_has_no_matching_monteiro_sale(isolated_app):
    token = _login(isolated_app.client)
    client_name = "Cliente Pagamento Sem Venda"
    _create_payment(
        isolated_app.client,
        token,
        client=client_name,
        payment_date="2026-06-18",
        amount=123.45,
        payment_type="credito",
    )

    summary = isolated_app.client.get(
        f"/api/monteiro/payments/summary?client={client_name}&month=6&year=2026",
        headers=_headers(token),
    )
    assert summary.status_code == 200
    assert summary.json() == {
        "total_vendido": 0.0,
        "num_notas": 0,
        "total_pago": 123.45,
        "num_pagamentos": 1,
        "ultimo_pagamento": "2026-06-18",
        "saldo": -123.45,
    }
    # Caracterizacao atual: saldo = total_vendido - total_pago.


def test_pagamentos_auth_permissions_and_invalid_payloads(isolated_app):
    admin_token = _login(isolated_app.client)
    _create_temp_user(isolated_app, "editor_pagamentos", "editor123", "editor")
    _create_temp_user(isolated_app, "viewer_pagamentos", "viewer123", "viewer")
    editor_token = _login(isolated_app.client, "editor_pagamentos", "editor123")
    viewer_token = _login(isolated_app.client, "viewer_pagamentos", "viewer123")

    read_without_token = isolated_app.client.get("/api/monteiro/payments")
    assert read_without_token.status_code == 401

    create_without_token = isolated_app.client.post(
        "/api/monteiro/payments",
        json=_payment_payload(),
    )
    assert create_without_token.status_code == 422

    viewer_read = isolated_app.client.get(
        "/api/monteiro/payments",
        headers=_headers(viewer_token),
    )
    assert viewer_read.status_code == 200

    viewer_create = isolated_app.client.post(
        "/api/monteiro/payments",
        headers=_headers(viewer_token),
        json=_payment_payload(client="Cliente Viewer Pagamento"),
    )
    assert viewer_create.status_code == 403

    editor_default_create = isolated_app.client.post(
        "/api/monteiro/payments",
        headers=_headers(editor_token),
        json=_payment_payload(client="Cliente Editor Sem Permissao"),
    )
    assert editor_default_create.status_code == 403

    permission = isolated_app.client.put(
        "/api/settings/monteiro-payment-permission",
        headers=_headers(admin_token),
        json={"roles": ["admin", "editor"]},
    )
    assert permission.status_code == 200
    assert permission.json() == {"ok": True}

    editor_allowed_create = isolated_app.client.post(
        "/api/monteiro/payments",
        headers=_headers(editor_token),
        json=_payment_payload(client="Cliente Editor Permitido"),
    )
    assert editor_allowed_create.status_code == 200
    assert editor_allowed_create.json() == {"ok": True}

    missing_client = isolated_app.client.post(
        "/api/monteiro/payments",
        headers=_headers(admin_token),
        json=_payment_payload(client=""),
    )
    assert missing_client.status_code == 400

    missing_date = isolated_app.client.post(
        "/api/monteiro/payments",
        headers=_headers(admin_token),
        json=_payment_payload(payment_date=""),
    )
    assert missing_date.status_code == 400

    zero_amount = isolated_app.client.post(
        "/api/monteiro/payments",
        headers=_headers(admin_token),
        json=_payment_payload(amount=0),
    )
    assert zero_amount.status_code == 400


def test_pagamentos_nonexistent_ids_current_behavior(isolated_app):
    token = _login(isolated_app.client)

    update_missing = isolated_app.client.put(
        "/api/monteiro/payments/999999",
        headers=_headers(token),
        json=_payment_payload(client="Cliente Pagamento Inexistente"),
    )
    assert update_missing.status_code == 200
    assert update_missing.json() == {"ok": True}

    delete_missing = isolated_app.client.delete(
        "/api/monteiro/payments/999999",
        headers=_headers(token),
    )
    assert delete_missing.status_code == 200
    assert delete_missing.json() == {"ok": True}


def test_pagamentos_are_isolated_by_x_company(isolated_app):
    token = _login(isolated_app.client)

    raios_payment = _create_payment(
        isolated_app.client,
        token,
        company="raios",
        client="Cliente Pagamento Raios",
        payment_date="2026-06-10",
        amount=111,
    )
    estrada_payment = _create_payment(
        isolated_app.client,
        token,
        company="estrada",
        client="Cliente Pagamento Estrada",
        payment_date="2026-06-10",
        amount=222,
    )

    raios_rows = isolated_app.client.get(
        "/api/monteiro/payments?month=6&year=2026",
        headers=_headers(token, "raios"),
    )
    assert raios_rows.status_code == 200
    assert [row["id"] for row in raios_rows.json()] == [
        estrada_payment["id"],
        raios_payment["id"],
    ]
    assert {row["client"] for row in raios_rows.json()} == {
        "Cliente Pagamento Raios",
        "Cliente Pagamento Estrada",
    }

    estrada_rows = isolated_app.client.get(
        "/api/monteiro/payments?month=6&year=2026",
        headers=_headers(token, "estrada"),
    )
    assert estrada_rows.status_code == 200
    assert estrada_rows.json() == raios_rows.json()

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    columns = [row[1] for row in conn.execute("PRAGMA table_info(monteiro_payments)").fetchall()]
    conn.close()
    assert "company" not in columns

    raios_summary = isolated_app.client.get(
        "/api/monteiro/payments/summary?month=6&year=2026",
        headers=_headers(token, "raios"),
    )
    assert raios_summary.status_code == 200
    assert raios_summary.json()["total_pago"] == 333

    estrada_summary = isolated_app.client.get(
        "/api/monteiro/payments/summary?month=6&year=2026",
        headers=_headers(token, "estrada"),
    )
    assert estrada_summary.status_code == 200
    assert estrada_summary.json() == raios_summary.json()
    # PENDENCIA: confirmar se pagamentos Monteiro devem ser compartilhados ou isolados por empresa.
    # Comportamento atual: rotas /api/monteiro/* forcam escopo em raios e ignoram x-company=estrada.
