from io import BytesIO

import qrcode
from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.html import format_html


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


class CustomUser(AbstractUser):
    telegram_id = models.CharField(max_length=255, unique=True, blank=True, null=True)
    phone = models.CharField(max_length=20, unique=True)

    def __str__(self):
        return self.username

    @classmethod
    def get_admin_ids(cls):
        """
        Отримує список Telegram ID адміністраторів з бази даних.
        """
        return list(cls.objects.values_list('telegram_id', flat=True))


class Form(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    email = models.EmailField()  # TODO: зробити нульовою
    form_name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.form_name} - {self.name}"


class Postcard(models.Model):
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200, verbose_name="Назва")
    content = models.TextField(verbose_name="Текст")

    def generate_qr_code_svg(self):
        # Створюємо URL для сторінки листівки
        url = f"{settings.SITE_URL}{reverse('postcard_detail', args=[self.id])}"

        # Генеруємо QR-код
        qr = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage)

        # Зберігаємо QR-код у SVG
        buffer = BytesIO()
        qr.save(buffer)
        svg_data = buffer.getvalue().decode()
        buffer.close()

        return svg_data  # Повертаємо SVG дані як строку

    def qr_code_link(self):
        if self.id:
            url = reverse('admin:postcard_qr_code_download', args=[self.id])
            return format_html(
                '<a href="{}" download class="button">Скачати QR-код</a>',
                url
            )
        return "QR-код недоступний"

    qr_code_link.allow_tags = True
    qr_code_link.short_description = "Завантажити QR-код"

