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
