import base64
import sqlite3
import uuid

import pytest


def _auth_headers():
    return {"x-token": "token-teste", "x-company": "raios"}


def _patch_auth(module, monkeypatch):
    monkeypatch.setattr(
        module,
        "require_auth",
        lambda _token: {
            "user_id": "user-teste",
            "username": "admin",
            "full_name": "Administrador",
            "role": "admin",
        },
    )


def _vale_payload():
    return {
        "client_id": f"vale-{uuid.uuid4()}",
        "solicitante_nome": "Bruno Teste",
        "amount": 150.75,
        "request_date": "2026-08-14",
        "signature_png_base64": base64.b64encode(b"assinatura-teste").decode("ascii"),
        "signature_format": "png",
    }


def test_mobile_vale_delete_requires_auth(isolated_app):
    response = isolated_app.client.delete("/api/mobile/vales/qualquer-id")

    assert response.status_code == 401


def test_mobile_vale_delete_removes_record_and_signature(isolated_app, monkeypatch):
    _patch_auth(isolated_app.module, monkeypatch)

    created = isolated_app.client.post(
        "/api/mobile/vales",
        headers=_auth_headers(),
        json=_vale_payload(),
    )
    assert created.status_code == 200
    vale_id = created.json()["vale"]["id"]

    before = isolated_app.client.get("/api/mobile/vales", headers=_auth_headers())
    assert before.status_code == 200
    assert any(item["id"] == vale_id for item in before.json()["items"])

    deleted = isolated_app.client.delete(
        f"/api/mobile/vales/{vale_id}",
        headers=_auth_headers(),
    )
    assert deleted.status_code == 200
    assert deleted.json()["success"] is True
    assert deleted.json()["deleted"] is True
    assert deleted.json()["vale"]["id"] == vale_id

    after = isolated_app.client.get("/api/mobile/vales", headers=_auth_headers())
    assert after.status_code == 200
    assert all(item["id"] != vale_id for item in after.json()["items"])

    signature = isolated_app.client.get(
        f"/api/mobile/vales/{vale_id}/signature",
        headers=_auth_headers(),
    )
    assert signature.status_code == 404


def test_mobile_vale_delete_unknown_id_returns_404(isolated_app, monkeypatch):
    _patch_auth(isolated_app.module, monkeypatch)

    response = isolated_app.client.delete(
        "/api/mobile/vales/vale-inexistente",
        headers=_auth_headers(),
    )

    assert response.status_code == 404


class _ValeConnectionSpy:
    def __init__(self, connection, *, fail_execute=False, fail_commit=False):
        self.connection = connection
        self.fail_execute = fail_execute
        self.fail_commit = fail_commit
        self.state = {"delete": 0, "commit": 0, "rollback": 0, "close": 0}

    def execute(self, sql, params=()):
        if sql.strip().upper().startswith("DELETE FROM APP_VALES"):
            self.state["delete"] += 1
            if self.fail_execute:
                raise sqlite3.OperationalError("falha controlada ao excluir vale")
        return self.connection.execute(sql, params)

    def commit(self):
        self.state["commit"] += 1
        if self.fail_commit:
            raise sqlite3.OperationalError("falha controlada no commit do vale")
        return self.connection.commit()

    def rollback(self):
        self.state["rollback"] += 1
        return self.connection.rollback()

    def close(self):
        self.state["close"] += 1
        return self.connection.close()


@pytest.mark.parametrize(
    ("failure", "message", "expected_commit"),
    [
        ("execute", "falha controlada ao excluir vale", 0),
        ("commit", "falha controlada no commit do vale", 1),
    ],
)
def test_mobile_vale_delete_rolls_back_and_closes_on_database_failure(
    isolated_app, monkeypatch, failure, message, expected_commit
):
    module = isolated_app.module
    _patch_auth(module, monkeypatch)
    created = isolated_app.client.post(
        "/api/mobile/vales",
        headers=_auth_headers(),
        json=_vale_payload(),
    )
    vale_id = created.json()["vale"]["id"]
    original_get_app_notes_db = module.get_app_notes_db
    spy = _ValeConnectionSpy(
        original_get_app_notes_db(),
        fail_execute=failure == "execute",
        fail_commit=failure == "commit",
    )
    monkeypatch.setattr(module, "get_app_notes_db", lambda: spy)

    with pytest.raises(sqlite3.OperationalError, match=message):
        module.delete_mobile_vale(vale_id, "token-teste")

    assert spy.state == {
        "delete": 1,
        "commit": expected_commit,
        "rollback": 1,
        "close": 1,
    }

    monkeypatch.setattr(module, "get_app_notes_db", original_get_app_notes_db)
    connection = original_get_app_notes_db()
    try:
        assert connection.execute(
            "SELECT id FROM app_vales WHERE id=?", (vale_id,)
        ).fetchone()["id"] == vale_id
        connection.execute(
            "INSERT INTO app_notes_meta(key,value) VALUES(?,?)",
            (f"write-after-{failure}", "ok"),
        )
        connection.commit()
    finally:
        connection.close()


def test_app_vale_actions_use_safe_delegated_handlers(isolated_app):
    html = (isolated_app.temp_backend / "static" / "index.html").read_text(
        encoding="utf-8"
    )

    assert 'data-app-vale-action="signature"' in html
    assert 'data-app-vale-action="delete"' in html
    assert "closest('[data-app-vale-action][data-app-vale-id]')" in html
    assert 'onclick="showAppValeSignature(' not in html
    assert 'onclick="deleteAppVale(' not in html
    assert html.count("async function showAppValeSignature(id)") == 1
