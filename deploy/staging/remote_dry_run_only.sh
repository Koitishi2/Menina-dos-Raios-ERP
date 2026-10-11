#!/usr/bin/env bash
set -euo pipefail

: "${RUN_DIR:?RUN_DIR obrigatorio}"
: "${APP_DIR:?APP_DIR obrigatorio}"
: "${SERVICE:?SERVICE obrigatorio}"
: "${PACKAGE_NAME:?PACKAGE_NAME obrigatorio}"
: "${CHECKSUM_NAME:?CHECKSUM_NAME obrigatorio}"
: "${UPDATER_NAME:?UPDATER_NAME obrigatorio}"
: "${EXPECTED_PACKAGE_SHA256:?EXPECTED_PACKAGE_SHA256 obrigatorio}"
: "${EXPECTED_CHECKSUM_SHA256:?EXPECTED_CHECKSUM_SHA256 obrigatorio}"
: "${EXPECTED_UPDATER_SHA256:?EXPECTED_UPDATER_SHA256 obrigatorio}"

case "$RUN_DIR" in
  /root/menina_refatoracao_staging/dryrun_*) ;;
  *) echo "STAGING_INVALIDO" >&2; exit 80 ;;
esac
test "$APP_DIR" = "/opt/menina/backend"
test "$SERVICE" = "menina"

PACKAGE_PATH="$RUN_DIR/$PACKAGE_NAME"
CHECKSUM_PATH="$RUN_DIR/$CHECKSUM_NAME"
UPDATER_PATH="$RUN_DIR/$UPDATER_NAME"
REPORT_PATH="$RUN_DIR/REMOTE_DRY_RUN_REPORT.txt"
SERVICE_PYTHON="/opt/menina/venv/bin/python3"
TEMP_DIR=""

cleanup() {
  local status=$?
  set +e
  if [[ -n "$TEMP_DIR" && "$TEMP_DIR" = /tmp/menina_remote_dryrun.* ]]; then
    rm -rf -- "$TEMP_DIR"
  fi
  exit "$status"
}
trap cleanup EXIT

exec > >(tee "$REPORT_PATH") 2>&1

echo "REMOTE_DRY_RUN_BEGIN"
echo "RUN_DIR=$RUN_DIR"
echo "APP_DIR=$APP_DIR"
echo "SERVICE=$SERVICE"

for tool in sha256sum python3 systemctl runuser; do
  command -v "$tool" >/dev/null
  echo "TOOL_${tool^^}=$(command -v "$tool")"
done
if command -v rsync >/dev/null 2>&1; then
  echo "TOOL_RSYNC=$(command -v rsync)"
  echo "COPY_FALLBACK=python3_disponivel"
else
  echo "TOOL_RSYNC=ausente"
  echo "COPY_FALLBACK=python3"
fi
if [[ ! -x "$SERVICE_PYTHON" ]]; then
  echo "SERVICE_PYTHON_NOT_EXECUTABLE: $SERVICE_PYTHON" >&2
  exit 84
fi
echo "SERVICE_PYTHON=$SERVICE_PYTHON"
runuser -u menina -- "$SERVICE_PYTHON" -c 'import fastapi; print("SERVICE_PYTHON_FASTAPI_OK")'

verify_hash() {
  local expected="$1" path="$2" label="$3" actual
  actual="$(sha256sum "$path" | awk '{print toupper($1)}')"
  echo "REMOTE_${label}_SHA256=$actual"
  [[ "$actual" = "${expected^^}" ]]
}

test -f "$PACKAGE_PATH"
test -f "$CHECKSUM_PATH"
test -f "$UPDATER_PATH"
verify_hash "$EXPECTED_PACKAGE_SHA256" "$PACKAGE_PATH" "ZIP"
verify_hash "$EXPECTED_CHECKSUM_SHA256" "$CHECKSUM_PATH" "CHECKSUM"
verify_hash "$EXPECTED_UPDATER_SHA256" "$UPDATER_PATH" "SCRIPT"
(
  cd "$RUN_DIR"
  sha256sum -c "$CHECKSUM_NAME"
)
echo "REMOTE_HASHES_OK"

id menina
test -d "$APP_DIR"
runuser -u menina -- test -x "$APP_DIR"
runuser -u menina -- test -r "$APP_DIR/app.py"
echo "MENINA_READ_AND_TRAVERSE_OK"

python3 - "$UPDATER_PATH" <<'PY'
import sys
from pathlib import Path

text = Path(sys.argv[1]).read_text(encoding="utf-8")
required = (
    'verify_sha256 "$EXPECTED_PACKAGE_SHA256"',
    'verify_sha256 "$EXPECTED_SCRIPT_SHA256"',
    'set +e',
    'ROLLBACK_RESTORE_STATUS=',
    'ROLLBACK_START_STATUS=',
    'ROLLBACK_STATUS_FINAL=',
    'SERVICE_STATUS_FINAL=',
    'SERVICE_PYTHON="/opt/menina/venv/bin/python3"',
    'runuser -u menina -- env',
    'PYTHONPATH="$root"',
    'BACKUP_DIR="$root/.preflight_backups"',
    '"$SERVICE_PYTHON" - "$root"',
    "trap 'handle_signal 129' HUP",
    "trap 'handle_signal 130' INT",
    "trap 'handle_signal 143' TERM",
)
missing = [item for item in required if item not in text]
if missing:
    raise SystemExit("UPDATER_REQUISITOS_AUSENTES: " + ", ".join(missing))

forbidden = (
    'chown -R menina:menina "$APP_DIR"',
    'find "$APP_DIR"',
    'rm -rf -- "$APP_DIR"',
    'curl -fsS http://127.0.0.1:8765/health',
    'systemctl restart "$SERVICE"',
    'systemctl daemon-reload',
)
found = [item for item in forbidden if item in text]
if found:
    raise SystemExit("UPDATER_OPERACAO_AMPLA: " + ", ".join(found))

trap_index = text.index("trap 'rollback $?' ERR")
stop_index = text.index('systemctl stop "$SERVICE"', trap_index)
backup_index = text.index('copy_code_tree "$APP_DIR" "$BACKUP_DIR/backend"', stop_index)
if not stop_index < backup_index:
    raise SystemExit("ORDEM_STOP_BACKUP_INVALIDA")

rollback = text[text.index("rollback() {"):text.index("handle_signal() {")]
restore_index = rollback.index('copy_code_tree "$BACKUP_DIR/backend"')
start_index = rollback.index('systemctl start "$SERVICE"')
if not restore_index < start_index:
    raise SystemExit("ORDEM_ROLLBACK_INVALIDA")
print("UPDATER_STATIC_SECURITY_OK")
print("ROLLBACK_LOGIC_OK=restore_errors_do_not_skip_start")
PY

TEMP_DIR="$(mktemp -d /tmp/menina_remote_dryrun.XXXXXX)"
chmod 0755 "$TEMP_DIR"
echo "SIMULATION_DIR=$TEMP_DIR"

python3 - "$PACKAGE_PATH" "$TEMP_DIR/package" <<'PY'
import stat
import sys
import zipfile
from pathlib import Path, PurePosixPath

archive = Path(sys.argv[1])
destination = Path(sys.argv[2]).resolve()
blocked = {
    ".env", "uploads", "upload", "logs", "log", "data", "instance",
    "storage", "media", "backups", "backup", "database", "databases",
    "auth_info_baileys", "app-updates", "node_modules", "certificates",
    "certs", "keys", "__pycache__",
}

with zipfile.ZipFile(archive) as package:
    for info in package.infolist():
        path = PurePosixPath(info.filename)
        parts = [part.lower() for part in path.parts]
        if path.is_absolute() or ".." in path.parts or any(part in blocked for part in parts):
            raise SystemExit(f"ENTRADA_ZIP_PROIBIDA: {info.filename}")
        if any(
            part.startswith(".env.")
            or part.endswith((".env", ".db", ".sqlite", ".sqlite3", "-wal", "-shm", "-journal", ".pyc"))
            for part in parts
        ):
            raise SystemExit(f"ENTRADA_ZIP_PERSISTENTE: {info.filename}")
        if stat.S_ISLNK(info.external_attr >> 16):
            raise SystemExit(f"LINK_ZIP_PROIBIDO: {info.filename}")
        target = (destination / Path(*path.parts)).resolve()
        if destination not in target.parents and target != destination:
            raise SystemExit(f"TRAVERSAL_ZIP: {info.filename}")
    package.extractall(destination)
print("ZIP_TRAVERSAL_LINKS_PERSISTENCE_OK")
PY

chmod -R a+rX "$TEMP_DIR/package"
chown -R menina:menina "$TEMP_DIR/package"
runuser -u menina -- sh -c 'cd "$1" && exec env PYTHONPATH="$1" BACKUP_DIR="$3" WHATSAPP_OUTBOUND_ENABLED=false WHATSAPP_OUTBOUND_MODE=disabled "$2" - "$1" <<'"'"'PY'"'"'
import importlib
import py_compile
import sys
import tempfile
from pathlib import Path

base = Path(sys.argv[1]).resolve()
paths = list(base.glob("*.py"))
for name in ("domains", "repositories", "routers", "services"):
    directory = base / name
    if directory.is_dir():
        paths.extend(directory.rglob("*.py"))
with tempfile.TemporaryDirectory(prefix="menina_remote_compile_") as output:
    target = Path(output)
    for index, path in enumerate(sorted(paths)):
        py_compile.compile(str(path), cfile=str(target / f"{index}.pyc"), doraise=True)
for module in (
    "domains.sellers",
    "repositories.sellers_repository",
    "routers.sellers",
    "services.sellers_service",
):
    importlib.import_module(module)
importlib.import_module("app")
print("REMOTE_PY_COMPILE_IMPORTS_OK")
PY' sh "$TEMP_DIR/package/backend" "$SERVICE_PYTHON" "$TEMP_DIR/package/backups"

python3 - "$TEMP_DIR" <<'PY'
import hashlib
import os
import pwd
import shutil
import stat
import sys
from pathlib import Path

base = Path(sys.argv[1])
staged = base / "package" / "backend"
active = base / "simulation_active"
backup = base / "simulation_backup"
code_dirs = ("domains", "repositories", "routers", "services", "migrations")
static_dirs = ("assets", "css", "js")
protected_dirs = {
    "uploads", "logs", "data", "instance", "storage", "media",
    "certificates", "auth_info_baileys", "backups", "app-updates",
}
protected_files = (
    ".env", "app.db", "app.sqlite", "app.sqlite3", "app.db-wal", "app.db-shm",
)

active.mkdir()
(active / "app.py").write_text("OLD_APP = True\n", encoding="utf-8")
(active / "requirements.txt").write_text("old-runtime\n", encoding="utf-8")
for name in code_dirs:
    directory = active / name
    directory.mkdir()
    (directory / "old.py").write_text("OLD = True\n", encoding="utf-8")
(active / "static").mkdir()
(active / "static" / "index.html").write_text("old frontend", encoding="utf-8")
for name in protected_dirs:
    directory = active / ("static" if name == "app-updates" else "") / name
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "marker.keep").write_text(f"protected:{name}", encoding="utf-8")
for name in protected_files:
    (active / name).write_text(f"protected:{name}", encoding="utf-8")

def snapshot(root):
    result = {}
    for path in sorted(root.rglob("*")):
        rel = path.relative_to(root).as_posix()
        if path.is_file() and (
            path.name in protected_files
            or "marker.keep" == path.name
        ):
            data = path.read_bytes()
            info = path.stat()
            result[rel] = (hashlib.sha256(data).hexdigest(), stat.S_IMODE(info.st_mode), info.st_uid, info.st_gid)
    return result

def blocked_file(path):
    name = path.name.lower()
    return name == ".env" or name.startswith(".env.") or name.endswith(
        (".env", ".db", ".sqlite", ".sqlite3", "-wal", "-shm", "-journal", ".pyc")
    )

def copy_dir(source, target):
    if not source.is_dir():
        return
    for root, dirs, files in os.walk(source, topdown=True, followlinks=False):
        dirs[:] = [d for d in dirs if d.lower() not in protected_dirs and not (Path(root) / d).is_symlink()]
        root_path = Path(root)
        out = target / root_path.relative_to(source)
        out.mkdir(parents=True, exist_ok=True)
        for filename in files:
            item = root_path / filename
            if blocked_file(item) or item.is_symlink():
                continue
            shutil.copy2(item, out / filename)

def copy_code(source, target, selection):
    target.mkdir(parents=True, exist_ok=True)
    for item in source.iterdir():
        if item.is_file() and not item.is_symlink() and not blocked_file(item):
            if item.suffix == ".py" or item.name == "requirements.txt":
                shutil.copy2(item, target / item.name)
    for name in code_dirs:
        copy_dir(source / name, target / name)
    source_static = source / "static"
    selection_static = selection / "static"
    target_static = target / "static"
    target_static.mkdir(parents=True, exist_ok=True)
    if selection_static.is_dir():
        for selected in selection_static.iterdir():
            item = source_static / selected.name
            if selected.is_file() and item.is_file() and not blocked_file(item):
                shutil.copy2(item, target_static / item.name)
    for name in static_dirs:
        copy_dir(source_static / name, target_static / name)

def clear_code(root, selection):
    for item in list(root.glob("*.py")) + [root / "requirements.txt"]:
        if item.is_file() and not item.is_symlink():
            item.unlink()
    for name in code_dirs:
        shutil.rmtree(root / name, ignore_errors=True)
    for name in static_dirs:
        shutil.rmtree(root / "static" / name, ignore_errors=True)
    selection_static = selection / "static"
    if selection_static.is_dir():
        for selected in selection_static.iterdir():
            target = root / "static" / selected.name
            if selected.is_file() and target.is_file() and not target.is_symlink():
                target.unlink()

before = snapshot(active)
copy_code(active, backup, staged)
clear_code(active, staged)
copy_code(staged, active, staged)

menina = pwd.getpwnam("menina")
for path in list(active.glob("*.py")) + [active / "requirements.txt"]:
    if path.is_file():
        os.chown(path, menina.pw_uid, menina.pw_gid)
for name in code_dirs:
    directory = active / name
    if directory.is_dir():
        for root, dirs, files in os.walk(directory):
            for entry in dirs + files:
                os.chown(Path(root) / entry, menina.pw_uid, menina.pw_gid)

after_apply = snapshot(active)
if before != after_apply:
    raise SystemExit("PERSISTENCIA_ALTERADA_NA_COPIA")

clear_code(active, staged)
copy_code(backup, active, backup)
after_restore = snapshot(active)
if before != after_restore:
    raise SystemExit("PERSISTENCIA_ALTERADA_NO_RESTORE")
if "OLD_APP = True" not in (active / "app.py").read_text(encoding="utf-8"):
    raise SystemExit("RESTORE_CODIGO_FALHOU")
print(f"PROTECTED_MARKERS_VALIDATED={len(before)}")
print("SIMULATED_COPY_OK")
print("SIMULATED_RESTORE_OK")
print("SIMULATED_CHOWN_CODE_ONLY_OK")
PY

SERVICE_STATUS_ATUAL="$(systemctl is-active "$SERVICE" 2>&1 || true)"
echo "SERVICE_STATUS_ATUAL=$SERVICE_STATUS_ATUAL"
systemctl show "$SERVICE" --no-pager \
  --property=LoadState \
  --property=ActiveState \
  --property=SubState \
  --property=User \
  --property=WorkingDirectory \
  --property=ExecStart

echo "NO_REAL_APP_WRITE_CONFIRMED"
echo "NO_REAL_SERVICE_CHANGE_CONFIRMED"
echo "REMOTE_DRY_RUN_APPROVED"
