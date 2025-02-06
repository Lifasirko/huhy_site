from ckeditor.fields import RichTextField
from django.db import models
from django.utils.text import slugify
from django.utils.timezone import now
from imagekit.models import ImageSpecField
from pilkit.processors import ResizeToFill
from django.urls import reverse


class BlogPost(models.Model):
    title = models.CharField(max_length=200, unique=True, verbose_name="Заголовок")
    slug = models.SlugField(max_length=200, unique=True, blank=True, verbose_name="URL")
    content = RichTextField(verbose_name="Контент")
    main_image = models.ImageField(upload_to='blog/main_images/', verbose_name="Головне зображення")
    main_image_thumbnail = ImageSpecField(
        source='main_image',
        processors=[ResizeToFill(800, 450)],  # Альбомне зображення
        format='JPEG',
        options={'quality': 85}
    )
    author = models.CharField(max_length=100, verbose_name="Автор")
    published_date = models.DateTimeField(default=now, verbose_name="Дата публікації")
    updated_date = models.DateTimeField(auto_now=True)
    tags = models.ManyToManyField('Tag', blank=True, verbose_name="Теги")

    def get_absolute_url(self):
        return reverse('blog_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Стаття"
        verbose_name_plural = "Статті"
        ordering = ['-published_date']

    def __str__(self):
        return self.title


class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True, verbose_name="Назва")
    slug = models.SlugField(max_length=50, unique=True, blank=True, verbose_name="URL")

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = "Тег"
        verbose_name_plural = "Теги"

    def __str__(self):
        return self.name
