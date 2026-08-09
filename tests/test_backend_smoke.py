import json
import sqlite3
import zipfile
from pathlib import Path

import pytest


def _make_sqlite_db(path):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE marker(id INTEGER PRIMARY KEY, value TEXT)")
    conn.execute("INSERT INTO marker(value) VALUES('ok')")
    conn.commit()
    conn.close()
    return path


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


def test_is_sqlite_file_current_signature_contract(isolated_app, tmp_path):
    is_sqlite_file = isolated_app.module._is_sqlite_file

    valid_db = _make_sqlite_db(tmp_path / "valid.db")
    text_file = tmp_path / "not_sqlite.db"
    text_file.write_text("nao sou sqlite", encoding="utf-8")
    short_file = tmp_path / "short.db"
    short_file.write_bytes(b"SQLite")
    directory = tmp_path / "db_dir"
    directory.mkdir()
    missing = tmp_path / "missing.db"

    assert is_sqlite_file(valid_db) is True
    assert is_sqlite_file(text_file) is False
    assert is_sqlite_file(missing) is False
    assert is_sqlite_file(directory) is False
    assert is_sqlite_file(short_file) is False


def test_backup_manifest_databases_current_zip_and_error_contract(isolated_app, tmp_path):
    manifest_databases = isolated_app.module._backup_manifest_databases

    valid_zip = tmp_path / "valid_manifest.zip"
    with zipfile.ZipFile(valid_zip, "w") as zf:
        zf.writestr(
            "manifest.json",
            json.dumps(
                {
                    "databases": [
                        {"filename": "bm_monteiro.db"},
                        {"filename": "app_notes.db"},
                        {"name": "sem_filename.db"},
                        {"filename": ""},
                    ]
                }
            ),
        )
    assert manifest_databases(valid_zip) == ["bm_monteiro.db", "app_notes.db"]

    no_manifest_zip = tmp_path / "no_manifest.zip"
    with zipfile.ZipFile(no_manifest_zip, "w") as zf:
        zf.writestr("outro.txt", "sem manifesto")
    assert manifest_databases(no_manifest_zip) == []

    invalid_manifest_zip = tmp_path / "invalid_manifest.zip"
    with zipfile.ZipFile(invalid_manifest_zip, "w") as zf:
        zf.writestr("manifest.json", "{json-invalido")
    assert manifest_databases(invalid_manifest_zip) == []

    unexpected_manifest_zip = tmp_path / "unexpected_manifest.zip"
    with zipfile.ZipFile(unexpected_manifest_zip, "w") as zf:
        zf.writestr("manifest.json", json.dumps({"databases": {"filename": "x.db"}}))
    assert manifest_databases(unexpected_manifest_zip) == []

    missing_zip = tmp_path / "missing.zip"
    not_zip = tmp_path / "not_zip.zip"
    not_zip.write_text("nao sou zip", encoding="utf-8")
    assert manifest_databases(missing_zip) == []
    assert manifest_databases(not_zip) == []


def test_backup_files_current_directory_glob_contract(isolated_app, tmp_path, monkeypatch):
    backup_files = isolated_app.module._backup_files
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    monkeypatch.setattr(isolated_app.module, "BACKUP_DIR", backup_dir)

    assert backup_files() == []

    created = [
        backup_dir / "bm_backup_20260101_manual.zip",
        backup_dir / "bm_backup_20260101_manual.db",
        backup_dir / "bm_backup_20260101_manual.txt",
        backup_dir / "outro_backup.zip",
    ]
    for path in created:
        path.write_text(path.name, encoding="utf-8")

    expected = list(backup_dir.glob("bm_backup_*.db")) + list(
        backup_dir.glob("bm_backup_*.zip")
    )
    result = backup_files()
    assert result == expected
    assert [path.name for path in result] == [path.name for path in expected]

    missing_dir = tmp_path / "missing_backups"
    monkeypatch.setattr(isolated_app.module, "BACKUP_DIR", missing_dir)
    assert backup_files() == []


def test_backup_expected_databases_current_paths_order_and_exists_contract(
    isolated_app,
    tmp_path,
    monkeypatch,
):
    expected_databases = isolated_app.module._backup_expected_databases
    base_dir = tmp_path / "backend"
    base_dir.mkdir()
    shared_db = _make_sqlite_db(base_dir / "shared.db")
    app_notes = _make_sqlite_db(base_dir / "app_notes.db")
    missing_notes = base_dir / "missing_app_notes.db"

    monkeypatch.setattr(isolated_app.module, "BASE_DIR", base_dir)
    monkeypatch.setattr(isolated_app.module, "DB_PATH", shared_db)
    monkeypatch.setattr(
        isolated_app.module,
        "COMPANY_DBS",
        {"raios": shared_db, "estrada": shared_db},
    )
    monkeypatch.setattr(isolated_app.module, "APP_NOTES_DB_PATH", app_notes)

    result = expected_databases()
    assert result == [
        {
            "key": "raios_monteiro",
            "label": "Menina dos Raios / Monteiro",
            "name": "shared.db",
            "exists": True,
        },
        {
            "key": "estrada",
            "label": "Menina da Estrada",
            "name": "shared.db",
            "exists": True,
        },
        {
            "key": "app_notes",
            "label": "Notas APP / Calendario",
            "name": "app_notes.db",
            "exists": True,
        },
    ]

    monkeypatch.setattr(isolated_app.module, "APP_NOTES_DB_PATH", missing_notes)
    result_with_missing_notes = expected_databases()
    assert result_with_missing_notes[2] == {
        "key": "app_notes",
        "label": "Notas APP / Calendario",
        "name": "missing_app_notes.db",
        "exists": False,
    }

    missing_main = base_dir / "missing_main.db"
    monkeypatch.setattr(isolated_app.module, "DB_PATH", missing_main)
    result_with_missing_main = expected_databases()
    assert result_with_missing_main[0] == {
        "key": "raios_monteiro",
        "label": "Menina dos Raios / Monteiro",
        "name": "missing_main.db",
        "exists": False,
    }


def test_backup_db_sources_current_discovery_dedup_and_order_contract(
    isolated_app,
    tmp_path,
    monkeypatch,
):
    backup_db_sources = isolated_app.module._backup_db_sources
    base_dir = tmp_path / "backend"
    base_dir.mkdir()
    main_db = _make_sqlite_db(base_dir / "bm_monteiro.db")
    estrada_db = _make_sqlite_db(base_dir / "menina_estrada.db")
    app_notes = _make_sqlite_db(base_dir / "app_notes.db")
    extra_db = _make_sqlite_db(base_dir / "extra_data.db")
    unrelated = base_dir / "nao_entra.txt"
    unrelated.write_text("fora", encoding="utf-8")

    monkeypatch.setattr(isolated_app.module, "BASE_DIR", base_dir)
    monkeypatch.setattr(isolated_app.module, "DB_PATH", main_db)
    monkeypatch.setattr(
        isolated_app.module,
        "COMPANY_DBS",
        {"raios": main_db, "estrada": estrada_db, "duplicada": extra_db},
    )
    monkeypatch.setattr(isolated_app.module, "APP_NOTES_DB_PATH", app_notes)

    sources = backup_db_sources()
    simplified = [(item["key"], item["label"], item["path"].name) for item in sources]
    assert simplified == [
        ("raios_monteiro", "Menina dos Raios / Monteiro", "bm_monteiro.db"),
        ("empresa_estrada", "Menina da Estrada", "menina_estrada.db"),
        ("empresa_duplicada", "duplicada", "extra_data.db"),
        ("app_notes", "Notas APP / Calendario", "app_notes.db"),
    ]
    assert unrelated.name not in [item["path"].name for item in sources]
    assert [item["path"].name for item in sources].count("extra_data.db") == 1

    missing_db = base_dir / "missing.db"
    monkeypatch.setattr(isolated_app.module, "DB_PATH", missing_db)
    monkeypatch.setattr(
        isolated_app.module,
        "COMPANY_DBS",
        {"raios": missing_db, "estrada": missing_db},
    )
    monkeypatch.setattr(isolated_app.module, "APP_NOTES_DB_PATH", base_dir / "missing_notes.db")
    only_extra = backup_db_sources()
    assert [(item["key"], item["path"].name) for item in only_extra] == [
        ("extra_app_notes", "app_notes.db"),
        ("extra_bm_monteiro", "bm_monteiro.db"),
        ("extra_extra_data", "extra_data.db"),
        ("extra_menina_estrada", "menina_estrada.db"),
    ]
