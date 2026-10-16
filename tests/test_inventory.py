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
    assert len(payload["products"]) == 4
    expected_opening = {
        "UVA-VITORIA-8KG": 5,
        "UVA-VITORIA-KIDS-250G": 110,
        "UVA-VITORIA-5KG": 2870,
        "UVA-THOMPSON-VERDE-500G": 0,
    }
    assert {item["sku"]: item["balance"] for item in payload["products"]} == expected_opening
    assert all(item["trend"] == [item["balance"]] for item in payload["products"])
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


def test_stock_debits_todays_grape_sales_with_sales_unit_conversion(isolated_app):
    token = _login(isolated_app.client)
    headers = _headers(token)
    payload = isolated_app.client.get("/api/stock?module=estrada", headers=headers).json()
    products = {item["sku"]: item for item in payload["products"]}
    assert products["UVA-VITORIA-5KG"]["sale_quantity_factor"] == 0.2

    conn = sqlite3.connect(isolated_app.db_paths["estrada"])
    today = datetime.now().date().isoformat()
    early_created_at = datetime.now().astimezone().replace(hour=1, minute=0, second=0, microsecond=0).isoformat()
    sales = [
        ("Uva Vitoria", 80, 8.5, 680, "108"),
        ("Uva Vitoria", 20, 8.5, 170, "109"),
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
    assert products["UVA-VITORIA-5KG"]["balance"] == 2850
    assert products["UVA-THOMPSON-VERDE-500G"]["balance"] == -70
    assert products["UVA-VITORIA-5KG"]["trend"][-1] == 2850
    sale_movements = [item for item in payload["movements"] if item.get("source_id") in sale_ids]
    assert len(sale_movements) == 4
    converted = next(
        item for item in sale_movements
        if item["product_id"] == products["UVA-VITORIA-5KG"]["id"] and item["sale_quantity"] == 80
    )
    assert converted["quantity_delta"] == -16
    assert "80 na venda → 16 CX no estoque" in converted["notes"]


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
    assert migrated["sale_quantity_factor"] == 0.2
    assert "ALIAS PERSONALIZADO" in aliases
    assert "Uva Vitoria" in aliases
    assert conn.execute(
        "SELECT quantity_delta FROM stock_movements WHERE id='opening-stock-uva-vitoria-5kg'"
    ).fetchone()[0] == 2870
    conn.close()
