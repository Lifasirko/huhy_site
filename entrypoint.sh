#!/usr/bin/env bash
set -euo pipefail

# ------------ налаштування ------------
: "${DB_HOST:=db}"
: "${DB_PORT:=5432}"
: "${DJANGO_SETTINGS_MODULE:=alphahuhysite.settings}"
: "${GUNICORN_BIND:=0.0.0.0:8000}"
: "${GUNICORN_WORKERS:=3}"
: "${GUNICORN_APP:=alphahuhysite.wsgi:application}"
# --------------------------------------

log(){ echo ">>> $*"; }

wait_for_db() {
  log "Waiting for DB at ${DB_HOST}:${DB_PORT}..."
  until nc -z "${DB_HOST}" "${DB_PORT}"; do
    sleep 1
  done
  log "DB is up"
}

maybe_build_frontend() {
  if [ -f package.json ]; then
    # Перевіряємо чи є scripts.build у package.json (без jq)
    if node -e "const p=require('./package.json');process.exit(p.scripts&&p.scripts.build?0:1)"; then
      log "frontend: installing deps (npm ci) ..."
      # Якщо немає lock-файлу — fallback на npm install
      if [ -f package-lock.json ]; then
        npm ci --no-audit --no-fund
      else
        npm install --no-audit --no-fund
      fi
      log "frontend: building (npm run build) ..."
      npm run build
      log "frontend: build done"
    else
      log "frontend: no scripts.build -> skip"
    fi
  else
    log "frontend: no package.json -> skip"
  fi
}

django_init() {
  log "start"
  export DJANGO_SETTINGS_MODULE

  # 1) чек БД
  wait_for_db

  # 2) опційний початковий сид / відновлення (твоя команда)
  if python manage.py help | grep -q '^  init_app$'; then
    python manage.py init_app
  fi

  # 3) міграції
  python manage.py migrate --noinput

  # 4) зібрати фронт (якщо треба) ПЕРЕД collectstatic
  maybe_build_frontend

  # 5) статика
  python manage.py collectstatic --noinput
}

run_gunicorn() {
  log "Starting gunicorn on ${GUNICORN_BIND} with ${GUNICORN_WORKERS} workers"
  exec gunicorn "${GUNICORN_APP}" --workers "${GUNICORN_WORKERS}" --bind "${GUNICORN_BIND}"
}

# main
django_init
run_gunicorn
