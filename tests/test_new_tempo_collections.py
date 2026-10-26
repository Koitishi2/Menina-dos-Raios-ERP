import uuid


def _login(client, username="admin", password="admin123", company="raios"):
    response = client.post("/api/auth/login", headers={"x-company": company}, json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["token"]


def _seed_sale(isolated_app, company, client, nf, sale_id=None):
    conn = isolated_app.module.get_db(company)
    try:
        conn.execute(
            """INSERT INTO sales(id,sale_type,sale_date,sale_time,client,product,nf_number,quantity,unit_price,total)
               VALUES(?,?,?,?,?,?,?,?,?,?)""",
            (sale_id or str(uuid.uuid4()), "NF", "2026-10-20", "07:31", client, "Alho 250g", nf, 1, 25, 25),
        )
        conn.commit()
    finally:
        conn.close()


def test_new_tempo_collections_group_invoice_rows_across_companies_and_persist_payment(isolated_app):
    token = _login(isolated_app.client)
    _seed_sale(isolated_app, "raios", "NOVO TEMPO - SÃO FRANCISCO", "NT-100")
    _seed_sale(isolated_app, "raios", "NOVO TEMPO - SÃO FRANCISCO", "NT-100")
    _seed_sale(isolated_app, "estrada", "NOVO TEMPO - MECEJANA", "NT-200")
    _seed_sale(isolated_app, "raios", "Outro Cliente", "NT-300")

    response = isolated_app.client.get("/api/mobile/new-tempo/collections", headers={"x-token": token})
    assert response.status_code == 200
    rows = response.json()
    assert len(rows) == 2
    first = next(row for row in rows if row["client"].endswith("SÃO FRANCISCO"))
    assert first["total"] == 50
    assert first["item_count"] == 2
    assert first["notifications_due"] is True
    assert first["status"] == "pendente"

    paid = isolated_app.client.put(
        f"/api/mobile/new-tempo/collections/{first['id']}",
        headers={"x-token": token},
        json={"company_key": first["company_key"], "status": "pago"},
    )
    assert paid.status_code == 200
    refreshed = isolated_app.client.get("/api/mobile/new-tempo/collections", headers={"x-token": token}).json()
    assert next(row for row in refreshed if row["id"] == first["id"])["status"] == "pago"


def test_new_tempo_collection_alert_api_is_admin_only(isolated_app):
    conn = isolated_app.module.get_control_db()
    viewer_id = str(uuid.uuid4())
    conn.execute(
        "INSERT INTO users(id,username,password_hash,full_name,role,active) VALUES(?,?,?,?,?,1)",
        (viewer_id, "viewer_alert", isolated_app.module.hash_password("viewerpass123"), "Viewer", "viewer"),
    )
    conn.commit()
    conn.close()
    token = _login(isolated_app.client, "viewer_alert", "viewerpass123")
    response = isolated_app.client.get("/api/mobile/new-tempo/collections", headers={"x-token": token})
    assert response.status_code == 403
