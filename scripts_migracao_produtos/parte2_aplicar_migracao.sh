#!/usr/bin/env bash
set -euo pipefail

# parte2_aplicar_migracao.sh
# Aplica migracao somente depois de comparar com a parte 1 e exigir confirmacao.
# Nao inicia/paralisa servicos, nao usa rede/SSH e nao toca em outros bancos.
#
# Uso:
#   ./parte2_aplicar_migracao.sh /caminho/real/bm_monteiro.db
#   DB_PATH=/caminho/real/bm_monteiro.db ./parte2_aplicar_migracao.sh

PY_TMP="$(mktemp)"
trap 'rm -f "$PY_TMP"' EXIT
cat > "$PY_TMP" <<'PY'
import os
import sys
import json
import sqlite3
import datetime
import traceback
import hashlib
from decimal import Decimal
from pathlib import Path

CONFIRMATION_TEXT = "APLICAR MIGRACAO PRODUTOS"
SAMPLE_LIMIT = 20
STATE_NAME = ".produto_mojibake_migracao_pre.json"

PRODUCTS = [
    "Macaxeira a V\u00e1cuo",
    "Pr\u00e9-Cozida",
    "Ab\u00f3bora Jacar\u00e9",
    "Ab\u00f3bora (vari\u00e1vel)",
]

# Variantes conhecidas pela auditoria, mas AINDA NAO confirmadas para migracao.
# Se qualquer uma existir no banco, esta parte 2 aborta antes de BEGIN/UPDATE.
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

# Colunas historicas com JSON/texto. Sao diagnosticadas e comparadas no
# snapshot, mas nao sao migradas e nao bloqueiam a migracao exata das colunas
# autorizadas. Nao usar REPLACE nelas.
INFORMATIONAL_TEXT_COLUMNS = {
    "audit_log": ["field_changed", "old_value", "new_value"],
}

TABLES = list(ALLOWED_PRODUCT_COLUMNS)

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
        raise SystemExit("ERRO: informe o banco: ./parte2_aplicar_migracao.sh /caminho/bm_monteiro.db")
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
    return [
        r[0] for r in conn.execute(
            f"SELECT DISTINCT {qident(col)} FROM {qident(table)} "
            f"WHERE {qident(col)} LIKE ? ESCAPE '\\' AND {qident(col)} <> ? LIMIT ?",
            ("%" + like_escape(term) + "%", term, SAMPLE_LIMIT),
        )
    ]

def authorized_diagnostics(conn, allowed):
    rows = []
    for table, cols in allowed.items():
        if not table_exists(conn, table):
            continue
        for col in cols:
            for bad, correct in REPLACEMENTS:
                exact_count = conn.execute(f"SELECT COUNT(*) FROM {qident(table)} WHERE {qident(col)} = ?", (bad,)).fetchone()[0]
                contained_count = conn.execute(
                    f"SELECT COUNT(*) FROM {qident(table)} WHERE {qident(col)} LIKE ? ESCAPE '\\' AND {qident(col)} <> ?",
                    ("%" + like_escape(bad) + "%", bad),
                ).fetchone()[0]
                correct_count = conn.execute(f"SELECT COUNT(*) FROM {qident(table)} WHERE {qident(col)} = ?", (correct,)).fetchone()[0]
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

def snapshot(conn, db_path):
    stat = db_path.stat()
    allowed, missing = allowed_columns_status(conn)
    return {
        "db_path": str(db_path),
        "db_size_bytes": stat.st_size,
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

def compare_subset(report):
    return {
        "db_path": report["db_path"],
        "products": report["products"],
        "replacements": report["replacements"],
        "audited_variants": report["audited_variants"],
        "unconfirmed_known_variants": report["unconfirmed_known_variants"],
        "allowed_product_columns_config": report["allowed_product_columns_config"],
        "informational_text_columns_config": report["informational_text_columns_config"],
        "allowed_product_columns_existing": report["allowed_product_columns_existing"],
        "missing_allowed_columns": report["missing_allowed_columns"],
        "schema": report["schema"],
        "integrity_check": report["integrity_check"],
        "row_counts": report["row_counts"],
        "table_digests": report["table_digests"],
        "authorized_diagnostics": report["authorized_diagnostics"],
        "out_of_scope_diagnostics": report["out_of_scope_diagnostics"],
        "informational_diagnostics": report["informational_diagnostics"],
        "known_unconfirmed_diagnostics": report["known_unconfirmed_diagnostics"],
        "sales_sums": report["sales_sums"],
    }

def combined_sales(rows):
    out = {}
    for r in rows:
        product = r["produto_canonico"]
        out.setdefault(product, {"linhas": 0, "soma_total_decimal": Decimal("0"), "soma_quantidade_decimal": Decimal("0")})
        out[product]["linhas"] += int(r["linhas"])
        out[product]["soma_total_decimal"] += Decimal(r["soma_total_decimal"])
        out[product]["soma_quantidade_decimal"] += Decimal(r["soma_quantidade_decimal"])
    return {
        product: {
            "linhas": values["linhas"],
            "soma_total_decimal": format(values["soma_total_decimal"], "f"),
            "soma_quantidade_decimal": format(values["soma_quantidade_decimal"], "f"),
        }
        for product, values in out.items()
    }

def authorized_count_errors(pre, post, phase):
    errors = []
    by_key = {
        (r["produto_canonico"], r["tabela"], r["coluna"]): r
        for r in post["authorized_diagnostics"]
    }
    for before in pre["authorized_diagnostics"]:
        key = (before["produto_canonico"], before["tabela"], before["coluna"])
        after = by_key.get(key)
        if after is None:
            errors.append(f"{phase}: diagnostico ausente para {key}")
            continue
        expected_correct = int(before["correto_exato"]) + int(before["mojibake_exato"])
        actual_correct = int(after["correto_exato"])
        actual_bad = int(after["mojibake_exato"])
        if actual_bad != 0:
            errors.append(f"{phase}: ainda ha {actual_bad} mojibake em {before['tabela']}.{before['coluna']} ({before['produto_canonico']})")
        if actual_correct != expected_correct:
            errors.append(
                f"{phase}: contagem unificada divergente em {before['tabela']}.{before['coluna']} "
                f"({before['produto_canonico']}): esperado={expected_correct} atual={actual_correct}"
            )
    return errors

def validation_errors(pre, post, phase):
    errors = []
    if post["integrity_check"] != "ok":
        errors.append(f"{phase}: integrity_check={post['integrity_check']}")
    if pre["row_counts"] != post["row_counts"]:
        errors.append(f"{phase}: total de linhas mudou")
    if post["missing_allowed_columns"]:
        errors.append(f"{phase}: ha tabela/coluna autorizada ausente")
    if post["out_of_scope_diagnostics"]:
        errors.append(f"{phase}: ha ocorrencias fora do escopo")
    if post["known_unconfirmed_diagnostics"]:
        errors.append(f"{phase}: ha variante mojibake conhecida sem destino confirmado")
    contained = [r for r in post["authorized_diagnostics"] if int(r["mojibake_contido_nao_exato"]) > 0]
    if contained:
        errors.append(f"{phase}: ha valores compostos em coluna autorizada; REPLACE nao e permitido")
    remaining = [r for r in post["authorized_diagnostics"] if int(r["mojibake_exato"]) > 0]
    if remaining:
        errors.append(f"{phase}: ainda ha mojibake exato nas colunas tratadas")
    errors.extend(authorized_count_errors(pre, post, phase))
    if not pre["sales_sums"]["available"] or not post["sales_sums"]["available"]:
        errors.append(f"{phase}: validacao monetaria/quantitativa de sales nao disponivel")
    else:
        pre_sum = combined_sales(pre["sales_sums"]["rows"])
        post_correct = combined_sales([r for r in post["sales_sums"]["rows"] if r["grafia"] == "correta"])
        if pre_sum != post_correct:
            errors.append(f"{phase}: somas/quantidades de sales divergiram: pre={pre_sum} pos={post_correct}")
    return errors

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

def abort(path, payload, message):
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(message)
    print(f"Relatorio: {path}")
    raise SystemExit(2)

db_path = require_db_path()
backup_dir = db_path.parent / "backups" / "produto_mojibake_migracao"
state_path = backup_dir / STATE_NAME
if not state_path.exists():
    raise SystemExit(f"ERRO: arquivo de estado da parte 1 nao encontrado: {state_path}")

pre_full = json.loads(state_path.read_text(encoding="utf-8"))
target_from_state = pre_full.get("target_db_path") or pre_full.get("db_path")
snapshot_from_state = pre_full.get("snapshot_db_path") or pre_full.get("backup_path")
if str(db_path) != target_from_state:
    raise SystemExit(f"ERRO: DB alvo difere da parte 1. parte1={target_from_state} atual={db_path}")
if not Path(pre_full.get("backup_path", "")).exists():
    raise SystemExit(f"ERRO: backup da parte 1 nao encontrado: {pre_full.get('backup_path')}")

ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
abort_report = backup_dir / f"migracao_abortada_{ts}.json"
post_report = backup_dir / f"pos_migracao_contagem_{ts}.json"

conn = sqlite3.connect(str(db_path), timeout=30)
try:
    current = snapshot(conn, db_path)
finally:
    conn.close()

pre_cmp = compare_subset(pre_full)
cur_cmp = compare_subset(current)
if pre_cmp != cur_cmp:
    abort(
        abort_report,
        {
            "motivo": "Banco ativo mudou depois do snapshot/backup da parte 1",
            "snapshot_analisado": snapshot_from_state,
            "banco_alvo": str(db_path),
            "backup_correspondente": pre_full.get("backup_path"),
            "backup_started_at": pre_full.get("backup_started_at"),
            "backup_finished_at": pre_full.get("backup_finished_at"),
            "banco_ativo_mudou_depois_do_snapshot": True,
            "parte1_snapshot": pre_cmp,
            "atual_banco_ativo": cur_cmp,
        },
        "O banco ativo mudou depois do snapshot da parte 1. Nenhum BEGIN/UPDATE foi executado.",
    )

if current["missing_allowed_columns"]:
    abort(abort_report, {"motivo": "Tabela/coluna autorizada ausente", "itens": current["missing_allowed_columns"]}, "Ha tabela/coluna autorizada ausente. Nenhuma alteracao sera feita.")

if current["out_of_scope_diagnostics"]:
    abort(abort_report, {"motivo": "Ocorrencias fora do escopo", "itens": current["out_of_scope_diagnostics"]}, "Ha ocorrencias fora do escopo. Nenhuma alteracao sera feita.")

if current["known_unconfirmed_diagnostics"]:
    abort(
        abort_report,
        {"motivo": "Variante mojibake conhecida sem destino confirmado", "itens": current["known_unconfirmed_diagnostics"]},
        "Ha variante mojibake conhecida sem destino confirmado. Nenhuma alteracao sera feita.",
    )

contained_before = [r for r in current["authorized_diagnostics"] if int(r["mojibake_contido_nao_exato"]) > 0]
if contained_before:
    abort(abort_report, {"motivo": "Valores compostos em coluna autorizada", "itens": contained_before}, "Ha valores compostos em coluna autorizada. REPLACE nao e autorizado. Nenhuma alteracao sera feita.")

if not current["sales_sums"]["available"]:
    abort(abort_report, {"motivo": "Validacao monetaria/quantitativa indisponivel", "sales_sums": current["sales_sums"]}, "Validacao de sales indisponivel. Nenhuma alteracao sera feita.")

print("ATENCAO: BEGIN IMMEDIATE bloqueara novas escritas enquanto a transacao estiver ativa.")
print("Tempo esperado em janela de baixo uso/manutencao: poucos segundos em bases normais.")
print("Nao rode se houver usuarios lancando vendas, boletos, avarias ou alterando produtos.")
print("\nAmostras que serao alteradas por correspondencia EXATA:")
for item in current["authorized_diagnostics"]:
    if int(item["mojibake_exato"]) > 0:
        print(f"- {item['tabela']}.{item['coluna']} | {item['produto_canonico']} | registros={item['mojibake_exato']} | amostras={item['amostras_mojibake_exato']}")
print("\nPara aplicar, digite exatamente:")
print(CONFIRMATION_TEXT)
if input("> ").strip() != CONFIRMATION_TEXT:
    raise SystemExit("Confirmacao incorreta. Nenhum UPDATE foi executado.")

conn = sqlite3.connect(str(db_path), timeout=30)
conn.isolation_level = None
committed = False
migration_log = []
inside = None
try:
    conn.execute("BEGIN IMMEDIATE")
    pre_inside = snapshot(conn, db_path)
    if compare_subset(pre_inside) != pre_cmp:
        raise RuntimeError("O banco mudou entre a confirmacao e o BEGIN IMMEDIATE")
    for table, cols in pre_inside["allowed_product_columns_existing"].items():
        for col in cols:
            for bad, correct in REPLACEMENTS:
                count = conn.execute(f"SELECT COUNT(*) FROM {qident(table)} WHERE {qident(col)} = ?", (bad,)).fetchone()[0]
                if count:
                    conn.execute(f"UPDATE {qident(table)} SET {qident(col)} = ? WHERE {qident(col)} = ?", (correct, bad))
                migration_log.append({
                    "tabela": table,
                    "coluna": col,
                    "produto": correct,
                    "modo": "EXATO",
                    "registros": count,
                    "from_escape": bad.encode("unicode_escape").decode("ascii"),
                    "to_escape": correct.encode("unicode_escape").decode("ascii"),
                })
    inside = snapshot(conn, db_path)
    errors = validation_errors(pre_inside, inside, "dentro_da_transacao")
    if errors:
        raise RuntimeError("; ".join(errors))
    conn.execute("COMMIT")
    committed = True
except Exception as exc:
    if not committed:
        try:
            conn.execute("ROLLBACK")
        except Exception:
            pass
    abort_report.write_text(json.dumps({
        "motivo": "Falha durante migracao",
        "committed": committed,
        "erro": str(exc),
        "traceback": traceback.format_exc(),
        "migration_log": migration_log,
        "inside_validation": inside,
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    conn.close()
    print("Migracao abortada. Se COMMIT nao ocorreu, ROLLBACK foi solicitado.")
    print(f"Relatorio: {abort_report}")
    raise
else:
    conn.close()

conn = sqlite3.connect(str(db_path), timeout=30)
try:
    after = snapshot(conn, db_path)
finally:
    conn.close()

post_errors = validation_errors(current, after, "depois_do_commit")
post_report.write_text(json.dumps({
    "committed": committed,
    "snapshot_analisado": snapshot_from_state,
    "banco_alvo": str(db_path),
    "backup_path": pre_full.get("backup_path"),
    "backup_started_at": pre_full.get("backup_started_at"),
    "backup_finished_at": pre_full.get("backup_finished_at"),
    "banco_ativo_mudou_depois_do_snapshot": False,
    "migration_log": migration_log,
    "validation_inside_transaction": inside,
    "validation_after_commit": after,
    "errors_after_commit": post_errors,
}, ensure_ascii=False, indent=2), encoding="utf-8")

print_table("Updates aplicados", migration_log, ["tabela", "coluna", "produto", "modo", "registros", "from_escape", "to_escape"])
print(f"Relatorio POS: {post_report}")
if post_errors:
    print("Validacao depois do COMMIT falhou. Nao restaure backup automaticamente sem autorizacao.")
    for err in post_errors:
        print(f"- {err}")
    raise SystemExit(4)
print("VALIDACAO OK: transacao unica, correspondencia EXATA, linhas e somas preservadas.")
PY
python3 "$PY_TMP" "$@"
