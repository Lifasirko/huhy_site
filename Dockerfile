# Використання базового образу
FROM python:3.12-slim

# Встановлення робочої директорії
WORKDIR /app

# Копіювання файлів
COPY . .

# Встановлення Poetry
RUN pip install poetry

# Конфігурація Poetry
RUN poetry config virtualenvs.create false

# Встановлення залежностей
RUN poetry install --only main

# Set environment variables
ENV OWNERS=131445541 \
    TELEGRAM_ADMIN_IDS=131445541 \
    TGBOT_TOKEN=7350767988:AAGt0-dMsehLYl3gXFXokjZgQF5JPsqg874 \
    ip=localhost

# Collect static files
#RUN python manage.py collectstatic --noinput

# Відкриття порту
EXPOSE 8000

# Запуск сервера
CMD ["gunicorn", "--bind", ":8000", "alphahuhysite.wsgi:application"]
