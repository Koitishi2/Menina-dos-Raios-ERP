import hashlib
import json
import re
import unicodedata
import uuid
from datetime import datetime
from decimal import Decimal, InvalidOperation


DEFAULT_ORDER_BOT_MESSAGES = {
    "order_bot_disclosure_message": (
        "Este é um atendimento automatizado. Esta conversa será registrada para processar o seu pedido."
    ),
    "order_bot_welcome_message": (
        "Olá, {cliente}! Qual produto você deseja solicitar?\n\n"
        "Nossa lista de produtos:\n"
        "1. Macaxeira com casca\n"
        "2. Macaxeira a vácuo\n"
        "3. Alho descascado 250g\n"
        "4. Alho descascado 1kg\n"
        "5. Macaxeira chips\n"
        "6. Macaxeira pré-cozida"
    ),
    "order_bot_quantity_message": "Qual quantidade? Informe o valor em KG ou UN.",
    "order_bot_damage_message": "Tem avaria? Se sim, informe quantos KG ou UN. Se não, responda NÃO.",
    "order_bot_confirm_message": "Está correto? Responda SIM ou NAO.",
    "order_bot_done_message": (
        "Pedido feito! Aguarde a mensagem da data que será entregue! "
        "Normalmente, a entrega ocorre em até 24 horas após o pedido."
    ),
}

PRODUCTS = (
    {"key": "MAC_PCT", "name": "Macaxeira com casca", "unit": "KG", "aliases": ("1", "macaxeira com casca", "macaxeira casca")},
    {"key": "MAC_VACUO", "name": "Macaxeira a vacuo", "unit": "KG", "aliases": ("2", "macaxeira a vacuo", "macaxeira vacuo")},
    {"key": "ALHO_250G", "name": "Alho descascado 250g", "unit": "UN", "aliases": ("3", "alho descascado 250g", "alho 250g")},
    {"key": "ALHO_KG", "name": "Alho descascado 1kg", "unit": "KG", "aliases": ("4", "alho descascado 1kg", "alho 1kg", "alho kg")},
    {"key": "MAC_CHIPS", "name": "Macaxeira chips", "unit": "UN", "aliases": ("5", "macaxeira chips", "chips")},
    {"key": "PRE_COZIDA", "name": "Macaxeira pre-cozida", "unit": "UN", "aliases": ("6", "macaxeira pre cozida", "macaxeira pre-cozida", "pre cozida")},
)

YES_WORDS = frozenset({"SIM", "S", "OK", "CONFIRMAR", "CONFIRMO", "PODE", "SALVAR"})
NO_WORDS = frozenset({"NAO", "N", "CANCELAR", "CANCELE"})
ORDER_ORIGIN = "cliente_iniciou_contato"
SCORE_COMPONENTS = {
    "cliente_identificado": 20,
    "produto_identificado": 20,
    "quantidade_informada": 25,
    "avaria_informada": 15,
    "confirmacao_explicita": 20,
}


def normalize_text(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"\s+", " ", text).strip().lower()


def order_bot_config(conn):
    rows = conn.execute("SELECT key,value FROM whatsapp_config").fetchall()
    config = {row["key"]: row["value"] for row in rows}
    for key, value in DEFAULT_ORDER_BOT_MESSAGES.items():
        config.setdefault(key, value)
    return config


def order_bot_runtime_reason(config, outbound, phone_e164, at_time):
    if str(config.get("bot_active", "0")) != "1" or str(config.get("auto_reply_enabled", "0")) != "1":
        return "bot_desativado"
    if not outbound.get("enabled") or outbound.get("mode") == "disabled":
        return "envio_desativado"
    if str(config.get("test_mode", "0")) == "1" and outbound.get("mode") != "sandbox":
        return "modo_teste_exige_sandbox"
    if outbound.get("mode") == "production" and not outbound.get("production_approved"):
        return "producao_nao_aprovada"
    if outbound.get("mode") == "sandbox" and phone_e164 not in outbound.get("sandbox_numbers", set()):
        return "numero_fora_da_sandbox"
    if config.get("provider") != "baileys":
        return "provedor_baileys_obrigatorio"
    start = str(config.get("auto_reply_from") or "00:00")
    end = str(config.get("auto_reply_to") or "23:59")
    current = at_time.strftime("%H:%M")
    inside = start <= current <= end if start <= end else current >= start or current <= end
    return "ativo" if inside else "fora_do_horario"


def match_product(value):
    normalized = normalize_text(value)
    for product in PRODUCTS:
        if normalized in {normalize_text(alias) for alias in product["aliases"]}:
            return product
    return None


def parse_quantity(value, expected_unit, allow_no=False):
    normalized = normalize_text(value)
    upper = normalized.upper()
    if allow_no and upper in NO_WORDS:
        return Decimal("0")
    match = re.fullmatch(r"(\d+(?:[.,]\d+)?)\s*(KG|KGS|QUILO|QUILOS|UN|UND|UNIDADE|UNIDADES)?", upper)
    if not match:
        return None
    try:
        quantity = Decimal(match.group(1).replace(",", "."))
    except InvalidOperation:
        return None
    if quantity <= 0:
        return None
    supplied = match.group(2) or expected_unit
    supplied_unit = "KG" if supplied in {"KG", "KGS", "QUILO", "QUILOS"} else "UN"
    if supplied_unit != expected_unit:
        return None
    return quantity


def _product_available(conn, product):
    columns = {row[1] for row in conn.execute("PRAGMA table_info(product_prices)")}
    fields = ["key"]
    for optional in ("label", "price", "active"):
        if optional in columns:
            fields.append(optional)
    row = conn.execute(f"SELECT {','.join(fields)} FROM product_prices WHERE key=?", (product["key"],)).fetchone()
    if not row or ("active" in row.keys() and not row["active"]):
        return None
    return {
        **product,
        "label": row["label"] if "label" in row.keys() else product["name"],
        "price": Decimal(str(row["price"] or 0)) if "price" in row.keys() else Decimal("0"),
    }


def _open_order(conn, company_key, conversation_id):
    return conn.execute(
        """SELECT * FROM whatsapp_order_drafts WHERE company_key=? AND conversation_id=?
           AND status IN ('rascunho','aguardando_confirmacao') ORDER BY created_at DESC LIMIT 1""",
        (company_key, conversation_id),
    ).fetchone()


def _order_item(conn, order_id):
    return conn.execute("SELECT * FROM whatsapp_order_items WHERE order_id=? ORDER BY created_at LIMIT 1", (order_id,)).fetchone()


def _set_conversation_state(conn, company_key, conversation_id, state):
    conn.execute(
        "UPDATE whatsapp_conversations SET status=?,updated_at=datetime('now') WHERE id=? AND company_key=?",
        (state, conversation_id, company_key),
    )


def _message(config, key, client_name):
    return str(config.get(key) or DEFAULT_ORDER_BOT_MESSAGES[key]).replace("{cliente}", client_name)


def _score_memory(*completed):
    completed_set = set(completed)
    earned = {key: value for key, value in SCORE_COMPONENTS.items() if key in completed_set}
    return json.dumps(
        {
            "origin": ORDER_ORIGIN,
            "automated_service": True,
            "order_score": sum(earned.values()),
            "score_components": earned,
        },
        ensure_ascii=False,
        sort_keys=True,
    )


def advance_order_bot(conn, company_key, processed, incoming_text, config):
    conversation = conn.execute(
        "SELECT * FROM whatsapp_conversations WHERE id=? AND company_key=?",
        (processed["conversation_id"], company_key),
    ).fetchone()
    client = conn.execute("SELECT * FROM clients WHERE id=? AND active=1", (processed["client_id"],)).fetchone()
    if not conversation or not client:
        return {"handled": False, "reason": "conversa_ou_cliente_ausente"}
    state = conversation["status"]
    if state in ("opt_out", "atendimento_humano", "cancelada", "concluida"):
        return {"handled": False, "reason": state}
    if state == "aguardando_aprovacao":
        return {"handled": False, "reason": "pedido_ja_confirmado", "state": state}

    if state == "nova":
        _set_conversation_state(conn, company_key, conversation["id"], "identificando_produto")
        disclosure = _message(config, "order_bot_disclosure_message", client["name"])
        welcome = _message(config, "order_bot_welcome_message", client["name"])
        return {"handled": True, "state": "identificando_produto", "reply": f"{disclosure}\n\n{welcome}"}

    if state == "identificando_produto":
        product = match_product(incoming_text)
        available = _product_available(conn, product) if product else None
        if not available:
            return {"handled": True, "state": state, "reply": "Nao identifiquei esse produto. Responda com um numero de 1 a 6 da lista."}
        order = _open_order(conn, company_key, conversation["id"])
        if not order:
            order_id = str(uuid.uuid4())
            order_key = hashlib.sha256(f"order:{company_key}:{conversation['id']}".encode()).hexdigest()
            conn.execute(
                """INSERT INTO whatsapp_order_drafts(
                       id,company_key,client_id,conversation_id,source_message_id,idempotency_key,status,total,calculation_memory)
                   VALUES(?,?,?,?,?,?,'rascunho','0',?)""",
                (
                    order_id, company_key, client["id"], conversation["id"], processed["message_id"], order_key,
                    _score_memory("cliente_identificado", "produto_identificado"),
                ),
            )
            conn.execute(
                """INSERT INTO whatsapp_order_items(
                       id,order_id,product_key,unit_price,total,confirmed_damage)
                   VALUES(?,?,?,?,?,'0')""",
                (str(uuid.uuid4()), order_id, available["key"], str(available["price"]), "0"),
            )
        _set_conversation_state(conn, company_key, conversation["id"], "coletando_quantidade")
        return {"handled": True, "state": "coletando_quantidade", "reply": _message(config, "order_bot_quantity_message", client["name"])}

    order = _open_order(conn, company_key, conversation["id"])
    item = _order_item(conn, order["id"]) if order else None
    if not order or not item:
        _set_conversation_state(conn, company_key, conversation["id"], "atendimento_humano")
        return {"handled": True, "state": "atendimento_humano", "reply": "Nao consegui recuperar o pedido. Um atendente continuara o atendimento."}
    product = next((entry for entry in PRODUCTS if entry["key"] == item["product_key"]), None)
    if not product:
        _set_conversation_state(conn, company_key, conversation["id"], "atendimento_humano")
        return {"handled": True, "state": "atendimento_humano", "reply": "Produto indisponivel. Um atendente continuara o atendimento."}

    if state == "coletando_quantidade":
        quantity = parse_quantity(incoming_text, product["unit"])
        if quantity is None:
            return {"handled": True, "state": state, "reply": f"Informe uma quantidade valida em {product['unit']}. Exemplo: 10 {product['unit']}."}
        total = quantity * Decimal(str(item["unit_price"] or 0))
        conn.execute(
            "UPDATE whatsapp_order_items SET requested_quantity=?,total=?,updated_at=datetime('now') WHERE id=?",
            (str(quantity), str(total), item["id"]),
        )
        conn.execute(
            "UPDATE whatsapp_order_drafts SET requested_quantity=?,total=?,calculation_memory=?,updated_at=datetime('now') WHERE id=?",
            (
                str(quantity), str(total),
                _score_memory("cliente_identificado", "produto_identificado", "quantidade_informada"), order["id"],
            ),
        )
        _set_conversation_state(conn, company_key, conversation["id"], "coletando_avaria")
        return {"handled": True, "state": "coletando_avaria", "reply": _message(config, "order_bot_damage_message", client["name"])}

    if state == "coletando_avaria":
        damage = parse_quantity(incoming_text, product["unit"], allow_no=True)
        if damage is None:
            return {"handled": True, "state": state, "reply": f"Responda NAO ou informe a avaria em {product['unit']}. Exemplo: 2 {product['unit']}."}
        requested = Decimal(str(item["requested_quantity"] or 0))
        if damage > requested:
            return {"handled": True, "state": state, "reply": "A avaria nao pode ser maior que a quantidade solicitada."}
        conn.execute("UPDATE whatsapp_order_items SET confirmed_damage=?,updated_at=datetime('now') WHERE id=?", (str(damage), item["id"]))
        conn.execute(
            "UPDATE whatsapp_order_drafts SET status='aguardando_confirmacao',calculation_memory=?,updated_at=datetime('now') WHERE id=?",
            (
                _score_memory(
                    "cliente_identificado", "produto_identificado", "quantidade_informada", "avaria_informada",
                ),
                order["id"],
            ),
        )
        _set_conversation_state(conn, company_key, conversation["id"], "aguardando_confirmacao")
        summary = f"Produto: {product['name']}\nQuantidade: {requested} {product['unit']}\nAvaria: {damage} {product['unit']}\n\n"
        return {"handled": True, "state": "aguardando_confirmacao", "reply": summary + _message(config, "order_bot_confirm_message", client["name"])}

    if state == "aguardando_confirmacao":
        answer = normalize_text(incoming_text).upper()
        if answer in YES_WORDS:
            now = datetime.now().astimezone().isoformat()
            conn.execute(
                """UPDATE whatsapp_order_drafts SET status='aguardando_aprovacao',confirmed_quantity=requested_quantity,
                       calculation_memory=?,confirmed_at=?,updated_at=datetime('now') WHERE id=?""",
                (
                    _score_memory(*SCORE_COMPONENTS), now, order["id"],
                ),
            )
            conn.execute("UPDATE whatsapp_order_items SET confirmed_quantity=requested_quantity,updated_at=datetime('now') WHERE order_id=?", (order["id"],))
            conn.execute(
                """INSERT INTO whatsapp_order_history(id,company_key,order_id,previous_status,new_status,changed_by,reason)
                   VALUES(?,?,?,'aguardando_confirmacao','aguardando_aprovacao','cliente','confirmacao_whatsapp')""",
                (str(uuid.uuid4()), company_key, order["id"]),
            )
            _set_conversation_state(conn, company_key, conversation["id"], "aguardando_aprovacao")
            return {"handled": True, "state": "aguardando_aprovacao", "order_id": order["id"], "reply": _message(config, "order_bot_done_message", client["name"])}
        if answer in NO_WORDS:
            conn.execute("UPDATE whatsapp_order_drafts SET status='cancelado',updated_at=datetime('now') WHERE id=?", (order["id"],))
            conn.execute(
                """INSERT INTO whatsapp_order_history(id,company_key,order_id,previous_status,new_status,changed_by,reason)
                   VALUES(?,?,?,'aguardando_confirmacao','cancelado','cliente','cancelamento_whatsapp')""",
                (str(uuid.uuid4()), company_key, order["id"]),
            )
            _set_conversation_state(conn, company_key, conversation["id"], "cancelada")
            return {"handled": True, "state": "cancelada", "order_id": order["id"], "reply": "Pedido cancelado. Quando precisar, envie uma nova mensagem."}
        return {"handled": True, "state": state, "reply": _message(config, "order_bot_confirm_message", client["name"])}

    return {"handled": False, "reason": "estado_nao_automatizado", "state": state}


def send_and_record_reply(conn, company_key, processed, reply, sender, config):
    if not reply:
        return {"attempted": False}
    client = conn.execute("SELECT phone FROM clients WHERE id=?", (processed["client_id"],)).fetchone()
    conversation = conn.execute("SELECT jid,status FROM whatsapp_conversations WHERE id=?", (processed["conversation_id"],)).fetchone()
    if not client or not conversation:
        return {"attempted": False, "reason": "destino_ausente"}
    try:
        response = sender(conversation["jid"].split("@", 1)[0].split(":", 1)[0], reply, config)
    except Exception as exc:
        response = {"ok": False, "response": f"erro_tecnico:{type(exc).__name__}"}
    ok = bool(response.get("ok"))
    external_id = f"bot:{processed['message_id']}:{conversation['status']}"
    idempotency = hashlib.sha256(f"{company_key}:{external_id}".encode()).hexdigest()
    message_id = str(uuid.uuid4())
    conn.execute(
        """INSERT OR IGNORE INTO whatsapp_messages(
               id,company_key,instance_key,conversation_id,client_id,direction,external_message_id,
               idempotency_key,event_hash,jid,body,status,error_text,processed_at)
           VALUES(?,?,?,?,?,'enviada',?,?,?,?,?,?,?,datetime('now'))""",
        (
            message_id, company_key, "order-bot", processed["conversation_id"], processed["client_id"],
            external_id, idempotency, idempotency, conversation["jid"], reply,
            "processada" if ok else "falha", None if ok else str(response.get("response") or "falha_envio")[:500],
        ),
    )
    conn.commit()
    return {"attempted": True, "sent": ok, "message_id": message_id, "detail": str(response.get("response") or "")[:200]}
