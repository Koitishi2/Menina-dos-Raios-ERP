import io


def _authorize(module, monkeypatch):
    monkeypatch.setattr(
        module,
        "require_any_tab_access",
        lambda _token, _tabs: {"role": "admin"},
    )


def test_mobile_tts_requires_azure_configuration(isolated_app, monkeypatch):
    _authorize(isolated_app.module, monkeypatch)
    monkeypatch.delenv("AZURE_SPEECH_KEY", raising=False)

    response = isolated_app.client.post(
        "/api/mobile/tts",
        headers={"x-token": "token-teste"},
        json={"text": "Qual é o nome do cliente?"},
    )

    assert response.status_code == 503
    assert "credencial Azure nao configurada" in response.json()["detail"]


def test_mobile_tts_requires_user_session(isolated_app):
    response = isolated_app.client.post(
        "/api/mobile/tts",
        json={"text": "Teste"},
    )

    assert response.status_code == 401


def test_mobile_tts_returns_francisca_audio(isolated_app, monkeypatch):
    _authorize(isolated_app.module, monkeypatch)
    monkeypatch.setenv("AZURE_SPEECH_KEY", "key-test-only")
    monkeypatch.setenv("AZURE_SPEECH_REGION", "brazilsouth")
    requests = []

    class FakeResponse(io.BytesIO):
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            self.close()

    def fake_urlopen(request, timeout):
        requests.append((request, timeout))
        return FakeResponse(b"mock-mp3")

    monkeypatch.setattr(isolated_app.module.urllib.request, "urlopen", fake_urlopen)
    response = isolated_app.client.post(
        "/api/mobile/tts",
        headers={"x-token": "token-teste"},
        json={"text": "Macaxeira <fresca> & alho"},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.content == b"mock-mp3"
    azure_request, timeout = requests[0]
    assert timeout == 12
    assert azure_request.full_url == "https://brazilsouth.tts.speech.microsoft.com/cognitiveservices/v1"
    assert azure_request.get_header("Ocp-apim-subscription-key") == "key-test-only"
    assert b"pt-BR-FranciscaNeural" in azure_request.data
    assert b"Macaxeira &lt;fresca&gt; &amp; alho" in azure_request.data


def test_mobile_tts_rejects_empty_and_long_text(isolated_app, monkeypatch):
    _authorize(isolated_app.module, monkeypatch)

    empty = isolated_app.client.post(
        "/api/mobile/tts",
        headers={"x-token": "token-teste"},
        json={"text": "  "},
    )
    too_long = isolated_app.client.post(
        "/api/mobile/tts",
        headers={"x-token": "token-teste"},
        json={"text": "x" * 501},
    )

    assert empty.status_code == 400
    assert too_long.status_code == 413
