import sqlite3
import uuid
import importlib
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
UP = ROOT / "backend" / "migrations" / "20260914_whatsapp_orders_up.sql"
DOWN = ROOT / "backend" / "migrations" / "20260914_whatsapp_orders_down.sql"


def _login(client, username="admin", password="admin123", company="raios"):
    response = client.post("/api/auth/login", headers={"x-company": company}, json={"username": username, "password": password})
    assert response.status_code == 200, response.text
    return response.json()["token"]


def _headers(token, company="raios"):
    return {"x-token": token, "x-company": company}


def _create_client(app, token, company="raios", name="Cliente WhatsApp", phone="95991234567"):
    response = app.client.post(
        "/api/clients",
        headers=_headers(token, company),
        json={"name": name, "phone": phone},
    )
    assert response.status_code == 200, response.text
    return response.json()


def _incoming(client_id=None, **overrides):
    body = {
        "instance_key": "simulacao-local",
        "external_message_id": "msg-001",
        "jid": "5595991234567@s.whatsapp.net",
        "received_at": "2026-09-14T22:00:00-04:00",
        "text": "Quero fazer um pedido",
        "event_hash": "event-001",
    }
    body.update(overrides)
    return body


def _seed_order(app, token, client, status="aguardando_aprovacao", order_id=None, message_id="msg-order"):
    incoming = app.client.post(
        "/api/whatsapp/webhooks/incoming",
        headers=_headers(token),
        json=_incoming(client["id"], external_message_id=message_id, event_hash=f"event-{message_id}"),
    ).json()
    oid = order_id or str(uuid.uuid4())
    conn = sqlite3.connect(app.db_paths["raios"])
    try:
        conn.execute(
            """INSERT INTO whatsapp_order_drafts(
                   id,company_key,client_id,conversation_id,source_message_id,idempotency_key,status,total)
               VALUES(?,?,?,?,?,?,?,?)""",
            (oid, "raios", client["id"], incoming["conversation_id"], incoming["message_id"], f"order-key-{oid}", status, "20"),
        )
        conn.execute(
            """INSERT INTO whatsapp_order_items(
                   id,order_id,product_key,requested_quantity,confirmed_quantity,unit_price,total,confirmed_damage)
               VALUES(?,?,?,?,?,?,?,'0')""",
            (str(uuid.uuid4()), oid, "MAC_PCT", "10", "10", "2", "20"),
        )
        if status:
            conn.execute(
                "UPDATE whatsapp_conversations SET status=? WHERE id=?",
                ("aguardando_aprovacao" if status == "aguardando_aprovacao" else "pedido_rascunho", incoming["conversation_id"]),
            )
        conn.commit()
    finally:
        conn.close()
    return oid, incoming


def test_migration_and_rollback_on_memory_database():
    conn = sqlite3.connect(":memory:")
    conn.execute("PRAGMA foreign_keys=ON")
    conn.executescript(
        """CREATE TABLE clients(id TEXT PRIMARY KEY, active INTEGER NOT NULL DEFAULT 1);
           CREATE TABLE product_prices(key TEXT PRIMARY KEY, active INTEGER NOT NULL DEFAULT 1);
           CREATE TABLE whatsapp_contacts(id TEXT PRIMARY KEY);"""
    )
    conn.executescript(UP.read_text(encoding="utf-8"))
    expected = {
        "whatsapp_consent", "whatsapp_conversations", "whatsapp_messages", "whatsapp_events",
        "whatsapp_order_drafts", "whatsapp_order_items", "whatsapp_order_history",
        "customer_product_consumption", "customer_product_damage",
    }
    tables = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert expected <= tables
    conn.executescript(DOWN.read_text(encoding="utf-8"))
    remaining = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert not expected & remaining
    assert {"clients", "product_prices", "whatsapp_contacts"} <= remaining
    conn.close()


def test_status_requires_auth_and_has_no_active_capabilities(isolated_app):
    denied = isolated_app.client.get("/api/whatsapp/status")
    assert denied.status_code == 401
    token = _login(isolated_app.client)
    response = isolated_app.client.get("/api/whatsapp/status", headers=_headers(token))
    assert response.status_code == 200
    data = response.json()
    assert data["mode"] == "inbound_disabled"
    assert data["inbound_enabled"] is False
    assert data["outbound_enabled"] is False
    assert data["outbound_mode"] == "disabled"
    assert data["sending_enabled"] is False
    assert data["conversion_enabled"] is False
    assert data["counts"] == {"conversations": 0, "messages": 0, "orders": 0, "inbound_events": 0, "inbound_attention": 0}
    assert isolated_app.external_calls == []


def test_incoming_message_is_recorded_once_and_does_not_create_order_or_sale(isolated_app):
    token = _login(isolated_app.client)
    client = _create_client(isolated_app, token)
    first = isolated_app.client.post("/api/whatsapp/webhooks/incoming", headers=_headers(token), json=_incoming(client["id"]))
    repeated = isolated_app.client.post("/api/whatsapp/webhooks/incoming", headers=_headers(token), json=_incoming(client["id"]))
    assert first.status_code == 200, first.text
    assert first.json()["duplicate"] is False
    assert repeated.status_code == 200
    assert repeated.json()["duplicate"] is True

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_messages").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_events").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_conversations").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_order_drafts").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0] == 0
    finally:
        conn.close()
    assert isolated_app.external_calls == []


def test_incoming_invalid_phone_unknown_client_and_company_isolation(isolated_app):
    token = _login(isolated_app.client)
    raios_client = _create_client(isolated_app, token, company="raios", name="Somente Raios")
    invalid = isolated_app.client.post(
        "/api/whatsapp/webhooks/incoming", headers=_headers(token), json=_incoming(jid="123@s.whatsapp.net")
    )
    unknown = isolated_app.client.post(
        "/api/whatsapp/webhooks/incoming", headers=_headers(token), json=_incoming(jid="5595988887777@s.whatsapp.net")
    )
    foreign_client = isolated_app.client.get(
        f"/api/clients/{raios_client['id']}/whatsapp", headers=_headers(token, "estrada")
    )
    assert invalid.status_code == 400
    assert unknown.status_code == 404
    assert foreign_client.status_code == 404


def test_incoming_rejects_group_and_ambiguous_duplicate_phone(isolated_app):
    token = _login(isolated_app.client)
    _create_client(isolated_app, token, name="Telefone A")
    _create_client(isolated_app, token, name="Telefone B")
    duplicate = isolated_app.client.post(
        "/api/whatsapp/webhooks/incoming", headers=_headers(token), json=_incoming()
    )
    group = isolated_app.client.post(
        "/api/whatsapp/webhooks/incoming",
        headers=_headers(token),
        json=_incoming(jid="5595991234567@g.us"),
    )
    assert duplicate.status_code == 404
    assert group.status_code == 400


def test_same_external_message_id_is_isolated_by_company(isolated_app):
    token = _login(isolated_app.client)
    _create_client(isolated_app, token, company="raios", name="Cliente Raios")
    _create_client(isolated_app, token, company="estrada", name="Cliente Estrada")
    raios = isolated_app.client.post("/api/whatsapp/webhooks/incoming", headers=_headers(token, "raios"), json=_incoming())
    estrada = isolated_app.client.post("/api/whatsapp/webhooks/incoming", headers=_headers(token, "estrada"), json=_incoming())
    assert raios.status_code == 200
    assert estrada.status_code == 200
    assert raios.json()["duplicate"] is False
    assert estrada.json()["duplicate"] is False


def test_incoming_failure_rolls_back_partial_conversation_and_allows_later_write(isolated_app):
    token = _login(isolated_app.client)
    _create_client(isolated_app, token)
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    conn.execute("CREATE TRIGGER fail_wa_event BEFORE INSERT ON whatsapp_events BEGIN SELECT RAISE(ABORT,'controlled event failure'); END")
    conn.commit()
    conn.close()
    with pytest.raises(sqlite3.IntegrityError, match="controlled event failure"):
        isolated_app.client.post("/api/whatsapp/webhooks/incoming", headers=_headers(token), json=_incoming())
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_conversations").fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM whatsapp_messages").fetchone()[0] == 0
        conn.execute("DROP TRIGGER fail_wa_event")
        conn.commit()
    finally:
        conn.close()
    after = isolated_app.client.post(
        "/api/whatsapp/webhooks/incoming",
        headers=_headers(token),
        json=_incoming(external_message_id="msg-after", event_hash="event-after"),
    )
    assert after.status_code == 200


def test_opt_out_updates_conversation_and_consent(isolated_app):
    token = _login(isolated_app.client)
    client = _create_client(isolated_app, token)
    response = isolated_app.client.post(
        "/api/whatsapp/webhooks/incoming",
        headers=_headers(token),
        json=_incoming(client["id"], text="SAIR"),
    )
    assert response.status_code == 200
    assert response.json()["intent"] == "opt_out"
    summary = isolated_app.client.get(f"/api/clients/{client['id']}/whatsapp", headers=_headers(token))
    assert summary.json()["consent"]["status"] == "opt_out"
    assert summary.json()["conversation"]["status"] == "opt_out"


def test_consumption_validates_values_product_and_company(isolated_app):
    token = _login(isolated_app.client)
    client = _create_client(isolated_app, token)
    body = {"product_key": "MAC_UNIT", "average_consumption": "10.25", "maximum_consumption": "15.50", "unit": "UND"}
    saved = isolated_app.client.put(f"/api/clients/{client['id']}/consumption", headers=_headers(token), json=body)
    assert saved.status_code == 200, saved.text
    assert saved.json()["average_consumption"] == "10.25"
    listed = isolated_app.client.get(f"/api/clients/{client['id']}/consumption", headers=_headers(token))
    assert len(listed.json()) == 1
    too_low = isolated_app.client.put(
        f"/api/clients/{client['id']}/consumption",
        headers=_headers(token),
        json={**body, "maximum_consumption": "9"},
    )
    negative = isolated_app.client.put(
        f"/api/clients/{client['id']}/consumption",
        headers=_headers(token),
        json={**body, "average_consumption": "-1"},
    )
    foreign = isolated_app.client.get(f"/api/clients/{client['id']}/consumption", headers=_headers(token, "estrada"))
    assert too_low.status_code == 400
    assert negative.status_code == 400
    assert foreign.status_code == 404


def test_damage_is_created_as_reported_only(isolated_app):
    token = _login(isolated_app.client)
    client = _create_client(isolated_app, token)
    response = isolated_app.client.post(
        f"/api/clients/{client['id']}/damages",
        headers=_headers(token),
        json={"product_key": "MAC_UNIT", "quantity": "2.5", "replacement_percent": "50", "reason": "Transporte"},
    )
    assert response.status_code == 200, response.text
    assert response.json()["status"] == "informada"
    assert response.json()["responsible_user_id"] == "admin"
    listed = isolated_app.client.get(f"/api/clients/{client['id']}/damages", headers=_headers(token))
    assert [row["id"] for row in listed.json()] == [response.json()["id"]]
    invalid = isolated_app.client.post(
        f"/api/clients/{client['id']}/damages",
        headers=_headers(token),
        json={"product_key": "MAC_UNIT", "quantity": "1", "replacement_percent": "101"},
    )
    assert invalid.status_code == 400


def test_conversation_and_order_reads_are_company_scoped_with_history(isolated_app):
    token = _login(isolated_app.client)
    client = _create_client(isolated_app, token)
    incoming = isolated_app.client.post("/api/whatsapp/webhooks/incoming", headers=_headers(token), json=_incoming()).json()
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        order_id = str(uuid.uuid4())
        conn.execute(
            """INSERT INTO whatsapp_order_drafts(
                   id,company_key,client_id,conversation_id,source_message_id,idempotency_key,status,total)
               VALUES(?,?,?,?,?,?,?,?)""",
            (order_id, "raios", client["id"], incoming["conversation_id"], incoming["message_id"], "order-key-1", "duplicado_suspeito", "0"),
        )
        conn.execute(
            "INSERT INTO whatsapp_order_history(id,company_key,order_id,previous_status,new_status,changed_by,reason) VALUES(?,?,?,?,?,?,?)",
            (str(uuid.uuid4()), "raios", order_id, "rascunho", "duplicado_suspeito", "sistema", "pedido_recente_do_cliente"),
        )
        conn.commit()
    finally:
        conn.close()
    conversation = isolated_app.client.get(f"/api/whatsapp/conversations/{incoming['conversation_id']}", headers=_headers(token))
    order = isolated_app.client.get(f"/api/whatsapp/orders/{order_id}", headers=_headers(token))
    foreign_conversation = isolated_app.client.get(f"/api/whatsapp/conversations/{incoming['conversation_id']}", headers=_headers(token, "estrada"))
    foreign_order = isolated_app.client.get(f"/api/whatsapp/orders/{order_id}", headers=_headers(token, "estrada"))
    assert conversation.status_code == 200
    assert len(conversation.json()["messages"]) == 1
    assert order.status_code == 200
    assert order.json()["status"] == "duplicado_suspeito"
    assert order.json()["client_phone"] == client["phone"]
    assert order.json()["history"][0]["reason"] == "pedido_recente_do_cliente"
    assert foreign_conversation.status_code == 404
    assert foreign_order.status_code == 404

    listed = isolated_app.client.get("/api/whatsapp/orders", headers=_headers(token))
    assert listed.status_code == 200
    assert listed.json()[0]["client_id"] == client["id"]
    assert listed.json()[0]["client_phone"] == client["phone"]


def test_order_reads_handle_client_without_orders_and_missing_order(isolated_app):
    token = _login(isolated_app.client)
    _create_client(isolated_app, token, name="Cliente sem pedidos")
    listed = isolated_app.client.get("/api/whatsapp/orders", headers=_headers(token))
    missing = isolated_app.client.get("/api/whatsapp/orders/pedido-inexistente", headers=_headers(token))
    assert listed.status_code == 200
    assert listed.json() == []
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Pedido nao encontrado."


def test_order_actions_are_idempotent_and_do_not_create_sale_or_stock(isolated_app):
    token = _login(isolated_app.client)
    client = _create_client(isolated_app, token)
    order_id, _ = _seed_order(isolated_app, token, client)

    confirmed = isolated_app.client.post(f"/api/whatsapp/orders/{order_id}/confirm", headers=_headers(token))
    repeated = isolated_app.client.post(f"/api/whatsapp/orders/{order_id}/confirm", headers=_headers(token))
    rejected_after_confirm = isolated_app.client.post(
        f"/api/whatsapp/orders/{order_id}/reject",
        headers=_headers(token),
        json={"reason": "cliente desistiu"},
    )
    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["order"]["status"] == "aprovado"
    assert repeated.status_code == 200
    assert repeated.json()["changed"] is False
    assert rejected_after_confirm.status_code == 409

    reject_id, _ = _seed_order(isolated_app, token, client, order_id=str(uuid.uuid4()), message_id="msg-reject")
    invalid_reject = isolated_app.client.post(
        f"/api/whatsapp/orders/{reject_id}/reject",
        headers=_headers(token),
        json={"reason": " "},
    )
    rejected = isolated_app.client.post(
        f"/api/whatsapp/orders/{reject_id}/reject",
        headers=_headers(token),
        json={"reason": "produto indisponivel"},
    )
    repeated_reject = isolated_app.client.post(
        f"/api/whatsapp/orders/{reject_id}/reject",
        headers=_headers(token),
        json={"reason": "produto indisponivel"},
    )
    assert invalid_reject.status_code in (400, 422)
    assert rejected.status_code == 200
    assert rejected.json()["order"]["status"] == "cancelado"
    assert repeated_reject.status_code == 200
    assert repeated_reject.json()["changed"] is False

    new_order = isolated_app.client.post(
        "/api/whatsapp/orders/new-for-client",
        headers=_headers(token),
        json={"client_id": client["id"], "items": [{"product_key": "MAC_PCT", "quantity": "3", "damage": "0"}]},
    )
    assert new_order.status_code == 200, new_order.text
    assert new_order.json()["order"]["status"] == "rascunho"
    new_order_id = new_order.json()["order"]["id"]
    removed = isolated_app.client.delete(f"/api/whatsapp/orders/{new_order_id}", headers=_headers(token))
    removed_again = isolated_app.client.delete(f"/api/whatsapp/orders/{new_order_id}", headers=_headers(token))
    removed_fetch = isolated_app.client.get(f"/api/whatsapp/orders/{new_order_id}", headers=_headers(token))
    assert removed.status_code == 200, removed.text
    assert removed.json()["order"]["id"] == new_order_id
    assert removed_again.status_code == 404
    assert removed_fetch.status_code == 404

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        assert conn.execute(
            "SELECT COUNT(*) FROM whatsapp_order_history WHERE order_id=? AND new_status='aprovado'",
            (order_id,),
        ).fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM whatsapp_order_history WHERE order_id=? AND new_status='cancelado'",
            (reject_id,),
        ).fetchone()[0] == 1
        assert conn.execute(
            "SELECT COUNT(*) FROM whatsapp_order_drafts WHERE id=?",
            (new_order_id,),
        ).fetchone()[0] == 0
        assert conn.execute(
            "SELECT COUNT(*) FROM whatsapp_order_items WHERE order_id=?",
            (new_order_id,),
        ).fetchone()[0] == 0
        assert conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0] == 0
    finally:
        conn.close()
    assert isolated_app.external_calls == []


def test_order_actions_notify_customer_when_outbound_is_allowed(isolated_app, monkeypatch):
    monkeypatch.setenv("WHATSAPP_OUTBOUND_ENABLED", "true")
    monkeypatch.setenv("WHATSAPP_OUTBOUND_MODE", "sandbox")
    monkeypatch.setenv("WHATSAPP_OUTBOUND_SANDBOX_NUMBERS", "+5595991234567")
    sent = []
    isolated_app.module.wa_send = lambda phone, message, config: sent.append(
        {"phone": phone, "message": message, "provider": config.get("provider")}
    ) or {"ok": True, "response": "mock sent"}

    token = _login(isolated_app.client)
    client = _create_client(isolated_app, token, name="Cliente Teste", phone="95991234567")
    order_id, _ = _seed_order(isolated_app, token, client, order_id=str(uuid.uuid4()), message_id="msg-notify-ok")
    reject_id, _ = _seed_order(isolated_app, token, client, order_id=str(uuid.uuid4()), message_id="msg-notify-no")

    confirmed = isolated_app.client.post(f"/api/whatsapp/orders/{order_id}/confirm", headers=_headers(token))
    rejected = isolated_app.client.post(
        f"/api/whatsapp/orders/{reject_id}/reject",
        headers=_headers(token),
        json={"reason": "produto indisponivel"},
    )
    repeated = isolated_app.client.post(f"/api/whatsapp/orders/{order_id}/confirm", headers=_headers(token))

    assert confirmed.status_code == 200, confirmed.text
    assert confirmed.json()["notification"] == {"sent": True, "reason": "enviado"}
    assert rejected.status_code == 200, rejected.text
    assert rejected.json()["notification"] == {"sent": True, "reason": "enviado"}
    assert repeated.status_code == 200
    assert repeated.json()["notification"] == {"sent": False, "reason": "pedido_sem_alteracao"}
    assert len(sent) == 2
    assert sent[0]["phone"] == "5595991234567"
    assert "Seu pedido" in sent[0]["message"]
    assert "foi aprovado" in sent[0]["message"]
    assert "nao sera possivel atender" in sent[1]["message"]
    assert "produto indisponivel" in sent[1]["message"]

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        events = sorted(
            row[0]
            for row in conn.execute(
                "SELECT event_type FROM whatsapp_log"
            ).fetchall()
        )
        assert events == ["pedido_aprovado", "pedido_recusado"]
    finally:
        conn.close()


def test_whatsapp_pending_order_replies_and_novo_starts_independent_flow(isolated_app):
    token = _login(isolated_app.client)
    client = _create_client(isolated_app, token)
    order_id, incoming = _seed_order(isolated_app, token, client)
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    conn.row_factory = sqlite3.Row
    try:
        for key, value in {
            "provider": "baileys",
            "bot_active": "1",
            "auto_reply_enabled": "1",
            "auto_reply_from": "00:00",
            "auto_reply_to": "23:59",
            "test_mode": "0",
        }.items():
            conn.execute("INSERT OR REPLACE INTO whatsapp_config(key,value) VALUES(?,?)", (key, value))
        conn.commit()
        service = importlib.import_module("services.whatsapp_inbound_service")
        sent = []
        outbound = {
            "enabled": True,
            "mode": "sandbox",
            "sandbox_numbers": {"+5595991234567"},
            "production_approved": False,
        }

        def sender(phone, message, config):
            sent.append({"phone": phone, "message": message})
            return {"ok": True, "response": "mocked"}

        pending_payload = {
            "instance": "simulacao-local",
            "event_id": "evt-pending",
            "message_id": "msg-pending",
            "remote_jid": "5595991234567@s.whatsapp.net",
            "from_me": False,
            "message_type": "conversation",
            "text": "oi",
            "timestamp": "2026-09-14T22:10:00-04:00",
        }
        pending = service.process_inbound_event(conn, "raios", pending_payload, sender=sender, outbound=outbound)
        duplicate = service.process_inbound_event(conn, "raios", pending_payload, sender=sender, outbound=outbound)
        assert pending["bot"]["reason"] == "pedido_pendente_aprovacao"
        assert "NOVO" in sent[-1]["message"]
        assert duplicate["duplicate"] is True
        assert len(sent) == 1

        outside = service.process_inbound_event(
            conn,
            "raios",
            {**pending_payload, "event_id": "evt-outside", "message_id": "msg-outside", "text": "teste"},
            sender=sender,
            outbound={**outbound, "sandbox_numbers": set()},
        )
        assert outside["bot"]["reason"] == "numero_fora_da_sandbox"
        assert len(sent) == 1

        lid_payload = {
            **pending_payload,
            "event_id": "evt-lid",
            "message_id": "msg-lid",
            "remote_jid": "1234567890@lid",
            "text": "pedido",
        }
        lid = service.process_inbound_event(
            conn,
            "raios",
            lid_payload,
            sender=sender,
            outbound={**outbound, "sandbox_numbers": set()},
        )
        assert lid["status"] == "processado"
        assert lid["bot"]["state"] == "identificando_produto"
        assert sent[-1]["phone"] == "1234567890@lid"

        conversations_before = conn.execute("SELECT COUNT(*) FROM whatsapp_conversations").fetchone()[0]
        novo = service.process_inbound_event(
            conn,
            "raios",
            {**pending_payload, "event_id": "evt-novo", "message_id": "msg-novo", "text": "NOVO"},
            sender=sender,
            outbound=outbound,
        )
        conversations_after = conn.execute("SELECT COUNT(*) FROM whatsapp_conversations").fetchone()[0]
        assert novo["bot"]["state"] == "identificando_produto"
        assert conversations_after == conversations_before + 1
        assert conn.execute("SELECT status FROM whatsapp_order_drafts WHERE id=?", (order_id,)).fetchone()[0] == "aguardando_aprovacao"
    finally:
        conn.close()


def test_managed_role_is_denied_by_default(isolated_app):
    admin = _login(isolated_app.client)
    role = isolated_app.client.post(
        "/api/admin/roles",
        headers=_headers(admin),
        json={
            "key": "sem_whatsapp",
            "name": "Sem WhatsApp",
            "active": True,
            "product_scope_mode": "all",
            "areas": {"menina_dos_raios": True},
            "modules": {"menina_dos_raios": {"clientes": {"view": True}}},
            "products": [],
        },
    )
    assert role.status_code == 200, role.text
    created = isolated_app.client.post(
        "/api/users",
        headers=_headers(admin),
        json={"username": "sem_whatsapp", "password": "SenhaTeste123!", "full_name": "Sem WhatsApp", "role": "sem_whatsapp"},
    )
    assert created.status_code == 200
    token = _login(isolated_app.client, "sem_whatsapp", "SenhaTeste123!")
    denied = isolated_app.client.get("/api/whatsapp/status", headers=_headers(token))
    assert denied.status_code == 403


def test_database_rejects_repeated_message_and_order_keys(isolated_app):
    token = _login(isolated_app.client)
    _create_client(isolated_app, token)
    first = isolated_app.client.post("/api/whatsapp/webhooks/incoming", headers=_headers(token), json=_incoming()).json()
    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    try:
        original = conn.execute("SELECT * FROM whatsapp_messages WHERE id=?", (first["message_id"],)).fetchone()
        values = list(original)
        values[0] = str(uuid.uuid4())
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO whatsapp_messages VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
        conn.rollback()

        values[0] = str(uuid.uuid4())
        values[6] = "msg-002"
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("INSERT INTO whatsapp_messages VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", values)
        conn.rollback()

        client_id = original[4]
        conversation_id = original[3]
        order_values = (str(uuid.uuid4()), "raios", client_id, conversation_id, original[0], "order-key", "rascunho", "0")
        conn.execute(
            """INSERT INTO whatsapp_order_drafts(
                   id,company_key,client_id,conversation_id,source_message_id,idempotency_key,status,total)
               VALUES(?,?,?,?,?,?,?,?)""",
            order_values,
        )
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                """INSERT INTO whatsapp_order_drafts(
                       id,company_key,client_id,conversation_id,source_message_id,idempotency_key,status,total)
                   VALUES(?,?,?,?,?,?,?,?)""",
                (str(uuid.uuid4()), *order_values[1:]),
            )
    finally:
        conn.rollback()
        conn.close()
