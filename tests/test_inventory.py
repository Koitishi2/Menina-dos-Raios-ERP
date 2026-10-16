import sqlite3
import uuid
from datetime import datetime, timedelta

from test_orcamentos import _headers, _login


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
