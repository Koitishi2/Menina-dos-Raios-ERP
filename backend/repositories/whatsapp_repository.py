from pathlib import Path


MIGRATIONS_DIR = Path(__file__).resolve().parents[1] / "migrations"


def init_whatsapp_schema(conn):
    for migration in ("20260914_whatsapp_orders_up.sql", "20260914_whatsapp_inbound_up.sql"):
        conn.executescript((MIGRATIONS_DIR / migration).read_text(encoding="utf-8"))


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
                     ORDER BY wc.updated_at DESC LIMIT 1) AS consent_status
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
            """SELECT o.*,cl.name AS client_name,
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
        """SELECT o.*,cl.name AS client_name FROM whatsapp_order_drafts o
           JOIN clients cl ON cl.id=o.client_id WHERE o.id=? AND o.company_key=?""",
        (order_id, company_key),
    ).fetchone()
    if not row:
        return None
    result = dict(row)
    result["items"] = [
        dict(item)
        for item in conn.execute(
            """SELECT i.*,COALESCE(p.label,i.product_key) AS product_name,
                      CASE i.product_key
                        WHEN 'MAC_PCT' THEN 'KG'
                        WHEN 'MAC_VACUO' THEN 'KG'
                        WHEN 'ALHO_KG' THEN 'KG'
                        WHEN 'ALHO_250G' THEN 'UN'
                        WHEN 'MAC_CHIPS' THEN 'UN'
                        WHEN 'PRE_COZIDA' THEN 'UN'
                        ELSE ''
                      END AS unit
               FROM whatsapp_order_items i
               LEFT JOIN product_prices p ON p.key=i.product_key
               WHERE i.order_id=? ORDER BY i.created_at,i.id""",
            (order_id,),
        ).fetchall()
    ]
    result["history"] = [dict(item) for item in conn.execute("SELECT * FROM whatsapp_order_history WHERE order_id=? AND company_key=? ORDER BY created_at,id", (order_id, company_key)).fetchall()]
    conversation = conn.execute(
        """SELECT id,status,last_message_at,created_at,updated_at
           FROM whatsapp_conversations WHERE id=? AND company_key=?""",
        (result["conversation_id"], company_key),
    ).fetchone()
    result["conversation"] = row_dict(conversation)
    result["messages"] = [
        dict(message)
        for message in conn.execute(
            """SELECT id,direction,body,status,error_text AS error_message,
                      received_at,processed_at AS sent_at,created_at
               FROM whatsapp_messages WHERE conversation_id=? AND company_key=?
               ORDER BY created_at,id""",
            (result["conversation_id"], company_key),
        ).fetchall()
    ]
    return result


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
