import hashlib
import json
import sqlite3
import uuid
from datetime import datetime

try:
    from ..domains.whatsapp_policies import conversation_control_intent, normalize_brazil_phone, normalize_command
    from ..repositories import whatsapp_repository as repository
    from .whatsapp_order_service import register_incoming_message
except ImportError:
    from domains.whatsapp_policies import conversation_control_intent, normalize_brazil_phone, normalize_command
    from repositories import whatsapp_repository as repository
    from services.whatsapp_order_service import register_incoming_message


SYSTEM_MESSAGE_TYPES = frozenset({
    "protocolMessage", "senderKeyDistributionMessage", "messageContextInfo",
    "reactionMessage", "pollUpdateMessage", "keepInChatMessage",
})


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


def _result(row, duplicate=False):
    return {
        "ok": row["processing_status"] not in ("erro",),
        "duplicate": duplicate,
        "event_record_id": row["id"],
        "status": row["processing_status"],
        "client_id": row["client_id"],
        "message_id": row["message_id"],
        "error_code": row["error_code"],
    }


def _mark_duplicate(conn, row):
    conn.execute(
        """UPDATE whatsapp_inbound_events
           SET duplicate_count=duplicate_count+1,last_duplicate_at=datetime('now'),updated_at=datetime('now')
           WHERE id=?""",
        (row["id"],),
    )
    conn.commit()
    return _result(conn.execute("SELECT * FROM whatsapp_inbound_events WHERE id=?", (row["id"],)).fetchone(), True)


def process_inbound_event(conn, company_key, payload):
    instance_key = str(payload.get("instance") or "").strip()
    event_id = str(payload.get("event_id") or "").strip()
    external_id = str(payload.get("message_id") or "").strip()
    jid = str(payload.get("remote_jid") or "").strip().lower()
    message_type = str(payload.get("message_type") or "").strip()
    raw_type = str(payload.get("raw_type") or "").strip()[:100] or None
    text = str(payload.get("text") or "")[:10000]
    received_at = validate_iso_timestamp(payload.get("timestamp"))

    duplicate = repository.find_inbound_duplicate(conn, company_key, instance_key, event_id, external_id)
    if duplicate:
        return _mark_duplicate(conn, duplicate)

    record_id = str(uuid.uuid4())
    phone = normalize_brazil_phone(jid.split("@", 1)[0].split(":", 1)[0])
    base = (
        record_id, company_key, "baileys", instance_key, event_id, external_id, jid,
        phone.e164 or None, message_type, raw_type, text[:500], received_at,
    )
    try:
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
        elif not jid.endswith("@s.whatsapp.net"):
            blocked_reason = "jid_nao_individual"
        elif message_type in SYSTEM_MESSAGE_TYPES or not text.strip():
            blocked_reason = "mensagem_de_sistema"
        elif not phone.valid:
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
            "received_at": received_at,
            "text": text,
            "event_hash": event_hash({
                "company": company_key, "instance": instance_key, "event": event_id,
                "message": external_id, "jid": jid, "timestamp": received_at,
            }),
        }
        try:
            processed = register_incoming_message(conn, company_key, incoming, manage_transaction=False)
        except LookupError:
            conn.execute(
                """UPDATE whatsapp_inbound_events
                   SET processing_status='nao_identificado',error_code='cliente_nao_encontrado_ou_duplicado',updated_at=datetime('now')
                   WHERE id=?""",
                (record_id,),
            )
            conn.commit()
            row = conn.execute("SELECT * FROM whatsapp_inbound_events WHERE id=?", (record_id,)).fetchone()
            return _result(row)

        command = normalize_command(text) if conversation_control_intent(text) == "opt_out" else None
        conn.execute(
            """UPDATE whatsapp_inbound_events SET processing_status='processado',client_id=?,message_id=?,
                   command=?,previous_state=?,new_state=?,updated_at=datetime('now') WHERE id=?""",
            (processed["client_id"], processed["message_id"], command, processed["previous_state"], processed["new_state"], record_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM whatsapp_inbound_events WHERE id=?", (record_id,)).fetchone()
        return _result(row)
    except sqlite3.IntegrityError:
        conn.rollback()
        duplicate = repository.find_inbound_duplicate(conn, company_key, instance_key, event_id, external_id)
        if duplicate:
            return _mark_duplicate(conn, duplicate)
        raise
    except Exception:
        conn.rollback()
        raise
