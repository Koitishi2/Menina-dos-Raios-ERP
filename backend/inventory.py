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
        ],
    },
    {
        "sku": "UVA-VITORIA-5KG",
        "name": "Uva Vitória - Caixa 5 kg",
        "unit": "CX",
        "aliases": ["UVA VITORIA CX 5 KG", "UVA VITORIA CAIXA 5 KG", "Uva Vitoria"],
    },
]


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
    now = datetime.now().astimezone().isoformat(timespec="seconds")
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
    conn.commit()


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
            "ALHO",
            "ALHODESCASCADO",
            "ALHO250G",
            "ALHO250GR",
            "ALHO250GRAMAS",
            "ALHODESCASCADO250G",
            "ALHODESCASCADO250GR",
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
                aliases = json.dumps([name], ensure_ascii=False)
                stock_conn.execute(
                    """INSERT INTO stock_products
                       (id,module_key,sku,name,unit,aliases_json,tracking_after,created_at)
                       VALUES(?, 'raios', ?, ?, ?, ?, ?, ?)""",
                    (product_id, sku, name, unit, aliases, now, now),
                )
                product = {"id": product_id, "name": name, "sku": sku, "unit": unit,
                           "aliases_json": aliases}
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


def _normalized(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(char for char in text if not unicodedata.combining(char))
    return re.sub(r"[^A-Z0-9]+", "", text.upper())


def _stock_sale_quantity(product, sale):
    quantity = float(sale["quantity"] or 0)
    if (
        product["sku"] == "UVA-VITORIA-5KG"
        and _normalized(sale["product"]) == _normalized("Uva Vitoria")
    ):
        return quantity / 10
    return quantity


def _normalized_stock_unit(value):
    unit = _normalized(value)
    return {"UNIDADE": "UN", "UNIDADES": "UN", "UND": "UN", "UN": "UN",
            "QUILO": "KG", "QUILOS": "KG", "KILO": "KG", "KILOS": "KG",
            "CAIXA": "CX", "CAIXAS": "CX", "MACO": "MC", "MACOS": "MC",
            "SACO": "SC", "SACOS": "SC"}.get(unit, unit)


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


def inventory_snapshot(stock_conn, source_conn, module_key):
    if module_key not in MODULES:
        raise ValueError("Módulo de estoque inválido.")
    products = [dict(row) for row in stock_conn.execute(
        "SELECT * FROM stock_products WHERE module_key=? AND active=1 ORDER BY name COLLATE NOCASE",
        (module_key,),
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
        balance = 0.0
        for row in manual_rows:
            if row["product_id"] == product["id"]:
                balance += float(row["quantity_delta"] or 0)
        matched_sales = []
        for sale in sales:
            if _normalized(sale["product"]) not in aliases:
                continue
            quantity = _stock_sale_quantity(product, sale)
            if quantity <= 0:
                continue
            matched_sales.append((sale, quantity))
            created = _as_datetime(sale["created_at"])
            if not started or not created or created < started:
                continue
            balance -= quantity
            movements.append({
                "id": f"sale:{module_key}:{sale['id']}",
                "product_id": product["id"],
                "product_name": product["name"],
                "sku": product["sku"],
                "unit": product["unit"],
                "movement_type": "exit",
                "quantity_delta": -quantity,
                "movement_date": sale["sale_date"],
                "reference": sale["nf_number"] or "",
                "client": sale["client"] or "",
                "notes": f"Saída por venda · {sale['client'] or 'Cliente não informado'}",
                "source": "sale",
                "source_id": str(sale["id"]),
                "total": float(sale["total"] or 0),
            })
        quantities = [quantity for _, quantity in matched_sales]
        product.update({
            "sales_count": len(quantities),
            "sold_quantity": round(sum(quantities), 3),
            "min_sale_quantity": round(min(quantities), 3) if quantities else 0,
            "max_sale_quantity": round(max(quantities), 3) if quantities else 0,
            "sales_revenue": round(sum(float(sale["total"] or 0) for sale, _ in matched_sales), 2),
            "sales_first_date": min((str(sale["sale_date"] or "") for sale, _ in matched_sales), default=""),
            "sales_last_date": max((str(sale["sale_date"] or "") for sale, _ in matched_sales), default=""),
        })
        product["balance"] = round(balance, 3)
        product["aliases"] = json.loads(product.pop("aliases_json") or "[]")
        product.pop("tracking_after", None)
    movements.sort(key=lambda row: (
        0 if row.get("source") == "sale" and _nf_number(row.get("reference")) is not None else
        1 if row.get("source") == "sale" else 2,
        _nf_number(row.get("reference")) if row.get("source") == "sale" and _nf_number(row.get("reference")) is not None else 0,
        str(row.get("movement_date") or ""), str(row.get("created_at") or ""),
    ))
    return {"module": module_key, "products": products, "movements": movements[:500]}


def _nf_number(value):
    match = re.search(r"\d+", str(value or ""))
    return int(match.group()) if match else None


def ensure_stock_balance_count(stock_conn, source_conn, module_key, sku, quantity, movement_id, reference):
    """Record a one-time opening quantity and apply recognized sales to its balance."""
    exists = stock_conn.execute("SELECT 1 FROM stock_movements WHERE id=?", (movement_id,)).fetchone()
    if exists:
        return False
    product = stock_conn.execute(
        "SELECT * FROM stock_products WHERE module_key=? AND sku=? AND active=1",
        (module_key, sku),
    ).fetchone()
    if not product:
        return False
    aliases = {_normalized(product["name"]), _normalized(product["sku"])}
    try:
        aliases.update(_normalized(value) for value in json.loads(product["aliases_json"] or "[]"))
    except (TypeError, ValueError):
        pass
    matching_dates = [
        parsed for sale in _sale_rows(source_conn, module_key)
        if _normalized(sale["product"]) in aliases
        if (parsed := _as_datetime(sale["created_at"])) is not None
    ]
    if matching_dates:
        stock_conn.execute(
            "UPDATE stock_products SET tracking_after=? WHERE id=?",
            (min(matching_dates).isoformat(timespec="seconds"), product["id"]),
        )
    snapshot = inventory_snapshot(stock_conn, source_conn, module_key)
    current_product = next((item for item in snapshot["products"] if item["id"] == product["id"]), None)
    current = float(current_product["balance"]) if current_product else 0
    sold = float(current_product["sold_quantity"]) if current_product else 0
    target_balance = float(quantity) - sold
    delta = round(target_balance - current, 3)
    now = datetime.now().astimezone()
    stock_conn.execute(
        """INSERT INTO stock_movements
           (id,product_id,movement_type,quantity_delta,movement_date,reference,notes,created_by,created_at)
           VALUES(?,?, 'adjustment', ?, ?, ?, ?, 'system', ?)""",
        (movement_id, product["id"], delta, now.date().isoformat(), reference,
         f"Estoque inicial de {quantity:g} UN; baixas de vendas reconhecidas aplicadas.", now.isoformat(timespec="seconds")),
    )
    stock_conn.commit()
    return True


def inventory_product_sales(source_conn, module_key, product):
    aliases = {_normalized(product["name"]), _normalized(product["sku"])}
    try:
        aliases.update(_normalized(value) for value in json.loads(product["aliases_json"] or "[]"))
    except (TypeError, ValueError):
        pass
    rows = []
    for sale in _sale_rows(source_conn, module_key):
        if _normalized(sale["product"]) not in aliases:
            continue
        quantity = _stock_sale_quantity(product, sale)
        if quantity <= 0:
            continue
        rows.append({
            "id": str(sale["id"]), "reference": str(sale["nf_number"] or ""),
            "date": str(sale["sale_date"] or ""), "client": str(sale["client"] or ""),
            "sale_type": str(sale["sale_type"] or "NF") if module_key != "monteiro" else "NF",
            "quantity": quantity, "unit": product["unit"], "total": float(sale["total"] or 0),
        })
    rows.sort(key=lambda row: (
        0 if _nf_number(row["reference"]) is not None else 1,
        _nf_number(row["reference"]) if _nf_number(row["reference"]) is not None else 0,
        row["date"], row["id"],
    ))
    return rows

