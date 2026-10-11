#!/usr/bin/env bash
set -Eeuo pipefail

APP_DIR=/opt/menina/evolution-go
BOOTSTRAP_DIR=/tmp/menina-evolution-go-bootstrap/deploy/evolution-go
SERVICE_FILE=/etc/systemd/system/menina-evolution-go.service
COMPOSE=/usr/bin/docker-compose
IMAGE=localhost/menina-evolution-go:0.7.2-login-preflight2
UPSTREAM_COMMIT=9337afc47e10b86cc896a6f432240e40fee95dd1

fail() {
  printf 'EVOLUTION_GO_SETUP_FAILED=%s\n' "$1" >&2
  exit 1
}

[[ "${EUID:-$(id -u)}" == "0" ]] || fail root_required
[[ $# == 0 ]] || fail unexpected_arguments
[[ -x "$COMPOSE" ]] || fail docker_compose_not_found
command -v docker >/dev/null 2>&1 || fail docker_podman_compat_not_found
command -v podman >/dev/null 2>&1 || fail podman_not_found
command -v git >/dev/null 2>&1 || fail git_not_found
command -v openssl >/dev/null 2>&1 || fail openssl_not_found
command -v curl >/dev/null 2>&1 || fail curl_not_found
podman network exists menina_evolution_go_private || fail private_network_missing
[[ -f "$BOOTSTRAP_DIR/compose.yaml" && -f "$BOOTSTRAP_DIR/init-users-db.sql" && -f "$BOOTSTRAP_DIR/resolv.conf" && -f "$BOOTSTRAP_DIR/manager-login-license-gate.patch" ]] || fail bootstrap_files_missing

if ! podman image exists "$IMAGE"; then
  BUILD_DIR="$(mktemp -d /tmp/menina-evolution-go-build.XXXXXX)"
  if ! git clone --depth 1 --branch 0.7.2 https://github.com/evolution-foundation/evolution-go.git "$BUILD_DIR/source"; then
    rm -rf -- "$BUILD_DIR"
    fail upstream_source_download_failed
  fi
  actual_commit="$(git -C "$BUILD_DIR/source" rev-parse HEAD)"
  [[ "$actual_commit" == "$UPSTREAM_COMMIT" ]] || {
    rm -rf -- "$BUILD_DIR"
    fail upstream_source_commit_mismatch
  }
  if ! git -C "$BUILD_DIR/source" apply --check "$BOOTSTRAP_DIR/manager-login-license-gate.patch" ||
    ! git -C "$BUILD_DIR/source" apply "$BOOTSTRAP_DIR/manager-login-license-gate.patch"; then
    rm -rf -- "$BUILD_DIR"
    fail manager_login_patch_failed
  fi
  if ! grep -q '^FROM golang:1.25.0-alpine AS build$' "$BUILD_DIR/source/Dockerfile" ||
    ! grep -q '^FROM alpine:3.19.1 AS final$' "$BUILD_DIR/source/Dockerfile"; then
    rm -rf -- "$BUILD_DIR"
    fail upstream_dockerfile_unexpected
  fi
  sed -i \
    -e 's|^FROM golang:1.25.0-alpine AS build$|FROM docker.io/library/golang:1.25.0-alpine AS build|' \
    -e 's|^FROM alpine:3.19.1 AS final$|FROM docker.io/library/alpine:3.19.1 AS final|' \
    "$BUILD_DIR/source/Dockerfile"
  if ! podman build --tag "$IMAGE" --build-arg VERSION=0.7.2-login-preflight2 "$BUILD_DIR/source"; then
    rm -rf -- "$BUILD_DIR"
    fail patched_image_build_failed
  fi
  rm -rf -- "$BUILD_DIR"
fi

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

for name in compose.yaml init-users-db.sql resolv.conf; do
  if [[ -f "$APP_DIR/$name" ]]; then
    cp -a "$APP_DIR/$name" "$APP_DIR/$name.backup.$(date +%Y%m%d_%H%M%S)"
  fi
done
install -m 0640 "$BOOTSTRAP_DIR/compose.yaml" "$APP_DIR/compose.yaml"
install -m 0644 "$BOOTSTRAP_DIR/init-users-db.sql" "$APP_DIR/init-users-db.sql"
install -m 0644 "$BOOTSTRAP_DIR/resolv.conf" "$APP_DIR/resolv.conf"
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
systemctl enable menina-evolution-go.service
if systemctl is-active --quiet menina-evolution-go.service; then
  (cd "$APP_DIR" && DOCKER_HOST=unix:///run/podman/podman.sock "$COMPOSE" -f compose.yaml up -d --no-deps evolution-go)
else
  systemctl start menina-evolution-go.service
fi

db_ready=0
for _ in $(seq 1 60); do
  if podman healthcheck run menina-evolution-go-postgres >/dev/null 2>&1; then
    db_ready=1
    break
  fi
  sleep 2
done
[[ "$db_ready" == 1 ]] || fail postgres_healthcheck_timeout

if ! podman exec menina-evolution-go-postgres psql -U evo_go -d evogo_auth -tAc \
  "SELECT 1 FROM pg_database WHERE datname = 'evogo_users'" | grep -q '^1$'; then
  podman exec menina-evolution-go-postgres psql -v ON_ERROR_STOP=1 -U evo_go -d evogo_auth \
    -c 'CREATE DATABASE evogo_users OWNER evo_go' >/dev/null
fi

# PostgreSQL is now ready and both databases exist; restart the API after its
# first dependency attempts so it connects using the static container address.
podman restart menina-evolution-go >/dev/null

license_dns_ready=0
for _ in $(seq 1 15); do
  if podman exec menina-evolution-go nslookup license.evolutionfoundation.com.br >/dev/null 2>&1; then
    license_dns_ready=1
    break
  fi
  sleep 2
done
[[ "$license_dns_ready" == 1 ]] || {
  printf 'EVOLUTION_GO_LICENSE_DNS=failed\n' >&2
  podman exec menina-evolution-go cat /etc/resolv.conf >&2 || true
  fail license_dns_resolution_failed
}

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
printf 'EVOLUTION_GO_LICENSE_DNS=ok\n'
printf 'EVOLUTION_GO_BIND=127.0.0.1:8766\n'
printf 'EVOLUTION_GO_WHATSAPP_SESSION=not_started\n'
printf 'EVOLUTION_GO_LICENSE=not_confirmed\n'
printf 'EVOLUTION_GO_MANAGER=http://127.0.0.1:8766/manager/login\n'
printf 'EVOLUTION_GO_TUNNEL=ssh -L 8766:127.0.0.1:8766 root@2.24.124.76\n'
