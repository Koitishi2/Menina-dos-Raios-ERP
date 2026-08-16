import sqlite3
import uuid
from urllib.parse import quote


MAC_VACUO = "Macaxeira a V\u00e1cuo"
UVA_VITORIA = "Uva Vit\u00f3ria"


def _headers(token):
    return {"x-token": token}


def _login_admin(isolated_app):
    response = isolated_app.client.post(
        "/api/auth/login",
        headers={"x-company": "raios"},
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    return response.json()["token"]


def _insert_sale(db_path, product, quantity, sale_date="2026-08-16"):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            INSERT INTO sales(
                id, sale_type, sale_date, sale_time, client, product,
                quantity, unit_price, total, source
            ) VALUES(?,?,?,?,?,?,?,?,?,?)
            """,
            (
                uuid.uuid4().hex,
                "NF",
                sale_date,
                "08:00",
                "Cliente Projecao",
                product,
                quantity,
                10,
                quantity * 10,
                "manual",
            ),
        )
        conn.commit()
    finally:
        conn.close()


def test_projection_accepts_multiple_products_and_filters_totals(isolated_app):
    token = _login_admin(isolated_app)
    db_path = isolated_app.db_paths["raios"]
    _insert_sale(db_path, MAC_VACUO, 10)
    _insert_sale(db_path, "Alho 250g", 5)
    _insert_sale(db_path, UVA_VITORIA, 20)

    products = quote(f"{MAC_VACUO},Alho 250g", safe="")
    response = isolated_app.client.get(
        f"/api/projecao/producao?days=7&products={products}",
        headers=_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    names = {row["produto"] for row in body["produtos"]}
    assert len(names) == 2
    assert "Alho 250g" in names
    assert all("Uva" not in name for name in names)
    assert body["resumo"]["total_vendido"] == 15
    assert body["resumo"]["proj_7"] > 0


def test_projection_keeps_single_product_filter_compatible(isolated_app):
    token = _login_admin(isolated_app)
    db_path = isolated_app.db_paths["raios"]
    _insert_sale(db_path, MAC_VACUO, 10)
    _insert_sale(db_path, "Alho 250g", 5)

    product = quote("Alho 250g", safe="")
    response = isolated_app.client.get(
        f"/api/projecao/producao?days=7&product={product}",
        headers=_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert [row["produto"] for row in body["produtos"]] == ["Alho 250g"]
    assert body["resumo"]["total_vendido"] == 5
