import json
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import pytest

from backend.services.whatsapp_campaign_service import confirm_manual_batch, create_manual_batch, list_suggestions


ROOT = Path(__file__).resolve().parents[1]
INBOUND_UP = ROOT / "backend" / "migrations" / "20260914_whatsapp_inbound_up.sql"
INBOUND_DOWN = ROOT / "backend" / "migrations" / "20260914_whatsapp_inbound_down.sql"
ORDERS_UP = ROOT / "backend" / "migrations" / "20260914_whatsapp_orders_up.sql"


def _login(app, username="admin", password="admin123", company="raios"):
    response = app.client.post("/api/auth/login", headers={"x-company": company}, json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["token"]


def _headers(token, company="raios"):
    return {"x-token": token, "x-company": company}


def _internal_headers(token="inbound-test-token"):
    return {"content-type": "application/json", "x-whatsapp-inbound-token": token}


def _event(**changes):
    value = {
        "provider": "baileys", "instance": "raios-primary", "event_id": "event-001",
        "message_id": "message-001", "remote_jid": "5595991234567@s.whatsapp.net",
        "from_me": False, "message_type": "conversation", "text": "Quero comprar",
        "timestamp": "2026-09-14T22:00:00-04:00",
    }
    value.update(changes)
    return value


def _configure_inbound(monkeypatch, company="raios", enabled="true"):
    monkeypatch.setenv("WHATSAPP_INBOUND_ENABLED", enabled)
    monkeypatch.setenv("WHATSAPP_INBOUND_TOKEN", "inbound-test-token")
    monkeypatch.setenv("WHATSAPP_INBOUND_INSTANCE", "raios-primary")
    monkeypatch.setenv("WHATSAPP_INBOUND_COMPANY", company)


def _configure_order_bot(isolated_app, monkeypatch):
    monkeypatch.setenv("WHATSAPP_OUTBOUND_ENABLED", "true")
    monkeypatch.setenv("WHATSAPP_OUTBOUND_MODE", "sandbox")
    monkeypatch.setenv("WHATSAPP_OUTBOUND_SANDBOX_NUMBERS", "+5595991234567")
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        conn.executemany(
            "INSERT OR REPLACE INTO whatsapp_config(key,value) VALUES(?,?)",
            [
                ("provider", "baileys"),
                ("bot_active", "1"),
                ("auto_reply_enabled", "1"),
                ("auto_reply_from", "00:00"),
                ("auto_reply_to", "23:59"),
            ],
        )
        conn.commit()
    finally:
        conn.close()


def _create_client(app, token, name="Cliente Inbound", phone="95991234567", company="raios"):
    response = app.client.post("/api/clients", headers=_headers(token, company), json={"name": name, "phone": phone})
    assert response.status_code == 200, response.text
    return response.json()


def _make_eligible(app, client, company="raios", sale_date="2026-08-01"):
    digits = "".join(char for char in client["phone"] if char.isdigit())
    if len(digits) in (10, 11):
        digits = "55" + digits
    conn = sqlite3.connect(app.db_paths[company])
    try:
        conn.execute(
            "INSERT INTO whatsapp_consent(id,company_key,client_id,phone_e164,status,source) VALUES(?,?,?,?,?,'manual')",
            ("consent-" + client["id"], company, client["id"], "+" + digits, "opt_in"),
        )
        conn.execute(
            "INSERT INTO sales(id,sale_type,sale_date,client,quantity,unit_price,total) VALUES(?, 'AVULSO', ?, ?, 1, 1, 1)",
            ("sale-" + client["id"], sale_date, client["name"]),
        )
        conn.commit()
    finally:
        conn.close()


def test_incremental_migration_and_rollback_preserve_previous_schema():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript("""CREATE TABLE clients(id TEXT PRIMARY KEY,active INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE product_prices(key TEXT PRIMARY KEY,active INTEGER NOT NULL DEFAULT 1);
        CREATE TABLE sales(id TEXT PRIMARY KEY);
        CREATE TABLE whatsapp_contacts(id TEXT PRIMARY KEY);
        INSERT INTO clients(id,active) VALUES('sentinel-client',1);
        INSERT INTO product_prices(key,active) VALUES('sentinel-product',1);
        INSERT INTO sales(id) VALUES('sentinel-sale');""")
    conn.executescript(ORDERS_UP.read_text(encoding="utf-8"))
    conn.executescript(INBOUND_UP.read_text(encoding="utf-8"))
    created = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"whatsapp_inbound_events", "whatsapp_manual_batches", "whatsapp_manual_batch_items"} <= created
    inbound_columns = {row[1]: row for row in conn.execute("PRAGMA table_info(whatsapp_inbound_events)")}
    batch_columns = {row[1]: row for row in conn.execute("PRAGMA table_info(whatsapp_manual_batches)")}
    item_columns = {row[1]: row for row in conn.execute("PRAGMA table_info(whatsapp_manual_batch_items)")}
    assert inbound_columns["id"][5] == 1
    assert {"event_id", "external_message_id", "processing_status", "duplicate_count", "client_id"} <= inbound_columns.keys()
    assert {"selection_version", "confirmed_at", "expires_at", "status"} <= batch_columns.keys()
    assert {"idempotency_key", "result_code", "result_detail", "sent_at", "status"} <= item_columns.keys()
    indexes = {
        row[1]
        for table in ("whatsapp_inbound_events", "whatsapp_manual_batches", "whatsapp_manual_batch_items")
        for row in conn.execute(f"PRAGMA index_list({table})")
    }
    assert {
        "idx_wa_inbound_company_created", "idx_wa_inbound_company_status",
        "idx_wa_manual_batches_company", "idx_wa_manual_items_batch", "idx_wa_manual_items_client",
    } <= indexes
    conn.executescript(INBOUND_DOWN.read_text(encoding="utf-8"))
    remaining = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert not {"whatsapp_inbound_events", "whatsapp_manual_batches", "whatsapp_manual_batch_items"} & remaining
    assert {"whatsapp_messages", "whatsapp_order_drafts", "clients"} <= remaining
    assert conn.execute("SELECT id FROM clients").fetchone()[0] == "sentinel-client"
    assert conn.execute("SELECT key FROM product_prices").fetchone()[0] == "sentinel-product"
    assert conn.execute("SELECT id FROM sales").fetchone()[0] == "sentinel-sale"
    conn.executescript(INBOUND_UP.read_text(encoding="utf-8"))
    reapplied = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert {"whatsapp_inbound_events", "whatsapp_manual_batches", "whatsapp_manual_batch_items"} <= reapplied
    conn.close()


@pytest.mark.parametrize("token", ["", "wrong-token"])
def test_internal_endpoint_requires_correct_token(isolated_app, monkeypatch, token):
    _configure_inbound(monkeypatch)
    response = isolated_app.client.post("/internal/whatsapp/events", headers=_internal_headers(token), json=_event())
    assert response.status_code == 401


def test_internal_endpoint_validates_enabled_content_type_size_and_instance(isolated_app, monkeypatch):
    _configure_inbound(monkeypatch, enabled="false")
    disabled = isolated_app.client.post("/internal/whatsapp/events", headers=_internal_headers(), json=_event())
    assert disabled.status_code == 503
    _configure_inbound(monkeypatch)
    wrong_type = isolated_app.client.post("/internal/whatsapp/events", headers={"x-whatsapp-inbound-token": "inbound-test-token"}, content="{}")
    invalid = isolated_app.client.post("/internal/whatsapp/events", headers=_internal_headers(), content="{")
    wrong_instance = isolated_app.client.post("/internal/whatsapp/events", headers=_internal_headers(), json=_event(instance="other"))
    monkeypatch.setenv("WHATSAPP_INBOUND_MAX_BODY_BYTES", "1024")
    too_large = isolated_app.client.post("/internal/whatsapp/events", headers=_internal_headers(), json=_event(text="x" * 2000))
    assert (wrong_type.status_code, invalid.status_code, wrong_instance.status_code, too_large.status_code) == (415, 400, 403, 413)


def test_internal_endpoint_rejects_invalid_timestamp_and_oversized_text(isolated_app, monkeypatch):
    _configure_inbound(monkeypatch)
    invalid_timestamp = isolated_app.client.post(
        "/internal/whatsapp/events", headers=_internal_headers(), json=_event(timestamp="not-a-date")
    )
    monkeypatch.setenv("WHATSAPP_INBOUND_MAX_BODY_BYTES", "20000")
    oversized_text = isolated_app.client.post(
        "/internal/whatsapp/events", headers=_internal_headers(), json=_event(text="x" * 10001)
    )
    assert invalid_timestamp.status_code == 400
    assert invalid_timestamp.json()["detail"] == "timestamp_invalido"
    assert oversized_text.status_code == 422
    assert isolated_app.external_calls == []


def test_valid_inbound_is_idempotent_and_creates_no_order_sale_or_stock(isolated_app, monkeypatch):
    _configure_inbound(monkeypatch)
    token = _login(isolated_app)
    client = _create_client(isolated_app, token)
    first = isolated_app.client.post("/internal/whatsapp/events", headers=_internal_headers(), json=_event())
    second = isolated_app.client.post("/internal/whatsapp/events", headers=_internal_headers(), json=_event())
    assert first.status_code == 200 and first.json()["client_id"] == client["id"]
    assert second.status_code == 200 and second.json()["duplicate"] is True
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_inbound_events").fetchone()[0] == 1
        assert conn.execute("SELECT duplicate_count FROM whatsapp_inbound_events").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_messages").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_conversations").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_order_drafts").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0] == 0
    finally:
        conn.close()
    assert isolated_app.external_calls == []


def test_order_bot_collects_request_and_creates_approval_order_without_sale(isolated_app, monkeypatch):
    _configure_inbound(monkeypatch)
    _configure_order_bot(isolated_app, monkeypatch)
    token = _login(isolated_app)
    client = _create_client(isolated_app, token, name="Cliente Pedido")
    sent = []
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    product_prices_before = conn.execute("SELECT * FROM product_prices ORDER BY key").fetchall()
    conn.close()

    def fake_send(phone, message, config):
        sent.append({"phone": phone, "message": message, "provider": config.get("provider"), "session": "initial"})
        return {"ok": True, "response": "mock_ok"}

    def restarted_send(phone, message, config):
        sent.append({"phone": phone, "message": message, "provider": config.get("provider"), "session": "restarted"})
        return {"ok": True, "response": "mock_ok"}

    isolated_app.module.wa_send = fake_send
    texts = ["Oi", "1", "10 kg", "nao", "sim"]
    responses = []
    for index, text in enumerate(texts, start=1):
        if index == 5:
            isolated_app.module.wa_send = restarted_send
        response = isolated_app.client.post(
            "/internal/whatsapp/events",
            headers=_internal_headers(),
            json=_event(
                event_id=f"order-event-{index}",
                message_id=f"order-message-{index}",
                text=text,
                timestamp=f"2026-09-14T12:0{index}:00-04:00",
            ),
        )
        assert response.status_code == 200, response.text
        responses.append(response.json())

    assert [item["bot"]["state"] for item in responses] == [
        "identificando_produto", "coletando_quantidade", "coletando_avaria",
        "aguardando_confirmacao", "aguardando_aprovacao",
    ]
    assert all(item["bot"]["delivery"]["sent"] is True for item in responses)
    assert sent[0]["phone"] == "5595991234567"
    assert "Cliente Pedido" in sent[0]["message"]
    assert "atendimento automatizado" in sent[0]["message"]
    assert "conversa será registrada" in sent[0]["message"]
    assert "Macaxeira com casca" in sent[0]["message"]
    assert "Qual quantidade" in sent[1]["message"]
    assert "Tem avaria" in sent[2]["message"]
    assert "Está correto? Responda SIM ou NAO." in sent[3]["message"]
    assert "Pedido feito" in sent[4]["message"]
    assert sent[4]["session"] == "restarted"

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    conn.row_factory = sqlite3.Row
    try:
        order = conn.execute("SELECT * FROM whatsapp_order_drafts").fetchone()
        item = conn.execute("SELECT * FROM whatsapp_order_items WHERE order_id=?", (order["id"],)).fetchone()
        assert order["status"] == "aguardando_aprovacao"
        assert order["requested_quantity"] == "10"
        assert item["product_key"] == "MAC_PCT"
        assert item["confirmed_quantity"] == "10"
        assert item["confirmed_damage"] == "0"
        score = json.loads(order["calculation_memory"])
        assert score["origin"] == "cliente_iniciou_contato"
        assert score["order_score"] == 100
        assert sum(score["score_components"].values()) == 100
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_consent WHERE client_id=?", (client["id"],)).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0] == 0
        assert [tuple(row) for row in conn.execute("SELECT * FROM product_prices ORDER BY key").fetchall()] == product_prices_before
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_messages WHERE direction='recebida'").fetchone()[0] == 5
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_messages WHERE direction='enviada'").fetchone()[0] == 5
    finally:
        conn.close()

    listed = isolated_app.client.get("/api/whatsapp/orders", headers=_headers(token))
    assert listed.status_code == 200
    assert listed.json()[0]["status"] == "aguardando_aprovacao"
    assert isolated_app.external_calls == []

    repeated = isolated_app.client.post(
        "/internal/whatsapp/events",
        headers=_internal_headers(),
        json=_event(
            event_id="order-event-repeat-sim", message_id="order-message-repeat-sim",
            text="SIM", timestamp="2026-09-14T12:06:00-04:00",
        ),
    )
    assert repeated.status_code == 200
    assert repeated.json()["bot"]["handled"] is False
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_order_drafts").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_messages WHERE direction='enviada'").fetchone()[0] == 5
    finally:
        conn.close()

    for marker in (
        "WEBHOOK_RECEBIDO_OK", "CONVERSA_REGISTRADA_OK", "MENSAGEM_AUTOMATICA_OK",
        "RESUMO_CONFIRMADO_OK", "PEDIDO_AGUARDANDO_APROVACAO_OK", "PONTUACAO_SALVA_OK",
        "VENDA_NAO_CRIADA_OK", "ESTOQUE_NAO_ALTERADO_OK", "IDEMPOTENCIA_OK",
    ):
        print(marker)


def test_order_bot_creates_unknown_client_only_when_sandbox_is_active(isolated_app, monkeypatch):
    _configure_inbound(monkeypatch)
    _configure_order_bot(isolated_app, monkeypatch)
    sent = []
    isolated_app.module.wa_send = lambda phone, message, config: sent.append((phone, message)) or {
        "ok": True, "response": "mock_ok",
    }

    response = isolated_app.client.post(
        "/internal/whatsapp/events", headers=_internal_headers(),
        json=_event(event_id="unknown-event", message_id="unknown-message", text="Oi"),
    )

    assert response.status_code == 200
    assert response.json()["bot"]["state"] == "identificando_produto"
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    conn.row_factory = sqlite3.Row
    try:
        client = conn.execute("SELECT * FROM clients WHERE phone='+5595991234567'").fetchone()
        assert client["name"] == "Cliente WhatsApp 4567"
        assert client["created_by"] == "whatsapp_bot"
        assert "Cadastro automatico" in client["notes"]
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_consent WHERE client_id=?", (client["id"],)).fetchone()[0] == 0
    finally:
        conn.close()
    assert len(sent) == 1


def test_order_bot_requests_only_missing_invalid_data(isolated_app, monkeypatch):
    _configure_inbound(monkeypatch)
    _configure_order_bot(isolated_app, monkeypatch)
    token = _login(isolated_app)
    _create_client(isolated_app, token)
    sent = []
    isolated_app.module.wa_send = lambda phone, message, config: sent.append(message) or {
        "ok": True, "response": "mock_ok",
    }

    texts = ["Oi", "1", "dez", "10 litros", "10 kg", "talvez"]
    states = []
    for index, text in enumerate(texts):
        response = isolated_app.client.post(
            "/internal/whatsapp/events", headers=_internal_headers(),
            json=_event(
                event_id=f"invalid-event-{index}", message_id=f"invalid-message-{index}",
                text=text, timestamp=f"2026-09-14T13:0{index}:00-04:00",
            ),
        )
        assert response.status_code == 200
        states.append(response.json()["bot"]["state"])

    assert states == [
        "identificando_produto", "coletando_quantidade", "coletando_quantidade",
        "coletando_quantidade", "coletando_avaria", "coletando_avaria",
    ]
    assert "quantidade valida em KG" in sent[2]
    assert "quantidade valida em KG" in sent[3]
    assert "Responda NAO ou informe a avaria em KG" in sent[5]
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        assert conn.execute("SELECT status FROM whatsapp_order_drafts").fetchone()[0] == "rascunho"
        assert conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0] == 0
    finally:
        conn.close()


def test_order_bot_records_outbound_failure_without_sale(isolated_app, monkeypatch):
    _configure_inbound(monkeypatch)
    _configure_order_bot(isolated_app, monkeypatch)
    token = _login(isolated_app)
    _create_client(isolated_app, token)
    isolated_app.module.wa_send = lambda *args: {"ok": False, "response": "falha_mockada"}

    response = isolated_app.client.post(
        "/internal/whatsapp/events", headers=_internal_headers(),
        json=_event(event_id="failed-send-event", message_id="failed-send-message", text="Oi"),
    )

    assert response.status_code == 200
    assert response.json()["bot"]["delivery"]["sent"] is False
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        outgoing = conn.execute(
            "SELECT status,error_text FROM whatsapp_messages WHERE direction='enviada'"
        ).fetchone()
        assert outgoing == ("falha", "falha_mockada")
        assert conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_order_drafts").fetchone()[0] == 0
    finally:
        conn.close()


def test_order_bot_hands_off_to_human_without_automatic_reply(isolated_app, monkeypatch):
    _configure_inbound(monkeypatch)
    _configure_order_bot(isolated_app, monkeypatch)
    token = _login(isolated_app)
    client = _create_client(isolated_app, token, name="Cliente Humano")
    sent = []
    isolated_app.module.wa_send = lambda *args: sent.append(args) or {"ok": True, "response": "mock"}

    first = isolated_app.client.post(
        "/internal/whatsapp/events",
        headers=_internal_headers(),
        json=_event(event_id="human-start-event", message_id="human-start-message", text="Oi"),
    )
    assert first.status_code == 200
    assert len(sent) == 1

    response = isolated_app.client.post(
        "/internal/whatsapp/events",
        headers=_internal_headers(),
        json=_event(event_id="human-event", message_id="human-message", text="Quero falar com atendente"),
    )

    assert response.status_code == 200
    assert "bot" not in response.json()
    assert len(sent) == 1
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        conversation = conn.execute(
            "SELECT status FROM whatsapp_conversations WHERE client_id=?", (client["id"],)
        ).fetchone()
        event = conn.execute(
            "SELECT command,new_state FROM whatsapp_inbound_events WHERE event_id='human-event'"
        ).fetchone()
        assert conversation[0] == "atendimento_humano"
        assert event == ("QUERO FALAR COM ATENDENTE", "atendimento_humano")
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_messages WHERE direction='enviada'").fetchone()[0] == 1
    finally:
        conn.close()
    print("ATENDIMENTO_HUMANO_OK")


def test_order_bot_test_mode_requires_sandbox(isolated_app, monkeypatch):
    _configure_inbound(monkeypatch)
    token = _login(isolated_app)
    client = _create_client(isolated_app, token, name="Cliente Teste", phone="95991234567")
    _configure_order_bot(isolated_app, monkeypatch)
    monkeypatch.setenv("WHATSAPP_OUTBOUND_MODE", "production")
    monkeypatch.setenv("WHATSAPP_OUTBOUND_PRODUCTION_APPROVED", "true")
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    conn.execute("INSERT OR REPLACE INTO whatsapp_config(key,value) VALUES('test_mode','1')")
    conn.commit()
    conn.close()

    response = isolated_app.client.post(
        "/internal/whatsapp/events",
        headers=_internal_headers(),
        json=_event(
            event_id="test-mode-event", message_id="test-mode-message",
            text="Oi", timestamp="2026-09-17T10:00:00-04:00",
        ),
    )

    assert response.status_code == 200
    assert response.json()["bot"] == {"handled": False, "reason": "modo_teste_exige_sandbox"}
    assert isolated_app.external_calls == []
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        assert conn.execute(
            "SELECT COUNT(*) FROM whatsapp_order_drafts WHERE client_id=?", (client["id"],)
        ).fetchone()[0] == 0
    finally:
        conn.close()


def test_event_id_and_message_id_are_independently_idempotent(isolated_app, monkeypatch):
    _configure_inbound(monkeypatch)
    token = _login(isolated_app)
    _create_client(isolated_app, token)
    first = isolated_app.client.post("/internal/whatsapp/events", headers=_internal_headers(), json=_event())
    same_message = isolated_app.client.post(
        "/internal/whatsapp/events", headers=_internal_headers(), json=_event(event_id="event-002")
    )
    same_event = isolated_app.client.post(
        "/internal/whatsapp/events", headers=_internal_headers(), json=_event(message_id="message-002")
    )
    assert first.json()["duplicate"] is False
    assert same_message.json()["duplicate"] is True
    assert same_event.json()["duplicate"] is True
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_inbound_events").fetchone()[0] == 1
        assert conn.execute("SELECT duplicate_count FROM whatsapp_inbound_events").fetchone()[0] == 2
    finally:
        conn.close()


@pytest.mark.parametrize(
    ("changes", "reason"),
    [
        ({"remote_jid": "120363000000@g.us"}, "grupo_bloqueado"),
        ({"from_me": True}, "mensagem_do_proprio_numero"),
        ({"message_type": "protocolMessage", "text": ""}, "mensagem_de_sistema"),
        ({"remote_jid": "123@s.whatsapp.net"}, "pais_nao_suportado"),
        ({"remote_jid": "invalid"}, "jid_nao_individual"),
    ],
)
def test_blocked_inbound_events_are_audited(isolated_app, monkeypatch, changes, reason):
    _configure_inbound(monkeypatch)
    response = isolated_app.client.post("/internal/whatsapp/events", headers=_internal_headers(), json=_event(**changes))
    assert response.status_code == 202
    assert response.json()["status"] == "bloqueado"
    assert response.json()["error_code"] == reason


def test_unknown_and_other_company_client_are_audited_without_exposure(isolated_app, monkeypatch):
    _configure_inbound(monkeypatch, company="raios")
    token = _login(isolated_app)
    _create_client(isolated_app, token, company="estrada", name="Somente Estrada")
    response = isolated_app.client.post("/internal/whatsapp/events", headers=_internal_headers(), json=_event())
    assert response.status_code == 202
    assert response.json()["status"] == "nao_identificado"
    events = isolated_app.client.get("/api/whatsapp/inbound-events", headers=_headers(token, "raios")).json()
    foreign = isolated_app.client.get("/api/whatsapp/inbound-events", headers=_headers(token, "estrada")).json()
    assert events[0]["client_name"] is None
    assert foreign == []


@pytest.mark.parametrize("command", ["SAIR", "STOP", "PARAR", "CANCELAR"])
def test_opt_out_from_internal_event_records_command_and_blocks_consent(isolated_app, monkeypatch, command):
    _configure_inbound(monkeypatch)
    _configure_order_bot(isolated_app, monkeypatch)
    token = _login(isolated_app)
    client = _create_client(isolated_app, token)
    sent = []
    isolated_app.module.wa_send = lambda *args: sent.append(args) or {"ok": True, "response": "mock"}
    initial = isolated_app.client.post(
        "/internal/whatsapp/events", headers=_internal_headers(),
        json=_event(event_id="before-optout", message_id="before-optout", text="Oi"),
    )
    assert initial.status_code == 200
    assert len(sent) == 1
    response = isolated_app.client.post(
        "/internal/whatsapp/events", headers=_internal_headers(),
        json=_event(event_id="optout-event", message_id="optout-message", text=command),
    )
    assert response.status_code == 200
    assert "bot" not in response.json()
    assert len(sent) == 1
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        event = conn.execute(
            "SELECT command,new_state FROM whatsapp_inbound_events WHERE event_id='optout-event'"
        ).fetchone()
        consent = conn.execute("SELECT status FROM whatsapp_consent WHERE client_id=?", (client["id"],)).fetchone()
        assert event == (command, "opt_out")
        assert consent[0] == "opt_out"
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_messages WHERE direction='enviada'").fetchone()[0] == 1
    finally:
        conn.close()
    print("OPT_OUT_OK")


def test_inbound_database_failure_rolls_back_all_and_later_write_works(isolated_app, monkeypatch):
    _configure_inbound(monkeypatch)
    token = _login(isolated_app)
    _create_client(isolated_app, token)
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    conn.execute("CREATE TRIGGER fail_inbound_message BEFORE INSERT ON whatsapp_messages BEGIN SELECT RAISE(ABORT,'inbound failure'); END")
    conn.commit(); conn.close()
    with pytest.raises(sqlite3.IntegrityError, match="inbound failure"):
        isolated_app.client.post("/internal/whatsapp/events", headers=_internal_headers(), json=_event())
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_inbound_events").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_conversations").fetchone()[0] == 0
        conn.execute("DROP TRIGGER fail_inbound_message"); conn.commit()
    finally:
        conn.close()
    after = isolated_app.client.post("/internal/whatsapp/events", headers=_internal_headers(), json=_event(event_id="after", message_id="after"))
    assert after.status_code == 200


def test_concurrent_duplicate_inbound_creates_one_record(isolated_app, monkeypatch):
    _configure_inbound(monkeypatch)
    token = _login(isolated_app)
    _create_client(isolated_app, token)
    barrier = threading.Barrier(2)
    def submit():
        barrier.wait()
        return isolated_app.client.post("/internal/whatsapp/events", headers=_internal_headers(), json=_event()).status_code
    with ThreadPoolExecutor(max_workers=2) as pool:
        statuses = list(pool.map(lambda _: submit(), range(2)))
    assert statuses == [200, 200]
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_inbound_events").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_messages").fetchone()[0] == 1
    finally:
        conn.close()


def test_suggestion_boundary_phone_consent_optout_and_open_work(isolated_app):
    conn = isolated_app.module.get_db("raios")
    try:
        conn.execute("INSERT INTO clients(id,name,phone,active) VALUES('c7','Sete','95991234567',1),('c8','Oito','95991234568',1),('bad','Sem telefone','',1)")
        for client_id, phone in (("c7", "+5595991234567"), ("c8", "+5595991234568"), ("bad", "")):
            conn.execute("INSERT INTO whatsapp_consent(id,company_key,client_id,phone_e164,status) VALUES(?,?,?,?,?)", ("co-" + client_id, "raios", client_id, phone, "opt_in"))
        conn.execute("INSERT INTO sales(id,sale_type,sale_date,client) VALUES('s7','AVULSO','2026-09-07','Sete'),('s8','AVULSO','2026-09-06','Oito')")
        conn.commit()
        rows = {row["client_id"]: row for row in list_suggestions(conn, "raios", {"minimum_days": 0, "include_blocked": True}, date(2026, 9, 14))}
        assert rows["c7"]["selectable"] is False
        assert rows["c8"]["selectable"] is True
        assert rows["bad"]["selectable"] is False
        conn.execute("UPDATE whatsapp_consent SET status='opt_out' WHERE client_id='c8'"); conn.commit()
        changed = {row["client_id"]: row for row in list_suggestions(conn, "raios", {"minimum_days": 0, "include_blocked": True}, date(2026, 9, 14))}
        assert changed["c8"]["selectable"] is False and "opt_out" in changed["c8"]["block_reasons"]
    finally:
        conn.close()


def test_recent_message_blocks_suggestion(isolated_app):
    token = _login(isolated_app)
    client = _create_client(isolated_app, token)
    _make_eligible(isolated_app, client)
    conn = isolated_app.module.get_db("raios")
    try:
        batch = create_manual_batch(
            conn, "raios", "admin", [client["id"]], "Mensagem recente",
            now=datetime(2026, 9, 14, 12, tzinfo=timezone.utc), request_id="recent-message-batch",
        )
        conn.execute(
            "UPDATE whatsapp_manual_batch_items SET status='enviado',sent_at='2026-09-13T12:00:00+00:00' WHERE batch_id=?",
            (batch["id"],),
        )
        conn.commit()
        row = next(item for item in list_suggestions(
            conn, "raios", {"minimum_days": 0, "include_blocked": True}, date(2026, 9, 14)
        ) if item["client_id"] == client["id"])
        assert row["selectable"] is False
        assert "mensagem_recente" in row["block_reasons"]
    finally:
        conn.close()


def test_pending_order_blocks_suggestion(isolated_app):
    token = _login(isolated_app)
    client = _create_client(isolated_app, token)
    _make_eligible(isolated_app, client)
    conn = isolated_app.module.get_db("raios")
    try:
        conn.execute(
            "INSERT INTO whatsapp_conversations(id,company_key,client_id,jid,status) VALUES('conv-pending','raios',?,'5595991234567@s.whatsapp.net','concluida')",
            (client["id"],),
        )
        conn.execute(
            """INSERT INTO whatsapp_messages(
                   id,company_key,instance_key,conversation_id,client_id,direction,external_message_id,
                   idempotency_key,event_hash,jid,body,status)
               VALUES('msg-pending','raios','test','conv-pending',?,'recebida','external-pending',
                      'idem-pending','hash-pending','5595991234567@s.whatsapp.net','Oi','processada')""",
            (client["id"],),
        )
        conn.execute(
            """INSERT INTO whatsapp_order_drafts(
                   id,company_key,client_id,conversation_id,source_message_id,idempotency_key,status)
               VALUES('order-pending','raios',?,'conv-pending','msg-pending','order-idem-pending','aguardando_aprovacao')""",
            (client["id"],),
        )
        conn.commit()
        row = next(item for item in list_suggestions(
            conn, "raios", {"minimum_days": 0, "include_blocked": True}, date(2026, 9, 14)
        ) if item["client_id"] == client["id"])
        assert row["pending_order"] is True
        assert row["selectable"] is False
        assert "pedido_pendente" in row["block_reasons"]
    finally:
        conn.close()


def test_manual_batch_requires_selection_confirmation_and_stays_disabled(isolated_app, monkeypatch):
    token = _login(isolated_app)
    client = _create_client(isolated_app, token)
    _make_eligible(isolated_app, client)
    empty = isolated_app.client.post("/api/whatsapp/manual-batches", headers=_headers(token), json={"client_ids": [], "message": "Oi"})
    assert empty.status_code == 422
    created = isolated_app.client.post("/api/whatsapp/manual-batches", headers=_headers(token), json={"client_ids": [client["id"]], "message": "Oi, {cliente}."})
    assert created.status_code == 200
    batch = created.json()
    assert batch["status"] == "rascunho" and batch["items"][0]["message_final"] == "Oi, Cliente Inbound."
    before_confirm = isolated_app.client.post(f"/api/whatsapp/manual-batches/{batch['id']}/send", headers=_headers(token))
    assert before_confirm.status_code == 400
    confirmed = isolated_app.client.post(f"/api/whatsapp/manual-batches/{batch['id']}/confirm", headers=_headers(token))
    assert confirmed.status_code == 200
    disabled = isolated_app.client.post(f"/api/whatsapp/manual-batches/{batch['id']}/send", headers=_headers(token))
    assert disabled.status_code == 403 and disabled.json()["detail"] == "envio_desativado"
    assert isolated_app.external_calls == []


def test_manual_batch_request_is_idempotent_and_reuse_is_safe(isolated_app):
    token = _login(isolated_app)
    first = _create_client(isolated_app, token, name="Primeiro", phone="95991234567")
    second = _create_client(isolated_app, token, name="Segundo", phone="95991234568")
    _make_eligible(isolated_app, first)
    _make_eligible(isolated_app, second)
    body = {
        "client_ids": [first["id"], second["id"]], "message": "Oi, {cliente}.",
        "filters": {"minimum_days": 8}, "request_id": "manual-request-001",
    }
    created = isolated_app.client.post("/api/whatsapp/manual-batches", headers=_headers(token), json=body)
    duplicate = isolated_app.client.post("/api/whatsapp/manual-batches", headers=_headers(token), json=body)
    assert created.status_code == duplicate.status_code == 200
    assert created.json()["id"] == duplicate.json()["id"]
    assert len(created.json()["items"]) == 2
    confirmed = isolated_app.client.post(
        f"/api/whatsapp/manual-batches/{created.json()['id']}/confirm", headers=_headers(token)
    )
    assert confirmed.status_code == 200
    reused_confirmation = isolated_app.client.post(
        f"/api/whatsapp/manual-batches/{created.json()['id']}/confirm", headers=_headers(token)
    )
    assert reused_confirmation.status_code == 400
    conflicting = isolated_app.client.post(
        "/api/whatsapp/manual-batches", headers=_headers(token),
        json={**body, "client_ids": [first["id"]]},
    )
    assert conflicting.status_code == 400
    assert conflicting.json()["detail"] == "chave_idempotencia_reutilizada"
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_manual_batches").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_manual_batch_items").fetchone()[0] == 2
    finally:
        conn.close()


def test_manual_batch_cancel_and_expiration_are_explicit(isolated_app):
    token = _login(isolated_app)
    client = _create_client(isolated_app, token)
    _make_eligible(isolated_app, client)
    created = isolated_app.client.post("/api/whatsapp/manual-batches", headers=_headers(token), json={"client_ids": [client["id"]], "message": "Oi"}).json()
    cancelled = isolated_app.client.post(f"/api/whatsapp/manual-batches/{created['id']}/cancel", headers=_headers(token))
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelado"
    assert cancelled.json()["items"][0]["status"] == "cancelado"

    conn = isolated_app.module.get_db("raios")
    try:
        now = datetime(2026, 9, 14, 12, tzinfo=timezone.utc)
        expired = create_manual_batch(conn, "raios", "admin", [client["id"]], "Nova", now=now)
        with pytest.raises(ValueError, match="selecao_expirada"):
            confirm_manual_batch(conn, "raios", expired["id"], "admin", now=now + timedelta(minutes=16))
        assert conn.execute("SELECT status FROM whatsapp_manual_batches WHERE id=?", (expired["id"],)).fetchone()[0] == "expirado"
    finally:
        conn.close()


def test_batch_creation_rolls_back_if_one_selected_item_fails(isolated_app):
    token = _login(isolated_app)
    first = _create_client(isolated_app, token, name="Primeiro", phone="95991234567")
    second = _create_client(isolated_app, token, name="Segundo", phone="95991234568")
    _make_eligible(isolated_app, first)
    _make_eligible(isolated_app, second)
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    conn.execute(f"""CREATE TRIGGER fail_second_batch_item BEFORE INSERT ON whatsapp_manual_batch_items
        WHEN NEW.client_id='{second['id']}' BEGIN SELECT RAISE(ABORT,'batch item failure'); END""")
    conn.commit(); conn.close()
    with pytest.raises(sqlite3.IntegrityError, match="batch item failure"):
        isolated_app.client.post("/api/whatsapp/manual-batches", headers=_headers(token), json={"client_ids": [first["id"], second["id"]], "message": "Oi"})
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_manual_batches").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_manual_batch_items").fetchone()[0] == 0
    finally:
        conn.close()


def test_manual_send_sandbox_is_individual_no_retry_and_no_business_writes(isolated_app, monkeypatch):
    token = _login(isolated_app)
    client = _create_client(isolated_app, token)
    _make_eligible(isolated_app, client)
    calls = []
    isolated_app.module.wa_send = lambda phone, message, config: calls.append((phone, message, config["provider"])) or {"ok": False, "response": "mock failure"}
    monkeypatch.setenv("WHATSAPP_OUTBOUND_ENABLED", "true")
    monkeypatch.setenv("WHATSAPP_OUTBOUND_MODE", "sandbox")
    monkeypatch.setenv("WHATSAPP_OUTBOUND_SANDBOX_NUMBERS", "+5595991234567")
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    conn.execute("INSERT OR REPLACE INTO whatsapp_config(key,value) VALUES('provider','baileys')"); conn.commit(); conn.close()
    created = isolated_app.client.post("/api/whatsapp/manual-batches", headers=_headers(token), json={"client_ids": [client["id"]], "message": "Oi, {cliente}."}).json()
    isolated_app.client.post(f"/api/whatsapp/manual-batches/{created['id']}/confirm", headers=_headers(token))
    sent = isolated_app.client.post(f"/api/whatsapp/manual-batches/{created['id']}/send", headers=_headers(token))
    assert sent.status_code == 200 and sent.json()["results"][0]["status"] == "falhou"
    assert len(calls) == 1
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_order_drafts").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0] == 1
    finally:
        conn.close()


def test_manual_batch_records_individual_results_for_multiple_clients(isolated_app, monkeypatch):
    token = _login(isolated_app)
    first = _create_client(isolated_app, token, name="Primeiro", phone="95991234567")
    second = _create_client(isolated_app, token, name="Segundo", phone="95991234568")
    _make_eligible(isolated_app, first)
    _make_eligible(isolated_app, second)
    calls = []

    def sender(phone, message, config):
        calls.append(phone)
        return {"ok": phone.endswith("567"), "response": "mock"}

    isolated_app.module.wa_send = sender
    monkeypatch.setenv("WHATSAPP_OUTBOUND_ENABLED", "true")
    monkeypatch.setenv("WHATSAPP_OUTBOUND_MODE", "sandbox")
    monkeypatch.setenv("WHATSAPP_OUTBOUND_SANDBOX_NUMBERS", "+5595991234567,+5595991234568")
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    conn.execute("INSERT OR REPLACE INTO whatsapp_config(key,value) VALUES('provider','baileys')")
    conn.commit()
    conn.close()
    created = isolated_app.client.post(
        "/api/whatsapp/manual-batches", headers=_headers(token),
        json={
            "client_ids": [first["id"], second["id"]], "message": "Oi, {cliente}.",
            "request_id": "individual-results-001",
        },
    ).json()
    isolated_app.client.post(f"/api/whatsapp/manual-batches/{created['id']}/confirm", headers=_headers(token))
    result = isolated_app.client.post(f"/api/whatsapp/manual-batches/{created['id']}/send", headers=_headers(token))
    assert result.status_code == 200
    assert sorted(item["status"] for item in result.json()["results"]) == ["enviado", "falhou"]
    assert len(calls) == 2
    stored = {item["client_id"]: item for item in result.json()["batch"]["items"]}
    assert stored[first["id"]]["status"] == "enviado"
    assert stored[second["id"]]["status"] == "falhou"


@pytest.mark.parametrize("change,expected_reason", [
    ("optout", "bloqueado_por_revalidacao"),
    ("phone", "dados_alterados_apos_selecao"),
    ("purchase", "bloqueado_por_revalidacao"),
])
def test_revalidation_blocks_optout_phone_or_purchase_change_without_send(isolated_app, monkeypatch, change, expected_reason):
    token = _login(isolated_app)
    client = _create_client(isolated_app, token)
    _make_eligible(isolated_app, client)
    calls = []
    isolated_app.module.wa_send = lambda *args: calls.append(args) or {"ok": True, "response": "mock"}
    monkeypatch.setenv("WHATSAPP_OUTBOUND_ENABLED", "true")
    monkeypatch.setenv("WHATSAPP_OUTBOUND_MODE", "sandbox")
    monkeypatch.setenv("WHATSAPP_OUTBOUND_SANDBOX_NUMBERS", "+5595991234567")
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    conn.execute("INSERT OR REPLACE INTO whatsapp_config(key,value) VALUES('provider','baileys')"); conn.commit(); conn.close()
    created = isolated_app.client.post("/api/whatsapp/manual-batches", headers=_headers(token), json={"client_ids": [client["id"]], "message": "Oi"}).json()
    isolated_app.client.post(f"/api/whatsapp/manual-batches/{created['id']}/confirm", headers=_headers(token))
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    if change == "optout":
        conn.execute("UPDATE whatsapp_consent SET status='opt_out' WHERE client_id=?", (client["id"],))
    elif change == "phone":
        conn.execute("UPDATE clients SET phone='95991230000' WHERE id=?", (client["id"],))
    else:
        recent_sale_date = (datetime.now(timezone.utc).date() - timedelta(days=1)).isoformat()
        conn.execute(
            "INSERT INTO sales(id,sale_type,sale_date,client,quantity,unit_price,total) VALUES('recent-sale','AVULSO',?,?,1,1,1)",
            (recent_sale_date, client["name"]),
        )
    conn.commit(); conn.close()
    result = isolated_app.client.post(f"/api/whatsapp/manual-batches/{created['id']}/send", headers=_headers(token))
    assert result.status_code == 200
    assert result.json()["results"][0]["reason"] == expected_reason
    assert calls == []


def test_sandbox_allowlist_and_recent_duplicate_block_without_retry(isolated_app, monkeypatch):
    token = _login(isolated_app)
    client = _create_client(isolated_app, token)
    _make_eligible(isolated_app, client)
    calls = []
    isolated_app.module.wa_send = lambda *args: calls.append(args) or {"ok": True, "response": "mock sent"}
    monkeypatch.setenv("WHATSAPP_OUTBOUND_ENABLED", "true")
    monkeypatch.setenv("WHATSAPP_OUTBOUND_MODE", "sandbox")
    monkeypatch.setenv("WHATSAPP_OUTBOUND_SANDBOX_NUMBERS", "+5595990000000")
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    conn.execute("INSERT OR REPLACE INTO whatsapp_config(key,value) VALUES('provider','baileys')"); conn.commit(); conn.close()
    outside = isolated_app.client.post("/api/whatsapp/manual-batches", headers=_headers(token), json={"client_ids": [client["id"]], "message": "Mensagem A"}).json()
    isolated_app.client.post(f"/api/whatsapp/manual-batches/{outside['id']}/confirm", headers=_headers(token))
    blocked = isolated_app.client.post(f"/api/whatsapp/manual-batches/{outside['id']}/send", headers=_headers(token)).json()
    assert blocked["results"][0]["reason"] == "numero_fora_da_sandbox" and calls == []

    monkeypatch.setenv("WHATSAPP_OUTBOUND_SANDBOX_NUMBERS", "+5595991234567")
    first = isolated_app.client.post("/api/whatsapp/manual-batches", headers=_headers(token), json={"client_ids": [client["id"]], "message": "Mensagem repetida"}).json()
    isolated_app.client.post(f"/api/whatsapp/manual-batches/{first['id']}/confirm", headers=_headers(token))
    assert isolated_app.client.post(f"/api/whatsapp/manual-batches/{first['id']}/send", headers=_headers(token)).json()["results"][0]["status"] == "enviado"
    repeated = isolated_app.client.post(
        "/api/whatsapp/manual-batches", headers=_headers(token),
        json={"client_ids": [client["id"]], "message": "Mensagem repetida"},
    )
    assert repeated.status_code == 400
    assert repeated.json()["detail"] == "cliente_bloqueado_na_selecao"
    assert len(calls) == 1


def test_other_company_selection_and_open_work_are_blocked(isolated_app):
    token = _login(isolated_app)
    raios = _create_client(isolated_app, token, name="Raios")
    estrada = _create_client(isolated_app, token, name="Estrada", company="estrada")
    _make_eligible(isolated_app, raios)
    _make_eligible(isolated_app, estrada, company="estrada")
    foreign = isolated_app.client.post("/api/whatsapp/manual-batches", headers=_headers(token, "raios"), json={"client_ids": [estrada["id"]], "message": "Oi"})
    assert foreign.status_code == 404
    incoming = isolated_app.client.post("/api/whatsapp/webhooks/incoming", headers=_headers(token), json={"instance_key": "local", "external_message_id": "open-msg", "jid": "5595991234567@s.whatsapp.net", "received_at": "2026-09-14T12:00:00-04:00", "text": "Oi", "event_hash": "open-event"})
    assert incoming.status_code == 200
    rows = isolated_app.client.get("/api/whatsapp/suggestions?minimum_days=0&include_blocked=true", headers=_headers(token)).json()
    item = next(row for row in rows if row["client_id"] == raios["id"])
    assert item["open_conversation"] is True and item["selectable"] is False


def test_new_sensitive_permissions_are_not_granted_to_legacy_editor(isolated_app):
    admin = _login(isolated_app)
    created = isolated_app.client.post("/api/users", headers=_headers(admin), json={"username": "campaign_editor", "password": "Campanha987!", "full_name": "Editor", "role": "editor"})
    assert created.status_code == 200
    editor = _login(isolated_app, "campaign_editor", "Campanha987!")
    denied = isolated_app.client.get("/api/whatsapp/suggestions", headers=_headers(editor))
    assert denied.status_code == 403


def test_whatsapp_permissions_are_separate_company_scoped_and_admin_is_protected(isolated_app):
    admin = _login(isolated_app)
    admin_headers = _headers(admin)
    base_role = {
        "key": "wa_limited", "name": "WhatsApp limitado", "active": True,
        "areas": {"menina_dos_raios": True},
        "modules": {"menina_dos_raios": {"clientes_whatsapp": {"view": True}}},
        "products": [],
    }
    role = isolated_app.client.post("/api/admin/roles", headers=admin_headers, json=base_role)
    assert role.status_code == 200, role.text
    user = isolated_app.client.post(
        "/api/users", headers=admin_headers,
        json={"username": "wa_limited_user", "password": "WhatsApp987!", "full_name": "WhatsApp", "role": "wa_limited"},
    )
    assert user.status_code == 200, user.text
    limited = _login(isolated_app, "wa_limited_user", "WhatsApp987!")
    limited_headers = _headers(limited)
    assert isolated_app.client.get("/api/whatsapp/status", headers=limited_headers).status_code == 200
    assert isolated_app.client.get("/api/whatsapp/suggestions", headers=limited_headers).status_code == 403
    assert isolated_app.client.post(
        "/api/whatsapp/manual-batches", headers=limited_headers,
        json={"client_ids": ["missing"], "message": "Oi", "request_id": "permission-denied"},
    ).status_code == 403
    assert isolated_app.client.post(
        "/api/whatsapp/manual-batches/missing/send", headers=limited_headers
    ).status_code == 403
    assert isolated_app.client.get(
        "/api/whatsapp/status", headers=_headers(limited, "estrada")
    ).status_code == 403

    granted_role = {
        **base_role,
        "modules": {"menina_dos_raios": {
            "clientes_whatsapp": {"view": True},
            "clientes_whatsapp_sugestoes": {"view": True},
            "clientes_whatsapp_lotes": {"view": True, "create": True, "edit": True, "approve": True},
            "clientes_whatsapp_envio": {"view": True, "create": True},
        }},
    }
    updated = isolated_app.client.put("/api/admin/roles/wa_limited", headers=admin_headers, json=granted_role)
    assert updated.status_code == 200, updated.text
    capabilities = isolated_app.client.get("/api/whatsapp/status", headers=limited_headers).json()["capabilities"]
    assert capabilities == {"view_suggestions": True, "create_manual_batch": True, "send_manual": True}
    assert isolated_app.client.get("/api/whatsapp/suggestions", headers=limited_headers).status_code == 200

    protected = isolated_app.client.put(
        "/api/admin/roles/admin", headers=admin_headers,
        json={"name": "Administrador", "active": False, "areas": {}, "modules": {}, "products": []},
    )
    assert protected.status_code == 400
