#!/usr/bin/env bash
set -euo pipefail

APP_DIR=/opt/menina/baileys-api
SERVICE=menina-baileys
STATUS_FILE=/run/menina-baileys-update-status.json
LOCK_FILE=/run/menina-baileys-update.lock
SERVICE_USER=root
STAGING=""
BACKUP=""
SWAPPED=0

write_status() {
  local status="$1" detail="$2" finished="${3:-}"
  python3 - "$STATUS_FILE" "$status" "$detail" "$finished" <<'PY'
import datetime, json, pathlib, sys
path, status, detail, finished = sys.argv[1:]
previous = {}
try:
    previous = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
except Exception:
    pass
now = datetime.datetime.now(datetime.timezone.utc).isoformat()
payload = {
    "status": status,
    "detail": detail[:300],
    "started_at": previous.get("started_at") if status != "running" else now,
    "finished_at": now if finished else None,
}
pathlib.Path(path).write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
PY
  chmod 0644 "$STATUS_FILE"
}

rollback() {
  local code="${1:-$?}"
  set +e
  trap - ERR
  if [[ "$SWAPPED" == 1 ]]; then
    systemctl stop "$SERVICE" >/dev/null 2>&1 || true
    rm -rf -- "$APP_DIR/node_modules"
    [[ ! -d "$BACKUP/node_modules" ]] || mv -- "$BACKUP/node_modules" "$APP_DIR/node_modules"
  fi
  systemctl start "$SERVICE" >/dev/null 2>&1 || true
  sleep 5
  local final_status
  final_status="$(systemctl is-active "$SERVICE" 2>&1)"
  write_status "failed" "rollback executado; service=$final_status; code=$code" yes
  exit "$code"
}

exec 9>"$LOCK_FILE"
flock -n 9 || { write_status "blocked" "outra atualizacao esta em andamento" yes; exit 75; }

[[ "$APP_DIR" == /opt/menina/baileys-api ]]
[[ -f "$APP_DIR/package.json" && ! -L "$APP_DIR/package.json" ]]
[[ -f "$APP_DIR/package-lock.json" && ! -L "$APP_DIR/package-lock.json" ]]
[[ -d "$APP_DIR/node_modules" && ! -L "$APP_DIR/node_modules" ]]
command -v node >/dev/null
command -v npm >/dev/null
command -v systemctl >/dev/null
command -v python3 >/dev/null
command -v flock >/dev/null
command -v curl >/dev/null

write_status "running" "preparando versao aprovada"
STAGING="$(mktemp -d /opt/menina/baileys-update.XXXXXX)"
BACKUP="/root/menina_refatoracao_backups/baileys_update_$(date +%Y%m%d_%H%M%S)"
trap 'rollback $?' ERR

cp -a -- "$APP_DIR/package.json" "$APP_DIR/package-lock.json" "$STAGING/"
for file in server.js inbound.js security.js maintenance.js; do
  cp -a -- "$APP_DIR/$file" "$STAGING/$file"
done
cd "$STAGING"
npm ci --omit=dev --ignore-scripts
node --check server.js
node --check inbound.js
node --check security.js
node --check maintenance.js
node -e "require('@whiskeysockets/baileys'); require('./inbound'); require('./security'); require('./maintenance')"

mkdir -p "$BACKUP"
cp -a -- "$APP_DIR/package.json" "$APP_DIR/package-lock.json" "$BACKUP/"
systemctl stop "$SERVICE"
systemctl is-active --quiet "$SERVICE" && { echo "SERVICE_STOP_FAILED" >&2; false; }
mv -- "$APP_DIR/node_modules" "$BACKUP/node_modules"
SWAPPED=1
mv -- "$STAGING/node_modules" "$APP_DIR/node_modules"
chown -R "$SERVICE_USER:$SERVICE_USER" "$APP_DIR/node_modules"
systemctl start "$SERVICE"
sleep 6
systemctl is-active --quiet "$SERVICE"
curl --fail --silent --show-error --max-time 5 http://127.0.0.1:3001/status >/dev/null

SWAPPED=0
trap - ERR
write_status "success" "versao aprovada instalada; backup=$BACKUP" yes
rm -rf -- "$STAGING"
echo "BAILEYS_UPDATE_OK"
