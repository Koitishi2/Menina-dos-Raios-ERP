import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

from test_orcamentos import _headers, _login


def test_stock_dynamic_note_buttons_use_delegated_click_handlers():
    html = (Path(__file__).resolve().parents[1] / "backend" / "static" / "index.html").read_text(encoding="utf-8")
    stock_render = html[html.index("function renderStock():"):html.index("async function submitStockMovement(")]

    assert "data-stock-open-module" in stock_render
    assert "data-stock-sales-product" in stock_render
    assert "onclick=" not in stock_render
    assert "document.addEventListener('click'" in html
    assert "window._stockActionsBound=true" in html
    assert "data-stock-open-date" in stock_render
    assert "clearFilters();" in html[html.index("async function stockOpenSource("):html.index("async function stockOpenSales(")]


def test_stock_starts_empty_and_tracks_manual_entry_and_sale(isolated_app):
    token = _login(isolated_app.client)
    headers = _headers(token)

    response = isolated_app.client.get("/api/stock?module=estrada", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["products"]) == 3
    product = next(item for item in payload["products"] if item["sku"] == "UVA-VITORIA-8KG")
    assert product["balance"] == 0

    response = isolated_app.client.post(
        "/api/stock/movements",
        headers=headers,
        json={
            "module": "estrada",
            "product_id": product["id"],
            "movement_type": "entry",
            "quantity": 20,
            "movement_date": datetime.now().date().isoformat(),
            "reference": "Contagem inicial",
        },
    )
    assert response.status_code == 200

    conn = sqlite3.connect(isolated_app.db_paths["estrada"])
    sale_id = str(uuid.uuid4())
    created_at = (datetime.now().astimezone() + timedelta(seconds=2)).isoformat(timespec="seconds")
    conn.execute(
        """INSERT INTO sales
           (id,sale_type,sale_date,sale_time,client,product,nf_number,quantity,unit_price,total,created_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        (sale_id, "NF", datetime.now().date().isoformat(), "12:00", "Cliente Teste",
         "Uva Vitória CX 8 KG", "NF-TESTE-42", 3, 75, 225, created_at),
    )
    conn.commit()
    conn.close()

    payload = isolated_app.client.get("/api/stock?module=estrada", headers=headers).json()
    product = next(item for item in payload["products"] if item["id"] == product["id"])
    assert product["balance"] == 17
    sale_movement = next(item for item in payload["movements"] if item["source"] == "sale")
    assert sale_movement["reference"] == "NF-TESTE-42"
    assert sale_movement["source_id"] == sale_id
    assert "Cliente Teste" in sale_movement["notes"]


def test_generic_uva_vitoria_sales_are_converted_from_units_to_cases(isolated_app):
    token = _login(isolated_app.client)
    headers = _headers(token)
    product = next(
        item for item in isolated_app.client.get("/api/stock?module=estrada", headers=headers).json()["products"]
        if item["sku"] == "UVA-VITORIA-5KG"
    )

    conn = sqlite3.connect(isolated_app.db_paths["estrada"])
    now = datetime.now().astimezone()
    sales = [("NF-124", 40), ("NF-125", 60)]
    for offset, (invoice, quantity) in enumerate(sales, start=2):
        created_at = (now + timedelta(seconds=offset)).isoformat(timespec="seconds")
        conn.execute(
            """INSERT INTO sales
               (id,sale_type,sale_date,sale_time,client,product,nf_number,quantity,unit_price,total,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (str(uuid.uuid4()), "NF", now.date().isoformat(), "13:45", "Cliente Teste",
             "Uva Vitoria", invoice, quantity, 7.5, quantity * 7.5, created_at),
        )
    conn.commit()
    conn.close()

    snapshot = isolated_app.client.get("/api/stock?module=estrada", headers=headers).json()
    converted = next(item for item in snapshot["products"] if item["id"] == product["id"])
    assert converted["sold_quantity"] == 10
    assert converted["balance"] == -10
    assert converted["min_sale_quantity"] == 4
    assert converted["max_sale_quantity"] == 6
    assert converted["sales_revenue"] == 750

    sale_rows = isolated_app.client.get(
        f"/api/stock/products/{product['id']}/sales?module=estrada", headers=headers
    ).json()["sales"]
    assert [(row["reference"], row["quantity"], row["unit"], row["total"]) for row in sale_rows] == [
        ("NF-124", 4, "CX", 300),
        ("NF-125", 6, "CX", 450),
    ]


def test_stock_rejects_unknown_module_and_negative_entry(isolated_app):
    token = _login(isolated_app.client)
    headers = _headers(token)
    response = isolated_app.client.get("/api/stock?module=desconhecido", headers=headers)
    assert response.status_code == 400
    product = isolated_app.client.get("/api/stock?module=estrada", headers=headers).json()["products"][0]
    response = isolated_app.client.post(
        "/api/stock/movements",
        headers=headers,
        json={"module": "estrada", "product_id": product["id"], "movement_type": "entry", "quantity": -2},
    )
    assert response.status_code == 400


def test_voice_stock_customer_adds_and_accumulates_stock_once(isolated_app):
    token = _login(isolated_app.client)
    headers = {
        "x-token": token,
        "x-app-token": isolated_app.module.APP_NOTES_TOKEN,
    }
    payload = {
        "external_id": "voice-stock-intake-001",
        "client": "ESTOQUE",
        "date": datetime.now().strftime("%d/%m/%Y"),
        "stock_intake": True,
        "items": [
            {"product": "Macaxeira a Vácuo", "weight": 12, "unit": "KG"},
            {"product": "ALHO 250 GRAMAS", "weight": 8, "unit": "KG"},
            {"product": "Produto falado novo", "weight": 3, "unit": "MC"},
        ],
    }
    first = isolated_app.client.post("/api/app-notes/mobile", headers=headers, json=payload)
    assert first.status_code == 200
    assert first.json()["stock_intake"] == {"ok": True, "duplicate": False, "items_added": 3}

    snapshot = isolated_app.client.get("/api/stock?module=raios", headers={"x-token": token}).json()
    products = {product["name"]: product for product in snapshot["products"]}
    assert products["Macaxeira a Vácuo"]["balance"] == 12
    assert products["Alho 250g"]["balance"] == 8
    assert products["Alho 250g"]["unit"] == "UN"
    assert not any("ALHO 250 GRAMAS" in product["name"] for product in snapshot["products"])
    assert products["Produto falado novo"]["balance"] == 3
    assert len([row for row in snapshot["movements"] if row.get("reference") == "Nota APP voice-stock-intake-001"]) == 3

    repeated = isolated_app.client.post("/api/app-notes/mobile", headers=headers, json=payload)
    assert repeated.status_code == 200
    assert repeated.json()["duplicate"] is True
    assert repeated.json()["stock_intake"] == {"ok": True, "duplicate": True, "items_added": 0}
    after_retry = isolated_app.client.get("/api/stock?module=raios", headers={"x-token": token}).json()
    after_products = {product["name"]: product for product in after_retry["products"]}
    assert after_products["Macaxeira a Vácuo"]["balance"] == 12
    assert after_products["Alho 250g"]["balance"] == 8

    second_payload = dict(payload)
    second_payload["external_id"] = "voice-stock-intake-002"
    second_payload["items"] = [{"product": "Macaxeira a Vácuo", "weight": 5, "unit": "KG"}]
    second = isolated_app.client.post("/api/app-notes/mobile", headers=headers, json=second_payload)
    assert second.status_code == 200
    accumulated = isolated_app.client.get("/api/stock?module=raios", headers={"x-token": token}).json()
    accumulated_products = {product["name"]: product for product in accumulated["products"]}
    assert accumulated_products["Macaxeira a Vácuo"]["balance"] == 17

    garlic_payload = dict(payload)
    garlic_payload["external_id"] = "voice-stock-intake-garlic-003"
    garlic_payload["items"] = [{"product": "Alho", "weight": 4, "unit": "unidades"}]
    garlic = isolated_app.client.post("/api/app-notes/mobile", headers=headers, json=garlic_payload)
    assert garlic.status_code == 200
    garlic_snapshot = isolated_app.client.get("/api/stock?module=raios", headers={"x-token": token}).json()
    garlic_products = {product["name"]: product for product in garlic_snapshot["products"]}
    assert garlic_products["Alho 250g"]["balance"] == 12
    assert garlic_products["Alho 250g"]["unit"] == "UN"
    assert not any(product["name"] == "Alho" for product in garlic_snapshot["products"])


def test_non_stock_voice_customer_does_not_create_stock(isolated_app):
    token = _login(isolated_app.client)
    response = isolated_app.client.post(
        "/api/app-notes/mobile",
        headers={"x-token": token, "x-app-token": isolated_app.module.APP_NOTES_TOKEN},
        json={
            "external_id": "voice-regular-client-001",
            "client": "Cliente comum",
            "date": datetime.now().strftime("%d/%m/%Y"),
            "stock_intake": True,
            "items": [{"product": "Macaxeira a Vácuo", "weight": 12, "unit": "KG"}],
        },
    )
    assert response.status_code == 200
    assert "stock_intake" not in response.json()
    snapshot = isolated_app.client.get("/api/stock?module=raios", headers={"x-token": token}).json()
    assert snapshot["products"] == []
    assert snapshot["movements"] == []


def test_stretch_film_count_is_idempotent_and_sales_are_numeric(isolated_app):
    token = _login(isolated_app.client)
    headers = _headers(token)
    stock_conn = sqlite3.connect(isolated_app.db_paths["raios"])
    from inventory import init_inventory_schema

    init_inventory_schema(stock_conn)
    created_at = datetime.now().astimezone().isoformat(timespec="seconds")
    product_id = str(uuid.uuid4())
    stock_conn.execute(
        """INSERT INTO stock_products
           (id,module_key,sku,name,unit,aliases_json,tracking_after,created_at)
           VALUES(?,?,?,?,?,?,?,?)""",
        (product_id, "estrada", "STRETCH-FILM", "Stretch Film Pvc 4Kg", "UN", "[]", created_at, created_at),
    )
    stock_conn.commit()
    stock_conn.close()

    source_conn = sqlite3.connect(isolated_app.db_paths["estrada"])
    sales = [("sale-100", "100", 150), ("sale-2", "2", 1)]
    for offset, (sale_id, nf, quantity) in enumerate(sales, start=2):
        sale_time = (datetime.now().astimezone() + timedelta(seconds=offset)).isoformat(timespec="seconds")
        source_conn.execute(
            """INSERT INTO sales
               (id,sale_type,sale_date,sale_time,client,product,nf_number,quantity,unit_price,total,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (sale_id, "NF", datetime.now().date().isoformat(), "12:00", "Cliente Teste",
             "Stretch Film PVC 4kg", nf, quantity, 80, quantity * 80, sale_time),
        )
    source_conn.commit()
    source_conn.close()

    response = isolated_app.client.get("/api/stock?module=estrada", headers=headers)
    assert response.status_code == 200
    product = next(item for item in response.json()["products"] if item["sku"] == "STRETCH-FILM")
    assert product["balance"] == 6249
    assert product["sold_quantity"] == 151
    assert product["sales_count"] == 2
    assert product["min_sale_quantity"] == 1
    assert product["max_sale_quantity"] == 150

    source_conn = sqlite3.connect(isolated_app.db_paths["estrada"])
    sale_time = (datetime.now().astimezone() + timedelta(seconds=10)).isoformat(timespec="seconds")
    source_conn.execute(
        """INSERT INTO sales
           (id,sale_type,sale_date,sale_time,client,product,nf_number,quantity,unit_price,total,created_at)
           VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
        ("sale-10", "NF", datetime.now().date().isoformat(), "12:01", "Cliente Teste",
         "Stretch Film PVC 4kg", "10", 8, 80, 640, sale_time),
    )
    source_conn.commit()
    source_conn.close()

    payload = isolated_app.client.get("/api/stock?module=estrada", headers=headers).json()
    product = next(item for item in payload["products"] if item["sku"] == "STRETCH-FILM")
    assert product["balance"] == 6241
    assert product["sold_quantity"] == 159
    detail = isolated_app.client.get(
        f"/api/stock/products/{product_id}/sales?module=estrada", headers=headers
    )
    assert detail.status_code == 200
    assert [row["reference"] for row in detail.json()["sales"]] == ["2", "10", "100"]

