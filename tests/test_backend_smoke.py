from pathlib import Path

import pytest


def test_backend_starts_serves_index_and_uses_temp_backup(isolated_app):
    response = isolated_app.client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers.get("content-type", "")
    assert "Monteiro" in response.text or "Menina" in response.text

    info = isolated_app.client.get("/api/server-info")
    assert info.status_code == 200
    payload = info.json()
    assert "local_url" in payload

    assert isolated_app.backup_dir.exists()
    assert not Path(isolated_app.module.BACKUP_DIR).resolve().is_relative_to(
        Path.cwd().resolve()
    )
    temp_backup_files = list(isolated_app.backup_dir.glob("bm_backup_*"))
    assert temp_backup_files, "Backup automatico de startup deve ir para pasta temporaria"


def test_lifespan_created_only_temp_databases(isolated_app):
    assert isolated_app.db_paths["raios"].exists()
    assert isolated_app.db_paths["estrada"].exists()
    for db_path in isolated_app.db_paths.values():
        assert not str(db_path.resolve()).startswith(str(Path.cwd().resolve()))
    isolated_app.assert_real_unchanged()


def test_valid_backup_name_current_prefix_extension_and_case_contract(isolated_app):
    valid_backup_name = isolated_app.module._valid_backup_name

    accepted = [
        "bm_backup_2026.db",
        "bm_backup_2026.zip",
        "bm_backup_2026.DB",
        "bm_backup_2026.ZIP",
        "bm_backup_2026 final.db",
        "bm_backup_@#$%.db",
        "bm_backup_2026.db.zip",
    ]
    for filename in accepted:
        result = valid_backup_name(filename)
        assert result is True
        assert isinstance(result, bool)

    rejected = [
        "BM_BACKUP_2026.db",
        "Bm_Backup_2026.db",
        "backup_2026.db",
        "bm_backup_2026.txt",
        "",
        "   ",
        "bm_backup_",
        "1",
        "bm_backup_2026.db.extra",
    ]
    for filename in rejected:
        result = valid_backup_name(filename)
        assert result is False
        assert isinstance(result, bool)


def test_valid_backup_name_current_textual_path_traversal_and_invalid_types(isolated_app):
    valid_backup_name = isolated_app.module._valid_backup_name

    accepted_textual_paths = [
        "bm_backup_../x.db",
        "bm_backup_dir/file.db",
        "bm_backup_dir\\file.db",
    ]
    for filename in accepted_textual_paths:
        assert valid_backup_name(filename) is True

    assert valid_backup_name("C:\\tmp\\bm_backup_2026.db") is False

    for value in (None, 123):
        with pytest.raises(AttributeError):
            valid_backup_name(value)
