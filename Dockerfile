# Dockerfile

# Вибираємо базовий образ Python
FROM python:3.10-slim

# Встановлюємо робочу директорію в контейнері
WORKDIR /app

# Копіюємо файли проекту в робочу директорію
COPY . .

# Встановлюємо залежності з використанням Poetry
RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

# Збірка статичних файлів
RUN python manage.py collectstatic --noinput

# Команда запуску сервера
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "alphahuhysite.wsgi:application"]
