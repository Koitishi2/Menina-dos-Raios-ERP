import json
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
        "sale_quantity_factor": 0.2,
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
        for row in manual_rows:
            if row["product_id"] == product["id"]:
                events.append((str(row["movement_date"] or ""), str(row["created_at"] or ""), float(row["quantity_delta"] or 0)))
        for sale in sales:
            if _normalized(sale["product"]) not in aliases:
                continue
            sold_on = _as_datetime(sale["sale_date"])
            if not started or not sold_on or sold_on.date() < started.date():
                continue
            quantity = float(sale["quantity"] or 0)
            if quantity <= 0:
                continue
            converted_quantity = quantity * sale_quantity_factor
            delta = -converted_quantity
            events.append((str(sale["sale_date"] or ""), str(sale["created_at"] or ""), delta))
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
        for _, _, delta in events:
            balance += delta
            balance_points.append(round(balance, 3))
        if not balance_points:
            balance_points = [0.0]
        elif len(balance_points) > 8:
            last_index = len(balance_points) - 1
            balance_points = [balance_points[round(index * last_index / 7)] for index in range(8)]
        product["balance"] = round(balance, 3)
        product["trend"] = balance_points
        product["aliases"] = json.loads(product.pop("aliases_json") or "[]")
        product.pop("tracking_after", None)
    movements.sort(key=lambda row: (str(row.get("movement_date") or ""), str(row.get("created_at") or "")), reverse=True)
    return {"module": module_key, "products": products, "movements": movements[:500]}
