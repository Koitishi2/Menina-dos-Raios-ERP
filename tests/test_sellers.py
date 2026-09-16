import importlib.util
import sqlite3
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load_sellers_repository():
    path = ROOT / "backend" / "repositories" / "sellers_repository.py"
    spec = importlib.util.spec_from_file_location("sellers_repository_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _base_conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.execute(
        """CREATE TABLE sales (
            id TEXT PRIMARY KEY,
            sale_date TEXT,
            product TEXT,
            total REAL
        )"""
    )
    conn.execute(
        """CREATE TABLE paladar_sales (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            saledate TEXT,
            product TEXT,
            total REAL
        )"""
    )
    return conn


def _columns(conn, table):
    return {row[1] for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _login(client, username="admin", password="admin123", company="raios"):
    response = client.post(
        "/api/auth/login",
        headers={"x-company": company},
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["token"]


def _headers(token, company="raios"):
    return {"x-token": token, "x-company": company}


def _seller(client, token, company="raios", name="Joao Vendedor"):
    response = client.post("/api/sellers", headers=_headers(token, company), json={"name": name})
    assert response.status_code == 200
    return response.json()["seller"]


def _sale_payload(**overrides):
    payload = {
        "sale_type": "NF",
        "sale_date": "2026-09-10",
        "sale_time": "09:00",
        "client": "Cliente Vendedor",
        "product": "Produto Vendedor",
        "nf_number": "SEL-001",
        "quantity": 2,
        "unit_price": 50,
        "total": 100,
        "delivery_person": "Entregador Teste",
        "source": "manual",
    }
    payload.update(overrides)
    return payload


def test_sellers_normalize_duplicates_per_company_and_history(isolated_app):
    token = _login(isolated_app.client)

    first = _seller(isolated_app.client, token, "raios", "Joao da Silva")
    duplicate = isolated_app.client.post(
        "/api/sellers",
        headers=_headers(token, "raios"),
        json={"name": "  joao   da silva  "},
    )
    assert duplicate.status_code == 200
    assert duplicate.json()["existed"] is True
    assert duplicate.json()["seller"]["id"] == first["id"]

    estrada = _seller(isolated_app.client, token, "estrada", "Joao da Silva")
    assert estrada["id"] != first["id"]

    renamed = isolated_app.client.put(
        f"/api/sellers/{first['id']}",
        headers=_headers(token, "raios"),
        json={"name": "Joao Silva", "reason": "correcao"},
    )
    assert renamed.status_code == 200
    assert renamed.json()["name"] == "Joao Silva"

    history = isolated_app.client.get(f"/api/sellers/{first['id']}/history", headers=_headers(token, "raios"))
    assert history.status_code == 200
    assert history.json()[0]["old_name"] == "Joao da Silva"


def test_sales_require_active_seller_and_keep_snapshot(isolated_app):
    token = _login(isolated_app.client)
    missing = isolated_app.client.post("/api/sales", headers=_headers(token), json=_sale_payload())
    assert missing.status_code == 400
    assert "vendeu" in missing.json()["detail"]

    seller = _seller(isolated_app.client, token, name="Maria Vendas")
    created = isolated_app.client.post(
        "/api/sales",
        headers=_headers(token),
        json=_sale_payload(seller_id=seller["id"]),
    )
    assert created.status_code == 200
    row = created.json()
    assert row["seller_id"] == seller["id"]
    assert row["seller_name_snapshot"] == "Maria Vendas"
    assert row["delivery_person"] == "Entregador Teste"

    isolated_app.client.put(
        f"/api/sellers/{seller['id']}",
        headers=_headers(token),
        json={"name": "Maria Renomeada"},
    )
    listed = isolated_app.client.get("/api/sales?search=SEL-001", headers=_headers(token)).json()
    assert listed[0]["seller_name_snapshot"] == "Maria Vendas"

    deactivated = isolated_app.client.post(f"/api/sellers/{seller['id']}/deactivate", headers=_headers(token))
    assert deactivated.status_code == 200
    blocked = isolated_app.client.post(
        "/api/sales",
        headers=_headers(token),
        json=_sale_payload(nf_number="SEL-002", seller_id=seller["id"]),
    )
    assert blocked.status_code == 400
    assert "inativo" in blocked.json()["detail"].lower()


def test_paladar_sales_store_seller_and_summary_filters(isolated_app):
    token = _login(isolated_app.client)
    first = _seller(isolated_app.client, token, name="Vendedor Monteiro Um")
    second = _seller(isolated_app.client, token, name="Vendedor Monteiro Dois")

    for seller, nf, total in ((first, "MON-SELL-1", 200), (second, "MON-SELL-2", 300)):
        response = isolated_app.client.post(
            "/api/monteiro/sales",
            headers=_headers(token),
            json={
                "saledate": "2026-09-12",
                "client": "Cliente Monteiro Vendedor",
                "nf_number": nf,
                "seller_id": seller["id"],
                "driver": "Motorista Monteiro",
                "items": [{"product": "Produto M", "quantity": 1, "unitprice": total, "total": total}],
            },
        )
        assert response.status_code == 200

    all_summary = isolated_app.client.get("/api/monteiro/summary?month=09&year=2026", headers=_headers(token))
    assert all_summary.status_code == 200
    assert all_summary.json()["total_receita"] == 500
    assert {row["seller_name"] for row in all_summary.json()["por_vendedor"]} == {
        "Vendedor Monteiro Um",
        "Vendedor Monteiro Dois",
    }

    filtered = isolated_app.client.get(
        f"/api/monteiro/summary?month=09&year=2026&seller_id={first['id']}",
        headers=_headers(token),
    )
    assert filtered.status_code == 200
    assert filtered.json()["total_receita"] == 200

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        stored = conn.execute(
            "SELECT seller_id, seller_name_snapshot, driver FROM paladar_sales WHERE nf_number=?",
            ("MON-SELL-1",),
        ).fetchone()
        assert stored == (first["id"], "Vendedor Monteiro Um", "Motorista Monteiro")
    finally:
        conn.close()


def test_sellers_schema_runner_is_idempotent_and_preserves_old_sales():
    repository = _load_sellers_repository()
    conn = _base_conn()
    try:
        conn.execute(
            "INSERT INTO sales(id,sale_date,product,total) VALUES('old','2026-09-01','Produto Antigo',10)"
        )
        repository.apply_sellers_schema(conn)
        repository.apply_sellers_schema(conn)

        assert {"seller_id", "seller_name_snapshot"}.issubset(_columns(conn, "sales"))
        assert {"seller_id", "seller_name_snapshot"}.issubset(_columns(conn, "paladar_sales"))
        old = conn.execute("SELECT seller_id,seller_name_snapshot,total FROM sales WHERE id='old'").fetchone()
        assert old["seller_id"] is None
        assert old["seller_name_snapshot"] is None
        assert old["total"] == 10

        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """INSERT INTO sellers(id,company_key,name,normalized_name)
                   VALUES('s1','raios','Joao','joao'),('s2','raios','JOAO','joao')"""
            )
        conn.execute(
            """INSERT INTO sellers(id,company_key,name,normalized_name)
               VALUES('s3','estrada','Joao','joao')"""
        )
    finally:
        conn.close()


def test_sellers_schema_runner_reapplies_after_documented_down_sql():
    repository = _load_sellers_repository()
    down_sql = (ROOT / "backend" / "migrations" / "20260916_sellers_down.sql").read_text(encoding="utf-8")
    conn = _base_conn()
    try:
        repository.apply_sellers_schema(conn)
        conn.executescript(down_sql)
        assert "seller_id" in _columns(conn, "sales")
        assert conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sellers'").fetchone() is None

        repository.apply_sellers_schema(conn)
        assert conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sellers'").fetchone()
        repository.apply_sellers_schema(conn)
    finally:
        conn.close()


def test_sellers_schema_runner_blocks_partial_schema_with_clear_error():
    repository = _load_sellers_repository()
    conn = _base_conn()
    try:
        conn.execute("CREATE TABLE sellers (id TEXT PRIMARY KEY, company_key TEXT)")
        with pytest.raises(repository.SellersMigrationError, match="Schema parcial em sellers"):
            repository.apply_sellers_schema(conn)
        assert conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='seller_history'").fetchone() is None
    finally:
        conn.close()


def test_sellers_schema_runner_rolls_back_failure_between_steps():
    repository = _load_sellers_repository()
    real_conn = _base_conn()

    class FailingConn:
        def __init__(self, conn):
            self.conn = conn
            self.created_sellers = False

        def execute(self, sql, params=()):
            normalized = " ".join(str(sql).split()).upper()
            if normalized.startswith("CREATE TABLE IF NOT EXISTS SELLERS"):
                self.created_sellers = True
            if self.created_sellers and normalized.startswith("CREATE TABLE IF NOT EXISTS SELLER_HISTORY"):
                raise sqlite3.OperationalError("falha controlada entre etapas")
            return self.conn.execute(sql, params)

    try:
        with pytest.raises(repository.SellersMigrationError, match="falha controlada entre etapas"):
            repository.apply_sellers_schema(FailingConn(real_conn))
        assert real_conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='sellers'").fetchone() is None
        assert "seller_id" not in _columns(real_conn, "sales")
    finally:
        real_conn.close()


def test_sellers_schema_runner_requires_base_sales_tables():
    repository = _load_sellers_repository()
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    try:
        with pytest.raises(repository.SellersMigrationError, match="Schema base ausente"):
            repository.apply_sellers_schema(conn)
        assert conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall() == []
    finally:
        conn.close()
