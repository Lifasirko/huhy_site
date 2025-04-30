#!/usr/bin/env bash
set -e

# —————————————————————————————————————————————————————————————
# 1. Підвантажуємо змінні середовища з .env без source
# —————————————————————————————————————————————————————————————
PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
ENV_FILE="$PROJECT_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then
  echo "❌ Файл .env не знайдено у $PROJECT_DIR"
  exit 1
fi

# Зчитуємо кожен рядок KEY=VALUE, ігноруючи коментарі та порожні рядки
while IFS='=' read -r key value; do
  # Пропускаємо коментарі та порожні ключі
  [[ -z "$key" || "$key" =~ ^\s*# ]] && continue
  # Видаляємо потенційні оточуючі лапки з value
  value="${value%\"}"
  value="${value#\"}"
  export "$key"="$value"
done < <(grep -v '^\s*#' "$ENV_FILE" | grep -v '^\s*$')

# —————————————————————————————————————————————————————————————
# 2. Перевірка обов’язкових змінних
# —————————————————————————————————————————————————————————————
: "${DB_NAME:?DB_NAME не встановлено у .env}"
: "${DB_USER:?DB_USER не встановлено у .env}"
: "${DB_PASSWORD:?DB_PASSWORD не встановлено у .env}"
: "${TGBOT_TOKEN:?TGBOT_TOKEN не встановлено у .env}"
: "${OWNERS:?OWNERS не встановено у .env}"

# Назва контейнера з БД (як у `docker-compose ps`)
# Якщо у вас інша — поміняйте на актуальну
CONTAINER="huhy_site_db_1"

# Папка для бекапів (підпапка backups у проекті)
OUT_DIR="$PROJECT_DIR/backups"

# Telegram
TOKEN="$TGBOT_TOKEN"
CHAT_ID="$OWNERS"

# Ім’я файлу за датою
DATE=$(date +%Y%m%d)
FNAME="backup_${DATE}.sql.gz"
DEST="$OUT_DIR/$FNAME"

# —————————————————————————————————————————————————————————————
# 3. Створюємо папку backups, якщо її нема
# —————————————————————————————————————————————————————————————
mkdir -p "$OUT_DIR"

# —————————————————————————————————————————————————————————————
# 4. Робимо дамп БД і стискаємо
# —————————————————————————————————————————————————————————————
# Передаємо пароль у змінній середовища для pg_dump
export PGPASSWORD="$DB_PASSWORD"
docker exec "$CONTAINER" pg_dump -U "$DB_USER" -d "$DB_NAME" | gzip > "$DEST"
unset PGPASSWORD

# —————————————————————————————————————————————————————————————
# 5. Відправка бекапу в Telegram
# —————————————————————————————————————————————————————————————
curl -s -X POST "https://api.telegram.org/bot$TOKEN/sendDocument" \
     -F chat_id="$CHAT_ID" \
     -F document=@"$DEST" \
     -F caption="🗄️ Бекап БД $DB_NAME за $DATE" \
     >/dev/null

# —————————————————————————————————————————————————————————————
# 6. Прибирання старих файлів (старше 28 днів)
# —————————————————————————————————————————————————————————————
find "$OUT_DIR" -type f -mtime +28 -delete
