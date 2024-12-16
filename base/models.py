from io import BytesIO, StringIO

import qrcode
import svgwrite
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

    def get_absolute_url(self):
        # Додаємо https://, якщо його немає у базовому URL
        base_url = settings.SITE_URL
        if not base_url.startswith("http://") and not base_url.startswith("https://"):
            base_url = f"https://{base_url}"
        return f"{base_url}{reverse('postcard_detail', args=[str(self.id)])}"


    def generate_qr_code_svg(self):
        # Отримує повний URL для QR-коду
        url = self.get_absolute_url()

        # Створює QR-код
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)

        # Створює SVG
        dwg = svgwrite.Drawing(size=(qr.modules_count * 10, qr.modules_count * 10))
        for row, line in enumerate(qr.modules):
            for col, module in enumerate(line):
                if module:  # Якщо модуль є чорним
                    dwg.add(dwg.rect(insert=(col * 10, row * 10), size=(10, 10), fill='black'))

        # Зберігає SVG у StringIO
        svg_data = StringIO()
        dwg.write(svg_data)
        svg_data.seek(0)
        return svg_data.getvalue()  # Повертає SVG як рядок

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
