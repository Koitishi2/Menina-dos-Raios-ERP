import hashlib
import json
import sqlite3
import uuid
from datetime import date, datetime, timedelta, timezone

try:
    from ..domains.whatsapp_policies import campaign_eligibility, normalize_brazil_phone
    from ..repositories import whatsapp_repository as repository
except ImportError:
    from domains.whatsapp_policies import campaign_eligibility, normalize_brazil_phone
    from repositories import whatsapp_repository as repository


OPEN_CONVERSATION_STATES = (
    "nova", "aguardando_resposta", "identificando_produto", "coletando_quantidade",
    "coletando_avaria", "calculando_reposicao", "aguardando_confirmacao",
    "pedido_rascunho", "aguardando_aprovacao", "atendimento_humano",
)
OPEN_ORDER_STATES = ("rascunho", "aguardando_confirmacao", "aguardando_aprovacao", "aprovado")


def _hash(value):
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _latest_consent(conn, company_key, client_id):
    return conn.execute(
        """SELECT status,updated_at FROM whatsapp_consent
           WHERE company_key=? AND client_id=? ORDER BY updated_at DESC LIMIT 1""",
        (company_key, client_id),
    ).fetchone()


def _client_snapshot(conn, company_key, client, today):
    phone = normalize_brazil_phone(client["phone"])
    consent = _latest_consent(conn, company_key, client["id"])
    consent_status = consent["status"] if consent else "desconhecido"
    sale = conn.execute(
        "SELECT MAX(sale_date) AS last_sale_at FROM sales WHERE lower(trim(client))=lower(trim(?))",
        (client["name"],),
    ).fetchone()
    last_sale_at = sale["last_sale_at"] if sale else None
    days = None
    if last_sale_at:
        try:
            days = (today - date.fromisoformat(last_sale_at[:10])).days
        except ValueError:
            days = None
    conversation = conn.execute(
        """SELECT id,status,last_message_at FROM whatsapp_conversations
           WHERE company_key=? AND client_id=? ORDER BY updated_at DESC LIMIT 1""",
        (company_key, client["id"]),
    ).fetchone()
    order = conn.execute(
        """SELECT id,status FROM whatsapp_order_drafts
           WHERE company_key=? AND client_id=? AND status IN (?,?,?,?)
           ORDER BY created_at DESC LIMIT 1""",
        (company_key, client["id"], *OPEN_ORDER_STATES),
    ).fetchone()
    last_sent = conn.execute(
        """SELECT sent_at,message_final FROM whatsapp_manual_batch_items
           WHERE company_key=? AND client_id=? AND status IN ('enviado','entregue')
           ORDER BY sent_at DESC LIMIT 1""",
        (company_key, client["id"]),
    ).fetchone()
    has_open_conversation = bool(conversation and conversation["status"] in OPEN_CONVERSATION_STATES)
    eligible, reason = campaign_eligibility(days if days is not None else 0, consent_status, has_open_conversation, bool(order))
    blocked = []
    if days is None:
        blocked.append("sem_historico_de_compra")
    elif days <= 7:
        blocked.append("menos_de_8_dias_sem_compra")
    if not phone.valid:
        blocked.append(phone.reason)
    if consent_status != "opt_in":
        blocked.append("opt_out" if consent_status == "opt_out" else "sem_consentimento")
    if has_open_conversation:
        blocked.append("conversa_aberta")
    if order:
        blocked.append("pedido_pendente")
    if last_sent and last_sent["sent_at"]:
        try:
            sent_date = datetime.fromisoformat(last_sent["sent_at"]).date()
            if sent_date >= today - timedelta(days=7):
                blocked.append("mensagem_recente")
        except ValueError:
            pass
    selectable = eligible and phone.valid and days is not None and not blocked
    return {
        "client_id": client["id"], "client_name": client["name"], "company": company_key,
        "phone_e164": phone.e164, "phone_valid": phone.valid, "consent": consent_status,
        "opt_out": consent_status == "opt_out", "last_sale_at": last_sale_at,
        "days_without_purchase": days, "last_message_at": conversation["last_message_at"] if conversation else None,
        "last_sent_at": last_sent["sent_at"] if last_sent else None,
        "open_conversation": has_open_conversation, "pending_order": bool(order),
        "suggestion_reason": reason if selectable else None,
        "block_reasons": blocked, "selectable": selectable,
    }


def list_suggestions(conn, company_key, filters=None, today=None):
    filters = filters or {}
    today = today or datetime.now(timezone.utc).date()
    rows = [_client_snapshot(conn, company_key, row, today) for row in repository.active_clients(conn)]
    minimum_days = max(0, int(filters.get("minimum_days", 8)))
    include_blocked = bool(filters.get("include_blocked", False))
    selectable_only = bool(filters.get("selectable_only", False))
    result = []
    for row in rows:
        if row["days_without_purchase"] is not None and row["days_without_purchase"] < minimum_days:
            continue
        if not include_blocked and row["block_reasons"]:
            continue
        if selectable_only and not row["selectable"]:
            continue
        if filters.get("phone_valid") is not None and row["phone_valid"] is not bool(filters["phone_valid"]):
            continue
        if filters.get("consent") and row["consent"] != filters["consent"]:
            continue
        if filters.get("open_conversation") is not None and row["open_conversation"] is not bool(filters["open_conversation"]):
            continue
        if filters.get("pending_order") is not None and row["pending_order"] is not bool(filters["pending_order"]):
            continue
        result.append(row)
    return sorted(result, key=lambda row: (-(row["days_without_purchase"] or -1), row["client_name"].lower()))


def create_manual_batch(conn, company_key, username, client_ids, message, filters=None, now=None, request_id=None):
    now = now or datetime.now(timezone.utc)
    clean_message = str(message or "").strip()
    selected = tuple(dict.fromkeys(str(value).strip() for value in client_ids if str(value).strip()))
    if not clean_message or len(clean_message) > 2000:
        raise ValueError("mensagem_invalida")
    if not selected or len(selected) > 200:
        raise ValueError("selecao_invalida")
    candidates = {row["client_id"]: row for row in list_suggestions(conn, company_key, {"minimum_days": 0, "include_blocked": True}, now.date())}
    missing = [client_id for client_id in selected if client_id not in candidates]
    if missing:
        raise LookupError("cliente_nao_encontrado")
    blocked = [candidates[client_id] for client_id in selected if not candidates[client_id]["selectable"]]
    if blocked:
        raise ValueError("cliente_bloqueado_na_selecao")
    batch_id = str(uuid.uuid4())
    message_version = _hash({"message": clean_message})
    request_id = str(request_id or "").strip()
    selection_version = _hash(
        {"company": company_key, "request_id": request_id, "user": username}
        if request_id else
        {"batch": batch_id, "company": company_key, "user": username}
    )
    filters_json = json.dumps(filters or {}, ensure_ascii=False, sort_keys=True)

    def existing_batch():
        row = conn.execute(
            "SELECT id FROM whatsapp_manual_batches WHERE company_key=? AND selection_version=?",
            (company_key, selection_version),
        ).fetchone()
        if not row:
            return None
        existing = repository.get_manual_batch(conn, company_key, row["id"])
        existing_clients = tuple(sorted(item["client_id"] for item in existing["items"]))
        if (
            existing["message_version"] != message_version
            or existing["filters_json"] != filters_json
            or existing_clients != tuple(sorted(selected))
        ):
            raise ValueError("chave_idempotencia_reutilizada")
        return existing

    if request_id:
        existing = existing_batch()
        if existing:
            return existing
    expires_at = (now + timedelta(minutes=15)).isoformat()
    try:
        conn.execute(
            """INSERT INTO whatsapp_manual_batches(
                   id,company_key,created_by,message_template,message_version,filters_json,
                   selection_version,status,expires_at,created_at,updated_at)
               VALUES(?,?,?,?,?,?,?,'rascunho',?,?,?)""",
            (batch_id, company_key, username, clean_message, message_version,
             filters_json, selection_version,
             expires_at, now.isoformat(), now.isoformat()),
        )
        for client_id in selected:
            row = candidates[client_id]
            final = clean_message.replace("{cliente}", row["client_name"]).replace("{CLIENTE}", row["client_name"])
            key = _hash({
                "company": company_key, "batch": batch_id, "client": client_id,
                "phone": row["phone_e164"], "message_version": message_version, "user": username,
            })
            conn.execute(
                """INSERT INTO whatsapp_manual_batch_items(
                       id,company_key,batch_id,client_id,phone_e164,consent_status,last_sale_at,
                       days_without_purchase,suggestion_reason,message_final,idempotency_key,status)
                   VALUES(?,?,?,?,?,?,?,?,?,?,?,'pendente')""",
                (str(uuid.uuid4()), company_key, batch_id, client_id, row["phone_e164"], row["consent"],
                 row["last_sale_at"], row["days_without_purchase"], row["suggestion_reason"], final, key),
            )
        conn.commit()
    except sqlite3.IntegrityError:
        conn.rollback()
        if request_id:
            existing = existing_batch()
            if existing:
                return existing
        raise
    except Exception:
        conn.rollback()
        raise
    return repository.get_manual_batch(conn, company_key, batch_id)


def confirm_manual_batch(conn, company_key, batch_id, username, now=None):
    now = now or datetime.now(timezone.utc)
    batch = repository.get_manual_batch(conn, company_key, batch_id)
    if not batch:
        raise LookupError("lote_nao_encontrado")
    if batch["created_by"] != username:
        raise PermissionError("lote_de_outro_usuario")
    if batch["status"] != "rascunho":
        raise ValueError("lote_nao_confirmavel")
    if datetime.fromisoformat(batch["expires_at"]) <= now:
        conn.execute("UPDATE whatsapp_manual_batches SET status='expirado',updated_at=? WHERE id=?", (now.isoformat(), batch_id))
        conn.commit()
        raise ValueError("selecao_expirada")
    conn.execute(
        "UPDATE whatsapp_manual_batches SET status='confirmado',confirmed_at=?,updated_at=? WHERE id=? AND company_key=?",
        (now.isoformat(), now.isoformat(), batch_id, company_key),
    )
    conn.commit()
    return repository.get_manual_batch(conn, company_key, batch_id)


def cancel_manual_batch(conn, company_key, batch_id, username, now=None):
    now = now or datetime.now(timezone.utc)
    batch = repository.get_manual_batch(conn, company_key, batch_id)
    if not batch:
        raise LookupError("lote_nao_encontrado")
    if batch["created_by"] != username:
        raise PermissionError("lote_de_outro_usuario")
    if batch["status"] not in ("rascunho", "confirmado"):
        raise ValueError("lote_nao_cancelavel")
    conn.execute("UPDATE whatsapp_manual_batches SET status='cancelado',cancelled_at=?,updated_at=? WHERE id=?", (now.isoformat(), now.isoformat(), batch_id))
    conn.execute("UPDATE whatsapp_manual_batch_items SET status='cancelado',updated_at=? WHERE batch_id=? AND status='pendente'", (now.isoformat(), batch_id))
    conn.commit()
    return repository.get_manual_batch(conn, company_key, batch_id)


def send_manual_batch(conn, company_key, batch_id, username, settings, config, sender, now=None):
    now = now or datetime.now(timezone.utc)
    batch = repository.get_manual_batch(conn, company_key, batch_id)
    if not batch:
        raise LookupError("lote_nao_encontrado")
    if batch["created_by"] != username:
        raise PermissionError("lote_de_outro_usuario")
    if batch["status"] != "confirmado" or not batch["confirmed_at"]:
        raise ValueError("confirmacao_obrigatoria")
    if datetime.fromisoformat(batch["expires_at"]) <= now:
        conn.execute("UPDATE whatsapp_manual_batches SET status='expirado',updated_at=? WHERE id=?", (now.isoformat(), batch_id))
        conn.commit()
        raise ValueError("selecao_expirada")
    if not settings["enabled"] or settings["mode"] == "disabled":
        raise PermissionError("envio_desativado")
    if settings["mode"] == "production" and not settings["production_approved"]:
        raise PermissionError("modo_producao_nao_autorizado")
    if config.get("provider") != "baileys":
        raise ValueError("provedor_baileys_obrigatorio")

    conn.execute("UPDATE whatsapp_manual_batches SET status='processando',updated_at=? WHERE id=?", (now.isoformat(), batch_id))
    conn.commit()
    results = []
    for item in batch["items"]:
        if item["status"] != "pendente":
            results.append({"client_id": item["client_id"], "status": "duplicado"})
            continue
        client = repository.find_client(conn, item["client_id"])
        current = _client_snapshot(conn, company_key, client, now.date()) if client else None
        reason = None
        if not current or not current["selectable"]:
            reason = "bloqueado_por_revalidacao"
        elif current["phone_e164"] != item["phone_e164"] or current["consent"] != item["consent_status"] or current["last_sale_at"] != item["last_sale_at"]:
            reason = "dados_alterados_apos_selecao"
        elif settings["mode"] == "sandbox" and current["phone_e164"] not in settings["sandbox_numbers"]:
            reason = "numero_fora_da_sandbox"
        recent = conn.execute(
            """SELECT 1 FROM whatsapp_manual_batch_items
               WHERE company_key=? AND client_id=? AND message_final=? AND status IN ('enviado','entregue')
                 AND sent_at>=? AND id<>? LIMIT 1""",
            (company_key, item["client_id"], item["message_final"], (now - timedelta(days=settings["dedupe_days"])).isoformat(), item["id"]),
        ).fetchone()
        if recent:
            reason = "mensagem_igual_recente"
        if reason:
            conn.execute(
                "UPDATE whatsapp_manual_batch_items SET status='bloqueado',result_code=?,updated_at=? WHERE id=?",
                (reason, now.isoformat(), item["id"]),
            )
            conn.commit()
            results.append({"client_id": item["client_id"], "status": "bloqueado", "reason": reason})
            continue
        try:
            response = sender(current["phone_e164"].lstrip("+"), item["message_final"], config)
        except Exception as exc:
            response = {"ok": False, "response": f"erro_tecnico:{type(exc).__name__}"}
        status = "enviado" if response.get("ok") else "falhou"
        detail = str(response.get("response") or "")[:300]
        conn.execute(
            """UPDATE whatsapp_manual_batch_items SET status=?,result_code=?,result_detail=?,sent_at=?,updated_at=? WHERE id=?""",
            (status, "ok" if status == "enviado" else "falha_envio", detail, now.isoformat(), now.isoformat(), item["id"]),
        )
        conn.commit()
        results.append({"client_id": item["client_id"], "status": status})
    final = "concluido"
    conn.execute("UPDATE whatsapp_manual_batches SET status=?,updated_at=? WHERE id=?", (final, now.isoformat(), batch_id))
    conn.commit()
    return {"batch": repository.get_manual_batch(conn, company_key, batch_id), "results": results}
