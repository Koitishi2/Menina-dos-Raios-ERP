#!/usr/bin/env bash
set -euo pipefail

: "${RUN_DIR:?RUN_DIR obrigatorio}"
: "${APP_DIR:?APP_DIR obrigatorio}"
: "${BACKUP_DIR:?BACKUP_DIR obrigatorio}"
: "${SERVICE:?SERVICE obrigatorio}"
: "${EXPECTED_PY_COUNT:?EXPECTED_PY_COUNT obrigatorio}"
: "${PACKAGE_NAME:?PACKAGE_NAME obrigatorio}"
: "${EXPECTED_PACKAGE_SHA256:?EXPECTED_PACKAGE_SHA256 obrigatorio}"
: "${EXPECTED_SCRIPT_SHA256:?EXPECTED_SCRIPT_SHA256 obrigatorio}"

case "$RUN_DIR" in
  /root/menina_refatoracao_staging/quick_*) ;;
  *) echo "STAGING_INVALIDO" >&2; exit 80 ;;
esac
case "$APP_DIR" in
  /opt/menina/backend) ;;
  *) echo "APP_DIR_INVALIDO" >&2; exit 81 ;;
esac
case "$BACKUP_DIR" in
  /root/menina_refatoracao_backups/quick_*) ;;
  *) echo "BACKUP_DIR_INVALIDO" >&2; exit 82 ;;
esac

# Os caminhos ja foram aceitos pelo allowlist; somente agora e seguro gravar
# o status remoto dentro do staging autorizado.
STATUS_FILE="$RUN_DIR/deploy_status.log"
status_phase() {
  printf 'APPLY_PHASE=%s at=%s\n' "$1" "$(date -Is)" >> "$STATUS_FILE"
}
status_finish() {
  local status=$?
  printf 'DEPLOY_EXIT_CODE=%s at=%s\n' "$status" "$(date -Is)" >> "$STATUS_FILE" 2>/dev/null || true
}
printf 'DEPLOY_STARTED=%s\n' "$(date -Is)" > "$STATUS_FILE"
status_phase "PRECHECK"
trap status_finish EXIT

case "$PACKAGE_NAME" in
  *.zip) ;;
  *) echo "PACOTE_INVALIDO" >&2; exit 83 ;;
esac
test "$SERVICE" = "menina"
test "$EXPECTED_PACKAGE_SHA256" != ""
test "$EXPECTED_SCRIPT_SHA256" != ""

PACKAGE_PATH="$RUN_DIR/$PACKAGE_NAME"
SCRIPT_PATH="$(readlink -f "${BASH_SOURCE[0]}")"
STAGED_BACKEND="$RUN_DIR/backend"
STAGED_BAILEYS="$RUN_DIR/baileys-api"
BAILEYS_DIR="/opt/menina/baileys-api"
BAILEYS_SERVICE="menina-baileys"
SERVICE_PYTHON="/opt/menina/venv/bin/python3"
CODE_DIR_NAMES=(domains repositories routers services migrations)
STATIC_DIR_NAMES=(assets css js)
BAILEYS_FILES=(server.js inbound.js security.js maintenance.js package.json package-lock.json update-baileys-safe.sh)
BACKUP_READY=0
BAILEYS_BACKUP_READY=0

command -v sha256sum >/dev/null
command -v python3 >/dev/null
command -v runuser >/dev/null
command -v node >/dev/null
command -v systemctl >/dev/null
if [[ ! -x "$SERVICE_PYTHON" ]]; then
  echo "SERVICE_PYTHON_NOT_EXECUTABLE: $SERVICE_PYTHON" >&2
  exit 84
fi

verify_sha256() {
  local expected="$1" path="$2" label="$3" actual
  actual="$(sha256sum "$path" | awk '{print toupper($1)}')"
  if [[ "$actual" != "${expected^^}" ]]; then
    echo "${label}_SHA256_INVALIDO esperado=${expected^^} atual=$actual" >&2
    return 1
  fi
  echo "${label}_SHA256=$actual"
}

# Copia somente a allowlist de codigo/configuracao de dependencias do adaptador.
# .env, auth_info_baileys, node_modules, logs e qualquer outro caminho nunca sao percorridos.
copy_baileys_code() {
  local src="$1" dst="$2" name item
  mkdir -p "$dst"
  for name in "${BAILEYS_FILES[@]}"; do
    item="$src/$name"
    [[ -f "$item" && ! -L "$item" ]] || {
      echo "BAILEYS_ALLOWLIST_FILE_INVALIDO: $item" >&2
      return 1
    }
    cp -p -- "$item" "$dst/$name"
  done
}

clear_baileys_code() {
  local root="$1" name item
  for name in "${BAILEYS_FILES[@]}"; do
    item="$root/$name"
    [[ ! -e "$item" || ( -f "$item" && ! -L "$item" ) ]] || {
      echo "BAILEYS_ACTIVE_FILE_INVALIDO: $item" >&2
      return 1
    }
    [[ ! -f "$item" ]] || rm -f -- "$item"
  done
}

validate_baileys_code() {
  local root="$1" name
  for name in server.js inbound.js security.js maintenance.js; do
    node --check "$root/$name"
  done
  bash -n "$root/update-baileys-safe.sh"
  NODE_PATH="$BAILEYS_DIR/node_modules" node -e \
    "require(process.argv[1]); require(process.argv[2]); require(process.argv[3]);" \
    "$root/inbound.js" "$root/security.js" "$root/maintenance.js"
  echo "BAILEYS_CODE_VALIDATION_OK"
}

validate_baileys_health() {
  python3 - <<'PY'
import json
import urllib.request

with urllib.request.urlopen("http://127.0.0.1:3001/status", timeout=10) as response:
    payload = json.load(response)
if payload.get("connected") is not True:
    raise SystemExit("BAILEYS_NOT_CONNECTED")
if (payload.get("inbound") or {}).get("listenerInstalled") is not True:
    raise SystemExit("BAILEYS_LISTENER_NOT_INSTALLED")
print("BAILEYS_HEALTH_OK=connected_listener_installed")
PY
}

# Copia somente arquivos e diretorios explicitamente classificados como codigo.
# A rotina nao percorre .env, bancos, WAL/SHM, uploads, logs, data, instance,
# storage, media ou app-updates.
copy_code_tree() {
  local src="$1" dst="$2" selection="${3:-$1}"
  python3 - "$src" "$dst" "$selection" <<'PY'
import os
import shutil
import sys
from pathlib import Path

src = Path(sys.argv[1])
dst = Path(sys.argv[2])
selection = Path(sys.argv[3])
code_dirs = ("domains", "repositories", "routers", "services", "migrations")
static_dirs = ("assets", "css", "js")
protected_dirs = {
    "uploads", "upload", "logs", "log", "data", "instance", "storage",
    "media", "backups", "backup", "database", "databases", "app-updates",
    "auth_info_baileys", "certificates", "certs", "keys", "__pycache__",
}

def protected_file(path: Path) -> bool:
    name = path.name.lower()
    return (
        name == ".env"
        or name.startswith(".env.")
        or name.endswith(".env")
        or name.endswith((".db", ".sqlite", ".sqlite3", "-wal", "-shm", "-journal", ".pyc"))
    )

def copy_dir(source: Path, target: Path) -> None:
    if not source.is_dir():
        return
    for root, dirs, files in os.walk(source, topdown=True, followlinks=False):
        dirs[:] = [
            name for name in dirs
            if name.lower() not in protected_dirs and not (Path(root) / name).is_symlink()
        ]
        root_path = Path(root)
        relative = root_path.relative_to(source)
        target_root = target / relative
        target_root.mkdir(parents=True, exist_ok=True)
        for name in files:
            item = root_path / name
            if protected_file(item) or item.is_symlink():
                continue
            shutil.copy2(item, target_root / name)

dst.mkdir(parents=True, exist_ok=True)
for item in src.iterdir():
    if item.is_file() and not item.is_symlink() and not protected_file(item):
        if item.suffix == ".py" or item.name == "requirements.txt":
            shutil.copy2(item, dst / item.name)

for name in code_dirs:
    copy_dir(src / name, dst / name)

static_src = src / "static"
static_dst = dst / "static"
if static_src.is_dir():
    static_dst.mkdir(parents=True, exist_ok=True)
    selection_static = selection / "static"
    if selection_static.is_dir():
        for selected in selection_static.iterdir():
            item = static_src / selected.name
            if selected.is_file() and item.is_file() and not item.is_symlink() and not protected_file(item):
                shutil.copy2(item, static_dst / item.name)
    for name in static_dirs:
        copy_dir(static_src / name, static_dst / name)
PY
}

clear_code_tree() {
  local root="$1" selection="$2" name selected
  local root_files=()
  shopt -s nullglob
  root_files=("$root"/*.py)
  [[ ! -f "$root/requirements.txt" ]] || root_files+=("$root/requirements.txt")
  ((${#root_files[@]} == 0)) || rm -f -- "${root_files[@]}"
  for name in "${CODE_DIR_NAMES[@]}"; do
    rm -rf -- "$root/$name"
  done
  for name in "${STATIC_DIR_NAMES[@]}"; do
    rm -rf -- "$root/static/$name"
  done
  for selected in "$selection"/static/*; do
    [[ -f "$selected" && ! -L "$selected" ]] || continue
    name="$root/static/$(basename "$selected")"
    [[ ! -f "$name" || -L "$name" ]] || rm -f -- "$name"
  done
  shopt -u nullglob
}

chown_code_tree() {
  local root="$1" selection="$2" name selected
  local root_files=()
  shopt -s nullglob
  root_files=("$root"/*.py)
  [[ ! -f "$root/requirements.txt" ]] || root_files+=("$root/requirements.txt")
  ((${#root_files[@]} == 0)) || chown menina:menina -- "${root_files[@]}"
  for name in "${CODE_DIR_NAMES[@]}"; do
    [[ ! -d "$root/$name" ]] || chown -R menina:menina -- "$root/$name"
  done
  for name in "${STATIC_DIR_NAMES[@]}"; do
    [[ ! -d "$root/static/$name" ]] || chown -R menina:menina -- "$root/static/$name"
  done
  for selected in "$selection"/static/*; do
    [[ -f "$selected" && ! -L "$selected" ]] || continue
    name="$root/static/$(basename "$selected")"
    [[ ! -f "$name" || -L "$name" ]] || chown menina:menina -- "$name"
  done
  shopt -u nullglob
}

remove_code_pycache() {
  local root="$1" name
  rm -rf -- "$root/__pycache__"
  for name in "${CODE_DIR_NAMES[@]}"; do
    [[ ! -d "$root/$name" ]] || find "$root/$name" -type d -name '__pycache__' -prune -exec rm -rf -- {} +
  done
}

validate_python_as_service_user() {
  local root="$1" import_app="${2:-0}"
  (
    cd "$root"
    runuser -u menina -- env \
      PYTHONPATH="$root" \
      BACKUP_DIR="$root/.preflight_backups" \
      WHATSAPP_OUTBOUND_ENABLED=false \
      WHATSAPP_OUTBOUND_MODE=disabled \
      "$SERVICE_PYTHON" - "$root" "$import_app" <<'PY'
import importlib
import py_compile
import sys
import tempfile
from pathlib import Path

base = Path(sys.argv[1]).resolve()
import_app = sys.argv[2] == "1"
code_dirs = ("domains", "repositories", "routers", "services")
paths = list(base.glob("*.py"))
for name in code_dirs:
    directory = base / name
    if directory.is_dir():
        paths.extend(directory.rglob("*.py"))

with tempfile.TemporaryDirectory(prefix="menina_pycompile_") as output:
    output_dir = Path(output)
    for index, path in enumerate(sorted(paths)):
        py_compile.compile(str(path), cfile=str(output_dir / f"{index}.pyc"), doraise=True)

if import_app:
    importlib.import_module("app")
else:
    for module in (
        "domains.sellers",
        "repositories.sellers_repository",
        "routers.sellers",
        "services.sellers_service",
    ):
        importlib.import_module(module)
print("PY_COMPILE_E_IMPORTS_OK")
PY
  )
}

rollback() {
  local original_status="${1:-$?}"
  local restore_status=0 baileys_restore_status=0 start_status=0 baileys_start_status=0
  local final_status="unknown" baileys_final_status="unknown"
  set +e
  trap - ERR
  echo "ROLLBACK_INICIADO erro_original=$original_status" >&2

  systemctl stop "$BAILEYS_SERVICE" >/dev/null 2>&1 || true
  systemctl stop "$SERVICE" >/dev/null 2>&1 || true
  if [[ "$BACKUP_READY" = "1" ]]; then
    clear_code_tree "$APP_DIR" "$STAGED_BACKEND" || restore_status=$?
    if [[ "$restore_status" = "0" ]]; then
      copy_code_tree "$BACKUP_DIR/backend" "$APP_DIR" "$BACKUP_DIR/backend" || restore_status=$?
    fi
    chown_code_tree "$APP_DIR" "$BACKUP_DIR/backend" || true
    remove_code_pycache "$APP_DIR" || true
  else
    echo "ROLLBACK_RESTORE_NAO_EXECUTADO backup_indisponivel" >&2
  fi
  echo "ROLLBACK_RESTORE_STATUS=$restore_status" >&2

  if [[ "$BAILEYS_BACKUP_READY" = "1" ]]; then
    clear_baileys_code "$BAILEYS_DIR" || baileys_restore_status=$?
    if [[ "$baileys_restore_status" = "0" ]]; then
      copy_baileys_code "$BACKUP_DIR/baileys-api" "$BAILEYS_DIR" || baileys_restore_status=$?
    fi
  else
    echo "ROLLBACK_BAILEYS_RESTORE_NAO_EXECUTADO backup_indisponivel" >&2
  fi
  echo "ROLLBACK_BAILEYS_RESTORE_STATUS=$baileys_restore_status" >&2

  systemctl start "$SERVICE"
  start_status=$?
  echo "ROLLBACK_START_STATUS=$start_status" >&2
  systemctl start "$BAILEYS_SERVICE"
  baileys_start_status=$?
  echo "ROLLBACK_BAILEYS_START_STATUS=$baileys_start_status" >&2
  sleep 5
  final_status="$(systemctl is-active "$SERVICE" 2>&1)"
  baileys_final_status="$(systemctl is-active "$BAILEYS_SERVICE" 2>&1)"
  echo "ROLLBACK_STATUS_FINAL=$final_status" >&2
  echo "ROLLBACK_BAILEYS_STATUS_FINAL=$baileys_final_status" >&2
  [[ "$final_status" = "active" ]] || systemctl status "$SERVICE" --no-pager -l >&2 || true
  [[ "$baileys_final_status" = "active" ]] || systemctl status "$BAILEYS_SERVICE" --no-pager -l >&2 || true
  echo "ROLLBACK_CONCLUIDO" >&2
  return "$original_status"
}

handle_signal() {
  local signal_status="$1"
  rollback "$signal_status" || true
  exit "$signal_status"
}

# Integridade e extracao segura acontecem antes de qualquer parada do servico.
test -f "$PACKAGE_PATH"
test -f "$SCRIPT_PATH"
verify_sha256 "$EXPECTED_PACKAGE_SHA256" "$PACKAGE_PATH" "PACKAGE"
verify_sha256 "$EXPECTED_SCRIPT_SHA256" "$SCRIPT_PATH" "SCRIPT"
test ! -e "$STAGED_BACKEND"
status_phase "EXTRACTION"
python3 - "$PACKAGE_PATH" "$RUN_DIR" <<'PY'
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
        lowered = [part.lower() for part in path.parts]
        if path.is_absolute() or ".." in path.parts or any(part in blocked for part in lowered):
            raise SystemExit(f"ENTRADA_ZIP_PROIBIDA: {info.filename}")
        if any(
            part.startswith(".env.")
            or part.endswith((".env", ".db", ".sqlite", ".sqlite3", "-wal", "-shm", "-journal", ".pyc"))
            for part in lowered
        ):
            raise SystemExit(f"ENTRADA_ZIP_PERSISTENTE: {info.filename}")
        mode = info.external_attr >> 16
        if stat.S_ISLNK(mode):
            raise SystemExit(f"LINK_ZIP_PROIBIDO: {info.filename}")
        target = (destination / Path(*path.parts)).resolve()
        if destination not in target.parents and target != destination:
            raise SystemExit(f"ENTRADA_ZIP_FORA_STAGING: {info.filename}")
    package.extractall(destination)
print("EXTRACAO_SEGURA_OK")
PY

status_phase "PREFLIGHT"
test -f "$STAGED_BACKEND/app.py"
test -f "$STAGED_BACKEND/backup_admin.py"
test -f "$STAGED_BACKEND/rbac.py"
test -f "$STAGED_BACKEND/static/index.html"
test -d "$STAGED_BAILEYS"
test -d "$BAILEYS_DIR/node_modules"
test -d "$BAILEYS_DIR/auth_info_baileys"
for name in "${BAILEYS_FILES[@]}"; do
  test -f "$STAGED_BAILEYS/$name"
  test ! -L "$STAGED_BAILEYS/$name"
done
ACTUAL_PY_COUNT="$(find "$STAGED_BACKEND" -maxdepth 1 -type f -name '*.py' | wc -l)"
test "$ACTUAL_PY_COUNT" = "$EXPECTED_PY_COUNT"

# Importa app somente em copia temporaria. O backend ativo e seus bancos nao
# sao usados durante este preflight.
PREFLIGHT_DIR="$(mktemp -d /tmp/menina_updater_preflight.XXXXXX)"
chmod 0755 "$PREFLIGHT_DIR"
mkdir -p "$PREFLIGHT_DIR/backend"
copy_code_tree "$STAGED_BACKEND" "$PREFLIGHT_DIR/backend" "$STAGED_BACKEND"
chown menina:menina "$PREFLIGHT_DIR" "$PREFLIGHT_DIR/backend"
chown_code_tree "$PREFLIGHT_DIR/backend" "$STAGED_BACKEND"
if ! validate_python_as_service_user "$PREFLIGHT_DIR/backend" 1; then
  rm -rf -- "$PREFLIGHT_DIR"
  echo "STAGING_IMPORT_APP_FAILED" >&2
  exit 85
fi
rm -rf -- "$PREFLIGHT_DIR"
echo "STAGING_IMPORT_APP_OK"
validate_baileys_code "$STAGED_BAILEYS"
echo "STAGING_BAILEYS_OK"

trap 'rollback $?' ERR
trap 'handle_signal 129' HUP
trap 'handle_signal 130' INT
trap 'handle_signal 143' TERM

# Os servicos devem estar comprovadamente parados antes de qualquer leitura do codigo atual.
status_phase "SERVICE_STOP"
systemctl stop "$BAILEYS_SERVICE"
if systemctl is-active --quiet "$BAILEYS_SERVICE"; then
  echo "BAILEYS_STOP_FAILED" >&2
  false
fi
echo "BAILEYS_STOPPED"
systemctl stop "$SERVICE"
if systemctl is-active --quiet "$SERVICE"; then
  echo "SERVICE_STOP_FAILED" >&2
  false
fi
echo "SERVICE_STOPPED"

status_phase "BACKUP"
mkdir -p "$BACKUP_DIR/backend"
copy_code_tree "$APP_DIR" "$BACKUP_DIR/backend" "$STAGED_BACKEND"
BACKUP_READY=1
mkdir -p "$BACKUP_DIR/baileys-api"
copy_baileys_code "$BAILEYS_DIR" "$BACKUP_DIR/baileys-api"
BAILEYS_BACKUP_READY=1
echo "BACKEND_AND_BAILEYS_BACKUP_OK"

status_phase "COPY"
clear_code_tree "$APP_DIR" "$STAGED_BACKEND"
copy_code_tree "$STAGED_BACKEND" "$APP_DIR" "$STAGED_BACKEND"
chown_code_tree "$APP_DIR" "$STAGED_BACKEND"
remove_code_pycache "$APP_DIR"
clear_baileys_code "$BAILEYS_DIR"
copy_baileys_code "$STAGED_BAILEYS" "$BAILEYS_DIR"

test -d "$APP_DIR/repositories"
test -d "$APP_DIR/routers"
test -d "$APP_DIR/services"
test -d "$APP_DIR/domains"
test -f "$APP_DIR/repositories/sellers_repository.py"
test -f "$APP_DIR/routers/sellers.py"
test -f "$APP_DIR/services/sellers_service.py"
validate_python_as_service_user "$APP_DIR" 0
validate_baileys_code "$BAILEYS_DIR"

status_phase "SERVICE_RESTART"
systemctl start "$SERVICE"
systemctl start "$BAILEYS_SERVICE"
sleep 5
FINAL_SERVICE_STATUS="$(systemctl is-active "$SERVICE" 2>&1 || true)"
BAILEYS_STATUS_FINAL="$(systemctl is-active "$BAILEYS_SERVICE" 2>&1 || true)"
echo "SERVICE_STATUS_FINAL=$FINAL_SERVICE_STATUS"
echo "BAILEYS_STATUS_FINAL=$BAILEYS_STATUS_FINAL"
test "$FINAL_SERVICE_STATUS" = "active"
test "$BAILEYS_STATUS_FINAL" = "active"
validate_baileys_health

# Nao ha rota GET /health no app.py atual. O readiness fica restrito ao estado
# do systemd; nenhuma rota com potencial efeito colateral e chamada.
trap - ERR HUP INT TERM
status_phase "COMPLETE"
echo "REMOTE_BACKEND_AND_BAILEYS_UPDATE_OK"
