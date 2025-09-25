#!/usr/bin/env sh
set -euo pipefail
# на час налагодження корисно:
# set -x

echo "SEED_ON_BOOT=${SEED_ON_BOOT} SEED_MODE=${SEED_MODE} SEED_PATH=${SEED_PATH}"

echo "Waiting for DB at ${DB_HOST}:${DB_PORT}..."
until nc -z "${DB_HOST}" "${DB_PORT}"; do
  sleep 1
done
echo "DB is up"

python manage.py init_app
python manage.py collectstatic --noinput

: "${GUNICORN_WORKERS:=3}"
: "${GUNICORN_TIMEOUT:=60}"
: "${GUNICORN_LOG_LEVEL:=info}"

exec gunicorn alphahuhysite.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS}" \
  --timeout "${GUNICORN_TIMEOUT}" \
  --log-level "${GUNICORN_LOG_LEVEL}"
