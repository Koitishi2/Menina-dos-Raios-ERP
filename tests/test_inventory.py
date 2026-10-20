import sqlite3
import uuid
from datetime import datetime, timedelta
import json

from backend.inventory import init_inventory_schema
from test_orcamentos import _headers, _login


def test_stock_seeds_note_quantities_once_and_tracks_manual_entry_and_sale(isolated_app):
    token = _login(isolated_app.client)
    headers = _headers(token)

    response = isolated_app.client.get("/api/stock?module=estrada", headers=headers)
    assert response.status_code == 200
    payload = response.json()
    assert len(payload["products"]) >= 4
    expected_opening = {
        "UVA-VITORIA-8KG": 5,
        "UVA-VITORIA-KIDS-250G": 110,
        "UVA-VITORIA-5KG": 2870,
        "UVA-THOMPSON-VERDE-500G": 0,
    }
    actual_opening = {item["sku"]: item["balance"] for item in payload["products"]}
    assert {sku: actual_opening[sku] for sku in expected_opening} == expected_opening
    assert all(item["trend"] == [item["balance"]] for item in payload["products"])
    assert {item["sku"] for item in payload["products"]} >= set(expected_opening)
    assert any(item["sku"] == "UVA-THOMPSON-VERDE-500G" for item in payload["all_products"])
    product = next(item for item in payload["products"] if item["sku"] == "UVA-VITORIA-8KG")
    assert product["balance"] == 5
    assert sum(item["reference"] == "Saldo inicial - nota das uvas enviada" for item in payload["movements"]) == 3

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

    repeated_payload = isolated_app.client.get("/api/stock?module=estrada", headers=headers).json()
    repeated_product = next(item for item in repeated_payload["products"] if item["sku"] == product["sku"])
    assert repeated_product["balance"] == 25
    assert sum(item["reference"] == "Saldo inicial - nota das uvas enviada" for item in repeated_payload["movements"]) == 3

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
    assert product["balance"] == 22
    assert product["trend"][-1] == 22
    sale_movement = next(item for item in payload["movements"] if item["source"] == "sale")
    assert sale_movement["reference"] == "NF-TESTE-42"
    assert sale_movement["source_id"] == sale_id
    assert "Cliente Teste" in sale_movement["notes"]


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
            {"product": "Alho Descascado 250g", "weight": 8, "unit": "UN"},
            {"product": "Produto falado novo", "weight": 3, "unit": "MC"},
        ],
    }
    first = isolated_app.client.post("/api/app-notes/mobile", headers=headers, json=payload)
    assert first.status_code == 200
    assert first.json()["stock_intake"] == {"ok": True, "duplicate": False, "items_added": 3}

    snapshot = isolated_app.client.get("/api/stock?module=raios", headers={"x-token": token}).json()
    products = {product["name"]: product for product in snapshot["products"]}
    assert products["Macaxeira a Vácuo"]["balance"] == 12
    assert products["Alho Descascado 250 g"]["balance"] == 8
    assert products["Produto falado novo"]["balance"] == 3

    repeated = isolated_app.client.post("/api/app-notes/mobile", headers=headers, json=payload)
    assert repeated.status_code == 200
    assert repeated.json()["stock_intake"] == {"ok": True, "duplicate": True, "items_added": 0}

    payload["external_id"] = "voice-stock-intake-002"
    payload["items"] = [{"product": "Macaxeira a Vácuo", "weight": 5, "unit": "KG"}]
    second = isolated_app.client.post("/api/app-notes/mobile", headers=headers, json=payload)
    assert second.status_code == 200
    accumulated = isolated_app.client.get("/api/stock?module=raios", headers={"x-token": token}).json()
    product = next(item for item in accumulated["products"] if item["name"] == "Macaxeira a Vácuo")
    assert product["balance"] == 17


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
    assert not any(
        movement.get("reference") == "Nota APP voice-regular-client-001"
        for movement in snapshot["movements"]
    )


def test_stock_debits_todays_grape_sales_with_sales_unit_conversion(isolated_app):
    token = _login(isolated_app.client)
    headers = _headers(token)
    payload = isolated_app.client.get("/api/stock?module=estrada", headers=headers).json()
    products = {item["sku"]: item for item in payload["products"]}
    assert products["UVA-VITORIA-5KG"]["sale_quantity_factor"] == 0.1

    conn = sqlite3.connect(isolated_app.db_paths["estrada"])
    today = datetime.now().date().isoformat()
    early_created_at = datetime.now().astimezone().replace(hour=1, minute=0, second=0, microsecond=0).isoformat()
    sales = [
        ("Uva Vitoria", 80, 8.5, 680, "108"),
        ("Uva Vitoria", 20, 8.5, 170, "109"),
        ("Uva Vitoria", 60, 8.5, 510, "110"),
        ("Uva Thompson Verde Cx 500G", 50, 10, 500, "107"),
        ("Uva Thompson Verde Cx 500G", 20, 10, 200, "108"),
    ]
    sale_ids = []
    for product, quantity, price, total, nf in sales:
        sale_id = str(uuid.uuid4())
        sale_ids.append(sale_id)
        conn.execute(
            """INSERT INTO sales
               (id,sale_type,sale_date,sale_time,client,product,nf_number,quantity,unit_price,total,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (sale_id, "NF", today, "12:00", "Cliente Teste", product, nf,
             quantity, price, total, early_created_at),
        )
    conn.commit()
    conn.close()

    payload = isolated_app.client.get("/api/stock?module=estrada", headers=headers).json()
    products = {item["sku"]: item for item in payload["products"]}
    assert products["UVA-VITORIA-5KG"]["balance"] == 2854
    assert products["UVA-THOMPSON-VERDE-500G"]["balance"] == -70
    assert products["UVA-VITORIA-5KG"]["today_sold_quantity"] == 16
    assert products["UVA-VITORIA-5KG"]["today_sales_count"] == 3
    assert products["UVA-VITORIA-5KG"]["today_sales_revenue"] == 1360
    assert products["UVA-THOMPSON-VERDE-500G"]["today_sold_quantity"] == 70
    assert products["UVA-VITORIA-5KG"]["trend"][-1] == 2854
    sale_movements = [item for item in payload["movements"] if item.get("source_id") in sale_ids]
    assert len(sale_movements) == 5
    assert [item["reference"] for item in sale_movements] == ["107", "108", "108", "109", "110"]
    assert sale_movements[0]["movement_date"] == today
    converted = next(
        item for item in sale_movements
        if item["product_id"] == products["UVA-VITORIA-5KG"]["id"] and item["sale_quantity"] == 80
    )
    assert converted["quantity_delta"] == -8
    assert "80 na venda → 8 CX no estoque" in converted["notes"]
    sixty_units = next(
        item for item in sale_movements
        if item["product_id"] == products["UVA-VITORIA-5KG"]["id"] and item["sale_quantity"] == 60
    )
    assert sixty_units["quantity_delta"] == -6
    assert "60 na venda → 6 CX no estoque" in sixty_units["notes"]


def test_inventory_schema_migrates_existing_products_for_sale_unit_conversion():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE stock_products (
            id TEXT PRIMARY KEY, module_key TEXT NOT NULL, sku TEXT NOT NULL,
            name TEXT NOT NULL, unit TEXT NOT NULL DEFAULT 'UND',
            aliases_json TEXT NOT NULL DEFAULT '[]', active INTEGER NOT NULL DEFAULT 1,
            tracking_after TEXT NOT NULL, created_at TEXT NOT NULL, UNIQUE(module_key,sku)
        );
        CREATE TABLE stock_movements (
            id TEXT PRIMARY KEY, product_id TEXT NOT NULL,
            movement_type TEXT NOT NULL CHECK(movement_type IN ('entry','exit','adjustment')),
            quantity_delta REAL NOT NULL, movement_date TEXT NOT NULL,
            reference TEXT NOT NULL DEFAULT '', notes TEXT NOT NULL DEFAULT '',
            created_by TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES stock_products(id)
        );
        """
    )
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    conn.execute(
        """INSERT INTO stock_products
           (id,module_key,sku,name,unit,aliases_json,tracking_after,created_at)
           VALUES(?,?,?,?,?,?,?,?)""",
        ("existing-5kg", "estrada", "UVA-VITORIA-5KG", "Uva Vitória - Caixa 5 kg", "CX",
         json.dumps(["ALIAS PERSONALIZADO"]), now, now),
    )

    init_inventory_schema(conn)
    migrated = conn.execute("SELECT * FROM stock_products WHERE id='existing-5kg'").fetchone()
    aliases = json.loads(migrated["aliases_json"])
    assert migrated["sale_quantity_factor"] == 0.1
    assert "ALIAS PERSONALIZADO" in aliases
    assert "Uva Vitoria" in aliases
    assert conn.execute(
        "SELECT quantity_delta FROM stock_movements WHERE id='opening-stock-uva-vitoria-5kg'"
    ).fetchone()[0] == 2870
    conn.close()


def test_stock_catalog_edit_archive_and_set_current_balance(isolated_app):
    token = _login(isolated_app.client)
    headers = _headers(token)
    source = sqlite3.connect(isolated_app.db_paths["estrada"])
    source.execute(
        "INSERT OR REPLACE INTO product_prices(key,label,price) VALUES(?,?,?)",
        ("stretch-filme", "Stretch Filme", 35),
    )
    source.commit()
    source.close()

    response = isolated_app.client.get("/api/stock?module=estrada", headers=headers)
    assert response.status_code == 200
    catalog_product = next(item for item in response.json()["all_products"] if item["sku"] == "STRETCH-FILME")
    assert catalog_product["name"] == "Stretch Filme"
    assert catalog_product["active"] == 1

    response = isolated_app.client.put(
        f"/api/stock/products/{catalog_product['id']}/balance",
        headers=headers,
        json={"module": "estrada", "quantity": 12},
    )
    assert response.status_code == 200
    payload = isolated_app.client.get("/api/stock?module=estrada", headers=headers).json()
    updated = next(item for item in payload["products"] if item["id"] == catalog_product["id"])
    assert updated["balance"] == 12

    response = isolated_app.client.put(
        f"/api/stock/products/{catalog_product['id']}",
        headers=headers,
        json={"module": "estrada", "name": "Stretch Filme Transparente", "sku": "STRETCH-FILME", "unit": "ROLO", "aliases": ["Stretch Filme"]},
    )
    assert response.status_code == 200
    edited = next(item for item in isolated_app.client.get("/api/stock?module=estrada", headers=headers).json()["products"] if item["id"] == catalog_product["id"])
    assert edited["name"] == "Stretch Filme Transparente"
    assert "Stretch Filme" in edited["aliases"]

    response = isolated_app.client.delete(
        f"/api/stock/products/{catalog_product['id']}?module=estrada", headers=headers
    )
    assert response.status_code == 200
    archived = next(item for item in isolated_app.client.get("/api/stock?module=estrada", headers=headers).json()["all_products"] if item["id"] == catalog_product["id"])
    assert archived["active"] == 0
    assert archived["balance"] == 12
    response = isolated_app.client.put(
        f"/api/stock/products/{catalog_product['id']}",
        headers=headers,
        json={"module": "estrada", "name": archived["name"], "sku": archived["sku"], "unit": archived["unit"], "aliases": archived["aliases"], "active": True},
    )
    assert response.status_code == 200
    restored = next(item for item in isolated_app.client.get("/api/stock?module=estrada", headers=headers).json()["all_products"] if item["id"] == catalog_product["id"])
    assert restored["active"] == 1


def test_stretch_film_opening_total_is_reconciled_once_and_keeps_manual_balance(isolated_app):
    token = _login(isolated_app.client)
    headers = _headers(token)
    source = sqlite3.connect(isolated_app.db_paths["estrada"])
    source.execute(
        "INSERT OR REPLACE INTO product_prices(key,label,price) VALUES(?,?,?)",
        ("stretch-film", "Stretch Film PVC 4kg", 80),
    )
    today = datetime.now().date().isoformat()
    for index, quantity in enumerate((400, 625), start=1):
        source.execute(
            """INSERT INTO sales
               (id,sale_type,sale_date,sale_time,client,product,nf_number,quantity,unit_price,total,created_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?)""",
            (f"stretch-sale-{index}", "NF", today, "10:00", "Cliente", "Stretch Film PVC 4kg",
             str(500 + index), quantity, 80, quantity * 80, datetime.now().astimezone().isoformat()),
        )
    source.commit()
    source.close()

    payload = isolated_app.client.get("/api/stock?module=estrada", headers=headers).json()
    product = next(item for item in payload["products"] if item["sku"] == "STRETCH-FILM")
    assert product["sold_quantity"] == 1025
    assert product["balance"] == 5375
    assert len([item for item in payload["movements"] if item.get("id") == "stock-count-stretch-film-20261016-6400"]) == 1

    stock = sqlite3.connect(isolated_app.db_paths["raios"])
    stock.execute(
        "UPDATE stock_movements SET quantity_delta=quantity_delta+2050,notes=? WHERE id=?",
        ("Saldo físico atual definido para 6400 UN; legado a corrigir", "stock-count-stretch-film-20261016-6400"),
    )
    stock.commit()
    stock.close()
    repaired = isolated_app.client.get("/api/stock?module=estrada", headers=headers).json()
    product = next(item for item in repaired["products"] if item["sku"] == "STRETCH-FILM")
    assert product["balance"] == 5375

    sales = isolated_app.client.get(
        f"/api/stock/products/{product['id']}/sales?module=estrada", headers=headers
    )
    assert sales.status_code == 200
    assert [sale["reference"] for sale in sales.json()["sales"]] == ["501", "502"]
    assert all(sale["id"] for sale in sales.json()["sales"])

    changed = isolated_app.client.put(
        f"/api/stock/products/{product['id']}/balance", headers=headers,
        json={"module": "estrada", "quantity": 4000},
    )
    assert changed.status_code == 200
    refreshed = isolated_app.client.get("/api/stock?module=estrada", headers=headers).json()
    current = next(item for item in refreshed["products"] if item["sku"] == "STRETCH-FILM")
    assert current["balance"] == 4000


def test_stock_summary_products_are_clickable_and_history_is_newest_first():
    from pathlib import Path

    source = Path(__file__).parents[1] / "backend" / "static" / "index.html"
    html = source.read_text(encoding="utf-8")
    assert 'class="stock-product-summary-card" role="button" tabindex="0"' in html
    assert "stockOpenSales(card.dataset.stockId)" in html
    assert "today_sold_quantity" in html
    assert "today_sales_revenue" in html
    assert "Vendido hoje" in html


def test_stock_invoice_navigation_opens_the_existing_sale_editor():
    from pathlib import Path

    html = (Path(__file__).parents[1] / "backend" / "static" / "index.html").read_text(encoding="utf-8")
    assert "panel.dataset.stockSourceNavigationBound" in html
    assert "[data-stock-open-module][data-stock-open-sale-id]" in html
    assert "stockOpenSource(button.dataset.stockOpenModule" in html
    assert "await editSale(sale.id)" in html
    assert ">Editar NF</button>" in html
    assert "onclick=\\'" not in html[html.index("function renderStock()") : html.index("function renderStockCatalog()")]
    assert "onclick=\\'" not in html[html.index("async function stockOpenSales(") : html.index("async function loadSellers(")]
