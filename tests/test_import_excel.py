import sqlite3
from datetime import datetime
from io import BytesIO

import pandas as pd
import pytest


def _login(test_client, username="admin", password="admin123", company="raios"):
    response = test_client.post(
        "/api/auth/login",
        headers={"x-company": company},
        json={"username": username, "password": password},
    )
    assert response.status_code == 200
    return response.json()["token"]


def _headers(token, company="raios"):
    return {"x-token": token, "x-company": company}


def _xlsx_bytes(rows, sheet_name="NF TESTE"):
    data = BytesIO()
    with pd.ExcelWriter(data, engine="openpyxl") as writer:
        pd.DataFrame(rows).to_excel(writer, sheet_name=sheet_name, header=False, index=False)
    data.seek(0)
    return data.getvalue()


def _post_import(test_client, token, rows, filename="import_teste.xlsx"):
    return test_client.post(
        "/api/import-excel",
        headers=_headers(token),
        files={
            "file": (
                filename,
                _xlsx_bytes(rows),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )


def _post_import_bytes(test_client, token, content, filename="import_teste.xlsx"):
    return test_client.post(
        "/api/import-excel",
        headers=_headers(token),
        files={
            "file": (
                filename,
                content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )


def _fetch_one(db_path, sql, args=()):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        row = conn.execute(sql, args).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def _fetch_all(db_path, sql, args=()):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in conn.execute(sql, args).fetchall()]
    finally:
        conn.close()


class _ImportFailureConnection:
    def __init__(self, inner, fail_at):
        self.inner = inner
        self.fail_at = fail_at
        self.sales_attempts = 0
        self.import_write_started = False
        self.rollback_count = 0
        self.close_count = 0

    def execute(self, sql, args=()):
        normalized = " ".join(str(sql).split()).upper()
        if normalized.startswith("INSERT INTO SALES"):
            self.import_write_started = True
            self.sales_attempts += 1
            if self.fail_at == "sales_second" and self.sales_attempts == 2:
                raise RuntimeError("falha sales passo 125")
        if normalized.startswith("INSERT INTO IMPORT_LOG"):
            self.import_write_started = True
            if self.fail_at == "import_log":
                raise RuntimeError("falha import_log passo 125")
        return self.inner.execute(sql, args)

    def commit(self):
        if self.fail_at == "commit" and self.import_write_started:
            raise RuntimeError("falha commit passo 125")
        return self.inner.commit()

    def rollback(self):
        self.rollback_count += 1
        return self.inner.rollback()

    def close(self):
        self.close_count += 1
        return self.inner.close()

    def __getattr__(self, name):
        return getattr(self.inner, name)


def _install_import_failure(isolated_app, monkeypatch, fail_at):
    real_get_db = isolated_app.module.get_db
    state = {"connections": [], "real_get_db": real_get_db}

    def fake_get_db(company=None):
        conn = _ImportFailureConnection(real_get_db(company), fail_at)
        state["connections"].append(conn)
        return conn

    monkeypatch.setattr(isolated_app.module, "get_db", fake_get_db)
    return state


def _target_import_connection(state):
    matches = [conn for conn in state["connections"] if conn.import_write_started]
    assert len(matches) == 1
    return matches[0]


def _assert_import_failure_rolled_back(isolated_app, monkeypatch, state, token):
    target = _target_import_connection(state)
    assert target.rollback_count == 1
    assert target.close_count == 1
    assert _fetch_one(
        isolated_app.db_paths["raios"],
        "SELECT COUNT(*) AS total FROM sales WHERE source='excel'",
    ) == {"total": 0}
    assert _fetch_one(
        isolated_app.db_paths["raios"],
        "SELECT COUNT(*) AS total FROM import_log",
    ) == {"total": 0}

    monkeypatch.setattr(isolated_app.module, "get_db", state["real_get_db"])
    follow_up_write = isolated_app.client.post(
        "/api/sales",
        headers=_headers(token),
        json={
            "sale_type": "NF",
            "sale_date": "2026-08-04",
            "client": "Cliente Escrita Posterior",
            "product": "Produto Escrita Posterior",
            "quantity": 1,
            "unit_price": 7,
            "total": 7,
        },
    )
    assert follow_up_write.status_code == 200


def test_import_excel_valid_sheet_persists_sales_and_log(isolated_app):
    token = _login(isolated_app.client)
    rows = [
        ["", "DATA", "CLIENTE", "PRODUTO", "NF", "QT", "P.UNIT", "TOTAL", "ENTREGADOR"],
        ["", datetime(2026, 8, 1), "Cliente Import A", "Produto Import A", 101, 2, 10, 20, "Lucas"],
        ["", datetime(2026, 8, 2), "Cliente Import B", "Produto Import B", 102, 3, 11, 33, "Junior"],
    ]

    response = _post_import(isolated_app.client, token, rows)

    assert response.status_code == 200
    assert response.json() == {"imported": 2, "total_in_file": 2}
    imported_sales = _fetch_all(
        isolated_app.db_paths["raios"],
        "SELECT client, product, total, source, created_by FROM sales WHERE source='excel' ORDER BY sale_date",
    )
    assert len(imported_sales) == 2
    assert [row["client"] for row in imported_sales] == ["Cliente Import A", "Cliente Import B"]
    assert [row["total"] for row in imported_sales] == [20.0, 33.0]
    assert {row["source"] for row in imported_sales} == {"excel"}
    assert {row["created_by"] for row in imported_sales} == {"admin"}

    log = _fetch_one(
        isolated_app.db_paths["raios"],
        "SELECT filename, rows_added, status, imported_by FROM import_log",
    )
    assert log == {
        "filename": "import_teste.xlsx",
        "rows_added": 2,
        "status": "ok",
        "imported_by": "admin",
    }

    follow_up_write = isolated_app.client.post(
        "/api/sales",
        headers=_headers(token),
        json={
            "sale_type": "NF",
            "sale_date": "2026-08-03",
            "client": "Cliente Pos Import",
            "product": "Produto Pos Import",
            "quantity": 1,
            "unit_price": 5,
            "total": 5,
        },
    )
    assert follow_up_write.status_code == 200


def test_import_excel_keeps_current_partial_behavior_for_invalid_rows(isolated_app):
    token = _login(isolated_app.client)
    rows = [
        ["", "DATA", "CLIENTE", "PRODUTO", "NF", "QT", "P.UNIT", "TOTAL", "ENTREGADOR"],
        ["", datetime(2026, 8, 1), "Cliente Parcial A", "Produto Parcial A", 201, 2, 10, 20, "Lucas"],
        ["", datetime(2026, 8, 1), "Cliente Parcial X", "Produto Parcial X", 202, "invalido", 10, "invalido", "Lucas"],
        ["", datetime(2026, 8, 2), "Cliente Parcial B", "Produto Parcial B", 203, 3, 10, 30, "Lucas"],
    ]

    response = _post_import(isolated_app.client, token, rows, filename="import_parcial.xlsx")

    assert response.status_code == 200
    assert response.json() == {"imported": 2, "total_in_file": 2}
    imported_sales = _fetch_all(
        isolated_app.db_paths["raios"],
        "SELECT client, total FROM sales WHERE source='excel' ORDER BY sale_date, client",
    )
    assert [row["client"] for row in imported_sales] == ["Cliente Parcial A", "Cliente Parcial B"]
    assert [row["total"] for row in imported_sales] == [20.0, 30.0]
    assert _fetch_one(
        isolated_app.db_paths["raios"],
        "SELECT rows_added, status FROM import_log WHERE filename='import_parcial.xlsx'",
    ) == {"rows_added": 2, "status": "ok"}


def test_import_excel_without_useful_rows_still_returns_400(isolated_app):
    token = _login(isolated_app.client)
    rows = [
        ["sem", "cabecalho", "util"],
        ["apenas", "texto", "solto"],
    ]

    response = _post_import(isolated_app.client, token, rows, filename="sem_dados.xlsx")

    assert response.status_code == 400
    assert response.json() == {"detail": "Nenhum dado encontrado."}
    assert _fetch_one(isolated_app.db_paths["raios"], "SELECT COUNT(*) AS total FROM sales") == {"total": 0}
    assert _fetch_one(isolated_app.db_paths["raios"], "SELECT COUNT(*) AS total FROM import_log") == {"total": 0}


def test_import_excel_rolls_back_and_closes_when_sales_insert_fails(isolated_app, monkeypatch):
    token = _login(isolated_app.client)
    state = _install_import_failure(isolated_app, monkeypatch, "sales_second")
    rows = [
        ["", "DATA", "CLIENTE", "PRODUTO", "NF", "QT", "P.UNIT", "TOTAL", "ENTREGADOR"],
        ["", datetime(2026, 8, 1), "Cliente Falha Sales A", "Produto Falha Sales A", 301, 2, 10, 20, "Lucas"],
        ["", datetime(2026, 8, 2), "Cliente Falha Sales B", "Produto Falha Sales B", 302, 3, 10, 30, "Lucas"],
    ]

    with pytest.raises(RuntimeError, match="falha sales passo 125"):
        _post_import(isolated_app.client, token, rows, filename="falha_sales.xlsx")

    _assert_import_failure_rolled_back(isolated_app, monkeypatch, state, token)


def test_import_excel_rolls_back_and_closes_when_import_log_insert_fails(isolated_app, monkeypatch):
    token = _login(isolated_app.client)
    state = _install_import_failure(isolated_app, monkeypatch, "import_log")
    rows = [
        ["", "DATA", "CLIENTE", "PRODUTO", "NF", "QT", "P.UNIT", "TOTAL", "ENTREGADOR"],
        ["", datetime(2026, 8, 1), "Cliente Falha Log", "Produto Falha Log", 401, 2, 10, 20, "Lucas"],
    ]

    with pytest.raises(RuntimeError, match="falha import_log passo 125"):
        _post_import(isolated_app.client, token, rows, filename="falha_log.xlsx")

    _assert_import_failure_rolled_back(isolated_app, monkeypatch, state, token)


def test_import_excel_rolls_back_and_closes_when_commit_fails(isolated_app, monkeypatch):
    token = _login(isolated_app.client)
    state = _install_import_failure(isolated_app, monkeypatch, "commit")
    rows = [
        ["", "DATA", "CLIENTE", "PRODUTO", "NF", "QT", "P.UNIT", "TOTAL", "ENTREGADOR"],
        ["", datetime(2026, 8, 1), "Cliente Falha Commit", "Produto Falha Commit", 501, 2, 10, 20, "Lucas"],
    ]

    with pytest.raises(RuntimeError, match="falha commit passo 125"):
        _post_import(isolated_app.client, token, rows, filename="falha_commit.xlsx")

    _assert_import_failure_rolled_back(isolated_app, monkeypatch, state, token)


def test_import_excel_rejects_invalid_extension_empty_upload_and_upload_limit(isolated_app):
    token = _login(isolated_app.client)

    invalid_extension = _post_import_bytes(isolated_app.client, token, b"conteudo", filename="import_teste.csv")
    assert invalid_extension.status_code == 400
    assert invalid_extension.json() == {"detail": "Envie uma planilha .xls ou .xlsx."}

    empty_upload = _post_import_bytes(isolated_app.client, token, b"", filename="vazio.xlsx")
    assert empty_upload.status_code == 400
    assert empty_upload.json() == {"detail": "Arquivo vazio."}

    too_large = _post_import_bytes(
        isolated_app.client,
        token,
        b"x" * (isolated_app.module.MAX_EXCEL_UPLOAD + 1),
        filename="grande.xlsx",
    )
    assert too_large.status_code == 400
    assert too_large.json() == {"detail": "Planilha muito grande. Limite: 10 MB."}

    assert _fetch_one(isolated_app.db_paths["raios"], "SELECT COUNT(*) AS total FROM sales") == {"total": 0}
    assert _fetch_one(isolated_app.db_paths["raios"], "SELECT COUNT(*) AS total FROM import_log") == {"total": 0}


def test_import_excel_requires_authentication_and_editor_permission(isolated_app):
    rows = [
        ["", "DATA", "CLIENTE", "PRODUTO", "NF", "QT", "P.UNIT", "TOTAL", "ENTREGADOR"],
        ["", datetime(2026, 8, 1), "Cliente Permissao", "Produto Permissao", 601, 2, 10, 20, "Lucas"],
    ]

    no_token = isolated_app.client.post(
        "/api/import-excel",
        files={
            "file": (
                "sem_token.xlsx",
                _xlsx_bytes(rows),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
    )
    assert no_token.status_code == 401

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    viewer_id = "viewer-import-excel"
    conn.execute(
        "INSERT INTO users(id, username, password_hash, full_name, role, active) VALUES(?,?,?,?,?,1)",
        (
            viewer_id,
            "viewer_import_excel",
            isolated_app.module.hash_password("viewer123"),
            "Viewer Import Excel",
            "viewer",
        ),
    )
    conn.commit()
    conn.close()
    viewer_token = _login(isolated_app.client, "viewer_import_excel", "viewer123")

    viewer_response = _post_import(
        isolated_app.client,
        viewer_token,
        rows,
        filename="viewer_bloqueado.xlsx",
    )
    assert viewer_response.status_code == 403
    assert viewer_response.json() == {"detail": "Permiss\u00c3\u00a3o insuficiente."}
    assert _fetch_one(isolated_app.db_paths["raios"], "SELECT COUNT(*) AS total FROM sales") == {"total": 0}
    assert _fetch_one(isolated_app.db_paths["raios"], "SELECT COUNT(*) AS total FROM import_log") == {"total": 0}
