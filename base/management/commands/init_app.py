# base/management/commands/init_app.py
import os
import re
import gzip
import uuid
import shutil
import requests
import subprocess
from pathlib import Path
from typing import List, Set, Tuple

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model


# ----------------------------
# helpers
# ----------------------------
def _env_bool(name: str, default=False) -> bool:
    v = os.getenv(name, str(default)).strip().lower()
    return v in ("1", "true", "yes", "y", "on")


def _psql(args: List[str], check=True, capture=False) -> str:
    """
    Run psql with project DB env. Raises on non-zero exit if check=True.
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


# ----------------------------
# DB state checks (safe)
# ----------------------------
def _schema_has_tables(schema: str = "public") -> bool:
    """
    Безпечна перевірка: чи є хоч одна таблиця у схемі (без звернення до юзерських таблиць напряму).
    """
    sql = (
        "SELECT COUNT(*) FROM pg_class c "
        "JOIN pg_namespace n ON n.oid = c.relnamespace "
        f"WHERE n.nspname='{schema}' AND c.relkind IN ('r','p');"
    )
    out = _psql(["-tAc", sql], capture=True) or "0"
    try:
        return int(out.strip()) > 0
    except ValueError:
        return False


# ----------------------------
# Seed selection
# ----------------------------
def _choose_seed_file(seed_path: str, seed_glob: str = "*.sql*") -> Path | None:
    """
    Якщо seed_path — файл, повертаємо його; якщо директорія — беремо найсвіжіший файл за маскою.
    """
    p = Path(seed_path)
    if p.is_file():
        return p
    if p.is_dir():
        files = sorted(p.glob(seed_glob), key=lambda x: x.stat().st_mtime, reverse=True)
        return files[0] if files else None
    return None


# ----------------------------
# Variant B: temp roles
# ----------------------------
_ROLE_IGNORE = {"postgres", "public"}


def _role_exists(name: str) -> bool:
    safe = name.replace("'", "''")
    out = _psql(["-tAc", f"SELECT 1 FROM pg_roles WHERE rolname = '{safe}' LIMIT 1;"], capture=True)
    return out.strip() == "1"


def _create_temp_role(name: str):
    safe = name.replace('"', '""')
    _psql(["-tAc", f'CREATE ROLE "{safe}" NOLOGIN;'], check=True, capture=False)


def _reassign_and_drop_role(name: str, new_owner: str):
    s_name = name.replace('"', '""')
    s_owner = new_owner.replace('"', '""')
    # Перепризначаємо всі об'єкти і прибираємо привілеї, потім видаляємо роль
    _psql(["-tAc", f'REASSIGN OWNED BY "{s_name}" TO "{s_owner}";'], check=False, capture=False)
    _psql(["-tAc", f'DROP OWNED BY "{s_name}";'], check=False, capture=False)
    _psql(["-tAc", f'DROP ROLE "{s_name}";'], check=False, capture=False)


def _extract_role_candidates(sql_text: str, db_user: str) -> Set[str]:
    """
    З сирого дампу дістаємо можливі імена ролей, щоб тимчасово їх створити.
    Беремо з конструкцій OWNER TO / GRANT ... TO / REVOKE ... FROM /
    ALTER DEFAULT PRIVILEGES FOR ROLE / CREATE ROLE.
    """
    patterns = [
        r"\bOWNER\s+TO\s+\"?([A-Za-z0-9_]+)\"?",
        r"\bGRANT\b[^\;]*?\bTO\s+\"?([A-Za-z0-9_]+)\"?",
        r"\bREVOKE\b[^\;]*?\bFROM\s+\"?([A-Za-z0-9_]+)\"?",
        r"\bALTER\s+DEFAULT\s+PRIVILEGES\s+FOR\s+ROLE\s+\"?([A-Za-z0-9_]+)\"?",
        r"\bCREATE\s+ROLE\s+\"?([A-Za-z0-9_]+)\"?",
    ]
    found: Set[str] = set()
    for pat in patterns:
        for m in re.finditer(pat, sql_text, flags=re.IGNORECASE):
            name = (m.group(1) or "").strip()
            if not name:
                continue
            if name in _ROLE_IGNORE:
                continue
            if name.lower() == db_user.lower():
                continue
            found.add(name)
    return found


# ----------------------------
# Seeding
# ----------------------------
def _seed_sql_if_needed() -> Tuple[bool, str]:
    """
    Виконує сидинг, якщо:
      - SEED_ON_BOOT=true і SEED_MODE=sql (або postgres_sql/sql_full),
      - і (FORCE=true або схоже, що БД порожня).
    Повертає (seeded: bool, info_message: str).
    """
    on_boot = _env_bool("SEED_ON_BOOT", False)
    mode = os.getenv("SEED_MODE", "sql").strip().lower()
    force = _env_bool("SEED_FORCE_ON_BOOT", False)

    # Можемо передати або шлях до файлу, або директорію.
    seed_path = os.getenv("SEED_PATH", "/app/backups").strip()
    seed_glob = os.getenv("SEED_GLOB", "*.sql*").strip()  # наприклад: backup_*.sql.gz

    db_user = os.getenv("DB_USER", "").strip()
    print(f"init_app: seed_on_boot={on_boot}, mode={mode}, force={force}, seed_path={seed_path}")

    if not (on_boot and mode in ("sql", "sql_full", "postgres_sql")):
        return False, "seeding disabled"

    # Безпечна евристика «порожня БД» — у схемі public немає таблиць
    empty = not _schema_has_tables("public")
    need = force or empty
    if not need:
        return False, "DB has content -> skip seeding"

    seed_file = _choose_seed_file(seed_path, seed_glob)
    if not seed_file or not seed_file.exists():
        return False, f"seed file not found: {seed_path}"

    print(f"init_app: seeding from {seed_file}")

    # 1) Скидаємо схему й створюємо з правильним owner
    drop_sql = (
        f'DROP SCHEMA IF EXISTS public CASCADE; '
        f'CREATE SCHEMA public AUTHORIZATION "{db_user}"; '
        f'ALTER SCHEMA public OWNER TO "{db_user}";'
    )
    _psql(["-tAc", drop_sql], check=True, capture=False)

    # 2) Розпаковуємо дамп у /tmp/seed.sql (щоб уникнути "Broken pipe")
    tmp = Path("/tmp/seed.sql")
    if seed_file.suffix == ".gz":
        with gzip.open(seed_file, "rb") as fsrc, open(tmp, "wb") as fdst:
            shutil.copyfileobj(fsrc, fdst)
    else:
        shutil.copyfile(seed_file, tmp)

    # 3) Витягаємо потенційні імена ролей (ВАРІАНТ B)
    raw = tmp.read_text(encoding="utf-8", errors="ignore")
    candidates = sorted(_extract_role_candidates(raw, db_user))
    print(f"init_app: role candidates -> {candidates}")

    created: List[str] = []
    for r in candidates:
        try:
            if not _role_exists(r):
                _create_temp_role(r)
                created.append(r)
                print(f'init_app: created temp role "{r}"')
        except Exception as e:
            print(f'init_app: cannot create temp role "{r}": {e}')

    # 4) Імпорт дампу
    try:
        _psql(["-f", str(tmp)], check=True, capture=False)
    except Exception as e:
        return False, f"seeding failed: {e}"

    # 5) Після імпорту: REASSIGN OWNED/DROP тимчасові ролі
    for r in created:
        try:
            _reassign_and_drop_role(r, db_user)
            print(f'init_app: dropped temp role "{r}"')
        except Exception as e:
            print(f'init_app: cleanup for role "{r}" failed: {e}')

    telegram_notify("✅ <b>Huhy.space</b>: БД відновлено з бекапу і готова до роботи.")
    return True, "seeding completed"


# ----------------------------
# Command
# ----------------------------
class Command(BaseCommand):
    help = "Initial setup: optional seed, migrate, ensure superuser, notify."

    def handle(self, *args, **options):
        print(">>> init_app: start")

        # 0) Можливий сидинг (до міграцій, бо дамп містить DDL)
        seeded, msg = _seed_sql_if_needed()
        print(f">>> init_app: seed phase -> {msg}")
        print(f">>> init_app: seeded = {seeded}")

        # 1) Міграції
        print(">>> init_app: migrate phase")
        call_command("migrate", interactive=False)

        # 2) Суперюзер (обережно з унікальним phone)
        print(">>> init_app: superuser phase")
        try:
            User = get_user_model()
            su_username = os.getenv("DJANGO_SUPERUSER_USERNAME", "admin").strip()
            su_email = os.getenv("DJANGO_SUPERUSER_EMAIL", "admin@example.com").strip()
            su_password = os.getenv("DJANGO_SUPERUSER_PASSWORD", "admin").strip()
            only_if_empty = _env_bool("DJANGO_SUPERUSER_IF_EMPTY", True)  # створювати лише якщо немає користувачів

            if only_if_empty and User.objects.exists():
                print("init_app: users already exist -> skip superuser creation")
            else:
                # Визначаємо поле телефону (якщо є) і гарантуємо унікальність
                extra = {}
                try:
                    field_names = {f.name for f in User._meta.get_fields() if hasattr(f, "name")}
                    phone_field = (
                        "phone" if "phone" in field_names
                        else ("phone_number" if "phone_number" in field_names else None)
                    )
                    if phone_field:
                        env_phone = os.getenv("DJANGO_SUPERUSER_PHONE", "").strip()
                        if not env_phone:
                            env_phone = f"+999{uuid.uuid4().int % 10**9:09d}"  # технічний унікальний номер
                        extra[phone_field] = env_phone
                except Exception:
                    pass

                obj, created = User.objects.get_or_create(
                    username=su_username,
                    defaults={"email": su_email, **extra},
                )
                if created:
                    if hasattr(obj, "is_staff"):
                        obj.is_staff = True
                    if hasattr(obj, "is_superuser"):
                        obj.is_superuser = True
                    obj.set_password(su_password)
                    obj.save()
                    print(f"init_app: superuser '{su_username}' created")
                    telegram_notify(f"👤 Створено суперкористувача <b>{su_username}</b>.")
                else:
                    print("init_app: superuser already exists")
        except Exception as e:
            print(f"init_app: superuser phase skipped due to error: {e}")

        print(">>> init_app: done")
