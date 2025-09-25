# alphahuhysite/management/commands/init_app.py
import os
import re
import subprocess
import requests
from pathlib import Path

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model


def _env_bool(name: str, default=False) -> bool:
    v = os.getenv(name, str(default)).strip().lower()
    return v in ("1", "true", "yes", "y", "on")


def _psql(args, check=True, capture=False):
    env = os.environ.copy()
    pg_env = {**env, "PGPASSWORD": env.get("DB_PASSWORD", "")}
    base = [
        "psql",
        "-h", env.get("DB_HOST", "db"),
        "-p", env.get("DB_PORT", "5432"),
        "-U", env.get("DB_USER", ""),
        "-d", env.get("DB_NAME", ""),
        "-v", "ON_ERROR_STOP=1",
    ]
    cmd = base + args
    if capture:
        res = subprocess.run(cmd, env=pg_env, text=True, capture_output=True)
        if check and res.returncode != 0:
            raise RuntimeError(res.stderr.strip() or "psql error")
        return (res.stdout or "").strip()
    else:
        res = subprocess.run(cmd, env=pg_env)
        if check and res.returncode != 0:
            raise RuntimeError("psql error")
        return ""


def telegram_notify(text: str):
    token = os.getenv("TGBOT_TOKEN", "").strip()
    ids_raw = os.getenv("TELEGRAM_ADMIN_IDS", "").strip()
    if not token or not ids_raw:
        print("init_app: telegram skipped (no token/admin ids)")
        return
    for chat_id in [x.strip() for x in ids_raw.split(",") if x.strip()]:
        try:
            requests.post(
                f"https://api.telegram.org/bot{token}/sendMessage",
                json={"chat_id": chat_id, "text": text, "parse_mode": "HTML"},
                timeout=10,
            )
        except Exception as e:
            print(f"init_app: telegram error for {chat_id}: {e}")


def _blog_count_or_missing() -> int:
    """
    Повертає:
      -1 якщо таблиці blog_blogpost нема,
       0..N — кількість рядків, якщо таблиця є.
    """
    sql = (
        "SELECT CASE WHEN to_regclass('public.blog_blogpost') IS NULL "
        "THEN -1 ELSE (SELECT COUNT(*) FROM public.blog_blogpost) END;"
    )
    out = _psql(["-tAc", sql], capture=True)
    try:
        return int((out or "0").strip())
    except ValueError:
        return -1


def _seed_sql_if_needed() -> bool:
    """
    За умови SEED_ON_BOOT=true та SEED_MODE=sql:
    - якщо SEED_FORCE_ON_BOOT=true, або блог порожній/відсутній — робимо:
      DROP SCHEMA public CASCADE; CREATE SCHEMA public ...; імпорт seed.sql
    Повертає True, якщо сидинг виконано.
    """
    on_boot = _env_bool("SEED_ON_BOOT", False)
    mode = os.getenv("SEED_MODE", "").strip().lower()
    force = _env_bool("SEED_FORCE_ON_BOOT", False)
    seed_path = os.getenv("SEED_PATH", "/app/backup/backup.sql").strip()
    db_user = os.getenv("DB_USER", "").strip()
    print(f"init_app: seed_on_boot={on_boot}, mode={mode}, force={force}, seed_path={seed_path}")

    if not (on_boot and mode in ("sql", "sql_full", "postgres_sql")):
        print("init_app: seeding disabled")
        return False

    count = _blog_count_or_missing()  # -1 (нема таблиці) або 0..N
    print(f"init_app: blog_count_check={count}")
    need = force or (count <= 0)
    if not need:
        print("init_app: DB has content -> skip seeding")
        return False

    p = Path(seed_path)
    if not p.is_file():
        print(f"init_app: seed file not found: {seed_path}")
        return False

    print("init_app: seeding DB from SQL ...")

    # 1) Скидаємо схему
    drop_sql = (
        f'DROP SCHEMA public CASCADE; '
        f'CREATE SCHEMA public AUTHORIZATION "{db_user}"; '
        f'ALTER SCHEMA public OWNER TO "{db_user}";'
    )
    _psql(["-tAc", drop_sql], check=True, capture=False)

    # 2) Готуємо тимчасовий SQL із правильним OWNER
    tmp = Path("/tmp/seed.sql")
    s = p.read_text(encoding="utf-8", errors="ignore")
    s = re.sub(r"OWNER TO [A-Za-z0-9_]+;", f"OWNER TO {db_user};", s)
    tmp.write_text(s, encoding="utf-8")

    # 3) Заливаємо
    _psql(["-f", str(tmp)], check=True, capture=False)

    print("init_app: seeding completed")
    telegram_notify("✅ <b>Huhy.space</b>: БД відновлено з бекапу і готова до роботи.")
    return True


class Command(BaseCommand):
    help = "Initial setup: optional seed, migrate, ensure superuser, notify."

    def handle(self, *args, **options):
        print(">>> init_app: start")

        # 0) Можливий сидинг (до міграцій, бо дамп містить DDL)
        print(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>/n"
              f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> init_app: seeded = ")
        seeded = _seed_sql_if_needed()
        print(f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>/n"
              f">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>> init_app: seeded = {seeded}")

        # 1) Міграції
        call_command("migrate", interactive=False)

        # 2) Суперюзер
        User = get_user_model()
        su_username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin").strip()
        su_email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com").strip()
        su_password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin").strip()
        if not User.objects.filter(username=su_username).exists():
            User.objects.create_superuser(su_username, su_email, su_password)
            print(f"init_app: superuser '{su_username}' created")
            telegram_notify(f"👤 Створено суперкористувача <b>{su_username}</b>.")
        else:
            print("init_app: superuser already exists")

        print(">>> init_app: done")
