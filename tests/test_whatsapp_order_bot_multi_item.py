import sqlite3

from backend.services.whatsapp_order_bot_service import advance_order_bot, order_bot_config


def _conn():
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE whatsapp_config(key TEXT PRIMARY KEY, value TEXT);
        CREATE TABLE clients(id TEXT PRIMARY KEY, name TEXT, phone TEXT, active INTEGER);
        CREATE TABLE product_prices(key TEXT PRIMARY KEY, label TEXT, price TEXT, active INTEGER);
        CREATE TABLE whatsapp_conversations(
            id TEXT PRIMARY KEY, company_key TEXT, client_id TEXT, jid TEXT, status TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE whatsapp_order_drafts(
            id TEXT PRIMARY KEY, company_key TEXT, client_id TEXT, conversation_id TEXT,
            source_message_id TEXT, idempotency_key TEXT, status TEXT, requested_quantity TEXT,
            confirmed_quantity TEXT, total TEXT, calculation_memory TEXT, confirmed_at TEXT,
            approved_by TEXT, approved_at TEXT, block_reason TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE whatsapp_order_items(
            id TEXT PRIMARY KEY, order_id TEXT, product_key TEXT, requested_quantity TEXT,
            confirmed_quantity TEXT, confirmed_damage TEXT, unit_price TEXT, total TEXT,
            maximum_consumption TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP, updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE whatsapp_order_history(
            id TEXT PRIMARY KEY, company_key TEXT, order_id TEXT, previous_status TEXT,
            new_status TEXT, changed_by TEXT, reason TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    conn.executemany(
        "INSERT INTO whatsapp_config(key,value) VALUES(?,?)",
        [
            ("bot_active", "1"),
            ("auto_reply_enabled", "1"),
            ("provider", "baileys"),
        ],
    )
    conn.execute("INSERT INTO clients(id,name,phone,active) VALUES('c1','Adriano','5595999999999',1)")
    conn.executemany(
        "INSERT INTO product_prices(key,label,price,active) VALUES(?,?,?,1)",
        [
            ("MAC_PCT", "Macaxeira com casca", "4"),
            ("ALHO_KG", "Alho descascado 1kg", "20"),
        ],
    )
    conn.execute(
        "INSERT INTO whatsapp_conversations(id,company_key,client_id,jid,status) VALUES('conv1','raios','c1','5595999999999@s.whatsapp.net','nova')"
    )
    return conn


def _processed(message_id="m1"):
    return {"conversation_id": "conv1", "client_id": "c1", "message_id": message_id}


def test_order_bot_accepts_multiple_items_before_confirmation():
    conn = _conn()
    config = order_bot_config(conn)

    first = advance_order_bot(conn, "raios", _processed("m1"), "oi", config)
    assert first["state"] == "identificando_produto"
    assert "ADICIONAR" in first["reply"]

    assert advance_order_bot(conn, "raios", _processed("m2"), "1", config)["state"] == "coletando_quantidade"
    assert advance_order_bot(conn, "raios", _processed("m3"), "10 kg", config)["state"] == "coletando_avaria"
    confirm = advance_order_bot(conn, "raios", _processed("m4"), "nao", config)
    assert confirm["state"] == "aguardando_confirmacao"
    assert "ADICIONAR" in confirm["reply"]

    add = advance_order_bot(conn, "raios", _processed("m5"), "adicionar", config)
    assert add["state"] == "identificando_produto"
    assert "Qual outro produto" in add["reply"]

    assert advance_order_bot(conn, "raios", _processed("m6"), "4", config)["state"] == "coletando_quantidade"
    assert advance_order_bot(conn, "raios", _processed("m7"), "2 kg", config)["state"] == "coletando_avaria"
    second_confirm = advance_order_bot(conn, "raios", _processed("m8"), "nao", config)
    assert second_confirm["state"] == "aguardando_confirmacao"
    assert "1. Macaxeira com casca" in second_confirm["reply"]
    assert "2. Alho descascado 1kg" in second_confirm["reply"]

    done = advance_order_bot(conn, "raios", _processed("m9"), "sim", config)
    assert done["state"] == "aguardando_aprovacao"
    order = conn.execute("SELECT * FROM whatsapp_order_drafts").fetchone()
    assert order["status"] == "aguardando_aprovacao"
    assert order["requested_quantity"] == "12"
    assert order["total"] == "80"
    items = conn.execute("SELECT * FROM whatsapp_order_items ORDER BY created_at,id").fetchall()
    assert len(items) == 2
    assert {item["product_key"] for item in items} == {"MAC_PCT", "ALHO_KG"}
    assert all(item["confirmed_quantity"] == item["requested_quantity"] for item in items)
