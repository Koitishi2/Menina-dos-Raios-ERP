from test_orcamentos import _login


def test_mobile_daily_motivation_uses_authenticated_erp_configuration(isolated_app):
    token = _login(isolated_app.client)
    response = isolated_app.client.get("/api/mobile/daily-motivation", headers={"x-token": token})

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload["enabled"], bool)
    assert payload["date"]
    assert isinstance(payload["message"], str)


def test_mobile_daily_motivation_requires_a_session(isolated_app):
    response = isolated_app.client.get("/api/mobile/daily-motivation")

    assert response.status_code == 401
