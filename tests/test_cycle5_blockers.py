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


def test_evolution_go_is_the_only_whatsapp_runtime_in_manifest():
    manifest = (ROOT / "deploy" / "whatsapp_sellers_manifest.txt").read_text(encoding="utf-8")
    assert "menina-baileys" not in manifest
    assert "baileys-api/" not in manifest
    assert "services/evolution_go.py" in manifest

def test_frontend_and_backend_have_no_baileys_runtime_controls():
    html = (ROOT / "backend" / "static" / "index.html").read_text(encoding="utf-8")
    app = (ROOT / "backend" / "app.py").read_text(encoding="utf-8")
    updater = (ROOT / "atualizar_backend_seguro.sh").read_text(encoding="utf-8")
    assert "baileys" not in html.lower()
    assert "/api/whatsapp/baileys-" not in app
    assert "menina-baileys.service" not in app
    assert 'test -d "$STAGED_BAILEYS"' not in updater
    assert 'systemctl disable "$BAILEYS_SERVICE"' in updater
    assert 'clear_baileys_code "$BAILEYS_DIR"' in updater
    assert 'credentials_and_node_modules=preserved' in updater
