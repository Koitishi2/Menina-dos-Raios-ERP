import hashlib
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _sha256(relative_path):
    return hashlib.sha256((ROOT / relative_path).read_bytes()).hexdigest().upper()


def test_whatsapp_migrations_are_versionable_and_unchanged():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    expected = {
        "backend/migrations/20260914_whatsapp_orders_up.sql": "9B0601BBCFB4C574DAC5F841514FA80A2E371D98F13093AE35C11D3749E69C2B",
        "backend/migrations/20260914_whatsapp_orders_down.sql": "BB9A33DB046C7FE724889D9C2A1AF3DF3730CD1B9D47D16A93601357E2E1B2FE",
        "backend/migrations/20260914_whatsapp_inbound_up.sql": "5E6FE3CEB3021155516D26E20D6251E1650551D693314DF72B8D9E1996ED6291",
        "backend/migrations/20260914_whatsapp_inbound_down.sql": "EAA81243C78BF47F5B6A77841235BC33915BB726610E955E948055BE5D3BC73C",
    }
    for path, digest in expected.items():
        assert f"!{path}" in ignore
        assert _sha256(path) == digest
        ignored = subprocess.run(
            ["git", "check-ignore", "-q", path], cwd=ROOT, check=False,
        )
        assert ignored.returncode == 1


def test_baileys_session_and_qr_artifacts_are_ignored():
    ignore = (ROOT / ".gitignore").read_text(encoding="utf-8")
    assert "baileys-api/auth_info_baileys/" in ignore
    assert "**/auth_info_baileys/" in ignore
    assert "baileys-api/qr*.png" in ignore
    assert "baileys-api/qr*.txt" in ignore
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "--no-index", "baileys-api/auth_info_baileys/creds.json"],
        cwd=ROOT, check=False,
    )
    assert ignored.returncode == 0


def test_new_runtime_sources_do_not_embed_secret_assignments():
    sources = [
        ROOT / "baileys-api/security.js",
        ROOT / "baileys-api/server.js",
        ROOT / "backend/static/js/client_whatsapp.js",
    ]
    forbidden = re.compile(r"(?i)(api_key|token|password|secret)\s*[:=]\s*['\"][^'\"]{12,}['\"]")
    for source in sources:
        assert not forbidden.search(source.read_text(encoding="utf-8")), source


def test_legacy_send_route_is_fail_closed_before_handler():
    server = (ROOT / "baileys-api/server.js").read_text(encoding="utf-8")
    assert 'app.post("/send", checkLegacySend' in server
    assert 'app.post("/send", checkAuth' not in server
    assert "authorizeOutboundSend({" in server
    assert "hasTrustedJid: Boolean(mappedJid)" in server
    assert 'delivery_status: "accepted"' in server
    assert 'sock.ev.on("messages.update", updateOutboundReceipts)' in server
    assert 'app.get("/send-status/:messageId", checkAuth' in server
    assert "WHATSAPP_OUTBOUND_ENABLED" in server
