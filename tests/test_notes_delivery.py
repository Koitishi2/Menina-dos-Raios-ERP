import json
import sqlite3
import uuid

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
        "client": "Cliente Nota Entrega",
        "product": "Produto Nota Entrega",
        "nf_number": "NF-ENT-001",
        "quantity": 1,
        "unit_price": 100,
        "total": 100,
        "notes": "nota temporaria de entrega",
        "delivery_person": "Lucas",
        "plate": "ENT-0001",
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


def _list_sales(test_client, token, company="raios", query=""):
    response = test_client.get(
        f"/api/sales{query}",
        headers=_headers(token, company),
    )
    assert response.status_code == 200
    return response.json()


def _mark_delivered(test_client, token, sale_id, company="raios", **body):
    response = test_client.put(
        f"/api/sales/{sale_id}/delivered",
        headers=_headers(token, company),
        json=body,
    )
    assert response.status_code == 200
    return response.json()


def _app_note_payload(**overrides):
    payload = {
        "external_id": f"nota-app-{uuid.uuid4().hex}",
        "client": "Cliente Nota App",
        "date": "20/08/2026",
        "items": [
            {
                "product": "Produto App Original",
                "quantity": 1,
                "weight": 1,
                "unit": "KG",
                "unit_price": 10,
            }
        ],
    }
    payload.update(overrides)
    return payload


def _create_app_note_mobile(test_client, isolated_app, **overrides):
    response = test_client.post(
        "/api/app-notes/mobile",
        headers={"x-app-token": isolated_app.module.APP_NOTES_TOKEN},
        json=_app_note_payload(**overrides),
    )
    assert response.status_code == 200
    return response.json()["note"]


def _assert_app_note_http_error(exc_info, status_code, detail):
    assert exc_info.value.status_code == status_code
    assert exc_info.value.detail == detail


def test_clean_app_note_current_basic_header_and_return_contract(isolated_app):
    clean = isolated_app.module._clean_app_note
    assert clean.__module__ == "app_notes_domain"

    client, note_date, items, total = clean(
        {
            "client": "  Cliente Nota Limpa  ",
            "date": " 20/08/2026 ",
            "note_date": "21/08/2026",
            "items": [
                {
                    "product": " Produto Limpo ",
                    "quantity": "2",
                    "weight": "3.5",
                    "unit": " KG ",
                    "unit_price": "4.25",
                    "extra": "ignorado",
                }
            ],
        }
    )

    assert (client, note_date, total) == ("Cliente Nota Limpa", "20/08/2026", 14.88)
    assert isinstance(items, list)
    assert len(items) == 1
    assert items[0] == {
        "product": "Produto Limpo",
        "quantity": 2.0,
        "quantity_provided": True,
        "weight": 3.5,
        "unit": "KG",
        "unit_price": 4.25,
        "price_provided": True,
        "position": 0,
    }

    assert clean({"items": []}) == ("", "", [], 0.0)
    assert clean({"client": None, "note_date": " 22/08/2026 ", "items": None}) == (
        "",
        "22/08/2026",
        [],
        0.0,
    )
    long_client = " C" * 200
    assert clean(
        {
            "client": long_client,
            "date": "",
            "note_date": "1234567890123456789012345",
            "items": [],
        }
    ) == (long_client.strip()[:120], "12345678901234567890", [], 0.0)


def test_clean_app_note_current_items_normalization_and_total_contract(isolated_app):
    clean = isolated_app.module._clean_app_note

    client, note_date, items, total = clean(
        {
            "client": "Cliente Itens",
            "note_date": "23/08/2026",
            "items": [
                "ignorado",
                {
                    "product": None,
                    "quantity": "",
                    "unit": None,
                    "unit_price": "",
                },
                {
                    "product": "P" * 200,
                    "quantity": 5,
                    "unit": "U" * 30,
                    "price": 2,
                },
                {
                    "product": "Produto Sem Preco",
                    "quantity": 4,
                    "weight": None,
                },
                {
                    "product": "Produto Peso Decimal",
                    "quantity": 2,
                    "weight": 1.5,
                    "unit_price": 3,
                },
                {
                    "product": "Produto Zero",
                    "quantity": 7,
                    "unit_price": 0,
                },
            ],
        }
    )

    assert (client, note_date, total) == ("Cliente Itens", "23/08/2026", 14.5)
    assert [item["position"] for item in items] == [1, 2, 3, 4, 5]
    assert items[0] == {
        "product": "",
        "quantity": 0.0,
        "quantity_provided": False,
        "weight": 0.0,
        "unit": "",
        "unit_price": 0.0,
        "price_provided": False,
        "position": 1,
    }
    assert items[1]["product"] == "P" * 160
    assert items[1]["unit"] == "U" * 20
    assert items[1]["quantity"] == 5.0
    assert items[1]["weight"] == 5.0
    assert items[1]["unit_price"] == 2.0
    assert items[1]["price_provided"] is True
    assert items[2]["weight"] == 4.0
    assert items[2]["price_provided"] is False
    assert items[3]["weight"] == 1.5
    assert items[3]["unit_price"] == 3.0
    assert items[4]["price_provided"] is True
    assert items[4]["unit_price"] == 0.0


def test_clean_app_note_current_invalid_input_errors(isolated_app):
    clean = isolated_app.module._clean_app_note

    for body in (
        {"items": "nao-lista"},
        {"items": [{}] * 101},
    ):
        with pytest.raises(isolated_app.module.HTTPException) as exc:
            clean(body)
        _assert_app_note_http_error(
            exc,
            400,
            "Lista de itens invÃ¡lida (mÃ¡ximo 100).",
        )

    for item in (
        {"quantity": "abc", "unit_price": 1},
        {"quantity": 1, "weight": "abc", "unit_price": 1},
        {"quantity": 1, "unit_price": "abc"},
        {"quantity": object(), "unit_price": 1},
    ):
        with pytest.raises(isolated_app.module.HTTPException) as exc:
            clean({"items": [item]})
        _assert_app_note_http_error(exc, 400, "Quantidade ou preÃ§o invÃ¡lido.")

    for item in (
        {"quantity": 100000001, "unit_price": 1},
        {"quantity": 1, "weight": -100000001, "unit_price": 1},
        {"quantity": 1, "unit_price": 100000001},
    ):
        with pytest.raises(isolated_app.module.HTTPException) as exc:
            clean({"items": [item]})
        _assert_app_note_http_error(exc, 400, "Valor fora do limite permitido.")


def _replace_paladar_products(db_path, rows):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("DELETE FROM paladar_products")
        conn.executemany(
            "INSERT INTO paladar_products(name,suggested_price,active) VALUES(?,?,?)",
            rows,
        )
        conn.commit()
    finally:
        conn.close()


def test_app_note_catalog_prices_current_selection_normalization_and_aliases(isolated_app):
    catalog_prices = isolated_app.module._app_note_catalog_prices
    normalize_name = isolated_app.module._normalize_name

    _replace_paladar_products(isolated_app.db_paths["raios"], [])
    assert catalog_prices() == {}

    _replace_paladar_products(
        isolated_app.db_paths["raios"],
        [
            (" Produto App KG ", 10, 1),
            ("Produto App Inativo KG", 99, 0),
            ("Produto Sem Preco UN", None, 1),
            ("Produto Zero CX", 0, 1),
            ("Produto Decimal", 7.25, 1),
            ("   ", 13, 1),
            ("AÇÚCAR Cristal KG", 4.5, 1),
            ("Produto Embalado (UN)", 6, 1),
            ("Produto Litro LT", 8, 1),
            ("Produto Duplicado KG", 5, 1),
            ("produto duplicado kg", 8, 1),
        ],
    )

    prices = catalog_prices()
    assert isinstance(prices, dict)
    assert prices[normalize_name("Produto App KG")] == 10.0
    assert prices[normalize_name("Produto App")] == 10.0
    assert normalize_name("Produto App Inativo KG") not in prices
    assert prices[normalize_name("Produto Sem Preco UN")] == 0.0
    assert prices[normalize_name("Produto Sem Preco")] == 0.0
    assert prices[normalize_name("Produto Zero CX")] == 0.0
    assert prices[normalize_name("Produto Zero")] == 0.0
    assert prices[normalize_name("Produto Decimal")] == 7.25
    assert prices[normalize_name("AÇÚCAR Cristal KG")] == 4.5
    assert prices[normalize_name("AÇÚCAR Cristal")] == 4.5
    assert prices[normalize_name("Produto Embalado (UN)")] == 6.0
    assert prices[normalize_name("Produto Embalado")] == 6.0
    assert prices[normalize_name("Produto Litro LT")] == 8.0
    assert normalize_name("Produto Litro") not in prices
    assert prices[normalize_name("Produto Duplicado KG")] == 8.0
    assert prices[normalize_name("Produto Duplicado")] == 8.0
    assert "" not in prices


def test_app_note_catalog_prices_current_company_scope(isolated_app):
    catalog_prices = isolated_app.module._app_note_catalog_prices
    normalize_name = isolated_app.module._normalize_name

    _replace_paladar_products(
        isolated_app.db_paths["raios"],
        [("Produto Escopo Raios KG", 11, 1)],
    )
    _replace_paladar_products(
        isolated_app.db_paths["estrada"],
        [("Produto Escopo Estrada KG", 22, 1)],
    )

    assert catalog_prices()[normalize_name("Produto Escopo Raios KG")] == 11.0

    token = isolated_app.module.CURRENT_COMPANY.set("estrada")
    try:
        estrada_prices = catalog_prices()
    finally:
        isolated_app.module.CURRENT_COMPANY.reset(token)

    assert normalize_name("Produto Escopo Raios KG") not in estrada_prices
    assert estrada_prices[normalize_name("Produto Escopo Estrada KG")] == 22.0
    assert estrada_prices[normalize_name("Produto Escopo Estrada")] == 22.0


def test_app_note_dict_current_header_empty_items_and_total_recalculation(isolated_app):
    app_note_dict = isolated_app.module._app_note_dict
    conn = isolated_app.module.get_app_notes_db()
    try:
        conn.execute(
            """
            INSERT INTO app_notes(
                id,external_id,client,note_date,total,created_at,updated_at,source,
                status,completed_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (
                "note-empty",
                "external-empty",
                "Cliente Sem Itens",
                "22/08/2026",
                123.45,
                "2026-08-22T10:00:00",
                "2026-08-22T10:01:00",
                "android",
                "completed",
                None,
            ),
        )
        conn.commit()

        row = conn.execute("SELECT * FROM app_notes WHERE id=?", ("note-empty",)).fetchone()
        serialized = app_note_dict(conn, row)
    finally:
        conn.close()

    assert serialized == {
        "id": "note-empty",
        "external_id": "external-empty",
        "client": "Cliente Sem Itens",
        "note_date": "22/08/2026",
        "total": 0.0,
        "created_at": "2026-08-22T10:00:00",
        "updated_at": "2026-08-22T10:01:00",
        "source": "android",
        "status": "completed",
        "completed_at": None,
        "items": [],
    }
    assert "date" not in serialized
    assert isinstance(serialized["total"], float)


def test_app_note_dict_current_items_prices_catalog_flags_and_order(isolated_app):
    app_note_dict = isolated_app.module._app_note_dict
    normalize_name = isolated_app.module._normalize_name
    conn = isolated_app.module.get_app_notes_db()
    try:
        for note_id, external_id in (
            ("note-serialized", "external-serialized"),
            ("note-other", "external-other"),
        ):
            conn.execute(
                """
                INSERT INTO app_notes(
                    id,external_id,client,note_date,total,created_at,updated_at
                ) VALUES(?,?,?,?,?,?,?)
                """,
                (
                    note_id,
                    external_id,
                    "Cliente Serializado",
                    "23/08/2026",
                    999,
                    "2026-08-23T08:00:00",
                    "2026-08-23T08:05:00",
                ),
            )

        rows = [
            (
                "item-no-price",
                "note-serialized",
                "Produto Sem Preco",
                5,
                0,
                5,
                "",
                13,
                0,
                2,
            ),
            (
                "item-catalog",
                "note-serialized",
                "Produto Catalogo",
                2,
                1,
                3,
                "KG",
                99,
                0,
                0,
            ),
            (
                "item-provided",
                "note-serialized",
                "Produto Informado",
                7,
                1,
                2.555,
                "CX",
                10.5,
                1,
                1,
            ),
            (
                "item-zero-catalog",
                "note-serialized",
                "Produto Zero Catalogo",
                1,
                1,
                9,
                "UN",
                3,
                0,
                3,
            ),
            (
                "item-other-note",
                "note-other",
                "Produto Outra Nota",
                1,
                1,
                100,
                "KG",
                100,
                1,
                0,
            ),
        ]
        conn.executemany(
            """
            INSERT INTO app_note_items(
                id,note_id,product,quantity,quantity_provided,weight,unit,
                unit_price,price_provided,position
            ) VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            rows,
        )
        conn.commit()

        row = conn.execute(
            "SELECT * FROM app_notes WHERE id=?", ("note-serialized",)
        ).fetchone()
        serialized = app_note_dict(
            conn,
            row,
            {
                normalize_name("Produto Catalogo"): 4.25,
                normalize_name("Produto Informado"): 99,
                normalize_name("Produto Zero Catalogo"): 0,
            },
        )
    finally:
        conn.close()

    assert [item["id"] for item in serialized["items"]] == [
        "item-catalog",
        "item-provided",
        "item-no-price",
        "item-zero-catalog",
    ]
    assert "item-other-note" not in [item["id"] for item in serialized["items"]]

    catalog_item, provided_item, no_price_item, zero_catalog_item = serialized["items"]
    assert catalog_item == {
        "id": "item-catalog",
        "product": "Produto Catalogo",
        "quantity": 2.0,
        "quantity_provided": 1,
        "weight": 3.0,
        "unit": "KG",
        "unit_price": 99.0,
        "price_provided": 0,
        "position": 0,
        "effective_unit_price": 4.25,
        "effective_price_provided": True,
        "price_from_catalog": True,
    }
    assert provided_item["effective_unit_price"] == 10.5
    assert provided_item["effective_price_provided"] is True
    assert provided_item["price_from_catalog"] is False
    assert no_price_item["effective_unit_price"] == 0.0
    assert no_price_item["effective_price_provided"] is False
    assert no_price_item["price_from_catalog"] is False
    assert zero_catalog_item["effective_unit_price"] == 0.0
    assert zero_catalog_item["effective_price_provided"] is True
    assert zero_catalog_item["price_from_catalog"] is True

    assert serialized["total"] == 39.58
    assert isinstance(serialized["total"], float)
    assert all(isinstance(item["effective_unit_price"], float) for item in serialized["items"])


def test_app_notes_db_initializes_schema_and_returns_open_connection(isolated_app):
    conn = isolated_app.module.get_app_notes_db()
    try:
        assert conn.execute("SELECT 1").fetchone()[0] == 1
        tables = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
        }
        assert {
            "app_notes",
            "app_note_items",
            "app_note_submissions",
            "app_notes_meta",
            "app_calendar_events",
        }.issubset(tables)

        indexes = {
            row["name"]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index'"
            ).fetchall()
        }
        assert {
            "idx_app_notes_client",
            "idx_app_notes_date",
            "idx_app_note_items_note",
            "idx_app_note_submissions_note",
            "idx_app_calendar_due_status",
        }.issubset(indexes)
    finally:
        conn.close()


def test_app_notes_db_migrates_legacy_notes_submissions_and_merges_duplicates(isolated_app):
    legacy = sqlite3.connect(isolated_app.db_paths["app_notes"])
    try:
        legacy.executescript(
            """
            CREATE TABLE app_notes(
                id TEXT PRIMARY KEY,
                external_id TEXT NOT NULL UNIQUE,
                client TEXT NOT NULL DEFAULT '',
                note_date TEXT NOT NULL DEFAULT '',
                total REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                source TEXT NOT NULL DEFAULT 'android'
            );
            CREATE TABLE app_note_items(
                id TEXT PRIMARY KEY,
                note_id TEXT NOT NULL,
                product TEXT NOT NULL DEFAULT '',
                quantity REAL NOT NULL DEFAULT 0,
                unit TEXT NOT NULL DEFAULT '',
                unit_price REAL NOT NULL DEFAULT 0,
                position INTEGER NOT NULL DEFAULT 0
            );
            """
        )
        legacy.executemany(
            """INSERT INTO app_notes(id,external_id,client,note_date,total,created_at,updated_at)
               VALUES(?,?,?,?,?,?,?)""",
            [
                ("nota-keep", "ext-keep", "Cliente Duplicado", "24/08/2026", 0, "2026-08-24T08:00:00", "2026-08-24T08:00:00"),
                ("nota-dup", "ext-dup", "cliente duplicado", "24/08/2026", 0, "2026-08-24T08:05:00", "2026-08-24T08:05:00"),
            ],
        )
        legacy.executemany(
            """INSERT INTO app_note_items(id,note_id,product,quantity,unit,unit_price,position)
               VALUES(?,?,?,?,?,?,?)""",
            [
                ("item-keep", "nota-keep", "Produto A", 2, "KG", 5, 0),
                ("item-dup", "nota-dup", "Produto B", 3, "UN", 7, 0),
            ],
        )
        legacy.commit()
    finally:
        legacy.close()

    conn = isolated_app.module.get_app_notes_db()
    try:
        note_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(app_notes)").fetchall()
        }
        item_columns = {
            row["name"] for row in conn.execute("PRAGMA table_info(app_note_items)").fetchall()
        }
        assert {"status", "completed_at"}.issubset(note_columns)
        assert {"weight", "quantity_provided", "price_provided"}.issubset(item_columns)

        notes = conn.execute("SELECT * FROM app_notes ORDER BY id").fetchall()
        assert len(notes) == 1
        assert notes[0]["id"] == "nota-keep"
        assert notes[0]["total"] == 31

        items = conn.execute(
            "SELECT note_id,product,quantity,weight,quantity_provided,price_provided,position "
            "FROM app_note_items ORDER BY position"
        ).fetchall()
        assert [item["note_id"] for item in items] == ["nota-keep", "nota-keep"]
        assert [item["product"] for item in items] == ["Produto B", "Produto A"]
        assert [item["weight"] for item in items] == [3, 2]
        assert [item["quantity_provided"] for item in items] == [1, 1]
        assert [item["price_provided"] for item in items] == [1, 1]
        assert [item["position"] for item in items] == [0, 1]

        submissions = conn.execute(
            "SELECT external_id,note_id FROM app_note_submissions ORDER BY external_id"
        ).fetchall()
        assert [dict(row) for row in submissions] == [
            {"external_id": "ext-dup", "note_id": "nota-keep"},
            {"external_id": "ext-keep", "note_id": "nota-keep"},
        ]
        marker = conn.execute(
            "SELECT value FROM app_notes_meta WHERE key='merge_client_day_v1'"
        ).fetchone()
        assert marker["value"] == "done"
        assert conn.execute("SELECT COUNT(*) FROM app_note_items").fetchone()[0] == 2
    finally:
        conn.close()


def test_app_note_mobile_create_multiple_items_submission_and_total(isolated_app):
    payload = {
        "external_id": "nota-app-mobile-multiplos-itens",
        "client": "Cliente Nota App Mobile",
        "date": "23/08/2026",
        "items": [
            {
                "product": "Produto Mobile A",
                "quantity": 2,
                "weight": 2,
                "unit": "KG",
                "unit_price": 7.5,
            },
            {
                "product": "Produto Mobile B",
                "quantity": 3,
                "weight": 3,
                "unit": "UN",
                "unit_price": 4,
            },
        ],
    }
    response = isolated_app.client.post(
        "/api/app-notes/mobile",
        headers={"x-app-token": isolated_app.module.APP_NOTES_TOKEN},
        json=payload,
    )
    assert response.status_code == 200
    body = response.json()
    assert body["ok"] is True
    assert body["duplicate"] is False
    assert body["merged"] is False
    assert body["note"]["client"] == "Cliente Nota App Mobile"
    assert body["note"]["note_date"] == "23/08/2026"
    assert body["note"]["total"] == 27
    assert [item["product"] for item in body["note"]["items"]] == [
        "Produto Mobile A",
        "Produto Mobile B",
    ]

    conn = sqlite3.connect(isolated_app.db_paths["app_notes"])
    conn.row_factory = sqlite3.Row
    try:
        note = conn.execute(
            "SELECT id,client,note_date,total,status FROM app_notes WHERE external_id=?",
            ("nota-app-mobile-multiplos-itens",),
        ).fetchone()
        items = conn.execute(
            "SELECT product,weight,unit_price,position FROM app_note_items WHERE note_id=? ORDER BY position",
            (body["note"]["id"],),
        ).fetchall()
        submission = conn.execute(
            "SELECT note_id FROM app_note_submissions WHERE external_id=?",
            ("nota-app-mobile-multiplos-itens",),
        ).fetchone()
    finally:
        conn.close()
    assert dict(note)["client"] == "Cliente Nota App Mobile"
    assert dict(note)["note_date"] == "23/08/2026"
    assert dict(note)["total"] == 27
    assert dict(note)["status"] == "pending"
    assert [dict(item)["product"] for item in items] == ["Produto Mobile A", "Produto Mobile B"]
    assert [dict(item)["position"] for item in items] == [0, 1]
    assert dict(submission)["note_id"] == body["note"]["id"]

    created_after_mobile_create = _create_app_note_mobile(
        isolated_app.client,
        isolated_app,
        external_id="nota-app-apos-create-mobile",
        client="Cliente Escrita Posterior",
    )
    assert created_after_mobile_create["client"] == "Cliente Escrita Posterior"


def test_notes_list_pending_nf_filters_and_delivery_sync(isolated_app):
    token = _login(isolated_app.client)
    nf_pending = _create_sale(
        isolated_app.client,
        token,
        client="Cliente Nota Pendente",
        nf_number="NF-PENDENTE",
        sale_date="2026-08-10",
        sale_time="08:00",
        delivery_person="Lucas",
    )
    nf_other_driver = _create_sale(
        isolated_app.client,
        token,
        client="Cliente Nota Outro Entregador",
        nf_number="NF-OUTRO-DRIVER",
        sale_date="2026-08-11",
        sale_time="09:00",
        delivery_person="Bruno",
    )
    pr_sale = _create_sale(
        isolated_app.client,
        token,
        sale_type="PR",
        client="Cliente Prod Rural",
        nf_number="PR-ENTREGA",
        sale_date="2026-08-12",
        sale_time="10:00",
        delivery_person="Lucas",
    )

    nf_rows = _list_sales(
        isolated_app.client,
        token,
        query="?sale_type=NF&year=2026&month=8",
    )
    assert {row["id"] for row in nf_rows} == {
        nf_pending["id"],
        nf_other_driver["id"],
    }
    assert all(row["sale_type"] == "NF" for row in nf_rows)
    assert all(row["delivered"] is None for row in nf_rows)

    driver_rows = _list_sales(
        isolated_app.client,
        token,
        query="?sale_type=NF&year=2026&month=8&driver=Lucas",
    )
    assert [row["id"] for row in driver_rows] == [nf_pending["id"]]

    search_rows = _list_sales(
        isolated_app.client,
        token,
        query="?search=NF-PENDENTE",
    )
    assert [row["id"] for row in search_rows] == [nf_pending["id"]]

    all_august = _list_sales(
        isolated_app.client,
        token,
        query="?year=2026&month=8",
    )
    assert {row["id"] for row in all_august} == {
        nf_pending["id"],
        nf_other_driver["id"],
        pr_sale["id"],
    }

    sync = isolated_app.client.get(
        "/api/sales/delivery-sync",
        headers=_headers(token),
    )
    assert sync.status_code == 200
    sync_by_id = {row["id"]: row for row in sync.json()}
    assert sync_by_id[nf_pending["id"]] == {
        "id": nf_pending["id"],
        "delivered": None,
        "delivered_at": None,
    }


def test_notes_individual_delivery_requery_already_delivered_and_missing_id(isolated_app):
    token = _login(isolated_app.client)
    sale = _create_sale(
        isolated_app.client,
        token,
        nf_number="NF-MARCAR-001",
        sale_date="2026-08-13",
        sale_time="08:30",
    )

    marked = _mark_delivered(
        isolated_app.client,
        token,
        sale["id"],
        delivered="sim",
        delivered_at="2026-08-13T12:00:00",
    )
    assert marked == {"ok": True}

    after_mark = _list_sales(
        isolated_app.client,
        token,
        query="?search=NF-MARCAR-001",
    )
    assert after_mark[0]["delivered"] == "sim"
    assert after_mark[0]["delivered_at"] == "2026-08-13T12:00:00"

    already_delivered = _mark_delivered(
        isolated_app.client,
        token,
        sale["id"],
        delivered="sim",
        delivered_at="2026-08-13T12:00:00",
    )
    assert already_delivered == {"ok": True}

    cleared = _mark_delivered(
        isolated_app.client,
        token,
        sale["id"],
        delivered=None,
        delivered_at=None,
    )
    assert cleared == {"ok": True}
    after_clear = _list_sales(
        isolated_app.client,
        token,
        query="?search=NF-MARCAR-001",
    )
    assert after_clear[0]["delivered"] is None
    assert after_clear[0]["delivered_at"] is None

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    count_before_missing = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    conn.close()

    missing = _mark_delivered(
        isolated_app.client,
        token,
        "id-inexistente-entrega",
        delivered="sim",
        delivered_at="2026-08-13T13:00:00",
    )
    assert missing == {"ok": True}

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    count_after_missing = conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0]
    conn.close()
    assert count_after_missing == count_before_missing


def test_notes_bulk_delivery_and_duplicate_nf_behavior(isolated_app):
    token = _login(isolated_app.client)
    first = _create_sale(
        isolated_app.client,
        token,
        client="Cliente Nota Duplicada",
        product="Produto Duplicado A",
        nf_number="NF-DUPLICADA",
        sale_date="2026-08-14",
        sale_time="08:00",
    )
    second = _create_sale(
        isolated_app.client,
        token,
        client="Cliente Nota Duplicada",
        product="Produto Duplicado B",
        nf_number="NF-DUPLICADA",
        sale_date="2026-08-14",
        sale_time="08:05",
        total=150,
        unit_price=150,
    )
    third = _create_sale(
        isolated_app.client,
        token,
        client="Cliente Nota Lote",
        nf_number="NF-LOTE",
        sale_date="2026-08-15",
        sale_time="09:00",
    )

    duplicate_rows = _list_sales(
        isolated_app.client,
        token,
        query="?search=NF-DUPLICADA",
    )
    assert {row["id"] for row in duplicate_rows} == {first["id"], second["id"]}

    one_marked = _mark_delivered(
        isolated_app.client,
        token,
        first["id"],
        delivered="sim",
        delivered_at="2026-08-14T12:00:00",
    )
    assert one_marked == {"ok": True}

    duplicate_after_one = {
        row["id"]: row
        for row in _list_sales(
            isolated_app.client,
            token,
            query="?search=NF-DUPLICADA",
        )
    }
    assert duplicate_after_one[first["id"]]["delivered"] == "sim"
    assert duplicate_after_one[second["id"]]["delivered"] is None

    bulk = isolated_app.client.put(
        "/api/sales/bulk-delivered",
        headers=_headers(token),
        json={
            "ids": [second["id"], third["id"]],
            "delivered": "sim",
            "delivered_at": "2026-08-15T12:00:00",
        },
    )
    assert bulk.status_code == 200
    assert bulk.json() == {"ok": True, "updated": 2}

    after_bulk = {
        row["id"]: row
        for row in _list_sales(
            isolated_app.client,
            token,
            query="?year=2026&month=8",
        )
    }
    assert after_bulk[second["id"]]["delivered"] == "sim"
    assert after_bulk[third["id"]]["delivered"] == "sim"

    clear_bulk = isolated_app.client.put(
        "/api/sales/bulk-delivered",
        headers=_headers(token),
        json={"ids": [first["id"], second["id"]], "delivered": ""},
    )
    assert clear_bulk.status_code == 200
    assert clear_bulk.json() == {"ok": True, "updated": 2}

    empty_bulk = isolated_app.client.put(
        "/api/sales/bulk-delivered",
        headers=_headers(token),
        json={"ids": []},
    )
    assert empty_bulk.status_code == 200
    assert empty_bulk.json() == {"ok": True, "updated": 0}

    missing_bulk = isolated_app.client.put(
        "/api/sales/bulk-delivered",
        headers=_headers(token),
        json={"ids": ["id-inexistente-lote"], "delivered": "sim"},
    )
    assert missing_bulk.status_code == 200
    assert missing_bulk.json() == {"ok": True, "updated": 0}


def test_notes_delivery_authentication_and_role_permissions(isolated_app):
    token = _login(isolated_app.client)
    sale = _create_sale(
        isolated_app.client,
        token,
        nf_number="NF-PERMISSAO",
    )

    no_token_list = isolated_app.client.get("/api/sales?sale_type=NF")
    assert no_token_list.status_code == 401

    no_token_sync = isolated_app.client.get("/api/sales/delivery-sync")
    assert no_token_sync.status_code == 401

    no_token_mark = isolated_app.client.put(
        f"/api/sales/{sale['id']}/delivered",
        json={"delivered": "sim"},
    )
    assert no_token_mark.status_code == 401

    no_token_bulk = isolated_app.client.put(
        "/api/sales/bulk-delivered",
        json={"ids": [sale["id"]], "delivered": "sim"},
    )
    assert no_token_bulk.status_code == 401

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    viewer_id = str(uuid.uuid4())
    editor_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO users(id, username, password_hash, full_name, role, active) VALUES(?,?,?,?,?,1)",
        (
            viewer_id,
            "viewer_entregas",
            isolated_app.module.hash_password("viewer123"),
            "Viewer Entregas",
            "viewer",
        ),
    )
    conn.execute(
        "INSERT INTO users(id, username, password_hash, full_name, role, active) VALUES(?,?,?,?,?,1)",
        (
            editor_id,
            "editor_entregas",
            isolated_app.module.hash_password("editor123"),
            "Editor Entregas",
            "editor",
        ),
    )
    conn.execute(
        "INSERT OR REPLACE INTO settings(key,value) VALUES('tab_permissions',?)",
        (json.dumps({"viewer": [], "editor": [], "admin": []}),),
    )
    conn.commit()
    conn.close()

    viewer_token = _login(isolated_app.client, "viewer_entregas", "viewer123")
    editor_token = _login(isolated_app.client, "editor_entregas", "editor123")

    viewer_list = isolated_app.client.get(
        "/api/sales?sale_type=NF",
        headers=_headers(viewer_token),
    )
    assert viewer_list.status_code == 200

    viewer_sync = isolated_app.client.get(
        "/api/sales/delivery-sync",
        headers=_headers(viewer_token),
    )
    assert viewer_sync.status_code == 200

    viewer_mark = isolated_app.client.put(
        f"/api/sales/{sale['id']}/delivered",
        headers=_headers(viewer_token),
        json={"delivered": "sim"},
    )
    assert viewer_mark.status_code == 403

    viewer_bulk = isolated_app.client.put(
        "/api/sales/bulk-delivered",
        headers=_headers(viewer_token),
        json={"ids": [sale["id"]], "delivered": "sim"},
    )
    assert viewer_bulk.status_code == 403

    editor_mark = isolated_app.client.put(
        f"/api/sales/{sale['id']}/delivered",
        headers=_headers(editor_token),
        json={"delivered": "sim", "delivered_at": "2026-08-05T12:00:00"},
    )
    assert editor_mark.status_code == 200
    assert editor_mark.json() == {"ok": True}

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    conn.execute(
        "INSERT OR REPLACE INTO settings(key,value) VALUES('tab_permissions',?)",
        (json.dumps({"viewer": ["produtos"], "editor": [], "admin": []}),),
    )
    conn.commit()
    conn.close()

    restrictive_list = isolated_app.client.get(
        "/api/sales?sale_type=NF",
        headers=_headers(viewer_token),
    )
    assert restrictive_list.status_code == 403

    restrictive_sync = isolated_app.client.get(
        "/api/sales/delivery-sync",
        headers=_headers(viewer_token),
    )
    assert restrictive_sync.status_code == 403


def test_notes_delivery_isolated_by_x_company(isolated_app):
    token = _login(isolated_app.client)
    raios_sale = _create_sale(
        isolated_app.client,
        token,
        company="raios",
        client="Cliente Entrega Raios",
        nf_number="NF-RAIOS-ENTREGA",
    )
    estrada_sale = _create_sale(
        isolated_app.client,
        token,
        company="estrada",
        client="Cliente Entrega Estrada",
        nf_number="NF-ESTRADA-ENTREGA",
    )

    _mark_delivered(
        isolated_app.client,
        token,
        raios_sale["id"],
        company="raios",
        delivered="sim",
        delivered_at="2026-08-05T12:00:00",
    )

    raios_rows = _list_sales(
        isolated_app.client,
        token,
        company="raios",
        query="?search=NF-RAIOS-ENTREGA",
    )
    assert [row["id"] for row in raios_rows] == [raios_sale["id"]]
    assert raios_rows[0]["delivered"] == "sim"

    estrada_rows = _list_sales(
        isolated_app.client,
        token,
        company="estrada",
        query="?search=NF-ESTRADA-ENTREGA",
    )
    assert [row["id"] for row in estrada_rows] == [estrada_sale["id"]]
    assert estrada_rows[0]["delivered"] is None


def test_app_note_update_replaces_items_and_preserves_status_behavior(isolated_app):
    token = _login(isolated_app.client)
    note = _create_app_note_mobile(isolated_app.client, isolated_app)

    update_payload = {
        "client": "Cliente Nota App Editada",
        "date": "21/08/2026",
        "status": "completed",
        "items": [
            {
                "product": "Produto App A",
                "quantity": 2,
                "weight": 2,
                "unit": "KG",
                "unit_price": 10,
            },
            {
                "product": "Produto App B",
                "quantity": 3,
                "weight": 3,
                "unit": "UN",
                "unit_price": 5,
            },
        ],
    }
    updated = isolated_app.client.put(
        f"/api/app-notes/{note['id']}",
        headers=_headers(token),
        json=update_payload,
    )
    assert updated.status_code == 200
    body = updated.json()
    assert body["ok"] is True
    assert body["note"]["client"] == "Cliente Nota App Editada"
    assert body["note"]["note_date"] == "21/08/2026"
    assert body["note"]["status"] == "completed"
    assert body["note"]["total"] == 35
    assert [item["product"] for item in body["note"]["items"]] == [
        "Produto App A",
        "Produto App B",
    ]

    conn = sqlite3.connect(isolated_app.db_paths["app_notes"])
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT client,note_date,total,status,completed_at FROM app_notes WHERE id=?",
        (note["id"],),
    ).fetchone()
    items = conn.execute(
        "SELECT product,weight,unit_price,position FROM app_note_items WHERE note_id=? ORDER BY position",
        (note["id"],),
    ).fetchall()
    conn.close()
    assert dict(row)["client"] == "Cliente Nota App Editada"
    assert dict(row)["note_date"] == "21/08/2026"
    assert dict(row)["total"] == 35
    assert dict(row)["status"] == "completed"
    assert dict(row)["completed_at"]
    assert [dict(item)["product"] for item in items] == ["Produto App A", "Produto App B"]


def test_app_note_update_missing_id_preserves_404_and_does_not_lock_db(isolated_app):
    token = _login(isolated_app.client)
    init_conn = isolated_app.module.get_app_notes_db()
    init_conn.close()
    conn = sqlite3.connect(isolated_app.db_paths["app_notes"])
    notes_before = conn.execute("SELECT COUNT(*) FROM app_notes").fetchone()[0]
    items_before = conn.execute("SELECT COUNT(*) FROM app_note_items").fetchone()[0]
    conn.close()

    missing = isolated_app.client.put(
        "/api/app-notes/nota-app-inexistente",
        headers=_headers(token),
        json={
            "client": "Cliente Ausente",
            "date": "22/08/2026",
            "items": [
                {
                    "product": "Produto Ausente",
                    "quantity": 1,
                    "weight": 1,
                    "unit": "KG",
                    "unit_price": 8,
                }
            ],
        },
    )
    assert missing.status_code == 404

    conn = sqlite3.connect(isolated_app.db_paths["app_notes"])
    notes_after = conn.execute("SELECT COUNT(*) FROM app_notes").fetchone()[0]
    items_after = conn.execute("SELECT COUNT(*) FROM app_note_items").fetchone()[0]
    conn.close()
    assert notes_after == notes_before
    assert items_after == items_before

    # A escrita seguinte confirma que a conexao foi fechada mesmo no caminho de erro.
    created_after_error = _create_app_note_mobile(
        isolated_app.client,
        isolated_app,
        external_id="nota-app-apos-404",
        client="Cliente Depois Do Erro",
    )
    assert created_after_error["client"] == "Cliente Depois Do Erro"
