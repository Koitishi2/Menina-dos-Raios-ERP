import importlib.util
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]


def _load_builder():
    path = ROOT / "scripts" / "build_deploy_package.py"
    spec = importlib.util.spec_from_file_location("build_deploy_package_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


def _write(path, content="ok"):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _minimal_source(tmp_path):
    source = tmp_path / "source"
    _write(
        source / "backend" / "app.py",
        "from routers.sellers import create_sellers_router\n"
        "from services.sellers_service import require_active_seller\n"
        "from repositories.sellers_repository import init_sellers_schema\n",
    )
    _write(source / "backend" / "routers" / "__init__.py", "")
    _write(
        source / "backend" / "routers" / "sellers.py",
        "from services import sellers_service\n"
        "def create_sellers_router():\n"
        "    return None\n",
    )
    _write(source / "backend" / "services" / "__init__.py", "")
    _write(
        source / "backend" / "services" / "sellers_service.py",
        "from repositories import sellers_repository\n"
        "def require_active_seller():\n"
        "    return None\n",
    )
    _write(source / "backend" / "repositories" / "__init__.py", "")
    _write(
        source / "backend" / "repositories" / "sellers_repository.py",
        "def init_sellers_schema():\n"
        "    return None\n",
    )
    _write(source / "backend" / "static" / "index.html", '<link href="css/client_whatsapp.css"><script src="js/client_orders.js"></script>')
    _write(source / "backend" / "static" / "css" / "client_whatsapp.css", "")
    _write(source / "backend" / "static" / "js" / "client_orders.js", "")
    _write(source / "baileys-api" / "server.js", "require('./inbound')\nrequire('./security')\n")
    _write(source / "baileys-api" / "inbound.js", "")
    _write(source / "baileys-api" / "security.js", "")
    _write(source / "baileys-api" / "package.json", "{}")
    _write(source / "baileys-api" / "package-lock.json", "{}")
    for migration in (
        "20260914_whatsapp_orders_up.sql",
        "20260914_whatsapp_orders_down.sql",
        "20260914_whatsapp_inbound_up.sql",
        "20260914_whatsapp_inbound_down.sql",
        "20260916_sellers_up.sql",
        "20260916_sellers_down.sql",
    ):
        _write(source / "backend" / "migrations" / migration, "-- sql\n")
    return source


def test_manifest_lists_runtime_dependencies_without_protected_data():
    text = (ROOT / "deploy" / "whatsapp_sellers_manifest.txt").read_text(encoding="utf-8")

    for required in (
        "backend/app.py",
        "backend/rbac.py",
        "backend/schemas.py",
        "backend/domains/sellers.py",
        "backend/repositories/sellers_repository.py",
        "backend/services/sellers_service.py",
        "backend/routers/sellers.py",
        "baileys-api/server.js",
        "baileys-api/inbound.js",
        "baileys-api/security.js",
        "backend/migrations/20260914_whatsapp_orders_up.sql",
        "backend/migrations/20260914_whatsapp_inbound_up.sql",
        "backend/migrations/20260916_sellers_up.sql",
    ):
        assert required in text
    runtime_block = text.split("[migrations]", 1)[0]
    for blocked in ("node_modules", "auth_info_baileys", ".env", "uploads", "backups"):
        assert blocked not in runtime_block
    assert "WHATSAPP_OUTBOUND_ENABLED=false" in text
    assert "WHATSAPP_OUTBOUND_MODE=disabled" in text


def test_packager_uses_git_archive_and_not_worktree():
    builder = _load_builder()
    script = (ROOT / "scripts" / "build_deploy_package.py").read_text(encoding="utf-8")

    assert '"archive"' in script
    assert '"cat-file"' in script
    assert "REMOTE_ACCESS=NO" in script
    assert '["ssh"' not in script.lower()
    assert '["scp"' not in script.lower()
    assert builder.DEFAULT_MANIFEST.name == "whatsapp_sellers_manifest.txt"


def test_packager_blocks_missing_python_dependency(tmp_path):
    builder = _load_builder()
    source = _minimal_source(tmp_path)
    (source / "backend" / "repositories" / "sellers_repository.py").unlink()

    with pytest.raises(builder.PackageError, match="imports Python locais ausentes"):
        builder.validate_python_imports(source)


def test_packager_resolves_backend_root_imports_and_module_members(tmp_path):
    builder = _load_builder()
    source = _minimal_source(tmp_path)

    builder.validate_python_imports(source)


def test_packager_blocks_missing_backend_root_submodule_import(tmp_path):
    builder = _load_builder()
    source = _minimal_source(tmp_path)
    (source / "backend" / "services" / "sellers_service.py").unlink()

    with pytest.raises(builder.PackageError, match="services.sellers_service"):
        builder.validate_python_imports(source)


def test_packager_blocks_missing_static_reference(tmp_path):
    builder = _load_builder()
    source = _minimal_source(tmp_path)
    (source / "backend" / "static" / "js" / "client_orders.js").unlink()

    with pytest.raises(builder.PackageError, match="referencias JS/CSS ausentes"):
        builder.validate_static_refs(source)


def test_packager_blocks_missing_baileys_dependency(tmp_path):
    builder = _load_builder()
    source = _minimal_source(tmp_path)
    (source / "baileys-api" / "inbound.js").unlink()

    with pytest.raises(builder.PackageError, match="Baileys runtime ausente|require local ausente"):
        builder.validate_node_refs(source)


def test_packager_blocks_protected_paths_and_secret_patterns(tmp_path):
    builder = _load_builder()
    source = _minimal_source(tmp_path)

    with pytest.raises(builder.PackageError, match="protegido"):
        builder.validate_relpath("backend/database/prod.db")

    secret = source / "backend" / "leak.py"
    _write(secret, "API_KEY=valor_real\n")
    with pytest.raises(builder.PackageError, match="possivel segredo"):
        builder.scan_secrets("backend/leak.py", secret)

    placeholder = source / "backend" / "safe_config_example.py"
    _write(placeholder, 'APP_NOTES_TOKEN = ""\nAPP_CALENDAR_TOKEN = ""\n')
    builder.scan_secrets("backend/safe_config_example.py", placeholder)

    hardcoded = source / "backend" / "hardcoded_config.py"
    _write(hardcoded, 'APP_NOTES_TOKEN = "valor-funcional-hardcoded"\n')
    with pytest.raises(builder.PackageError, match="possivel segredo"):
        builder.scan_secrets("backend/hardcoded_config.py", hardcoded)


def test_runtime_code_and_readme_do_not_define_functional_app_token_defaults():
    app_text = (ROOT / "backend" / "app.py").read_text(encoding="utf-8")
    readme_text = (ROOT / "README.md").read_text(encoding="utf-8")

    assert 'os.environ.get("APP_NOTES_TOKEN", ' not in app_text
    assert 'os.environ.get("APP_CALENDAR_TOKEN", ' not in app_text
    assert 'APP_NOTES_TOKEN = "' not in app_text
    assert 'APP_CALENDAR_TOKEN = "' not in app_text


def test_packager_validates_known_migration_hashes_from_real_commit():
    builder = _load_builder()
    meta, sections = builder.parse_manifest(ROOT / "deploy" / "whatsapp_sellers_manifest.txt")

    assert meta["version_commit"] is not None
    assert sections["migration_order"].index("backend/migrations/20260914_whatsapp_orders_up.sql") < sections["migration_order"].index("backend/migrations/20260914_whatsapp_inbound_up.sql")
    assert "backend/migrations/20260916_sellers_up.sql" in sections["migration_order"]
    assert builder.KNOWN_MIGRATION_HASHES["backend/migrations/20260916_sellers_down.sql"] == "8037233A5D66BA327C976053EB97922B2DDE30AC244771DC8ADCAD732FBFD5FB"


def test_packager_allows_package_after_runtime_secrets_are_removed(tmp_path):
    builder = _load_builder()
    meta, _ = builder.parse_manifest(ROOT / "deploy" / "whatsapp_sellers_manifest.txt")
    commit = meta["version_commit"]

    builder.main([
        "--commit",
        commit,
        "--manifest",
        str(ROOT / "deploy" / "whatsapp_sellers_manifest.txt"),
        "--output-dir",
        str(tmp_path),
    ])

    zips = list(tmp_path.glob("*.zip"))
    assert len(zips) == 1


def test_parent_commit_helper():
    builder = _load_builder()
    parent = builder.parent_commit("HEAD")
    assert len(parent) == 40
    assert parent != builder.run(["git", "rev-parse", "HEAD"]).stdout.strip()


def test_is_ancestor():
    builder = _load_builder()
    current = builder.run(["git", "rev-parse", "HEAD"]).stdout.strip()
    parent = builder.parent_commit(current)
    assert builder.is_ancestor(parent, current)
    assert not builder.is_ancestor(current, parent)


def test_version_commit_accepts_head(monkeypatch, tmp_path):
    builder = _load_builder()
    current = builder.run(["git", "rev-parse", "HEAD"]).stdout.strip()
    manifest = tmp_path / "manifest.txt"
    manifest.write_text(
        f"version_commit={current}\n"
        "branch=test\n"
        "package_name=test.zip\n\n"
        "[runtime]\nREADME.md\n\n"
        "[migrations]\n\n"
        "[migration_order]\n\n"
        "[rollback_order]\n\n"
        "[expected_config_names]\n\n"
        "[services]\n\n"
        "[smoke_tests]\n\n"
        "[rollback]\n",
        encoding="utf-8",
    )
    meta, sections = builder.parse_manifest(manifest)
    assert meta["version_commit"] == current


def test_version_commit_accepts_parent():
    builder = _load_builder()
    current = builder.run(["git", "rev-parse", "HEAD"]).stdout.strip()
    parent = builder.parent_commit(current)
    assert parent is not None
    assert len(parent) == 40
    assert builder.is_ancestor(parent, current)


def test_version_commit_accepts_old_ancestor():
    builder = _load_builder()
    current = builder.run(["git", "rev-parse", "HEAD"]).stdout.strip()
    parent = builder.parent_commit(current)
    grandparent = builder.parent_commit(parent)
    assert builder.is_ancestor(grandparent, current)


def test_version_commit_rejects_non_ancestor(monkeypatch, tmp_path):
    builder = _load_builder()
    current = builder.run(["git", "rev-parse", "HEAD"]).stdout.strip()
    fake_commit = "0000000000000000000000000000000000000000"
    manifest = tmp_path / "manifest.txt"
    manifest.write_text(
        f"version_commit={fake_commit}\n"
        "branch=test\n"
        "package_name=test.zip\n\n"
        "[runtime]\nREADME.md\n\n"
        "[migrations]\n\n"
        "[migration_order]\n\n"
        "[rollback_order]\n\n"
        "[expected_config_names]\n\n"
        "[services]\n\n"
        "[smoke_tests]\n\n"
        "[rollback]\n",
        encoding="utf-8",
    )
    with pytest.raises(builder.PackageError, match="nao e ancestral"):
        builder.main([
            "--commit", current,
            "--manifest", str(manifest),
            "--output-dir", str(tmp_path),
            "--no-require-published",
        ])
