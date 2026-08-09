import sqlite3
from datetime import datetime, timedelta


def _login(client, username="admin", password="admin123", company="raios"):
    return client.post(
        "/api/auth/login",
        headers={"x-company": company},
        json={"username": username, "password": password},
    )


def test_valid_login_and_me_with_company_header(isolated_app):
    response = _login(isolated_app.client, company="estrada")
    assert response.status_code == 200
    payload = response.json()
    assert payload["username"] == "admin"
    assert payload["role"] == "admin"
    assert payload["company"] == "estrada"
    assert payload["token"]

    me = isolated_app.client.get("/api/auth/me", headers={"x-token": payload["token"]})
    assert me.status_code == 200
    assert me.json()["username"] == "admin"


def test_invalid_login_is_rejected(isolated_app):
    response = _login(isolated_app.client, password="senha-errada")
    assert response.status_code == 401
    assert "incorretos" in response.text


def test_protected_route_without_token_is_rejected(isolated_app):
    response = isolated_app.client.get("/api/auth/me")
    assert response.status_code == 401


def test_invalid_token_is_rejected(isolated_app):
    response = isolated_app.client.get("/api/auth/me", headers={"x-token": "token-invalido"})
    assert response.status_code == 401


def test_logout_invalidates_token(isolated_app):
    login = _login(isolated_app.client)
    assert login.status_code == 200
    token = login.json()["token"]

    logout = isolated_app.client.post("/api/auth/logout", headers={"x-token": token})
    assert logout.status_code == 200
    assert logout.json()["ok"] is True

    me = isolated_app.client.get("/api/auth/me", headers={"x-token": token})
    assert me.status_code == 401


def test_expired_session_is_rejected(isolated_app):
    login = _login(isolated_app.client)
    assert login.status_code == 200
    token = login.json()["token"]

    conn = sqlite3.connect(isolated_app.db_paths["raios"])
    expired = (datetime.now() - timedelta(hours=1)).strftime("%Y-%m-%d %H:%M:%S")
    conn.execute("UPDATE sessions SET expires_at=? WHERE token=?", (expired, token))
    conn.commit()
    conn.close()

    me = isolated_app.client.get("/api/auth/me", headers={"x-token": token})
    assert me.status_code == 401
