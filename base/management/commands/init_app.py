import os
import re
import gzip
import subprocess
import requests
from pathlib import Path

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model


# =========================
# Допоміжні утиліти / ENV
# =========================

def _env_str(name: str, default: str = "") -> str:
    return os.getenv(name, default).strip()


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name, str(default)).strip().lower()
    return v in ("1", "true", "yes", "y", "on")


def _psql(args, *, check: bool = True, capture: bool = False, text_input: str | None = None) -> str:
    """
    Викликає psql з коректними ENV. Повертає stdout, якщо capture=True.
    Підтримує text_input (stdin).
    """
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
    cmd = base + list(args)

    if capture or text_input is not None:
        res = subprocess.run(cmd, env=pg_env, text=True, capture_output=capture, input=text_input)
        if check and res.returncode != 0:
            err = (res.stderr or "").strip() or "psql error"
            raise RuntimeError(err)
        return (res.stdout or "").strip() if capture else ""
    else:
        res = subprocess.run(cmd, env=pg_env)
        if check and res.returncode != 0:
            raise RuntimeError("psql error")
        return ""


def telegram_notify(text: str):
    token = _env_str("TGBOT_TOKEN")
    ids_raw = _env_str("TELEGRAM_ADMIN_IDS")
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


# =========================
# Діагностика БД / блокування
# =========================

def _db_diag():
    try:
        diag = _psql(["-tAc", "select current_database(), current_user;"], capture=True)
        print(f"init_app: DB diag -> {diag or '?'}")
    except Exception as e:
        print(f"init_app: DB diag failed: {e}")


def _db_has_content() -> bool:
    """
    Вважаємо БД "непорожньою", якщо:
      - є таблиця django_migrations і в ній є записи, або
      - є таблиця blog_blogpost і в ній count > 0
    """
    try:
        mig = int((_psql(
            ["-tAc",
             "SELECT CASE WHEN to_regclass('public.django_migrations') IS NULL "
             "THEN 0 ELSE (SELECT COUNT(*) FROM public.django_migrations) END;"],
            capture=True
        ) or "0").strip())
        if mig > 0:
            return True
    except Exception:
        pass

    try:
        blog = int((_psql(
            ["-tAc",
             "SELECT CASE WHEN to_regclass('public.blog_blogpost') IS NULL "
             "THEN 0 ELSE (SELECT COUNT(*) FROM public.blog_blogpost) END;"],
            capture=True
        ) or "0").strip())
        return blog > 0
    except Exception:
        return False


def _advisory_lock() -> bool:
    """
    Проста взаємна виключність між репліками web:
    TRUE — якщо вдалося взяти lock; FALSE — якщо ні.
    """
    try:
        out = _psql(["-tAc", "SELECT pg_try_advisory_lock(905221234);"], capture=True)
        return (out or "").strip().lower() in ("t", "true", "1")
    except Exception as e:
        print(f"init_app: advisory lock failed: {e}")
        return True  # не блокуємо виконання при діагностичних збоях


# =========================
# Вибір файлу сидингу
# =========================

def _find_seed_file() -> str | None:
    """
    Повертає шлях до seed-файлу:
      1) якщо заданий SEED_PATH і такий файл існує — використовуємо його;
      2) інакше шукаємо найновіший файл у SEED_DIR за маскою SEED_GLOB.
    За замовчуванням: SEED_DIR=/app/backups, SEED_GLOB=*.sql*
    """
    seed_path = _env_str("SEED_PATH")
    if seed_path:
        p = Path(seed_path)
        if p.is_file():
            return str(p)

    seed_dir = Path(_env_str("SEED_DIR", "/app/backups"))
    seed_glob = _env_str("SEED_GLOB", "*.sql*")
    if not seed_dir.exists():
        return None
    files = sorted(seed_dir.glob(seed_glob), key=lambda x: x.stat().st_mtime, reverse=True)
    return str(files[0]) if files else None


# =========================
# Обробка SQL-дампу
# =========================

_OWNER_PATTERNS = (
    re.compile(r'OWNER\s+TO\s+"?[^";]+"\s*;', re.IGNORECASE),
    re.compile(r'ALTER\s+SCHEMA\s+public\s+OWNER\s+TO\s+"?[^";]+"\s*;', re.IGNORECASE),
)


def _normalize_owner_line(line: str, db_user: str) -> str:
    """Заміняє OWNER TO ... на OWNER TO "{db_user}"; у поточному рядку."""
    for pat in _OWNER_PATTERNS:
        line = pat.sub(f'OWNER TO "{db_user}";', line)
    return line


def _stream_seed_into_psql(seed_file: str, *, db_user: str,
                           skip_drop: bool, single_tx: bool) -> None:
    """
    Стрімить .sql / .sql.gz у psql.
    - Якщо skip_drop=False — перед цим скидає схему public і створює заново з OWNER=db_user.
    - Якщо single_tx=True — імпорт у одній транзакції (-1).
    """
    if not skip_drop:
        drop_sql = (
            f'DROP SCHEMA IF EXISTS public CASCADE; '
            f'CREATE SCHEMA public AUTHORIZATION "{db_user}"; '
            f'ALTER SCHEMA public OWNER TO "{db_user}";'
        )
        _psql(["-tAc", drop_sql], check=True)

    # Готуємо psql для читання зі stdin
    args = []
    if single_tx:
        args.append("-1")
    args += ["-f", "-"]  # читати SQL зі stdin

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

    proc = subprocess.Popen(cmd, env=pg_env, stdin=subprocess.PIPE, text=True)

    def _write_stream(fobj):
        for line in fobj:
            proc.stdin.write(_normalize_owner_line(line, db_user))

    try:
        if seed_file.endswith(".gz"):
            with gzip.open(seed_file, "rt", encoding="utf-8", errors="ignore") as f:
                _write_stream(f)
        else:
            with open(seed_file, "rt", encoding="utf-8", errors="ignore") as f:
                _write_stream(f)
    finally:
        try:
            proc.stdin.close()
        except Exception:
            pass

    rc = proc.wait()
    if rc != 0:
        raise RuntimeError(f"psql returned non-zero exit code: {rc}")


# =========================
# Основна логіка сидингу
# =========================

def _seed_sql_if_needed() -> bool:
    """
    Сидинг БД із SQL/SQL.GZ дампу.
    ENV:
      SEED_ON_BOOT (bool)        — вмикає сидинг (default: false)
      SEED_MODE (str)            — "sql" / "sql_full" / "postgres_sql" (для сумісності; значення не критичне)
      SEED_FORCE_ON_BOOT (bool)  — ігнорувати перевірку "порожня/непорожня" (default: false)
      SEED_PATH (str)            — явний шлях до файлу (опц.)
      SEED_DIR (str)             — каталог з дампами (default: /app/backups)
      SEED_GLOB (str)            — маска пошуку файлів (default: *.sql*)
      SEED_SKIP_DROP (bool)      — не скидати схему public перед відновленням (default: false)
      SEED_PSQL_SINGLE_TX (bool) — виконувати в одній транзакції (-1) (default: true)
      SEED_OWNER_FIX (bool)      — нормалізувати OWNER TO ... на поточного DB_USER (default: true; вимикає лише нормалізацію рядків, але сам дамп все одно виконається)
    """
    on_boot = _env_bool("SEED_ON_BOOT", False)
    mode = _env_str("SEED_MODE", "sql").lower()
    force = _env_bool("SEED_FORCE_ON_BOOT", False)
    skip_drop = _env_bool("SEED_SKIP_DROP", False)
    single_tx = _env_bool("SEED_PSQL_SINGLE_TX", True)
    owner_fix = _env_bool("SEED_OWNER_FIX", True)
    db_user = _env_str("DB_USER", "")

    print(f"init_app: seed_on_boot={on_boot}, mode={mode}, force={force}")
    _db_diag()

    if not (on_boot and mode in ("sql", "sql_full", "postgres_sql")):
        print("init_app: seeding disabled by mode/on_boot")
        return False

    # М'ютекс між репліками
    if not _advisory_lock():
        print("init_app: another instance is seeding -> skip")
        return False

    need = force or (not _db_has_content())
    print(f"init_app: db_has_content={not need}, will_seed={need}")

    if not need:
        print("init_app: DB has content -> skip seeding")
        return False

    seed_file = _find_seed_file()
    if not seed_file:
        print("init_app: no seed file found (SEED_PATH / SEED_DIR+SEED_GLOB)")
        return False

    print(f"init_app: seeding from {seed_file} (skip_drop={skip_drop}, single_tx={single_tx}, owner_fix={owner_fix})")

    # Якщо вимкнули owner_fix — просто стрімимо як є, без нормалізації
    if not owner_fix:
        # Прямий стрім без змін рядків
        def _raw_stream_to_psql(path: str):
            args = []
            if single_tx:
                args.append("-1")
            args += ["-f", "-"]
            data = None
            if path.endswith(".gz"):
                with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
                    data = f.read()
            else:
                data = Path(path).read_text(encoding="utf-8", errors="ignore")
            if not skip_drop:
                drop_sql = (
                    f'DROP SCHEMA IF EXISTS public CASCADE; '
                    f'CREATE SCHEMA public AUTHORIZATION "{db_user}"; '
                    f'ALTER SCHEMA public OWNER TO "{db_user}";'
                )
                _psql(["-tAc", drop_sql], check=True)
            _psql(args, check=True, capture=False, text_input=data)

        _raw_stream_to_psql(seed_file)
    else:
        # Нормальний потік з нормалізацією OWNER
        _stream_seed_into_psql(seed_file, db_user=db_user, skip_drop=skip_drop, single_tx=single_tx)

    print("init_app: seeding completed")
    telegram_notify("✅ <b>Huhy.space</b>: БД відновлено з бекапу і готова до роботи.")
    return True


# =========================
# Django command
# =========================

class Command(BaseCommand):
    help = "Initial setup: optional seed (latest SQL/SQL.GZ), migrate, ensure superuser, Telegram notify."

    def handle(self, *args, **options):
        print(">>> init_app: start")

        # 0) Сидинг (перед міграціями, бо дамп може містити DDL)
        print(">>> init_app: seed phase")
        try:
            seeded = _seed_sql_if_needed()
            print(f">>> init_app: seeded = {seeded}")
        except Exception as e:
            print(f"init_app: seeding failed: {e}")
            # свідомо НЕ падаємо — даємо шанс піти далі (наприклад, якщо дампу немає)

        # 1) Міграції
        print(">>> init_app: migrate phase")
        call_command("migrate", interactive=False)

        # 2) Суперюзер (з підтримкою *_FILE)
        print(">>> init_app: superuser phase")
        User = get_user_model()
        su_username = _env_str("DJANGO_SUPERUSER_USERNAME", "admin")
        su_email = _env_str("DJANGO_SUPERUSER_EMAIL", "admin@example.com")

        # Підтримка secret-файлу (docker secrets)
        su_password = _env_str("DJANGO_SUPERUSER_PASSWORD", "")
        su_password_file = _env_str("DJANGO_SUPERUSER_PASSWORD_FILE", "")
        if not su_password and su_password_file and Path(su_password_file).is_file():
            try:
                su_password = Path(su_password_file).read_text(encoding="utf-8").strip()
            except Exception:
                pass
        if not su_password:
            su_password = "admin"

        if not User.objects.filter(username=su_username).exists():
            User.objects.create_superuser(su_username, su_email, su_password)
            print(f"init_app: superuser '{su_username}' created")
            telegram_notify(f"👤 Створено суперкористувача <b>{su_username}</b>.")
        else:
            print("init_app: superuser already exists")

        print(">>> init_app: done")
