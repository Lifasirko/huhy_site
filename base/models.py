from django.db import models


class Banner(models.Model):
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=500)
    image = models.ImageField(upload_to='banners/')
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class RPG(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    game_system = models.CharField(max_length=100)  # Наприклад, D&D, Pathfinder тощо
    max_players = models.IntegerField()
    duration = models.DurationField()  # Тривалість гри
    date = models.DateField()  # Дата проведення
    time = models.TimeField()  # Час початку
    location = models.CharField(max_length=200)  # Місце проведення
    game_master = models.CharField(max_length=100)  # Ім'я ведучого гри

    def __str__(self):
        return f"{self.title} - {self.game_system}"


class AboutUs(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()

    def __str__(self):
        return self.title


class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    date = models.DateField()
    time = models.TimeField()
    location = models.CharField(max_length=200)

    def __str__(self):
        return f"{self.title} on {self.date}"


class ContactFormSubmission(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    submitted_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.name} at {self.submitted_at}"


class Footer(models.Model):
    address = models.CharField(max_length=300)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    map_embed_code = models.TextField()

    def __str__(self):
        return f"Contact Info: {self.address}, {self.phone}, {self.email}"


class User(models.Model):
    telegram_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(unique=True)
    password = models.CharField(max_length=255)

    def __str__(self):
        return self.name


class Form(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    form_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.form_name} - {self.name}"
