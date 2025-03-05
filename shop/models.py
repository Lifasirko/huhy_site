# huhy_site/shop/models.py

from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


# Нова модель для тегів
class Tag(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Назва тегу")

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=255, verbose_name="Назва категорії")
    slug = models.SlugField(unique=True, verbose_name="URL slug")
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children',
        verbose_name="Батьківська категорія"
    )

    class Meta:
        verbose_name_plural = "Категорії"

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products',
        verbose_name="Категорія"
    )
    name = models.CharField(max_length=255, verbose_name="Назва товару")
    slug = models.SlugField(unique=True, verbose_name="URL slug")
    description = models.TextField(blank=True, verbose_name="Опис товару")
    image = models.ImageField(
        upload_to='shop/products/',
        blank=True,
        null=True,
        verbose_name="Головне зображення"
    )
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")
    stock = models.PositiveIntegerField(default=0, verbose_name="Кількість на складі")
    available = models.BooleanField(default=True, verbose_name="Доступний")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated = models.DateTimeField(auto_now=True, verbose_name="Оновлено")
    # Поле тегів
    tags = models.ManyToManyField(Tag, blank=True, related_name='products', verbose_name="Теги")
    # Перейменовано з is_pack на is_bundle
    is_bundle = models.BooleanField(default=False, verbose_name="Бандл")
    # Багато до багатьох зв’язок для компонентів бандлу.
    bundle_components = models.ManyToManyField('self', symmetrical=False, blank=True, related_name='bundled_in',
                                               verbose_name="Компоненти бандлу")
    # Поля знижки (блок у товарі)
    discount_active = models.BooleanField(default=False, verbose_name="Активна знижка")
    discount_percent = models.PositiveIntegerField(default=0, verbose_name="Відсоток знижки")

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('shop:product_detail', kwargs={'slug': self.slug})

    @property
    def discounted_price(self):
        if self.discount_active and self.discount_percent > 0:
            return self.price * (100 - self.discount_percent) / 100
        return self.price

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Якщо товар є бандлом, додати його назву як тег
        if self.is_bundle:
            from django.db import IntegrityError
            try:
                tag, created = Tag.objects.get_or_create(name=self.name)
                if tag not in self.tags.all():
                    self.tags.add(tag)
            except IntegrityError:
                pass


class ProductImage(models.Model):
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name="Товар"
    )
    image = models.ImageField(upload_to='shop/products/', verbose_name="Зображення")
    caption = models.CharField(max_length=255, blank=True, null=True, verbose_name="Підпис")

    def __str__(self):
        return f"Image for {self.product.name}"


class Order(models.Model):
    PAYMENT_CHOICES = (
        ('online', 'Онлайн-оплата'),
        ('cash', 'Готівка'),
    )
    DELIVERY_CHOICES = (
        ('nova_poshta', 'Нова Пошта'),
        ('pickup', 'Самовивіз'),
    )
    STATUS_CHOICES = (
        ('new', 'Нове'),
        ('processing', 'В обробці'),
        ('shipped', 'Відправлено'),
        ('completed', 'Виконано'),
    )
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='orders',
        verbose_name="Користувач"
    )
    full_name = models.CharField(max_length=255, verbose_name="Ім'я")
    phone = models.CharField(max_length=20, verbose_name="Телефон")
    address = models.TextField(verbose_name="Адреса")
    payment_method = models.CharField(max_length=20, choices=PAYMENT_CHOICES, verbose_name="Спосіб оплати")
    delivery_method = models.CharField(max_length=20, choices=DELIVERY_CHOICES, verbose_name="Спосіб доставки")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='new', verbose_name="Статус")
    created = models.DateTimeField(auto_now_add=True, verbose_name="Створено")
    updated = models.DateTimeField(auto_now=True, verbose_name="Оновлено")

    def __str__(self):
        return f"Order {self.id} - {self.full_name}"


class OrderItem(models.Model):
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Замовлення"
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name="Товар"
    )
    quantity = models.PositiveIntegerField(default=1, verbose_name="Кількість")
    price = models.DecimalField(max_digits=10, decimal_places=2, verbose_name="Ціна")

    def __str__(self):
        return f"{self.quantity} x {self.product.name if self.product else 'Unknown'}"
