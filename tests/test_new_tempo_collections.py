import uuid
from datetime import datetime as RealDateTime


def _login(client, username="admin", password="admin123", company="raios"):
    response = client.post("/api/auth/login", headers={"x-company": company}, json={"username": username, "password": password})
    assert response.status_code == 200
    return response.json()["token"]


def _seed_sale(isolated_app, company, client, nf, sale_id=None, delivered=None, delivered_at=None):
    conn = isolated_app.module.get_db(company)
    try:
        conn.execute(
            """INSERT INTO sales(id,sale_type,sale_date,sale_time,client,product,nf_number,quantity,unit_price,total,delivered,delivered_at)
               VALUES(?,?,?,?,?,?,?,?,?,?,?,?)""",
            (sale_id or str(uuid.uuid4()), "NF", "2026-10-20", "07:31", client, "Alho 250g", nf, 1, 25, 25, delivered, delivered_at),
        )
        conn.commit()
    finally:
        conn.close()


def test_new_tempo_collections_group_invoice_rows_across_companies_and_persist_payment(isolated_app):
    token = _login(isolated_app.client)
    _seed_sale(isolated_app, "raios", "NOVO TEMPO - SÃO FRANCISCO", "NT-100", delivered="sim", delivered_at="2026-10-20T07:31:00")
    _seed_sale(isolated_app, "raios", "NOVO TEMPO - SÃO FRANCISCO", "NT-100", delivered="sim", delivered_at="2026-10-20T07:31:00")
    _seed_sale(isolated_app, "estrada", "NOVO TEMPO - MECEJANA", "NT-200", delivered="sim", delivered_at="2026-10-20T07:31:00")
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


def test_new_tempo_notifications_only_start_24_hours_after_delivery(isolated_app, monkeypatch):
    token = _login(isolated_app.client)
    undelivered_id = str(uuid.uuid4())
    delivered_id = str(uuid.uuid4())
    mixed_id_a = str(uuid.uuid4())
    mixed_id_b = str(uuid.uuid4())
    _seed_sale(isolated_app, "raios", "NOVO TEMPO - CENTRO", "NT-400", undelivered_id)
    _seed_sale(isolated_app, "raios", "NOVO TEMPO - CENTRO", "NT-401", delivered_id, delivered="sim", delivered_at="2026-10-26T07:30:00")
    _seed_sale(isolated_app, "raios", "NOVO TEMPO - CENTRO", "NT-402", mixed_id_a, delivered="sim", delivered_at="2026-10-26T07:30:00")
    _seed_sale(isolated_app, "raios", "NOVO TEMPO - CENTRO", "NT-402", mixed_id_b)

    class FrozenDateTime(RealDateTime):
        current = RealDateTime(2026, 10, 27, 7, 29)

        @classmethod
        def now(cls, tz=None):
            return cls.current

    monkeypatch.setattr(isolated_app.module, "datetime", FrozenDateTime)

    rows = isolated_app.client.get("/api/mobile/new-tempo/collections", headers={"x-token": token}).json()
    undelivered = next(row for row in rows if row["nf_number"] == "NT-400")
    delivered = next(row for row in rows if row["nf_number"] == "NT-401")
    mixed = next(row for row in rows if row["nf_number"] == "NT-402")
    assert undelivered["delivered"] is False
    assert undelivered["notifications_due"] is False
    assert delivered["delivered"] is True
    assert delivered["delivered_at"] == "2026-10-26T07:30"
    assert delivered["notifications_due"] is False
    assert delivered["alert_starts_at"] == "2026-10-27T07:30"
    assert mixed["delivered"] is False
    assert mixed["notifications_due"] is False

    FrozenDateTime.current = RealDateTime(2026, 10, 27, 7, 30)
    rows = isolated_app.client.get("/api/mobile/new-tempo/collections", headers={"x-token": token}).json()
    delivered = next(row for row in rows if row["nf_number"] == "NT-401")
    assert delivered["notifications_due"] is True
    assert delivered["next_alert_at"] == "2026-10-27T08:00"


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
