# Use the official Python image from the Docker Hub
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install Poetry for dependency management
RUN pip install poetry

# Configure Poetry to not create virtual environments
RUN poetry config virtualenvs.create false

# Install dependencies without dev packages
RUN poetry install --only main

# Set environment variables
ENV OWNERS=131445541 \
    TELEGRAM_ADMIN_IDS=131445541 \
    TGBOT_TOKEN=7350767988:AAGt0-dMsehLYl3gXFXokjZgQF5JPsqg874 \
    ip=localhost

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose the application port
EXPOSE 8000

# Command to run the Django server
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
