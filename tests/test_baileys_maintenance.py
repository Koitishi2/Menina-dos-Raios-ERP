def _login(client):
    response = client.post(
        "/api/auth/login",
        headers={"x-company": "raios"},
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    return response.json()["token"]


def _headers(token):
    return {"x-token": token, "x-company": "raios"}


def _set_config(path, key, value):
    import sqlite3

    conn = sqlite3.connect(path)
    conn.execute("INSERT OR REPLACE INTO whatsapp_config(key,value) VALUES(?,?)", (key, value))
    conn.commit()
    conn.close()


def test_baileys_update_status_uses_local_authenticated_service(isolated_app, monkeypatch):
    token = _login(isolated_app.client)
    path = isolated_app.db_paths["raios"]
    _set_config(path, "provider", "baileys")
    _set_config(path, "api_url", "http://127.0.0.1:3001")
    _set_config(path, "api_token", "secret-test")
    calls = []

    class Response:
        status_code = 200
        text = "{}"

        def json(self):
            return {"installed_version": "6.7.24", "approved_version": "6.7.24", "legacy_version": "6.7.24"}

    import httpx

    def fake_get(url, headers=None, params=None, timeout=None):
        calls.append((url, headers, params, timeout))
        return Response()

    monkeypatch.setattr(httpx, "get", fake_get)
    response = isolated_app.client.get(
        "/api/whatsapp/baileys-update-status?refresh=true",
        headers=_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["installed_version"] == "6.7.24"
    assert calls == [("http://127.0.0.1:3001/maintenance/status", {"x-api-key": "secret-test"}, {"refresh": "1"}, 8)]


def test_baileys_update_rejects_non_local_api(isolated_app, monkeypatch):
    token = _login(isolated_app.client)
    path = isolated_app.db_paths["raios"]
    _set_config(path, "provider", "baileys")
    _set_config(path, "api_url", "https://example.com")
    called = []

    import httpx

    monkeypatch.setattr(httpx, "post", lambda *args, **kwargs: called.append((args, kwargs)))
    response = isolated_app.client.post("/api/whatsapp/baileys-update", headers=_headers(token))

    assert response.status_code == 400
    assert called == []


def test_baileys_update_requires_admin(isolated_app):
    response = isolated_app.client.post("/api/whatsapp/baileys-update", headers={"x-token": "invalid", "x-company": "raios"})
    assert response.status_code == 401


def test_baileys_update_forwards_only_fixed_action(isolated_app, monkeypatch):
    token = _login(isolated_app.client)
    path = isolated_app.db_paths["raios"]
    _set_config(path, "provider", "baileys")
    _set_config(path, "api_url", "http://localhost:3001")
    _set_config(path, "api_token", "secret-test")
    calls = []

    class Response:
        status_code = 202
        text = "{}"

        def json(self):
            return {"ok": True, "unit": "menina-baileys-update-1"}

    import httpx

    def fake_post(url, headers=None, json=None, timeout=None):
        calls.append((url, headers, json, timeout))
        return Response()

    monkeypatch.setattr(httpx, "post", fake_post)
    response = isolated_app.client.post("/api/whatsapp/baileys-update", headers=_headers(token))

    assert response.status_code == 200
    assert response.json()["ok"] is True
    assert calls == [("http://localhost:3001/maintenance/update", {"x-api-key": "secret-test"}, {}, 12)]


def test_frontend_exposes_baileys_update_tab_and_bot_prompts(isolated_app):
    html = (isolated_app.temp_backend / "static" / "index.html").read_text(encoding="utf-8")
    assert 'data-view="update"' in html
    assert 'id="wa-view-update"' in html
    assert "/api/whatsapp/baileys-update-status" in html
    assert "/api/whatsapp/baileys-update" in html
    assert 'id="wa-update-legacy"' in html
    assert "Versão aprovada instalada" in html
    assert "order_bot_welcome_message" in isolated_app.module._BOT_SETTINGS_KEYS


def test_baileys_safe_updater_preserves_session_and_closes_swap_window():
    from pathlib import Path

    root = Path(__file__).resolve().parents[1]
    script = (root / "baileys-api" / "update-baileys-safe.sh").read_text(encoding="utf-8")
    old_move = 'mv -- "$APP_DIR/node_modules" "$BACKUP/node_modules"'
    new_move = 'mv -- "$STAGING/node_modules" "$APP_DIR/node_modules"'
    assert script.index(old_move) < script.index("SWAPPED=1") < script.index(new_move)
    assert "auth_info_baileys" not in script
    assert 'rm -rf -- "$APP_DIR"' not in script
    assert 'rm -rf -- "$APP_DIR/node_modules"' in script
    assert 'systemctl start "$SERVICE"' in script
    assert 'curl --fail --silent --show-error' in script
    assert 'd.get("connected") is True' in script
    assert "BAILEYS_ALREADY_CURRENT" in script
