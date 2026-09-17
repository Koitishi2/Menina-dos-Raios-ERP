import sqlite3
import uuid
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation

try:
    from ..domains.whatsapp_policies import conversation_control_intent, message_idempotency_key, normalize_brazil_phone
    from ..repositories.whatsapp_repository import active_clients
except ImportError:
    from domains.whatsapp_policies import conversation_control_intent, message_idempotency_key, normalize_brazil_phone
    from repositories.whatsapp_repository import active_clients


OPEN_CONVERSATION_STATES = (
    "nova", "aguardando_resposta", "identificando_produto", "coletando_quantidade",
    "coletando_avaria", "calculando_reposicao", "aguardando_confirmacao",
    "pedido_rascunho", "aguardando_aprovacao", "atendimento_humano",
)


def decimal_text(value, field, optional=False):
    if optional and value in (None, ""):
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field}_invalido") from exc
    if not number.is_finite() or number < 0:
        raise ValueError(f"{field}_invalido")
    return str(number)


def find_client_for_phone(conn, phone_value):
    target = normalize_brazil_phone(phone_value)
    if not target.valid:
        return None, target
    matches = []
    for row in active_clients(conn):
        current = normalize_brazil_phone(row["phone"])
        if current.valid and current.digits == target.digits:
            matches.append(row)
    return (matches[0] if len(matches) == 1 else None), target


def ensure_inbound_client(conn, phone_value):
    client, phone = find_client_for_phone(conn, phone_value)
    if client:
        return client, False
    if not phone.valid:
        raise ValueError(phone.reason)
    matches = []
    for row in active_clients(conn):
        current = normalize_brazil_phone(row["phone"])
        if current.valid and current.digits == phone.digits:
            matches.append(row)
    if matches:
        raise LookupError("cliente_duplicado_para_telefone")
    client_id = str(uuid.uuid4())
    suffix = phone.digits[-4:]
    conn.execute(
        """INSERT INTO clients(id,name,phone,notes,created_by)
           VALUES(?,?,?,?,?)""",
        (
            client_id,
            f"Cliente WhatsApp {suffix}",
            phone.e164,
            "Cadastro automatico por conversa iniciada no WhatsApp.",
            "whatsapp_bot",
        ),
    )
    return conn.execute("SELECT * FROM clients WHERE id=?", (client_id,)).fetchone(), True


def register_incoming_message(conn, company_key, payload, manage_transaction=True):
    external_id = str(payload.get("external_message_id") or "").strip()
    instance_key = str(payload.get("instance_key") or "").strip()
    jid = str(payload.get("jid") or "").strip()
    event_hash = str(payload.get("event_hash") or "").strip()
    if not all((external_id, instance_key, jid, event_hash)):
        raise ValueError("evento_incompleto")

    existing = conn.execute(
        "SELECT id,conversation_id,client_id FROM whatsapp_messages WHERE company_key=? AND instance_key=? AND external_message_id=?",
        (company_key, instance_key, external_id),
    ).fetchone()
    if existing:
        return {"ok": True, "duplicate": True, "message_id": existing["id"], "conversation_id": existing["conversation_id"], "client_id": existing["client_id"]}

    if not jid.endswith("@s.whatsapp.net"):
        raise ValueError("jid_nao_individual")
    client, phone = find_client_for_phone(conn, jid.split("@", 1)[0].split(":", 1)[0])
    if not phone.valid:
        raise ValueError(phone.reason)
    if not client:
        raise LookupError("cliente_nao_encontrado_ou_duplicado")

    received_at = str(payload.get("received_at") or datetime.now(timezone.utc).isoformat())
    text = str(payload.get("text") or "")
    key = message_idempotency_key(company_key, external_id, jid, received_at, {"text": text, "event_hash": event_hash})
    states = ",".join("?" for _ in OPEN_CONVERSATION_STATES)
    conversation = conn.execute(
        f"""SELECT * FROM whatsapp_conversations
            WHERE company_key=? AND client_id=? AND jid=? AND status IN ({states})
            ORDER BY updated_at DESC LIMIT 1""",
        (company_key, client["id"], jid, *OPEN_CONVERSATION_STATES),
    ).fetchone()
    conversation_id = conversation["id"] if conversation else str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    intent = conversation_control_intent(text)
    next_state = intent or (conversation["status"] if conversation else "nova")

    previous_state = conversation["status"] if conversation else None
    try:
        if not conversation:
            conn.execute(
                """INSERT INTO whatsapp_conversations(id,company_key,client_id,jid,status,last_message_at)
                   VALUES(?,?,?,?,?,?)""",
                (conversation_id, company_key, client["id"], jid, next_state, received_at),
            )
        else:
            conn.execute(
                "UPDATE whatsapp_conversations SET status=?,last_message_at=?,updated_at=datetime('now') WHERE id=? AND company_key=?",
                (next_state, received_at, conversation_id, company_key),
            )
        conn.execute(
            """INSERT INTO whatsapp_messages(
                   id,company_key,instance_key,conversation_id,client_id,direction,
                   external_message_id,idempotency_key,event_hash,jid,body,status,received_at)
               VALUES(?,?,?,?,?,'recebida',?,?,?,?,?,'processada',?)""",
            (message_id, company_key, instance_key, conversation_id, client["id"], external_id, key, event_hash, jid, text, received_at),
        )
        conn.execute(
            "INSERT INTO whatsapp_events(id,company_key,message_id,event_hash,event_type,processing_status) VALUES(?,?,?,?,?,?)",
            (str(uuid.uuid4()), company_key, message_id, event_hash, "incoming", "processado"),
        )
        if intent == "opt_out":
            consent_id = str(uuid.uuid4())
            conn.execute(
                """INSERT INTO whatsapp_consent(id,company_key,client_id,phone_e164,status,source,revoked_at)
                   VALUES(?,?,?,?,?,'cliente',?)
                   ON CONFLICT(company_key,client_id,phone_e164) DO UPDATE SET
                     status='opt_out',source='cliente',revoked_at=excluded.revoked_at,updated_at=datetime('now')""",
                (consent_id, company_key, client["id"], phone.e164, "opt_out", received_at),
            )
        if manage_transaction:
            conn.commit()
    except sqlite3.IntegrityError:
        if not manage_transaction:
            raise
        conn.rollback()
        existing = conn.execute(
            "SELECT id,conversation_id,client_id FROM whatsapp_messages WHERE company_key=? AND instance_key=? AND external_message_id=?",
            (company_key, instance_key, external_id),
        ).fetchone()
        if existing:
            return {"ok": True, "duplicate": True, "message_id": existing["id"], "conversation_id": existing["conversation_id"], "client_id": existing["client_id"]}
        raise
    except Exception:
        if manage_transaction:
            conn.rollback()
        raise
    return {
        "ok": True,
        "duplicate": False,
        "message_id": message_id,
        "conversation_id": conversation_id,
        "client_id": client["id"],
        "intent": intent,
        "previous_state": previous_state,
        "new_state": next_state,
    }


def save_consumption(conn, company_key, client_id, body, username):
    average = decimal_text(body.get("average_consumption"), "consumo_medio")
    maximum = decimal_text(body.get("maximum_consumption"), "consumo_maximo", optional=True)
    if maximum is not None and Decimal(maximum) < Decimal(average):
        raise ValueError("consumo_maximo_menor_que_medio")
    product_key = str(body.get("product_key") or "").strip()
    unit = str(body.get("unit") or "").strip()
    if not product_key or not unit:
        raise ValueError("produto_e_unidade_obrigatorios")
    if not conn.execute("SELECT 1 FROM product_prices WHERE key=? AND active=1", (product_key,)).fetchone():
        raise LookupError("produto_nao_encontrado")
    item_id = str(uuid.uuid4())
    try:
        conn.execute(
            """INSERT INTO customer_product_consumption(
                   id,company_key,client_id,product_key,average_consumption,maximum_consumption,unit,updated_by)
               VALUES(?,?,?,?,?,?,?,?)
               ON CONFLICT(company_key,client_id,product_key) DO UPDATE SET
                 average_consumption=excluded.average_consumption,
                 maximum_consumption=excluded.maximum_consumption,
                 unit=excluded.unit,updated_by=excluded.updated_by,updated_at=datetime('now')""",
            (item_id, company_key, client_id, product_key, average, maximum, unit, username),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return conn.execute(
        "SELECT * FROM customer_product_consumption WHERE company_key=? AND client_id=? AND product_key=?",
        (company_key, client_id, product_key),
    ).fetchone()


def create_damage(conn, company_key, client_id, body, username):
    quantity = decimal_text(body.get("quantity"), "quantidade")
    percent = decimal_text(body.get("replacement_percent", 0), "percentual_reposicao")
    if Decimal(percent) > 100:
        raise ValueError("percentual_reposicao_invalido")
    product_key = str(body.get("product_key") or "").strip()
    if not product_key or not conn.execute("SELECT 1 FROM product_prices WHERE key=? AND active=1", (product_key,)).fetchone():
        raise LookupError("produto_nao_encontrado")
    damage_id = str(uuid.uuid4())
    try:
        conn.execute(
            """INSERT INTO customer_product_damage(
                   id,company_key,client_id,product_key,quantity,status,replacement_percent,
                   reason,notes,responsible_user_id)
               VALUES(?,?,?,?,?,'informada',?,?,?,?)""",
            (damage_id, company_key, client_id, product_key, quantity, percent, body.get("reason"), body.get("notes"), username),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    return conn.execute("SELECT * FROM customer_product_damage WHERE id=? AND company_key=?", (damage_id, company_key)).fetchone()
