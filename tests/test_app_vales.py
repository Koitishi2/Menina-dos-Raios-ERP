import base64
import uuid


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
