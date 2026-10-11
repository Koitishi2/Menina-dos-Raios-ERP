from pathlib import Path
import hashlib
import uuid
from decimal import Decimal, InvalidOperation

try:
    from ..domains.whatsapp_policies import normalize_brazil_phone
except ImportError:
    from domains.whatsapp_policies import normalize_brazil_phone


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"

UMBANDA_MOTIVATION_TEMPLATES = (
    "Que a serenidade dos Pretos-Velhos inspire seus passos. Com humildade e firmeza, um dia de cada vez, você também chega longe.",
    "Na Umbanda, a caridade se revela nos gestos sinceros. Faça o bem que estiver ao seu alcance e siga com o coração em paz.",
    "A sabedoria ensinada pelos Pretos-Velhos nos lembra: paciência não é desistir, é confiar no caminho enquanto fazemos a nossa parte.",
    "Que a luz de Oxalá fortaleça sua esperança. Mesmo devagar, todo passo guiado pelo bem tem valor.",
    "Respire fundo, aquiete o pensamento e recomece. A fé na Umbanda também floresce na coragem de tentar mais uma vez.",
    "Os Pretos-Velhos nos inspiram a ouvir com atenção e falar com bondade. Hoje, ofereça a alguém uma palavra que acolha.",
    "A força espiritual também se mostra na mansidão. Continue com dignidade, sem deixar que a dificuldade apague sua luz.",
    "Que os bons caminhos se abram diante de você. Caminhe com respeito, responsabilidade e confiança no bem.",
    "A caridade começa perto: no cuidado, na escuta e no respeito. Um gesto simples pode ser abrigo para alguém.",
    "Quando o caminho parecer comprido, lembre-se: firmeza se constrói passo a passo, com fé e atitude.",
    "Que a ancestralidade lhe recorde a força que existe em seguir em frente. Você carrega histórias de resistência e coragem.",
    "A humildade não diminui ninguém; ela abre espaço para aprender, crescer e repartir o que se sabe.",
    "Que a proteção dos bons guias acompanhe suas escolhas. Faça sua parte com honestidade e mantenha o coração sereno.",
    "Na Umbanda, cada pessoa merece respeito. Trate a si mesmo com a mesma dignidade que você oferece ao próximo.",
    "Os ensinamentos dos Pretos-Velhos convidam à calma: antes de responder, escute; antes de julgar, compreenda.",
    "Que a esperança renasça hoje, ainda que pequena. Uma chama cuidada com carinho volta a iluminar o caminho.",
    "A fé não elimina os desafios, mas pode renovar sua coragem para atravessá-los com consciência e amor.",
    "Siga com os pés no chão e o coração voltado ao bem. Espiritualidade também é responsabilidade nas escolhas diárias.",
    "Que a paz de um congá em oração inspire tranquilidade no seu dia, onde quer que você esteja.",
    "Cada recomeço merece respeito. Não se cobre por ainda estar aprendendo; honre a coragem de continuar.",
    "A palavra cuidadosa pode aliviar um peso. Que hoje sua voz leve respeito, consolo e verdade.",
    "Os Pretos-Velhos nos inspiram a valorizar a simplicidade: presença, escuta e bondade também são grandes forças.",
    "Que a energia de Iemanjá lhe inspire acolhimento e equilíbrio para cuidar dos sentimentos com ternura.",
    "Com a coragem de Ogum como inspiração, enfrente os obstáculos com disciplina, prudência e determinação.",
    "Que a alegria de Oxóssi inspire curiosidade e aprendizado. Há conhecimento novo esperando por você em cada caminho.",
    "A justiça de Xangô nos lembra de agir com equilíbrio. Faça o que é correto, mesmo quando ninguém estiver olhando.",
    "Que a generosidade de Oxum inspire delicadeza consigo e com os outros. Cuidar do coração também é um ato de força.",
    "A transformação pede coragem. Deixe para trás o que já cumpriu seu ciclo e avance com sabedoria para o novo.",
    "Que a força dos seus guias lhe inspire proteção e discernimento. Nem toda pressa é caminho; escolha com consciência.",
    "A fé se fortalece quando caminha junto com a ação. Peça luz, planeje seus passos e faça o que depende de você.",
    "No trabalho e na vida, faça o possível com amor e capricho. O bem semeado com constância dá frutos no tempo certo.",
    "Que a memória dos mais velhos seja fonte de aprendizado e respeito. Honrar quem veio antes também é construir futuro.",
    "Quando faltar ânimo, permita-se descansar e depois retomar. Cuidar das próprias forças também é caminho de equilíbrio.",
    "A caridade verdadeira respeita a liberdade de cada pessoa. Ofereça ajuda com generosidade e sem esperar recompensa.",
    "Que a luz que você busca também encontre espaço dentro de você: em sua coragem, sua bondade e sua capacidade de mudar.",
    "Os ensinamentos da Umbanda valorizam o amor e o respeito. Leve esses valores para cada encontro deste dia.",
    "Não compare sua caminhada à de ninguém. Cada pessoa tem seu tempo, seus aprendizados e sua própria estrada.",
    "Que a firmeza dos Pretos-Velhos lhe ajude a atravessar esta fase com paciência, lucidez e esperança.",
    "A gratidão não apaga as lutas; ela também reconhece a força que você encontrou para chegar até aqui.",
    "Escolha a paz sempre que puder, mas não abandone seus limites. Respeito e firmeza podem caminhar juntos.",
    "Que o amor de mãe e o acolhimento de Iemanjá lhe recordem que pedir apoio também é um gesto de coragem.",
    "Um conselho sábio pode nascer do silêncio. Reserve um instante para ouvir sua consciência e escolher com serenidade.",
    "A esperança não precisa ser barulhenta. Às vezes, ela é apenas a decisão tranquila de tentar novamente amanhã.",
    "Que a força de Ogum lhe inspire a abrir caminhos sem ferir ninguém, com coragem, ética e determinação.",
    "Respeite os ciclos: há tempo de plantar, tempo de cuidar e tempo de colher. Continue fazendo sua parte com confiança.",
    "Seja ponte de acolhimento, não de julgamento. A empatia aproxima pessoas e fortalece comunidades.",
    "A sabedoria dos Pretos-Velhos nos inspira a não perder a ternura diante das dificuldades. Firmeza também pode ser gentil.",
    "Que os bons espíritos lhe inspirem clareza para reconhecer o que pode mudar e serenidade para aceitar o que não depende de você.",
    "Cada atitude de respeito ajuda a tornar o mundo mais justo. Faça hoje a diferença que está ao seu alcance.",
    "Siga com fé, humildade e coragem. Que seu caminho seja iluminado pelo bem que você escolhe praticar todos os dias.",
)


def init_whatsapp_schema(conn):
    for migration in ("20260914_whatsapp_orders_up.sql", "20260914_whatsapp_inbound_up.sql"):
        conn.executescript((MIGRATIONS_DIR / migration).read_text(encoding="utf-8"))
    conn.executemany(
        """INSERT OR IGNORE INTO whatsapp_templates (id, name, category, content)
           VALUES (?, ?, ?, ?)""",
        [
            (
                f"motivacao_umbanda_{index:03d}",
                f"Umbanda - Preto Velho {index:02d}",
                "motivacao_umbanda",
                content,
            )
            for index, content in enumerate(UMBANDA_MOTIVATION_TEMPLATES, start=1)
        ],
    )


def row_dict(row):
    return dict(row) if row is not None else None


def find_client(conn, client_id):
    return conn.execute("SELECT * FROM clients WHERE id=? AND active=1", (client_id,)).fetchone()


def active_clients(conn):
    return conn.execute("SELECT id,name,phone FROM clients WHERE active=1 ORDER BY name").fetchall()


def list_inbound_events(conn, company_key, limit=100):
    rows = conn.execute(
        """SELECT e.*,c.name AS client_name
           FROM whatsapp_inbound_events e
           LEFT JOIN clients c ON c.id=e.client_id
           WHERE e.company_key=?
           ORDER BY e.created_at DESC,e.id DESC LIMIT ?""",
        (company_key, max(1, min(int(limit), 500))),
    ).fetchall()
    return [dict(row) for row in rows]


def find_inbound_duplicate(conn, company_key, instance_key, event_id, external_message_id):
    return conn.execute(
        """SELECT * FROM whatsapp_inbound_events
           WHERE company_key=? AND instance_key=?
             AND (event_id=? OR external_message_id=?)
           ORDER BY created_at LIMIT 1""",
        (company_key, instance_key, event_id, external_message_id),
    ).fetchone()


def get_manual_batch(conn, company_key, batch_id):
    batch = conn.execute(
        "SELECT * FROM whatsapp_manual_batches WHERE company_key=? AND id=?",
        (company_key, batch_id),
    ).fetchone()
    if not batch:
        return None
    result = dict(batch)
    result["items"] = [
        dict(row)
        for row in conn.execute(
            """SELECT i.*,c.name AS client_name FROM whatsapp_manual_batch_items i
               JOIN clients c ON c.id=i.client_id
               WHERE i.company_key=? AND i.batch_id=? ORDER BY c.name,i.id""",
            (company_key, batch_id),
        ).fetchall()
    ]
    return result


def list_manual_batches(conn, company_key, limit=50):
    return [
        dict(row)
        for row in conn.execute(
            """SELECT b.*,
                      (SELECT COUNT(*) FROM whatsapp_manual_batch_items i WHERE i.batch_id=b.id) AS item_count,
                      (SELECT COUNT(*) FROM whatsapp_manual_batch_items i WHERE i.batch_id=b.id AND i.status='enviado') AS sent_count,
                      (SELECT COUNT(*) FROM whatsapp_manual_batch_items i WHERE i.batch_id=b.id AND i.status IN ('falhou','bloqueado','duplicado')) AS attention_count
               FROM whatsapp_manual_batches b WHERE b.company_key=?
               ORDER BY b.created_at DESC,b.id DESC LIMIT ?""",
            (company_key, max(1, min(int(limit), 200))),
        ).fetchall()
    ]


def client_whatsapp_summary(conn, company_key, client_id):
    client = find_client(conn, client_id)
    if not client:
        return None
    consent = conn.execute(
        "SELECT * FROM whatsapp_consent WHERE company_key=? AND client_id=? ORDER BY updated_at DESC LIMIT 1",
        (company_key, client_id),
    ).fetchone()
    conversation = conn.execute(
        "SELECT * FROM whatsapp_conversations WHERE company_key=? AND client_id=? ORDER BY updated_at DESC LIMIT 1",
        (company_key, client_id),
    ).fetchone()
    return {"client": dict(client), "consent": row_dict(consent), "conversation": row_dict(conversation)}


def list_conversations(conn, company_key, client_id=None):
    sql = """SELECT c.*,cl.name AS client_name,
                    (SELECT wc.status FROM whatsapp_consent wc
                     WHERE wc.company_key=c.company_key AND wc.client_id=c.client_id
                     ORDER BY wc.updated_at DESC LIMIT 1) AS consent_status,
                    (SELECT wm.direction FROM whatsapp_messages wm
                     WHERE wm.company_key=c.company_key AND wm.conversation_id=c.id
                     ORDER BY COALESCE(wm.received_at,wm.created_at) DESC,wm.id DESC LIMIT 1) AS last_message_direction,
                    (SELECT wm.body FROM whatsapp_messages wm
                     WHERE wm.company_key=c.company_key AND wm.conversation_id=c.id
                     ORDER BY COALESCE(wm.received_at,wm.created_at) DESC,wm.id DESC LIMIT 1) AS last_message_preview
             FROM whatsapp_conversations c JOIN clients cl ON cl.id=c.client_id
             WHERE c.company_key=?"""
    args = [company_key]
    if client_id:
        sql += " AND c.client_id=?"
        args.append(client_id)
    sql += " ORDER BY COALESCE(c.last_message_at,c.created_at) DESC"
    return [dict(row) for row in conn.execute(sql, args).fetchall()]


def get_conversation(conn, company_key, conversation_id):
    row = conn.execute(
        """SELECT c.*,cl.name AS client_name FROM whatsapp_conversations c
           JOIN clients cl ON cl.id=c.client_id WHERE c.id=? AND c.company_key=?""",
        (conversation_id, company_key),
    ).fetchone()
    if not row:
        return None
    result = dict(row)
    result["messages"] = [
        dict(item)
        for item in conn.execute(
            "SELECT * FROM whatsapp_messages WHERE conversation_id=? AND company_key=? ORDER BY created_at,id",
            (conversation_id, company_key),
        ).fetchall()
    ]
    return result


def list_orders(conn, company_key):
    return [
        dict(row)
        for row in conn.execute(
            """SELECT o.*,cl.name AS client_name,cl.phone AS client_phone,
                      EXISTS(SELECT 1 FROM customer_product_damage d WHERE d.order_id=o.id) AS with_damage,
                      EXISTS(SELECT 1 FROM whatsapp_order_items i WHERE i.order_id=o.id
                             AND i.maximum_consumption IS NOT NULL
                             AND CAST(i.requested_quantity AS REAL)>CAST(i.maximum_consumption AS REAL)) AS above_maximum
               FROM whatsapp_order_drafts o
               JOIN clients cl ON cl.id=o.client_id WHERE o.company_key=?
               ORDER BY o.created_at DESC""",
            (company_key,),
        ).fetchall()
    ]


def get_order(conn, company_key, order_id):
    row = conn.execute(
        """SELECT o.*,cl.name AS client_name,cl.phone AS client_phone FROM whatsapp_order_drafts o
           JOIN clients cl ON cl.id=o.client_id WHERE o.id=? AND o.company_key=?""",
        (order_id, company_key),
    ).fetchone()
    if not row:
        return None
    result = dict(row)
    result["items"] = [dict(item) for item in conn.execute("SELECT * FROM whatsapp_order_items WHERE order_id=? ORDER BY created_at,id", (order_id,)).fetchall()]
    result["history"] = [dict(item) for item in conn.execute("SELECT * FROM whatsapp_order_history WHERE order_id=? AND company_key=? ORDER BY created_at,id", (order_id, company_key)).fetchall()]
    return result


def _decimal_text(value, field, allow_zero=False):
    try:
        number = Decimal(str(value).replace(",", "."))
    except (InvalidOperation, TypeError, ValueError) as exc:
        raise ValueError(f"{field}_invalido") from exc
    if not number.is_finite() or number < 0 or (number == 0 and not allow_zero):
        raise ValueError(f"{field}_invalido")
    return number


def _append_order_history(conn, company_key, order_id, previous_status, new_status, username, reason):
    conn.execute(
        """INSERT INTO whatsapp_order_history(id,company_key,order_id,previous_status,new_status,changed_by,reason)
           VALUES(?,?,?,?,?,?,?)""",
        (str(uuid.uuid4()), company_key, order_id, previous_status, new_status, username or "sistema", reason or ""),
    )


def confirm_order(conn, company_key, order_id, username):
    row = conn.execute(
        "SELECT * FROM whatsapp_order_drafts WHERE id=? AND company_key=?",
        (order_id, company_key),
    ).fetchone()
    if not row:
        return None, False
    if row["status"] == "aprovado":
        return get_order(conn, company_key, order_id), False
    if row["status"] != "aguardando_aprovacao":
        raise ValueError(f"transicao_invalida:{row['status']}:aprovado")
    conn.execute(
        """UPDATE whatsapp_order_drafts
           SET status='aprovado',approved_by=?,approved_at=datetime('now'),updated_at=datetime('now')
           WHERE id=? AND company_key=?""",
        (username or "sistema", order_id, company_key),
    )
    _append_order_history(conn, company_key, order_id, row["status"], "aprovado", username, "aprovacao_ui")
    return get_order(conn, company_key, order_id), True


def reject_order(conn, company_key, order_id, username, reason):
    reason = str(reason or "").strip()
    if not reason:
        raise ValueError("motivo_obrigatorio")
    row = conn.execute(
        "SELECT * FROM whatsapp_order_drafts WHERE id=? AND company_key=?",
        (order_id, company_key),
    ).fetchone()
    if not row:
        return None, False
    if row["status"] == "cancelado":
        return get_order(conn, company_key, order_id), False
    if row["status"] != "aguardando_aprovacao":
        raise ValueError(f"transicao_invalida:{row['status']}:cancelado")
    conn.execute(
        """UPDATE whatsapp_order_drafts
           SET status='cancelado',block_reason=?,updated_at=datetime('now')
           WHERE id=? AND company_key=?""",
        (reason[:500], order_id, company_key),
    )
    _append_order_history(conn, company_key, order_id, row["status"], "cancelado", username, reason[:500])
    return get_order(conn, company_key, order_id), True


def delete_order(conn, company_key, order_id, username):
    row = conn.execute(
        "SELECT id,status FROM whatsapp_order_drafts WHERE id=? AND company_key=?",
        (order_id, company_key),
    ).fetchone()
    if not row:
        return None, False
    result = {"id": row["id"], "status": row["status"], "removed_by": username or "sistema"}
    conn.execute(
        "UPDATE customer_product_damage SET order_id=NULL WHERE order_id=? AND company_key=?",
        (order_id, company_key),
    )
    conn.execute(
        "DELETE FROM whatsapp_order_history WHERE order_id=? AND company_key=?",
        (order_id, company_key),
    )
    conn.execute("DELETE FROM whatsapp_order_items WHERE order_id=?", (order_id,))
    conn.execute("DELETE FROM whatsapp_order_drafts WHERE id=? AND company_key=?", (order_id, company_key))
    return result, True


def create_order_for_client(conn, company_key, client_id, items, username):
    client = find_client(conn, client_id)
    if not client:
        return None
    if not isinstance(items, list) or not items:
        raise ValueError("itens_obrigatorios")
    if len(items) > 20:
        raise ValueError("itens_excedem_limite")
    order_id = str(uuid.uuid4())
    conversation_id = str(uuid.uuid4())
    message_id = str(uuid.uuid4())
    phone = normalize_brazil_phone(client["phone"] or "")
    jid = phone.jid if phone.valid else f"{client_id}@manual.local"
    external_id = f"ui:new-order:{order_id}"
    idempotency = hashlib.sha256(f"{company_key}:{external_id}".encode()).hexdigest()
    total = Decimal("0")
    total_quantity = Decimal("0")
    prepared_items = []
    seen_products = set()
    for item in items:
        product_key = str((item or {}).get("product_key") or "").strip()
        if not product_key:
            raise ValueError("produto_obrigatorio")
        if product_key in seen_products:
            raise ValueError("produto_duplicado")
        seen_products.add(product_key)
        product = conn.execute("SELECT key,label,price FROM product_prices WHERE key=?", (product_key,)).fetchone()
        if not product:
            raise LookupError("produto_nao_encontrado")
        quantity = _decimal_text((item or {}).get("quantity"), "quantidade")
        damage = _decimal_text((item or {}).get("damage") or "0", "avaria", allow_zero=True)
        if damage > quantity:
            raise ValueError("avaria_maior_que_quantidade")
        unit_price = Decimal(str(product["price"] or 0))
        line_total = quantity * unit_price
        total += line_total
        total_quantity += quantity
        prepared_items.append((product_key, str(quantity), str(damage), str(unit_price), str(line_total)))
    conn.execute(
        """INSERT INTO whatsapp_conversations(id,company_key,client_id,jid,status,last_message_at)
           VALUES(?,?,?,?,?,datetime('now'))""",
        (conversation_id, company_key, client_id, jid, "pedido_rascunho"),
    )
    conn.execute(
        """INSERT INTO whatsapp_messages(
               id,company_key,instance_key,conversation_id,client_id,direction,
               external_message_id,idempotency_key,event_hash,jid,body,status,processed_at)
           VALUES(?,?,?,?,?,'recebida',?,?,?,?,?,'processada',datetime('now'))""",
        (
            message_id, company_key, "ui", conversation_id, client_id,
            external_id, idempotency, idempotency, jid, "Pedido criado manualmente na aba Pedidos.",
        ),
    )
    conn.execute(
        """INSERT INTO whatsapp_order_drafts(
               id,company_key,client_id,conversation_id,source_message_id,idempotency_key,status,
               requested_quantity,total,calculation_memory)
           VALUES(?,?,?,?,?,?,'rascunho',?,?,?)""",
        (
            order_id, company_key, client_id, conversation_id, message_id, idempotency,
            str(total_quantity), str(total), '{"origin":"pedidos_ui","draft_only":true}',
        ),
    )
    for product_key, quantity, damage, unit_price, line_total in prepared_items:
        conn.execute(
            """INSERT INTO whatsapp_order_items(
                   id,order_id,product_key,requested_quantity,confirmed_damage,unit_price,total)
               VALUES(?,?,?,?,?,?,?)""",
            (str(uuid.uuid4()), order_id, product_key, quantity, damage, unit_price, line_total),
        )
    _append_order_history(conn, company_key, order_id, None, "rascunho", username, "pedido_ui_manual")
    return get_order(conn, company_key, order_id)


def list_consumption(conn, company_key, client_id):
    return [dict(row) for row in conn.execute(
        "SELECT * FROM customer_product_consumption WHERE company_key=? AND client_id=? ORDER BY product_key",
        (company_key, client_id),
    ).fetchall()]


def list_damages(conn, company_key, client_id):
    return [dict(row) for row in conn.execute(
        "SELECT * FROM customer_product_damage WHERE company_key=? AND client_id=? ORDER BY created_at DESC",
        (company_key, client_id),
    ).fetchall()]
