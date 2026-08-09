#!/usr/bin/env bash
set -euo pipefail

# parte1_backup_e_diagnostico.sh
# Leitura/backup apenas. Nao executa UPDATE, INSERT, DELETE, DROP ou VACUUM.
# Uso:
#   ./parte1_backup_e_diagnostico.sh /caminho/real/bm_monteiro.db
#   DB_PATH=/caminho/real/bm_monteiro.db ./parte1_backup_e_diagnostico.sh

PY_TMP="$(mktemp)"
trap 'rm -f "$PY_TMP"' EXIT
cat > "$PY_TMP" <<'PY'
import os
import sys
import json
import sqlite3
import datetime
import hashlib
from decimal import Decimal
from pathlib import Path

PRODUCTS = [
    "Macaxeira a V\u00e1cuo",
    "Pr\u00e9-Cozida",
    "Ab\u00f3bora Jacar\u00e9",
    "Ab\u00f3bora (vari\u00e1vel)",
]

# Variantes conhecidas pela auditoria, mas AINDA NAO confirmadas para migracao.
# A parte 1 apenas relata ocorrencias e destino proposto. A parte 2 aborta se
# encontrar qualquer uma delas, antes de BEGIN/UPDATE.
UNCONFIRMED_KNOWN_VARIANTS = [
    {"variant": "MACAXEIRA A V\u00c3\u0081CUO", "proposed_target": "Macaxeira a V\u00e1cuo", "status": "NAO_CONFIRMADA"},
    {"variant": "PR\u00c3\u0089 COZIDA", "proposed_target": "Pr\u00e9-Cozida", "status": "NAO_CONFIRMADA"},
    {"variant": "AB\u00c3\u0093BORA JACAR\u00c3\u0089", "proposed_target": "Ab\u00f3bora Jacar\u00e9", "status": "NAO_CONFIRMADA"},
    {"variant": "AB\u00c3\u0093BORA", "proposed_target": "Ab\u00f3bora", "status": "NAO_CONFIRMADA"},
]

ALLOWED_PRODUCT_COLUMNS = {
    "sales": ["product"],
    "price_history": ["key"],
    "product_prices": ["key", "label"],
    "audit_log": ["product_label"],
}

# Colunas de auditoria com JSON/texto historico. Elas sao diagnosticadas para
# transparencia, mas nao sao migradas e nao bloqueiam a migracao dos dados
# principais. Nao usar REPLACE nelas.
INFORMATIONAL_TEXT_COLUMNS = {
    "audit_log": ["field_changed", "old_value", "new_value"],
}

STATE_NAME = ".produto_mojibake_migracao_pre.json"
TABLES = list(ALLOWED_PRODUCT_COLUMNS)
SAMPLE_LIMIT = 20

def mojibake(text: str) -> str:
    return text.encode("utf-8").decode("latin1")

REPLACEMENTS = sorted(
    dict.fromkeys((mojibake(correct), correct) for correct in PRODUCTS if mojibake(correct) != correct),
    key=lambda pair: len(pair[0]),
    reverse=True,
)

AUDITED_VARIANTS = [
    {"variant": bad, "target": correct, "status": "CONFIRMADA", "source": "mojibake_gerado"}
    for bad, correct in REPLACEMENTS
] + [
    {"variant": item["variant"], "target": item["proposed_target"], "status": item["status"], "source": "auditoria_maiuscula"}
    for item in UNCONFIRMED_KNOWN_VARIANTS
]

def qident(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'

def like_escape(value: str) -> str:
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")

def require_db_path() -> Path:
    supplied = sys.argv[1] if len(sys.argv) > 1 else os.environ.get("DB_PATH", "")
    if not supplied:
        raise SystemExit("ERRO: informe o banco: ./parte1_backup_e_diagnostico.sh /caminho/bm_monteiro.db")
    path = Path(supplied).expanduser().resolve()
    if not path.exists() or not path.is_file():
        raise SystemExit(f"ERRO: caminho invalido: {path}")
    if path.name != "bm_monteiro.db":
        raise SystemExit(f"ERRO: o arquivo precisa se chamar bm_monteiro.db: {path}")
    return path

def table_exists(conn, table):
    return conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone() is not None

def table_info(conn, table):
    if not table_exists(conn, table):
        return []
    return [
        {"cid": r[0], "name": r[1], "type": r[2], "notnull": r[3], "default": r[4], "pk": r[5]}
        for r in conn.execute(f"PRAGMA table_info({qident(table)})")
    ]

def table_columns(conn, table):
    return [r["name"] for r in table_info(conn, table)]

def text_columns(conn, table):
    cols = []
    for r in table_info(conn, table):
        typ = (r["type"] or "").upper()
        if typ == "" or "TEXT" in typ or "CHAR" in typ or "CLOB" in typ or "VARCHAR" in typ:
            cols.append(r["name"])
    return cols

def schema_snapshot(conn):
    return {table: table_info(conn, table) for table in TABLES}

def normalize_cell(value):
    if isinstance(value, bytes):
        return {"__bytes__": value.hex()}
    return value

def table_digest(conn, table):
    if not table_exists(conn, table):
        return {"exists": False, "rows": "TABELA_AUSENTE", "sha256": None}
    cols = table_columns(conn, table)
    if not cols:
        return {"exists": True, "rows": 0, "sha256": hashlib.sha256(b"").hexdigest()}
    order_cols = [r["name"] for r in table_info(conn, table) if r["pk"]]
    order_sql = ", ".join(qident(c) for c in order_cols) if order_cols else "rowid"
    sql = f"SELECT {', '.join(qident(c) for c in cols)} FROM {qident(table)} ORDER BY {order_sql}"
    fallback_sql = f"SELECT {', '.join(qident(c) for c in cols)} FROM {qident(table)} ORDER BY {', '.join(qident(c) for c in cols)}"
    digest = hashlib.sha256()
    count = 0
    try:
        cursor = conn.execute(sql)
    except sqlite3.OperationalError:
        cursor = conn.execute(fallback_sql)
    for row in cursor:
        count += 1
        payload = json.dumps([normalize_cell(v) for v in row], ensure_ascii=False, sort_keys=True, separators=(",", ":"))
        digest.update(payload.encode("utf-8"))
        digest.update(b"\n")
    return {"exists": True, "rows": count, "sha256": digest.hexdigest()}

def table_digests(conn):
    return {table: table_digest(conn, table) for table in TABLES}

def allowed_columns_status(conn):
    existing = {}
    missing = []
    for table, cols in ALLOWED_PRODUCT_COLUMNS.items():
        available = set(table_columns(conn, table))
        existing[table] = []
        if not table_exists(conn, table):
            missing.append({"tabela": table, "coluna": "*", "motivo": "tabela ausente"})
            continue
        for col in cols:
            if col in available:
                existing[table].append(col)
            else:
                missing.append({"tabela": table, "coluna": col, "motivo": "coluna ausente"})
    return existing, missing

def row_counts(conn):
    out = {}
    for table in TABLES:
        out[table] = conn.execute(f"SELECT COUNT(*) FROM {qident(table)}").fetchone()[0] if table_exists(conn, table) else "TABELA_AUSENTE"
    return out

def decimal_sum(conn, table, col, where_col, term):
    if col not in table_columns(conn, table):
        return None
    rows = conn.execute(f"SELECT {qident(col)} FROM {qident(table)} WHERE {qident(where_col)} = ?", (term,)).fetchall()
    total = Decimal("0")
    for (value,) in rows:
        if value is not None:
            total += Decimal(str(value))
    return format(total, "f")

def sales_sums(conn):
    if not table_exists(conn, "sales"):
        return {"available": False, "reason": "tabela sales ausente", "rows": []}
    cols = set(table_columns(conn, "sales"))
    missing = [col for col in ("product", "total", "quantity") if col not in cols]
    if missing:
        return {"available": False, "reason": "colunas ausentes: " + ", ".join(missing), "rows": []}
    rows = []
    for bad, correct in REPLACEMENTS:
        for form, term in [("mojibake", bad), ("correta", correct)]:
            count = conn.execute('SELECT COUNT(*) FROM "sales" WHERE "product" = ?', (term,)).fetchone()[0]
            rows.append({
                "produto_canonico": correct,
                "grafia": form,
                "linhas": count,
                "soma_total_decimal": decimal_sum(conn, "sales", "total", "product", term),
                "soma_quantidade_decimal": decimal_sum(conn, "sales", "quantity", "product", term),
            })
    return {"available": True, "reason": "ok", "rows": rows}

def samples_exact(conn, table, col, term):
    return [
        r[0] for r in conn.execute(
            f"SELECT DISTINCT {qident(col)} FROM {qident(table)} WHERE {qident(col)} = ? LIMIT ?",
            (term, SAMPLE_LIMIT),
        )
    ]

def samples_contained_not_exact(conn, table, col, term):
    pattern = "%" + like_escape(term) + "%"
    return [
        r[0] for r in conn.execute(
            f"SELECT DISTINCT {qident(col)} FROM {qident(table)} "
            f"WHERE {qident(col)} LIKE ? ESCAPE '\\' AND {qident(col)} <> ? LIMIT ?",
            (pattern, term, SAMPLE_LIMIT),
        )
    ]

def authorized_diagnostics(conn, allowed):
    rows = []
    for table, cols in allowed.items():
        if not table_exists(conn, table):
            continue
        for col in cols:
            for bad, correct in REPLACEMENTS:
                exact_count = conn.execute(
                    f"SELECT COUNT(*) FROM {qident(table)} WHERE {qident(col)} = ?",
                    (bad,),
                ).fetchone()[0]
                contained_count = conn.execute(
                    f"SELECT COUNT(*) FROM {qident(table)} WHERE {qident(col)} LIKE ? ESCAPE '\\' AND {qident(col)} <> ?",
                    ("%" + like_escape(bad) + "%", bad),
                ).fetchone()[0]
                correct_count = conn.execute(
                    f"SELECT COUNT(*) FROM {qident(table)} WHERE {qident(col)} = ?",
                    (correct,),
                ).fetchone()[0]
                rows.append({
                    "produto_canonico": correct,
                    "tabela": table,
                    "coluna": col,
                    "modo_autorizado": "EXATO",
                    "mojibake_exato": exact_count,
                    "mojibake_contido_nao_exato": contained_count,
                    "correto_exato": correct_count,
                    "amostras_mojibake_exato": samples_exact(conn, table, col, bad),
                    "amostras_mojibake_contido_nao_exato": samples_contained_not_exact(conn, table, col, bad),
                })
    return rows

def out_of_scope_diagnostics(conn, allowed):
    rows = []
    for table in TABLES:
        if not table_exists(conn, table):
            continue
        allowed_set = set(allowed.get(table, []))
        informational_set = set(INFORMATIONAL_TEXT_COLUMNS.get(table, []))
        for col in text_columns(conn, table):
            if col in allowed_set or col in informational_set:
                continue
            for bad, correct in REPLACEMENTS:
                count = conn.execute(
                    f"SELECT COUNT(*) FROM {qident(table)} WHERE {qident(col)} LIKE ? ESCAPE '\\'",
                    ("%" + like_escape(bad) + "%",),
                ).fetchone()[0]
                if count:
                    rows.append({
                        "produto_canonico": correct,
                        "tabela": table,
                        "coluna": col,
                        "ocorrencias": count,
                        "amostras": [
                            r[0] for r in conn.execute(
                                f"SELECT DISTINCT {qident(col)} FROM {qident(table)} WHERE {qident(col)} LIKE ? ESCAPE '\\' LIMIT ?",
                                ("%" + like_escape(bad) + "%", SAMPLE_LIMIT),
                            )
                        ],
                    })
    return rows

def informational_diagnostics(conn):
    rows = []
    for table, cols in INFORMATIONAL_TEXT_COLUMNS.items():
        if not table_exists(conn, table):
            continue
        available = set(table_columns(conn, table))
        for col in cols:
            if col not in available:
                rows.append({
                    "tabela": table,
                    "coluna": col,
                    "status": "coluna ausente",
                    "produto_canonico": "",
                    "ocorrencias": 0,
                    "amostras": [],
                })
                continue
            for bad, correct in REPLACEMENTS:
                count = conn.execute(
                    f"SELECT COUNT(*) FROM {qident(table)} WHERE {qident(col)} LIKE ? ESCAPE '\\'",
                    ("%" + like_escape(bad) + "%",),
                ).fetchone()[0]
                if count:
                    rows.append({
                        "tabela": table,
                        "coluna": col,
                        "status": "informativo_nao_migrar",
                        "produto_canonico": correct,
                        "ocorrencias": count,
                        "amostras": [
                            r[0] for r in conn.execute(
                                f"SELECT DISTINCT {qident(col)} FROM {qident(table)} WHERE {qident(col)} LIKE ? ESCAPE '\\' LIMIT ?",
                                ("%" + like_escape(bad) + "%", SAMPLE_LIMIT),
                            )
                        ],
                    })
    return rows

def known_unconfirmed_diagnostics(conn):
    rows = []
    for table in TABLES:
        if not table_exists(conn, table):
            continue
        for col in text_columns(conn, table):
            for item in UNCONFIRMED_KNOWN_VARIANTS:
                term = item["variant"]
                count = conn.execute(
                    f"SELECT COUNT(*) FROM {qident(table)} WHERE {qident(col)} = ?",
                    (term,),
                ).fetchone()[0]
                contained = conn.execute(
                    f"SELECT COUNT(*) FROM {qident(table)} WHERE {qident(col)} LIKE ? ESCAPE '\\' AND {qident(col)} <> ?",
                    ("%" + like_escape(term) + "%", term),
                ).fetchone()[0]
                if count or contained:
                    samples = [
                        r[0] for r in conn.execute(
                            f"SELECT DISTINCT {qident(col)} FROM {qident(table)} "
                            f"WHERE {qident(col)} LIKE ? ESCAPE '\\' LIMIT ?",
                            ("%" + like_escape(term) + "%", SAMPLE_LIMIT),
                        )
                    ]
                    rows.append({
                        "variant_escape": term.encode("unicode_escape").decode("ascii"),
                        "variant_text": term,
                        "destino_proposto": item["proposed_target"],
                        "status": item["status"],
                        "tabela": table,
                        "coluna": col,
                        "exato": count,
                        "contido_nao_exato": contained,
                        "amostras": samples,
                    })
    return rows

def print_table(title, rows, cols):
    print("\n" + title)
    print("=" * len(title))
    if not rows:
        print("(sem registros)")
        return
    widths = {c: max(len(c), *(len(str(r.get(c, ""))) for r in rows)) for c in cols}
    print(" | ".join(c.ljust(widths[c]) for c in cols))
    print("-+-".join("-" * widths[c] for c in cols))
    for r in rows:
        print(" | ".join(str(r.get(c, "")).ljust(widths[c]) for c in cols))

db_path = require_db_path()
active_stat_before = db_path.stat()
backup_dir = db_path.parent / "backups" / "produto_mojibake_migracao"
backup_dir.mkdir(parents=True, exist_ok=True)
ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
backup_path = backup_dir / f"bm_monteiro_PRE_MIGRACAO_PROD_{ts}.db"
state_path = backup_dir / STATE_NAME
report_path = backup_dir / f"pre_migracao_contagem_{ts}.json"
backup_started_at = datetime.datetime.now().isoformat(timespec="seconds")

src = sqlite3.connect(str(db_path))
dst = sqlite3.connect(str(backup_path))
try:
    src.backup(dst)
finally:
    dst.close()
backup_finished_at = datetime.datetime.now().isoformat(timespec="seconds")
src.close()

bak = sqlite3.connect(str(backup_path))
try:
    integrity_bak = bak.execute("PRAGMA integrity_check").fetchone()[0]
    bak_counts = row_counts(bak)
finally:
    bak.close()

if integrity_bak != "ok":
    raise SystemExit(f"ERRO: integrity_check do backup falhou. backup={integrity_bak}")

backup_stat = backup_path.stat()
conn = sqlite3.connect(str(backup_path))
try:
    allowed, missing = allowed_columns_status(conn)
    report = {
        "timestamp": ts,
        "snapshot_source": "backup_sqlite_api",
        "db_path": str(db_path),
        "db_size_bytes": backup_stat.st_size,
        "snapshot_db_path": str(backup_path),
        "target_db_path": str(db_path),
        "target_db_size_bytes_at_backup_start": active_stat_before.st_size,
        "backup_db_size_bytes": backup_stat.st_size,
        "backup_path": str(backup_path),
        "backup_started_at": backup_started_at,
        "backup_finished_at": backup_finished_at,
        "diagnostic_calculated_from": str(backup_path),
        "products": PRODUCTS,
        "replacements": [
            {"from_escape": bad.encode("unicode_escape").decode("ascii"), "to_escape": correct.encode("unicode_escape").decode("ascii")}
            for bad, correct in REPLACEMENTS
        ],
        "audited_variants": [
            {
                "variant_escape": item["variant"].encode("unicode_escape").decode("ascii"),
                "target": item["target"],
                "status": item["status"],
                "source": item["source"],
            }
            for item in AUDITED_VARIANTS
        ],
        "unconfirmed_known_variants": [
            {
                "variant_escape": item["variant"].encode("unicode_escape").decode("ascii"),
                "proposed_target": item["proposed_target"],
                "status": item["status"],
            }
            for item in UNCONFIRMED_KNOWN_VARIANTS
        ],
        "allowed_product_columns_config": ALLOWED_PRODUCT_COLUMNS,
        "informational_text_columns_config": INFORMATIONAL_TEXT_COLUMNS,
        "allowed_product_columns_existing": allowed,
        "missing_allowed_columns": missing,
        "schema": schema_snapshot(conn),
        "integrity_check": conn.execute("PRAGMA integrity_check").fetchone()[0],
        "row_counts": row_counts(conn),
        "table_digests": table_digests(conn),
        "authorized_diagnostics": authorized_diagnostics(conn, allowed),
        "out_of_scope_diagnostics": out_of_scope_diagnostics(conn, allowed),
        "informational_diagnostics": informational_diagnostics(conn),
        "known_unconfirmed_diagnostics": known_unconfirmed_diagnostics(conn),
        "sales_sums": sales_sums(conn),
    }
finally:
    conn.close()

state_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"Banco alvo da futura migracao: {db_path}")
print(f"Snapshot analisado: {backup_path}")
print(f"Backup criado e validado: {backup_path}")
print(f"Backup inicio: {backup_started_at}")
print(f"Backup fim: {backup_finished_at}")
print(f"Estado salvo: {state_path}")
print(f"Relatorio PRE: {report_path}")
print_table("Colunas autorizadas ausentes", missing, ["tabela", "coluna", "motivo"])
print_table(
    "Diagnostico autorizado PRE",
    report["authorized_diagnostics"],
    ["produto_canonico", "tabela", "coluna", "modo_autorizado", "mojibake_exato", "mojibake_contido_nao_exato", "correto_exato"],
)
print_table(
    "Ocorrencias fora do escopo PRE",
    report["out_of_scope_diagnostics"],
    ["produto_canonico", "tabela", "coluna", "ocorrencias", "amostras"],
)
print_table(
    "Ocorrencias informativas nao migradas PRE",
    report["informational_diagnostics"],
    ["produto_canonico", "tabela", "coluna", "status", "ocorrencias", "amostras"],
)
print_table(
    "Variantes conhecidas NAO confirmadas PRE",
    report["known_unconfirmed_diagnostics"],
    ["variant_escape", "destino_proposto", "status", "tabela", "coluna", "exato", "contido_nao_exato", "amostras"],
)
print("\nSales sums:")
print(json.dumps(report["sales_sums"], ensure_ascii=False, indent=2))
print("\nPARE AQUI. Revise o relatorio antes de qualquer execucao da parte 2.")
PY
python3 "$PY_TMP" "$@"
