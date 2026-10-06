import hashlib
import json
import sqlite3
import uuid
from datetime import datetime

try:
    from ..domains.whatsapp_policies import conversation_control_intent, normalize_brazil_phone, normalize_command
    from ..repositories import whatsapp_repository as repository
    from .whatsapp_order_bot_service import (
        advance_order_bot, order_bot_config, order_bot_runtime_reason, send_and_record_reply,
    )
    from .whatsapp_order_service import ensure_inbound_client, register_incoming_message
    from .whatsapp_order_service import ensure_inbound_jid_client
except ImportError:
    from domains.whatsapp_policies import conversation_control_intent, normalize_brazil_phone, normalize_command
    from repositories import whatsapp_repository as repository
    from services.whatsapp_order_bot_service import (
        advance_order_bot, order_bot_config, order_bot_runtime_reason, send_and_record_reply,
    )
    from services.whatsapp_order_service import ensure_inbound_client, register_incoming_message
    from services.whatsapp_order_service import ensure_inbound_jid_client


SYSTEM_MESSAGE_TYPES = frozenset({
    "protocolMessage", "senderKeyDistributionMessage", "messageContextInfo",
    "reactionMessage", "pollUpdateMessage", "keepInChatMessage",
})

NEW_ORDER_COMMANDS = frozenset({
    "PEDIDO", "FAZER PEDIDO", "QUERO PEDIDO", "QUERO FAZER PEDIDO",
    "NOVO", "NOVO PEDIDO", "NOVO ATENDIMENTO",
})
ORDER_BOT_CONVERSATION_STATES = frozenset({
    "nova", "identificando_produto", "coletando_quantidade", "coletando_avaria",
    "aguardando_confirmacao", "aguardando_aprovacao", "aguardando_resposta",
    "pedido_rascunho",
})
ORDER_BOT_NUMERIC_OPTIONS = frozenset({"1", "2", "3", "4", "5", "6"})


def validate_iso_timestamp(value):
    raw = str(value or "").strip()
    try:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("timestamp_invalido") from exc
    if parsed.tzinfo is None:
        raise ValueError("timestamp_sem_fuso")
    return parsed.isoformat()


def event_hash(payload):
    canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _result(row, duplicate=False, bot=None):
    result = {
        "ok": row["processing_status"] not in ("erro",),
        "duplicate": duplicate,
        "event_record_id": row["id"],
        "status": row["processing_status"],
        "client_id": row["client_id"],
        "message_id": row["message_id"],
        "error_code": row["error_code"],
    }
    if bot is not None:
        result["bot"] = bot
    return result


def _mark_duplicate(conn, row):
    conn.execute(
        """UPDATE whatsapp_inbound_events
           SET duplicate_count=duplicate_count+1,last_duplicate_at=datetime('now'),updated_at=datetime('now')
           WHERE id=?""",
        (row["id"],),
    )
    conn.commit()
    return _result(conn.execute("SELECT * FROM whatsapp_inbound_events WHERE id=?", (row["id"],)).fetchone(), True)


def _first_valid_phone_jid(*values):
    for value in values:
        text = str(value or "").strip().lower()
        if not text:
            continue
        phone = normalize_brazil_phone(text.split("@", 1)[0].split(":", 1)[0])
        if phone.valid:
            return text, phone
    return "", normalize_brazil_phone("")


def process_inbound_event(conn, company_key, payload, sender=None, outbound=None):
    instance_key = str(payload.get("instance") or "").strip()
    event_id = str(payload.get("event_id") or "").strip()
    external_id = str(payload.get("message_id") or "").strip()
    jid = str(payload.get("remote_jid") or "").strip().lower()
    message_type = str(payload.get("message_type") or "").strip()
    raw_type = str(payload.get("raw_type") or "").strip()[:100] or None
    text = str(payload.get("text") or "")[:10000]
    received_at = validate_iso_timestamp(payload.get("timestamp"))
    phone_jid, phone = _first_valid_phone_jid(
        payload.get("phone_jid"),
        payload.get("remote_jid_alt"),
        payload.get("participant_alt"),
        jid,
    )
    is_lid = jid.endswith("@lid")
    config = order_bot_config(conn) if sender is not None and outbound is not None else None
    runtime_reason = (
        order_bot_runtime_reason(config, outbound, phone.e164 if phone.valid else None, datetime.fromisoformat(received_at), jid=jid)
        if config is not None else None
    )

    duplicate = repository.find_inbound_duplicate(conn, company_key, instance_key, event_id, external_id)
    retry_incomplete = bool(
        duplicate
        and duplicate["processing_status"] == "bloqueado"
        and duplicate["error_code"] == "mensagem_de_sistema"
        and text.strip()
    )
    if duplicate and not retry_incomplete:
        return _mark_duplicate(conn, duplicate)

    record_id = duplicate["id"] if retry_incomplete else str(uuid.uuid4())
    base = (
        record_id, company_key, "baileys", instance_key, event_id, external_id, jid,
        phone.e164 or None, message_type, raw_type, text[:500], received_at,
    )
    try:
        if retry_incomplete:
            conn.execute(
                """UPDATE whatsapp_inbound_events
                   SET processing_status='recebido',error_code=NULL,provider=?,jid=?,phone_e164=?,
                       message_type=?,raw_type=?,body_preview=?,received_at=?,updated_at=datetime('now')
                   WHERE id=?""",
                (base[2], base[6], base[7], base[8], base[9], base[10], base[11], record_id),
            )
            conn.commit()
        else:
            conn.execute(
                """INSERT INTO whatsapp_inbound_events(
                       id,company_key,provider,instance_key,event_id,external_message_id,jid,
                       phone_e164,message_type,raw_type,body_preview,received_at,processing_status)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?, 'recebido')""",
                base,
            )

        blocked_reason = None
        if payload.get("from_me") is True:
            blocked_reason = "mensagem_do_proprio_numero"
        elif jid.endswith("@g.us"):
            blocked_reason = "grupo_bloqueado"
        elif not jid.endswith("@s.whatsapp.net") and not is_lid:
            blocked_reason = "jid_nao_individual"
        elif message_type in SYSTEM_MESSAGE_TYPES or not text.strip():
            blocked_reason = "mensagem_de_sistema"
        elif not is_lid and not phone.valid:
            blocked_reason = phone.reason

        if blocked_reason:
            conn.execute(
                """UPDATE whatsapp_inbound_events SET processing_status='bloqueado',error_code=?,updated_at=datetime('now')
                   WHERE id=?""",
                (blocked_reason, record_id),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM whatsapp_inbound_events WHERE id=?", (record_id,)).fetchone()
            return _result(row)

        incoming = {
            "instance_key": instance_key,
            "external_message_id": external_id,
            "jid": jid,
            "phone_e164": phone.e164 if phone.valid else None,
            "phone_jid": phone_jid,
            "remote_jid_alt": payload.get("remote_jid_alt"),
            "participant_alt": payload.get("participant_alt"),
            "received_at": received_at,
            "text": text,
            "event_hash": event_hash({
                "company": company_key, "instance": instance_key, "event": event_id,
                "message": external_id, "jid": jid, "timestamp": received_at,
            }),
        }
        normalized_command = normalize_command(text)
        starts_new_order = normalized_command in NEW_ORDER_COMMANDS
        try:
            processed = register_incoming_message(
                conn, company_key, incoming, manage_transaction=False, force_new_conversation=starts_new_order,
            )
        except LookupError:
            if runtime_reason == "ativo":
                if is_lid:
                    ensure_inbound_jid_client(conn, jid, phone.e164 if phone.valid else None)
                else:
                    ensure_inbound_client(conn, phone.e164)
                processed = register_incoming_message(
                    conn, company_key, incoming, manage_transaction=False, force_new_conversation=starts_new_order,
                )
            else:
                conn.execute(
                    """UPDATE whatsapp_inbound_events
                       SET processing_status='nao_identificado',error_code='cliente_nao_encontrado_ou_duplicado',updated_at=datetime('now')
                       WHERE id=?""",
                    (record_id,),
                )
                conn.commit()
                row = conn.execute("SELECT * FROM whatsapp_inbound_events WHERE id=?", (record_id,)).fetchone()
                return _result(row)

        intent = conversation_control_intent(text)
        current_flow_state = processed.get("previous_state") or processed.get("new_state")
        if current_flow_state in ORDER_BOT_CONVERSATION_STATES and normalized_command in ORDER_BOT_NUMERIC_OPTIONS:
            intent = None
        command = normalized_command if (intent is not None or starts_new_order) else None
        bot = None
        if sender is not None and outbound is not None and (intent is None or starts_new_order):
            if runtime_reason == "ativo":
                bot = advance_order_bot(conn, company_key, processed, text, config)
            else:
                bot = {"handled": False, "reason": runtime_reason}
        final_state = bot.get("state") if bot and bot.get("state") else processed["new_state"]
        conn.execute(
            """UPDATE whatsapp_inbound_events SET processing_status='processado',client_id=?,message_id=?,
                   command=?,previous_state=?,new_state=?,updated_at=datetime('now') WHERE id=?""",
            (processed["client_id"], processed["message_id"], command, processed["previous_state"], final_state, record_id),
        )
        conn.commit()
        if bot and bot.get("reply"):
            bot["delivery"] = send_and_record_reply(conn, company_key, processed, bot["reply"], sender, config)
        row = conn.execute("SELECT * FROM whatsapp_inbound_events WHERE id=?", (record_id,)).fetchone()
        return _result(row, bot=bot)
    except sqlite3.IntegrityError:
        conn.rollback()
        duplicate = repository.find_inbound_duplicate(conn, company_key, instance_key, event_id, external_id)
        if duplicate:
            return _mark_duplicate(conn, duplicate)
        raise
    except Exception:
        conn.rollback()
        raise
