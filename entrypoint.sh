#!/usr/bin/env sh
set -e

echo "Waiting for DB at ${DB_HOST:-db}:${DB_PORT:-5432}..."
until nc -z "${DB_HOST:-db}" "${DB_PORT:-5432}"; do
  sleep 1
done
echo "DB is up"

# (опціонально) базова перевірка Django-конфігурації
python manage.py check

# ВАЖЛИВО: сидимо ЛИШЕ через Django-команду (без жодного psql -f)
python manage.py init_app

# Збір статики у stdout (щоб бачилось у docker logs)
python manage.py collectstatic --noinput

# Запуск gunicorn у foreground з логами в stdout/stderr
exec gunicorn --bind :8000 ${DJANGO_WSGI_MODULE:-alphahuhysite.wsgi:application} \
  --access-logfile - --error-logfile -
