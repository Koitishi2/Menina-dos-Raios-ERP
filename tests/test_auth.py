import sqlite3
from datetime import datetime, timedelta
from types import SimpleNamespace

import pytest


def _login(client, username="admin", password="admin123", company="raios"):
    return client.post(
        "/api/auth/login",
        headers={"x-company": company},
        json={"username": username, "password": password},
    )


class _FakeRequest:
    def __init__(self, direct_host="127.0.0.1", headers=None, include_client=True):
        if include_client:
            self.client = SimpleNamespace(host=direct_host) if direct_host is not None else None
        self.headers = headers or {}


@pytest.fixture
def isolated_login_rate_state(isolated_app):
    module = isolated_app.module
    original = dict(module._LOGIN_ATTEMPTS)
    module._LOGIN_ATTEMPTS.clear()
    try:
        yield module
    finally:
        module._LOGIN_ATTEMPTS.clear()
        module._LOGIN_ATTEMPTS.update(original)


def test_is_trusted_proxy_host_current_ipaddress_contract(isolated_app):
    trusted_proxy_host = isolated_app.module._is_trusted_proxy_host

    trusted = [
        "127.0.0.1",
        "::1",
        "10.0.0.1",
        "10.0.0.0",
        "10.255.255.255",
        "172.16.0.1",
        "172.31.255.255",
        "192.168.0.0",
        "192.168.1.1",
        "192.168.255.255",
        "169.254.1.1",
        "255.255.255.255",
        123,
    ]
    for host in trusted:
        result = trusted_proxy_host(host)
        assert result is True
        assert isinstance(result, bool)

    untrusted = [
        "8.8.8.8",
        "1.1.1.1",
        "100.64.0.1",
        "172.15.255.255",
        "172.32.0.0",
        "224.0.0.1",
    ]
    for host in untrusted:
        result = trusted_proxy_host(host)
        assert result is False
        assert isinstance(result, bool)


def test_is_trusted_proxy_host_current_malformed_hostname_and_empty_values(isolated_app):
    trusted_proxy_host = isolated_app.module._is_trusted_proxy_host

    malformed_or_named_hosts = [
        "localhost",
        "proxy.local",
        "",
        "   ",
        "127.0.0.1:8000",
        "[::1]",
        "999.999.999.999",
        None,
    ]
    for host in malformed_or_named_hosts:
        result = trusted_proxy_host(host)
        assert result is False
        assert isinstance(result, bool)


def test_client_ip_current_direct_host_without_proxy_headers(isolated_app):
    client_ip = isolated_app.module._client_ip

    assert client_ip(_FakeRequest("8.8.8.8")) == "8.8.8.8"
    assert client_ip(_FakeRequest("10.0.0.5")) == "10.0.0.5"
    assert client_ip(_FakeRequest("127.0.0.1")) == "127.0.0.1"
    assert client_ip(_FakeRequest("::1")) == "::1"
    assert client_ip(_FakeRequest(None)) == "?"


def test_client_ip_current_trusted_proxy_uses_forwarded_for_before_real_ip(isolated_app):
    client_ip = isolated_app.module._client_ip

    assert client_ip(
        _FakeRequest("127.0.0.1", {"x-forwarded-for": "203.0.113.10"})
    ) == "203.0.113.10"
    assert client_ip(
        _FakeRequest("10.0.0.5", {"x-forwarded-for": "203.0.113.10, 198.51.100.2"})
    ) == "203.0.113.10"
    assert client_ip(
        _FakeRequest("::1", {"x-forwarded-for": " 203.0.113.10 , 198.51.100.2 "})
    ) == "203.0.113.10"
    assert client_ip(
        _FakeRequest(
            "127.0.0.1",
            {"x-forwarded-for": "203.0.113.10", "x-real-ip": "198.51.100.2"},
        )
    ) == "203.0.113.10"


def test_client_ip_current_trusted_proxy_uses_real_ip_when_forwarded_for_is_empty(isolated_app):
    client_ip = isolated_app.module._client_ip

    assert client_ip(
        _FakeRequest("127.0.0.1", {"x-real-ip": "198.51.100.2"})
    ) == "198.51.100.2"
    assert client_ip(
        _FakeRequest("127.0.0.1", {"x-forwarded-for": "", "x-real-ip": " 198.51.100.2 "})
    ) == "198.51.100.2"
    assert client_ip(
        _FakeRequest("127.0.0.1", {"x-forwarded-for": "   ", "x-real-ip": "198.51.100.2"})
    ) == ""


def test_client_ip_current_untrusted_proxy_ignores_forwarding_headers(isolated_app):
    client_ip = isolated_app.module._client_ip

    assert client_ip(
        _FakeRequest("8.8.8.8", {"x-forwarded-for": "203.0.113.10", "x-real-ip": "198.51.100.2"})
    ) == "8.8.8.8"
    assert client_ip(
        _FakeRequest("localhost", {"x-forwarded-for": "203.0.113.10"})
    ) == "localhost"
    assert client_ip(
        _FakeRequest("127.0.0.1:8000", {"x-forwarded-for": "203.0.113.10"})
    ) == "127.0.0.1:8000"


def test_client_ip_current_malformed_request_paths_do_not_escape_exceptions(isolated_app):
    client_ip = isolated_app.module._client_ip

    assert client_ip(None) == "?"
    assert client_ip(_FakeRequest("127.0.0.1", include_client=False)) == "?"
    request_without_headers = SimpleNamespace(client=SimpleNamespace(host="127.0.0.1"))
    assert client_ip(request_without_headers) == "?"
    request_with_header_object_without_get = SimpleNamespace(
        client=SimpleNamespace(host="127.0.0.1"),
        headers={},
    )
    request_with_header_object_without_get.headers = []
    assert client_ip(request_with_header_object_without_get) == "?"


def test_login_rate_check_current_empty_below_limit_blocked_and_expired(
    isolated_login_rate_state,
    monkeypatch,
):
    module = isolated_login_rate_state
    check_login_rate = module._check_login_rate
    attempts = module._LOGIN_ATTEMPTS
    monkeypatch.setattr(module._time_mod, "time", lambda: 1000.0)

    assert check_login_rate("203.0.113.10") == (True, 0)
    assert attempts["203.0.113.10"] == []

    attempts["203.0.113.10"] = [(995.0, False)] * (module.LOGIN_RATE_MAX_FAILS - 1)
    assert check_login_rate("203.0.113.10") == (True, 0)

    attempts["203.0.113.10"].append((990.0, False))
    assert check_login_rate("203.0.113.10") == (
        False,
        module.LOGIN_RATE_BLOCK_SECS - 10,
    )

    monkeypatch.setattr(module._time_mod, "time", lambda: 1049.0)
    assert check_login_rate("203.0.113.10") == (
        False,
        module.LOGIN_RATE_BLOCK_SECS - 59,
    )

    monkeypatch.setattr(module._time_mod, "time", lambda: 1061.0)
    assert check_login_rate("203.0.113.10") == (True, 0)
    assert attempts["203.0.113.10"]

    monkeypatch.setattr(module._time_mod, "time", lambda: 1296.0)
    assert check_login_rate("203.0.113.10") == (True, 0)
    assert attempts["203.0.113.10"] == []


def test_login_rate_check_current_separates_ips_and_prunes_block_window(
    isolated_login_rate_state,
    monkeypatch,
):
    module = isolated_login_rate_state
    check_login_rate = module._check_login_rate
    attempts = module._LOGIN_ATTEMPTS
    monkeypatch.setattr(module._time_mod, "time", lambda: 2000.0)

    attempts["203.0.113.10"] = [(1995.0, False)] * module.LOGIN_RATE_MAX_FAILS
    attempts["198.51.100.20"] = [(1995.0, False)] * (module.LOGIN_RATE_MAX_FAILS - 1)
    attempts["192.0.2.30"] = [
        (2000.0 - module.LOGIN_RATE_BLOCK_SECS, False),
        (1999.0, True),
    ]

    assert check_login_rate("203.0.113.10") == (
        False,
        module.LOGIN_RATE_BLOCK_SECS - 5,
    )
    assert check_login_rate("198.51.100.20") == (True, 0)
    assert check_login_rate("192.0.2.30") == (True, 0)
    assert attempts["192.0.2.30"] == [(1999.0, True)]


def test_record_login_current_failures_success_clear_and_check_interaction(
    isolated_login_rate_state,
    monkeypatch,
):
    module = isolated_login_rate_state
    record_login = module._record_login
    check_login_rate = module._check_login_rate
    attempts = module._LOGIN_ATTEMPTS
    now = {"value": 3000.0}
    monkeypatch.setattr(module._time_mod, "time", lambda: now["value"])

    record_login("203.0.113.10", False)
    assert attempts["203.0.113.10"] == [(3000.0, False)]
    assert check_login_rate("203.0.113.10") == (True, 0)

    for index in range(1, module.LOGIN_RATE_MAX_FAILS):
        now["value"] = 3000.0 + index
        record_login("203.0.113.10", False)

    assert len(attempts["203.0.113.10"]) == module.LOGIN_RATE_MAX_FAILS
    assert check_login_rate("203.0.113.10") == (
        False,
        module.LOGIN_RATE_BLOCK_SECS - 9,
    )

    record_login("198.51.100.20", False)
    assert check_login_rate("198.51.100.20") == (True, 0)

    record_login("203.0.113.10", True)
    assert "203.0.113.10" not in attempts
    assert check_login_rate("203.0.113.10") == (True, 0)


def test_record_login_current_large_state_cleanup_contract(
    isolated_login_rate_state,
    monkeypatch,
):
    module = isolated_login_rate_state
    record_login = module._record_login
    attempts = module._LOGIN_ATTEMPTS
    monkeypatch.setattr(module._time_mod, "time", lambda: 5000.0)

    for index in range(10001):
        attempts[f"10.0.{index // 255}.{index % 255}"] = [
            (5000.0 - module.LOGIN_RATE_BLOCK_SECS, False),
        ]
    attempts["203.0.113.10"] = [(4999.0, False)]

    record_login("198.51.100.20", False)

    assert "203.0.113.10" in attempts
    assert "198.51.100.20" in attempts
    assert len(attempts) == 2


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
