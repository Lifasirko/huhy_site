#!/usr/bin/env bash
set -Eeuo pipefail

log() { echo "[start] $*"; }
die() { echo "[start][ERR] $*" >&2; exit 1; }

DB_HOST="${DB_HOST:-127.0.0.1}"
DB_PORT="${DB_PORT:-5432}"
DB_USER="${DB_USER:-}"
DB_NAME="${DB_NAME:-postgres}"
DB_PASSWORD="${DB_PASSWORD:-}"
WAIT_FOR_DB_TIMEOUT="${WAIT_FOR_DB_TIMEOUT:-120}"
GUNICORN_WORKERS="${GUNICORN_WORKERS:-3}"
SOCK_PATH="${SOCK_PATH:-/root/huhy/huhy_site/huhy_site.sock}"

# 1) Чекаємо відкриття порту БД
log "waiting DB at ${DB_HOST}:${DB_PORT} (timeout ${WAIT_FOR_DB_TIMEOUT}s)..."
end=$((SECONDS + WAIT_FOR_DB_TIMEOUT))
until nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; do
  (( SECONDS >= end )) && die "DB tcp port isn't reachable"
  sleep 1
done
log "DB tcp port is reachable."

# 2) Перевіряємо простим запитом SELECT 1
if ! PGPASSWORD="${DB_PASSWORD}" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT 1" >/dev/null 2>&1; then
  die "cannot run SELECT 1 on db=$DB_NAME as user=$DB_USER"
fi
log "psql check passed."

# 3) Ініціалізація застосунку (перевірка/сід/міграції всередині init_app)
log "running manage.py init_app..."
python manage.py init_app
log "init_app done."

# 4) Запускаємо gunicorn
log "starting gunicorn..."
exec gunicorn alphahuhysite.wsgi:application --workers "$GUNICORN_WORKERS" --bind "unix:${SOCK_PATH}"
