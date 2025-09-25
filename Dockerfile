# Dockerfile

# Вибираємо базовий образ Python
FROM python:3.12-slim

# Встановлюємо робочу директорію в контейнері
WORKDIR /app

# 1) pip preflight: оновлюємо pip і стабілізуємо 'attrs'/'packaging'
RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install "attrs>=23.2.0" "packaging==24.2" && \
    python -m pip uninstall -y attr || true

# 2) Poetry
RUN pip install poetry
RUN poetry config virtualenvs.create false

# 3) Інсталимо залежності з lock-файлу (без dev)
COPY pyproject.toml poetry.lock* ./
RUN poetry install --no-interaction --no-ansi --no-root

# 4) Далі копіюємо увесь код
COPY . .


# Збірка статичних файлів
#RUN python manage.py collectstatic --noinput

RUN apt-get update && apt-get install -y --no-install-recommends \
    postgresql-client netcat-openbsd \
 && rm -rf /var/lib/apt/lists/*


COPY entrypoint.sh /entrypoint.sh
RUN sed -i 's/\r$//' /entrypoint.sh && chmod +x /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]


# Команда запуску сервера
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "alphahuhysite.wsgi:application"]
