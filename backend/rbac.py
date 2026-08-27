import hashlib
import re
import unicodedata
from datetime import datetime


AREA_MODULES = {
    "menina_dos_raios": [
        "consolidado", "nf", "pr", "avulso", "avaria", "projecao",
        "grafico", "produtividade", "clientes", "boletos", "pendentes",
        "produtos", "config", "cargos",
    ],
    "monteiro": [
        "painel", "lancamentos", "produtos", "clientes", "pagamentos",
        "notas_app", "calendario", "dados",
    ],
    "menina_da_estrada": [
        "consolidado", "nf", "avulso", "avaria", "projecao", "grafico",
        "produtividade", "clientes", "boletos", "pendentes", "produtos",
        "config", "cargos",
    ],
}

ACTIONS = ("view", "create", "edit", "delete", "export", "import", "approve", "configure")


def normalize_product_key(value):
    text = unicodedata.normalize("NFKD", str(value or ""))
    text = "".join(ch for ch in text if not unicodedata.combining(ch)).upper()
    return re.sub(r"[^A-Z0-9]+", "_", text).strip("_")


def stable_product_id(product_key):
    digest = hashlib.sha256(normalize_product_key(product_key).encode("utf-8")).hexdigest()[:24]
    return f"product_{digest}"


def init_rbac_schema(conn):
    conn.executescript(
        """
        CREATE TABLE IF NOT EXISTS roles (
            id TEXT PRIMARY KEY,
            key TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            description TEXT,
            active INTEGER NOT NULL DEFAULT 1,
            is_system INTEGER NOT NULL DEFAULT 0,
            product_scope_mode TEXT NOT NULL DEFAULT 'all' CHECK(product_scope_mode IN ('all','specific')),
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS role_area_permissions (
            role_id TEXT NOT NULL,
            area_key TEXT NOT NULL,
            can_view INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(role_id, area_key),
            FOREIGN KEY(role_id) REFERENCES roles(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS role_module_permissions (
            role_id TEXT NOT NULL,
            area_key TEXT NOT NULL,
            module_key TEXT NOT NULL,
            can_view INTEGER NOT NULL DEFAULT 0,
            can_create INTEGER NOT NULL DEFAULT 0,
            can_edit INTEGER NOT NULL DEFAULT 0,
            can_delete INTEGER NOT NULL DEFAULT 0,
            can_export INTEGER NOT NULL DEFAULT 0,
            can_import INTEGER NOT NULL DEFAULT 0,
            can_approve INTEGER NOT NULL DEFAULT 0,
            can_configure INTEGER NOT NULL DEFAULT 0,
            sort_order INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(role_id, area_key, module_key),
            FOREIGN KEY(role_id) REFERENCES roles(id) ON DELETE CASCADE
        );
        CREATE TABLE IF NOT EXISTS permission_products (
            id TEXT PRIMARY KEY,
            product_key TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL DEFAULT (datetime('now')),
            updated_at TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS role_product_permissions (
            role_id TEXT NOT NULL,
            product_id TEXT NOT NULL,
            can_view INTEGER NOT NULL DEFAULT 0,
            can_create INTEGER NOT NULL DEFAULT 0,
            can_edit INTEGER NOT NULL DEFAULT 0,
            can_delete INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY(role_id, product_id),
            FOREIGN KEY(role_id) REFERENCES roles(id) ON DELETE CASCADE,
            FOREIGN KEY(product_id) REFERENCES permission_products(id) ON DELETE CASCADE
        );
        CREATE INDEX IF NOT EXISTS idx_role_modules_role ON role_module_permissions(role_id, area_key);
        CREATE INDEX IF NOT EXISTS idx_role_products_role ON role_product_permissions(role_id, can_view);
        """
    )


def ensure_permission_product(conn, name, product_key=None):
    clean_name = re.sub(r"\s+", " ", str(name or "").strip())
    key = normalize_product_key(product_key or clean_name)
    if not key or not clean_name:
        return None
    product_id = stable_product_id(key)
    conn.execute(
        """INSERT INTO permission_products(id,product_key,name,active)
           VALUES(?,?,?,1)
           ON CONFLICT(product_key) DO UPDATE SET
             name=excluded.name,active=1,updated_at=datetime('now')""",
        (product_id, key, clean_name),
    )
    return product_id


def seed_rbac_defaults(conn):
    init_rbac_schema(conn)
    conn.execute(
        """INSERT OR IGNORE INTO roles(id,key,name,description,active,is_system,product_scope_mode)
           VALUES('role_admin','admin','Administrador','Acesso total ao sistema.',1,1,'all')"""
    )
    cliente_exists = conn.execute("SELECT 1 FROM roles WHERE key='cliente'").fetchone()
    if not cliente_exists:
        conn.execute(
            """INSERT INTO roles(id,key,name,description,active,is_system,product_scope_mode)
               VALUES('role_cliente','cliente','Cliente',
               'Acesso restrito a Menina da Estrada, com modulos e produtos definidos pelo administrador.',
               1,1,'specific')"""
        )
        conn.execute(
            """INSERT INTO role_area_permissions(role_id,area_key,can_view)
               VALUES('role_cliente','menina_da_estrada',1)"""
        )
        for order, module_key in enumerate(("produtos", "consolidado")):
            conn.execute(
                """INSERT INTO role_module_permissions(
                       role_id,area_key,module_key,can_view,sort_order)
                   VALUES('role_cliente','menina_da_estrada',?,1,?)""",
                (module_key, order),
            )
        for name in ("Uva Vit\u00f3ria", "Uva Vit\u00f3ria 250g"):
            product_id = ensure_permission_product(conn, name)
            conn.execute(
                """INSERT INTO role_product_permissions(role_id,product_id,can_view)
                   VALUES('role_cliente',?,1)""",
                (product_id,),
            )


def role_context_from_db(conn, role_key):
    role = conn.execute("SELECT * FROM roles WHERE key=? AND active=1", (role_key,)).fetchone()
    if not role:
        return {"managed": False, "role": {"key": role_key, "name": role_key}}
    role = dict(role)
    if role_key == "admin":
        return {
            "managed": True,
            "role": {"key": "admin", "name": role["name"]},
            "default_route": {"area": "menina_dos_raios", "module": "consolidado"},
            "areas": {key: True for key in AREA_MODULES},
            "modules": {
                area: {module: {action: True for action in ACTIONS} for module in modules}
                for area, modules in AREA_MODULES.items()
            },
            "product_scope": {"mode": "all", "allowed_product_ids": []},
        }
    areas = {
        row["area_key"]: bool(row["can_view"])
        for row in conn.execute(
            "SELECT area_key,can_view FROM role_area_permissions WHERE role_id=? AND can_view=1",
            (role["id"],),
        ).fetchall()
    }
    modules = {}
    rows = conn.execute(
        """SELECT * FROM role_module_permissions
           WHERE role_id=? AND can_view=1 ORDER BY sort_order,module_key""",
        (role["id"],),
    ).fetchall()
    for row in rows:
        item = dict(row)
        area_key = item["area_key"]
        modules.setdefault(area_key, {})[item["module_key"]] = {
            action: bool(item[f"can_{action}"]) for action in ACTIONS
        }
    default_area = next((key for key in AREA_MODULES if areas.get(key) and modules.get(key)), "")
    default_module = next(iter(modules.get(default_area, {})), "")
    products = conn.execute(
        """SELECT p.id,p.product_key,p.name,rp.can_view,rp.can_create,rp.can_edit,rp.can_delete
           FROM role_product_permissions rp
           JOIN permission_products p ON p.id=rp.product_id
           WHERE rp.role_id=? AND p.active=1 AND rp.can_view=1 ORDER BY p.name""",
        (role["id"],),
    ).fetchall()
    return {
        "managed": True,
        "role": {"key": role["key"], "name": role["name"]},
        "default_route": {"area": default_area, "module": default_module},
        "areas": areas,
        "modules": modules,
        "product_scope": {
            "mode": role["product_scope_mode"],
            "allowed_product_ids": [row["id"] for row in products],
            "products": [dict(row) for row in products],
        },
    }


def role_has_permission(context, area_key, module_key, action="view"):
    if not context.get("managed"):
        return True
    if context.get("role", {}).get("key") == "admin":
        return True
    if not context.get("areas", {}).get(area_key):
        return False
    return bool(context.get("modules", {}).get(area_key, {}).get(module_key, {}).get(action))


def allowed_product_keys(context, action="view"):
    if not context.get("managed"):
        return None
    scope = context.get("product_scope", {})
    if scope.get("mode") == "all":
        return None
    field = f"can_{action}"
    return {row["product_key"] for row in scope.get("products", []) if row.get(field)}


def filter_records_by_product(context, records, field="product", action="view"):
    allowed = allowed_product_keys(context, action=action)
    if allowed is None:
        return list(records)
    return [row for row in records if normalize_product_key(row.get(field)) in allowed]
