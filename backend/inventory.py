import json
import math
import re
import sqlite3
import unicodedata
import uuid
from datetime import datetime


MODULES = {"raios", "estrada", "monteiro"}

SEED_PRODUCTS = [
    {
        "sku": "UVA-VITORIA-8KG",
        "name": "Uva Vitória - Caixa 8 kg",
        "unit": "CX",
        "aliases": ["UVA VITORIA CX 8 KG", "UVA VITORIA CAIXA 8 KG"],
    },
    {
        "sku": "UVA-VITORIA-KIDS-250G",
        "name": "Uva Vitória Kids - Caixa 5 kg (250 g)",
        "unit": "CX",
        "aliases": [
            "UVA VITORIA 5 KG KIDS - 250 G",
            "UVA VITORIA 5KG KIDS 250G",
            "Uva Vitória 250G - Cx",
        ],
        "sale_quantity_factor": 0.05,
    },
    {
        "sku": "UVA-VITORIA-5KG",
        "name": "Uva Vitória - Caixa 5 kg",
        "unit": "CX",
        "aliases": ["UVA VITORIA CX 5 KG", "UVA VITORIA CAIXA 5 KG", "Uva Vitoria"],
        "sale_quantity_factor": 0.1,
    },
    {
        "sku": "UVA-THOMPSON-VERDE-500G",
        "name": "Uva Thompson Verde - Caixa 500 g",
        "unit": "CX",
        "aliases": ["Uva Thompson Verde Cx 500G"],
        "sale_quantity_factor": 1,
    },
]

INITIAL_STOCK = {
    "UVA-VITORIA-8KG": 5,
    "UVA-VITORIA-KIDS-250G": 110,
    "UVA-VITORIA-5KG": 2870,
}


def init_inventory_schema(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS stock_products (
            id TEXT PRIMARY KEY,
            module_key TEXT NOT NULL,
            sku TEXT NOT NULL,
            name TEXT NOT NULL,
            unit TEXT NOT NULL DEFAULT 'UND',
            aliases_json TEXT NOT NULL DEFAULT '[]',
            sale_quantity_factor REAL NOT NULL DEFAULT 1,
            active INTEGER NOT NULL DEFAULT 1,
            tracking_after TEXT NOT NULL,
            created_at TEXT NOT NULL,
            UNIQUE(module_key, sku)
        );
        CREATE TABLE IF NOT EXISTS stock_movements (
            id TEXT PRIMARY KEY,
            product_id TEXT NOT NULL,
            movement_type TEXT NOT NULL CHECK(movement_type IN ('entry','exit','adjustment')),
            quantity_delta REAL NOT NULL,
            movement_date TEXT NOT NULL,
            reference TEXT NOT NULL DEFAULT '',
            notes TEXT NOT NULL DEFAULT '',
            created_by TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            FOREIGN KEY(product_id) REFERENCES stock_products(id)
        );
        CREATE TABLE IF NOT EXISTS stock_app_note_intakes (
            external_id TEXT PRIMARY KEY,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_stock_products_module ON stock_products(module_key, active, name);
        CREATE INDEX IF NOT EXISTS idx_stock_movements_product_date ON stock_movements(product_id, movement_date DESC);
        """
    )
    columns = {row[1] for row in conn.execute("PRAGMA table_info(stock_products)")}
    if "sale_quantity_factor" not in columns:
        conn.execute("ALTER TABLE stock_products ADD COLUMN sale_quantity_factor REAL NOT NULL DEFAULT 1")
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    opening_at = datetime.now().astimezone().replace(hour=0, minute=0, second=0, microsecond=0).isoformat(timespec="seconds")
    for item in SEED_PRODUCTS:
        conn.execute(
            """INSERT OR IGNORE INTO stock_products
               (id,module_key,sku,name,unit,aliases_json,tracking_after,created_at)
               VALUES(?,?,?,?,?,?,?,?)""",
            (
                str(uuid.uuid4()),
                "estrada",
                item["sku"],
                item["name"],
                item["unit"],
                json.dumps(item["aliases"], ensure_ascii=False),
                now,
                now,
            ),
        )
        product = conn.execute(
            "SELECT id,aliases_json FROM stock_products WHERE module_key='estrada' AND sku=? AND active=1",
            (item["sku"],),
        ).fetchone()
        try:
            aliases = json.loads(product["aliases_json"] or "[]")
        except (TypeError, ValueError):
            aliases = []
        aliases = list(dict.fromkeys([*aliases, *item["aliases"]]))
        conn.execute(
            "UPDATE stock_products SET aliases_json=?,sale_quantity_factor=? WHERE id=?",
            (json.dumps(aliases, ensure_ascii=False), item.get("sale_quantity_factor", 1), product["id"]),
        )
    today = datetime.now().date().isoformat()
    for sku, quantity in INITIAL_STOCK.items():
        product = conn.execute(
            "SELECT id FROM stock_products WHERE module_key='estrada' AND sku=? AND active=1",
            (sku,),
        ).fetchone()
        if not product:
            continue
        has_history = conn.execute(
            "SELECT 1 FROM stock_movements WHERE product_id=? LIMIT 1",
            (product["id"],),
        ).fetchone()
        movement_id = f"opening-stock-{sku.lower()}"
        if has_history:
            conn.execute(
                """UPDATE stock_movements SET created_at=?
                   WHERE id=? AND movement_date=? AND substr(created_at,12,8)!='00:00:00'""",
                (opening_at, movement_id, today),
            )
            continue
        conn.execute(
            """INSERT OR IGNORE INTO stock_movements
               (id,product_id,movement_type,quantity_delta,movement_date,reference,notes,created_by,created_at)
               VALUES(?,?,?,?,?,?,?,?,?)""",
            (
                movement_id,
                product["id"],
                "entry",
                quantity,
                today,
                "Saldo inicial - nota das uvas enviada",
                "Quantidade informada na nota enviada pelo usuário.",
                "system",
                opening_at,
            ),
        )
    conn.commit()


def _normalized(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^A-Z0-9]+", "", text.upper())


def _normalized_stock_unit(value):
    unit = _normalized(value)
    return {"UNIDADE": "UN", "UNIDADES": "UN", "UND": "UN", "UN": "UN",
            "QUILO": "KG", "QUILOS": "KG", "KILO": "KG", "KILOS": "KG",
            "CAIXA": "CX", "CAIXAS": "CX", "MACO": "MC", "MACOS": "MC",
            "SACO": "SC", "SACOS": "SC"}.get(unit, unit)


def record_app_note_stock_intake(stock_conn, external_id, items, movement_date, created_by=""):
    """Add an app note to Raios stock exactly once, creating products on demand."""
    external_id = str(external_id or "").strip()[:80]
    if not external_id:
        raise ValueError("Identificador da nota obrigatório.")
    try:
        datetime.strptime(str(movement_date), "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError("Data da movimentação inválida.") from exc

    normalized_items = []
    for item in items or []:
        name = str(item.get("product") or "").strip()[:160]
        unit = str(item.get("unit") or "UND").strip().upper()[:20]
        try:
            quantity = float(item.get("weight"))
        except (TypeError, ValueError) as exc:
            raise ValueError("Quantidade de estoque inválida.") from exc
        if not name or quantity <= 0 or not math.isfinite(quantity):
            raise ValueError("Produto e quantidade positiva são obrigatórios.")
        normalized = _normalized(name)
        normalized_unit = _normalized_stock_unit(unit)
        garlic_pack_aliases = {
            "ALHO", "ALHODESCASCADO", "ALHO250G", "ALHO250GR",
            "ALHO250GRAMAS", "ALHODESCASCADO250G", "ALHODESCASCADO250GR",
            "ALHODESCASCADO250GRAMAS",
        }
        if normalized in garlic_pack_aliases and (
            normalized_unit == "UN" or "250" in normalized
        ):
            name = "Alho 250g"
            unit = "UN"
        elif normalized == "MACAXEIRAAVACUO":
            name = "Macaxeira a Vácuo"
        normalized_items.append((name, unit, quantity))
    if not normalized_items:
        raise ValueError("A nota não contém produtos para entrada no estoque.")

    now = datetime.now().astimezone().isoformat(timespec="seconds")
    stock_conn.execute("BEGIN IMMEDIATE")
    try:
        if stock_conn.execute(
            "SELECT 1 FROM stock_app_note_intakes WHERE external_id=?", (external_id,)
        ).fetchone():
            stock_conn.commit()
            return {"ok": True, "duplicate": True, "items_added": 0}

        products = [dict(row) for row in stock_conn.execute(
            "SELECT * FROM stock_products WHERE module_key='raios' AND active=1"
        ).fetchall()]
        added = 0
        for index, (name, unit, quantity) in enumerate(normalized_items):
            key = _normalized(name)
            product = None
            for candidate in products:
                if _normalized_stock_unit(candidate["unit"]) != _normalized_stock_unit(unit):
                    continue
                aliases = {_normalized(candidate["name"]), _normalized(candidate["sku"])}
                try:
                    aliases.update(_normalized(alias) for alias in json.loads(candidate["aliases_json"] or "[]"))
                except (TypeError, ValueError):
                    pass
                if key in aliases:
                    product = candidate
                    break
            if product is None:
                sku = "APP-" + (key[:62] or uuid.uuid4().hex[:12]) + "-" + (_normalized_stock_unit(unit)[:12] or "UN")
                product_id = str(uuid.uuid4())
                aliases_json = json.dumps([name], ensure_ascii=False)
                stock_conn.execute(
                    """INSERT INTO stock_products
                       (id,module_key,sku,name,unit,aliases_json,tracking_after,created_at)
                       VALUES(?, 'raios', ?, ?, ?, ?, ?, ?)""",
                    (product_id, sku, name, unit, aliases_json, now, now),
                )
                product = {"id": product_id, "name": name, "sku": sku, "unit": unit,
                           "aliases_json": aliases_json}
                products.append(product)
            stock_conn.execute(
                """INSERT INTO stock_movements
                   (id,product_id,movement_type,quantity_delta,movement_date,reference,notes,created_by,created_at)
                   VALUES(?, ?, 'entry', ?, ?, ?, ?, ?, ?)""",
                (f"app-note:{external_id}:{index}", product["id"], quantity, movement_date,
                 "Nota APP " + external_id,
                 "Entrada automática da Entrega por voz · cliente ESTOQUE",
                 str(created_by or "")[:120], now),
            )
            added += 1
        stock_conn.execute(
            "INSERT INTO stock_app_note_intakes(external_id,created_at) VALUES(?,?)", (external_id, now)
        )
        stock_conn.commit()
        return {"ok": True, "duplicate": False, "items_added": added}
    except Exception:
        stock_conn.rollback()
        raise


def sync_stock_catalog(stock_conn, source_conn, module_key):
    """Make registered module products manageable in inventory without duplicating SKUs."""
    if module_key not in MODULES:
        raise ValueError("Módulo de estoque inválido.")
    if module_key == "monteiro":
        try:
            rows = source_conn.execute(
                "SELECT id,name FROM paladar_products WHERE COALESCE(active,1)=1 ORDER BY name COLLATE NOCASE"
            ).fetchall()
        except sqlite3.OperationalError:
            rows = []
        catalog = [(str(row["id"]), str(row["name"] or "").strip()) for row in rows]
    else:
        try:
            rows = source_conn.execute(
                "SELECT key,label FROM product_prices WHERE COALESCE(active,1)=1 ORDER BY label COLLATE NOCASE"
            ).fetchall()
        except sqlite3.OperationalError:
            rows = []
        catalog = [(str(row["key"]), str(row["label"] or "").strip()) for row in rows]

    now = datetime.now().astimezone().isoformat(timespec="seconds")
    inserted = 0
    changed = False
    for source_key, label in catalog:
        if not label:
            continue
        normalized_label = _normalized(label)
        matched = None
        for existing in stock_conn.execute(
            "SELECT id,name,aliases_json FROM stock_products WHERE module_key=? AND active=1",
            (module_key,),
        ).fetchall():
            try:
                existing_aliases = json.loads(existing["aliases_json"] or "[]")
            except (TypeError, ValueError):
                existing_aliases = []
            if normalized_label in {_normalized(existing["name"]), *(_normalized(value) for value in existing_aliases)}:
                matched = (existing, existing_aliases)
                break
        if matched:
            existing, existing_aliases = matched
            if label not in existing_aliases:
                existing_aliases.append(label)
                stock_conn.execute(
                    "UPDATE stock_products SET aliases_json=? WHERE id=?",
                    (json.dumps(existing_aliases, ensure_ascii=False), existing["id"]),
                )
                changed = True
            continue
        sku = re.sub(r"[^A-Z0-9]+", "-", source_key.upper()).strip("-")[:60] or _normalized(label)[:60]
        product_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"bm-stock:{module_key}:{sku}"))
        unit_match = re.search(r"\b(CX|CAIXA|KG|QUILO|G|GRAMA|GRAMAS|MAÇO|MACO|SACO|UN|UND|UNIDADE|ROLO|L|LITRO)\b", label, re.IGNORECASE)
        unit = (unit_match.group(1).upper() if unit_match else "UND")
        unit = {"CAIXA": "CX", "QUILO": "KG", "G": "G", "GRAMA": "G", "GRAMAS": "G", "MACO": "MAÇO", "UNIDADE": "UN", "UND": "UN", "LITRO": "L"}.get(unit, unit)
        cursor = stock_conn.execute(
            """INSERT OR IGNORE INTO stock_products
               (id,module_key,sku,name,unit,aliases_json,tracking_after,created_at)
               VALUES(?,?,?,?,?,?,?,?)""",
            (product_id, module_key, sku, label, unit, json.dumps([label], ensure_ascii=False), now, now),
        )
        inserted += max(0, cursor.rowcount)
        changed = changed or bool(cursor.rowcount)
    if changed:
        stock_conn.commit()
    return inserted


def _as_datetime(value):
    try:
        parsed = datetime.fromisoformat(str(value or "").replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if parsed.tzinfo is None:
        parsed = parsed.astimezone()
    return parsed


def _sale_rows(conn, module_key):
    if module_key == "monteiro":
        try:
            return conn.execute(
                """SELECT id, saledate AS sale_date, created_at, client, product,
                          quantity, nf_number, total
                   FROM paladar_sales ORDER BY id"""
            ).fetchall()
        except sqlite3.OperationalError:
            return []
    return conn.execute(
        """SELECT id, sale_date, created_at, client, product, quantity,
                  nf_number, total, sale_type
           FROM sales WHERE sale_type!='AVARIA' ORDER BY sale_date, sale_time, id"""
    ).fetchall()


def inventory_snapshot(stock_conn, source_conn, module_key, include_archived=False):
    if module_key not in MODULES:
        raise ValueError("Módulo de estoque inválido.")
    products = [dict(row) for row in stock_conn.execute(
        "SELECT * FROM stock_products WHERE module_key=? AND (?=1 OR active=1) ORDER BY name COLLATE NOCASE",
        (module_key, int(bool(include_archived))),
    ).fetchall()]
    manual_rows = stock_conn.execute(
        """SELECT m.*, p.name AS product_name, p.sku, p.unit
           FROM stock_movements m JOIN stock_products p ON p.id=m.product_id
           WHERE p.module_key=? ORDER BY m.movement_date DESC, m.created_at DESC""",
        (module_key,),
    ).fetchall()
    movements = [dict(row) | {"source": "manual"} for row in manual_rows]
    sales = _sale_rows(source_conn, module_key)
    today = datetime.now().date().isoformat()
    for product in products:
        aliases = {_normalized(product["name"]), _normalized(product["sku"])}
        try:
            aliases.update(_normalized(value) for value in json.loads(product["aliases_json"] or "[]"))
        except (TypeError, ValueError):
            pass
        started = _as_datetime(product["tracking_after"])
        sale_quantity_factor = float(product.get("sale_quantity_factor") or 1)
        balance = 0.0
        events = []
        matched_sales = []
        for row in manual_rows:
            if row["product_id"] == product["id"]:
                is_count = "contagem" in str(row["reference"] or "").casefold()
                events.append((str(row["movement_date"] or ""), str(row["created_at"] or ""), float(row["quantity_delta"] or 0), is_count))
        for sale in sales:
            if _normalized(sale["product"]) not in aliases:
                continue
            quantity = float(sale["quantity"] or 0)
            if quantity <= 0:
                continue
            matched_sales.append(sale)
            sold_on = _as_datetime(sale["sale_date"])
            if not started or not sold_on or sold_on.date() < started.date():
                continue
            converted_quantity = quantity * sale_quantity_factor
            delta = -converted_quantity
            events.append((str(sale["sale_date"] or ""), str(sale["created_at"] or ""), delta, False))
            conversion_note = (
                f" · {quantity:g} na venda → {converted_quantity:g} {product['unit']} no estoque"
                if sale_quantity_factor != 1 else ""
            )
            movements.append({
                "id": f"sale:{module_key}:{sale['id']}",
                "product_id": product["id"],
                "product_name": product["name"],
                "sku": product["sku"],
                "unit": product["unit"],
                "movement_type": "exit",
                "quantity_delta": delta,
                "movement_date": sale["sale_date"],
                "reference": sale["nf_number"] or "",
                "client": sale["client"] or "",
                "notes": f"Saída por venda · {sale['client'] or 'Cliente não informado'}{conversion_note}",
                "sale_quantity": quantity,
                "sale_quantity_factor": sale_quantity_factor,
                "source": "sale",
                "source_id": str(sale["id"]),
                "total": float(sale["total"] or 0),
            })
        events.sort(key=lambda event: (event[0], event[1]))
        balance_points = []
        count_events = [event for event in events if event[3]]
        latest_count = max(count_events, key=lambda event: (event[0], event[1])) if count_events else None
        after_count = latest_count is None
        for event in events:
            _, _, delta, is_count = event
            balance += delta
            if is_count and latest_count == event:
                after_count = True
                balance_points = [round(balance, 3)]
            elif after_count:
                balance_points.append(round(balance, 3))
        if not balance_points:
            balance_points = [0.0]
        elif len(balance_points) > 8:
            last_index = len(balance_points) - 1
            balance_points = [balance_points[round(index * last_index / 7)] for index in range(8)]
        product["balance"] = round(balance, 3)
        product["trend"] = balance_points
        converted_sales = [float(sale["quantity"] or 0) * sale_quantity_factor for sale in matched_sales]
        today_sales = [sale for sale in matched_sales if str(sale["sale_date"] or "")[:10] == today]
        product["sales_count"] = len(matched_sales)
        product["sold_quantity"] = round(sum(converted_sales), 3)
        product["today_sales_count"] = len(today_sales)
        product["today_sold_quantity"] = round(sum(float(sale["quantity"] or 0) * sale_quantity_factor for sale in today_sales), 3)
        product["today_sales_revenue"] = round(sum(float(sale["total"] or 0) for sale in today_sales), 2)
        product["min_sale_quantity"] = round(min(converted_sales), 3) if converted_sales else 0
        product["max_sale_quantity"] = round(max(converted_sales), 3) if converted_sales else 0
        product["sales_revenue"] = round(sum(float(sale["total"] or 0) for sale in matched_sales), 2)
        product["sales_first_date"] = min((str(sale["sale_date"] or "")[:10] for sale in matched_sales), default="")
        product["sales_last_date"] = max((str(sale["sale_date"] or "")[:10] for sale in matched_sales), default="")
        product["max_balance"] = round(max([0.0, *balance_points]), 3)
        product["min_balance"] = 0
        product["aliases"] = json.loads(product.pop("aliases_json") or "[]")
        product.pop("tracking_after", None)
    def movement_order(row):
        ref = str(row.get("reference") or "")
        match = re.search(r"\d+", ref)
        movement_date = _as_datetime(row.get("movement_date"))
        day_order = -(movement_date.date().toordinal() if movement_date else 0)
        sale_order = 0 if row.get("source") == "sale" else 1
        invoice_order = int(match.group()) if row.get("source") == "sale" and match else 0
        return (day_order, sale_order, invoice_order, str(row.get("created_at") or ""), str(row.get("source_id") or row.get("id") or ""))
    movements.sort(key=movement_order)
    return {"module": module_key, "products": products, "movements": movements[:500]}


def ensure_stock_balance_count(stock_conn, source_conn, module_key, sku, quantity, movement_id, reference):
    if module_key not in MODULES:
        raise ValueError("Módulo de estoque inválido.")
    product = stock_conn.execute(
        "SELECT id,unit FROM stock_products WHERE module_key=? AND sku=? AND active=1",
        (module_key, sku),
    ).fetchone()
    if not product:
        return False
    snapshot = inventory_snapshot(stock_conn, source_conn, module_key)
    snapshot_product = next((item for item in snapshot["products"] if item["id"] == product["id"]), {})
    current = float(snapshot_product.get("balance") or 0)
    target_balance = max(0.0, float(quantity) - float(snapshot_product.get("sold_quantity") or 0))
    delta = round(target_balance - current, 6)
    existing = stock_conn.execute(
        "SELECT quantity_delta,notes FROM stock_movements WHERE id=? AND product_id=?",
        (movement_id, product["id"]),
    ).fetchone()
    if existing:
        if not str(existing["notes"] or "").startswith("Saldo físico atual definido para"):
            return False
        corrected_delta = round(float(existing["quantity_delta"] or 0) + delta, 6)
        stock_conn.execute(
            "UPDATE stock_movements SET quantity_delta=?,notes=? WHERE id=?",
            (corrected_delta,
             f"Saldo inicial reconciliado: {float(quantity):g} {product['unit']} menos {float(snapshot_product.get('sold_quantity') or 0):g} vendidos.",
             movement_id),
        )
        stock_conn.commit()
        return True
    now = datetime.now().astimezone().isoformat(timespec="seconds")
    stock_conn.execute(
        """INSERT INTO stock_movements
           (id,product_id,movement_type,quantity_delta,movement_date,reference,notes,created_by,created_at)
           VALUES(?,?,?,?,?,?,?,?,?)""",
        (movement_id, product["id"], "adjustment", delta, datetime.now().date().isoformat(), reference,
         f"Saldo inicial de {float(quantity):g} {product['unit']} menos {float(snapshot_product.get('sold_quantity') or 0):g} vendidos.",
         "system", now),
    )
    stock_conn.commit()
    return True


def inventory_product_sales(stock_conn, source_conn, module_key, product_id):
    product = stock_conn.execute(
        "SELECT * FROM stock_products WHERE id=? AND module_key=?",
        (product_id, module_key),
    ).fetchone()
    if not product:
        return None
    aliases = {_normalized(product["name"]), _normalized(product["sku"])}
    try:
        aliases.update(_normalized(value) for value in json.loads(product["aliases_json"] or "[]"))
    except (TypeError, ValueError):
        pass
    factor = float(product["sale_quantity_factor"] or 1)
    rows = []
    for sale in _sale_rows(source_conn, module_key):
        if _normalized(sale["product"]) not in aliases or float(sale["quantity"] or 0) <= 0:
            continue
        rows.append({
            "id": str(sale["id"]), "date": str(sale["sale_date"] or "")[:10],
            "reference": str(sale["nf_number"] or ""), "client": str(sale["client"] or ""),
            "sale_type": str(sale["sale_type"] or ""), "quantity": round(float(sale["quantity"]) * factor, 3),
            "unit": product["unit"], "total": round(float(sale["total"] or 0), 2),
        })
    def invoice_order(row):
        match = re.search(r"\d+", row["reference"])
        try:
            date_order = -datetime.fromisoformat(row["date"]).date().toordinal()
        except ValueError:
            date_order = 0
        return (date_order, 0 if match else 1, int(match.group()) if match else 0, row["id"])
    rows.sort(key=invoice_order)
    return rows
