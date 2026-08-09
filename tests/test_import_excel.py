import sqlite3
from datetime import datetime
from io import BytesIO

import pandas as pd


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
