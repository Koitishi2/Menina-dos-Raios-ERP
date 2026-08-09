from pathlib import Path


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
