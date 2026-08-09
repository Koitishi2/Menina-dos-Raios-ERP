import hashlib
import importlib.util
import os
import shutil
import sys
import uuid
from dataclasses import dataclass
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
REAL_BACKEND = PROJECT_ROOT / "backend"
REAL_STATIC = REAL_BACKEND / "static"
REAL_DB_FILES = [
    REAL_BACKEND / "bm_monteiro.db",
    REAL_BACKEND / "menina_estrada.db",
    REAL_BACKEND / "app_notes.db",
]
REAL_WATCH_DIRS = [
    REAL_BACKEND / "backups",
    PROJECT_ROOT / "backups",
    REAL_BACKEND / "monteiro_notas",
]


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _file_snapshot(path: Path):
    if not path.exists():
        return {"exists": False}
    st = path.stat()
    return {
        "exists": True,
        "size": st.st_size,
        "mtime_ns": st.st_mtime_ns,
        "sha256": _sha256(path),
    }


def _dir_snapshot(path: Path):
    if not path.exists():
        return {"exists": False, "items": []}
    items = []
    for child in sorted(path.rglob("*")):
        if child.is_file():
            rel = str(child.relative_to(path))
            st = child.stat()
            items.append((rel, st.st_size, st.st_mtime_ns))
    return {"exists": True, "items": items}


def _is_relative_to(child: Path, parent: Path) -> bool:
    try:
        child.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def _real_db_has_sales(path: Path) -> bool:
    if not path.exists():
        return False
    import sqlite3

    try:
        conn = sqlite3.connect(str(path))
        row = conn.execute(
            "SELECT 1 FROM sqlite_master WHERE type='table' AND name='sales'"
        ).fetchone()
        conn.close()
        return bool(row)
    except Exception:
        return False


@dataclass
class IsolatedApp:
    client: TestClient
    module: object
    temp_root: Path
    temp_backend: Path
    db_paths: dict
    backup_dir: Path
    notes_dir: Path
    external_calls: list
    real_db_before: dict
    real_dir_before: dict
    real_db_sales_presence: dict

    def assert_real_unchanged(self):
        for path, before in self.real_db_before.items():
            assert _file_snapshot(path) == before, f"Banco real alterado: {path}"
        for path, before in self.real_dir_before.items():
            assert _dir_snapshot(path) == before, f"Diretorio real alterado: {path}"
        assert self.external_calls == [], f"Servico externo chamado: {self.external_calls}"


@pytest.fixture()
def isolated_app(tmp_path, monkeypatch):
    real_db_before = {path: _file_snapshot(path) for path in REAL_DB_FILES}
    real_dir_before = {path: _dir_snapshot(path) for path in REAL_WATCH_DIRS}
    real_db_sales_presence = {path: _real_db_has_sales(path) for path in REAL_DB_FILES}

    temp_root = tmp_path / "isolated_project"
    temp_backend = temp_root / "backend"
    temp_static = temp_backend / "static"
    temp_backup = temp_root / "backups"
    temp_notes = temp_backend / "monteiro_notas"
    temp_static.mkdir(parents=True)
    temp_backup.mkdir(parents=True)
    temp_notes.mkdir(parents=True)

    shutil.copy2(REAL_BACKEND / "app.py", temp_backend / "app.py")
    shutil.copy2(REAL_BACKEND / "backup_admin.py", temp_backend / "backup_admin.py")
    shutil.copy2(REAL_BACKEND / "company_config.py", temp_backend / "company_config.py")
    shutil.copy2(REAL_BACKEND / "monteiro_periods.py", temp_backend / "monteiro_periods.py")
    shutil.copy2(REAL_BACKEND / "orcamentos.py", temp_backend / "orcamentos.py")
    shutil.copy2(REAL_BACKEND / "permissions_tabs.py", temp_backend / "permissions_tabs.py")
    shutil.copy2(REAL_BACKEND / "security_auth.py", temp_backend / "security_auth.py")
    shutil.copy2(REAL_BACKEND / "security_request.py", temp_backend / "security_request.py")
    shutil.copy2(REAL_BACKEND / "schemas.py", temp_backend / "schemas.py")
    shutil.copy2(REAL_BACKEND / "utils.py", temp_backend / "utils.py")
    shutil.copy2(REAL_STATIC / "index.html", temp_static / "index.html")

    db_paths = {
        "raios": temp_backend / "bm_monteiro.db",
        "estrada": temp_backend / "menina_estrada.db",
        "app_notes": temp_backend / "app_notes.db",
    }

    candidate_paths = [*db_paths.values(), temp_backup, temp_notes]
    for candidate in candidate_paths:
        resolved = candidate.resolve()
        assert not _is_relative_to(resolved, PROJECT_ROOT), (
            f"BLOQUEADO: caminho temporario aponta para o projeto real: {resolved}"
        )
        assert "opt/menina" not in str(resolved).replace("\\", "/").lower(), (
            f"BLOQUEADO: caminho temporario parece producao: {resolved}"
        )

    for real_path, has_sales in real_db_sales_presence.items():
        if has_sales:
            assert real_path.resolve() not in [p.resolve() for p in db_paths.values()], (
                f"BLOQUEADO: banco real com sales seria usado: {real_path}"
            )

    monkeypatch.setenv("BACKUP_DIR", str(temp_backup))
    monkeypatch.setenv("CORS_ORIGINS", "*")
    monkeypatch.syspath_prepend(str(temp_backend))
    sys.modules.pop("backend.app", None)

    module_name = f"isolated_backend_app_{uuid.uuid4().hex}"
    spec = importlib.util.spec_from_file_location(module_name, temp_backend / "app.py")
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)

    assert module.DB_PATH.resolve() == db_paths["raios"].resolve()
    assert module.COMPANY_DBS["raios"].resolve() == db_paths["raios"].resolve()
    assert module.COMPANY_DBS["estrada"].resolve() == db_paths["estrada"].resolve()
    assert module.APP_NOTES_DB_PATH.resolve() == db_paths["app_notes"].resolve()
    assert module.BACKUP_DIR.resolve() == temp_backup.resolve()
    assert module.MONTEIRO_NOTES_DIR.resolve() == temp_notes.resolve()
    for path in [
        module.DB_PATH,
        *module.COMPANY_DBS.values(),
        module.APP_NOTES_DB_PATH,
        module.BACKUP_DIR,
        module.MONTEIRO_NOTES_DIR,
    ]:
        assert not _is_relative_to(Path(path), PROJECT_ROOT), (
            f"BLOQUEADO: app isolado apontou para caminho real: {path}"
        )

    external_calls = []

    def _blocked_external(*args, **kwargs):
        external_calls.append({"args": args, "kwargs": kwargs})
        raise AssertionError("Servico externo nao deve ser chamado nos testes isolados")

    module.wa_send = _blocked_external
    module.backup_scheduler = lambda: None
    module.motivation_scheduler = lambda: None

    with TestClient(module.app) as client:
        ctx = IsolatedApp(
            client=client,
            module=module,
            temp_root=temp_root,
            temp_backend=temp_backend,
            db_paths=db_paths,
            backup_dir=temp_backup,
            notes_dir=temp_notes,
            external_calls=external_calls,
            real_db_before=real_db_before,
            real_dir_before=real_dir_before,
            real_db_sales_presence=real_db_sales_presence,
        )
        yield ctx

    ctx.assert_real_unchanged()
