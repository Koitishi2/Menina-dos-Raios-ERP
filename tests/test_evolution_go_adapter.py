from backend.services import evolution_go
from backend.routers.whatsapp_inbound import _normalize_evolution_go


def test_instance_resolution_and_send_text_use_instance_token(monkeypatch):
    evolution_go.clear_instance_cache()
    calls = []

    class Response:
        text = "{}"

        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    def fake_request(method, url, headers=None, json=None, timeout=None):
        calls.append((method, url, headers))
        if url.endswith("/instance/all"):
            return Response({"data": [{"id": "instance-uuid", "name": "menina-teste"}]})
        return Response({"data": {"id": "instance-uuid", "name": "menina-teste", "token": "instance-secret"}})

    import httpx
    monkeypatch.setattr(httpx, "request", fake_request)
    _, instance = evolution_go.get_instance({
        "api_url": "http://127.0.0.1:8766", "api_token": "global-admin-key",
        "instance_id": "menina-teste",
    })

    assert instance["token"] == "instance-secret"
    assert calls[0][1].endswith("/instance/all")
    assert calls[1][1].endswith("/instance/info/instance-uuid")
    assert all(call[2]["apikey"] == "global-admin-key" for call in calls)
    evolution_go.clear_instance_cache()
    calls = []

    class Response:
        text = '{"message":"success"}'

        def __init__(self, payload):
            self.payload = payload

        def raise_for_status(self):
            return None

        def json(self):
            return self.payload

    def fake_request(method, url, headers=None, json=None, timeout=None):
        calls.append((method, url, headers, json, timeout))
        if url.endswith("/instance/all"):
            return Response({"data": [{"name": "menina-teste", "token": "instance-secret"}]})
        return Response({"message": "success"})

    import httpx
    monkeypatch.setattr(httpx, "request", fake_request)
    result = evolution_go.send_text("+55 (95) 99123-4567", "Olá", {
        "api_url": "http://127.0.0.1:8766", "api_token": "global-admin-key",
        "instance_id": "menina-teste",
    })

    assert result == {"message": "success"}
    assert calls[0][0:3] == ("GET", "http://127.0.0.1:8766/instance/all", {
        "apikey": "global-admin-key", "Content-Type": "application/json",
    })
    assert calls[1][0:4] == ("POST", "http://127.0.0.1:8766/send/text", {
        "apikey": "instance-secret", "Content-Type": "application/json",
    }, {"number": "5595991234567", "text": "Olá"})
    evolution_go.clear_instance_cache()


def test_evolution_go_message_event_normalizes_for_existing_inbound_pipeline():
    event = _normalize_evolution_go({
        "event": "Message",
        "instance": "menina-teste",
        "data": {
            "key": {
                "id": "wamid-123", "remoteJid": "5595991234567@s.whatsapp.net",
                "fromMe": False,
            },
            "message": {"conversation": "Quero fazer um pedido"},
            "messageTimestamp": "1791280800",
        },
    })

    assert event["provider"] == "evolution_go"
    assert event["instance"] == "menina-teste"
    assert event["message_id"] == "wamid-123"
    assert event["remote_jid"] == "5595991234567@s.whatsapp.net"
    assert event["text"] == "Quero fazer um pedido"
    assert event["from_me"] is False
    assert event["timestamp"].startswith("2026-")


def test_evolution_go_rejects_events_without_instance_name():
    assert _normalize_evolution_go({
        "event": "MESSAGE",
        "data": {"key": {"id": "id-1", "remoteJid": "5511999999999@s.whatsapp.net"},
                 "message": {"conversation": "Oi"}},
    }) is None
