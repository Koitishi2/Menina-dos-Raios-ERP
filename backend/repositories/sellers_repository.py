import sqlite3
import uuid


class SellersMigrationError(RuntimeError):
    pass


SELLERS_COLUMNS = {
    "id", "company_key", "name", "normalized_name", "active",
    "created_at", "updated_at", "created_by", "updated_by",
}
SELLER_HISTORY_COLUMNS = {
    "id", "seller_id", "company_key", "old_name", "new_name",
    "changed_by", "changed_at", "reason",
}
SALES_SELLER_COLUMNS = {"seller_id": "TEXT", "seller_name_snapshot": "TEXT"}


def _row_value(row, index, key):
    try:
        return row[key]
    except Exception:
        return row[index]


def _table_exists(conn, table):
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
        (table,),
    ).fetchone())


def _table_columns(conn, table):
    if not _table_exists(conn, table):
        return set()
    return {_row_value(row, 1, "name") for row in conn.execute(f"PRAGMA table_info({table})").fetchall()}


def _index_exists(conn, name):
    return bool(conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='index' AND name=?",
        (name,),
    ).fetchone())


def _has_unique_index(conn, table, columns):
    expected = list(columns)
    for idx in conn.execute(f"PRAGMA index_list({table})").fetchall():
        idx_name = _row_value(idx, 1, "name")
        is_unique = bool(_row_value(idx, 2, "unique"))
        if not is_unique:
            continue
        idx_cols = [
            _row_value(row, 2, "name")
            for row in conn.execute(f"PRAGMA index_info({idx_name})").fetchall()
        ]
        if idx_cols == expected:
            return True
    return False


def _validate_existing_table(conn, table, required_columns, unique_columns=None):
    if not _table_exists(conn, table):
        return
    columns = _table_columns(conn, table)
    missing = sorted(required_columns.difference(columns))
    if missing:
        raise SellersMigrationError(f"Schema parcial em {table}: colunas ausentes {', '.join(missing)}.")
    if unique_columns and not _has_unique_index(conn, table, unique_columns):
        raise SellersMigrationError(
            f"Schema parcial em {table}: UNIQUE({', '.join(unique_columns)}) ausente."
        )


def apply_sellers_schema(conn):
    """Runner oficial idempotente da migracao sellers/produtividade."""
    missing_base = [table for table in ("sales", "paladar_sales") if not _table_exists(conn, table)]
    if missing_base:
        raise SellersMigrationError(
            "Schema base ausente para sellers: " + ", ".join(missing_base) + "."
        )
    conn.execute("SAVEPOINT sellers_schema_migration")
    try:
        _validate_existing_table(conn, "sellers", SELLERS_COLUMNS, ("company_key", "normalized_name"))
        _validate_existing_table(conn, "seller_history", SELLER_HISTORY_COLUMNS)

        conn.execute(
            """CREATE TABLE IF NOT EXISTS sellers (
                id TEXT PRIMARY KEY,
                company_key TEXT NOT NULL,
                name TEXT NOT NULL,
                normalized_name TEXT NOT NULL,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT DEFAULT (datetime('now')),
                updated_at TEXT DEFAULT (datetime('now')),
                created_by TEXT,
                updated_by TEXT,
                UNIQUE(company_key, normalized_name)
            )"""
        )
        conn.execute(
            """CREATE TABLE IF NOT EXISTS seller_history (
                id TEXT PRIMARY KEY,
                seller_id TEXT NOT NULL,
                company_key TEXT NOT NULL,
                old_name TEXT,
                new_name TEXT NOT NULL,
                changed_by TEXT,
                changed_at TEXT DEFAULT (datetime('now')),
                reason TEXT,
                FOREIGN KEY(seller_id) REFERENCES sellers(id)
            )"""
        )
        for table in ("sales", "paladar_sales"):
            columns = _table_columns(conn, table)
            for col, typ in SALES_SELLER_COLUMNS.items():
                if col not in columns:
                    conn.execute(f"ALTER TABLE {table} ADD COLUMN {col} {typ}")
                    columns.add(col)

        conn.execute("CREATE INDEX IF NOT EXISTS idx_sellers_company_active ON sellers(company_key, active, name)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_seller_history_seller ON seller_history(seller_id, changed_at DESC)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_sales_seller_date ON sales(seller_id, sale_date)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_paladar_sales_seller_date ON paladar_sales(seller_id, saledate)")

        _validate_existing_table(conn, "sellers", SELLERS_COLUMNS, ("company_key", "normalized_name"))
        _validate_existing_table(conn, "seller_history", SELLER_HISTORY_COLUMNS)
        for table in ("sales", "paladar_sales"):
            missing = sorted(set(SALES_SELLER_COLUMNS).difference(_table_columns(conn, table)))
            if missing:
                raise SellersMigrationError(f"Schema parcial em {table}: colunas ausentes {', '.join(missing)}.")
        for index in (
            "idx_sellers_company_active",
            "idx_seller_history_seller",
            "idx_sales_seller_date",
            "idx_paladar_sales_seller_date",
        ):
            if not _index_exists(conn, index):
                raise SellersMigrationError(f"Indice ausente apos migracao sellers: {index}.")
        conn.execute("RELEASE SAVEPOINT sellers_schema_migration")
    except Exception as exc:
        conn.execute("ROLLBACK TO SAVEPOINT sellers_schema_migration")
        conn.execute("RELEASE SAVEPOINT sellers_schema_migration")
        if isinstance(exc, SellersMigrationError):
            raise
        raise SellersMigrationError(f"Falha ao aplicar schema sellers: {exc}") from exc


def init_sellers_schema(conn):
    apply_sellers_schema(conn)


def list_sellers(conn, company_key, include_inactive=False, search=""):
    sql = "SELECT * FROM sellers WHERE company_key=?"
    args = [company_key]
    if not include_inactive:
        sql += " AND active=1"
    if search:
        sql += " AND name LIKE ?"
        args.append(f"%{search}%")
    sql += " ORDER BY active DESC, name COLLATE NOCASE"
    return [dict(row) for row in conn.execute(sql, args).fetchall()]


def find_by_id(conn, company_key, seller_id):
    row = conn.execute(
        "SELECT * FROM sellers WHERE company_key=? AND id=?",
        (company_key, seller_id),
    ).fetchone()
    return dict(row) if row else None


def find_by_normalized(conn, company_key, normalized_name):
    row = conn.execute(
        "SELECT * FROM sellers WHERE company_key=? AND normalized_name=?",
        (company_key, normalized_name),
    ).fetchone()
    return dict(row) if row else None


def create_seller(conn, company_key, name, normalized_name, username):
    seller_id = str(uuid.uuid4())
    conn.execute(
        """INSERT INTO sellers(id,company_key,name,normalized_name,active,created_by,updated_by)
           VALUES(?,?,?,?,1,?,?)""",
        (seller_id, company_key, name, normalized_name, username, username),
    )
    return find_by_id(conn, company_key, seller_id)


def update_seller_name(conn, company_key, seller_id, name, normalized_name, username, reason=""):
    current = find_by_id(conn, company_key, seller_id)
    if not current:
        return None
    conn.execute(
        """UPDATE sellers SET name=?, normalized_name=?, updated_by=?, updated_at=datetime('now')
           WHERE company_key=? AND id=?""",
        (name, normalized_name, username, company_key, seller_id),
    )
    conn.execute(
        """INSERT INTO seller_history(id,seller_id,company_key,old_name,new_name,changed_by,reason)
           VALUES(?,?,?,?,?,?,?)""",
        (str(uuid.uuid4()), seller_id, company_key, current["name"], name, username, reason or ""),
    )
    return find_by_id(conn, company_key, seller_id)


def set_active(conn, company_key, seller_id, active, username):
    conn.execute(
        """UPDATE sellers SET active=?, updated_by=?, updated_at=datetime('now')
           WHERE company_key=? AND id=?""",
        (1 if active else 0, username, company_key, seller_id),
    )
    return find_by_id(conn, company_key, seller_id)


def seller_history(conn, company_key, seller_id):
    return [
        dict(row)
        for row in conn.execute(
            """SELECT * FROM seller_history
               WHERE company_key=? AND seller_id=?
               ORDER BY changed_at DESC, id DESC""",
            (company_key, seller_id),
        ).fetchall()
    ]


def sales_usage_count(conn, seller_id):
    total = 0
    for table in ("sales", "paladar_sales"):
        try:
            total += conn.execute(
                f"SELECT COUNT(*) FROM {table} WHERE seller_id=?",
                (seller_id,),
            ).fetchone()[0]
        except sqlite3.OperationalError:
            pass
    return total
