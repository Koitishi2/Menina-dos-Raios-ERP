import sqlite3
import threading
import time


def test_get_db_does_not_change_journal_mode(isolated_app, monkeypatch):
    module = isolated_app.module
    statements = []
    connect_kwargs = []
    original_connect = module.sqlite3.connect

    def traced_connect(*args, **kwargs):
        connect_kwargs.append(kwargs.copy())
        conn = original_connect(*args, **kwargs)
        conn.set_trace_callback(statements.append)
        return conn

    monkeypatch.setattr(module.sqlite3, "connect", traced_connect)
    conn = module.get_db("raios")
    try:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert conn.execute("PRAGMA busy_timeout").fetchone()[0] == 20000
    finally:
        conn.close()

    setup_statements = statements[:-2]
    assert not any("journal_mode=" in statement.replace(" ", "").lower() for statement in setup_statements)
    assert connect_kwargs[-1]["timeout"] == 20


def test_get_app_notes_db_does_not_change_journal_mode(isolated_app, monkeypatch):
    module = isolated_app.module
    statements = []
    original_connect = module.sqlite3.connect

    def traced_connect(*args, **kwargs):
        conn = original_connect(*args, **kwargs)
        conn.set_trace_callback(statements.append)
        return conn

    monkeypatch.setattr(module.sqlite3, "connect", traced_connect)
    conn = module.get_app_notes_db()
    try:
        assert conn.execute("PRAGMA journal_mode").fetchone()[0].lower() == "wal"
        assert conn.execute("PRAGMA busy_timeout").fetchone()[0] == 20000
    finally:
        conn.close()

    assert not any("journal_mode=" in statement.replace(" ", "").lower() for statement in statements)


def test_concurrent_writer_waits_without_database_locked(isolated_app):
    module = isolated_app.module
    first = module.get_db("raios")
    first.execute("CREATE TABLE IF NOT EXISTS app_lock_probe(id INTEGER PRIMARY KEY, value TEXT NOT NULL)")
    first.commit()
    first.execute("BEGIN IMMEDIATE")
    first.execute("INSERT INTO app_lock_probe(value) VALUES(?)", ("first",))

    result = {}

    def second_writer():
        conn = module.get_db("raios")
        try:
            conn.execute("INSERT INTO app_lock_probe(value) VALUES(?)", ("second",))
            conn.commit()
            result["ok"] = True
        except Exception as exc:  # pragma: no cover - asserted below
            result["error"] = repr(exc)
        finally:
            conn.close()

    worker = threading.Thread(target=second_writer)
    worker.start()
    time.sleep(0.2)
    assert worker.is_alive(), "A segunda escrita deveria aguardar o primeiro escritor."
    first.commit()
    first.close()
    worker.join(timeout=5)

    assert not worker.is_alive()
    assert result == {"ok": True}
    conn = module.get_db("raios")
    try:
        values = [row[0] for row in conn.execute("SELECT value FROM app_lock_probe ORDER BY id")]
    finally:
        conn.close()
    assert values == ["first", "second"]
    isolated_app.assert_real_unchanged()


def test_existing_sale_edit_waits_for_concurrent_writer(isolated_app):
    client = isolated_app.client
    login = client.post(
        "/api/auth/login",
        headers={"x-company": "raios"},
        json={"username": "admin", "password": "admin123"},
    )
    assert login.status_code == 200
    headers = {"x-token": login.json()["token"], "x-company": "raios"}
    seller = client.post("/api/sellers", headers=headers, json={"name": "Vendedor Concorrencia"})
    assert seller.status_code == 200
    seller_id = seller.json()["seller"]["id"]
    created = client.post(
        "/api/sales",
        headers=headers,
        json={
            "sale_type": "NF", "sale_date": "2026-09-17", "sale_time": "08:00",
            "client": "Cliente Edicao Concorrente", "product": "Macaxeira com Casca (KG)",
            "nf_number": "LOCK-EDIT-001", "quantity": 2, "unit_price": 4,
            "total": 8, "notes": "antes", "source": "manual", "seller_id": seller_id,
        },
    )
    assert created.status_code == 200

    blocker = isolated_app.module.get_db("raios")
    blocker.execute("BEGIN IMMEDIATE")
    result = {}

    def edit_sale():
        response = client.put(
            f"/api/sales/{created.json()['id']}",
            headers=headers,
            json={
                "sale_type": "NF", "sale_date": "2026-09-17", "sale_time": "08:30",
                "client": "Cliente Edicao Concorrente", "product": "Macaxeira com Casca (KG)",
                "nf_number": "LOCK-EDIT-001", "quantity": 3, "unit_price": 4,
                "total": 12, "notes": "editado", "delivery_person": None,
                "plate": None, "source": "manual", "seller_id": seller_id,
            },
        )
        result["status"] = response.status_code
        result["body"] = response.json()

    worker = threading.Thread(target=edit_sale)
    worker.start()
    time.sleep(0.2)
    assert worker.is_alive(), "A edicao HTTP deveria aguardar o escritor concorrente."
    blocker.commit()
    blocker.close()
    worker.join(timeout=5)

    assert not worker.is_alive()
    assert result == {"status": 200, "body": {"ok": True}}
    rows = client.get("/api/sales?search=LOCK-EDIT-001", headers=headers)
    assert rows.status_code == 200
    assert len(rows.json()) == 1
    assert rows.json()[0]["total"] == 12
    assert rows.json()[0]["notes"] == "editado"
    isolated_app.assert_real_unchanged()
