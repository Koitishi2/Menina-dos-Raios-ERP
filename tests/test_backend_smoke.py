import json
import os
import sqlite3
import zipfile
from pathlib import Path
from urllib.parse import quote

import pytest


def _make_sqlite_db(path):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE marker(id INTEGER PRIMARY KEY, value TEXT)")
    conn.execute("INSERT INTO marker(value) VALUES('ok')")
    conn.commit()
    conn.close()
    return path


def _make_sqlite_db_with_marker(path, value):
    conn = sqlite3.connect(path)
    conn.execute("CREATE TABLE marker(id INTEGER PRIMARY KEY, value TEXT)")
    conn.execute("INSERT INTO marker(value) VALUES(?)", (value,))
    conn.commit()
    conn.close()
    return path


def _sqlite_rows(path, sql):
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        return [dict(row) for row in conn.execute(sql).fetchall()]
    finally:
        conn.close()


def _configure_temp_backup_env(isolated_app, tmp_path, monkeypatch):
    base_dir = tmp_path / "backup_backend"
    backup_dir = tmp_path / "backup_output"
    base_dir.mkdir(parents=True)
    backup_dir.mkdir(parents=True)

    main_db = _make_sqlite_db(base_dir / "bm_monteiro.db")
    estrada_db = _make_sqlite_db(base_dir / "menina_estrada.db")
    app_notes = _make_sqlite_db(base_dir / "app_notes.db")
    extra_db = _make_sqlite_db(base_dir / "extra_data.db")
    ignored = base_dir / "ignored.txt"
    ignored.write_text("fora do backup", encoding="utf-8")

    monkeypatch.setattr(isolated_app.module, "BASE_DIR", base_dir)
    monkeypatch.setattr(isolated_app.module, "BACKUP_DIR", backup_dir)
    monkeypatch.setattr(isolated_app.module, "DB_PATH", main_db)
    monkeypatch.setattr(
        isolated_app.module,
        "COMPANY_DBS",
        {"raios": main_db, "estrada": estrada_db},
    )
    monkeypatch.setattr(isolated_app.module, "APP_NOTES_DB_PATH", app_notes)
    isolated_app.module.init_db()

    return {
        "base_dir": base_dir,
        "backup_dir": backup_dir,
        "main_db": main_db,
        "estrada_db": estrada_db,
        "app_notes": app_notes,
        "extra_db": extra_db,
        "ignored": ignored,
    }


def _write_restore_zip(path, members):
    with zipfile.ZipFile(path, "w") as zf:
        for arcname, source in members:
            if isinstance(source, bytes):
                zf.writestr(arcname, source)
            else:
                zf.write(source, arcname=arcname)
    return path


def _admin_headers(isolated_app):
    response = isolated_app.client.post(
        "/api/auth/login",
        headers={"x-company": "raios"},
        json={"username": "admin", "password": "admin123"},
    )
    assert response.status_code == 200
    return {"x-token": response.json()["token"]}


def _backup_route(filename):
    return f"/api/admin/backup/{quote(filename, safe='')}"


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


def test_company_key_current_normalization_fallback_and_state(isolated_app):
    module = isolated_app.module
    company_key = module._company_key
    current_before = module.CURRENT_COMPANY.get()
    company_dbs_before = dict(module.COMPANY_DBS)

    cases = [
        (None, "raios"),
        ("", "raios"),
        ("   ", "raios"),
        ("raios", "raios"),
        ("RAIOS", "raios"),
        ("RaIoS", "raios"),
        ("estrada", "estrada"),
        (" ESTRADA ", "estrada"),
        ("EsTrAdA", "estrada"),
        ("desconhecida", "raios"),
        ("../estrada", "raios"),
        (123, "raios"),
        ([], "raios"),
        (["estrada"], "raios"),
    ]
    for value, expected in cases:
        result = company_key(value)
        assert result == expected
        assert isinstance(result, str)

    assert module.CURRENT_COMPANY.get() == current_before
    assert module.COMPANY_DBS == company_dbs_before


def test_company_db_path_current_selection_fallback_and_no_filesystem_side_effects(
    isolated_app, tmp_path, monkeypatch
):
    module = isolated_app.module
    company_db_path = module._company_db_path
    main_db = tmp_path / "paths" / "bm_monteiro.db"
    estrada_db = tmp_path / "paths" / "menina_estrada.db"
    raios_alt_db = tmp_path / "paths" / "raios_alt.db"

    monkeypatch.setattr(module, "DB_PATH", main_db)
    monkeypatch.setattr(module, "COMPANY_DBS", {"raios": raios_alt_db, "estrada": estrada_db})
    company_dbs_before = dict(module.COMPANY_DBS)

    assert company_db_path("raios") == raios_alt_db
    assert company_db_path(" RAIOS ") == raios_alt_db
    assert company_db_path("estrada") == estrada_db
    assert company_db_path(" EsTrAdA ") == estrada_db
    assert company_db_path("desconhecida") == raios_alt_db
    assert company_db_path(None) == raios_alt_db
    assert company_db_path("") == raios_alt_db
    assert company_db_path(123) == raios_alt_db
    assert isinstance(company_db_path("raios"), Path)

    assert not main_db.exists()
    assert not estrada_db.exists()
    assert not raios_alt_db.exists()
    assert not main_db.parent.exists()
    assert module.COMPANY_DBS == company_dbs_before


def test_company_db_path_current_falls_back_to_db_path_when_raios_is_not_configured(
    isolated_app, tmp_path, monkeypatch
):
    module = isolated_app.module
    company_db_path = module._company_db_path
    main_db = tmp_path / "missing_raios" / "bm_monteiro.db"
    estrada_db = tmp_path / "missing_raios" / "menina_estrada.db"

    monkeypatch.setattr(module, "DB_PATH", main_db)
    monkeypatch.setattr(module, "COMPANY_DBS", {"estrada": estrada_db})
    company_dbs_before = dict(module.COMPANY_DBS)

    assert module._company_key("raios") == "raios"
    assert company_db_path("raios") == main_db
    assert company_db_path("desconhecida") == main_db
    assert company_db_path(None) == main_db
    assert company_db_path("estrada") == estrada_db

    assert not main_db.exists()
    assert not estrada_db.exists()
    assert not main_db.parent.exists()
    assert module.COMPANY_DBS == company_dbs_before


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


def test_backup_path_for_filename_contains_paths_after_basic_name_validation(isolated_app, tmp_path):
    backup_path_for_filename = isolated_app.module.backup_path_for_filename
    backup_dir = tmp_path / "backups"
    backup_dir.mkdir()
    inside_dir = backup_dir / "bm_backup_sub"
    inside_dir.mkdir()
    outside = tmp_path / "outside.zip"
    similar_prefix = tmp_path / "backups_extra" / "outside.zip"

    assert backup_path_for_filename("bm_backup_2026.zip", backup_dir) == (
        backup_dir / "bm_backup_2026.zip"
    ).resolve()
    assert backup_path_for_filename("bm_backup_sub\\inside.zip", backup_dir) == (
        inside_dir / "inside.zip"
    ).resolve()

    rejected = [
        "bm_backup_x\\..\\..\\outside.zip",
        "bm_backup_x/../../outside.zip",
        f"bm_backup_x\\..\\..\\{similar_prefix.name}\\outside.zip",
        str(outside),
        "",
        "backup_2026.zip",
    ]
    for filename in rejected:
        with pytest.raises(isolated_app.module.HTTPException) as exc:
            backup_path_for_filename(filename, backup_dir)
        assert exc.value.status_code == 400
        assert exc.value.detail == "Arquivo invÃ¡lido."


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


def test_create_backup_current_auto_zip_manifest_and_sqlite_content(
    isolated_app,
    tmp_path,
    monkeypatch,
):
    env = _configure_temp_backup_env(isolated_app, tmp_path, monkeypatch)
    create_backup = isolated_app.module.create_backup

    filename = create_backup("auto")
    backup_path = env["backup_dir"] / filename

    assert filename.startswith("bm_backup_")
    assert filename.endswith("_auto.zip")
    assert isolated_app.module._valid_backup_name(filename) is True
    assert backup_path.exists()
    assert backup_path.stat().st_size > 0
    assert not backup_path.resolve().is_relative_to(Path.cwd().resolve())

    with zipfile.ZipFile(backup_path, "r") as zf:
        names = zf.namelist()
        assert "manifest.json" in names
        assert "databases/bm_monteiro.db" in names
        assert "databases/menina_estrada.db" in names
        assert "databases/app_notes.db" in names
        assert "databases/extra_data.db" in names
        assert "ignored.txt" not in names
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        copied_main = tmp_path / "copied_main.db"
        copied_main.write_bytes(zf.read("databases/bm_monteiro.db"))

    assert manifest["label"] == "auto"
    assert manifest["version"] == "multi-db-v1"
    assert [item["filename"] for item in manifest["databases"]] == [
        "bm_monteiro.db",
        "menina_estrada.db",
        "app_notes.db",
        "extra_data.db",
    ]
    assert [item["archive_path"] for item in manifest["databases"]] == [
        "databases/bm_monteiro.db",
        "databases/menina_estrada.db",
        "databases/app_notes.db",
        "databases/extra_data.db",
    ]
    assert _sqlite_rows(copied_main, "SELECT value FROM marker") == [{"value": "ok"}]

    source_conn = sqlite3.connect(env["main_db"])
    try:
        source_conn.execute("INSERT INTO marker(value) VALUES('apos-backup')")
        source_conn.commit()
    finally:
        source_conn.close()
    assert _sqlite_rows(env["main_db"], "SELECT value FROM marker ORDER BY id") == [
        {"value": "ok"},
        {"value": "apos-backup"},
    ]


def test_create_backup_current_retention_uses_temp_backup_dir(
    isolated_app,
    tmp_path,
    monkeypatch,
):
    env = _configure_temp_backup_env(isolated_app, tmp_path, monkeypatch)
    monkeypatch.setattr(isolated_app.module, "MAX_BACKUPS", 2)
    backup_dir = env["backup_dir"]

    old_files = [
        backup_dir / "bm_backup_20260101_000000_old0.zip",
        backup_dir / "bm_backup_20260101_000001_old1.zip",
        backup_dir / "bm_backup_20260101_000002_old2.zip",
    ]
    for index, path in enumerate(old_files):
        path.write_text(path.name, encoding="utf-8")
        os.utime(path, (1000 + index, 1000 + index))

    created = isolated_app.module.create_backup("manual")
    remaining = sorted(path.name for path in backup_dir.glob("bm_backup_*"))

    assert created in remaining
    assert len(remaining) == 2
    assert "bm_backup_20260101_000002_old2.zip" in remaining
    assert "bm_backup_20260101_000000_old0.zip" not in remaining
    assert "bm_backup_20260101_000001_old1.zip" not in remaining


def test_create_backup_current_error_and_empty_source_contract(
    isolated_app,
    tmp_path,
    monkeypatch,
):
    base_dir = tmp_path / "empty_backend"
    backup_dir = tmp_path / "backups"
    base_dir.mkdir()
    backup_dir.mkdir()

    monkeypatch.setattr(isolated_app.module, "BASE_DIR", base_dir)
    monkeypatch.setattr(isolated_app.module, "BACKUP_DIR", backup_dir)
    monkeypatch.setattr(isolated_app.module, "DB_PATH", base_dir / "missing_main.db")
    monkeypatch.setattr(
        isolated_app.module,
        "COMPANY_DBS",
        {"raios": base_dir / "missing_main.db", "estrada": base_dir / "missing_estrada.db"},
    )
    monkeypatch.setattr(isolated_app.module, "APP_NOTES_DB_PATH", base_dir / "missing_notes.db")

    assert isolated_app.module.create_backup("manual") == ""
    assert list(backup_dir.glob("bm_backup_*")) == []

    env = _configure_temp_backup_env(isolated_app, tmp_path / "with_sources", monkeypatch)
    missing_backup_dir = tmp_path / "missing_backup_dir"
    monkeypatch.setattr(isolated_app.module, "BACKUP_DIR", missing_backup_dir)

    with pytest.raises(FileNotFoundError):
        isolated_app.module.create_backup("manual")
    assert not missing_backup_dir.exists()
    assert _sqlite_rows(env["main_db"], "SELECT value FROM marker") == [{"value": "ok"}]


def test_safety_backup_before_restore_current_pre_restore_zip_contract(
    isolated_app,
    tmp_path,
    monkeypatch,
):
    env = _configure_temp_backup_env(isolated_app, tmp_path, monkeypatch)

    filename = isolated_app.module._safety_backup_before_restore()
    backup_path = env["backup_dir"] / filename

    assert filename.startswith("bm_backup_")
    assert filename.endswith("_pre_restore.zip")
    assert isolated_app.module._valid_backup_name(filename) is True
    assert backup_path.exists()
    assert backup_path.stat().st_size > 0
    assert not backup_path.resolve().is_relative_to(Path.cwd().resolve())

    with zipfile.ZipFile(backup_path, "r") as zf:
        names = zf.namelist()
        assert "manifest.json" in names
        assert "databases/bm_monteiro.db" in names
        assert "databases/menina_estrada.db" in names
        assert "databases/app_notes.db" in names
        assert "databases/extra_data.db" in names
        manifest = json.loads(zf.read("manifest.json").decode("utf-8"))
        copied_main = tmp_path / "pre_restore_main.db"
        copied_main.write_bytes(zf.read("databases/bm_monteiro.db"))

    assert manifest["label"] == "pre_restore"
    assert manifest["version"] == "multi-db-v1"
    assert [item["filename"] for item in manifest["databases"]] == [
        "bm_monteiro.db",
        "menina_estrada.db",
        "app_notes.db",
        "extra_data.db",
    ]
    assert _sqlite_rows(copied_main, "SELECT value FROM marker") == [{"value": "ok"}]
    assert _sqlite_rows(env["main_db"], "SELECT value FROM marker") == [{"value": "ok"}]

    source_conn = sqlite3.connect(env["main_db"])
    try:
        source_conn.execute("INSERT INTO marker(value) VALUES('apos-safety')")
        source_conn.commit()
    finally:
        source_conn.close()
    assert _sqlite_rows(env["main_db"], "SELECT value FROM marker ORDER BY id") == [
        {"value": "ok"},
        {"value": "apos-safety"},
    ]


def test_safety_backup_before_restore_current_error_contract(
    isolated_app,
    tmp_path,
    monkeypatch,
):
    base_dir = tmp_path / "empty_backend"
    backup_dir = tmp_path / "backups"
    base_dir.mkdir()
    backup_dir.mkdir()

    monkeypatch.setattr(isolated_app.module, "BASE_DIR", base_dir)
    monkeypatch.setattr(isolated_app.module, "BACKUP_DIR", backup_dir)
    monkeypatch.setattr(isolated_app.module, "DB_PATH", base_dir / "missing_main.db")
    monkeypatch.setattr(
        isolated_app.module,
        "COMPANY_DBS",
        {"raios": base_dir / "missing_main.db", "estrada": base_dir / "missing_estrada.db"},
    )
    monkeypatch.setattr(isolated_app.module, "APP_NOTES_DB_PATH", base_dir / "missing_notes.db")

    assert isolated_app.module._safety_backup_before_restore() == ""
    assert list(backup_dir.glob("bm_backup_*")) == []

    env = _configure_temp_backup_env(isolated_app, tmp_path / "with_sources", monkeypatch)
    missing_backup_dir = tmp_path / "missing_backup_dir"
    monkeypatch.setattr(isolated_app.module, "BACKUP_DIR", missing_backup_dir)

    with pytest.raises(FileNotFoundError):
        isolated_app.module._safety_backup_before_restore()
    assert not missing_backup_dir.exists()
    assert _sqlite_rows(env["main_db"], "SELECT value FROM marker") == [{"value": "ok"}]


def test_restore_zip_backup_current_valid_allowlist_and_destination_contract(
    isolated_app,
    tmp_path,
    monkeypatch,
):
    env = _configure_temp_backup_env(isolated_app, tmp_path, monkeypatch)
    restored_main = _make_sqlite_db_with_marker(tmp_path / "restored_main.db", "restored-main")
    restored_notes = _make_sqlite_db_with_marker(tmp_path / "restored_notes.db", "restored-notes")
    unknown_db = _make_sqlite_db_with_marker(tmp_path / "unknown.db", "unknown")
    archive = _write_restore_zip(
        tmp_path / "restore.zip",
        [
            ("databases/bm_monteiro.db", restored_main),
            ("databases/app_notes.db", restored_notes),
            ("databases/unknown.db", unknown_db),
            ("databases/ignored.txt", b"fora"),
        ],
    )

    restored = isolated_app.module._restore_zip_backup(archive)

    assert restored == ["bm_monteiro.db", "app_notes.db"]
    assert _sqlite_rows(env["main_db"], "SELECT value FROM marker") == [
        {"value": "restored-main"}
    ]
    assert _sqlite_rows(env["app_notes"], "SELECT value FROM marker") == [
        {"value": "restored-notes"}
    ]
    assert _sqlite_rows(env["estrada_db"], "SELECT value FROM marker") == [{"value": "ok"}]
    assert not (env["base_dir"] / "unknown.db").exists()

    conn = sqlite3.connect(env["main_db"])
    try:
        conn.execute("INSERT INTO marker(value) VALUES('apos-restore')")
        conn.commit()
    finally:
        conn.close()
    assert _sqlite_rows(env["main_db"], "SELECT value FROM marker ORDER BY id") == [
        {"value": "restored-main"},
        {"value": "apos-restore"},
    ]


def test_restore_zip_backup_current_zip_error_contract(
    isolated_app,
    tmp_path,
    monkeypatch,
):
    _configure_temp_backup_env(isolated_app, tmp_path, monkeypatch)

    with pytest.raises(FileNotFoundError):
        isolated_app.module._restore_zip_backup(tmp_path / "missing.zip")

    not_zip = tmp_path / "not_zip.zip"
    not_zip.write_text("nao sou zip", encoding="utf-8")
    with pytest.raises(zipfile.BadZipFile):
        isolated_app.module._restore_zip_backup(not_zip)

    empty_zip = _write_restore_zip(tmp_path / "empty.zip", [])
    with pytest.raises(isolated_app.module.HTTPException) as no_members:
        isolated_app.module._restore_zip_backup(empty_zip)
    assert no_members.value.status_code == 400
    assert no_members.value.detail == "Pacote de backup nÃ£o possui bancos de dados."

    no_known = _write_restore_zip(
        tmp_path / "no_known.zip",
        [("databases/unknown.db", _make_sqlite_db(tmp_path / "unknown_restore.db"))],
    )
    with pytest.raises(isolated_app.module.HTTPException) as no_restored:
        isolated_app.module._restore_zip_backup(no_known)
    assert no_restored.value.status_code == 400
    assert no_restored.value.detail == "Nenhum banco reconhecido foi restaurado."


def test_restore_zip_backup_current_invalid_sqlite_and_textual_path_contract(
    isolated_app,
    tmp_path,
    monkeypatch,
):
    env = _configure_temp_backup_env(isolated_app, tmp_path, monkeypatch)

    invalid_sqlite = _write_restore_zip(
        tmp_path / "invalid_sqlite.zip",
        [("databases/bm_monteiro.db", b"nao sou sqlite")],
    )
    with pytest.raises(isolated_app.module.HTTPException) as invalid:
        isolated_app.module._restore_zip_backup(invalid_sqlite)
    assert invalid.value.status_code == 400
    assert invalid.value.detail == "Banco invÃ¡lido dentro do backup: bm_monteiro.db"
    assert _sqlite_rows(env["main_db"], "SELECT value FROM marker") == [{"value": "ok"}]

    traversal_db = _make_sqlite_db_with_marker(tmp_path / "traversal.db", "via-traversal")
    traversal_zip = _write_restore_zip(
        tmp_path / "traversal.zip",
        [("databases/..\\bm_monteiro.db", traversal_db.read_bytes())],
    )

    restored = isolated_app.module._restore_zip_backup(traversal_zip)

    assert restored == ["bm_monteiro.db"]
    assert _sqlite_rows(env["main_db"], "SELECT value FROM marker") == [
        {"value": "via-traversal"}
    ]
    assert not (env["base_dir"].parent / "bm_monteiro.db").exists()


def test_backup_routes_current_listing_status_and_manual_backup_contract(
    isolated_app,
    tmp_path,
    monkeypatch,
):
    env = _configure_temp_backup_env(isolated_app, tmp_path, monkeypatch)
    headers = _admin_headers(isolated_app)
    existing_zip = _write_restore_zip(
        env["backup_dir"] / "bm_backup_20260101_000000_manual.zip",
        [("databases/bm_monteiro.db", env["main_db"])],
    )
    existing_db = _make_sqlite_db(env["backup_dir"] / "bm_backup_20260101_000001_manual.db")
    os.utime(existing_zip, (1000, 1000))
    os.utime(existing_db, (2000, 2000))

    listing = isolated_app.client.get("/api/admin/backups", headers=headers)
    assert listing.status_code == 200
    listed = listing.json()
    assert [item["filename"] for item in listed] == [
        "bm_backup_20260101_000001_manual.db",
        "bm_backup_20260101_000000_manual.zip",
    ]
    assert listed[0]["kind"] == "banco"
    assert listed[0]["databases"] == ["bm_monteiro.db"]
    assert listed[1]["kind"] == "pacote"
    assert listed[1]["databases"] == []

    status = isolated_app.client.get("/api/admin/backup-status", headers=headers)
    assert status.status_code == 200
    status_payload = status.json()
    assert status_payload["total"] == 2
    assert status_payload["last"]["filename"] == "bm_backup_20260101_000001_manual.db"
    assert status_payload["included_databases"] == [
        "bm_monteiro.db",
        "menina_estrada.db",
        "app_notes.db",
        "extra_data.db",
    ]

    manual = isolated_app.client.post("/api/admin/backup", headers=headers)
    assert manual.status_code == 200
    manual_payload = manual.json()
    assert manual_payload["ok"] is True
    assert manual_payload["filename"].endswith("_manual.zip")
    assert (env["backup_dir"] / manual_payload["filename"]).exists()


def test_backup_routes_current_download_delete_and_textual_escape_contract(
    isolated_app,
    tmp_path,
    monkeypatch,
):
    env = _configure_temp_backup_env(isolated_app, tmp_path, monkeypatch)
    headers = _admin_headers(isolated_app)
    simple = env["backup_dir"] / "bm_backup_20260101_000000_manual.db"
    simple.write_bytes(b"simple-backup")
    subdir = env["backup_dir"] / "bm_backup_sub"
    subdir.mkdir()
    nested = subdir / "inside.zip"
    nested.write_bytes(b"nested-backup")
    escape_parent = env["backup_dir"].parent
    escaped = escape_parent / "outside.zip"
    escaped.write_bytes(b"outside-backup")
    (env["backup_dir"] / "bm_backup_x").mkdir()
    escape_filename = "bm_backup_x\\..\\..\\outside.zip"
    resolved_escape = (env["backup_dir"] / escape_filename).resolve()
    assert resolved_escape == escaped.resolve()
    assert resolved_escape.is_relative_to(tmp_path.resolve())
    assert not resolved_escape.is_relative_to(env["backup_dir"].resolve())

    download_simple = isolated_app.client.get(_backup_route(simple.name), headers=headers)
    assert download_simple.status_code == 200
    assert download_simple.content == b"simple-backup"

    download_nested = isolated_app.client.get(
        _backup_route("bm_backup_sub\\inside.zip"),
        headers=headers,
    )
    assert download_nested.status_code == 200
    assert download_nested.content == b"nested-backup"

    download_escaped = isolated_app.client.get(_backup_route(escape_filename), headers=headers)
    assert download_escaped.status_code == 400
    assert download_escaped.json()["detail"] == "Arquivo invÃ¡lido."
    assert escaped.exists()

    unknown = isolated_app.client.get(_backup_route("bm_backup_missing.zip"), headers=headers)
    assert unknown.status_code == 404
    assert unknown.json()["detail"] == "Backup nÃ£o encontrado."

    invalid = isolated_app.client.get(_backup_route("backup_manual.zip"), headers=headers)
    assert invalid.status_code == 400
    assert invalid.json()["detail"] == "Arquivo invÃ¡lido."

    encoded_slash = isolated_app.client.get(
        "/api/admin/backup/bm_backup_sub%2Finside.zip",
        headers=headers,
    )
    assert encoded_slash.status_code == 200
    assert "text/html" in encoded_slash.headers.get("content-type", "")
    assert b"nested-backup" not in encoded_slash.content

    delete_simple = isolated_app.client.delete(_backup_route(simple.name), headers=headers)
    assert delete_simple.status_code == 200
    assert delete_simple.json() == {"ok": True}
    assert not simple.exists()

    delete_escaped = isolated_app.client.delete(_backup_route(escape_filename), headers=headers)
    assert delete_escaped.status_code == 400
    assert delete_escaped.json()["detail"] == "Arquivo invÃ¡lido."
    assert escaped.exists()


def test_backup_route_current_restore_by_filename_contract(
    isolated_app,
    tmp_path,
    monkeypatch,
):
    env = _configure_temp_backup_env(isolated_app, tmp_path, monkeypatch)
    headers = _admin_headers(isolated_app)
    restored_main = _make_sqlite_db_with_marker(tmp_path / "route_restore_main.db", "route-main")
    archive = _write_restore_zip(
        env["backup_dir"] / "bm_backup_20260101_000000_manual.zip",
        [("databases/bm_monteiro.db", restored_main)],
    )
    escape_parent = env["backup_dir"].parent
    escaped_archive = _write_restore_zip(
        escape_parent / "outside.zip",
        [("databases/bm_monteiro.db", restored_main)],
    )
    (env["backup_dir"] / "bm_backup_x").mkdir()
    escape_filename = "bm_backup_x\\..\\..\\outside.zip"

    invalid = isolated_app.client.post(_backup_route("backup_manual.zip") + "/restore", headers=headers)
    assert invalid.status_code == 400
    assert invalid.json()["detail"] == "Arquivo invÃ¡lido."

    missing = isolated_app.client.post(_backup_route("bm_backup_missing.zip") + "/restore", headers=headers)
    assert missing.status_code == 404
    assert missing.json()["detail"] == "Backup nÃ£o encontrado."

    before_safety = set(env["backup_dir"].glob("*_pre_restore.zip"))
    escaped_restore = isolated_app.client.post(_backup_route(escape_filename) + "/restore", headers=headers)
    assert escaped_restore.status_code == 400
    assert escaped_restore.json()["detail"] == "Arquivo invÃ¡lido."
    assert escaped_archive.exists()
    assert set(env["backup_dir"].glob("*_pre_restore.zip")) == before_safety
    assert _sqlite_rows(env["main_db"], "SELECT value FROM marker") == [{"value": "ok"}]

    response = isolated_app.client.post(_backup_route(archive.name) + "/restore", headers=headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["restored_from"] == archive.name
    assert payload["restored_databases"] == ["bm_monteiro.db"]
    assert payload["safety_backup"].endswith("_pre_restore.zip")
    assert (env["backup_dir"] / payload["safety_backup"]).exists()
    assert _sqlite_rows(env["main_db"], "SELECT value FROM marker") == [
        {"value": "route-main"}
    ]


def test_backup_route_current_upload_restore_contract(
    isolated_app,
    tmp_path,
    monkeypatch,
):
    env = _configure_temp_backup_env(isolated_app, tmp_path, monkeypatch)
    headers = _admin_headers(isolated_app)
    uploaded_db = _make_sqlite_db_with_marker(tmp_path / "uploaded.db", "uploaded-main")

    bad_extension = isolated_app.client.post(
        "/api/admin/backup/upload-restore",
        headers=headers,
        files={"file": ("backup.txt", b"texto", "text/plain")},
    )
    assert bad_extension.status_code == 400
    assert bad_extension.json()["detail"] == "Apenas arquivos .db ou .zip sÃ£o aceitos."

    bad_content = isolated_app.client.post(
        "/api/admin/backup/upload-restore",
        headers=headers,
        files={"file": ("backup.db", b"texto", "application/octet-stream")},
    )
    assert bad_content.status_code == 400
    assert bad_content.json()["detail"] == (
        "Arquivo enviado nÃ£o Ã© um banco SQLite nem pacote de backup vÃ¡lido."
    )

    response = isolated_app.client.post(
        "/api/admin/backup/upload-restore",
        headers=headers,
        files={"file": ("uploaded.db", uploaded_db.read_bytes(), "application/octet-stream")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["restored_from"] == "uploaded.db"
    assert payload["archived_as"].endswith("_uploaded.db")
    assert payload["safety_backup"].endswith("_pre_restore.zip")
    assert payload["restored_databases"] == ["bm_monteiro.db"]
    assert (env["backup_dir"] / payload["archived_as"]).exists()
    assert (env["backup_dir"] / payload["safety_backup"]).exists()
    assert _sqlite_rows(env["main_db"], "SELECT value FROM marker") == [
        {"value": "uploaded-main"}
    ]


def test_copy_sqlite_consistent_current_valid_copy_to_missing_destination(isolated_app, tmp_path):
    copy_sqlite_consistent = isolated_app.module._copy_sqlite_consistent
    src = tmp_path / "source.db"
    dest = tmp_path / "dest.db"
    conn = sqlite3.connect(src)
    conn.execute("CREATE TABLE marker(id INTEGER PRIMARY KEY, value TEXT)")
    conn.executemany(
        "INSERT INTO marker(value) VALUES(?)",
        [(f"linha-{index}",) for index in range(25)],
    )
    conn.execute("CREATE TABLE secondary(name TEXT, amount REAL)")
    conn.execute("INSERT INTO secondary(name, amount) VALUES('total', 123.45)")
    conn.commit()
    conn.close()

    copy_sqlite_consistent(src, dest)

    assert dest.exists()
    assert dest.stat().st_size > 0
    assert _sqlite_rows(dest, "SELECT value FROM marker ORDER BY id") == [
        {"value": f"linha-{index}"} for index in range(25)
    ]
    assert _sqlite_rows(dest, "SELECT name, amount FROM secondary") == [
        {"name": "total", "amount": 123.45}
    ]

    write_conn = sqlite3.connect(dest)
    try:
        write_conn.execute("INSERT INTO marker(value) VALUES('pos-copia')")
        write_conn.commit()
    finally:
        write_conn.close()


def test_copy_sqlite_consistent_current_overwrites_existing_destination(isolated_app, tmp_path):
    copy_sqlite_consistent = isolated_app.module._copy_sqlite_consistent
    src = _make_sqlite_db(tmp_path / "source.db")
    dest = tmp_path / "dest.db"
    conn = sqlite3.connect(dest)
    conn.execute("CREATE TABLE old_data(value TEXT)")
    conn.execute("INSERT INTO old_data(value) VALUES('sera removido')")
    conn.commit()
    conn.close()

    copy_sqlite_consistent(src, dest)

    assert _sqlite_rows(dest, "SELECT value FROM marker") == [{"value": "ok"}]
    with pytest.raises(sqlite3.OperationalError, match="no such table: old_data"):
        _sqlite_rows(dest, "SELECT value FROM old_data")


def test_copy_sqlite_consistent_current_error_contract_and_connections_close(
    isolated_app,
    tmp_path,
):
    copy_sqlite_consistent = isolated_app.module._copy_sqlite_consistent

    missing_src = tmp_path / "missing.db"
    missing_dest = tmp_path / "missing_dest.db"
    copy_sqlite_consistent(missing_src, missing_dest)
    assert missing_src.exists()
    assert missing_dest.exists()
    assert _sqlite_rows(
        missing_dest,
        "SELECT name FROM sqlite_master WHERE type='table'",
    ) == []

    invalid_src = tmp_path / "invalid.db"
    invalid_src.write_text("nao sou sqlite", encoding="utf-8")
    invalid_dest = tmp_path / "invalid_dest.db"
    with pytest.raises(sqlite3.DatabaseError):
        copy_sqlite_consistent(invalid_src, invalid_dest)

    valid_src = _make_sqlite_db(tmp_path / "valid_source.db")
    invalid_dest_path = tmp_path / "sem_pasta" / "dest.db"
    with pytest.raises(sqlite3.OperationalError):
        copy_sqlite_consistent(valid_src, invalid_dest_path)

    reopened_src = sqlite3.connect(valid_src)
    try:
        reopened_src.execute("INSERT INTO marker(value) VALUES('apos-erro')")
        reopened_src.commit()
    finally:
        reopened_src.close()
    assert _sqlite_rows(valid_src, "SELECT value FROM marker ORDER BY id") == [
        {"value": "ok"},
        {"value": "apos-erro"},
    ]
