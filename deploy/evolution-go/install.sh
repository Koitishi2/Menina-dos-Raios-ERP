#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR=/opt/menina/evolution-go
BOOTSTRAP_DIR=/tmp/menina-evolution-go-bootstrap/deploy/evolution-go
SERVICE_FILE=/etc/systemd/system/menina-evolution-go.service
COMPOSE=/usr/bin/docker-compose

fail() {
  printf 'EVOLUTION_GO_SETUP_FAILED=%s\n' "$1" >&2
  exit 1
}

[[ "${EUID:-$(id -u)}" == "0" ]] || fail root_required
[[ $# == 0 ]] || fail unexpected_arguments
[[ -x "$COMPOSE" ]] || fail docker_compose_not_found
command -v docker >/dev/null 2>&1 || fail docker_podman_compat_not_found
command -v podman >/dev/null 2>&1 || fail podman_not_found
command -v openssl >/dev/null 2>&1 || fail openssl_not_found
command -v curl >/dev/null 2>&1 || fail curl_not_found
[[ -f "$BOOTSTRAP_DIR/compose.yaml" && -f "$BOOTSTRAP_DIR/init-users-db.sql" ]] || fail bootstrap_files_missing

install -d -m 0750 "$APP_DIR"
if [[ -e "$APP_DIR/.env" ]]; then
  cp -a "$APP_DIR/.env" "$APP_DIR/.env.backup.$(date +%Y%m%d_%H%M%S)"
  for key in POSTGRES_USER POSTGRES_PASSWORD GLOBAL_API_KEY; do
    grep -q "^${key}=" "$APP_DIR/.env" || fail "existing_env_missing_${key}"
  done
  if grep -q '^EVOLUTION_OPERATOR_EMAIL=.' "$APP_DIR/.env"; then
    fail operator_email_is_set_review_license_activation_before_start
  fi
  grep -q '^EVOLUTION_OPERATOR_EMAIL=' "$APP_DIR/.env" || printf '\nEVOLUTION_OPERATOR_EMAIL=\n' >> "$APP_DIR/.env"
else
  POSTGRES_PASSWORD="$(openssl rand -hex 24)"
  GLOBAL_API_KEY="$(openssl rand -hex 32)"
  cat > "$APP_DIR/.env" <<EOF
POSTGRES_USER=evo_go
POSTGRES_PASSWORD=$POSTGRES_PASSWORD
GLOBAL_API_KEY=$GLOBAL_API_KEY
EVOLUTION_OPERATOR_EMAIL=
EOF
fi
chmod 0600 "$APP_DIR/.env"

for name in compose.yaml init-users-db.sql; do
  if [[ -f "$APP_DIR/$name" ]]; then
    cp -a "$APP_DIR/$name" "$APP_DIR/$name.backup.$(date +%Y%m%d_%H%M%S)"
  fi
done
install -m 0640 "$BOOTSTRAP_DIR/compose.yaml" "$APP_DIR/compose.yaml"
install -m 0640 "$BOOTSTRAP_DIR/init-users-db.sql" "$APP_DIR/init-users-db.sql"
chown -R root:root "$APP_DIR"
if ! (cd "$APP_DIR" && DOCKER_HOST=unix:///run/podman/podman.sock "$COMPOSE" -f compose.yaml config --quiet); then
  fail compose_config_invalid
fi

cat > "$SERVICE_FILE" <<'EOF'
[Unit]
Description=Menina Evolution Go (isolated WhatsApp provider)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/menina/evolution-go
Environment=DOCKER_HOST=unix:///run/podman/podman.sock
ExecStart=/usr/bin/docker-compose -f /opt/menina/evolution-go/compose.yaml up -d
ExecStop=/usr/bin/docker-compose -f /opt/menina/evolution-go/compose.yaml down
TimeoutStartSec=0
TimeoutStopSec=120

[Install]
WantedBy=multi-user.target
EOF
chmod 0644 "$SERVICE_FILE"

systemctl enable --now podman.socket
systemctl daemon-reload
systemctl enable --now menina-evolution-go.service

ready=0
for _ in $(seq 1 60); do
  if curl -fsS --max-time 3 http://127.0.0.1:8766/server/ok >/dev/null; then
    ready=1
    break
  fi
  sleep 2
done
[[ "$ready" == 1 ]] || {
  systemctl status menina-evolution-go.service --no-pager -l >&2 || true
  "$COMPOSE" -f "$APP_DIR/compose.yaml" logs --tail=100 >&2 || true
  fail healthcheck_timeout
}

rm -rf -- /tmp/menina-evolution-go-bootstrap
printf 'EVOLUTION_GO_SERVICE=active\n'
printf 'EVOLUTION_GO_HEALTH=ok\n'
printf 'EVOLUTION_GO_BIND=127.0.0.1:8766\n'
printf 'EVOLUTION_GO_WHATSAPP_SESSION=not_started\n'
printf 'EVOLUTION_GO_LICENSE=not_confirmed\n'
printf 'EVOLUTION_GO_MANAGER=http://127.0.0.1:8766/manager/login\n'
printf 'EVOLUTION_GO_TUNNEL=ssh -L 8766:127.0.0.1:8766 root@2.24.124.76\n'
